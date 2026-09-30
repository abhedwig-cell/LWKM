"""Build and validate the canonical bodem370 classification lookup."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

FIELDS=("bofek79","pawn21","grondsoort4","grondsoort2")
KNOWN_CORRECTIONS={
  78:(40,39),79:(39,40),81:(39,44),82:(44,39),94:(31,28),
  95:(28,31),147:(46,41),148:(41,46),170:(44,39),171:(39,44),
}
UNOBSERVED={14,142,143,197,198}


def build(realized_csv:Path, reference_csv:Path|None=None):
    combos=defaultdict(set)
    with realized_csv.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            b=int(r["bodem370"])
            combos[b].add(tuple(int(r[k]) for k in FIELDS))
    bad={b:v for b,v in combos.items() if len(v)!=1}
    if bad:
        raise ValueError(f"non-deterministic realized soil mapping: {bad}")

    ref={}
    if reference_csv:
        with reference_csv.open(newline="",encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                b=int(r.get("bodem370",r.get("bodem",r.get("code"))))
                v=int(r.get("bofek79",r.get("bofek2020",r.get("bofek"))))
                ref[b]=v

    rows=[]
    for b in range(1,371):
        if b in combos:
            bo,p21,g4,g2=next(iter(combos[b]))
            rv=ref.get(b)
            rows.append(dict(
                bodem370=b,bofek79=bo,pawn21=p21,grondsoort4=g4,grondsoort2=g2,
                source="REALIZED_SVAT_INFO",
                reference_bofek=rv if rv is not None else "",
                differs_from_reference=(rv is not None and rv!=bo),
                status="QUALIFIED_REALIZED",
            ))
        else:
            rows.append(dict(
                bodem370=b,bofek79="",pawn21="",grondsoort4="",grondsoort2="",
                source="NONE",reference_bofek=ref.get(b,""),
                differs_from_reference="",
                status="UNOBSERVED_IN_REALIZED_POPULATION",
            ))
    return rows


def read(path:Path):
    with Path(path).open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def validate(rows):
    if len(rows)!=370:
        raise AssertionError(("unexpected row count",len(rows)))

    observed={
        int(r["bodem370"]):r
        for r in rows
        if r["status"]=="QUALIFIED_REALIZED"
    }
    missing={
        int(r["bodem370"])
        for r in rows
        if r["status"]!="QUALIFIED_REALIZED"
    }
    if missing!=UNOBSERVED:
        raise AssertionError(("unexpected unobserved codes",missing))
    if len(observed)!=365:
        raise AssertionError(("unexpected observed code count",len(observed)))

    for b,(realized,reference) in KNOWN_CORRECTIONS.items():
        if int(observed[b]["bofek79"])!=realized:
            raise AssertionError((b,observed[b],realized))
        rv=observed[b]["reference_bofek"]
        if rv!="" and int(rv)!=reference:
            raise AssertionError((b,rv,reference))

    tuples={}
    for b,r in observed.items():
        tup=tuple(int(r[k]) for k in FIELDS)
        tuples[b]=tup
    if len(tuples)!=365:
        raise AssertionError("non-unique observed lookup keys")
    return True


def write(rows,out:Path):
    fields=(
        "bodem370","bofek79","pawn21","grondsoort4","grondsoort2","source",
        "reference_bofek","differs_from_reference","status",
    )
    with Path(out).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
