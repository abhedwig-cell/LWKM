# LWKM MODFLOW laag-1 FRF/FFF reconstructie (gecorrigeerd 2026-10-16)

Deze runner leest de dagelijkse `head_YYYYMMDD000000_l1.IDF` in de bestaande `LWKM_run_resultaten_totaal\modflow\head`-map en schrijft precies één FRF- en één FFF-IDF per datum voor het gehele modelrooster (1200 x 1300 cellen; 250 meter), naar `modflow\bdgfrf` en `modflow\bdgfff`.

## Correcties op de oorspronkelijke runner

De onafhankelijke vergelijking met de originele MODFLOW-partitie-uitvoer van **2020-07-01** gaf:
- FRF was van tegengesteld teken: nu `C_FRF * (h_buur - h_cel)`.
- FFF was tegengesteld en factor vijf te klein: nu `C_FFF * (h_buur - h_cel)`, zonder eerder toegepaste `TRPY=0,2`.
- Datumlabel liep één dag achter: nu levert head-bestand `head_20200701000000_l1.IDF` de flux met daglabel `20200701`, overeenkomstig de empirisch beste oorspronkelijke WEL-vrije face-fluxvergelijking.

Na de drie correcties op 1 juli 2020: MAE FRF 0,015334 m³/d, MAE FFF 0,015359 m³/d; grootste verschillen 53,24 respectievelijk 58,50 m³/d. Dat is een goede maar **niet exacte** overeenkomst. Andere dagen van 2020 tot en met 2022 blijven nog te toetsen. Gebruik de herrekende bestanden pas nadat de gekozen afwijkingen expliciet zijn aanvaard.

## Vereisten

Pak alle vier bestanden van dit archief in dezelfde map uit. Windows PowerShell 5.1 + .NET C# compiler nodig, geen Python. `IBOUND_L1.IDF` en `kdw_L1.IDF` zijn de oorspronkelijke gebruikte statische rasters; de source `LWKM_MF_L1_Horizontal.cs` berekent harmonische conductanties op hetzelfde modelrooster. Schijfopslag voor de hele periode is aanzienlijk; 2 float32 IDF's per dag à circa 6,24 MB.

## CMD-opdrachten

1. Toon alle dagen, schrijf niets:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_lwkm_mf_l1.ps1" -All -DryRun
```

2. Herbereken een beperkte, eerder geverifieerde dag, met bestaande bestanden vervangen:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_lwkm_mf_l1.ps1" -Start 2020-07-01 -End 2020-07-01 -Overwrite
```

3. Hele beschikbare headreeks corrigeren, inclusief reeds bestaande output:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -File "run_lwkm_mf_l1.ps1" -All -Overwrite
```

Zonder `-Overwrite` worden volledige bestaande dagparen overgeslagen. Met `-Overwrite` worden nieuwe rasters eerst geschreven naar tijdelijke bestanden; bestaande rasters worden per dagpaar apart bewaard onder `.old` totdat beide nieuwe bestanden geplaatst zijn. Bij een fout wordt teruggezet. Achtergebleven `.old`-bestanden na serveruitval moeten handmatig worden gecontroleerd.

Een ontbrekende head geeft geen dagresultaat; de runner rapporteert hoeveel datums daadwerkelijk gevonden zijn. Hij controleert niet zelfstandig of alle kalenderdagen aanwezig zijn. Controleer deze dekking voor volledige productie. Berekening van zowel FRF als FFF op actieve cellen; NoData buiten het actieve model. De x- en y-face aan de buitenrand krijgen nul als er geen actieve buur is.

**Let op:** de datering is bepaald uit de beschikbare onafhankelijke benchmark, niet uit een bewezen algemeen geldende output-timestampregel voor alle versies.
