# Frank Fldrou mapping, projecteigenaarbesluit 2026-11-06

Bij het samenstellen van de LHM SVAT-tabel voor Frank worden de 16 al geëxporteerde getekende/bruto MODFLOW-bronfluxen niet gewijzigd.

**Ontwatering, alle waarden als positieve drainagehoeveelheid**:
- Fldrou1 = RIV_SYS1_ONTWATERING + RIV_SYS4_ONTWATERING (hoofdwaterlopen H1 bij primair)
- Fldrou2 = RIV_SYS2_ONTWATERING
- Fldrou3 = RIV_SYS3_ONTWATERING
- Fldrou4 = DRN_SYS1_ONTWATERING (buisdrainage)
- Fldrou5 = DRN_SYS3_ONTWATERING (overland flow)

DRN_SYS2_ONTWATERING (maaiveldgreppels, MVG) blijft **apart** en wordt meegenomen in alle-zeven-systemen `Ontwatering_totaal`, maar mag niet ongemerkt verdwijnen.

`Ontwatering_totaal = Fldrou1+Fldrou2+Fldrou3+Fldrou4+Fldrou5+DRN_SYS2_ONTWATERING`.

Bronvolume per MODFLOW-cel over 1991–2020 in m3, aan het einde omzetten naar cel-equivalent mm/j met `1000/(62500*30)`. Weeg/aggereer celvolumes niet meermaals bij meerdere SVAT's in dezelfde MODFLOW-cel.

De historische bron-toewijzing zonder H1 was: Fldrou1=RIV1, Fldrou2=RIV2, Fldrou3=RIV3, Fldrou4=DRN1, Fldrou5=DRN3. Dit besluit voegt RIV4 expliciet aan Fldrou1 toe, en bevestigt DRN3 voor Fldrou5. `Fldrin` infiltratiesystemen zijn **niet** met dit besluit gewijzigd; hun toewijzing blijft apart te bevestigen, met behoud van alle RIV1..RIV4 infiltratiecomponenten.

Controleer exact sluiting van 7 bronvolumes tegen 5+MVG en controleer unit/geometrie/bron-ID's.
