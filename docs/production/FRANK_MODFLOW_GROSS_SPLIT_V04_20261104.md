# Frank/NHI v0.4: DRN/RIV bruto-fluxsplitsing vóór tijdaggregatie

Projecteigenaarbesluit 4 november 2026: voor ieder dagelijks oorspronkelijk MODFLOW-laag-1 systeem-IDF per cel de twee richtingen onderscheiden **vóór** optellen over de hele tijdreeks.

- DRN SYS1, SYS2, SYS3: **alleen ontwatering**; positieve budgetwaarden >1e-6 m3/d stopfout i.p.v. omzetten naar infiltratie.
- RIV SYS1, SYS2, SYS3, SYS4: `infiltratie(t)=max(Q(t),0)` en `ontwatering(t)=max(-Q(t),0)`, bij bestaande conventie Q>0 naar aquifer.
- Per SVAT-coördinaat en per systeem worden de bruto jaartotalen in één leespassage opgebouwd, naast de getekende nettofluxen.
- Zowel `m3_gehele_periode_cel`, `m3_per_jaar_cel` als `mm_per_jaar_cel` opgeslagen voor alle bron- en afgeleide grootheden. Mm equivalent per volledige 62500 m² MODFLOW-cel, **niet** per `Opp_svat`.
- Na aggregatie moeten per systeem `RIV_signed = RIV_infiltratie - RIV_ontwatering` en `DRN_signed = -DRN_ontwatering` binnen afronding overeenkomen.
- Samenvattende velden: DRN_ONTWATERING_TOTAAL, RIV_ONTWATERING_TOTAAL, RIV_INFILTRATIE_TOTAAL, OPPERVLAKTEWATER_ONTWATERING_TOTAAL, DRN_TOTAAL, RIV_TOTAAL, QEXT4, DRAIN_RIV.
- Geen STO, BND of qmodf. Alleen originele, ongecorrigeerde FLF.
- Nieuwe uitvoer/checkpoints in `frank_export_modflow_systemen_v04`; oude v0.3-netto-checkpoints kunnen de bruto splitsing *niet* reconstrueren. Is v0.3 al uitgevoerd, dan moet de oorspronkelijke daguitvoer voor de splitsing helaas opnieuw worden gelezen.
- Dit betreft splitsing op **beschikbare dagelijkse MODFLOW-IDF-resolutie**. Tegengestelde deelcelstromen op één dag kunnen in de netto IDF al gemaskeerd zijn en zijn niet reconstrueerbaar.

De Python-code en CMD-starters zijn op 4 november 2026 als gecontroleerd ZIP `LWKM_Frank_LHM_Server_v04_BRUTO_FLUXEN.zip` in de conversatie beschikbaar. `test_gross_split.py` test twee dagen met tekenwisselingen in RIV, absolute richting-totalen, tekeninvarianten, checkpoint-herstart en geen STO/BND; eerdere MetaSWAP-zelftest (36 decades) geslaagd. Nog geen echte NHI-run van v0.4.

Invoering: CMD vanuit uitgepakte `LWKM_Frank_LHM_Server_v04` onder `LWKM_tools`: `CONTROLE_MODFLOW_2020.cmd`, daarna `START_MODFLOW_PROEF_2020.cmd`; na goedgekeurd manifest `CONTROLE_MODFLOW_KLIMAAT.cmd` en `START_MODFLOW_KLIMAAT.cmd`. Voor Franks officiële velden `Fldrou`/`Fldrin` is verdere mapping nodig omdat 3 DRN+4 RIV niet gelijk is aan zijn oorspronkelijke 5-systeemindeling.
