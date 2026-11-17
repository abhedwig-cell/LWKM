# LWKM SWAP 4.3.1 batchpakket v01

Dit pakket bevat de uitvoerbare Python-aansturing en CMD-starters. Geen nieuwe
SWAP-build of installatie nodig. Alleen Python 3.8+ met standaardbibliotheek;
geen NumPy voor deze runner. Gebruik de bestaande serverinterpreter.

## Nu: het lopende MET07-herstel ongemoeid laten

Pak deze ZIP alvast uit onder `LWKM_tools`. Start de batch pas nadat MET07 volledig
is afgerond en het terugrapport is beoordeeld. De voorbereiding weigert ontbrekende,
onvolledige of gewijzigde MET07-rapporten. Het pakket wijzigt geen MET07-code,
jaarcache, gewichten, bronrasters, parameters of bestaande invoermappen.

## Uitvoeren vanuit CMD in de map met de starters

Eerst voorbereiden, zonder SWAP te starten:

```cmd
01_BEREID_REFERENTIERUN_VOOR.cmd
```

Daarna de vastgelegde startbatch, standaard maximaal twee modelprocessen tegelijk:

```cmd
02_START_REFERENTIEBATCH_100.cmd
```

Deze startbatch bestaat uit 100 HRUs die reproduceerbaar worden geselecteerd op
werkelijk gelezen gewasbestanden, bodemprofieltabellen, onderrand, drainage en
beregeningsinstelling. De zes eerdere proef-HRUs zijn inbegrepen. Bodemidentiteit
is een fingerprint van de hydraulische/discretisatietabellen, geen verzonnen
BOFEK-classificatie. Dit is gerichte dekking, geen statistisch representatieve
steekproef. `SELECTION_100.json` vermeldt redenen en ongedekte categorieen.

Na beoordeling van de startbatch dezelfde campagne uitbreiden:

```cmd
03_VERVOLG_REFERENTIE_ALLE_HRUS.cmd
```

De starter vraagt `JA`. Hij weigert uitbreiding zolang niet de hele startbatch
technisch geslaagd is. De bevestiging bindt de beoordeelde resultaten aan deze
campagne, maar verleent geen wetenschappelijke productievrijgave. De geslaagde
startbatch wordt niet opnieuw berekend.

Alle paden zijn ingevuld. Een extra map bij het uitpakken is toegestaan. De
starters vinden hun code via hun eigen directory, niet de huidige werkdirectory.

## Pauzeren, hervatten, foutgevallen

Vanuit een tweede CMD-venster in de pakketmap:

```cmd
PAUZEER.cmd
TOON_STATUS.cmd
```

Pauzeren stopt nieuwe starts; lopende HRUs mogen afronden. Een enkele Ctrl+C in
het controller-venster vraagt dezelfde pauze. Nogmaals Ctrl+C breekt lopende
berekeningen af. De Windows-controller gebruikt een Job Object om ook bij een
harde controllerstop achtergebleven worker/modelprocessen te beeindigen.

Hervatten: voer dezelfde startopdracht opnieuw uit. De pauze wordt dan opgeheven.
Afgeronde HRUs worden opnieuw op invoer, executable, resultaatbestanden en volledige
dagelijkse CSV gecontroleerd en hergebruikt. Een onderbroken HRU begint in een
nieuwe pogingmap opnieuw vanaf 1970. Dit is geen restart midden in een modelrun.

Een gewone modelfout wordt geisoleerd. Andere HRUs gaan door. Mislukte HRUs worden
niet automatisch steeds opnieuw geprobeerd. Expliciet opnieuw proberen:

```cmd
02_START_REFERENTIEBATCH_100.cmd --retry-failed
```

Bij gewijzigde invoer, beschadigde uitvoer, afwijkende code/executable of een
gedeeld opslagprobleem worden geen nieuwe HRUs gestart. Lopende HRUs mogen
normaal afronden, met eindcontrole van hun invoer. Integriteitsblokkades moet je
eerst onderzoeken; verwijder geen statusbestanden om deze te omzeilen.

Het aantal parallelle processen en de tijdslimiet zijn expliciete runopties:

```cmd
02_START_REFERENTIEBATCH_100.cmd --workers 4 --timeout-seconds 3600
```

Het aantal wordt begrensd door beschikbare CPUs en een veiligheidsmaximum van 32.
Twee is een voorzichtige begininstelling, geen gemeten optimum. Per HRU worden
rekentijd, waargenomen piekgeheugen en beschikbare OS-I/O-tellers geregistreerd.
De tijdslimiet geldt per modelproces. Bij overschrijding is de HRU mislukt, niet
succesvol. De simulatieperiode wordt nooit ingekort.

## Invoer, executable en opslag

Uitsluitend gecorrigeerde invoer:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP_HRU_Server06_MET07_1970_2022_v01
```

Model:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\SWAP_4.3.1\SWAP_4.3.1\tools\SWAP\swap_4.3.1.exe
```

De executable-SHA256 moet gelijk zijn aan die van de zes geslaagde proeven:
`d13f5e0321db1780d211520287dc59db2e7aa763649998a4b29a187195ca89a5`.

Campagne en zelfstandige werkkopieen:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP431_Referentie_MET07_v01
```

Daaronder staan `runs\run_00001\try_001_<id>\work`, `analysis`, het modelrapport en
bestandsidentiteiten. Geen hardlinks, geen overschrijven van oude pogingen, geen
automatisch verwijderen. Alleen modelinvoer wordt uit de kandidaatmappen gekopieerd.

De voorbereiding leest alle catalogi en kleine SWP/CRP/CO2-bestanden, maar niet
opnieuw alle grote MET/BBC-bestanden. Volledige invoerhashcontrole volgt per HRU
voor kopieren en uitvoering en na afloop. Dat bespaart een dubbele landelijke
leesronde zonder de uitvoeringscontrole te verzwakken.

`PREPARATION.json` telt de werkelijk opgegeven invoerbytes. Voor uitvoerruimte is
128 MiB per HRU een expliciete conservatieve werkhypothese, geen gemeten behoefte.
De runner bewaakt daarnaast een vrije reserve van 2 GiB plus ruimte voor actieve
processen. Hij reserveert niet vooraf de opslag voor alle 10.242 berekeningen.
Gebruik de echte uitvoeromvang van de startbatch om de verdere opslag te beoordelen.
De eerdere 55 GB voor MET07-herstel is geen opslaggarantie voor deze campagne.

## De zes eerdere proeven

Hun oorspronkelijke servermappen zijn in `evidence/trial_imports.json` gebonden.
Wanneer die mappen beschikbaar zijn, vergelijkt de runner alle modelinvoerhashes,
de executable en de volledige ruwe resultaat-CSV met het ontvangen proefbewijs.
Dan worden deze resultaten overgenomen zonder nieuwe SWAP-run. Ontbreekt zo'n map,
dan draait die HRU normaal. Bij aanwezige maar afwijkende evidence stopt de import:
er wordt niet stilzwijgend opnieuw gerekend om een integriteitsprobleem te verbergen.
De eerder geuploade CSV-fragmenten alleen worden nooit als volledige uitvoer aanvaard.

## Resultaten en terugsturen

Per geslaagde HRU staan in `analysis`:

- `YEAR.csv` en `DECADE.csv`, met native fluxsommen en toestandsgemiddelden/extremen.
- `NUMERICAL_SUMMARY.json`, met volledige datum-/eindigheidscontrole en BALDEV-statistiek.

Fluxen blijven in cm; grondwaterstanden en bergingen worden niet als flux opgeteld.
De begintoestand wordt gecontroleerd maar niet als extra simulatiedag opgeteld.
`EACT` wordt niet als totale verdamping benoemd. Zie `OUTPUT_CONTRACT.md`.
Dit pakket berekent geen nieuwe GxG, geen LHM-vergelijking en geen kalibratie.

Voortgang en compacte, campagnebrede native statistieken staan in:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_SWAP431_Batch_v01_resultaat
```

De status/HRU-samenvatting worden periodiek en na afloop geschreven. Na elke
normale batchstop of afhandeling van een fout wordt een terug-ZIP gemaakt:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_SWAP431_Batch_v01_resultaat\SWAP_BATCH_TERUG.zip
```

Open de rapportmap met `OPEN_RESULTAAT.cmd`. Stuur deze ZIP terug na de startbatch,
ook bij fouten. Hij bevat status, selectie/dekking, campagnebinding, per-HRU-hashes
en compacte native statistiek. Van maximaal twintig mislukte HRUs worden begrensde
logstaarten opgenomen. De grote ruwe uitvoer en jaar-/decadetabellen blijven op de server.

Na een harde controllerstop kan de laatst gemaakte ZIP verouderd zijn. Hervat de
campagne om achtergebleven `running`-statussen te verwerken. `TOON_STATUS.cmd`
toont het actuele register; een `running`-status is nooit bewijs van voltooiing.
`MAAK_TERUGRAPPORT.cmd` bundelt bestaande rapporten wanneer geen controller actief is.

## Versies en grenzen

Wijzig geen code/configuratie tijdens een campagne. De code-, configuratie-,
selectie- en MET07-identiteiten zijn vastgelegd. Veranderingen vereisen een
bewuste nieuwe campagneversie. Alleen worker-aantal, expliciete retry en tijdslimiet
zijn vastgelegde uitvoeropties die per aanroep mogen verschillen.

De pakketmanifestcontrole bewaakt de geleverde bestanden. `TEST_BATCHRUNNER.cmd`
voert de meegeleverde synthetische tests uit; deze draaien geen echte SWAP.
De interpreter kan voor tests via `LWKM_BATCH_PYTHON` worden aangewezen; standaard
blijft `E:\tools\deltaforge\deltaforge_4\python.exe`.

Dit is een uitvoeringspakket voor een referentiecampagne, geen verklaring dat
10.242 echte HRUs al zijn doorgerekend of wetenschappelijk aanvaard.
`production_enabled=false` blijft in alle rapporten staan.
