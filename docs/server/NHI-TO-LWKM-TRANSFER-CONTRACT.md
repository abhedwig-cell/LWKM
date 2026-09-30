# NHI server -> LWKM transfer contract

## Goal

One reproducible handoff from an authoritative LHM run environment to the independent LWKM environment.

## On the NHI server

Command concept:
  lwkm-source collect --controls <control-directory> --profile lhm433-lwkm --output <bundle.zip>

The collector must:

1. discover all supplied LHM control files;
2. order/identify their run periods;
3. preserve them byte-for-byte;
4. resolve configured aliases and paths;
5. select the declared LWKM source dependencies;
6. select required LHM run outputs;
7. expand period-dependent meteo sources;
8. identify restart lineage;
9. hash every transferred file;
10. deduplicate physical payload by SHA-256;
11. write manifest.json and run_chain.json;
12. create the portable zip;
13. verify the zip before reporting success.

No scientific calculation is performed by this command.

## Required source classes

STATIC LHM INPUT:
- MODFLOW vertical resistance c1 / VCW L1;
- drainage/RIV conductances, stages, bottoms, infiltration factors;
- uopp and required MetaSWAP spatial grids;
- other explicitly consumed model parameters.

PERIOD INPUT:
- precipitation;
- evaporation/reference forcing sources;
- temperature/radiation/humidity/wind or other meteorological families actually consumed;
- period-specific configured sources.

RUN OUTPUT:
- MODFLOW head fields required for GWLI/BBC;
- MetaSWAP/SVAT periodic output required for flux reconstruction;
- other outputs only when an LWKM producer explicitly declares them.

UPSTREAM LHM RUN QUALIFICATION:
- MODFLOW/MetaSWAP restart handling between LHM sub-runs is outside LWKM responsibility;
- LWKM does not copy or manage restart payload as a downstream dependency;
- before source collection, verify that the authoritative upstream LHM run completed sufficiently for LWKM use;
- retain only evidence needed to identify/qualify the source run.

## In the LWKM environment

Command concept:
  lwkm-source verify <bundle.zip>
  lwkm-source unpack <bundle.zip> --target <snapshot-directory>

Verification must occur before extraction/use.

The extracted snapshot is immutable. Derived LWKM products are written elsewhere.

## Provenance rule

Every downstream derived artifact must be able to report:
  bundle_id -> logical source(s) -> source hash(es) -> original LHM path(s) -> control file(s).

## Update behavior

For a new LHM run:
- build a new bundle;
- do not mutate an old snapshot;
- content-addressed payload may be reused/cached locally;
- derived LWKM products are invalidated only when their declared dependencies changed.

This supports selective regeneration without losing historical reproducibility.

## Qualification gate before collection

A bundle may be marked QUALIFIED only if the upstream LHM run passes available checks:
- expected control/sub-run periods are present;
- periods have no unexplained gaps or overlaps;
- required MODFLOW head outputs exist for the requested LWKM period;
- required MetaSWAP/SVAT outputs exist and cover the requested period;
- expected final output for each sub-run exists;
- available process logs/exit markers show no failed sub-run;
- file sizes are nonzero and obvious truncation/missing-output conditions are absent.

LWKM does not certify the numerical correctness of MODFLOW itself through these checks. The gate establishes execution completeness and provenance fitness for downstream use.
