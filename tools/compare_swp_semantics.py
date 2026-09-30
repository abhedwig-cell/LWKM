#!/usr/bin/env python3
"""Compare a candidate SWP file against a semantic oracle.

Exit status:
0 = no semantic differences in the qualified gate fields/tables
1 = semantic differences found
2 = invalid input/oracle
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.swp_semantic_oracle import compare_semantics, extract_semantics


def _load_oracle(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "scalars" not in data or "tables" not in data:
        raise ValueError("oracle JSON must contain scalars and tables")
    return {"scalars": data["scalars"], "tables": data["tables"]}


def compare_candidate(candidate: Path, oracle: Path, *, atol: float = 1e-9, rtol: float = 1e-9):
    actual = extract_semantics(candidate.read_text(encoding="utf-8", errors="replace"))
    expected = _load_oracle(oracle)
    return compare_semantics(expected, actual, atol=atol, rtol=rtol)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="compare-swp-semantics")
    p.add_argument("candidate", type=Path)
    p.add_argument("oracle", type=Path)
    p.add_argument("--atol", type=float, default=1e-9)
    p.add_argument("--rtol", type=float, default=1e-9)
    a = p.parse_args(argv)
    try:
        diffs = compare_candidate(a.candidate, a.oracle, atol=a.atol, rtol=a.rtol)
    except Exception as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, indent=2))
        return 2
    payload = {
        "status": "match" if not diffs else "different",
        "difference_count": len(diffs),
        "differences": [
            {"path": d.path, "expected": d.expected, "actual": d.actual}
            for d in diffs
        ],
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if not diffs else 1


if __name__ == "__main__":
    raise SystemExit(main())
