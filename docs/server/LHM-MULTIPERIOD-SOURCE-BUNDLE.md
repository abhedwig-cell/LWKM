# LHM multi-period source bundle

Input: all authoritative control files that together define the historical LHM run.

Automated workflow:
1. preserve every original control file unchanged;
2. resolve path aliases per control file;
3. compare logical dependencies across control files;
4. classify dependencies as stable or period-varying;
5. expand annual meteo dependencies;
6. hash physical source files;
7. deduplicate identical files by SHA-256;
8. record restart lineage between period runs;
9. build one portable LWKM source bundle.

Archive layout:
  provenance/control/
  provenance/run_chain.json
  manifest.json
  objects/<sha256>
  logical/static/...
  logical/period/<period>/...

The objects store avoids copying identical large files repeatedly. Logical entries in the manifest retain the original LHM key, source path, control file and period.

A source that has the same path but a different hash across periods is NOT static.
A source that has different paths but identical hash may share one physical object while retaining both provenance records.

Restart output is lineage, not immutable source data. Preserve its producer period and target period explicitly.

No batch-file path or current working directory may be required to interpret the exported bundle.
