# LWKM vervolg na WB27: terug naar productie SVAT → HRU → SWAP

4 november 2026. Projecteigenaar: WB27 beëindigen, bevindingen vastleggen, HRU-productie voortzetten.

## Gecontroleerde branch- en contractbasis
- `integration/hru-population-variable-20261028`: actuele HRU-populatie.
- `work/swp-direct-hru-20261029`: SWP-productie.
- `work/work-e-bbc08-20261029`: BBC-stroom.
- `docs/lhm-hru-swap/README.md` beschrijft canonical keten LHM_EXPORT → SVAT_BASE → SVAT_QUALIFIED → SVAT_HRU_MAP/HRU_SCHEMA → SWAP_INPUT → SWAP_OUTPUT_QA; actuele HRU10242 is authority.
- WB27 bevindingen: `docs/production/WB27_GW_DEPTH_STO_CLOSURE_20261104.md`.

## Functionele scope komende integratiestap
1. Herstel en toets (niet herschat) de SVAT→HRU mapping en cel-/SVAT-oppervlakcontracten, inclusief expliciete uitsluiting van kwalificatieproblemen.
2. SWP per HRU: valideer dat gekozen `cropfile` en atmosferische CO2-file daadwerkelijk in dezelfde HRU-outputmap terechtkomen; landgebruikscodes lu1=gras, lu2=mais, lu3=bouwland, lu4=natuur; lu4 mag niet stilzwijgend ontstaan voor al geselecteerde HRU's.
3. Irrigatie: `schedule=1` waar originele planning aanwezig, anders `schedule=0`; toekenning en totale arealen uit SVAT-oppervlakken, bij gelijk beregend oppervlak voorkeur voor grondwater; bestaande versoepelde beslisregel behouden, niet herdefiniëren zonder regressietest.
4. BBC-contract: volledig MODFLOW-celoppervlak (62500m² op 250 m raster) en oorspronkelijke budgettekenconventie; niet SVAT- of HRU-oppervlak op BBC toepassen. Dagelijkse QEXT=QLAT+originele FLF+WEL+GHB; FLF-correctie Flevoland als aparte diagnostiek, niet in canonical historic reconstructie mengen.
5. DRA-configuratie: afhankelijk van aantal bodemlagen uit SWP, geen toepassing van beregeningsoppervlakken bij DRA.
6. Productie moet op NHI/LHM Windows-server zonder Python waar van toepassing als zelfstandige EXE draaien, met vaste `LWKM_tools`-startdirectory en eenvoudige CMD-starter. Nieuwe tools uitsluitend na test op daadwerkelijke artefacten als 'server-ready' aanmerken.

## Begrenzing waterbalans
- `qmodf` slechts diagnostisch, niet onafhankelijk bij QEXT optellen.
- Geen automatische STO-switch gebaseerd op residual fit of grondwaterdiepte; klasse 4 blijft diagnostisch.
- Bewaar prognose- en kwalificatieflags; geen onbewezen fluxcorrecties.

## Volgende verificatie
Controleer echte branch-heads en laatste PR-integratie voor SWP/BBC/DRA versus HRU10242; voer eerst bestaande regressietests en een sample dry run uit. De huidige Git-notitie is **geen** bewijs dat productiecode van deze werkbranches reeds gemerged of tegen de server is getest.
