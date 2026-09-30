# Server logistics status

READY:
- LHM control file as primary configured-source provenance;
- alias/path extraction;
- cross-control stable/varying comparison;
- meteo-year dependency detection;
- portable ZIP manifest with SHA-256;
- bundle integrity verification;
- deduplicated multi-period design;
- explicit static/period/run-output/restart classes;
- immutable snapshot policy.

PENDING EXECUTION DATA:
- inspect control_runs.zip when runtime becomes available;
- bind exact period names/order from those files;
- narrow run-output patterns to the exact BBC/GWLI/other producer requirements;
- inspect exe.zip to map current batch/executable orchestration;
- decide which batch scripts are retained, wrapped or replaced.

DO NOT BLOCK ON:
- rewriting existing Fortran executables;
- reproducing entire LHM server directory;
- copying restart payload when downstream LWKM generation does not need it.

TARGET:
one server-side collect command produces one verified portable bundle; downstream LWKM work starts only from a verified immutable snapshot.
