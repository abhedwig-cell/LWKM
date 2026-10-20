# KNMI SVAT → HRU MET adapter (2026-10-20)

Implements a local, pre-consumer adapter for existing W09 MET. Inputs are three CSV tables: membership (hru_id,svat_id,area_m2), sampled LHM daily SVAT met (svat_id,date,rad_kj_m2_d,tmin_c,tmax_c,vapour_pressure_kpa,rain_mm_d,etref_mm_d), and sampled KNMI WIND/WET_RAW grids (svat_id,date,wind_m_s,wet_raw_fraction). These are already geographically sampled by the upstream raster reader, including nearest-valid meteoraster replacement. This adapter must not invent that raster sampling.

Calculates per-SVAT WET before area averaging:
- rain=0 → WET=0, even when raw duration is positive;
- rain>0 and positive raw fraction → preserve raw;
- rain>0 with raw NODATA → owner fallback WET=0.1.

The adapter rejects partial HRU/day membership and invalid inputs, preserves area weighting, produces an HRU-day CSV compatible with tools.daily_forcing.modern_met, fallback audit and source/output SHA manifest. Units/geometry and wind ALT W still require producer evidence. Run tests: python -m unittest tests/test_met_knmi_svat_adapter.py.

Operational note: this does not replace the already running KNMI raster producer, does not complete MET datasets and does not imply PRODUCTION_ADMITTED. Actual 1970-2022 LHM raster-to-SVAT extraction and complete user server data remain dependent on the offline server route.
