# LHM upstream run qualification for LWKM

## Scope boundary

The LHM/MODFLOW run is an upstream product.

LWKM is NOT responsible for:
- restart mechanics between MODFLOW sub-runs;
- reproducing those restart transitions;
- certifying MODFLOW numerical correctness.

LWKM IS responsible for refusing an incomplete or evidently failed upstream run as source authority.

## Gate levels

### Q0 CONFIGURED
Control files are present and parseable.

### Q1 PERIOD_COMPLETE
The control-file set covers the intended simulation period without unexplained gaps or overlaps.

### Q2 OUTPUT_COMPLETE
For every required period, the outputs consumed by LWKM exist:
- MODFLOW layer-1 head outputs needed by downstream producers;
- required MetaSWAP/SVAT periodic output;
- any explicitly declared producer source.

### Q3 EXECUTION_EVIDENCE
Where available:
- process exit status/log indicates success;
- expected final timestamp/output exists;
- no fatal/error marker;
- no zero-byte/truncated required outputs.

### Q4 LWKM_SOURCE_QUALIFIED
Q0-Q3 pass and source bundle hashes successfully.

Qualification is execution/provenance qualification, not an independent hydrological validation of LHM.

## Optional stronger checks

Useful when inexpensive:
- compare first/last timestamp against requested period;
- sanity range checks on head grids;
- count expected head snapshots;
- verify grid geometry/extent remains consistent;
- compare adjacent sub-run boundary states only as a diagnostic.

A boundary-state mismatch is reported upstream; LWKM does not repair the restart.
