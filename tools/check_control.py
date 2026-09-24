#!/usr/bin/env python3
"""Validate LWKM key=value control files against a source-bound schema."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


def parse_control(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    duplicates: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("!", "#", ";", "::", "REM ", "rem ")):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in result:
            duplicates.append(key)
        result[key] = value
    result["__duplicates__"] = duplicates
    return result


def required_keys(schema: dict) -> list[str]:
    keys = list(schema.get("required_parameters", []))
    for item in schema.get("dynamic_parameters", {}).get("patterns", {}).values():
        keys.extend(item.get("parameters", []))
    return keys


def path_like(key: str, value: str) -> bool:
    if key in {"DRA", "MET", "BOT", "TimStart", "TimEnd", "crunoff_par", "crunon_par", "MaxPondDepth", "tempCbotk", "kwelmax"}:
        return False
    if re.fullmatch(r"[-+]?\d+(\.\d+)?", value):
        return False
    return any(x in value for x in ("\\", "/", "."))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--schema", type=Path, required=True)
    ap.add_argument("--base-dir", type=Path, default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    ns = ap.parse_args()

    schema = yaml.safe_load(ns.schema.read_text(encoding="utf-8"))
    control = parse_control(ns.control)
    duplicates = control.pop("__duplicates__", [])

    required = required_keys(schema)
    missing = [k for k in required if k not in control or control[k] == ""]
    extra = sorted(k for k in control if k not in required)

    missing_files = []
    if ns.base_dir is not None:
        for key, value in control.items():
            if not path_like(key, value):
                continue
            p = Path(value)
            if not p.is_absolute():
                p = ns.base_dir / p
            if not p.exists():
                missing_files.append({"key": key, "value": value, "resolved": str(p)})

    result = {
        "program": schema.get("program"),
        "source_version": schema.get("source_version"),
        "control": str(ns.control),
        "parameter_count": len(control),
        "required_count": len(required),
        "missing_parameters": missing,
        "extra_parameters": extra,
        "duplicate_parameters": duplicates,
        "missing_files": missing_files,
        "status": "PASS" if not missing and not duplicates and not missing_files else "FAIL",
    }

    print(json.dumps(result, indent=2))
    if ns.json_out:
        ns.json_out.parent.mkdir(parents=True, exist_ok=True)
        ns.json_out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
