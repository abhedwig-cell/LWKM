# LWKM v0.3: ontvangst MetaSWAP-vergelijking en vervolg MODFLOW

12 november 2026. Dit is een aanvulling op de v0.3-proefketen, geen productievrijgave.

## Ontvangen resultaat

COMPARE_MSW_REFERENCE_V03.json meldt FIRST_STAGE_VALUES_EQUAL. Beide CSV's
bevatten 645582 rijen, nul verschillen en gelijke SHA256's voor referentie en
kandidaat. Beide bestanden zijn volgens de serververgelijking byte-identiek.
De gerapporteerde bronbinding komt exact overeen met de eerder ontvangen
run_source_binding.json. De twee grote CSV's zijn hier niet onafhankelijk
opnieuw gelezen. De acceptatie betreft hun gerapporteerde tabelgelijkheid.
De historische eindtabel is nog niet gecontroleerd. De bestaande besluiten
over statische invoer en broncode/executable worden niet heropend.

## Uitvoering

Dit downloadpakket is zelfstandig en bevat alle ongewijzigde v0.3-bestanden,
plus de MODFLOW-vergelijking en twee starters. De oude v0.3-map mag blijven staan.
Pak de bovenste map LWKM_Frank_Pipeline_v03_MODFLOW uit onder LWKM_tools.
Open CMD in de map waarin START_MODFLOW_V03.cmd staat:

```bat
START_MODFLOW_V03.cmd
```

De starter controleert eerst het bestaande geslaagde MetaSWAP-rapport en de
historische MODFLOW-referentie. Daarna voert hij broncontrole en uitsluitend
de MODFLOW-stap uit. Afsluitend wordt de nieuwe tabel met de historische tabel
vergeleken. MetaSWAP en de overige zeven modules worden niet gestart.
Een fout stopt de volgende opdracht. Niets handmatig vrijgeven of op true zetten.

De interpreter blijft E:\tools\deltaforge\deltaforge_4\python.exe met NumPy.
Rekenmodules, pipeline_v03.py, compare_v03.py, bronbinding en configuratie zijn
niet gewijzigd. De bestaande proefmap blijft:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\Frank_v03_runlocal_1991_2020

Bestaande results\msw_basic blijven onaangeroerd. De centrale STATUS_V03.json
beschrijft de laatst gestarte selectie en is geen optelsom van alle eerdere
stappen; de eigen receipts per resultaatsmap blijven het bewijs per stap.

## Expliciete referentie en uitvoer

Referentietabel:
LWKM_run_resultaten_totaal\frank_export_modflow_bruto_v07\MF_SVAT_BRUTO_16_1991_2020.csv

Nieuwe tabel binnen de proefmap:
results\modflow_original\MF_SVAT_BRUTO_16_1991_2020.csv

Dit is de tabel met 16 oorspronkelijke MODFLOW-fluxen, op SVAT-locaties.
De bestaande rekenregel blijft gelden: volumes over 1991 tot en met 2020 per
volledige MODFLOW-cel, geen deling door SVAT-oppervlak. Positieve DRN-waarden
worden volgens de oorspronkelijke producent op nul gezet en apart gelogd.
De vergelijking bewijst niet dat de waterbalans fysisch sluit.

Vergelijkingsrapport in de hoofdmap van de proefrun:
COMPARE_MODFLOW_REFERENCE_V03.json

MODFLOW_STAGE_VALUES_EQUAL betekent dat alle tabelwaarden gelijk zijn.
MODFLOW_STAGE_DIFFERENCES_FOUND bevat afwijkingen per kolom en voorbeelden.
De vergelijking gebruikt exact Decimal, zonder numerieke tolerantie.
Lege waarden zijn niet gelijk aan nul. Bytegelijkheid wordt apart gerapporteerd.
Het DRN-anomalierapport wordt met deze aanvulling niet inhoudelijk vergeleken;
deze beperking staat ook expliciet in het JSON-rapport.

Alleen de vergelijking opnieuw uitvoeren:

```bat
COMPARE_MODFLOW_REFERENCE_V03.cmd
```

Geen automatische zoektocht naar een alternatieve historische referentie.
Bij ontbreken van het expliciete referentiepad stopt de starter voor de berekening.
Bron-IDFs houden de bestaande metadata-controle; dit is geen volledige inhoudelijke
SHA256-controle per ruw IDF-bestand. production_enabled blijft false.

## Lokale controles

De nieuwe tests gebruiken kleine synthetische CSV's en receipts. Ze controleren
onder andere verschillen, ontbrekende referentie, gewijzigde kandidaat,
verkeerde code/configuratie/bronbinding, de uitvoerlock en behoud bij fouten.
Deze tests zijn geen MODFLOW-berekening met NHI-bestanden. De nieuwe CMD-starters
zijn hier niet op Windows uitgevoerd. Zie het lokale testbewijs in evidence.
