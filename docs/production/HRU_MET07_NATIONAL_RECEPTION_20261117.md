# Ontvangst landelijke MET07-correctie, 17 november 2026

## Besluit en reikwijdte

Het door de projecteigenaar aangeleverde `MET07_LANDELIJK_TERUG.zip` is rechtstreeks geopend en volledig programmatisch gelezen. De landelijke HUM-correctie en herbinding zijn op rapportniveau aanvaard voor de voorbereiding en uitvoering van de eerder afgesproken startbatch van 100 HRU's. Het bestaande batchpakket behoeft op basis van deze ontvangst geen wijziging.

Dit is geen landelijke modelrunacceptatie of wetenschappelijke productievrijgave. De actuele 10242 servercatalogi, modelinvoerbestanden en jaarcache-arrays zitten niet in de terug-ZIP en zijn in deze ontvangststap niet onafhankelijk opnieuw gelezen. De batchvoorbereiding controleert de werkelijke servercatalogi; volledige invoerhashcontrole volgt per HRU voor de modeluitvoering. Er is hier geen SWAP gestart en niets op de NHI-server gewijzigd.

## Identiteit van het ontvangen bewijs

- Archief: `MET07_LANDELIJK_TERUG.zip`, 4087303 bytes, 7 bestanden.
- Archief-SHA256: `0ad7519f686bd665331911dcbdce0a04c2c573cc7d0398e830094f9f2ca060c1`.
- `STATUS_MET07_LANDELIJK.json`: `8d0d343437239bb849de69169bef6a0cce63a8fea65253f5758873f6610b3256`.
- `HRU_MET07_RESULTS.json`: `789d49396c237160aefda891c29fef9f2ba442ee76470b6deb47b80b66413c6b`.
- `YEAR_CACHE_RESULTS.json`: `e786b3549a26998330c6e0d0c5bbbaddeb33e8be9c8c7562d64c8499d5fea8d2`.
- `ANCHOR_MET_CHECKS.json`: `4b37f0eff6d23eda78dd76fe164b818b7cbb8177b4a5d0f71da658cce07ab912`.
- `BINDING.json`, oorspronkelijke bestandbytes: `169418c8e3cabe6fff5e161218c2a2630186bc4674d63f1b78931a11359e8ea4`.
- BINDING als canoniek geserialiseerd object: `5bfdb74d06ee55cb7b1a4555637d75c9c94cf5bad3bff04ca7c06af6428d62ee`.
- `HUM_SOURCE_LEDGER.csv`: `86ff1262f407bcc2287315fd2dd39eedcbdaeb5da3d31fd35d5c9059400683a5`.

Alle zes payloadhashes kloppen met `ARCHIVE_HASHES.json`. De verschillende bytehash en objecthash van BINDING zijn correct: het zijn verschillende serialisaties, geen identiteitstegenstrijdigheid.

## Volledige resultatencontrole

| Onderdeel | Uitkomst |
| --- | ---: |
| HRU-records | 10242 |
| Unieke HRU-ID's | Exact 1 tot en met 10242 |
| `MET07_REBOUND_HASH_VERIFIED` | 10242 |
| Gerapporteerde fouten | 0 |
| Nieuw aangemaakte / hergebruikte pakketten | 10242 / 0 |
| Dagrecords per HRU | 19358 |
| Jaarcaches | 53, exact 1970 tot en met 2022 |
| Overeenkomst met zes proef-MET-hashes | 6 van 6 |
| Non-HUM-bytes ongewijzigd volgens elk serverrecord | 10242 van 10242 |
| Overige modelinvoer ongewijzigd volgens elk serverrecord | 10242 van 10242 |
| Pakketten met 6 / 7 modelinvoerbestanden | 9581 / 661 |
| Totaal modelinvoerbestanden volgens resultatenlijst | 62113 |
| Totaal modelinvoerbytes volgens resultatenlijst | 25574864407 |
| Minimale / maximale HUM volgens jaarcaches, kPa | 0.1397736072540277 / 2.5425524711608936 |
| Dagen met donorvervanging / vervangen doelcellen | 0 / 0 |

Alle oorspronkelijke catalogushashes zijn teruggekoppeld naar de eerder ontvangen volledige assemblagelijst. Alle nieuwe doelpaden verwijzen uniek naar de juiste `run_<HRU met vijf cijfers>` onder de MET07-doelmap. De HRU-periodes, bestandsaantallen en gerapporteerde invarianten zijn per record gecontroleerd.

Het dagelijkse bronregister bevat exact alle 19358 opeenvolgende dagen van 1970-01-01 tot en met 2022-12-31. Het is byte-identiek aan het oorspronkelijke ontvangen bronregister van de zes geslaagde proeven. De 53 afzonderlijke jaarregisterhashes zijn opnieuw berekend uit de bijbehorende dagelijkse bytes en stemmen allemaal overeen met de jaarcachemetadata. Ook de populatie, periode, methodebinding, eindige HUM-extremen en nul donorvervangingen kloppen onderling voor alle 53 jaarverslagen. De numerieke cache-arrays zijn niet meegeleverd; hun waarden zijn hier niet opnieuw berekend.

De zes HRU's 1, 3, 181, 7870, 7871 en 7929 hebben in het nationale rapport exact dezelfde volledige MET-hashes als in de oorspronkelijke `MET_HUM_PROEF_TERUG.zip`. Dit is gecontroleerd tegen de werkelijk opnieuw gelezen proefrapporten, niet uitsluitend tegen de nationale `expected`-velden. Deze hashgelijkheid is geen nieuwe modelrun.

De teller `changed_hum_tokens` is 19358 bij 9502 HRU's en 19357 bij 740 HRU's. Alle HRU's rapporteren wel 19358 verwerkte dagen. Het aantal daadwerkelijk gewijzigde tokens is niet hetzelfde als het aantal verwerkte dagen; deze twee velden zijn niet gelijkgesteld.

Het statusrapport meldt voltooiing op `2026-11-17T12:51:45.790362+00:00`, met `ALL_10242_HUM_CORRECTED_REBOUND_NOT_PRODUCTION_ADMITTED`, `production_enabled=false` en `swap_executed=false`.

## Aansluiting op het bestaande batchpakket

Het daadwerkelijk geleverde `LWKM_SWAP431_Batch_v01.zip` is opnieuw geopend: 56892 bytes, SHA256 `985fac07a9e96f85526314e39e1b459a1048f6806a3bc231481312b8dcb09481`.

Het ontvangen BINDING-object is exact gelijk aan `evidence/met07_expected_binding.json` in dit pakket. De verwachte objecthash, populatie, periode, zes regressiehashes en serverpaden in `batch_config.json` komen overeen. De negen gerapporteerde herstelmodulehashes zijn vergeleken met de werkelijke Python-bytes in het eerder geleverde landelijke MET07-pakket en kloppen allemaal.

Er is geen volledige `load_met07`-servergate lokaal gesimuleerd: de controle van het werkelijke root-BINDING-bestand, catalogi en modelinvoer blijft bij de bestaande servervoorbereiding. De uitgevoerde ontvangstcontrole bevat 45 geslaagde controlegroepen en nul afwijzingen. Dit zijn controles op ontvangen bewijs, geen 45 wetenschappelijke modeltests.

Afgeleid downloadrapport: `LWKM_MET07_Landelijk_Ontvangst_20261117.json`, SHA256 `af3c2d3515d17678eb94e320cada23a54b03fd90dfbbcb1d957076b925e8277d`.

## Vervolg op de server

Gebruik het al geleverde batchpakket. Open CMD in de map met de starters. Eerst:

```cmd
01_BEREID_REFERENTIERUN_VOOR.cmd
```

Alleen na succesvolle voorbereiding:

```cmd
02_START_REFERENTIEBATCH_100.cmd
```

De startbatch gebruikt maximaal twee processen tegelijk, de bestaande SWAP 4.3.1-executable en de ongewijzigde periode 1970 tot en met 2022. De gecorrigeerde bronmap is:

```text
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_rebuilds\SWAP_HRU_Server06_MET07_1970_2022_v01
```

Na de startbatch `SWAP_BATCH_TERUG.zip` ontvangen en beoordelen. Nog niet met starter 03 naar de hele populatie uitbreiden. Geen nieuwe correctie, assemblage, kalibratie of LHM-waterbalansanalyse nodig op grond van deze ontvangst. Oude MET06-bestanden blijven uitgesloten voor deze berekeningen. Deze commit wijzigt uitsluitend de ontvangstnotitie; geen runnerwijziging en geen merge naar main.
