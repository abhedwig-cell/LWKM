# Five-stage hydrological comparison design

Status: **DRAFT AUTHORITY**

## Purpose

The core communication and QA question is not only whether the final HRU representation is acceptable, but **which transformation step causes which hydrological change**.

For the current LWKM 2.0 line this is reduced to five directly comparable stages. A purely technical spatial clip is separated from the scientifically relevant agriculture+nature domain selection.

## Stage sequence

### S0 — SVAT Netherlands baseline

Population:
- original LHM/SVAT hydrology;
- foreign cells removed;
- large/open water areas outside the relevant national modelling domain removed;
- **no agriculture+nature selection yet**;
- no Flevoland hydrological correction;
- no extreme-value replacement.

Target product:
`SVAT_NL_BASE.csv`

This is the national hydrological baseline after only the agreed technical/spatial trimming.

### S1 — SVAT agriculture + nature

Same hydrological values as S0, but the population is reduced to the LWKM agriculture+nature domain.

Target product:
`SVAT_LBN.csv`

Comparison:
`S1 - S0` = **agriculture+nature domain-selection effect**.

This effect is scientifically relevant and must be shown explicitly. It is not treated as mere ballast removal.

### S2 — SVAT + Flevoland correction

Same SVAT keys, same schema and same domain as S0.

Only the accepted Flevoland hydrological correction is applied.

Target product:
`SVAT_FLEVOLAND_CORR.csv`

The correction may include more than kwel if the alternative LHM run shows that associated drainage/ontwatering or other balance terms must change consistently.

Comparison:
`S2 - S1` = **Flevoland correction effect**.

### S3 — SVAT + extreme/outlier policy

Same SVAT keys, same schema and same domain as S2.

Hydrologically implausible/extreme SVAT values are treated according to an explicit, versioned policy. If replacement by donor/other SVAT is used, target/source and replaced variables must be recorded.

Target product:
`SVAT_QUALIFIED_REP.csv`

Comparison:
`S3 - S2` = **extreme/outlier treatment effect**.

This effect must not include the Flevoland correction, because that was already applied in S2.

### S4 — HRU10242 representation

The HRU derivation is based on S3.

Required products:
- `SVAT_HRU_MAP.csv`;
- `HRU_SCHEMA.csv`;
- HRU-level hydrological representation.

For one-to-one comparison with S3, HRU-level hydrological values must be **back-projected to the original SVAT domain**:

`SVAT -> HRU -> HRU value assigned back to each member SVAT`.

Target comparison product:
`SVAT_HRU10242_BACKPROJECTED.csv`

It must contain the same SVAT keys and comparable hydrological columns as S2.

Comparison:
`S4_backprojected - S3` = **pure HRU representation effect**.

This is the quantity that can be communicated as hydrological information change/loss caused by going from roughly 400k SVATs to about 10k HRUs.

## Why back-projection is essential

A national HRU total can look good while local HRU errors compensate each other.

By mapping the HRU representation back to every original SVAT location, S3 and S4 have:
- identical spatial support;
- identical SVAT keys;
- identical weighting basis.

This allows:
- national balance comparison;
- regional balance comparison;
- maps of local error;
- distributions of absolute/relative error;
- identification of regions where aggregation error becomes unacceptable.

## Required comparison outputs

For each transition:

1. S0 → S1: agriculture+nature domain selection;
2. S1 → S2: Flevoland correction;
3. S2 → S3: extreme/outlier treatment;
4. S3 → S4: HRU representation.

Report for each relevant water-balance variable:

- area-weighted national total/mean before and after;
- absolute and relative delta;
- MAE;
- RMSE;
- P01/P50/P99 of local differences;
- maximum absolute difference;
- affected area;
- regional summaries;
- spatial map of delta.

## Attribution rule

The effects must be **incremental**, not cumulative.

Therefore:

```text
TOTAL CHANGE S0 → S4
  =
  agriculture+nature selection effect (S0 → S1)
+ Flevoland effect                   (S1 → S2)
+ extreme-policy effect              (S2 → S3)
+ HRU effect                         (S3 → S4)
```

For additive balance quantities, this decomposition should close numerically subject to rounding and any explicitly documented non-linear transformations.

## Regional analysis

National averages are not sufficient.

Every comparison should support aggregation by a stable regional key, for example:
- water-management region;
- LHM district;
- province;
- agricultural region;
- other agreed reporting areas.

The regional system itself must be versioned and kept identical across the four stages.

The purpose is to identify:
- areas where the national effect is concentrated;
- compensation of positive/negative local errors;
- regions where HRU representation is insufficient even if the national balance is good.

## Communication to Deltares

The analysis should explicitly separate:

**LHM/source corrections**
- Flevoland correction;
- treatment of implausible/extreme LHM results.

from:

**LWKM schematisation effect**
- HRU aggregation/representation.

The key communication result is therefore not only the final LHM-versus-HRU difference, but the attribution:

> Which part of the final change is caused by correcting the LHM source data, and which part is caused by reducing the spatial representation to HRUs?

## Minimum data requirement

The analysis can be performed cleanly when these five comparable products exist:

1. `SVAT_NL_BASE.csv`
2. `SVAT_LBN.csv`
3. `SVAT_FLEVOLAND_CORR.csv`
4. `SVAT_QUALIFIED_REP.csv`
5. `SVAT_HRU10242_BACKPROJECTED.csv`

All five must use:
- the same SVAT key;
- the same domain;
- the same column names;
- the same units;
- the same period;
- the same area basis.

The separate `SVAT_HRU_MAP` and `HRU_SCHEMA` remain required provenance products for stage 4.
