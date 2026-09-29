# SWP generation replacement workstream

Status: initiated from Tools(1).zip.

## Evidence from legacy R workflow

run_SWAP.R delegates input generation to SWAPtools::create_SWAP for every run_id. The call can receive directories/templates for SWP, MET, ATM, INI, CRP, DRA, BBC and IRG. The same workflow can also build SQLite from Excel, execute SWAP, zip outputs and post-process results.

The supplied SQLite contains domain tables including Runs, Scenario, Meteo, Wortelzone, bodem370_2_bofek2020, discretisatie, dqsat, lu2crop, Irrigatie, Output and crop-related tables.

This is substantially broader than LWKM's desired operation: generate/update SWP input for HRUs.

## Target contract

Canonical HRU/SVAT products + versioned SWAP parameter tables -> deterministic SWP renderer.

Properties:
1. SWP generation is a separate operation from running SWAP.
2. No CRP/MET/INI/DRA/BBC/IRG file is generated or copied unless explicitly requested by that output type.
3. Shared immutable assets are referenced, not duplicated per HRU.
4. Each HRU has an input fingerprint derived only from fields that influence its rendered SWP.
5. Incremental mode regenerates only HRUs whose fingerprint or renderer/template version changed.
6. Dry-run reports create/update/unchanged/error counts without writing.
7. Output is deterministic and atomic.
8. Legacy R/SWAPtools output is regression evidence, not the target implementation.

## Reconstruction phases

A. inventory SQLite tables and SWP template variables.
B. recover create_SWAP field-to-variable contract from realized SWP outputs / SWAPtools metadata where available.
C. implement read-only Python renderer for one HRU.
D. byte/semantic regression against legacy generated SWP.
E. batch renderer with fingerprint cache and selective regeneration.
F. optional independent renderers for DRA/BBC/etc only if LWKM actually needs them.

Do not couple this workstream back into HRU derivation. HRU identity and SWP rendering remain separate.
