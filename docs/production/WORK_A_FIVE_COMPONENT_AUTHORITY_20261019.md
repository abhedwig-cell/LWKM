# Work A: bestaande vijf fluxproducten en uitvoering

Het aanvullende projecteigenaarbesluit van 19 oktober 2026 bindt de bestaande dagelijkse FLF-, FRF-, FFF-, GHB- en WEL-producten. WEL en GHB staan in `LWKM_run_resultaten_totaal/modflow/bdgwel` en `bdgghb`, met aangewezen periode 1970-2022. Dit is een bronaanwijzing van de eigenaar, geen claim dat deze runtime alle dagelijkse bytes heeft geverifieerd. Er is geen reconstructie opnieuw uitgevoerd en geen analyse van oorspronkelijke MODFLOW-face-semantiek heropend.

## Vastgelegde authority

De bestaande `LWKM_MF_L1_Balance.cs`, afkomstig uit het eerder aangeleverde balanspakket, is ongewijzigd opgenomen in `docs/evidence/2026-10-19-work-a-five/`. De componentfunctie documenteert de samengevoegde locaties `modflow/bdgfrf/bdgfrf_YYYYMMDD_l1.idf` en analoog FFF, FLF en WEL. FLF ondersteunt ook de vastgelegde datum met `000000`. De GHB-locatie en beperkingen staan in de bestaande uitroldocumentatie onder `docs/evidence/2026-10-19-work-a-owner/`.

De bestaande C#-balanslus, regels 139-143, definieert de opgeslagen richting als:

- FRF-netto = huidige cel minus vorige kolom, aan de linker modelrand zonder vorige cel.
- FFF-netto = huidige cel minus vorige rij, aan de bovenste modelrand zonder vorige cel.
- FLF wordt met het opgeslagen positieve teken gebruikt.

GHB/WEL behouden hun vastgelegde positieve richting naar laag 1. Dit is een hergebruik van de bestaande opslagconventie. De oudere generieke MODFLOW-tekenaudit wordt niet gebruikt om deze opgeslagen producten opnieuw te interpreteren. Het besluit van 18 oktober voor de HRU-laag-1-balans blijft de ruimtelijke authority, met het aanvullende besluit van 19 oktober als bronroute.

Het plan maakt de ruimtelijke bewerking expliciet als `SAVED_CURRENT_MINUS_PREVIOUS_COLUMN`, `SAVED_CURRENT_MINUS_PREVIOUS_ROW` of `CELL_NET`. Reeds netto opgeslagen componenten krijgen uitsluitend `CELL_NET`. Termen worden niet dubbel gedifferentieerd. De viercomponentenroute blijft compatibel, maar de vijfcomponentenroute bewaart FRF en FFF ook afzonderlijk in dagelijkse cel- en HRU-uitvoer. `LAT=FRF+FFF` blijft beschikbaar. De externe flux telt LAT slechts eenmaal mee.

## Daadwerkelijk geproduceerde HRU-randvoorwaarden

De bestaande bronproef van 1 juli 2020 is opnieuw verwerkt met de vastgelegde FRF/FFF-bewerking. Op 427.391 vergelijkbare echte broncellen wijkt FRF+FFF maximaal 4,375e-9 m³/d af van de eerder opgeslagen LAT. Dit is afronding van de bestaande CSV, geen nieuwe tekenkeuze. De volledige membership omvat 427.656 cellen en 10.242 HRU's.

Er zijn zes complete HRU-randvoorwaarden en zes BBC-bestanden geproduceerd, voor HRU 3363-3368. De generieke vijfcomponentenprocessor is eveneens echt uitgevoerd op deze zes HRU's, gevolgd door een succesvolle incrementele herhaling. Alle vijf componenten, LAT, oppervlakten en mm/d staan in de evidence.

De GHB-invoer van deze lokale regressie is het reeds opgeslagen onderzoekproduct uit de eerdere bronproef. Het is alleen opnieuw als raster geserialiseerd; conductantie of heads zijn niet opnieuw gebruikt voor reconstructie. De bekende oudere head-datering blijft expliciet gemarkeerd. Deze proef vervangt dus niet het binden van de aangewezen dagelijkse serverreeks `bdgghb`. Onvolledige HRU's zijn niet met nul aangevuld. De zes bestanden zijn onderzoeksproducten en geen volledig toegelaten moderne productieruns.

## BBC-interface: echte modelproef en gevonden beperking

De nieuwe experimentele BBC-serializer beschrijft elke dag door twee gelijke fluxwaarden op opeenvolgende middernachten. Dubbele datums markeren de overgang. Daardoor is de wiskundige dagintegraal exact gelijk aan de aangeleverde mm/d. Een eerste driedaagse proef voltooide en behield alle drie volumes exact. Die proef bleek onvoldoende representatief.

Er zijn vervolgens 98 echte SWAP 4.3.1-berekeningen uitgevoerd op de 49 bestaande C2-pakketten, met DTMAX 0,04 en 1 dag. De expliciet synthetische interfacefluxen bevatten tekenwisselingen, nul en kleine waarden. Dit zijn geen moderne LHM-forcings. Alle 98 berekeningen voltooiden normaal, maar slechts 45 behielden ieder dagvolume binnen 1e-7 mm. Bij DTMAX 0,04 slaagde geen van de 49 gevallen voor deze volumetoets; de maximale afwijking was 0,2 mm/d. Over alle runs was de maximale afwijking 1,1511 mm/d. De maximale gerapporteerde interne BALDEV was 2,853e-5 mm. Een kleine interne waterbalansfout bewijst dus niet dat het juiste externe dagvolume is opgelegd.

De bestaande SWAP-broncode bepaalt `BoundBottom` vóór de lus die de tijdstap kan verkorten. `boundbottom.f90` vraagt AFGEN op `t1900+dt`; de flux kan daardoor al de volgende dag betreffen wanneer dt later wordt ingekort. De modeluitvoer bevestigt de fout rond dagovergangen. De evidence bevat alle invoer, uitvoer, waarschuwingen en logs. Een eerder ontdekte parserfout bij een integer nul in een reële kolom is verholpen door nul als `0.` te schrijven.

Deze BBC-traproute blijft daarom uitsluitend beschikbaar met `experimental_daily_steps=True`. De standaardroute weigert variërende daggemiddelden. Constante intervallen, waaronder de zes geproduceerde eendaagse BBC's, blijven beschikbaar. Er wordt geen wetenschappelijke toelating geclaimd voor het variërende profiel. De engine is niet gewijzigd. De maximale tabelcapaciteit van de standalone 4.3.1-bron is 36.600 regels; grotere dagreeksen moeten in uitvoerperioden worden opgesplitst.

## Serveruitvoering en resterende grens

Gebruik `tools.server.make_five_component_config`, vervolgens `tools.server.bind_reconstructed_daily`, de bestaande Q0-Q4-collector en `tools.process_daily_budget_plan`. De bijgewerkte serverhandleiding geeft de commando's. Correcte objecten worden hergebruikt, gehashte inhoud wordt gecontroleerd en ontbrekende dagen blokkeren een uitvoerbaar plan. Er worden alleen de geselecteerde componentmappen en datums gelezen, geen nieuwe reconstructies of oorspronkelijke budgetten gezocht.

Deze runtime heeft nog geen toegang tot de Windows-bronmap. Daardoor ontbreken de operationele dagelijkse GHB-reeks en volledige gemeenschappelijke forcing hier nog. Ook volledige moderne MET is niet gebonden. Dit verhindert moderne volledige pakketten en nieuwe brongebonden SWAP-runs. De variërende BBC-interface heeft daarnaast de hierboven concreet aangetoonde technische beperking. De bestaande C2-resultaten en 29 drainageblokkades blijven behouden. Het ontbreken van oorspronkelijke WEL/GHB-budgetten en het ontbreken van een aparte LAT-map zijn geen zelfstandige blokkades.

## Reproduceerbare controles

De volledige lokale suite slaagt met 378 tests en 3 subtests. De vijfcomponentenprocessor en de onafhankelijke bronreplay verschillen maximaal 4,336e-9 mm/d, binnen de vastgelegde 1e-8 mm/d-regressietolerantie. De scripts `replay_existing_five_components`, `bind_snapshot_five_regression` en `qualify_daily_bbc_steps` bevatten CLI-ingangen voor herhaling; volledige modelinvoeridentiteiten en uitvoer staan in de evidence-ZIP. De incrementele processorproef hergebruikt beide dagbestanden byte-identiek.
