# P12 STATIC04 representative-SVAT dqsat result — 30 September 2026

Status:
**SOURCE-SIDE QUALIFIED; 49-RUN REALIZED DISCRIMINATION GATE PENDING**

## Question

Does the confirmed legacy ordering defect materially change dqsat when the intended schema-first rule is used?

Compared hypotheses:
- legacy: member BFE majority, then dqsat majority inside that BFE population;
- candidate: dqsat sampled directly at Piet's authoritative `svat_repr`.

No dqsat value was inferred from realized DRA `L`. Realized `L/4` remains an independent oracle only.

## Recovered authority

A previously uploaded `csv.zip` was recovered from Library and is raw-readable in the current runtime.

Raw archive:
- SHA-256: `84ae4963145176767a00c67b968ace5b817002d5292fd9cab8d3933476e509e3`.

Used archive members:

### HRU schema

`csv/export_HRUschema_10242.csv`
- rows: 10,242;
- columns: 36;
- SHA-256: `0ca8534216d1ab2944dcfee4c528926c7798fd967dcc58f760c88befd1c83997`;
- contains one unique `svat_repr` for every HRU.

This archived schema predates the later 43-column schema/copy reconciliation, but the repository reconciliation established that `svat_repr` is unchanged between original and `_copy`. Only `rz_repr`, `bfe_repr`, and `bodem_repr` were altered in the problematic copy. It is therefore sufficient authority for the representative-SVAT identity used here.

### SVAT to HRU relation

`csv/export_svat_HRU_NRU_10242.csv`
- rows: 427,656;
- SHA-256: `13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4`;
- contains `svat_orig`, `HRU`, `x`, `y`, and `bodem370_orig`.

The relation member count equals schema `N` for all 10,242 HRUs.

Every one of the 10,242 representative SVAT ids:
- occurs exactly once in the relation;
- belongs to the same HRU as its schema row.

Therefore no representative location was guessed or recomputed.

## Source raster

The complete numerical content of `grensvlak_NHIWQ_v2_fill.asc` was recovered as documented in:
`P12-DRA-R3-RASTER-RECOVERY-2026-09-30.md`.

Grid:
- 1200 x 1300;
- 250 m cell size;
- 1,560,000 cells;
- observed dqsat values: 0 and 2 through 20;
- no sampled `-9999` NODATA value in the recovered grid;
- semantic float64 array SHA-256:
  `79fdfc37153aea04a9ec24cef1b3d981f519aaed062f8c07e8922766bb3849cd`.

The x/y coordinates in the relation were converted only through the exact ESRI raster geometry. All 427,656 member coordinates land on exact cell centres and inside the raster.

## Exact legacy reconstruction

The supplied source semantics were reproduced literally:

1. read member BFE from the soil identity represented by `bodem370_orig`;
2. apply the supplied HRUlist2SWAP correction `204 -> 205`;
3. compute member BFE majority;
4. retain members whose BFE equals that majority;
5. compute dqsat majority on those retained source-raster values.

Tie behavior matches `Alterratools.f90`:
- values are sorted;
- the counter is replaced only on a strictly greater frequency;
- frequency ties therefore retain the lowest sorted value.

Reproducible implementation:
- `tools/compare_dqsat_authority.py`;
- `tests/test_compare_dqsat_authority.py`.

## Result

Across all 10,242 HRUs:

| class | HRUs | fraction |
| --- | ---: | ---: |
| legacy dqsat = representative-SVAT dqsat | 7,471 | 72.945% |
| different | 2,771 | 27.055% |

Direction among the 2,771 differences:
- representative dqsat greater than legacy: 1,357 HRUs;
- representative dqsat lower than legacy: 1,414 HRUs.

Magnitude:
- median absolute difference among discriminating HRUs: 4 cm;
- maximum absolute difference: 20 cm.

Because active DRA systems use `L = 4 * dqsat`, the corresponding spacing difference can be four times the dqsat difference where source length is positive.

This is not a corner case. The ordering defect changes the dqsat authority result for more than one quarter of the current 10,242 HRUs.

## Independent run-2000 check

Run 2000 remains non-discriminating:
- reconstructed legacy dqsat: 20;
- representative-SVAT dqsat: 20;
- historical `Runs.dqsat`: 20;
- realized active DRA systems have `L = 80`, hence `L/4 = 20`.

This is a useful propagation check, but it does not choose between the two authority semantics.

## Interpretation

The previous conclusion can now be strengthened.

The legacy sequence is not merely theoretically inconsistent. It produces a numerically different dqsat for 2,771 current HRUs when compared with the direct representative-SVAT value.

The intended production rule remains:

1. use source dqsat at Piet's authoritative representative SVAT when that value is accepted as valid;
2. if that value is unavailable or later judged invalid, use only a separately qualified richer fallback;
3. never use a new HRU majority;
4. never infer representative dqsat from realized `L/4`;
5. never reduce dqsat to a `bodem_id -> dqsat` lookup.

## Closure state

Qualified now:
- representative-SVAT identity for all 10,242 HRUs;
- exact source-cell mapping for those representative SVATs without `svat.asc`, using the persisted SVAT-HRU relation x/y;
- representative-SVAT dqsat for all 10,242 HRUs;
- exact supplied-source legacy majority-BFE dqsat reconstruction;
- full-population legacy versus representative comparison;
- material impact of the ordering defect.

Still pending before the DRA producer itself can be admitted:
- classify the 49 realized DRA cases against both predictions;
- require zero unexplained differences outside preregistered authority corrections;
- close nature/DRA4 discrimination separately.

Therefore:
**STATIC04_DQSAT_SOURCE_SIDE_QUALIFIED**.

Not yet:
**DIRECT_DRA_PRODUCER_ADMITTED**.
