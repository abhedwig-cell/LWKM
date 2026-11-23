"""Oppervlaktegewogen samenvattingen binnen de bestaande HRU-indeling.

Dit module leest geen bestanden en bepaalt geen nieuwe HRU's. De aanroeper
controleert vooraf dat MODFLOW-celvolumes niet dubbel aan leden zijn toegekend.
Grondwaterkengetallen zijn gewogen samenvattingen van SVAT-kengetallen; er
worden hier geen nieuwe kengetallen uit een HRU-tijdreeks berekend.
"""

import math
from collections import Counter
from decimal import Decimal, InvalidOperation

from schema import CATEGORICAL_COLUMNS, HEADERS, NUMERIC_COLUMNS


ID_COLUMN = HEADERS[0]
COUNT_COLUMN = HEADERS[1]
AREA_COLUMN = HEADERS[2]
GLG_COLUMN = HEADERS[13]
GHG_COLUMN = HEADERS[14]
GG_COLUMN = HEADERS[15]
DYNAMICS_COLUMN = HEADERS[16]
KWELCLASS_COLUMN = HEADERS[19]
FLAG_COLUMN = HEADERS[47]
REGION_COLUMN = HEADERS[48]


class _Sum:
    """Neumaier-som: behoud ook kleine bijdragen bij signed fluxen."""

    __slots__ = ("total", "compensation")

    def __init__(self):
        self.total = 0.0
        self.compensation = 0.0

    def add(self, value):
        subtotal = self.total + value
        if not math.isfinite(subtotal):
            raise ValueError("Som buiten het bereik van eindige getallen")
        if abs(self.total) >= abs(value):
            self.compensation += (self.total - subtotal) + value
        else:
            self.compensation += (value - subtotal) + self.total
        self.total = subtotal

    def value(self):
        result = self.total + self.compensation
        if not math.isfinite(result):
            raise ValueError("Som buiten het bereik van eindige getallen")
        return result


def _text(value):
    return "" if value is None else str(value).strip()


def _number(value, label, allow_missing=False):
    text = _text(value)
    if not text:
        if allow_missing:
            return None
        raise ValueError("Lege waarde: " + label)
    if isinstance(value, bool):
        raise ValueError("Boolean in numeriek veld: " + label)
    try:
        number = float(text)
    except (TypeError, ValueError):
        raise ValueError("Ongeldig getal voor {}: {!r}".format(label, value))
    if not math.isfinite(number):
        raise ValueError("Niet-eindige waarde: " + label)
    return number


def _identifier(value, label):
    if isinstance(value, bool):
        raise ValueError("Ongeldige {}: {!r}".format(label, value))
    text = _text(value)
    if not text.isdigit() or int(text) <= 0:
        raise ValueError("Ongeldige {}: {!r}".format(label, value))
    return int(text)


def _sort_value(value):
    # Categoriecodes blijven letterlijk behouden; alleen de volgorde is numeriek
    # waar dat kan. Hierdoor staat 2 voor 10 zonder tekstcodes te veranderen.
    try:
        numeric = Decimal(value)
        if numeric.is_finite():
            return (0, numeric, value)
    except InvalidOperation:
        pass
    return (1, value.casefold(), value)


def _format_number(value):
    if value == 0:
        return "0"
    return format(value, ".15g")


class _Coverage:
    __slots__ = ("count", "area")

    def __init__(self):
        self.count = 0
        self.area = _Sum()

    def add(self, area):
        self.count += 1
        self.area.add(area)


class _Group:
    def __init__(self):
        self.count = 0
        self.area = _Sum()
        self.weighted = {column: _Sum() for column in NUMERIC_COLUMNS}
        self.numeric_coverage = {column: _Coverage() for column in NUMERIC_COLUMNS}
        self.categories = {column: {} for column in CATEGORICAL_COLUMNS}
        self.category_coverage = {column: _Coverage() for column in CATEGORICAL_COLUMNS}
        self.regions = {}
        self.region_coverage = _Coverage()
        self.changed = _Coverage()


class HruAggregator:
    """Verzamel unieke SVAT-rijen en lever exact dezelfde 49 kolommen per HRU.

    ``schema_rows`` bevat HRU-id -> categorievelden met de exacte Frank-headers.
    Een niet-lege officiële schemacategorie gaat voor op een samenvatting van
    leden. Ontbreekt die, dan blijven alle waargenomen categorieën zichtbaar
    als bijvoorbeeld ``1|3``. Er wordt geen modus of nieuwe representant gekozen.

    ``membership`` is optioneel, met integer SVAT-id -> integer HRU-id. Als deze
    is meegegeven, moet iedere toegevoegde rij exact met die koppeling kloppen.

    Gebruik ``use_schema_kwelklasse=False`` voor beide fluxvarianten wanneer de
    actuele kwelklassen uit de SVAT-tabel leidend zijn. Dan is ook Kwelklasse4
    een lijst van de werkelijk voorkomende klassen binnen de HRU.
    """

    def __init__(self, schema_rows=None, membership=None, *, use_schema_kwelklasse=True):
        self.schema_rows = {}
        for hru, row in (schema_rows or {}).items():
            key = _identifier(hru, "HRU-id in schema")
            if key in self.schema_rows:
                raise ValueError("Dubbele HRU-id in schema: {}".format(key))
            self.schema_rows[key] = dict(row)
        self.membership = membership
        self.use_schema_kwelklasse = use_schema_kwelklasse
        self._groups = {}
        self._seen_svats = set()

    def add(self, hru, row):
        """Voeg één SVAT toe; ontbrekende numerieke waarden zijn geen nul."""
        hru = _identifier(hru, "HRU-id")
        svat = _identifier(row.get(ID_COLUMN), "SVAT-id")
        if svat in self._seen_svats:
            raise ValueError("Dubbele SVAT in HRU-aggregatie: {}".format(svat))
        if self.membership is not None:
            if svat not in self.membership:
                raise ValueError("SVAT {} ontbreekt in HRU-membership".format(svat))
            expected = _identifier(self.membership[svat], "HRU-id in membership")
            if expected != hru:
                raise ValueError("SVAT {}: HRU {} wijkt af van membership {}".format(svat, hru, expected))

        label = "SVAT {}".format(svat)
        area = _number(row.get(AREA_COLUMN), label + " oppervlakte")
        if area <= 0:
            raise ValueError(label + ": oppervlakte moet positief zijn")
        count = _number(row.get(COUNT_COLUMN), label + " N")
        if count != 1:
            raise ValueError(label + ": invoer moet één SVAT per rij bevatten (N=1)")
        flag = _number(row.get(FLAG_COLUMN), label + " correctie-indicator")
        if flag not in (0.0, 1.0):
            raise ValueError(label + ": correctie-indicator moet 0 of 1 zijn")

        # Valideer de hele rij voordat de toestand wordt bijgewerkt.
        values = {}
        for column in NUMERIC_COLUMNS:
            value = _number(row.get(column), label + " " + column, allow_missing=True)
            if value is not None and not math.isfinite(value * area):
                raise ValueError(label + ": oppervlaktegewogen waarde te groot voor " + column)
            values[column] = value
        categories = {column: _text(row.get(column)) for column in CATEGORICAL_COLUMNS}
        region = _text(row.get(REGION_COLUMN))

        group = self._groups.get(hru)
        if group is None:
            group = _Group()
            self._groups[hru] = group
        group.count += 1
        group.area.add(area)
        for column, value in values.items():
            if value is not None:
                group.weighted[column].add(value * area)
                group.numeric_coverage[column].add(area)
        for column, value in categories.items():
            if value:
                coverage = group.categories[column].get(value)
                if coverage is None:
                    coverage = _Coverage()
                    group.categories[column][value] = coverage
                coverage.add(area)
                group.category_coverage[column].add(area)
        if region:
            coverage = group.regions.get(region)
            if coverage is None:
                coverage = _Coverage()
                group.regions[region] = coverage
            coverage.add(area)
            group.region_coverage.add(area)
        if flag:
            group.changed.add(area)
        self._seen_svats.add(svat)

    def _category(self, hru, group, column):
        value = _text(self.schema_rows.get(hru, {}).get(column))
        use_schema = column != KWELCLASS_COLUMN or self.use_schema_kwelklasse
        if value and use_schema:
            return value, "official_hru_schema"
        values = sorted(group.categories[column], key=_sort_value)
        return "|".join(values), "member_values"

    def _numeric_means(self, group):
        area = group.area.value()
        means = {}
        for column in NUMERIC_COLUMNS:
            complete = group.numeric_coverage[column].count == group.count
            means[column] = group.weighted[column].value() / area if complete else None
        # Deze twee velden zijn per definitie afgeleid, niet onafhankelijk.
        if means[GHG_COLUMN] is None or means[GLG_COLUMN] is None:
            means[GG_COLUMN] = None
            means[DYNAMICS_COLUMN] = None
        else:
            means[GG_COLUMN] = means[GHG_COLUMN] / 2.0 + means[GLG_COLUMN] / 2.0
            means[DYNAMICS_COLUMN] = means[GLG_COLUMN] - means[GHG_COLUMN]
        if any(value is not None and not math.isfinite(value) for value in means.values()):
            raise ValueError("Niet-eindige HRU-gemiddelde of afgeleide grondwaterwaarde")
        return means

    def rows(self):
        """Lever HRU-rijen in numerieke HRU-volgorde; opent geen bestanden."""
        for hru in sorted(self._groups):
            group = self._groups[hru]
            result = {column: "" for column in HEADERS}
            result[ID_COLUMN] = str(hru)
            result[COUNT_COLUMN] = str(group.count)
            result[AREA_COLUMN] = _format_number(group.area.value())
            for column, value in self._numeric_means(group).items():
                result[column] = "" if value is None else _format_number(value)
            for column in CATEGORICAL_COLUMNS:
                result[column] = self._category(hru, group, column)[0]
            result[FLAG_COLUMN] = "1" if group.changed.count else "0"
            result[REGION_COLUMN] = "|".join(sorted(group.regions, key=_sort_value))
            yield result

    @staticmethod
    def _coverage_record(hru, column, coverage, group):
        area = group.area.value()
        valid_area = coverage.area.value()
        return {
            "hru": hru,
            "column": column,
            "valid_svats": coverage.count,
            "total_svats": group.count,
            "valid_area_m2": valid_area,
            "total_area_m2": area,
            "valid_area_fraction": valid_area / area,
        }

    @staticmethod
    def _category_values(values):
        return [
            {"value": value, "svats": values[value].count, "area_m2": values[value].area.value()}
            for value in sorted(values, key=_sort_value)
        ]

    def diagnostics(self):
        """Geef controleerbare dekking, categorieherkomst en gemengde gebieden.

        Diagnostiek is per HRU en veld, zonder een extra kopie van SVAT-rijen.
        Een niet-volledig numeriek veld krijgt geen gemiddelde op een kleinere
        noemer. GG/dynamiek worden uitsluitend uit GLG/GHG afgeleid.
        """
        numeric_missing = []
        categorical_missing = []
        mixed_categories = []
        schema_conflicts = []
        region_records = []
        category_sources = {column: Counter() for column in CATEGORICAL_COLUMNS}
        total_area = _Sum()
        changed_area = _Sum()
        changed_svats = 0
        changed_hrus = 0
        numeric_totals = {column: _Sum() for column in NUMERIC_COLUMNS}
        numeric_valid_areas = {column: _Sum() for column in NUMERIC_COLUMNS}
        numeric_complete_hrus = Counter()

        for hru in sorted(self._groups):
            group = self._groups[hru]
            total_area.add(group.area.value())
            changed_area.add(group.changed.area.value())
            changed_svats += group.changed.count
            changed_hrus += bool(group.changed.count)
            means = self._numeric_means(group)
            for column in NUMERIC_COLUMNS:
                coverage = group.numeric_coverage[column]
                numeric_totals[column].add(group.weighted[column].value())
                numeric_valid_areas[column].add(coverage.area.value())
                if means[column] is not None:
                    numeric_complete_hrus[column] += 1
                if coverage.count != group.count:
                    record = self._coverage_record(hru, column, coverage, group)
                    record["output"] = "derived_from_ghg_glg" if column in (GG_COLUMN, DYNAMICS_COLUMN) and means[column] is not None else "blank"
                    numeric_missing.append(record)
            for column in CATEGORICAL_COLUMNS:
                output, source = self._category(hru, group, column)
                category_sources[column][source] += 1
                values = group.categories[column]
                coverage = group.category_coverage[column]
                if coverage.count != group.count:
                    record = self._coverage_record(hru, column, coverage, group)
                    record.update({"output": output, "source": source})
                    categorical_missing.append(record)
                if len(values) > 1:
                    mixed_categories.append({
                        "hru": hru, "column": column, "output": output,
                        "source": source, "values": self._category_values(values),
                    })
                if source == "official_hru_schema" and values and output not in values:
                    schema_conflicts.append({
                        "hru": hru, "column": column, "schema_value": output,
                        "member_values": sorted(values, key=_sort_value),
                    })
            if len(group.regions) != 1 or group.region_coverage.count != group.count:
                record = self._coverage_record(hru, REGION_COLUMN, group.region_coverage, group)
                record["regions"] = self._category_values(group.regions)
                region_records.append(record)

        return {
            "method": "area_weighted_member_summaries_on_actual_svat_area",
            "groundwater_statistics": "Area-weighted SVAT characteristics; not statistics recalculated from an HRU time series.",
            "missing_numeric_policy": "Blank if any member is missing; GG/dynamics derived from complete aggregated GLG/GHG only.",
            "categorical_policy": "Official HRU schema where supplied, otherwise all observed values separated by |; no new mode.",
            "kwelklasse_uses_schema": self.use_schema_kwelklasse,
            "region_policy": "All observed region codes separated by |; partial missing coverage is reported.",
            "flag_policy": "1 if at least one member has correction flag 1, otherwise 0.",
            "hrus": len(self._groups),
            "svats": len(self._seen_svats),
            "total_area_m2": total_area.value(),
            "corrected_hrus": changed_hrus,
            "corrected_svats": changed_svats,
            "corrected_area_m2": changed_area.value(),
            "numeric_field_totals": {
                column: {
                    "sum_member_area_times_value": numeric_totals[column].value(),
                    "valid_member_area_m2": numeric_valid_areas[column].value(),
                    "complete_output_hrus": numeric_complete_hrus[column],
                }
                for column in NUMERIC_COLUMNS
            },
            "category_sources": {column: dict(counts) for column, counts in category_sources.items()},
            "numeric_missing": numeric_missing,
            "categorical_missing": categorical_missing,
            "mixed_categories": mixed_categories,
            "schema_values_not_present_in_members": schema_conflicts,
            "regions_multiple_or_missing": region_records,
        }
