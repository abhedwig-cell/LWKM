# Renderer authority recovery search — 1 October 2026

Status:
**ALTERNATIVE RAW AUTHORITY SEARCH EXHAUSTED IN CURRENT PROJECT/LIBRARY SURFACE**

## Purpose

R5 requires a raw-readable renderer database and template/profile authority before the 49-run direct-SWP gate can be executed without guessing.

This search was performed before requesting any additional user upload.

## Repository authority already established

Earlier raw recovery established a historical archive:
- `Datamodel_9830.zip`;
- archive SHA-256 `7eed8c4e609c490efb8eb7cff998e537cf3530eb742709d44a05f2c36271b2f7`.

Recovered from that archive in the earlier runtime:
- `Datamodel_10242.sqlite`;
- SHA-256 `4b697e7f806d0e6f0c345b92bb78c456238c3af5634559a7e2f7edd4171183bb`;
- historical `Datamodel_10242.xlsx`;
- `swap_wwl.swp`;
- SHA-256 `d960f7ede8074672f8f8d6c938df0554383f631e75dfdb67ea33bfe15cc5beab`;
- `swap_tools.log`;
- control and supporting artifacts.

Those bytes were sufficient to close:
- the 10,242-run datamodel completeness audit;
- the datamodel-to-render-context contract;
- run-2000 full active-SWP serialization.

The archive itself is not currently exposed as a raw-readable Project/Library object in this runtime.

## Current Project/Library search

Searches covered:
- `Datamodel_10242.sqlite`;
- `Datamodel_10242.db`;
- `Datamodel_9830.zip`;
- `swap_wwl.swp`;
- `swap_tools.log`;
- `Template.zip`;
- generic archive/SQLite/template terms.

Results:
- current `Datamodel_10242.xlsx` exists;
- a copied `Datamodel_10242_copy.xlsx` exists;
- current `Template.zip` exists in both original and recovery folders;
- no separately addressable `Datamodel_10242.sqlite`, `Datamodel_9830.zip`, or `swap_wwl.swp` object is exposed.

Raw materialization was retried for:
- current Datamodel XLSX;
- copied Datamodel XLSX;
- original Template.zip;
- recovery-copy Template.zip.

All remain blocked by:
`This Project file does not have an authorized raw-byte materialization path`.

## Indexed-content boundary

The current XLSX is searchable/indexed and exposes table content, but this is not a safe substitute for a renderer database in the 49-run admission gate.

Reasons:
1. indexed snippets are not guaranteed complete table exports;
2. row ordering/types/null semantics may be transformed;
3. reconstructing a SQLite database from search snippets would introduce an unqualified parser/transcription path;
4. the 49-run gate is specifically intended to test the renderer, so fabricating its database input from partial indexed content would weaken the evidence.

Therefore no guessed SQLite reconstruction is admitted.

## Template decision

The historical `swap_wwl.swp` has already been qualified as a mapping oracle and, through the explicit adapter, reproduces run 2000 fully.

The current Template.zip is confirmatory rather than automatically a hard production dependency, but 49-run admission still requires actual template bytes or an explicitly versioned canonical replacement.

Without raw bytes for either the historical mapping template in this runtime or the current template package, the harness cannot be executed honestly.

## Blocker classification

**BLOCKER_RENDERER_RAW_DATABASE_AND_TEMPLATE_RUNTIME_BYTES**

This is an evidence-access blocker, not a scientific-authority blocker.

No user input is needed to understand the renderer semantics.

To clear the runtime gate, any one of the following is sufficient:
1. raw-readable `Datamodel_9830.zip` again;
2. raw-readable `Datamodel_10242.sqlite` plus `swap_wwl.swp`;
3. raw-readable current `Datamodel_10242.xlsx` plus current `Template.zip`, followed by a qualified XLSX-to-SQLite/context path;
4. a repository fixture containing the exact already-hashed historical SQLite/template bytes.

Until then:
- retain R2 context qualification;
- retain run-2000 serialization qualification;
- do not claim `DIRECT_SWP_RENDERER_ADMITTED`;
- continue DRA admission work independently.
