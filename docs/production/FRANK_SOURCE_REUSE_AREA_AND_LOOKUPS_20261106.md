# Frank SVAT basistabel: eerste bronnen en bestaande lookups (6 november 2026)

Doel: bestaande NHI-bronwaarden hergebruiken voor Frank, zonder onnodig opnieuw data op te bouwen. Eerst source binding controleren, dan op NHI-server assembleren.

## Direct uit area_svat.inp
De officiële MetaSWAP-IO-documentatie (Report 913.3 V8.1.1.4, §2.3.1) noemt `svat` (ID), `ark` (m2), `glk` (maaiveld), `slk` (bodemfysische eenheid), `luk` (landgebruik), `dprzk` (wortelzone), `nm` (meteorologische regio), `tempCbotk`, `cfPm`, `cfETref`. De gebruikte lokale Python-reader leest uit het actuele 14-tokenbestand SVAT id `a[0]`, area `a[1]`, RD-X `a[9]`, RD-Y `a[10]`; de betekenis van andere tokenposities van **de exacte NHI-variant** eerst op een beperkt aantal echte regels verifiëren voordat nieuwe indexen worden vastgelegd.

MetaSWAP `luk` is niet bij definitie `landgebruik22`; `slk` is niet bij definitie `bodem370`; `nm` is geen bewezen vervanger voor Franks `Gebied`; `glk` is maaiveldhoogte, niet GLG/GG. Bind alleen na kruistoets tegen oorspronkelijke `BasicData/grids/lgn250.asc`, `bodem.asc` en zo nodig de historisch gerealiseerde SVAT-populatie. Controleer eenheden, unieke ID's en volledige 645582 SVATs.

Bron: https://nhi.nu/documents/49/MetaSWAP_Report_913_3_V8.1.1.4.pdf

## Hergebruik gekwalificeerde repository-tabellen
1. `config/preprocessing/landuse-mapping-realized-v1.csv`: historische gerealiseerde directe `landgebruik22 -> lu7,lu4,lu2`. 19 source landuse codes, geen ongedocumenteerde extrapolatie.
2. `config/p12/bodem370_classification_lookup.csv`: `bodem370 -> bofek79,pawn21,grondsoort4,grondsoort2`. 370 bodemcodes in lookup; 365 gerealiseerd gekwalificeerd; geen authority voor de vijf ongeobserveerde codes `{14,142,143,197,198}`. Niet de oudere BOFEK referentietabel ongewijzigd gebruiken wegens tien erkende verschillen.
3. `tools/recover_preprocessing_mappings.py`, `tools/build_bodem370_lookup.py`: deterministische checks. `tools/build_svat_from_rasters.py` ondersteunt brongebonden rasters/lookup met expliciete SHA256 en ontbrekende-data-gate.
4. `config/preprocessing/upstream-product-inventory-v1.yml`: oorspronkelijke `lgn250.asc`, `bodem.asc`, district `ECHO_toestroom_geclusterd_66gebieden.asc`, `gt.asc` en `Riv_infiltratie_1991-2020_sum.asc` als mogelijke inputs; veel postprocessed grids zijn al afgeleid en hoeven niet opnieuw te worden geproduceerd als oorspronkelijke bron+lookup toereikend zijn.
5. `config/preprocessing/lookup-chain-manifest-v1.yml`: lookupbestanden voor `gt`, GHG- en kwelklassen worden genoemd maar niet alle drempeltabellen zijn in de repository als waarden vastgelegd. Niet raden.

## Frank-veldroute
- Rechtstreeks: SVAT, Opp_svat, x/y, glk; mogelijk luk/slk/nm na de broncodekruistoets.
- Lookups: Landuse->LU4,LU2; Bodem370->Pawn21,Grondsoort4,Grondsoort2.
- Reeds onafhankelijk geproduceerd: GHG, GLG, GVG, GG, Dynamiek uit layer-1 head; neerslag/ET/runoff uit MetaSWAP; 16 bruto MODFLOW-fluxen.
- Aanvullende bron: district/`Gebied` uit relevante district- of 66-gebiedenbron, GT-class rule uit erkende legacy grid of bestaande code, kwelklasse4 uit echte class-boundary/lookup, beregening uit juiste output, evaporatiecomponenten uit afzonderlijke decadische MetaSWAP-IDFs en niet uit totale ET.
- Onbekend: `Indicator vervangen Svats` uit versioned donor/replacement relation; `N ???` pas na Frank/Leo.

## Voorgesteld minimaal server-checkpoint
Een beperkte read-only probe op `area_svat.inp` (header/eerste regels plus domeinverdelingen voor slk/luk/nm), veldvergelijking tegen `lgn250.asc`/`bodem.asc` voor exact overeenkomende SVAT-coördinaten; die valideert de twee essentiele 1:1 identiteiten voor gebruik van repository-lookups. Geen nieuwe hydrologische berekening en geen grote CSV-export voordat dit is opgelost.

Geen claim dat op 6 november deze volledige bron-naar-sourcecode-conversie al op NHI-server getest is.
