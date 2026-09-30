# P12 SWALLO / river-infiltration contract

Source:
  riv_infil = LHM_uitvoer/filter/Riv_infiltratie_1991-2020.asc

Legacy:
  infil_avg = equal-member mean(riv_infil_i)

DRA rendering:
  if system > 3 OR INFRES > 20000 OR infil_avg < 10:
      SWALLO = 3
  else:
      SWALLO = 1

Interpretation:
riv_infil is a long-term regional river/infiltration diagnostic from LHM output, not a soil-hydraulic property and not part of Piet HRU representative identity.

Therefore:
- do not derive it from representative soil;
- retain it as an independent spatial aggregate for historical compatibility;
- preserve threshold 10 until its calibration/provenance is recovered;
- name it river_infiltration_indicator rather than generic infil.

Exact unit/threshold provenance remains OPEN_DOCUMENTATION, but this does not block direct SWP/DRA rendering.

Status: SEMANTICS_SUFFICIENT_FOR_COMPATIBILITY.
