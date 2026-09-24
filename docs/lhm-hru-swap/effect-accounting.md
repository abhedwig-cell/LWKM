# Effect accounting for LHM → SVAT → HRU

The first QA tool is `tools/qa_lhm_hru_swap.py`.

It is intentionally read-only. It does not create a corrected production dataset. It quantifies what the current artifacts imply and keeps different effects separate.

## Current configured analyses

With `config/qa/HRU10242-current.json` the tool produces:

- `stage_hydrology.csv`: hydrologic statistics for the physical SVAT table and the LWKM-selected domain;
- `domain_effect.csv`: effect of the `isLWKM` domain selection;
- `correction_diagnostics.csv`: current source-versus-other-value diagnostics, initially `kwel_org → kwel`;
- `qualification_counts.csv`: number and area of SVATs hit by each qualification flag and their union;
- `hru_mapping_summary.csv`: key counts for the current SVAT→HRU relation;
- `representation_effect.csv`: two deliberately separate effects:
  - cluster-donor representation using `svat_donor`;
  - HRU-representative-SVAT representation using `svat_repr`;
- `qa_summary.json`;
- `report.md`.

## Run

From a workspace where the current production artifacts are available under the configured paths:

    python tools/qa_lhm_hru_swap.py \
      --config config/qa/HRU10242-current.json \
      --out evidence/HRU10242/current

Dependencies:

    pip install -r tools/requirements-lhm-hru-swap.txt

## Interpretation

The tool deliberately refuses to collapse the project-leader stages into one number.

### LHM4.3 → lbn

This is treated as a **domain-selection effect**. A change in a national mean can occur because the population changes, even when every retained SVAT value is unchanged.

### cor

The current configuration compares `kwel_org(mm/j)` with `kwel(mm/j)`, but marks this as **not yet an official correction**. The result only becomes the Flevoland-correction effect after the producer, spatial mask and semantics are bound.

### rep

Qualification flags are quantified, but they are not automatically converted into a replacement effect. A replacement effect requires a versioned replacement policy.

### representative SVAT and HRU

`svat_donor` and `svat_repr` are analysed separately. They represent different relations in the current workflow.

## Next extension

After the current SVAT and HRU effects have been qualified, the same evidence package should be extended with:

1. HRU-level balance table comparison;
2. SWAP input manifest comparison;
3. SWAP output balance comparison;
4. one consolidated project-leader effect table in which every number links back to the evidence files above.
