# NHI/LHM server provenance contract

## Primary principle

Do not manually duplicate the complete LHM dependency inventory.

The LHM run control file is the primary provenance source for an LHM run. For the supplied 1970-1979 example it identifies:
- model root and model version;
- static MODFLOW inputs;
- MetaSWAP inputs;
- drainage and river inputs;
- meteorological inputs by year;
- executables;
- restart rules;
- model settings and coupling configuration.

LWKM extracts only the dependency subset it actually consumes.

## Provenance layers

### L0 LHM run
Archive unchanged:
- control file;
- run period;
- model root/version identifier;
- executable references;
- preferably content hash of control file.

### L1 resolved LHM sources
Resolve control-file aliases such as:
  %model%, %moddata%, %vcw%, %riv_reg%, %g2m%
to concrete paths at extraction time.

Do not hard-code those resolved paths into scientific producer code.

### L2 LWKM source subset
Automatically extract provenance for sources consumed by LWKM, including at least:
- MODFLOW initial/stationary head;
- VCW/c1;
- drainage/RIV conductances;
- drainage bottoms and winter/summer stages;
- infiltration factors;
- uopp;
- ground elevation;
- land use / soil / rootzone where required for reconstruction/QA;
- meteorological source families;
- relevant MetaSWAP mappings.

### L3 LWKM derived artifacts
Record dependency hashes for:
- SVAT_INFO;
- HRU schema;
- canonical soil lookup;
- BBC;
- DRA;
- MET;
- typed run records;
- SWP.

## Execution policy on NHI server

Existing Fortran executables remain supported tools. No language rewrite is required merely for modernization.

Batch orchestration is not provenance authority. Replace or wrap batch files where useful with a runner that:
- resolves control-file dependencies;
- logs executable + arguments + timestamps + exit codes;
- writes output inventory and hashes;
- stops on failure;
- supports restart/selective execution.

## Snapshot/export

An LWKM source snapshot exported from the NHI server must contain:
- original LHM control file;
- machine-readable resolved-source manifest;
- only required source products (or stable references where copying is inappropriate);
- hashes/size/mtime;
- producing step/executable where known;
- run period and LHM version.

The W-drive/LWKM environment starts from this snapshot. It must not depend on undocumented files left elsewhere on the NHI server.

## Important distinction

Control-file path provenance answers:
  "which configured source was used?"

File hash answers:
  "which exact bytes were used?"

Both are required for a reproducible snapshot.
