"""Resolve the 29 blocked Work C2 HRU checkpoints into real DRA files.

Do not reconstruct from reduced protected-partition-diagnostics.json.
Uses the authoritative full retained_physical from immutable Work C2 checkpoints
and original, already serialized SWP files. Existing 10,213 DRA bytes are never
touched. This is an executable on-site/local recovery step, not scientific admission.
"""
from __future__ import annotations
import argparse
from dataclasses import fields
import json
from pathlib import Path
from tools.dra_level_compression import PhysicalDrainageSystem, to_render_level
from tools.w07_autofive_full_records import solve
from tools.generate_dra import render_dra_explicit
from tools.swp_full_oracle import parse_named_table
from tools.swp_template_adapter import TABLE_HEADERS
from tools.assemble_swap_package import sha256
from tools.run_dra_protected_population import atomic_json


def from_record(x):
    allowed={f.name for f in fields(PhysicalDrainageSystem)}
    record={k:v for k,v in x.items() if k in allowed}
    record["source_ids"]=tuple(record["source_ids"])
    if record.get("level_series") is not None:
        record["level_series"]=tuple((str(d),float(v)) for d,v in record["level_series"])
    record["merge_history"]=tuple(record.get("merge_history") or ())
    return PhysicalDrainageSystem(**record)


def run(checkpoints,swps,old_dra,output,*,start_year=1971,end_year=1972):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    paths=sorted((Path(checkpoints)/"hrus").glob("*.json"),key=lambda p:int(p.stem))
    if not paths: raise ValueError("no Work C2 full checkpoints found")
    blocked=0
    for path in paths:
        row=json.loads(path.read_text())
        hid=int(row["hru"])
        if row["status"]!="BLOCKED":
            rows.append(dict(hru=hid,status="UNCHANGED_EXISTING"))
            continue
        blocked+=1
        report=dict(hru=hid,status="ERROR")
        try:
            if not row.get("retained_physical"):
                raise ValueError("missing complete retained_physical checkpoint")
            source=[from_record(x) for x in row["retained_physical"]]
            levels,audit=solve(source)
            if not (1<=len(levels)<=5):
                raise ValueError("five-level selection invalid")
            render=[to_render_level(x) for x in levels]
            swp=Path(swps)/f"run_{hid:05d}"/"swap.swp"
            n=len(parse_named_table(swp.read_text(),TABLE_HEADERS["TABLE_SOILHYDRFUNC"]))
            if n<=0: raise ValueError("no SWP soil profile")
            text=render_dra_explicit(render,n,start_year,end_year,0.)
            dest=output/f"{hid}.dra"
            data=text.encode()
            if dest.exists() and dest.read_bytes()!=data:
                raise ValueError("existing recovery DRA differs: choose new output directory")
            if not dest.exists():
                tmp=dest.with_suffix(".partial")
                tmp.write_bytes(data)
                tmp.replace(dest)
            report.update(status="DRA_SERIALIZED_APPROXIMATE_NOT_ADMITTED",
                source_checkpoint_sha256=sha256(path),swp_sha256=sha256(swp),
                sha256=sha256(dest),path=str(dest.resolve()),
                original_levels=len(source),represented_levels=len(levels),
                audit=audit)
        except (ValueError,AssertionError,KeyError,TypeError,FileNotFoundError) as exc:
            report["error"]=str(exc)
        rows.append(report)
    # Existing files are not copied, edited, or regenerated. Explicitly
    # fingerprint the existing population so a release step can prove identity.
    original=sorted(Path(old_dra).glob("*.dra"))
    existing={p.stem:sha256(p) for p in original}
    generated=[r for r in rows if r["status"]=="DRA_SERIALIZED_APPROXIMATE_NOT_ADMITTED"]
    conflicts=sorted(set(existing)&{str(r["hru"]) for r in generated})
    if conflicts: raise ValueError("blocked IDs already exist in qualified DRA area: "+",".join(conflicts))
    summary=dict(schema_version=1,status="RESEARCH_DRA_NOT_ADMITTED",
        checkpoint_population=len(paths),original_existing=len(existing),
        blocked_count=blocked,generated_count=len(generated),
        unresolved_count=sum(x["status"]=="ERROR" for x in rows),
        total_dra_candidates=len(existing)+len(generated),
        original_sha256=existing,rows=rows)
    atomic_json(output/"w07-29-build-status.json",summary)
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("checkpoints","swps","old-dra","output"):
        p.add_argument("--"+key,required=True,type=Path)
    p.add_argument("--start-year",type=int,default=1971)
    p.add_argument("--end-year",type=int,default=1972)
    a=p.parse_args()
    r=run(a.checkpoints,a.swps,a.old_dra,a.output,
          start_year=a.start_year,end_year=a.end_year)
    print(json.dumps({k:r[k] for k in ("checkpoint_population","blocked_count",
        "generated_count","unresolved_count","total_dra_candidates")}))
    raise SystemExit(1 if r["unresolved_count"] or r["total_dra_candidates"]!=r["checkpoint_population"] else 0)
