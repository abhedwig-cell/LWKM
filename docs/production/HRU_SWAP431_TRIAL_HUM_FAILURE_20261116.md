# Eerste SWAP 4.3.1-proef: HUM-invoerfout

## Werkelijk ontvangen en gelezen

Op 16 november 2026 is `SWAP_PROEF_TERUG.zip` rechtstreeks geopend. SHA256: `360cde505b6e0810450208b2c087bd79fac8d61994524039458e2b3ff9e84262`. Het archief bevat 16 bestanden, waaronder de volledige HRU-1-invoer, `swap.err`, `swap.log`, `execution.json` en de proefstatus.

HRU 1 is gestart en na circa 1,046 seconde gestopt met procescode 0, zonder normale eindmelding of dagelijkse resultaat-CSV. De runner heeft dit terecht als `EXECUTION_FAIL` gerapporteerd. HRU 3, 181, 7870, 7871 en 7929 zijn niet gestart. Er is in deze ontvangststap geen nieuwe modelrun uitgevoerd.

De werkelijke fatale melding, aan het einde van `swap.err`, is:

```text
ERROR in RDFDOR: Range error of identifier 'hum( 51)',
                 value = 10.300, range = [0.0000, 10.000]
Fatal execution error
```

Dit betreft MET-record 51, gedateerd 20 februari 1970. Die datum is geen bewijs van bereikte simulatievoortgang: de fout ontstaat bij het inlezen van de meteorologische reeks.

## Volledige lokale controle van de ontvangen HRU-1-MET

`1.met` heeft SHA256 `c740427c0b2df5c43246b8c3705fa927d10f6a842f22575b2116807782c011a1`. Alle 19358 dagelijkse records zijn gelezen: 1970-01-01 tot en met 2022-12-31, opeenvolgend en uniek. HUM varieert van 0,5 tot 18,0; 541 records overschrijden de bovengrens 10. De eerste overschrijding is het door SWAP genoemde record 51. De Pearson-correlatie van de ontvangen HUM- en WIND-kolommen is 0,988696578852414; dit is slechts een aanwijzing voor een verkeerde variabele, geen bewijs van de broneenheid.

Alle zes meegeleverde modelinvoerbestanden komen inhoudelijk overeen met hun hashes in `catalogue.json`. Het serverrapport meldt bovendien ongewijzigde bron- en werkinvoer na uitvoering. De executable is gebonden aan SHA256 `d13f5e0321db1780d211520287dc59db2e7aa763649998a4b29a187195ca89a5`; `swap.log` meldt modelversie 4.3.1.

Het foutlog bevat ook 19163 BBC-waarschuwingen over veel cijfers. De BBC-reader bereikt daarna de melding dat 1.BBC met vier variabelen is geparsed. De aantoonbare fatale stop in deze proef volgt bij HUM; de waarschuwingen worden niet zonder grond als oorzaak aangemerkt en BBC wordt hier niet gewijzigd.

## Brontoewijzing en resterende onzekerheid

Op commit `276fbaf8d0571a3fe7f4c78946835fa0b0aee097` is `tools/native/w09_met05/src/w09_direct_met.cpp` opnieuw volledig gelezen, Git-blob `dff2def188f53a0cf50dbcbdb9b2f90c86cc9053`. De bronvelden zijn RD1, EV24, TN, TX, Q, FG, WIND en WET_RAW. De writer schrijft de gewogen waarde van FG (`v[5]`, na `scale_FG`) onder de uitvoerkolom HUM. De bestaande config noemt `path_FG`. De writer heeft geen HUM-bereikstoets in de betreffende waardecontrole.

Het eerdere LWKM-contract in `docs/production/WORK_A_20261019.md` en `W09_KNMI_SVAT_MET_ADAPTER_2026-10-20.md` verlangt werkelijke dampdruk in kPa. KNMI definieert FG als windsnelheid; bron: https://daggegevens.knmi.nl/klimatologie/daggegevens . Het eigenaarbesluit `WORK_A_KNMI_WIND_WET_OFFLINE_POLICY_2026-10-20.md` beperkt de KNMI-aanvulling expliciet tot wind en neerslagduur.

De daadwerkelijke MET06-runtimeconfiguratie en de oorspronkelijke FG-/vochtigheidsrasters zitten echter niet in de proef-ZIP. De fysieke betekenis van een specifiek LHM-bestand is daarom niet uitsluitend op zijn directorynaam vastgesteld. Een verkeerde grootheidstoewijzing is verdacht, maar een definitieve broncorrectie is nog niet uitgevoerd. Een blind gekozen factor 0,1 of afkappen op 10 is geen verantwoorde reparatie. Ook SWETR veranderen zou de bedoelde procesroute veranderen en wordt niet gedaan.

## Begrensde vervolglevering

`LWKM_MET_HUM_Bronbewijs_v01.zip`, 18846 bytes, SHA256 `7a65780c1320e171837be710acce73caedd57a70567874ad7db41d25a86a13d5` bevat een read-only collector, CMD-starter, uitleg, oorspronkelijke bewijsfragmenten en 15 tests. De driver `collect_met_hum.py` heeft SHA256 `0b9108c89d7893693aa2a0cab4dc697a7d30b6f19141695631f9e0c5a9ee0a6e`. Alle 15 tests zijn uitgevoerd en slagen, ook opnieuw uit de definitieve ZIP. Python 3.8-grammatica is gecontroleerd; geen Windows-serveruitvoering van deze collector geclaimd.

De collector gebruikt de eerder gevonden MET06-producermap, neemt de werkelijke configuratie/startcode/metadata mee en leest uitsluitend de betrokken bronrasters van 1 januari en 20 februari 1970. HRU-1-gewichten worden zonder normalisatie uit de geconfigureerde tabel geëxtraheerd. Mogelijke vochtigheidsbronnen blijven ongekwalificeerde kandidaten. Geen 10242-MET-herproductie, geen wijziging van modelinvoer, geen SWAP-start en geen LHM-waterbalansanalyse.

Start: `VERZAMEL_MET_HUM_BRONNEN.cmd` vanuit de uitgepakte pakketmap. Terugrapport: `LWKM_tools\LWKM_MET_HUM_Bronbewijs_v01_resultaat\MET_HUM_BRONBEWIJS.zip`.

De lokale volledige diagnose staat ook in `LWKM_SWAP431_HUM_Diagnose_20261116.json`, SHA256 `bd380ea5f92c514da2ee19821715a7ec26e1cdcb2053dc342cc5fac2d77c4bbc`.

Deze commit bevat de ontvangst-/diagnosenotitie en de distributie-identiteiten. De nieuwe collector en tests zijn in de ZIP geleverd, niet als losse bronbestanden in deze Git-commit ingecheckt.

## Status

Technische assemblage en eerder uitgevoerde interfacecontroles blijven geldig binnen hun eigen scope. Ze bewijzen geen juiste HUM-bronsemantiek. De eerste echte modelproef is mislukt en de betreffende MET-invoer mag nog niet voor de landelijke run worden vrijgegeven. Er wordt geen algemene foutclaim over niet-uitgevoerde HRU's gedaan. `production_enabled=false` blijft staan; geen merge naar main.
