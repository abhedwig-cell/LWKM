# P12 target architecture: incremental SWAP input production

## Scope

P12 is modernized as a dependency DAG. The first objective is operational decomposition and exact reproduction of current scientific semantics, not changing hydrological aggregation rules.

## Authorities

Upstream HRU/SVAT relations and LHM time series are scientific inputs.

P12 producers:
1. RUNS producer
   - HRU aggregate/static properties -> canonical run/datamodel records.
2. BBC producer
   - HRU bottom-boundary aggregate time series -> BBC products.
   - Historical reference: hrulist2SWAP qq(t), SWBOTB=2; separate mixed-boundary products where requested.
3. MET producer
   - HRU precipitation/evaporation plus district meteorology -> MET products.
4. DRA producer
   - HRU drainage characteristics/time series -> DRA products.
5. SWP renderer
   - canonical datamodel + named profile + generic template -> SWP.
6. Optional asset exporters
   - CRP/CO2/etc only where an explicit deployment requires materialized copies.

## Dependency isolation

Each product has its own semantic fingerprint. A change propagates only to dependent products.

Examples:
- bottom flux changes -> BBC only, unless a SWP switch/reference also changes;
- soil hydraulic parameters change -> SWP only;
- precipitation changes -> MET only;
- HRU identity/path policy changes -> deployment references, not scientific products;
- crop/rooting changes -> SWP and possibly crop asset, not BBC/MET.

## Historical first phase

Fortran hrulist2SWAP remains the scientific oracle for BBC/MET/DRA and Runs aggregation until each producer is independently qualified.

No physical formula is altered during decomposition.

## Admission gates per producer

- input contract documented;
- exact units/sign conventions documented;
- deterministic output;
- historical sample regression;
- national/full-set aggregate regression;
- changed-only regression;
- no writes outside requested product scope.

Only after these gates may a Python producer replace its Fortran counterpart.
