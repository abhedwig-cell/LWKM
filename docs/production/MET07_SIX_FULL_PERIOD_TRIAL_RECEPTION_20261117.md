# MET07: zes volledige SWAP 4.3.1-proeven ontvangen

Ontvangstbeoordeling: 17 november 2026. De berekeningen zelf zijn op 16 november 2026 voltooid. Dit vervolgt de FG-naar-HUM-diagnose en de gerichte correctie met de oorspronkelijke LHM-UG-bron. Geen nieuwe LHM-waterbalansanalyse.

## Uitkomst

Alle zes geselecteerde HRU's, 1, 3, 181, 7870, 7871 en 7929, hebben de periode 1970-01-01 tot en met 2022-12-31 normaal doorlopen met dezelfde gebonden SWAP 4.3.1-executable. Elke uitvoering meldt `EXECUTION_PASS_NOT_PRODUCTION_ADMITTED`, exitcode 100, `normal_completion=true`, nul fouten en geen timeout. Zowel de werkelijke `runtime.log` met `Swap normal completion!` als `swap.log` met `Swap simulation okay!` is voor elk geval rechtstreeks gelezen.

De status is `CORRECTED_HUM_SELECTED_TRIAL_PASSED_NOT_PRODUCTION_ADMITTED`, completed=6, corrected_hrus=6, failed=0 en not_started=[]. Het eindtijdstip is 2026-11-16T15:16:46.476967+00:00.

| HRU | Uitvoerregels volgens servercontrole | Laatste uitvoerdatum | Verstreken modelprocesseconden |
| --- | ---: | --- | ---: |
| 1 | 19359 | 2022-12-31 | 148.922 |
| 3 | 19359 | 2022-12-31 | 195.703 |
| 181 | 19359 | 2022-12-31 | 117.390 |
| 7870 | 19359 | 2022-12-31 | 156.313 |
| 7871 | 19359 | 2022-12-31 | 91.750 |
| 7929 | 19359 | 2022-12-31 | 174.953 |

19359 regels zijn 19358 simulatie-etmalen plus de begintoestand op 1969-12-31. De geleverde runner heeft per run 387180 numerieke uitvoerwaarden en de volledige dagelijkse datumreeks gecontroleerd, totaal 2323080 numerieke waarden. Het gebruikte check_csv-algoritme is in deze ontvangst opnieuw gelezen: opeenvolgende dagen, alle numerieke kolommen eindig, eerste toestand en laatste dag vereist.

## Werkelijk ontvangen bronmateriaal

`MET_HUM_PROEF_TERUG.zip`: 1046074 bytes, 68 archiefleden, SHA256 `d3051a4a326168e9cd6c098d901c051e557042a87323275038667a219872dac5`.

Bestandsidentiteiten uit de daadwerkelijk gelezen ZIP:

- STATUS_MET_HUM_PROEF.json: `4eeb2267a4e68382a4406fb2eabe3c355b48445360af12bf655cc7e64755c8fb`.
- RUN_RESULTS.json: `054e6468e45d18496248ef8a2356aa7a13f2fb676a396e6291830e263a8e170b`.
- HUM_CORRECTIONS.json: `5f96a085fa70b625dae5bf082afe6a12011f52d949897afe3f5ef83addf39ee8`.
- HUM_SOURCE_LEDGER.csv: `86ff1262f407bcc2287315fd2dd39eedcbdaeb5da3d31fd35d5c9059400683a5`.
- EXECUTABLE_BINDING.json: `f0d53aa87c6efff4fbf2a1ae6bba9e40790d2121035e6af033c62cdb6f4ce4d1`.

De executablehash is ongewijzigd `d13f5e0321db1780d211520287dc59db2e7aa763649998a4b29a187195ca89a5`. Configuratie en alle negen gerapporteerde Python-codebestanden zijn vergeleken met de werkelijk geleverde `LWKM_MET07_HUM_Herstel_Proef_v01.zip`, SHA256 `704b27457b370c329d164e62190637c3e6c52f932bb5785502280e58786739ae`. Alle identiteiten komen overeen.

## HUM-correctie en behouden invoer

Het volledige bronregister bevat exact 19358 opeenvolgende dagen van 1970-01-01 tot en met 2022-12-31. Elke rij noemt de oorspronkelijke UG-bestandsnaam, SHA256 en byteomvang. Beide eerder gebonden echte rasterankers komen overeen. De HRU-gewichten blijven gebonden aan `6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c`.

De gerapporteerde gewogen HUM-waarden voor deze zes HRU's lopen van 0.14730457961559304 tot 2.445127385224317 kPa. Er zijn voor deze selectie op geen enkele dag dichtstbijzijnde-geldige donorcellen gebruikt. Dit zegt niets over de mogelijke noodzaak van donors bij de overige HRU's.

Alle zes correctierapporten bevestigen `non_hum_bytes_verified_equal=true`: alleen het HUM-token in nieuwe MET-afgeleiden is gewijzigd. In elk bestand zijn 19358 HUM-tokens vervangen. Alle overige modelinvoerhashes komen overeen met de oude broncatalogus. De oude broncatalogi zelf zijn tegen de eerder ontvangen landelijke assemblageresultaten gecontroleerd. Alle 19 meegeleverde modelinvoerbestanden (SWP, CRP en CO2) zijn hier opnieuw rechtstreeks gehasht en komen overeen met de uitvoeringsmanifesten.

De zes gecorrigeerde MET-hashes zijn geschikte regressieankers voor een volgende landelijke implementatie:

| HRU | Gecorrigeerde MET-SHA256 volgens consistent gekoppelde serverrapporten |
| --- | --- |
| 1 | 77f11a5b68e040ec2af13ecf5645281cde71d192d272fb524893aad5c461e1af |
| 3 | aa15c9c64524795fe36811eb4f53bcb8173873096b69e1604e6ffb69639beef5 |
| 181 | eae4dfd2f2b1122981904913b486559dc3f0c2bb6cd9b62a8472858e208efe57 |
| 7870 | d7e800f84943ef752638821871a4fd763f279263763928729a5d6d1fe8fced27 |
| 7871 | e19416a4b12b56a644836ddf4bcd4c3bf0c92cff8f19fdf5db36de18b3e6ad7a |
| 7929 | cf86b658954f2c5497f0131fb64206d3114d1276a9f862b512e945fda5298f74 |

## Grenzen van deze ontvangst

De grote gecorrigeerde MET-bestanden en volledige resultaat-CSV's zijn niet in de terug-ZIP opgenomen. De reviewer heeft de servercontroles daarop dus niet onafhankelijk op alle ruwe bytes herhaald. De ZIP bevat volledige logs, manifesten, broncatalogi, correctierapporten en het dagelijkse bronregister, plus kop/staartfragmenten van iedere resultaat-CSV. Die fragmenten bevestigen begin- en einddatum, maar bewijzen op zichzelf geen dagelijkse volledigheid. De claim over volledige tijdas en eindige waarden berust op de ontvangen uitvoeringsrapporten en de gecontroleerde runnercode.

De lokale ontvangstcontrole heeft 209 consistentie-, identiteit- en inhoudsasserties uitgevoerd zonder afwijzing. Dit zijn controles op ontvangen evidence, geen nieuwe modelberekeningen of onafhankelijke numerieke modeltests. Het afgeleide rapport `LWKM_MET07_Proef_Ontvangst_20261117.json` heeft SHA256 `61bc8eb575e0ce6b4b43b500480f4a55cb70693afd53147ce82e288390da7204`.

## Besluit en concrete vervolgscope

De HUM-bronfout en de technische uitvoering van deze zes gecorrigeerde proefgevallen zijn afgehandeld binnen de beschreven scope. De proeven hoeven niet alleen voor deze ontvangst opnieuw te worden uitgevoerd. Geen nieuwe broninventarisatie, herafleiding van SWP/DRA/BBC of herhaling van het LHM-waterbalansonderzoek.

Dit is geen landelijke vrijgave. Alleen de zes afgeleide MET-bestanden en hun werkkopieen zijn gecorrigeerd. De oorspronkelijke 10242 kandidaat-runmappen en MET06-uitvoer zijn bewust ongewijzigd en bevatten nog de verkeerde HUM-bron.

Volgende implementatie: dezelfde HUM-correctie voor alle 10242 HRU's, met hetzelfde broncontract en ongewijzigde gewichten; daarna de gecorrigeerde MET expliciet binden in nieuwe kandidaatcatalogi en runmappen. SWP/DRA/BBC/CRP/CO2 blijven byte-identiek. Gebruik de zes bovenstaande MET-hashes als regressieankers. Een nieuwe landelijke correctie mag niet worden voorgesteld als reeds uitgevoerd of als volledige wetenschappelijke/modelvrijgave.

In deze ontvangststap is geen nieuwe SWAP-run uitgevoerd, geen landelijk herstelpakket opgeleverd en geen modelinvoer gewijzigd. `production_enabled=false` blijft staan. Deze commit bevat de ontvangstnotitie, geen merge naar main.
