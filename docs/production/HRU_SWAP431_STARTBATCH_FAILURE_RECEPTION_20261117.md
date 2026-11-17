# Ontvangst eerste SWAP431-startbatch, 17 november 2026

## Besluit

De startbatch is niet aanvaard voor uitbreiding naar alle 10242 HRU's. Van de 100 geselecteerde HRU's zijn 82 technisch geslaagd volgens de ontvangen samenvatting: 76 nieuwe berekeningen en de zes eerder geslaagde, opnieuw gecontroleerde proeven. Er zijn 18 mislukte modelberekeningen. De overige 10142 HRU's zijn nog pending. Opdracht 03 blijft geblokkeerd; de acceptatiecontrole wordt niet omzeild.

De bestaande 82 geslaagde resultaten blijven behouden. Een latere reparatie moet gewijzigde modelinvoer als expliciete afgeleide versie binden. Alleen inhoudelijk identieke geslaagde berekeningen mogen worden overgenomen. Geen handmatige wijziging van gehashte kandidaatmappen of bestaande campagne-identiteit.

## Werkelijk ontvangen bewijs

`SWAP_BATCH_TERUG.zip`: 214968 bytes, 96 archiefleden, SHA256 `eb8a3030642099afd5a89e96d9e8233cab1660e45c3dcddf49a143a52af724e4`.

De ZIP is rechtstreeks geopend. De volledige `HRU_SUMMARY.csv` met 10242 records, alle 18 foutmanifesten en alle aangeleverde foutlogstaarten zijn gelezen. De vijf hashes uit ARCHIVE_INDEX kloppen. De 100 unieke geselecteerde HRU's zijn exact de niet-pending populatie. De campagne-objecthash, alle zeven softwarehashes en de configuratie komen overeen met de geleverde batchrunner. De vijf bovenliggende MET07-rapporthashes komen overeen met de eerder ontvangen nationale ZIP. De 18 gebruikte MET-hashes komen overeen met hun MET07-records.

Campagne: `8c7ed46571d62b749978ee6fb8cd1e5f79432cffe38b5bff14c5ee0cde17c1d2`.
Executable: `d13f5e0321db1780d211520287dc59db2e7aa763649998a4b29a187195ca89a5`.
STATUS_BATCH: `BATCH_FINISHED_WITH_FAILED_OR_UNFINISHED_HRUS`, tijd `2026-11-17T15:25:19.517204+00:00`.

Alle foutmanifesten melden ongewijzigde invoer en executable, returncode 0, ontbrekende normale voltooiing en fatale modelmeldingen. Geen van deze 18 fouten is een timeout of als gedeelde infrastructuurfout geclassificeerd. Een procescode nul is terecht niet als modelsucces aanvaard. Het lege top-level errors-veld is geen bewijs van nul HRU-fouten.

## Foutgroep 1: natuurtemplate en verdampingsinstelling, 17 HRU's

HRU's: 3061, 3198, 4309, 4317, 4382, 4696, 5195, 7649, 8532, 8650, 8688, 8691, 8893, 9120, 9740, 9877 en 10114.

Alle 17 foutlogstaarten bevatten:

```text
ERROR in cropfactor: If ETref is used (SWETR = 1), always define crop factors (SWCF = 1)
```

Alle 17 gebruiken dezelfde `gras_beweiding.crp`-hash:
`d00123a4078c788ba1d8c1496ffae2a0425f6d9d5024e8c8285a90ddde0a2bad`.
De uitvoering stopt na circa 0,83 tot 0,97 seconde. De aangeleverde logstaarten tonen dat MET en DRA al zijn ingelezen voor de cropfactor-stop.

De oorzaak is herleid in de oorspronkelijke producent op commit `276fbaf8d0571a3fe7f4c78946835fa0b0aee097`:

- `docs/landgebruik.md`: lu4=4 betekent natuur en gebruikt `gras_beweiding.crp`. De bestandsnaam mag niet als een nieuwe landgebruiksklasse worden gelezen.
- `config/swp/four_landuse_crop_candidate.csv`: voor beide soil2-klassen krijgt lu4=4, crop_id=22, SWETR=1.
- `tools/swp_run_parameters.py`: SWETR wordt uit deze crop_lookup overgenomen.
- `tools/swp_local_assets.py`: crop_id=22 verwijst naar gras_beweiding.
- `templates/crops/base/gras_beweiding.crp`: SWCF=2, met CHTB, ALBEDO en RSC, dus een crop-height-parameterisatie in plaats van de door SWETR=1 verlangde gewasfactorroute.

Er is dus een inconsistentie tussen de nieuwe cropfiletoewijzing en de behouden verdampingskeuze. SWCF blind veranderen naar 1 zonder een onderbouwde gewasfactortabel is geen volledige reparatie. Voor behoud van de geleverde crop-height-parameterisatie moet de SWP-route expliciet daarmee in overeenstemming worden gebracht. In deze ontvangst zijn geen waarden gewijzigd.

Volgens SELECTION_100 bevat de landelijke invoer 2825 HRU's met gras_beweiding.crp. Dat is een potentiële reikwijdte van de bronfout, geen claim dat alle 2825 modelruns zijn uitgevoerd.

## Foutgroep 2: ingeschakelde vanggewasberegening zonder schema

HRU 9549 stopt met:

```text
Routine RDDATA, called by RDFINR, attempts to read
precisely 2 values from file VANGGEWAS.CRP
into INTEGER array STARTIRR
ERROR in RDDATA: Variable name not in data file
Fatal execution error in RDDATA
```

De bijbehorende volledige cropfilehash in EXECUTION.json is:
`8cbf577c19f965e72ce35862bf2533eee84dd23c4a0e22600b0b86fdb68a78fd`.

De oorzaak is rechtstreeks zichtbaar in `tools/swp_local_assets.py`: de HRU-irrigatiekeuze wordt naar alle cropfiles geschreven, ook naar vanggewas. De oorspronkelijke `templates/crops/auxiliary/vanggewas.crp` eindigt met SCHEDULE=0 en bevat geen STARTIRR of volledig actief beregeningsschema.

Er is bovendien een exacte lokale byte-replay uitgevoerd. Het daadwerkelijk eerder ontvangen `MET_HUM_PROEF_TERUG.zip:run_00181/vanggewas.crp` heeft hash `1b738566883bc4097ec2cd498f0a65d7b8d7355040cb0853147ff37774cdbe7a`. Alleen het ene SCHEDULE-token van 0 naar 1 wijzigen levert exact de cropfilehash van de mislukte HRU9549 op. Het gereproduceerde bestand bevat geen STARTIRR. Dit is een bytevergelijking, geen nieuwe modelrun.

De reparatie moet het crop-specifieke beregeningsgedrag expliciet definiëren: ofwel een volledig en onderbouwd schema voor het vanggewas, ofwel een expliciete uitzondering voor dat gewas. De irrigatietoekenning aan de HRU en het hoofdgewas mag niet worden uitgeschakeld als technische omweg. Geen STARTIRR-datum of andere irrigatieparameter is in deze ontvangst verzonnen of toegevoegd.

Volgens de landelijke categorieën zijn er 165 HRU's met de beregende combinatie snijmais/vanggewas. Ook dit is potentiële reikwijdte, niet 165 waargenomen mislukte runs.

## Geslaagde deelset en beoordelingsgrens

Alle 82 completed-records melden 19358 simulatie-etmalen, einddatum 2022-12-31 en returncode 100. De zes imports zijn exact HRU 1, 3, 181, 7870, 7871 en 7929. Hun resultaten worden niet als 82 nieuw gedraaide runs geteld.

De grootste gerapporteerde absolute dagelijkse BALDEV is 0,03088 cm bij HRU9609. De grootste absolute waarde van de gesommeerde dagelijkse BALDEV over de gehele periode is 0,613188122471351 cm bij HRU9624. Dit zijn native diagnostische samenvattingen, geen nieuwe LHM-balansreconstructie en geen automatische aanvaarding op basis van een verzonnen tolerantie.

De volledige dagelijkse resultaat-CSV's en afzonderlijke succesmanifesten zijn niet meegeleverd. De successful-reeksen zijn daarom hier niet onafhankelijk opnieuw opgeteld of doorgerekend; hun statistieken zijn ontvangen serverresultaten. De volledige foutlogs zijn evenmin meegeleverd, alleen staarten; hashes van volledige grote logs zijn niet uit de staarten gevalideerd. De korte runtime- en swap.log-bestanden passen wel geheel in de staarten en hun hashes kloppen.

Er is een extra rapportagebeperking gevonden in de geleverde `results.py`: inspect_logs leest runtime.log, swap.log en swap.err, maar niet swap.wrn. Daarom bewijst warning_lines=0 in de geslaagde samenvattingen niet dat alle modelwaarschuwingen zijn afwezig. Deze leemte moet in de volgende gebonden runner-/rapportageversie worden hersteld zonder bestaande manifesten stilzwijgend te herschrijven.

## Vastlegging en vervolg

De ontvangstcontrole heeft 113 geslaagde consistentie- en identiteitstoetsen, nul afwijzingen van het ontvangen bewijspakket. Dit is uitdrukkelijk geen geslaagde startbatch: de 18 modelmislukkingen blijven staan.

Afgeleid rapport: `LWKM_SWAP431_Startbatch_Beoordeling_20261117.json`, SHA256 `16603ae95589911b69e1de983e9c6ad2041ce1f4f8ce54a3277ed514947b9fdd`.
Daarnaast zijn een foutentabel voor 18 HRU's en een compacte CSV met uitsluitend de 100 geselecteerde HRU's gemaakt.

Volgende stap: herstel de twee inconsistenties in de oorspronkelijke SWP/crop-producent, voeg expliciete controles toe op SWETR/SWCF en op volledige invoer bij SCHEDULE=1, bind gewijzigde invoer als nieuwe versie en voer uitsluitend de getroffen gevallen opnieuw uit. Behoud de 82 ongewijzigde resultaten na verificatie bij overname. Geen landelijke uitbreiding voordat de startbatch opnieuw beoordeeld is.

In deze ontvangststap zijn geen producenten of modelinvoer aangepast, geen nieuwe SWAP-berekeningen gestart, geen serverbestanden gewijzigd en geen branches samengevoegd. De MET07-correctie wordt niet opnieuw uitgevoerd.
