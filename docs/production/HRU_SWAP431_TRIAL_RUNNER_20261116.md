# LWKM: afgebakende SWAP 4.3.1-proefrunner

16 november 2026. Vervolg op de geslaagde assemblage van 10242 HRU-kandidaten. Geen herafleiding of nieuw LHM-waterbalansonderzoek.

## Executablekeuze van de projecteigenaar

De projecteigenaar gaf op 16 november 2026 expliciet dit pad op:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\SWAP_4.3.1\SWAP_4.3.1\tools\SWAP\swap_4.3.1.exe
```

De executable is niet naar deze sessie gekopieerd en is hier niet uitgevoerd. Zijn SHA256 wordt bij de eerste serveruitvoering gemeten en in EXECUTABLE_BINDING.json vastgelegd; er wordt nu geen executablehash of zelfstandige binaire versiecontrole geclaimd. Er wordt geen SWAP5 of andere executable gekozen.

## Werkelijk geleverd en getest

Pakket: LWKM_SWAP431_Proef_v01.zip, 562280 bytes.
SHA256: acecfe6757f95ee5cecc9ff4369c781979829054a436cd076535e67f11c6d644.
Nieuwe driver: run_swap_trial.py, SHA256 c604b0592ccf4355782e2d90f1a094c72125061b4aa31edf43d80d36a1216869.

Dit is het geteste lokale distributiepakket. Deze Git-commit legt de executablekeuze, het gedrag en de distributie-identiteit vast. De nieuwe driver en tests zijn in deze commit niet als losse Git-bronbestanden geintegreerd. De ZIP bevat de volledige broncode, configuratie, tests en PACKAGE_MANIFEST.json.

De bestaande assemble_received_hrus.py en vier W11-hulpmodules zijn ongewijzigd overgenomen uit LWKM_HRU_Assemblage_v01.zip (SHA256 810cf3b6ba547a1bf278ee098a267bf5154d9801e384abdcc48f189af4e24527). Hun Git-blobidentiteiten worden waar beschikbaar getest. De nieuwe subprocessaanroep en uitvoercriteria volgen de bestaande tools/execute_swap_candidate.py, opnieuw gelezen op commit 276fbaf8d0571a3fe7f4c78946835fa0b0aee097, maar gebruiken de Python-standaardbibliotheek in plaats van pandas.

28 lokale unittest-tests slagen, zowel voor als opnieuw na het uitpakken van de definitieve ZIP. Zij starten een expliciet synthetisch testproces, niet SWAP. Getest zijn onder meer exitcodes 0 en 100, fout met exitcode nul, normale eindmelding, ontbrekende CSV, ontbrekende/ongeldige/duplicaatdagen, NaN, foutieve numerieke velden, timeout en procesbeeindiging, input- en catalogustampering, ongewijzigde bronnen, verse werkkopieen, locks, paden met spaties, stoppen na de eerste fout en volledige foutinvoer in de terug-ZIP. Alle Python-bestanden zijn tevens met de Python-3.8-grammatica geparsed. De CMD-starter is hier niet op Windows uitgevoerd.

## Ontvangen gegevens en selectie

De originele STATUS_HRU_ASSEMBLAGE.json en HRU_ASSEMBLAGE_RESULTS.json zitten ongewijzigd in het pakket, met hashes d106860584334c811ac27adb58fbe094eba9126dfa0042a22ef7720af7a4369e en 67f987aaaaeecc76e48df44621acb3adcb2dd5009a3564d433dcca5f3a32b2f4. De onderlinge hashkoppeling en populatie zijn lokaal opnieuw gecontroleerd.

Standaardselectie: HRU 1, 3, 181, 7870, 7871 en 7929. Deze zes records zijn daadwerkelijk in de ontvangen resultatenlijst gevonden, alle ASSEMBLED_HASH_VERIFIED. HRU 181 heeft zeven modelinvoerbestanden; de overige vijf hebben zes. Dit is een technische proefselectie, geen bewijs van representatieve dekking van alle gewas-/bodem-/drainagecombinaties.

De simulatieperiode wordt NIET ingekort. TSTART en TEND worden uit SWP en de gehashte catalogus gelezen. Alle invoerbytes blijven gelijk. Per gekozen HRU worden catalogus en modelinvoer tegen de ontvangen hashes gecontroleerd, waarna een onafhankelijke kopie wordt gemaakt. Er worden geen hardlinks gebruikt.

## Uitvoering

Vanuit de uitgepakte map met de starter:

```cmd
START_SWAP_PROEF.cmd
```

Bestaande interpreter: E:\tools\deltaforge\deltaforge_4\python.exe. Geen aanvullende modules vereist. Aanroep: absoluut executablepad met argument swap, vanuit de werkkopie met swap.swp. Iedere start gebruikt een nieuwe gedateerde pogingsmap onder:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP431_HRU_Proef_v01
```

De zes HRUs worden sequentieel uitgevoerd. Bij de eerste fout stopt de reeks. De veiligheidslimiet is standaard 3600 seconden per HRU, expliciet instelbaar via --timeout-seconds. Een expliciete selectie via --hrus is beperkt tot twintig HRUs. Er wordt geen nationale productiebatch gestart.

De runner verlangt exitcode 0 of 100, de melding Swap normal completion!, een eindige numerieke dagelijkse CSV met DATE van TSTART min een dag tot en met TEND, en ongewijzigde invoer/executable. Dit kalendercriterium komt uit de bestaande LWKM-uitvoercontrole. De CSV-bestandsnaam volgt OUTFIL. Onherkende uitvoer wordt als fout gerapporteerd; outputinstellingen worden niet aangepast.

## Terugrapport

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools\LWKM_SWAP431_Proef_v01_resultaat\SWAP_PROEF_TERUG.zip
```

Hierin zitten status, per-run uitvoeringsrapporten, executable-identiteit, logs, SWP/CRP/CO2 en uitvoeruitsneden. Bij een mislukte HRU worden ook zijn DRA/BBC/MET-bestanden opgenomen. Volledige CSVs en logs blijven in de werkkopie; logs boven 8 MiB worden herkenbaar ingekort in de terug-ZIP. Een archiefindex documenteert volledige en gedeeltelijke bestanden. Iedere poging bewaart ook haar eigen rapportkopie.

Status bij een geslaagde proef: SELECTED_SWAP431_TRIAL_PASSED_NOT_PRODUCTION_ADMITTED. Production_enabled blijft false. Werkelijke uitvoering met de opgegeven Windows-executable is een nog te ontvangen serverresultaat, geen lokale testclaim. Er is in deze sessie geen SWAP op de NHI-server gestart en geen merge naar main gedaan.
