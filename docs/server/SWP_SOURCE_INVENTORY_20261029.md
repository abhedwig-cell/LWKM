# SWP: bestaande NHI-bronlocaties inventariseren

Pak LWKM_WorkE_SWP_Bronnen.zip uit onder:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools

Open CMD in de uitgepakte map met inventariseer_swp_bronnen.cmd en voer uit:

```cmd
inventariseer_swp_bronnen.cmd
```

Je hoeft geen controlbestand of oorspronkelijke lokale werkmap op te geven.
De starter gebruikt de bestaande NHI-serverlocaties. Python:
E:\tools\deltaforge\deltaforge_4\python.exe. Alleen standaardbibliotheek nodig.

Na afloop staat in diezelfde map:

```text
swp_broninventarisatie.zip
```

Deel dat ZIP-bestand terug. Het bevat een leesbare samenvatting, de configuratie-
verwijzingen met regelnummer en een volledig JSON-rapport met bronlocaties.
Er worden geen grids verplaatst, gekopieerd of gewijzigd en geen modellen gestart.

## Bestaande bronkennis

De eerder aangeleverde control_runs-archiefbestanden bevatten de oorspronkelijke
control_run_YYYY_YYYY.ini-bestanden. Deze kleine configuraties zijn in dit pakket
opgenomen; het programma gebruikt de bestaande aliasresolver uit de repository.
Het leest daarnaast de actuele configuraties op hun oorspronkelijke serverlocatie.
Eerder aangeleverde en actuele configuraties blijven afzonderlijk herkenbaar.

Bekende locaties:
- E:\LHM_4.3.3
- G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM
- de run_*-mappen met de directe submappen nhi_py, config en control;
- LWKM_run_resultaten_totaal\modflow\head en metaswap.

De scan doorzoekt geen 2,87 TB uitvoerboom. Hij leest kleine INI-configuraties op
de genoemde locaties en controleert alleen metadata van hun bronverwijzingen.
RUN/PRJ/CMD/BAT-bestanden op deze locaties worden als vervolgbewijs vermeld;
hun inhoud wordt in deze eerste inventarisatie nog niet geïnterpreteerd.
Een niet gevonden actuele configuratie betekent niet dat de eerdere verwijzing
onbruikbaar is, maar wordt ook niet als actuele bevestiging voorgesteld.

## Grenzen en vervolgstap

Een bestaand bestand is nog geen bewezen juiste bron voor een SWP-parameter.
Het rapport houdt relatieve verwijzingen, ontbrekende aliases, verschillende
periodeconfiguraties en overlapvarianten zichtbaar. Het kiest die niet stilzwijgend.
Bestanden krijgen geen eenhedenconversie op grond van hun naam. Bijvoorbeeld:
maaiveld_asc verwijst in de echte configuraties naar ahn_f250_cm.asc, terwijl de
oude lokale Fortran-invoer een meterbestand gebruikte. Die overgang moet in de
producer expliciet worden uitgewerkt en gecontroleerd.

Dit pakket inventariseert bronnen. Het produceert nog geen SWP-bestanden.
Het eerdere SWP_Direct-pakket met verplicht --control/--base is voor de nieuwe
serverroute vervangen als aanbevolen startpunt. Na beoordeling van het rapport
wordt de bestaande SWP-producer rechtstreeks aan bevestigde serverbronnen gekoppeld.

Als de vastgelegde servermappen inmiddels zijn veranderd, zijn er optionele
--runs-root en --model-root argumenten; die zijn normaal niet nodig.
