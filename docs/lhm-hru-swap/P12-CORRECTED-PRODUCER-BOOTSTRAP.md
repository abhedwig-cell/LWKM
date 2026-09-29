# P12 corrected producer bootstrap

## Objective

Implement corrected P12 producers alongside, never over, the historical Fortran path.

Modes:
- historical_compat: exact hrulist2SWAP membership/fallback semantics.
- corrected_donor: select svat_orig == svat_donor; zero donors is fatal.

## First producer scope

BBC/QBOT2:
  q_i = (head_l2_i - head_l1_i) / c1_i [m/day]
  QBOT2 = 100 * arithmetic_mean(q_i over selected source members) [cm/day]

Selection differs by mode only. No FLF/QLAT involvement.

MET spatial precipitation/evaporation:
  value_HRU = sum(value_i * area_i) / sum(area_i)
over the same selected membership for the chosen mode.

## Required comparison output per HRU

- n_members
- n_selected_historical
- n_selected_corrected
- selected_area_historical
- selected_area_corrected
- QBOT2 historical/corrected and delta per time step
- precipitation historical/corrected and delta
- evaporation historical/corrected and delta
- provenance counts: donor source / matched target / restgroup donor / restgroup target

## Admission

Correction is not production-admitted until:
- all 10,242 HRUs have >=1 donor source;
- historical mode reproduces existing Fortran outputs on a sample;
- corrected impact is quantified;
- outlier HRUs are inspected;
- no unrelated P12 semantics change in the same patch.
