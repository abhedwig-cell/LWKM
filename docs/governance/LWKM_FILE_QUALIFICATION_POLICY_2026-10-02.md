# LWKM file qualification policy — 2026-10-02

## Project rule

Every file consumed by the LWKM production workflow must be individually qualified before use.

A file may exist, be historically used, be present in a server directory or occur in a recovered archive without being qualified. Presence is evidence of existence, not permission for production use.

The production rule is fail-closed:

`UNQUALIFIED FILE -> NOT CONSUMABLE BY DOWNSTREAM PRODUCTION`

This policy applies to the complete chain:

`LHM server -> source snapshot -> post-processing -> SVAT -> HRU -> DRA/BBC/MET/SWP -> SWAP`.

## Minimum qualification record

Every consumed file must have, directly or through an admitted bundle manifest:

- stable file identifier;
- provenance class;
- original source location or producing transformation;
- exact filename/path;
- byte size;
- SHA-256;
- format;
- semantic role;
- downstream consumer;
- qualification status;
- qualification evidence;
- transformation/version identity when derived;
- parent input identities when derived;
- known caveats or intentional deviations.

A filename alone is never sufficient identity.

## Qualification states

Use the following states.

### UNSEEN

Expected or referenced, but not yet found.

### RECOVERED_UNQUALIFIED

Bytes are available, but source identity, semantics or suitability have not been qualified.

### PROVENANCE_BOUND

Origin is sufficiently bound to a source run, server location, archive or producing process. This does not yet prove semantic suitability.

### FORMAT_QUALIFIED

The file can be parsed under an explicit format contract and passes structural checks.

### SEMANTICALLY_QUALIFIED

Its meaning, units, support, coordinate system, temporal interpretation and downstream role are sufficiently established for the intended use.

### REGRESSION_QUALIFIED

When applicable, use of the file has passed the relevant historical/golden regression.

### PRODUCTION_ADMITTED

All required provenance, format, semantic and regression gates for the intended production use have passed.

Qualification is use-specific. A file can be admitted for one consumer and still be unqualified for another.

## Source versus derived files

### Source files

A source file is consumed directly from an authoritative source snapshot.

Its qualification must bind:
- where it came from;
- which run/model state it belongs to;
- what it means;
- how its bytes are identified.

### Derived files

A derived file must additionally bind:
- all qualified parent files;
- code commit/version;
- configuration version;
- transformation semantics;
- output SHA-256;
- regression evidence when required.

A derived file must never become "source authority" merely because it is convenient to reuse.

## Immutable identity

Once a file is admitted for a specific production version, its identity is:

`logical_id + SHA-256 + qualification record`.

If bytes change, it is a new file identity and must be requalified.

Renaming a file without byte changes does not change byte identity, but may still require provenance metadata to be updated.

## Bundle qualification

A Q4 source ZIP may qualify collection integrity, but it does not automatically make every contained file semantically production-admitted.

Bundle Q4 proves:
- selected files were frozen;
- paths and hashes are reproducible;
- extraction reproduces the manifest.

Each downstream-consumed file must still have the required semantic qualification for its use.

The manifest should therefore carry file-level status, not only bundle-level status.

## Downstream enforcement

Production tools should consume files through a manifest or explicit qualification registry where practical.

Before execution, the pipeline should verify:
1. logical file ID exists;
2. status is sufficient for that consumer;
3. SHA-256 matches;
4. required parent/config identities match;
5. no unresolved duplicate source is present.

Direct ad hoc path consumption should be treated as a migration state, not the target architecture.

## Historical files

Historical files may be qualified for:
- provenance reconstruction;
- behavioral oracle use;
- compatibility testing;
- production reuse.

These are different purposes.

For example, a realized historical DRA file can be:
`PRODUCTION_ADMITTED_AS_HISTORICAL_ORACLE`
while remaining invalid as modern source input.

Historical defects must not be promoted to modern production authority unless explicitly admitted as a compatibility mode.

## Qualification evidence hierarchy

Prefer, in order:

1. authoritative source-run binding plus exact content hash;
2. explicit model/control configuration binding;
3. independent structural/semantic checks;
4. historical realized regression;
5. source-code inference;
6. filename/path similarity.

Lower levels cannot silently override contradictory higher-level evidence.

## Required production invariant

For every final SWAP run, it must be possible to trace every consumed input recursively to:

- one or more qualified immutable source files;
- exact transformations;
- exact code/config versions;
- exact output hashes.

No unexplained file may enter the graph.

Target invariant:

`100% OF CONSUMED FILE IDENTITIES QUALIFIED`

and

`ZERO UNTRACED PRODUCTION INPUTS`.

## Immediate implementation consequence

The current LHM source specification and future manifests must evolve from a selection list into a qualification registry.

At minimum each entry should carry:

- `logical_id`;
- `provenance_class`;
- `source_path`;
- `sha256`;
- `qualification_status`;
- `semantic_contract`;
- `required_by`;
- `evidence_refs`.

During Q1-Q4 the fields can move from unresolved to qualified. Downstream execution must refuse entries whose status is below the consumer's required gate.

## Decision

This policy is project-wide authority for file use in the reconstructed LWKM production chain.

No file is trusted merely because it is old, familiar, available, previously used or present in an archive.

Every consumed file must be qualified.
