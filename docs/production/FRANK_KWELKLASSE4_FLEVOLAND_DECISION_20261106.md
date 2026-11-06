# Frank: kwelklasse4 en Flevoland-correctie (projecteigenaarbesluit 2026-11-06)

## 1. Kwelklasse4

Vastgestelde omschrijving, niet "sterke wegzijging" maar **wegzijging** voor klasse 1.

Gebruik netto kwel als getekende flux q = kwel - wegzijging met kwel positief opwaarts, wegzijging positief als absolute neerwaartse flux. Indien de invoer twee positieve bruto-componenten bevat, trek wegzijging af. mm/dag:

| Klasse | Naam | Interval |
|---|---|---|
| 1 | Wegzijging | q <= -0.25 |
| 2 | Neutraal | -0.25 < q < 0.25 |
| 3 | Lichte kwel | 0.25 <= q <= 0.75 |
| 4 | Matige tot zware kwel | q > 0.75 |

Grenzen zijn projecteigenaarbesluit: q exact -0.25 klasse 1; +0.25 klasse 3; +0.75 klasse 3. Ongeldige of ontbrekende q is NoData en geen klasse.

Voor ongewijzigde ruwe FLF uit de MODFLOW-v07-export (cumulatieve celvolumes m3/30y over **volle cellen van 62500 m2**) geldt q_mm_d = 1000*(FLF_KWEL_m3-FLF_WEGZIJGING_m3)/(62500*10958). SVAT-rijen met dezelfde volle MODFLOW-cel delen de celwaarde; geen dubbele volumetelling bij gebiedstotalen.

## 2. Flevoland, historische relatie is al gereconstrueerd

Source authority: `docs/lhm-hru-swap/flevoland-correction-design-note.md`; `docs/lhm-hru-swap/FLEVOLAND-QUALIFICATION-POLICY.md`; `tools/flevoland_correction.py`.

- Corrected and original historical annual seepage on SVAT support: `LHM_uitvoer/kwel_corr/Kwel_1991-2020.asc`, `LHM_uitvoer/filter/Kwel_1991-2020.asc`. The realized `SVAT_INFO_HRU` contains `kwel(mm/j)` and `kwel_org(mm/j)` and so can supply a sparse relation directly.
- Previous audited realized relation: 4677 corrected SVATs, approx 268.0 km2, annual equivalent delta around -210.7 Mm3/y over affected area. Historical method/script Deltares not yet recovered.
- Never claim corrected *daily* original MODFLOW-FLF values are available. The historical correction is long-term mean annual seepage; it **does not determine daily corrections or unique full-MODFLOW-cell budgets**.
- For Frank's same-SVAT comparison, calculate corrected long-term **SVAT-support** q_corr_mm_d = q_raw_svat_mm_d + (kwel_corrected_mm_y-kwel_original_mm_y) / (10958/30). Retain `kwel_original_mm_y`, `kwel_corrected_mm_y`, `delta_kwel_mm_y`, raw and corrected q, `kwelklasse4_raw`, `kwelklasse4_corrected`, `flevoland_correction_flag`. Since historical correction may concern positive/negative signed net seepage values, apply to signed net q, not only positive gross kwel. Historical class depends on whether the requested classification is pre/post-correction; do not silently choose.
- **Area-support caveat**: Frank's present FLF raw is m3 per *full* MODFLOW cell, while historical kwel comparison can be SVAT-active area (uopp). Do not add `delta_kwel_mm_y` straight to the full-cell FLF depth without verifying matching support and original value identity. Proposed formula is conditional: first reconstruct raw net q per SVAT on historical support, confirm equality to the historical `kwel_org(mm/j)` within tolerance, then apply Deltares sparse delta. Alternative equivalent volumetric change per SVAT = `delta_kwel_mm_y/1000 * Opp_svat_m2` m3/yr, but aggregating it to MODFLOW cells requires explicit overlap/support accounting. **Do not overwrite original 16-flux export**, and never synthesize daily corrected FLF timeseries from annual delta without a separately approved distribution law.
- QA: 4677 historical correction records on the **selected LWKM population**, no duplicate keys, expected area approx 268km2, match source original values and sign; invalid/missing targets fail. Outside selected historic population correction remains undefined, do not assume unchanged if unverified.

## Next step
Extract historical `kwel_org` and `kwel` from authoritative SVAT_INFO_HRU or two rasters on NHI server, build sparse CSV with original/corrected/delta and provenance. Join only after area/semantic comparison to v07 raw FLF. Produce both raw and qualified corrected kwelklasse4. No fresh MODFLOW run required, but existing 30-year source files must be examined.
