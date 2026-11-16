# Ontvangst volledige HRU-assemblage, 16 november 2026

## Uitkomst en reikwijdte

De volledige assemblagestap is technisch aanvaard op basis van de twee door de projecteigenaar aangeleverde serverrapporten. Alle 10242 kandidaat-runmappen zijn volgens de server samengesteld met controle van bron- en kopiehashes. De ontvangen resultatenlijst is in deze ontvangststap volledig lokaal ingelezen en gecontroleerd, niet alleen via een uittreksel.

Dit is geen modelrunvrijgave. De reviewer heeft de 10242 servermappen en hun afzonderlijke invoerbestanden niet opnieuw rechtstreeks gelezen. `production_enabled=false` en `swap_executed=false` blijven ongewijzigd.

## Ontvangen bestanden en vastgestelde identiteiten

- `STATUS_HRU_ASSEMBLAGE.json`: SHA256 `d106860584334c811ac27adb58fbe094eba9126dfa0042a22ef7720af7a4369e`.
- `HRU_ASSEMBLAGE_RESULTS.json`: SHA256 `67f987aaaaeecc76e48df44621acb3adcb2dd5009a3564d433dcca5f3a32b2f4`; deze hash is gelijk aan `outcome_report_sha256` uit het statusrapport.
- Geleverde ZIP `LWKM_HRU_Assemblage_v01.zip`: 25027 bytes, SHA256 `810cf3b6ba547a1bf278ee098a267bf5154d9801e384abdcc48f189af4e24527`.
- De gerapporteerde gecombineerde code-identiteit `binder_code_sha256` is `584570cfd248bda7147025829a3590887d91a67d6404d2947aeb08eed3ba4120`. Deze is opnieuw berekend met `code_identity()` uit de daadwerkelijk geleverde ZIP en is gelijk. Dit is een hash van de mapping van alle betrokken Python-codebestanden, niet de hash van uitsluitend `assemble_received_hrus.py`. De afzonderlijke driverhash blijft `242d70e6bdd573149b4d742338627b09bdee06491e411260598e04a941762040`.
- W11-broncommit blijft `276fbaf8d0571a3fe7f4c78946835fa0b0aee097`.
- Ontvangsten: preflight `b1c11d87dd499455543c09a948cfbf44f977bf973fb19e2455ef95dbb5de174b`; SWP/DRA-interface `0a2de18ce610d4b081b002cf94606dfc1100f2983b71a3117159c4ff3cf21550`. Beide komen overeen met de originele bewijsbestanden in de ZIP.

## Volledige resultatenlijst

| Controle | Uitkomst |
| --- | ---: |
| Records | 10242 |
| Unieke HRU-ID's | 10242 |
| HRU-populatie | Exact 1 tot en met 10242 |
| Ontbrekende, extra of dubbele HRU-ID's | 0 |
| ASSEMBLED_HASH_VERIFIED | 10242 |
| Nieuw samengesteld / hergebruikt | 10242 / 0 |
| Gerapporteerde fouten | 0 |
| Onjuiste of dubbele doelmappaden | 0 |
| Geldige, unieke catalogushashes | 10242 |
| Pakketten met 6 modelinvoerbestanden | 9581 |
| Pakketten met 7 modelinvoerbestanden | 661 |
| Totaal modelinvoerbestanden volgens de resultatenlijst | 62113 |
| Totale modelinvoerbytes volgens de resultatenlijst | 25578572243 |

De bestandstotalen zijn opgeteld uit `assets` en `bytes`; ze omvatten niet de catalogus-/manifestmetadata of filesystemoverhead. De afzonderlijke servercatalogi zijn niet aangeleverd. De vier bronmappen en de doelmap zijn gelijk aan de configuratie van het geleverde assemblagepakket.

Het serverrapport vermeldt voltooiing op `2026-11-16T11:37:07.433483+00:00` en status `ALL_HRU_CANDIDATE_PACKAGES_ASSEMBLED_NOT_MODEL_VALIDATED`.

Doelmap:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP_HRU_Server06_1970_2022_v01
```

De lokale ontvangstcontrole bevat 23 geslaagde consistentie- en identiteitstoetsen, nul afwijzingen. Het afgeleide downloadrapport `LWKM_HRU_Assemblage_Ontvangst_20261116.json` heeft SHA256 `f4e211c6cd2dc33b5ab8a38caa00c7160b0b3f9294742859c40ac329ae20ae34`. Dit getal is het aantal controles op de ontvangen rapporten, geen nieuwe modeltestsuite. Het grote oorspronkelijke resultatenbestand blijft bij de server-/gespreksartefacten; deze commit bevat de ontvangstnotitie en de identiteiten, niet de 62113 modelinvoerbestanden.

## Vervolg zonder herhaling van afgerond werk

De aanwezigheid, crop/CO2-koppeling, SWP/DRA-bodemlaaginterface en technische assemblage zijn afgerond binnen hun vastgelegde scope. Geen nieuwe inventarisatie of herproductie op grond van deze ontvangst. Bestaande producentkwalificaties blijven gelden. Geen heropening van het LHM-waterbalansonderzoek.

De volgende uitvoering is een afgebakende SWAP-proef met de samengestelde invoer, vanuit afzonderlijke werkkopieen. De gehashte kandidaatmappen blijven ongewijzigd; modeluitvoer hoort niet in die mappen. Voor die uitvoering moet de daadwerkelijk gekozen SWAP-executable expliciet worden gebonden. De ontvangen assemblagerapporten bevatten geen uitvoerbaar SWAP-pad, executablehash of uitgevoerde SWAP-aanroep. Daarom wordt hier geen executablelocatie verondersteld en geen overstap naar SWAP5 gemaakt.

Er is in deze ontvangststap geen SWAP gestart, geen runmap op de NHI-server gewijzigd, geen bestaande producent aangepast en geen merge naar main uitgevoerd.
