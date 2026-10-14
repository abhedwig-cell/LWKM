# LWKM waterbalansen 1991–2020: WB1–WB5 overdracht (14 oktober 2026)

Status: **KANDIDAAT, niet wetenschappelijk toegelaten als sluitende waterbalans**.

## Doel en overeengekomen grenzen

Een transparante waterbalans voor MetaSWAP plus MODFLOW-laag 1, met diagnostische deelbalansen voor beide modellen. Alle termen langjarig gemiddeld 1991–2020, in miljoen m³/jaar en mm/jaar. Onbekende laterale grensfluxen, overige laag-1-onttrekkingen en BDGSTO blijven onbekend en worden niet op nul gezet. `qlat` wordt niet gebruikt. BDA/PDA-uitvoer is niet beschikbaar. De gedeelde grondwaterstand maakt dat `bdgqmsw` en `bdgqmodf` niet elkaars tegenpost hoeven te zijn.

- WB1: voorlopig geldig landelijk rasterdomein, Nederlandse landsgrens nog niet definitief bewezen.
- WB2: landbouw en natuur volgens `filter_lwkm.asc`.
- WB3: WB2 plus gecorrigeerde FLF, met zowel FLF-only als afzonderlijke boekhoudkundige compensatie op oppervlaktewatersysteem 1.
- WB4: WB3 exclusief `verdacht.asc > 0`.
- WB5: WB3 met donorvervanging voor verdachte SVAT's, waarbij het oorspronkelijke gebied behouden blijft. WB5 is een **scenarioaanname** en niet bewezen identiek aan de historische donorprocedure.

## Bronnen en numerieke afspraken

Bronrasters uit `wbuitvoer(1).zip`, gecorrigeerde FLF ZIP, `UOPP.ASC`, `filter_lwkm.asc`, `verdacht.asc`, `area_svat.inp`, `scap_svat.inp`, `export_svat_HRU_NRU_10242(2).csv`. Bewaar bronidentiteiten en scripts bij de overdracht.

MODFLOW gebruikt volledige 250 × 250 m cellen (62.500 m²); MetaSWAP is oorspronkelijk m³/m² op `UOPP`. Geproduceerde jaarras ters kunnen al naar mm/jaar zijn omgerekend; voorkom dubbele conversies.

De afgeleide `bdgqmsw` wordt volgens eigenaarbesluit **voor alle cellen opnieuw berekend** uit zes oorspronkelijke MetaSWAP-termen, geschaald met UOPP/62500. Het oude `bdgqmsw`-raster is uitsluitend historisch vergelijkingsmateriaal. Tel de afgeleide term niet bovenop de zes componenten.

Runoff is een zelfstandige MetaSWAP-afvoerterm. `Psgw` en `Pssw` zijn beregening uit respectievelijk grondwater en oppervlaktewater. Alleen voor SVAT 207543 is in `scap_svat.inp` laag 1 gevonden; de eigenaar staat toe diens `Psgw` als even grote MODFLOW-laag-1-onttrekking te boeken. Berekening: 145,46 m³/jaar, interne tegenpost, opgenomen voor WB1–WB4 en analoog te behouden bij WB5 zolang dezelfde SVAT niet wordt vervangen. Eén SVAT per rastercel.

## Donorvervanging WB5

Van de 20.709 verdachte cellen op de gemeenschappelijke geldige WB2-support zijn 19.394 aan een andere donor met beschikbare waarden gekoppeld; 1.315 hebben geen andere donor. Van de gebruikte donoren zijn 1.472 zelf als verdacht aangemerkt. **Dit is een open kwaliteitsvraag, geen automatisch goedgekeurde correctie.**

Voor WB5 zijn als scenario alle beschikbare MetaSWAP- en MODFLOW-waterbalanstermen door donorwaarden vervangen bij de 19.394 cellen, terwijl de ontvangende SVAT, coördinaten en het eigen UOPP behouden blijven. Deze aanpak is nog niet bewezen gelijk aan de historische herschikkingsprocedure. Donorrelatie, oorspronkelijke en nieuwe waarden moeten per SVAT zichtbaar zijn.

De Flevoland-FLF-correctie en systeem-1-compensatie blijven afzonderlijk herkenbaar, evenals een binaire indicator of de FLF-correctie de cel raakt.

## Overdracht: één Excel plus één CSV

De Excel bevat de samenvatting WB1–WB5 in mm/jaar, leeswijzer, metadata, kolomdefinities en kwalificatiestatus, **zonder** 427.654 grote celregels. De CSV bevat alle oorspronkelijke SVAT/celgegevens plus WB5-donorwaarden naast elkaar, één regel per SVAT. De laatste bestandsnamen in de conversatie:
- `LWKM_waterbalansen_WB1_WB5_met_CSV_metadata.xlsx`
- `LWKM_WB5_replaced_full.csv`

De CSV bevat 427.654 SVAT-regels en 41 kolommen. Beide artefacten zijn conversatiebestanden en zijn **niet** door deze documentatiecommit als binaire bestanden in Git opgeslagen. De Excel/CSV dienen samen te worden bewaard. Controleer bij overdracht bestandshashes, werkelijke kolomnamen, 19.394 donorvervangingen, de WB5-sommen en de Flevolandmarkering. Niet aannemen dat het Excelbestand technisch correct is zonder heropening en validatie.

## Openstaande werkzaamheden

1. Exacte donorsemantiek van Leo's vervangingsroute tegenover Piet's HRU-clustering reconstrueren en beide routes onafhankelijk vergelijken.
2. De landgrens WB1 en de enkele ontbrekende MODFLOW-rastercellen kwalificeren.
3. Broneenheden, tekens, bergingsbetekenis en onafhankelijke externe termenset vaststellen.
4. Laterale MODFLOW-grensfluxen, overige onttrekkingen en BDGSTO later uit oorspronkelijke MODFLOW-uitvoer reconstrueren; residu nooit kunstmatig als qlat benoemen.
5. Definitieve fysieke deelbalansen en gecombineerde balans pas presenteren met expliciete ontbrekende posten.

De repository is authority voor ontwerpbesluiten; de grote rasterdata blijven buiten Git. Gebruik lokale tests; GitHub Actions alleen indien noodzakelijk.
