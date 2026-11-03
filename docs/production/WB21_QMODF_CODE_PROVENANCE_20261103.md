# WB21: source trace MODFLOW–MetaSWAP qmodf (2026-11-03)

## Model evidence
From the user-supplied 2020 `modsobsimtranmoz.log`:
- iMODFLOW 5_6_2 April 2024; 1124x1300x8 model, 250 m cells.
- WEL, DRN, RIV, GHB active; conventional RECHARGE, EVT, CONSTANT_HEAD, OVERLANDFLOW not present.
- Post-MODFLOW iteration logging prints `msw1postfm_qmodf_begin, k = 1` and `msw1postfm_qmodf_end, k = 21752` (first at source lines 141828–141829). This proves execution of a named postprocessing routine, **not** its precise formula, units or layer mapping.
- Log shows `SIMGRO_save_state`, despite generic 'SIMGRO not present' flag in the active module table: the flag must not be interpreted as absence of any MetaSWAP/SIMGRO coupling.

## Verified public provenance
- Deltares SVN guide, 2023, says MetaSWAP and coupling sources are in GWSobek SVN `https://repos.deltares.nl/repos/GWSobek`, iMODFLOW code in `https://svn.oss.deltares.nl/repos/imod`. Branches: `dfm_fase2`, `lumbricus_combined_mappers`. Source: https://publicwiki.deltares.nl/download/attachments/201032835/Technische%20handleiding%20TKI%20prototype%20Koppeling%20iMODFLOW.pdf?api=v2
- NWM official LHM 4.3 model executable provenance: `imodflow_svn3705_metaswap_svn2299_fix_2351.exe`, iMOD 5.6; https://publicwiki.deltares.nl/spaces/NW/pages/389480549/Overzicht%2Bsoftware%2Bversies%2Brelease%2B2.4.3.1. The exact exe for user's run must be independently verified against the run configuration; no equivalence assumed.
- iMOD 5.6 release notes cite MetaSWAP svn2299 (https://content.oss.deltares.nl/imod/imod56/iMOD_releasenotes_V5_6.pdf).
- Public iMODFLOW v5.6 source path `https://svn.oss.deltares.nl/repos/imod/tags/version5.6/MODFLOW/DRIVER/metaswap_comp.FOR`; the current session could not retrieve the full source due network/server access, so do not assert exact implementation beyond previously documented call flow.

## Open scientific question
SVAT 198271 at 149625,496625, area 12562m2: `bdgqmodf` in Feb D1 about +13434.7 m3; four-term QEXT4 about +759.9 m3; unexplained +12674.9 m3, approximately 1267.5 m3/day. Adjacent cells have heterogeneous residuals. Some other extreme qmodf residuals approximate full RIV, but this does not prove RIV belongs universally to qmodf or that DRN/RIV should be double-counted.

## Next verification
1. Obtain exact source file defining `msw1postfm_qmodf` for GWSobek svn 2299 plus fix 2351; inspect all assignments to qmodf, source MODFLOW arrays and simulation time-step transfer.
2. Verify exact executable identity for user run in run-file or startup record; avoid assuming NWM release provenance identical.
3. Explicitly separate MF-to-MSW recharge, MF cell-budget stresses and SVAT drainage flux. Determine whether `qmodf` includes RIV/DRN, model storage, and coupled recharge.
4. Test the verified formula for SVAT198271 over six decades against raw daily fields and mod2svat mapping. No physically interpreted balance 'correction' before equality proved.
