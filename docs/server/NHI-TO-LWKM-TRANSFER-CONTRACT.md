# NHI server -> LWKM transfer contract

## Goal

One reproducible handoff from an authoritative LHM run environment to the independent LWKM environment.

## On the NHI server

Implemented command:

```text
python -m tools.lwkm_source_cli collect \
  --controls <authoritative-LHM-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  --output <bundle.zip>
```

Optional plan-only inspection:

```text
python -m tools.lwkm_source_cli plan \
  --controls <authoritative-LHM-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  --output <resolved-plan.json>
```

The collector:

1. discovers `control_run_YYYY_YYYY.ini` files recursively;
2. orders periods and rejects gaps/overlaps;
3. preserves control files byte-for-byte in the bundle;
4. resolves configured aliases and paths;
5. expands configured wildcard source families;
6. requires every declared annual source for every year in its control period;
7. selects only transfer-profile-approved static inputs;
8. locates the original run root from required run-tree markers;
9. selects only transfer-profile-approved raw run outputs;
10. excludes restart payload while preserving restart lineage in the original controls;
11. hashes every transferred file with SHA-256;
12. deduplicates identical physical payload by content hash;
13. writes manifest, resolved collection plan and run-chain provenance;
14. verifies the bundle before reporting success.

No scientific calculation is performed by this command.

## Required source classes

### STATIC LHM INPUT

Current profile includes:
- starting heads L1/L2;
- MODFLOW vertical resistance c1 / VCW L1;
- drainage/RIV conductances, stages, bottoms and infiltration factors;
- uopp;
- ground elevation;
- land use;
- soil;
- rootzone;
- meteo district grid.

### PERIOD INPUT

The control file is authority for annual source paths. Current profile requires:
- precipitation;
- evaporation/reference forcing;
- Tmin;
- Tmax;
- Tmean;
- radiation;
- humidity;
- vapour-pressure family.

Configured wildcard values are expanded to their physical files and each payload is hashed separately.

### RAW RUN OUTPUT

The raw output boundary is intentionally narrower than the historical post-processing tree.

MODFLOW:
- head L1 and L2;
- RIV systems 1-6, L1/L2;
- DRN systems 1-3, L1;
- FLF L1 as audited diagnostic/water-balance source.

MetaSWAP:
- bdgPm;
- bdgPssw;
- bdgPsgw;
- bdgETact;
- bdgqrun;
- bdgqmodf;
- bdgdecStot;
- msw_Ebs;
- msw_Esp;
- msw_Epd;
- msw_Eic;
- msw_Tact.

Derived climate summaries, `bdgqmsw`, `bdgqlat`, fuzzy-class grids and RAR archives are downstream products, not source authority.

## Upstream LHM run qualification

MODFLOW/MetaSWAP restart handling between LHM sub-runs is outside LWKM responsibility.

LWKM:
- does not copy or manage restart payload;
- checks whether the source run is complete enough for downstream use;
- preserves the control files that document restart lineage.

Qualification levels:
- Q0 CONFIGURED;
- Q1 PERIOD_COMPLETE;
- Q2 OUTPUT_COMPLETE;
- Q3 EXECUTION_EVIDENCE;
- Q4 LWKM_SOURCE_QUALIFIED.

## In the LWKM environment

```text
python -m tools.lwkm_source_cli verify <bundle.zip>
python -m tools.lwkm_source_cli unpack <bundle.zip> --target <snapshot-directory>
```

Verification occurs before extraction/use.

The extracted snapshot is immutable. Derived LWKM products are written elsewhere.

## Provenance rule

Every downstream derived artifact must be able to report:

```text
bundle_id
  -> logical source
  -> source SHA-256
  -> original LHM path
  -> control file / period
```

## Update behavior

For a new LHM run:
- build a new bundle;
- do not mutate an old snapshot;
- identical payload may be reused/cached by hash;
- invalidate derived LWKM products only when their declared dependencies changed.

## Qualification gate before collection

A real bundle may be marked Q4 only when available evidence shows:
- expected control/sub-run periods are present;
- there are no unexplained gaps or overlaps;
- all required profile sources resolve;
- all required raw run-output families exist;
- expected final output per sub-run exists;
- available process logs/exit markers show no failed sub-run;
- transferred files are nonzero and not obviously truncated;
- the resulting bundle verifies successfully;
- a downstream consumer smoke test succeeds from the immutable snapshot.

These checks establish execution completeness and provenance fitness. They do not certify the numerical correctness of MODFLOW itself.
