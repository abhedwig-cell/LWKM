# Frank productieketen v0.2: bronbeheer en veilige referentie-adoptie
Datum: 10 november 2026
Status: **LOKAAL GETEST, NHI-NIET-UITGEVOERD, GEEN NIEUWE PRODUCTIE TOEGELATEN**

## Geleverd codepakket

`LWKM_Frank_Pipeline_v02_Bronbeheer.zip` als conversation artifact. Exact negen originele producenten plus drie gedeelde readers komen byte-identiek uit `LWKM_Frank_Pipeline_v01.zip` (6 november). Hun 12 SHA256's zijn zelfstandig vastgelegd in Git:
`config/production/frank_original_producers_sha256_v01.json` en controlecode `tools/lwkm_frank/release_integrity.py`. Tests: `tests/test_lwkm_frank_release_integrity.py`. De rekenmodules zelf zijn **nog niet als twaalf losse Git-bronbestanden opgenomen**. Deze beperking moet eerst worden gesloten voor formele code-integratie.

Nieuwe lokaal uitgevoerde toetsen:
- `test_pipeline.py`: 9 producenten hebben parseerbare `--help`, dependencies, ID- en kolomcontrole, Gebied-NoData policy.
- `test_pipeline_v02.py`: oorspronkelijke referentie beschermd; geen impliciete globale invoer onder run-lokaal profiel.
- `test_release_integrity.py`: ongewijzigde 9 producenten + 3 readers matchen de 12 oude SHA's, afwezige files leveren fail.
- `py_compile` alle Python; ZIP-integriteitscontrole; 32 bestanden.

## Onderverdeling van de controller

De oorspronkelijke historische productiemodus staat in `pipeline_config.json` met `source_profile=legacy_reference`. Het oude `E:\LHM_4.3.3\Data\2_Model_Input\metaswap\inp\area_svat.inp` is uitsluitend historische evidence voor de eerder geproduceerde referentie; **niet** de norm voor nieuwe runs.

`pipeline_run_local_TEMPLATE.json` heeft `source_profile=run_local` en aangewezen `run_name`. Hier staat een *kandidaat* `run_1970_1979/metaswap/inp/area_svat.inp`; de effectieve locatie moet eerst uit echte run-directory worden gebonden. Projecteigenaar bevestigt dat de statische MetaSWAP-invoer tussen runs identiek is; hashes zijn eenmalige, bevestigende QA, geen routinematige blokkade.

- `CONTROLE_FRANK.cmd`: snelle aanwezigheid/kolomcheck, geen producer, geen volledige SVAT telling.
- `VERIFY_FRANK.cmd`: controleert alle bestaande CSV's op 645582 unieke SVATs en vereiste kolommen (dure leestoets).
- `VERIFY_REFERENCE.cmd`: SHA256 van werkelijke `FRANK_SVAT_BASIS_ONGECORRIGEERD_1991_2020.csv` tegen `7ec5b7bf24f5f8552d655bed96a71f97d088bcbc088201a293752dd46ac559df`.
- `VERIFY_SOURCECODE.cmd`: SHA256 controle van originele producenten en readers.
- `START_FRANK.cmd`: uitsluitend controle en expliciete heradoptie van **bestaande** originele CSV's als `REUSED_LEGACY_STRUCTURAL_ONLY`, niet opnieuw berekenen. Geen nieuwe NHI-output producer starten.
- `TEST_FRANK.cmd`: lokale regressietests.

Nieuwe `frank_pipeline_v02/PIPELINE_STATUS.json` maakt expliciet onderscheid tussen status-only, bestaande structuurvalidering en bronkwalificatie. De controller staat niet toe dat run-lokale output in dezelfde historische directories zonder fingerprints wordt hergebruikt. De **berekeningsroute is bewust fail-closed**, zelfs met `--allow-compute`, omdat originele producers nog vaste outputdirs en uiteenlopende cache/bronfingerprints hebben. Eerst geïsoleerde nieuwe namespaces en exacte module-scopes bouwen.

## Werkelijke resterende implementatie

1. Commit de negen producerbronnen plus drie readers onder `tools/lwkm_frank/legacy`, met Git-source hashes exact gelijk aan registratietabel. Het v02 ZIP is momenteel de code-overdracht.
2. Maak centraal versiebeheerbare `run_definition` die effectieve run-lokale MetaSWAP-input koppelt aan `control_run_*.ini` en de geautoriseerde outputroot. Geen `svat_border` of globale `E:`-fallback.
3. Refactor één producer tegelijk naar `--config`, nieuwe geïsoleerde outputdir en atomair checkpoint/restart-schema, zonder numerieke wijziging.
4. Voor iedere stap: input+code+config SHA en inhoudsregressie. Oude Frank-referentietabel blijft onaangeroerd.
5. Pas na een clean-run equivalentietest de centrale `run`-route productietoelaten.

Dit pakket verbetert het bronbeheer en de veiligheidsgrenzen concreet, maar is **nog geen** afgeronde, wetenschappelijk reproduceerbare LHM-naar-SVAT-productieketen.
