# HRU R-to-canonical regression gate

The historical R implementation remains the numerical partition authority until a candidate engine passes this gate.

## Required comparison

Run the historical bound source and candidate engine on the exact same immutable input manifest.

Compare:

1. SVAT universe;
2. HRU count and NRU count;
3. HRU partition as sets of SVAT member sets, ignoring numeric HRU labels;
4. per-SVAT aggregation/assignment route;
5. rest/donor route counts;
6. representative SVAT relation;
7. GHG and NettoKwel backprojection metrics;
8. categorical purity distributions.

A matching HRU count alone is insufficient.

## Acceptance levels

- STRUCTURE_ONLY: counts and SVAT universe match.
- PARTITION_EQUIVALENT: every HRU member set matches label-invariantly.
- SCIENTIFIC_EQUIVALENT: partition may differ, but preregistered hydrological and categorical tolerances pass.
- HISTORICAL_EXACT: partition, routes, representative relations and safe derived outputs match.

Initial replacement target is HISTORICAL_EXACT where the historical behaviour is well-defined. Known historical defects or ambiguous artifacts are excluded from exactness and handled by explicit candidate policies.

The comparator is implemented in tools/compare_hru_partitions.py.
