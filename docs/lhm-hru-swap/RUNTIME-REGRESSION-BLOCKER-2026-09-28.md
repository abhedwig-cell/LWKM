# Runtime regression blocker - 2026-09-28

Attempted direct execution of the canonical regression against the indexed production source.

## Located source

Library index exposes:

- svat_info_lwkm_new.csv
- size: 96,324,523 bytes
- file_id: file_00000000b6b881f4a0052f406de8ff28
- native provider / editor access

## Materialization result

Raw-file materialization to the execution container was attempted explicitly.

Result: no artifact; server warning:

"This Project file does not have an authorized raw-byte materialization path."

Therefore the blocker is not file discovery, filename ambiguity, file size, or missing Library indexing. The current Project/Library projection does not authorize a raw-byte copy into the runtime.

The folder /LWKM-reconstruction is visible in Library metadata but currently lists no child items through files.list.

The exact R source HRU_clustering_LWKM20_31082026.R is not exposed as a standalone Library file; only indexed documentation referring to it is available.

## Consequence

Do not repeatedly retry container execution from the same indexed Project source. Full-row regression requires one of:

1. source files uploaded/attached with raw-byte backing in the active conversation/project;
2. a Library record with authorized raw-file materialization;
3. the relevant regression fixtures committed to the repository.

Indexed text remains usable for source reconstruction/evidence, but cannot support pandas/R execution over the complete 427k-row dataset.

## First regression once bytes are available

1. run build_canonical_svat.py and verify 427656 / 4677 / 20934;
2. run historical R and canonical primary HRU runner on identical manifest;
3. label-invariant partition comparison;
4. run build_swap_inputs.py;
5. compare Runs/BBC/DRA/MET, with special report for the 2559 representative sentinel HRUs.
