# Donor assignment authority

## Donor eligibility

Only SVATs in accepted post-clustering clusters (df_res) are donors for donor rounds 1 and 2.

Targets are:
- unresolved clustering remainder;
- clusters removed by the minimum NRU-size check;
- the complete suspicious set df_suspected.

Therefore suspicious SVATs cannot themselves become donor SVATs in the two historical nearest-neighbour rounds.

## Round 1

Grouping constraint: exact LDGB x lu4.

A subgroup is matched only when at least 4 donors are available.

Weighted feature space:
- grondsoort2: 250
- grondsoort4: 100
- pawn21 rank: 10
- Gt: 0.5
- kwelklasse4: 0.5
- GHG: 0.01
- NettoKwel: 0.01

Historical R implementation multiplies each feature by sqrt(weight) and calls RANN::nn2. This is weighted Euclidean nearest-neighbour distance.

## Round 2

Grouping constraint: exact LDGB x lu2.

Minimum donor pool: 2.

Same feature weights plus:
- codelu4: 250

## Remaining targets

Targets still unmatched after round 2 become HRUextra, grouped by LDGB, lu4, grondsoort4 and Gt. The documentation says the donor is selected from the largest subgroup. The exact subgroup/tie rule remains source-unbound and must not be guessed in the historical compatibility path.

## Important identities

Cluster donor and final representative SVAT are different concepts.

The cluster donor assigns an individual target to an existing HRU and supplies donor attributes in df_complete.

The final HRU representative SVAT is selected later from HRU donor values using hierarchical categorical matching followed by a GHG/NettoKwel medoid rule.
