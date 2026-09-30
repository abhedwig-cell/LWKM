# P12 DRA realized reproduction gate status

Available source inputs:
- five system conductance families;
- primary/secondary/tertiary infiltration-factor families;
- drainage bottom/level families supplied in drn/regionaal/steady_state archives;
- 49 realized .dra oracle files;
- HRU membership.

Still missing as directly readable source rasters:
- BasicData/grids/ahn_f250_m.asc (glk);
- BasicData/grids/grensvlak_NHIWQ_v2_fill.asc (dqsat).

Consequences:
- DRARES can be independently reconstructed now.
- INFRES can be independently reconstructed now where factor inputs are available; systems 4/5 are expected 100000 because source sets inf=0.
- ZBOTDR and LEVEL need glk for exact reproduction.
- L uses dqsat_maj*4 in current source and therefore needs dqsat plus majority semantics.

Do not infer missing grids from realized output for admission. That would make the validation circular.
