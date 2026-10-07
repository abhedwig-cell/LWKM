"""Fail-closed package guards for drainage level-index coupling.

The modern seven-to-five DRA route makes SWAP level numbers a serialization
detail. Any SWP feature that explicitly refers to a drainage level must bind
through physical source lineage after compression, never through a historical
hard-coded level number.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping


def resolve_lineage_level(
    levels: Iterable[Mapping],
    required_source_ids: Iterable[str],
) -> int:
    """Return the 1-based SWAP level containing all requested physical sources.

    Exactly one compressed level must contain the full requested lineage.
    """
    required=frozenset(str(x) for x in required_source_ids)
    if not required:
        raise ValueError("required_source_ids must not be empty")

    matches=[]
    for index,level in enumerate(levels,1):
        lineage=frozenset(str(x) for x in level.get("source_ids",()))
        if required.issubset(lineage):
            matches.append(index)

    if len(matches)!=1:
        raise ValueError(
            "cannot bind requested drainage lineage to exactly one SWAP level: "
            f"required={sorted(required)}, matches={matches}"
        )
    return matches[0]


def resolve_numlevrapdra(
    levels: Iterable[Mapping],
    *,
    swmacro: int | bool,
    swdrrap: int | bool,
    rapid_drainage_source_ids: Iterable[str] | None = None,
    configured_numlevrapdra: int | None = None,
) -> int | None:
    """Resolve/validate NUMLEVRAPDRA for a complete SWP+DRA package.

    When indexed rapid macropore drainage is inactive, no level binding is
    required. When it is active, the intended physical source lineage must be
    supplied and must resolve to exactly one post-compression SWAP level.
    """
    active=bool(swmacro) and bool(swdrrap)
    if not active:
        return None

    if rapid_drainage_source_ids is None:
        raise ValueError(
            "SWMACRO=1 and SWDRRAP=1 require explicit rapid-drainage source lineage"
        )

    level_list=list(levels)
    resolved=resolve_lineage_level(level_list,rapid_drainage_source_ids)

    if configured_numlevrapdra is not None and int(configured_numlevrapdra)!=resolved:
        raise ValueError(
            "configured NUMLEVRAPDRA does not match post-compression lineage: "
            f"configured={configured_numlevrapdra}, resolved={resolved}"
        )
    return resolved
