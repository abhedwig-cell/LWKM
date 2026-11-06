# Frank: directe dagelijkse FLF/Flevoland-correctie en SVAT-eindtabel v0.1 (2026-11-06)

Geleverd Windows/NHI Python pakket: `LWKM_Frank_Finale_Server_v01.zip` in de gebruikerconversatie. Dit document legt de feitelijke output en de lokale testresultaten vast; **de broncode zelf is in het ZIP-pakket en nog niet als losse Git-bron gecommit**.

Uitvoering vanuit `LWKM_tools/LWKM_Frank_Finale_Server_v01`, zonder argumenten:
```cmd
CONTROLE_FLEVO.cmd
START_FLEVO_RIV1.cmd
START_EINDTABEL.cmd
```

Lees direct drie dagelijkse oorspronkelijke IDF-bronnen over 1991–2020, alle 10958 dagen:
- `LWKM_run_resultaten_totaal/modflow/bdgflf/bdgflf_YYYYMMDD000000_l1.IDF`
- `LWKM_run_resultaten_totaal/modflow/bdgflf/diepe_slootkwel_gecorrigeerd/bdgflf_YYYYMMDD000000_l1.IDF`
- `LWKM_run_resultaten_totaal/modflow/bdgriv/bdgriv_sys1_YYYYMMDD000000_l1.IDF`

Per dag en oorspronkelijke MODFLOW-cel: `delta_flf=flf_corrected-flf_original`; `riv1_bookkeeping=riv1_original-delta_flf`; classificeer dagelijks het teken van beide gecorrigeerde getekende fluxen. Hierdoor worden richtingomslagen van RIV1 van ontwatering naar infiltratie zonder afkappen meegenomen, op de daadwerkelijk beschikbare MODFLOW-dagresolutie. Geaccumuleerde gecorrigeerde **bruto** richtingen zijn dus niet afgeleid door long-term net simpel te splitsen. Controleer dat `delta_flf+delta_riv1=0` en dat alle opnieuw gelezen oorspronkelijke FLF- en RIV1-brutovolumes overeenkomen met `frank_export_modflow_bruto_v07/MF_SVAT_BRUTO_16_1991_2020.csv`. Falen is fataal, geen stilzwijgende terugval.

Outputs:
- `frank_export_flevoland_daily_v02/FRANK_SVAT_FLEVO_FLF_RIV1_1991_2020.csv`, `MANIFEST_FLEVO_FLF_RIV1.json`, jaarcheckpoints.
- `frank_export_eindtabel/samengesteld_v02/FRANK_SVAT_EINDTABEL_1991_2020.csv`, `MANIFEST_FRANK_SVAT_EINDTABEL.json`.

Strikte SVAT-ID joins voor MetaSWAP basis, GxG+GW5+GW95, MODFLOW v07 originele 16 fluxen, MSW ET/irrigatie, statisch+Gt, 66 gebiedsindeling+N, en FLF/RIV1 correctie. Verwacht precies 645582 SVATs. De statische v05 code gebruikte feitelijk outputdir `frank_export_aanvulling_v04`. Gebied NoData (88581 records) leeg laten, N=1.

Boekhoudkundig gecorrigeerde systeemindeling, in full-cell equivalent mm/jaar:
- `Fldrou1=RIV1_corr_drain+RIV4_drain`; `Fldrou2=RIV2_drain`; `Fldrou3=RIV3_drain`; `Fldrou4=DRN1_drain`; `Fldrou5=DRN2_drain+DRN3_drain`.
- `Fldrin1=RIV1_corr_infil+RIV4_infil`; `Fldrin2=RIV2_infil`; `Fldrin345=RIV3_infil`. DRN infil=0.
- Originele 16 MODFLOW-kolommen blijven intact.
- Gecorrigeerde FLF wordt dagelijks opgesplitst in bruto positieve kwel en absolute wegzijging. Kwelklasse4 uit 30-jaars getekende netto-FLF in mm/dag: q<=-0.25:1 'wegzijging'; -0.25<q<0.25:2 neutraal; 0.25<=q<=0.75:3 lichte kwel; q>0.75:4 matige tot zware kwel.
- M3/cel/30y -> mm/jaar cel-equivalent `1000/(62500*30)`; mm/dag `1000/(62500*10958)`. Meerdere SVATs op één MODFLOW-cel delen dezelfde waarden. Optellen per SVAT tot landelijk volume zonder cell deduplicatie is onjuist.

Geen correctie van werkelijke MODFLOW-bronbestanden, geen nieuwe simulatie. Niet bewezen dat oorspronkelijke RIV1 met boekhoudcorrectie fysisch gemodelleerde drainage representeert. Oude kwel-rastercorrecties/SVAT-info zijn niet nodig zolang beide originele en gecorrigeerde dagelijkse FLF series compleet zijn.

Lokaal synthetisch getest: (1) dagflux RIV1 van -2 naar +3 bij FLF-delta -5; (2) sluiting delta's; (3) alle vijf Fldrou en drie Fldrin-veldtoewijzingen; (4) kwelklassegrenzen; (5) area NoData en N=1; (6) basis CSV join behoud. `python test_finale.py` PASS; `py_compile` PASS; ZIP-integriteit PASS. **Geen echte NHI-serverrun geverifieerd**. Voor productietoelating eerst manifesten inspecteren.
