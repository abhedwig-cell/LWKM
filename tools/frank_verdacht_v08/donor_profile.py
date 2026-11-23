"""Pas een volledig donorprofiel toe op de bestaande Frank-SVAT-tabel.

De aanroeper koppelt de oorspronkelijke verdachtvlaggen aan de operationele
donor en kiest dezelfde bronvariant voor target en donor. Deze module kiest
zelf geen donor en leidt geen nieuwe verdachte cellen af.

Identiteit, werkelijk targetoppervlak, gebied en de negen landgebruik-/
bodemvelden blijven targetgegevens. De 35 hydrologische velden worden als
een geheel letterlijk overgenomen. Hun mm/jaar-waarden zijn intensiteiten;
een verschillend targetoppervlak verandert die waarden niet. Een daaruit
berekend volume is een equivalent op targetoppervlak, geen herlezen lokaal
MODFLOW-celbudget. Bestaande balansdiagnostiek wordt niet op nul gezet.
"""

import math

from schema import AREA, COUNT, FLAG, HEADERS, ID, NET, NUMERIC_COLUMNS, P5, P95, REGION


HYDRO_COLUMNS = tuple(HEADERS[12:47])
PRESERVED_COLUMNS = tuple(HEADERS[:12] + [REGION])
FLUX_COLUMNS = tuple(HEADERS[20:47])

REL_TOL = 2e-7
ABS_TOL = 5e-5

_HEADER_SET = frozenset(HEADERS)


def _number(value, label, allow_missing=False):
    if not isinstance(value, str):
        raise ValueError('CSV-waarde is geen tekst: ' + label)
    text = value.strip()
    if not text:
        if allow_missing:
            return None
        raise ValueError('Verplichte waarde ontbreekt: ' + label)
    try:
        result = float(text)
    except (ValueError, OverflowError):
        raise ValueError('Geen getal voor {}: {!r}'.format(label, value))
    if not math.isfinite(result):
        raise ValueError('Niet-eindig getal: ' + label)
    return result


def _area(row, label):
    area = _number(row[AREA], label + ' oppervlak')
    if area <= 0:
        raise ValueError(label + ': oppervlak moet positief zijn')
    return area


def _relation(values, result_column, inputs, operation, label):
    """Controleer alleen relaties waarvoor alle betrokken bronwaarden bestaan."""
    result = values[result_column]
    operands = [values[column] for column in inputs]
    if result is None or any(value is None for value in operands):
        return
    try:
        expected = operation(operands)
    except (OverflowError, ValueError):
        raise ValueError(label + ': afgeleide waarde buiten bereik voor ' + result_column)
    if not math.isfinite(expected):
        raise ValueError(label + ': afgeleide waarde buiten bereik voor ' + result_column)
    if not math.isclose(result, expected, rel_tol=REL_TOL, abs_tol=ABS_TOL):
        raise ValueError('{}: {} wijkt af van componenten: {} versus {}'.format(
            label, result_column, result, expected))


def validate_row(row):
    """Valideer een SVAT-rij met exact de 49 Frankkolommen; retourneer None.

    Iedere CSV-waarde is een string. ID, N, oppervlakte en indicator zijn
    verplicht; N is 1. Een numeriek leeg veld blijft ontbrekend. Daardoor
    zijn gedeeltelijk ontbrekende profielen herkenbaar en wordt een bekende
    bronleemte niet stilzwijgend nul. Categorische codes blijven letterlijk.
    Er geldt geen bovengrens van 62500 m2 voor SVAT-oppervlak.
    """
    if not hasattr(row, 'keys') or frozenset(row.keys()) != _HEADER_SET:
        raise ValueError('SVAT-rij heeft niet exact de 49 Frankkolommen')
    if any(not isinstance(row[column], str) for column in HEADERS):
        raise ValueError('Iedere CSV-waarde moet tekst zijn; een leeg veld is een lege string')
    sid = row[ID].strip()
    if not sid.isdigit() or int(sid) <= 0:
        raise ValueError('Ongeldig positief SVAT-id: ' + repr(row[ID]))
    label = 'SVAT ' + sid
    if _number(row[COUNT], label + ' N') != 1:
        raise ValueError(label + ': N moet 1 zijn')
    _area(row, label)
    if row[FLAG] not in ('0', '1'):
        raise ValueError(label + ': indicator moet exact 0 of 1 zijn')

    values = {column: _number(row[column], label + ' ' + column, allow_missing=True)
              for column in NUMERIC_COLUMNS}
    for lower, upper in (('GHG m-mv', 'GLG m-mv'), (P5, P95)):
        if values[lower] is not None and values[upper] is not None:
            if values[lower] > values[upper]:
                raise ValueError('{}: {} is groter dan {}'.format(label, lower, upper))

    _relation(values, 'GG ((GHG+GLG)/2)', ['GHG m-mv', 'GLG m-mv'],
              lambda v: v[0] / 2.0 + v[1] / 2.0, label)
    _relation(values, 'Dynamiek (GLG-GHG)', ['GLG m-mv', 'GHG m-mv'],
              lambda v: v[0] - v[1], label)
    _relation(values, NET, ['Kwel', 'Wegzijging'], lambda v: v[0] - v[1], label)
    _relation(values, 'Ontwatering', ['Fldrou' + str(i) for i in range(1, 6)],
              math.fsum, label)
    _relation(values, 'Infiltratie', ['Fldrin1', 'Fldrin2', 'Fldrin345'],
              math.fsum, label)


def apply_profile(target, donor, is_suspect):
    """Geef een nieuwe rij; vervang uitsluitend bij de expliciete verdachtvlag.

    Voor een niet-verdachte target mag ``donor`` None zijn. Een afwijkend
    donor-ID alleen is geen reden voor vervanging. Bij een verdachte target
    wordt de indicator 1, ook wanneer de gekopieerde waarden toevallig gelijk
    zijn. De aanroeper bewaart de afzonderlijke Flevoland- en donorherkomst.
    """
    if not isinstance(is_suspect, bool):
        raise ValueError('is_suspect moet een expliciete bool uit de kwalificatie zijn')
    validate_row(target)
    result = dict(target)
    if not is_suspect:
        return result
    if donor is None:
        raise ValueError('Donorprofiel ontbreekt voor verdachte SVAT ' + target[ID])
    validate_row(donor)
    for column in HYDRO_COLUMNS:
        result[column] = donor[column]
    result[FLAG] = '1'
    return result


def equivalent_annual_volume(row, column):
    """Retourneer mm/jaar * werkelijk targetoppervlak / 1000 in m3/jaar.

    Alleen flux-, opslag- en balansdiagnostiekvelden hebben deze conversie.
    Een ontbrekende intensiteit levert None op. Dit is een afgeleid volume-
    equivalent, geen waarneming of lokaal modelbudget na donorvervanging.
    """
    if column not in FLUX_COLUMNS:
        raise ValueError('Veld heeft geen mm/jaar-conversie: ' + str(column))
    area = _area(row, 'SVAT ' + row[ID])
    value = _number(row[column], column, allow_missing=True)
    if value is None:
        return None
    result = (value / 1000.0) * area
    if not math.isfinite(result):
        raise ValueError('Volume-equivalent buiten eindig bereik: ' + column)
    return result
