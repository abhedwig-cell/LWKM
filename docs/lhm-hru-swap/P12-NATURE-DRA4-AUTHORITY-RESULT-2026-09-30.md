# P12 nature / DRA4 authority result — 30 September 2026

Status:
**SOURCE-SIDE CLOSED; CURRENT POPULATION NON-DISCRIMINATING FOR DRA4 NATURE SHUTDOWN**

## Question

HRUlist2SWAP v0.38 computes the nature flag before Piet's representative-SVAT land-use override.

Supplied-source sequence:
1. compute legacy HRU land-use as member `landgebruik22` majority;
2. set `isnatuur = true` when `10 < lgn < 21` and `lgn != 18`;
3. later replace final `lgn_maj` by land use of Piet's `svat_repr`;
4. do not recompute `isnatuur`;
5. system 4 is disabled when `isnatuur` is true, independently of the representative land-use value later written to Runs/SWP.

This is an ordering defect in the supplied source.

The question here is whether the defect changes the boolean DRA4 nature decision in the current 10,242-HRU population.

## Authority and inputs

Representative-SVAT authority:
- `csv/export_HRUschema_10242.csv`;
- 10,242 HRUs;
- one unique `svat_repr` per HRU.

Membership authority:
- `csv/export_svat_HRU_NRU_10242.csv`;
- 427,656 SVAT members;
- exact HRU membership.

Source land use:
- `csv/SVAT_INFO_HRU.CSV`;
- field `landgebruik22`;
- all 427,656 member SVATs resolve;
- all 10,242 representative SVATs resolve.

No realized DRA output is used to construct either hypothesis.

## Exact legacy reconstruction

For every HRU:
1. join all member SVATs to source `landgebruik22`;
2. compute `MAJORITY` with the supplied Alterratools tie semantics, where the lowest sorted value wins a frequency tie;
3. apply the exact source nature predicate:
   `lgn > 10 and lgn < 21 and lgn != 18`.

Schema-first candidate:
1. take the source `landgebruik22` of authoritative `svat_repr`;
2. apply the same nature predicate.

Implementation:
- `tools/compare_nature_authority.py`;
- `tests/test_compare_nature_authority.py`.

## Result

Across all 10,242 HRUs:

| comparison | HRUs |
| --- | ---: |
| legacy land-use code = representative land-use code | 8,268 |
| legacy land-use code != representative land-use code | 1,974 |
| legacy nature flag = representative nature flag | 10,242 |
| legacy nature flag != representative nature flag | **0** |

Nature counts:
- legacy `isnatuur = true`: 2,825 HRUs;
- representative-SVAT `isnatuur = true`: 2,825 HRUs.

The 1,974 land-use-code differences split as:
- 1,107 non-nature -> non-nature;
- 867 nature -> nature.

Therefore the source ordering defect is real, but the current HRU population does not contain a case where it changes the boolean nature classification that controls the system-4 shutdown.

## Interpretation

This is stronger than the earlier run-2000 observation.

Run 2000 was individually non-discriminating. The full source population now shows that **all 10,242 HRUs are non-discriminating for the nature boolean**, even though 1,974 HRUs differ in the exact legacy versus representative land-use code.

Hence a 49-run realized oracle is not required to decide the authority correction for the current population:
- recomputing nature from the authoritative representative-SVAT land use is still the correct schema-first design;
- for the current 10,242 HRUs it produces the same `isnatuur` boolean as supplied-source legacy behavior;
- therefore this correction should not itself produce a DRA4 realized difference in the current population.

A future population can still discriminate. The modern producer must not preserve the legacy ordering merely because the present population is non-discriminating.

## DRA4 consequence

The system-4 repair condition remains:

`drnres4 > 20000 OR is_nature`.

The nature term can now be treated as a zero-expected-difference authority correction for the current 10,242-HRU population.

Any realized 49-run system-4 difference therefore cannot be explained by the legacy-versus-representative nature flag for this population. It must trace to another DRA input, aggregation rule, executable provenance issue, or an unexplained defect.

## Closure

Classification:

**STATIC_NATURE_ORDERING_DEFECT_CONFIRMED_CURRENT_POPULATION_NON_DISCRIMINATING**

and:

**DRA4_NATURE_SOURCE_SIDE_CLOSED**

Still pending for direct DRA producer admission:
- raw 49-run realized DRA oracle;
- numeric DRARES / INFRES / ZBOTDR / LEVEL / SWALLO regression;
- STATIC04 dqsat realized discrimination for the 49 supplied cases.

