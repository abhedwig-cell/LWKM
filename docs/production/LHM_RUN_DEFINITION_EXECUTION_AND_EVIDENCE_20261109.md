# LHM-rundefinitie voor de Frank-productieketen

Deze stap legt de basis **voor** de Frank-export vast. Conform het projecteigenaarbesluit is `LWKM_run_resultaten_totaal` de geaccepteerde downstream LHM-outputautoriteit. De configuratieautoriteit ligt bij de oorspronkelijke `control_run_*.ini` van de LHM 4.3.3-run. **Bestaan van een INI is niet gelijk aan bewijs dat hij de historische run produceerde.**

## Nieuwe, daadwerkelijk gecommitte broncode

- `tools/lwkm_frank/run_definition.py`: read-only INI-inventaris, secties en sleutel-waarden, ConfigObj-achtige `%(alias)s`-interpolatie, paden en SHA256.
- `tests/test_lwkm_frank_run_definition.py`: synthetische INI en expliciete ontbrekende-bestanden-test.

Het script muteert geen LHM-bestand. Schrijft:
- `lhm_run_definition.json` met INI-ID's, bytehashes en zichtbare onzekerheden.
- `lhm_ini_references.csv` met bronverwijzingen, géén ongefundeerde status `historically verified`.

Op de NHI-server vanuit de folder met een checkout van `abhedwig-cell/LWKM`:

```cmd
"E:\tools\deltaforge\deltaforge_4\python.exe" -m tools.lwkm_frank.run_definition --ini-root "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM" --ini-root "E:\LHM_4.3.3" --out "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\lhm_run_provenance" --output-root "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal"
```

Dit is **een verkennende run**, geen onvoorwaardelijke garantie dat elke historische INI binnen de twee geselecteerde roots aanwezig is. Voor ontbrekende controles aanvullend specifieke bronmappen opgeven; niet zelf historische run-data aanvullen. De scan is read-only, maar kan op grote directories enige tijd kosten.

## Verificatiecriteria in volgende fase

1. Alle relevante periode-INI's geïdentificeerd, run-periode/restart-keten gedocumenteerd.
2. Exacte gebruikte LHM-statische invoer: `area_svat.inp`, `mod2svat.inp`, MODFLOW-raster, RIV/DRN configuratie, forcings en uitvoerselectie, gelinkt aan INI-keys en SHA256.
3. Toegestane bronfamilies in `LWKM_run_resultaten_totaal`, inclusief twee **alternatieve** FLF-reeksen als verschillende productvarianten.
4. Originele ongecorrigeerde Frank SVAT-basistabel als onveranderde regressie-oracle: 645582 records, table SHA256 `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`.
5. Eén versioned source tree voor **alle** bestaande Frank-producenten, uniform source/config fingerprint en onafhankelijke clean-run regressie. Deze fase is nog niet afgerond.

De reeds geleverde `LWKM_Frank_Pipeline_v01.zip` is een operationele bundeling maar nog geen aangetoonde reproduceerbare codeautoriteit. De oorspronkelijke subprogramma's moeten met SHA-behoud onder `tools/lwkm_frank/legacy` opgenomen en daarna gecontroleerd worden gerefactord. Geen nieuwe fysische algoritmen invoeren tijdens deze reorganisatie.

**Prioriteit:** eerst W01 INI/bronbinding en code-integratie, daarna herhaalbaar SVAT-output op NHI testen, pas daarna Flevolandvariant en HRU-producten. Bestaande historische WB19-WB28 resultaten niet onnodig opnieuw interpreteren.
