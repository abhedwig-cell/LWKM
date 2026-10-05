# W01 LHM authority split — 2026-10-05

## Decision

Project-owner authority clarifies the first provenance step.

The LWKM reconstruction must **not** reconstruct the internal Deltares period-run assembly as a prerequisite for using LHM output.

Instead W01 is split into two explicit authorities:

### W01-O — LHM output authority

Authoritative output root:

`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal`

This directory tree was assembled by Deltares colleagues and is the source we must use for LHM output files.

Its subfolders are therefore the provenance authority for downstream-used LHM/MODFLOW/MetaSWAP output.

The period-specific `run_*` directories remain useful historical context, but are **not** a required reconstruction gate for W01-O.

### W01-I — LHM input/configuration authority

The project-owner supplied LHM `.ini` control files are the authority for the LHM input configuration.

These INI files define:
- model/data roots;
- MODFLOW package input files;
- MetaSWAP inputs;
- drainage/river inputs;
- meteorological inputs;
- coupling inputs;
- executable bindings;
- restart inputs and restart semantics;
- output-selection settings.

The supplied loose Library state currently exposes:
`control_run_1970_1979.ini`.

That file explicitly identifies the model family as LHM 4.3.3 through paths such as:
`e:\LHM_4.3.3`
and:
`Data\2_Model_Input`.

Further supplied INI files, when recovered from existing project uploads/archives, must be added to the same W01-I authority set. No re-upload should be requested before existing project/Library/archive evidence is exhausted.

## Consequence for provenance

The first production provenance graph becomes:

```text
W01-I qualified LHM INI/config
      |
      +--> qualified referenced LHM input files
      |
      v
   LHM execution
      |
      v
W01-O Deltares-collected output tree
      |
      v
downstream LWKM postprocessing
```

The LHM execution itself is external to the reconstructed LWKM software, but its configuration and output identities must be traceable.

## W01-O qualification contract

For every file consumed downstream from `LWKM_run_resultaten_totaal` record:
- relative path below the authoritative output root;
- byte size;
- SHA-256;
- file type;
- temporal coverage where applicable;
- semantic role;
- downstream consumer;
- qualification status.

Files not consumed downstream do not automatically need to become LWKM production inputs, but may be retained in a broader immutable source snapshot if storage policy permits.

The output tree must not be replaced by a reconstructed mixture of underlying `run_*` directories.

## W01-I qualification contract

For every authoritative INI:
- stable logical ID;
- original supplied identity;
- exact text/bytes if recoverable;
- SHA-256 when raw bytes are available;
- period/run scope;
- model root;
- referenced paths;
- restart relationship;
- output-selection semantics.

For every input file that is actually required for:
1. reproducing the authoritative LHM configuration; or
2. direct downstream LWKM reuse,

record:
- resolved path;
- logical role from the INI key;
- byte size;
- SHA-256;
- format;
- period/static scope;
- semantic qualification.

The INI reference itself does not automatically prove that the resolved current server file is the historical byte-identical file. Historical/current identity must be tested where relevant.

## Separation from HRU/SWAP provenance

HRU/SWAP producer files are not NHI-server W01 inputs unless explicitly referenced by the LHM INI/config itself.

Keep separate downstream provenance for:
- HRU/SVAT schematisation files;
- HRU2SWAP executable/source/log;
- SWP templates;
- DRA/BBC/MET generation;
- datamodel/lookups.

This removes the previous false requirement that the NHI server contain HRU/SWAP runtime material.

## Effect on previous Q0A run-chain discovery

The previous attempt to infer the exact internal period-run chain is no longer a W01 admission requirement.

Retained evidence:
- all observed LWKM `metaswap\svat.asc` files were byte-identical;
- this remains useful corroborating evidence for stable SVAT schematisation.

Superseded requirement:
- proving which `run_*` directories Deltares copied into `LWKM_run_resultaten_totaal`.

The project owner directly identifies `LWKM_run_resultaten_totaal` as the authoritative output collection. That is the relevant provenance boundary for the reconstructed LWKM chain.

## Current W01 state

`W01_OUTPUT_AUTHORITY_BOUND_INPUT_CONFIG_AUTHORITY_PARTIAL`.

Closed:
- output root authority identified;
- HRU/SWAP false server dependency removed;
- one supplied LHM control INI recovered and inspected.

Remaining:
1. inventory the authoritative output tree;
2. determine which output files are actually consumed downstream;
3. qualify those file identities;
4. recover/catalog all supplied LHM control INIs from existing project sources;
5. parse each INI into a machine-readable referenced-input manifest;
6. bind required referenced input files to hashes and semantic roles;
7. freeze output/config/input evidence into immutable provenance bundles/manifests.

No period-run reconstruction is required before these steps.
