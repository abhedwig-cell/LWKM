# Frank/NHI exporter v0.3: afzonderlijke DRN- en RIV-systemen

Projecteigenaarbesluit 4 november 2026: **STO en BND niet exporteren**; schrijf **DRN SYS1–3** en **RIV SYS1–4** ieder afzonderlijk, naast de totalen.

De feitelijk gebouwde en lokaal geteste Python-software is als gebruikersdownload geleverd: `LWKM_Frank_LHM_Server_v03_SYSTEMEN.zip`. Dit vervangt v0.2 voor MODFLOW-export. Code is nog niet als source tree in Git opgenomen, alleen pakket in conversatie en deze release-notitie. De zes hoofdposten plus subklassen zijn QLAT, originele FLF, WEL, GHB, DRN_SYS1..3, RIV_SYS1..4. Daarnaast worden DRN_TOTAAL, RIV_TOTAAL, QEXT4 en DRN+RIV afgeleid. Waarden zijn in getekende m3/volle MODFLOW-cel/jaar en equivalente mm/jaar per 62500 m2; SVAT-oppervlak is geen deler.

Belangrijke operationele verandering: nieuwe outputdirectory `LWKM_run_resultaten_totaal/frank_export_modflow_systemen_v03`; v0.2 checkpoints mogen niet worden hergebruikt. Starters `CONTROLE_MODFLOW_2020.cmd`, `START_MODFLOW_PROEF_2020.cmd`, en klimaatvarianten gebruiken Deltaforge Python. Hard fail bij ontbrekende systeem-IDF; proefrun lokaal met gemockte synthetische 2 SVAT×2 dagen, totalen, conversie en join geslaagd; originele MetaSWAP-test (36 decades) geslaagd, ZIP-integriteit geslaagd.

**Echte NHI-server-run nog niet geverifieerd.** System-IDF padpatronen gebaseerd op bestaande WB03: `bdgdrn_sys{i}_YYYYMMDD000000_l1.IDF` (i=1..3), `bdgriv_sys{i}_YYYYMMDD000000_l1.IDF` (i=1..4). Verifieer broninventaris/check-only, dan proef-2020, daarna klimaatperiode.

Let op: de systeem-totalen zijn sommen van de **origineel getekende** budgetten; geen herinterpretatie als Frank `Fldrou/Fldrin` zonder passende teken- en fluxsplitsing.