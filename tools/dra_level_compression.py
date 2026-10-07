"""Diagnostic compression of seven physical LHM drainage systems to <=5 SWAP levels.

This module does not render production DRA files and does not grant admission.

Principles:
- aggregate every physical LHM drainage component first;
- never drop a physical component merely because SWAP has fewer levels;
- keep drain tubes separate from open channels;
- only merge hydraulically compatible open-channel components;
- preserve parallel drainage/infiltration conductance exactly;
- represent bottom and seasonal levels by drainage-conductance weighting;
- choose merges by minimum conductance-weighted hydraulic level variance.

Spacing/L and final SWAP level ordering remain separate qualification gates.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite
from datetime import date
from typing import Iterable


INACTIVE_RESISTANCE = 100000.0


@dataclass(frozen=True)
class PhysicalDrainageSystem:
    source_ids: tuple[str, ...]
    hydraulic_class: str
    medium: str
    drnres: float
    infres: float
    dep: float
    peil_sum: float
    peil_win: float
    dd: float | None = None
    level_series: tuple[tuple[str, float], ...] | None = None
    drainage_conductance_raw: float | None = None
    infiltration_conductance_raw: float | None = None
    physical_active: bool | None = None
    merge_history: tuple[dict, ...] = ()

    @property
    def allow_infiltration(self) -> bool:
        return self.hydraulic_class == "infiltration_capable_open"

    @property
    def drainage_conductance(self) -> float:
        if self.drainage_conductance_raw is not None:
            return float(self.drainage_conductance_raw)
        return _resistance_to_conductance(self.drnres)

    @property
    def infiltration_conductance(self) -> float:
        if not self.allow_infiltration:
            return 0.0
        if self.infiltration_conductance_raw is not None:
            return float(self.infiltration_conductance_raw)
        return _resistance_to_conductance(self.infres)

    @property
    def active(self) -> bool:
        if self.physical_active is not None:
            return bool(self.physical_active)
        return self.drainage_conductance > 0.0


def _resistance_to_conductance(resistance: float) -> float:
    r = float(resistance)
    if not isfinite(r) or r <= 0.0 or r >= INACTIVE_RESISTANCE:
        return 0.0
    return 1.0 / r


def _conductance_to_resistance(conductance: float) -> float:
    """Return the exact equivalent resistance for positive conductance.

    Do not clamp physical resistance to the SWAP parser maximum here. Values
    above 1e5 d are valid diagnostic evidence that the physical source cannot
    be represented exactly by a standalone SWAP method-3 level. Production
    rendering owns that separate fail-closed interface gate.
    """
    g = float(conductance)
    if not isfinite(g) or g <= 0.0:
        return INACTIVE_RESISTANCE
    return 1.0 / g


def _weighted(a: float, ga: float, b: float, gb: float) -> float:
    total = ga + gb
    if total <= 0.0:
        return 0.0
    return (ga * float(a) + gb * float(b)) / total


def _series_map(system: PhysicalDrainageSystem) -> dict[str, float] | None:
    if system.level_series is None:
        return None
    out = dict(system.level_series)
    if len(out) != len(system.level_series):
        raise ValueError(f"duplicate level-series dates in {system.source_ids}")
    return out


def _seasonal_level(system: PhysicalDrainageSystem, date_key: str) -> float:
    try:
        month = date.fromisoformat(date_key).month
    except ValueError as exc:
        raise ValueError(f"level-series date must be ISO YYYY-MM-DD: {date_key}") from exc
    return system.peil_sum if 4 <= month <= 9 else system.peil_win


def _level_on(system: PhysicalDrainageSystem, date_key: str) -> float:
    series = _series_map(system)
    if series is None:
        return _seasonal_level(system, date_key)
    if date_key not in series:
        raise ValueError(f"missing explicit level date {date_key} in {system.source_ids}")
    return float(series[date_key])


def _common_level_dates(
    a: PhysicalDrainageSystem,
    b: PhysicalDrainageSystem,
) -> list[str]:
    sa = _series_map(a)
    sb = _series_map(b)
    if sa is None and sb is None:
        return []
    if sa is None:
        return sorted(sb)
    if sb is None:
        return sorted(sa)
    if set(sa) != set(sb):
        raise ValueError(
            f"dynamic level-series date mismatch: {a.source_ids} versus {b.source_ids}"
        )
    return sorted(sa)


def _merge_level_series(
    a: PhysicalDrainageSystem,
    b: PhysicalDrainageSystem,
    ga: float,
    gb: float,
) -> tuple[tuple[str, float], ...] | None:
    dates = _common_level_dates(a, b)
    if not dates:
        return None
    return tuple(
        (key, _weighted(_level_on(a, key), ga, _level_on(b, key), gb))
        for key in dates
    )


def max_source_level_separation(
    a: PhysicalDrainageSystem,
    b: PhysicalDrainageSystem,
) -> float:
    """Maximum prescribed-level separation collapsed by a merge.

    Any non-zero separation means two physical activation breakpoints are
    represented by one SWAP level. Even when drainage and infiltration
    conductance ratios are proportional, the source piecewise flux relation is
    not generally exact between those two breakpoints.
    """
    dates=_common_level_dates(a,b)
    if dates:
        return max(
            (abs(_level_on(a,key)-_level_on(b,key)) for key in dates),
            default=0.0,
        )
    return max(
        abs(float(a.peil_sum)-float(b.peil_sum)),
        abs(float(a.peil_win)-float(b.peil_win)),
    )


def drainage_infiltration_level_gap(
    a: PhysicalDrainageSystem,
    b: PhysicalDrainageSystem,
) -> float:
    """Maximum gap between drainage- and infiltration-equivalent levels.

    One SWAP method-3 level has one water-level series shared by DRARES and
    INFRES. For two infiltration-capable physical systems, the exact drainage
    centroid uses drainage conductance weights while the exact infiltration
    centroid uses infiltration conductance weights. A non-zero gap therefore
    quantifies irreducible level-representation tension in a one-level merge.
    """
    ga=a.drainage_conductance
    gb=b.drainage_conductance
    ia=a.infiltration_conductance
    ib=b.infiltration_conductance
    if ga+gb<=0.0 or ia+ib<=0.0:
        return 0.0

    dates=_common_level_dates(a,b)
    if dates:
        pairs=[(_level_on(a,key),_level_on(b,key)) for key in dates]
    else:
        pairs=[
            (float(a.peil_sum),float(b.peil_sum)),
            (float(a.peil_win),float(b.peil_win)),
        ]

    gaps=[]
    for la,lb in pairs:
        ld=_weighted(la,ga,lb,gb)
        li=_weighted(la,ia,lb,ib)
        gaps.append(abs(ld-li))
    return max(gaps,default=0.0)


def hydraulic_merge_cost(a: PhysicalDrainageSystem, b: PhysicalDrainageSystem) -> float:
    """Ward-like merge cost over bottom/summer/winter levels.

    The factor ga*gb/(ga+gb) weights the squared level separation by hydraulic
    importance. For equal levels, merging is lossless for the represented levels.
    """
    if a.medium != "open_channel" or b.medium != "open_channel":
        return float("inf")
    if a.hydraulic_class != b.hydraulic_class:
        return float("inf")
    ga = a.drainage_conductance
    gb = b.drainage_conductance
    if ga <= 0.0 or gb <= 0.0:
        return float("inf")
    factor = ga * gb / (ga + gb)
    dates = _common_level_dates(a, b)
    if dates:
        level_distance = sum(
            (_level_on(a, key) - _level_on(b, key)) ** 2 for key in dates
        ) / len(dates)
        distance2 = (a.dep - b.dep) ** 2 + level_distance
    else:
        distance2 = (
            (a.dep - b.dep) ** 2
            + (a.peil_sum - b.peil_sum) ** 2
            + (a.peil_win - b.peil_win) ** 2
        )
    return factor * distance2


def _merge_spacing(a: PhysicalDrainageSystem, b: PhysicalDrainageSystem) -> float | None:
    """Preserve modern representative-SVAT spacing through compression.

    Under the modern DRA authority every active physical system in one HRU uses
    the same L = 4 * representative-SVAT dqsat. A differing non-null spacing is
    therefore a contract violation, not something to average silently.
    """
    if a.dd is None and b.dd is None:
        return None
    if a.dd is None:
        return b.dd
    if b.dd is None:
        return a.dd
    if abs(float(a.dd) - float(b.dd)) > 1e-9:
        raise ValueError(
            f"incompatible drainage spacing during merge: {a.dd} versus {b.dd}"
        )
    return float(a.dd)


def from_aggregate(
    *,
    source_id: str,
    hydraulic_class: str,
    medium: str,
    aggregate: dict,
    level_series: tuple[tuple[str, float], ...] | None = None,
) -> PhysicalDrainageSystem:
    """Create a physical-system record from aggregate_physical_system output."""
    support_area = float(
        aggregate.get(
            "support_area_m2",
            62500.0 * float(aggregate.get("member_count", 0)),
        )
    )
    cdr_sum = float(aggregate.get("cdr_sum", 0.0))
    inf_sum = float(aggregate.get("infiltration_conductance_sum", 0.0))
    drainage_g = cdr_sum / support_area if support_area > 0.0 else 0.0
    infiltration_g = inf_sum / support_area if support_area > 0.0 else 0.0
    return PhysicalDrainageSystem(
        source_ids=(source_id,),
        hydraulic_class=hydraulic_class,
        medium=medium,
        # Modern physical-system objects retain the exact equivalent
        # resistance. aggregate_physical_system also exposes SWAP-capped
        # compatibility values, but using those here would make the
        # >1e5-parser-range diagnostic impossible by construction.
        drnres=_conductance_to_resistance(drainage_g),
        infres=(
            _conductance_to_resistance(infiltration_g)
            if hydraulic_class == "infiltration_capable_open"
            else INACTIVE_RESISTANCE
        ),
        dep=float(aggregate["dep"]),
        peil_sum=float(aggregate["peil_sum"]),
        peil_win=float(aggregate["peil_win"]),
        dd=float(aggregate["dd"]),
        level_series=level_series,
        drainage_conductance_raw=drainage_g,
        infiltration_conductance_raw=infiltration_g,
        physical_active=(cdr_sum > 0.0),
    )


def to_render_level(system: PhysicalDrainageSystem) -> dict:
    """Convert a compressed physical system to explicit DRA renderer input.

    SWAP 4.3.1 method-3 accepts DRARES/INFRES only through 1e5 d. Fail
    explicitly when the exact modern physical equivalent is outside that
    interface instead of silently changing its conductance.
    """
    if system.dd is None:
        raise ValueError("drainage spacing L is unresolved for compressed level")
    if not 1.0 <= float(system.drnres) <= INACTIVE_RESISTANCE:
        raise ValueError(
            f"SWAP DRARES range overflow for {system.source_ids}: {system.drnres}"
        )
    if not 0.0 <= float(system.infres) <= INACTIVE_RESISTANCE:
        raise ValueError(
            f"SWAP INFRES range overflow for {system.source_ids}: {system.infres}"
        )
    return {
        "source_ids": system.source_ids,
        "medium": system.medium,
        "allow_infiltration": system.allow_infiltration,
        "drnres": system.drnres,
        "infres": system.infres,
        "dd": system.dd,
        "dep": system.dep,
        "peil_sum": system.peil_sum,
        "peil_win": system.peil_win,
        "level_series": system.level_series,
    }


def merge_systems(a: PhysicalDrainageSystem, b: PhysicalDrainageSystem) -> PhysicalDrainageSystem:
    if a.medium != "open_channel" or b.medium != "open_channel":
        raise ValueError("only open-channel systems may be merged")
    if a.hydraulic_class != b.hydraulic_class:
        raise ValueError("cross-hydraulic-class merge is prohibited")

    ga = a.drainage_conductance
    gb = b.drainage_conductance
    if ga <= 0.0 or gb <= 0.0:
        raise ValueError("only active systems may be merged")

    gi = a.infiltration_conductance + b.infiltration_conductance
    merged = PhysicalDrainageSystem(
        source_ids=tuple(sorted(a.source_ids + b.source_ids)),
        hydraulic_class=a.hydraulic_class,
        medium="open_channel",
        drnres=_conductance_to_resistance(ga + gb),
        infres=_conductance_to_resistance(gi),
        dep=_weighted(a.dep, ga, b.dep, gb),
        peil_sum=_weighted(a.peil_sum, ga, b.peil_sum, gb),
        peil_win=_weighted(a.peil_win, ga, b.peil_win, gb),
        dd=_merge_spacing(a, b),
        level_series=_merge_level_series(a, b, ga, gb),
        drainage_conductance_raw=ga + gb,
        infiltration_conductance_raw=gi,
        physical_active=True,
        merge_history=a.merge_history
        + b.merge_history
        + (
            {
                "left": list(a.source_ids),
                "right": list(b.source_ids),
                "cost": hydraulic_merge_cost(a, b),
                "max_drainage_infiltration_level_gap_m":
                    drainage_infiltration_level_gap(a, b),
                "max_source_level_separation_m":
                    max_source_level_separation(a, b),
                "bottom_depth_separation_m":
                    abs(float(a.dep)-float(b.dep)),
            },
        ),
    )
    return merged


def compress_to_swap_levels(
    systems: Iterable[PhysicalDrainageSystem],
    *,
    max_levels: int = 5,
) -> list[PhysicalDrainageSystem]:
    """Compress active physical systems to at most max_levels.

    Inactive systems are retained in lineage only when already merged upstream;
    standalone inactive inputs do not consume a SWAP level.

    Drain tubes are never merged. Open channels may only merge inside the same
    hydraulic class.
    """
    original = list(systems)
    if max_levels < 1:
        raise ValueError("max_levels must be positive")

    active = [s for s in original if s.active]
    inactive = [s for s in original if not s.active]

    pipe = [s for s in active if s.medium == "drain_tube"]
    if len(pipe) > max_levels:
        raise ValueError("more active drain-tube systems than available SWAP levels")

    work = active[:]
    while len(work) > max_levels:
        best = None
        best_key = None
        for i in range(len(work)):
            for j in range(i + 1, len(work)):
                cost = hydraulic_merge_cost(work[i], work[j])
                pair_lineage = tuple(sorted((work[i].source_ids, work[j].source_ids)))
                candidate_key = (cost, pair_lineage)
                if best_key is None or candidate_key < best_key:
                    best_key = candidate_key
                    best = (i, j)
        best_cost = float("inf") if best_key is None else best_key[0]
        if best is None or not isfinite(best_cost):
            classes = [(s.source_ids, s.hydraulic_class, s.medium) for s in work]
            raise ValueError(
                "cannot reduce to SWAP level limit without prohibited merge; "
                f"active={classes}"
            )
        i, j = best
        merged = merge_systems(work[i], work[j])
        work = [s for k, s in enumerate(work) if k not in {i, j}] + [merged]

    # Deterministic output ordering. Merge tie-breaks above are also canonical
    # on source lineage, so compression is independent of caller input order.
    work.sort(key=lambda s: (-s.dep, s.medium, s.source_ids))

    _validate_lineage(original, work, inactive)
    _validate_conductance_conservation(active, work)
    return work


def _validate_lineage(
    original: list[PhysicalDrainageSystem],
    compressed: list[PhysicalDrainageSystem],
    inactive: list[PhysicalDrainageSystem],
) -> None:
    expected = sorted(x for s in original if s.active for x in s.source_ids)
    actual = sorted(x for s in compressed for x in s.source_ids)
    if expected != actual:
        raise AssertionError(f"active source lineage changed: expected={expected}, actual={actual}")


def _validate_conductance_conservation(
    original_active: list[PhysicalDrainageSystem],
    compressed: list[PhysicalDrainageSystem],
) -> None:
    gd0 = sum(s.drainage_conductance for s in original_active)
    gd1 = sum(s.drainage_conductance for s in compressed)
    gi0 = sum(s.infiltration_conductance for s in original_active)
    gi1 = sum(s.infiltration_conductance for s in compressed)
    tol = 1e-12
    if abs(gd0 - gd1) > tol * max(1.0, abs(gd0)):
        raise AssertionError("drainage conductance not conserved")
    if abs(gi0 - gi1) > tol * max(1.0, abs(gi0)):
        raise AssertionError("infiltration conductance not conserved")
