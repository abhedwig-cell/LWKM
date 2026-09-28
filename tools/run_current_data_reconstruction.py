#!/usr/bin/env python3
"""
Run the current LWKM five-stage reconstruction directly from the shared ZIP archives.

This wrapper:
1. locates the required members in csv.zip and LHM2SWAP.zip;
2. extracts only those members to a temporary/staging directory;
3. records archive member names, sizes and SHA-256 checksums;
4. rewrites the QA config to absolute staged paths;
5. runs tools/qa_lhm_hru_swap.py.

No scientific values are changed by this wrapper.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable


CURRENT_REQUIRED = {
    "svat_table": "SVAT_INFO_HRU.CSV",
    "svat_hru_map": "export_svat_HRU_NRU_10242.csv",
    "hru_schema": "export_HRUschema_10242.csv",
    "nru_schema": "export_NRUschema_10242.csv",
    "hruafv": "HRUAFV.CSV",
}

BASE_SUFFIX_CANDIDATES = [
    "LHM4.3 data 2024/SVAT_INFO.CSV",
    "LHM4.3 data/SVAT_INFO.CSV",
    "SVAT_INFO.CSV",
]

OPTIONAL_HISTORICAL_SUFFIXES = {
    "svat_historical": "analyses/svat.csv",
    "svat_cor_historical": "analyses/svat_cor.csv",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_zip_name(name: str) -> str:
    return name.replace("\\", "/").lstrip("./")


def exact_basename_member(zf: zipfile.ZipFile, basename: str) -> str:
    matches = [
        n for n in zf.namelist()
        if not n.endswith("/") and Path(normalize_zip_name(n)).name.casefold() == basename.casefold()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one archive member named {basename!r}; found {len(matches)}: {matches[:20]}"
        )
    return matches[0]


def suffix_member(zf: zipfile.ZipFile, suffixes: Iterable[str], required: bool = True) -> str | None:
    names = [n for n in zf.namelist() if not n.endswith("/")]
    for suffix in suffixes:
        s = normalize_zip_name(suffix).casefold()
        matches = [n for n in names if normalize_zip_name(n).casefold().endswith(s)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            # Prefer the shortest path if a generic suffix has multiple matches.
            matches = sorted(matches, key=lambda x: (len(normalize_zip_name(x)), normalize_zip_name(x)))
            return matches[0]
    if required:
        raise RuntimeError(f"No archive member matched suffix candidates: {list(suffixes)}")
    return None


def extract_member(zf: zipfile.ZipFile, member: str, target: Path) -> dict:
    target.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(member) as src, target.open("wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    info = zf.getinfo(member)
    return {
        "archive_member": normalize_zip_name(member),
        "compressed_size": int(info.compress_size),
        "uncompressed_size": int(info.file_size),
        "staged_path": str(target),
        "sha256": sha256_file(target),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-zip", type=Path, required=True)
    ap.add_argument("--lhm2swap-zip", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("config/qa/HRU10242-current.json"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--keep-staging", action="store_true")
    ns = ap.parse_args()

    ns.out.mkdir(parents=True, exist_ok=True)
    base_cfg = json.loads(ns.config.read_text(encoding="utf-8"))

    temp_ctx = None
    if ns.keep_staging:
        staging = ns.out / "_staging"
        staging.mkdir(parents=True, exist_ok=True)
    else:
        temp_ctx = tempfile.TemporaryDirectory(prefix="lwkm-five-stage-")
        staging = Path(temp_ctx.name)

    inventory = {
        "csv_zip": {
            "path": str(ns.csv_zip),
            "sha256": sha256_file(ns.csv_zip),
            "members": {},
        },
        "lhm2swap_zip": {
            "path": str(ns.lhm2swap_zip),
            "sha256": sha256_file(ns.lhm2swap_zip),
            "members": {},
        },
    }

    with zipfile.ZipFile(ns.csv_zip) as zf:
        for key, basename in CURRENT_REQUIRED.items():
            member = exact_basename_member(zf, basename)
            target = staging / "current" / basename
            inventory["csv_zip"]["members"][key] = extract_member(zf, member, target)

    with zipfile.ZipFile(ns.lhm2swap_zip) as zf:
        member = suffix_member(zf, BASE_SUFFIX_CANDIDATES, required=True)
        target = staging / "base" / "SVAT_INFO.CSV"
        inventory["lhm2swap_zip"]["members"]["svat_base_table"] = extract_member(zf, member, target)

        for key, suffix in OPTIONAL_HISTORICAL_SUFFIXES.items():
            member = suffix_member(zf, [suffix], required=False)
            if member:
                target = staging / "historical" / Path(suffix).name
                inventory["lhm2swap_zip"]["members"][key] = extract_member(zf, member, target)

    cfg = dict(base_cfg)
    cfg["data_root"] = "."
    cfg["inputs"] = dict(base_cfg["inputs"])
    cfg["inputs"]["svat_base_table"] = str(staging / "base" / "SVAT_INFO.CSV")
    cfg["inputs"]["svat_table"] = str(staging / "current" / "SVAT_INFO_HRU.CSV")
    cfg["inputs"]["svat_hru_map"] = str(staging / "current" / "export_svat_HRU_NRU_10242.csv")
    cfg["inputs"]["hru_schema"] = str(staging / "current" / "export_HRUschema_10242.csv")

    effective_cfg = ns.out / "effective-HRU10242-current.json"
    effective_cfg.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    (ns.out / "archive-inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")

    qa_script = Path(__file__).with_name("qa_lhm_hru_swap.py")
    cmd = [sys.executable, str(qa_script), "--config", str(effective_cfg), "--out", str(ns.out)]
    subprocess.run(cmd, check=True)

    if temp_ctx is not None:
        temp_ctx.cleanup()

    print(f"Five-stage QA written to {ns.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
