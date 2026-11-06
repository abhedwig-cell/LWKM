# Frank 1991–2020 originele SVAT-basis: NHI-serverpakket (2026-11-06)

Geleverd als daadwerkelijk gebouwd en lokaal getest ZIP-artifact in gebruikersconversatie: `LWKM_Frank_SVAT_Basis_Ongecorrigeerd_v01.zip`. Bevat `export_qmodf.py`, `maak_svat_basis.py`, bestaande rasterreader `wb10_reader.py`, `CONTROLE_QMODF.cmd`, `START_QMODF.cmd`, `START_SVAT_BASIS.cmd`, `TEST_LOKAAL.cmd`, `test_basis.py`, `LEESMIJ.md`. Softwarebroncode staat in ZIP; deze Git-commit documenteert de release, niet een Git-implementatiecommit.

## Productievolgorde
1. `CONTROLE_QMODF.cmd`: test 1080 Qmodf-bron-IDF's + bestaande signed bron-CSV 645582 SVATs.
2. `START_QMODF.cmd`: leest uitsluitend `bdgqmodf` uit originele MetaSWAP-decadebestanden, via de al gegenereerde `MSW_SOURCE_SIGNED_1991_2020.csv` voor ID, X/Y en SVAT-oppervlakte. Herstartbare jaarcaches met source size/mtime-fingerprint plus SHA256 op jaarcache.
3. `START_SVAT_BASIS.cmd`: strikte SVAT joins van bestaande MetaSWAP basis+signed, heads percentielen, oorspronkelijke v07 MODFLOW 16 fluxen, ET+beregening, statisch/Gt, 66 gebieden/N, QModF klimaatproduct. **Geen afhankelijkheid van FLF/Flevoland correctierun, en geen Flevoland-, RIV1-correctie, donorvervanging of HRU**. Start vanuit uitgepakte folder onder `LWKM_tools`, Deltaforge Python zonder commandoregelargumenten.

## Output
- `LWKM_run_resultaten_totaal/frank_export_qmodf_v01/FRANK_SVAT_QMODF_1991_2020.csv`.
- `LWKM_run_resultaten_totaal/frank_export_eindtabel/svat_basis_ongecorrigeerd_v01/FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv`.
- Audit-CSV `FRANK_SVAT_BASIS_CONTROLE_1991_2020.csv`.
- `MANIFEST_FRANK_SVAT_BASIS.json`.

## Gebruikerbesluiten
Volgorde Frank: SVAT/HRU, Gebied, N, Opp_svat/hru, landuse LHM22, ANIMO4 tekst (gras/maïs/akkerbouw/natuur), lu4,lu2,bodem370,bodem79,pawn21,grondsoort4,grondsoort2,Gtnr, GLG, GHG, GG, Dynamiek, GW5, GW95, kwelklasse4, neerslag, beregening, ETact, 3 verdampingscomponenten, runoff, ontwatering, Fldrou1..5, infiltratie, Fldrin1,Fldrin2,Fldrin345, netto FLF, LAT, WEL, GHB, wegzijging, kwel, QModF, MetaSWAP berging, diagnostisch MSW7, overall onverklaard saldo excl MF storage, indicator latere selectiefase.

- GG = (GHG+GLG)/2; GHG/GLG/GW5/GW95 hergebruik 14/28.
- Oppervlakte-/hydrologische kolommen in **m below surface** voor grondwater, mm/y voor fluxen.
- Fluxmapping en infiltratie conform `FRANK_FLDROU_SYSTEM_MAPPING_20261106.md`.
- Kwelklasse op originele FLF.
- N=1; Gebied NoData blijft leeg; geen Flevolandcorrectie.
- QModF=getekende originele MetaSWAP `bdgqmodf` mm/y, helper, NIET extra externe term in overall som.
- MetaSWAP afwijking = getekende 7-termensom uit `bdgdecstot,bdgpm,bdgpssw,bdgpsgw,bdgetact,bdgqrun,bdgqmodf`; dit is alleen een diagnostische 7-postensom, niet een bewezen fysiek gesloten MetaSWAP balans. Het oudere WB10-restcontract gebruikt het tegengestelde teken `-sum`; hier is de **getekende som** in het veld contractueel gekozen, dus omslag bij vergelijking nodig.
- Overall afwijking = de **WB23 R0** getekende MSW6-som op jaarlijks SVAT-volume (Opp_svat_m2 × signed-mm/y /1000) + (originele MODFLOW LAT+FLF+WEL+GHB+RIV+DRN) per 30 jaar /30; voor mm/y cel-equivalent `1000/62500`. Geen MODFLOW-STO, BND of qmodf in deze formule. Is een **onverklaard deel van de beschikbare-termensom**, geen bewezen modelfout.

De mogelijke dubbeltelling van celbudgetvolume bij meerdere SVATs in één MODFLOW-cel wordt vermeden bij per-SVAT presentatie, maar landelijke volumeaggregatie over de SVAT-rijen is NIET toelaatbaar zonder celontdubbeling. Het originele 16-flux v07 blijft origineel en ongewijzigd. De basis bevat exact 645582 records of stopt.

## Verificatie
`python test_basis.py` lokaal PASS op synthetische input voor schema-volgorde, 5+3 systeemmapping, GG, GW5/95, class, getekende 7-postensom, areaondersteuning overall, gebied NoData, geen Flevolandafhankelijkheid. `python -m py_compile` en `unzip -t` PASS. **NHI-run nog niet uitgevoerd.** Review de bronmanifesten en controleer referentiestalen voor acceptatie.
