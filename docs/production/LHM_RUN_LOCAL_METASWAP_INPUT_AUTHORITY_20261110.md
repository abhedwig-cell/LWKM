# LHM run-lokale MetaSWAP-invoer: statische inputidentiteit

Projecteigenaarbesluit 10 november 2026: **alle niet-tijdsafhankelijke LHM-invoerbestanden zijn identiek tussen de runs**. Neem dit als vastgesteld projectuitgangspunt; een herhaalde volledige statische reconstructie per periode is niet nodig.

## Bronkeuze
De statische LHM/MetaSWAP-input komt uit een run-directory, bijv.:
`G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\run_1970_1979\metaswap`.

Dit is de referentie voor de gedeelde statische schematisatie. De algemene `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp` is géén automatische vervanging voor run-lokale bronbestanden. Voor Frank's reeds uitgevoerde 645582-SVAT-productie blijft de eerdere inputkeuze expliciet als historische productprovenance genoteerd, zonder onnodige herberekening.

## Kwalificatiebeleid
- Het gegeven dat **statische input over runs identiek is, is eigenaarvastgesteld**.
- Controleer waar praktisch SHA256 van corresponderende statische run-lokale bestanden; behandel dit als **bevestigende QA**, niet als een open wetenschappelijke vraag en niet als een verplicht terugkerende blocker.
- Als de controle onverwacht een inhoudelijk verschil toont, rapporteer precies welk bestand/versie afwijkt en onderzoek gericht; gooi het uitgangspunt niet op basis van een bestandsnaam of enkele afwijkende bytes zonder context overboord.
- Registreer tijdafhankelijke invoer, meteorologische jaarbestanden, begin-/herstarttoestanden, uitvoerinstellingen en runperiodes **wel afzonderlijk per run**.
- De reeds vastgestelde broncode-executablekoppeling voor deze LHM-run is `LWKM-LHM-SOURCE-20261110-01` op main; niet opnieuw openen.
- Outputautoriteit blijft `LWKM_run_resultaten_totaal` (door Deltares verzameld).
- Frank's originele 1991–2020 SVAT-tabel blijft immutable referentie, SHA256 `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`.

## Bestaande optionele QA
`tools/lwkm_frank/inventory_run_local_metaswap.py` bestaat voor run-lokale named-input inventarisatie en hashes, en kan eenmalig worden gebruikt, niet als verplicht preflight bij iedere productierun. `tests/test_lwkm_frank_run_local_metaswap.py` beschermt het onderscheid met dynamische runvarianten. Voor voortgang in de productieketen heeft uniform broncodebeheer, runmanifest, centrale configuratie en regressie tegen de Frank-referentie prioriteit boven herhaalde statische hashes.
