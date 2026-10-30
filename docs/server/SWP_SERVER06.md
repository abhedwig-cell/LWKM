# LWKM SWP Server06

Deze versie bevat de vier bevestigde basis-cropfiles en de atmosferische CO2-bron. Iedere HRU krijgt een eigen map met de SWP, de benodigde ingevulde cropfiles en een kopie van het CO2-bestand. De bestaande maisrotatie met vanggewas blijft behouden.

## Starten in CMD

Pak de zip uit naar een nieuwe map onder:

G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools

Open CMD in de map waar maak_swp.cmd staat en voer uit:

```cmd
maak_swp.cmd
```

De starter gebruikt de bestaande E:\tools\deltaforge\deltaforge_4\python.exe en leest dezelfde serverbronnen als Server05. Standaardperiode: 1970-01-01 t/m 2022-12-31. Er is geen nieuwe Python-installatie nodig; de bestaande omgeving moet NumPy bevatten. Er worden geen bronbestanden verplaatst.

Uitvoer:

- swp_server06_productie\swp\<HRU>\<HRU>.swp
- dezelfde HRU-map: gras_maaien.crp, snijmais.crp, fictief.crp of gras_beweiding.crp, volgens de landgebruiksklasse;
- indien de bestaande rotatie het vraagt: vanggewas.crp;
- iedere HRU-map: atmospheric_1975-2020.co2;
- swp_server06_productie\controle.zip voor het terugrapport.

SCHEDULE is 1 bij toegekende beregening en anders 0. CROPFIL en ATMOFIL verwijzen lokaal; de extensies .crp en .co2 zijn impliciet. De CO2-bron dekt ieder jaar 1970 t/m 2025 met een vaste 360,80 ppm. De historische naam is behouden.

De opdracht mag opnieuw worden gestart. Alle gegenereerde SWP-, crop- en CO2-bestanden worden gecontroleerd; afwijkende bestanden worden opnieuw gegenereerd. Bewaar latere HRU-kalibraties daarom in een aparte werkmap. Gebruik geen bestaande Server05-uitvoermap als output: de indeling is gewijzigd van platte bestanden naar HRU-submappen.

Na voltooiing, vanuit dezelfde CMD-map:

```cmd
controleer_swp_dra.cmd
```

De checker zoekt SWP's in de HRU-submappen en bestaande voltooide DRA-uitvoer. Bij meerdere of ontbrekende DRA-mappen moet een expliciete --dra-map worden opgegeven.

## Grenzen

Dit pakket genereert kandidaat-invoer, het start geen SWAP-modelruns. BBC, DRA en MET moeten nog worden samengesteld met de HRU-runmappen. De bestaande Server05-parameterafleiding blijft behouden; deze release implementeert de lokale crop/CO2-bestanden en veranderde mapindeling. SOURCE_BACKGROUND.md beschrijft die bestaande afleiding, CROP_CO2.md de gewasbestanden.

Er is geen nieuwe Windows/NHI-serveruitvoering of hydrologische validatie uitgevoerd. package_manifest.json legt de pakketbestanden met hashes en broncommit vast.
