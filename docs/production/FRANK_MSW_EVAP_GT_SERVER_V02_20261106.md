# Frank export, extra MetaSWAP ET components and static Gt, 6 November 2026

Implementation delivered as downloadable NHI Python bundle `LWKM_Frank_Aanvulling_v02_ET_GT.zip`. Package contains `export_msw_aanvulling.py`, `derive_static_gt.py`, imported `wb10_reader.py`, landuse lookup, CMD runners and regression tests.

- MetaSWAP 1991–2020: read only five **not yet exported** decade IDF series (`msw_Tact`, `msw_Eic`, `msw_Ebs`, `msw_Epd`, `msw_Esp`), 1080 decade records per variable. Positive presentation: `-Tact`, `-(Eic+Esp)`, `-(Ebs+Epd)`. Retain five signed source totals. Annual checkpoint hashes and deterministic period geometry.
- Irrigation reuses *existing* `frank_export/MSW_SOURCE_SIGNED_1991_2020.csv` `bdgpsgw_signed_mm_per_year + bdgpssw_signed_mm_per_year`; do not reread historical Psgw/Pssw IDFs.
- Separate QA compares sum of five evap components to existing 1991–2020 `Evapotranspiratie` in `FRANK_LHM_SVAT_BASE_1991_2020.csv`. Never force closure.
- Statically: `slk` = bodem370 and `luk` = landgebruik22 **owner confirmed**. Repository `config/preprocessing/landuse-mapping-realized-v1.csv` included as small data asset. Repo `config/p12/bodem370_classification_lookup.csv` **must be copied to software folder by server operator**, since the code does not guess its 370-row qualified contents; ten BOFEK corrections and five blank unobserved soil codes preserved. Check exact position of slk/luk/nm in user's 14-field area_svat variant; code fails at invalid ranges.
- Gt main class 1..8 computed directly from existing halfmonthly `GHG_cm_mv, GLG_cm_mv` using declared GLG thresholds 50/80/120 and GHG 40/80/140; separate from historical `gt.asc`. No kwelklasse4 inference until lookup thresholds/producer identified.
- Both outputs remain per SVAT; no repeat of head processing, no MODFLOW 16-flux processing, no HRU aggregation.
- Tested on synthetic binary 1271 IDF 36 decades and cache re-run, Gt 8-class test, Psgw+Pssw signed-CSV join; **NHI real execution pending**.
- Code is currently shipped in verified ZIP; this commit is a traceability note, not a claim that source code is itself committed to Git.
