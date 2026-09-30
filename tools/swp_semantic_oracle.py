"""Semantic parser/comparator for realized SWAP .swp regression oracles.

This module ignores comments and formatting. It extracts active scalar
assignments plus datamodel-driven tables used by the direct-renderer gate.
It can also project a validated render context into the same semantic shape,
so datamodel binding can be qualified independently of template serialization.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any

ASSIGNMENT = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")

SCALAR_GATE_FIELDS = (
    "TSTART",
    "TEND",
    "METFIL",
    "SWETR",
    "SWINCO",
    "GWLI",
    "PONDMX",
    "RSRO",
    "RDS",
    "SWDRA",
    "DRFIL",
    "SWBBCFILE",
    "BBCFIL",
    "SWBOTB",
    "NUMNODNEW",
)

TABLE_HEADERS = {
    "crop_rotation": ("CROPSTART", "CROPEND", "CROPNAME", "CROPFIL", "CROPTYPE"),
    "soil_profile": ("ISUBLAY", "ISOILLAY", "HSUBLAY", "NCOMP"),
    "soil_hydraulics": (
        "ORES",
        "OSAT",
        "ALFA",
        "NPAR",
        "KSATFIT",
        "LEXP",
        "H_ENPR",
        "KSATEXM",
        "BDENS",
        "ELAS",
    ),
    "soil_textures": ("PSAND", "PSILT", "PCLAY", "ORGMAT"),
}


@dataclass(frozen=True)
class SemanticDifference:
    path: str
    expected: Any
    actual: Any


def _without_comment(line: str) -> str:
    """Remove active-line ! comments while respecting single quoted strings."""
    out = []
    in_quote = False
    for ch in line:
        if ch == "'":
            in_quote = not in_quote
            out.append(ch)
            continue
        if ch == "!" and not in_quote:
            break
        out.append(ch)
    return "".join(out).rstrip()


def _unquote(value: Any) -> Any:
    if isinstance(value,str):
        value=value.strip()
        if len(value)>=2 and value[0]==value[-1]=="'":
            return value[1:-1].replace("''","'")
    return value


def _atom(value: str) -> Any:
    value = _unquote(value.strip())
    if not isinstance(value,str):
        return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _row_atom(value: str) -> Any:
    return _atom(value)


def parse_scalars(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw in text.splitlines():
        stripped = raw.lstrip()
        if not stripped or stripped.startswith("*"):
            continue
        active = _without_comment(raw)
        m = ASSIGNMENT.match(active)
        if not m:
            continue
        key, value = m.groups()
        result[key.upper()] = _atom(value)
    return result


def _header_match(line: str, header: tuple[str, ...]) -> bool:
    tokens = tuple(line.strip().split())
    return tokens == header


def parse_table(text: str, header: tuple[str, ...]) -> list[dict[str, Any]]:
    lines = text.splitlines()
    start = None
    for i, raw in enumerate(lines):
        if _header_match(raw, header):
            start = i + 1
            break
    if start is None:
        return []

    rows: list[dict[str, Any]] = []
    for raw in lines[start:]:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("*"):
            if rows:
                break
            continue
        values = stripped.split()
        if len(values) != len(header):
            if rows:
                break
            continue
        rows.append(dict(zip(header, map(_row_atom, values))))
    return rows


def extract_semantics(text: str) -> dict[str, Any]:
    scalars = parse_scalars(text)
    return {
        "scalars": {k: scalars.get(k) for k in SCALAR_GATE_FIELDS},
        "tables": {name: parse_table(text, header) for name, header in TABLE_HEADERS.items()},
    }


def context_semantics(ctx:dict[str,Any])->dict[str,Any]:
    """Project a resolved render context into the regression-oracle schema."""
    scalars={
        "TSTART":ctx.get("TSTART"),
        "TEND":ctx.get("TEND"),
        "METFIL":_unquote(ctx.get("METFIL")),
        "SWETR":ctx.get("SWETR"),
        "SWINCO":ctx.get("SWINCO"),
        "GWLI":ctx.get("GWLI"),
        "PONDMX":ctx.get("PONDMX"),
        "RSRO":ctx.get("RSRO"),
        "RDS":ctx.get("RDS_effective",ctx.get("RDS")),
        "SWDRA":ctx.get("SWDRA"),
        "DRFIL":_unquote(ctx.get("DRFIL")),
        "SWBBCFILE":ctx.get("SWBBCFILE"),
        "BBCFIL":_unquote(ctx.get("BBCFIL")),
        "SWBOTB":ctx.get("SWBOTB"),
        "NUMNODNEW":ctx.get("NUMNODNEW"),
    }
    crop=[]
    for r in ctx.get("TABLE_CROPROTATION",[]):
        crop.append({
            "CROPSTART":r.get("CROPSTART"),
            "CROPEND":r.get("CROPEND"),
            "CROPNAME":_unquote(r.get("CROPNAME")),
            "CROPFIL":_unquote(r.get("CROPFIL")),
            "CROPTYPE":r.get("CROPTYPE"),
        })
    return {
        "scalars":scalars,
        "tables":{
            "crop_rotation":crop,
            "soil_profile":ctx.get("TABLE_SOILPROFILE",[]),
            "soil_hydraulics":ctx.get("TABLE_SOILHYDRFUNC",[]),
            "soil_textures":ctx.get("TABLE_SOILTEXTURES",[]),
        },
    }


def _numeric_equal(a: Any, b: Any, atol: float, rtol: float) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol)
    return a == b


def compare_semantics(
    expected: dict[str, Any],
    actual: dict[str, Any],
    *,
    atol: float = 1e-9,
    rtol: float = 1e-9,
) -> list[SemanticDifference]:
    diffs: list[SemanticDifference] = []

    e_scalars = expected.get("scalars", {})
    a_scalars = actual.get("scalars", {})
    for key in SCALAR_GATE_FIELDS:
        ev = e_scalars.get(key)
        av = a_scalars.get(key)
        if not _numeric_equal(ev, av, atol, rtol):
            diffs.append(SemanticDifference(f"scalars.{key}", ev, av))

    e_tables = expected.get("tables", {})
    a_tables = actual.get("tables", {})
    for name, header in TABLE_HEADERS.items():
        if name not in e_tables:
            continue
        erows = e_tables.get(name, [])
        arows = a_tables.get(name, [])
        if len(erows) != len(arows):
            diffs.append(SemanticDifference(f"tables.{name}.row_count", len(erows), len(arows)))
            continue
        for i, (erow, arow) in enumerate(zip(erows, arows)):
            for column in header:
                ev = erow.get(column)
                av = arow.get(column)
                if not _numeric_equal(ev, av, atol, rtol):
                    diffs.append(
                        SemanticDifference(f"tables.{name}[{i}].{column}", ev, av)
                    )
    return diffs


def compare_text(expected_text: str, actual_text: str, **kwargs) -> list[SemanticDifference]:
    return compare_semantics(
        extract_semantics(expected_text),
        extract_semantics(actual_text),
        **kwargs,
    )
