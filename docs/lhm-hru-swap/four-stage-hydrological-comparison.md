# Four-stage hydrological comparison design

Status: **DRAFT AUTHORITY**

## Purpose

The core communication and QA question is not only whether the final HRU representation is acceptable, but **which transformation step causes which hydrological change**.

For the current LWKM 2.0 line this is reduced to four directly comparable stages.

## Stage sequence

### S0 — SVAT original

Population:
- within the Netherlands;
- agriculture + nature only;
- no Flevoland hydrological correction;
- no extreme-value replacement;
- original LHM/SVAT hydrology.

Target product:
`SVAT_ORIGINAL_LBN.csv`

This is the clean baseline for the comparison.

### S1 — SVAT + Flevoland correction

Same SVAT keys, same schema and same domain as S0.

Only the accepted Flevoland hydrological correction is applied.

Target product:
`SVAT_FLEVOLAND_CORR.csv`

The correction may include more than kwel if the alternative LHM run shows that associated drainage/ontwatering or other balance terms must change consistently.

Comparison:
`S1 - S0` = **Flevoland correction effect**.

### S2 — SVAT + extreme/outlier policy

Same SVAT keys, same schema and same domain as S1.

Hydrologically implausible/extreme SVAT values are treated according to an explicit, versioned policy. If replacement by donor/other SVAT is used, target/source and replaced variables must be recorded.

Target product:
`SVAT_QUALIFIED_REP.csv`

Comparison:
`S2 - S1` = **extreme/outlier treatment effect**.

This effect must not include the Flevoland correction, because that was already applied in S1.

### S3 — HRU10242 representation

The HRU derivation is based on S2.

Required products:
- `SVAT_HRU_MAP.csv`;
- `HRU_SCHEMA.csv`;
- HRU-level hydrological representation.

For one-to-one comparison with S2, HRU-level hydrological values must be **back-projected to the original SVAT domain**:

`SVAT -> HRU -> HRU value assigned back to each member SVAT`.

Target comparison product:
`SVAT_HRU10242_BACKPROJECTED.csv`

It must contain the same SVAT keys and comparable hydrological columns as S2.

Comparison:
`S3_backprojected - S2` = **pure HRU representation effect**.

This is the quantity that can be communicated as hydrological information change/loss caused by going from roughly 400k SVATs to about 10k HRUs.

## Why back-projection is essential

A national HRU total can look good while local HRU errors compensate each other.

By mapping the HRU representation back to every original SVAT location, S2 and S3 have:
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

1. S0 → S1: Flevoland correction;
2. S1 → S2: extreme/outlier treatment;
3. S2 → S3: HRU representation.

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
TOTAL CHANGE S0 → S3
  =
  Flevoland effect      (S0 → S1)
+ extreme-policy effect (S1 → S2)
+ HRU effect            (S2 → S3)
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

The analysis can be performed cleanly when these four comparable products exist:

1. `SVAT_ORIGINAL_LBN.csv`
2. `SVAT_FLEVOLAND_CORR.csv`
3. `SVAT_QUALIFIED_REP.csv`
4. `SVAT_HRU10242_BACKPROJECTED.csv`

All four must use:
- the same SVAT key;
- the same domain;
- the same column names;
- the same units;
- the same period;
- the same area basis.

The separate `SVAT_HRU_MAP` and `HRU_SCHEMA` remain required provenance products for stage 4.
