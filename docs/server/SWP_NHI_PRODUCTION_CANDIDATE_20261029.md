# SWP rechtstreeks uit NHI-serverbronnen

De teruggestuurde broncontrole is verwerkt: 427.656 SVAT's, 10.242 HRU's,
geen rasterleesfouten, alle punten op celcentra. De dagelijkse headuitsnede
heeft 1.124 kolommen versus 1.200 voor de statische invoer. Dat geeft geen
ontbrekende SVAT-punten en vereist geen interpolatie of verschuiving.

## Uitvoeren

Pak LWKM_WorkE_SWP_Server03.zip uit onder de gebruikelijke LWKM_tools-map.
Open CMD in de map met maak_swp.cmd:

```cmd
maak_swp.cmd
```

Geen paden invullen. De bestaande serverbestanden worden rechtstreeks gelezen.
De standaardperiode is 1970-01-01 t/m 2022-12-31. Dit maakt kandidaat-invoer,
geen SWAP-modeluitvoering.

Uitvoer onder swp_server_productie:
- runs_candidate.csv: de afgeleide 37 velden;
- swp/HRU.swp: één .swp per geslaagde HRU (bestandsnaam bijvoorbeeld 1.swp);
- dqsat_hru.csv en dqsat_source_manifest.json: HRU-waarden en rasterherkomst;
- area_source_manifest.json: area_svat-bronnen, periodevergelijking en afwijkingen;
- parameter_errors.json en diagnostics.json: fouten en bronkeuzes per HRU;
- production_manifest.json en swp/manifest.json: aantallen en hashes;
- controle.zip: klein terugrapport, ook bij een fatale invoerfout.

Deel na afloop swp_server_productie\controle.zip. De SWP-bestanden blijven op
de server; er hoeven geen grote grids of duizenden SWP's geüpload te worden.
Dezelfde opdracht kan opnieuw worden gestart. Een volledig geslaagde,
ongewijzigde parameterfase wordt hergebruikt na bron- en uitvoerhashcontrole;
ongewijzigde SWP-bestanden worden eveneens hergebruikt.

## Vastgelegde bronnen en beslissingen

- HRU-identiteit, bodem370 en de vier landgebruiksvormen blijven uit de HRU-CSV.
- Maaiveld: bestaande ahn_f250_cm.asc, expliciet *0.01 naar m NAP. De eerder
  gekwalificeerde DRA-bronbeschrijving bevestigt cm, naast de actuele waarden.
- Beginhead: dagelijks resultaat van exact 1970-01-01, in m NAP. Niet de
  stationaire initialisatiegrid uit de MODFLOW-modelconfiguratie.
- GWLI: conform v0.38 gelijke gewichten per HRU-lid voor head en maaiveld,
  daarna MIN(0,NINT((head_mean-ground_mean)*100)). Dieper dan 20 m wordt gemeld.
- SVAT-oppervlakken: rechtstreeks uit de werkelijke area_svat.inp, gekoppeld
  op oorspronkelijk SVAT-ID én X/Y (tolerantie 0,001 m). Alleen 14-koloms
  area_svat-layout zoals in de bestaande MetaSWAP-HRU-EXE wordt geaccepteerd.
  Er is geen terugval op UOPP of membership-oppervlakken en geen aftopping op
  62.500 m². BBC blijft onafhankelijk het volledige MODFLOW-celoppervlak gebruiken.
- De bestaande run_1970_1979 t/m run_2020_2022 worden gericht gecontroleerd op
  metaswap/area_svat.inp en metaswap/inp/area_svat.inp. De MS_daily-overlapruns
  en svat_border-appendage worden niet als vervanging gekozen. Bestanden worden
  gehasht; bij verschillende hashes worden de geselecteerde SVAT-waarden vergeleken.
  Als die tussen runbestanden verschillen, stopt statische nationale generatie.
  Ontbrekende periodebestanden blijven expliciet in het terugrapport staan.
- Zijn er geen periodebestanden gevonden, dan wordt alleen een reeds aanwezig
  area_svat-bestand met de SHA-256 van het door de eigenaar aangeleverde bestand
  gebruikt: 352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc.
  Daarvoor worden de bestaande MetaSWAP-exportpakketten onder LWKM_tools en de
  geconsolideerde metaswap-map gericht gecontroleerd. Dat is kandidaatgebruik van
  de aangeleverde modelinvoer, geen bewijs van gelijke bestanden in alle perioden.
  Als ook die bron ontbreekt, stopt de producer en vermeldt controle.zip de
  onderzochte locaties. Er wordt geen bronbestand verplaatst of in dit pakket
  opgenomen. De waarden worden ter plaatse gelezen.
- De lokale echte-data-audit op het eerder aangeleverde area_svat(2).inp koppelt
  alle 427.656 geselecteerde SVAT's foutloos op ID en coördinaten. Zeven SVAT-
  oppervlakken verschillen van membership en veranderen zeven HRU-totalen.
  Bijvoorbeeld SVAT 7317 / HRU 8444: 2.412.219 m² tegenover 62.500 m² in
  membership. De nieuwe producer neemt de modelinvoer over en registreert dit;
  hij verklaart de grote bronwaarde niet automatisch hydrologisch gevalideerd.
  Een verschil tussen UOPP en membership bewijst dus op zichzelf geen UOPP-
  bronfout. De beslissende oppervlaktebron is de werkelijk gebruikte area_svat.
- Worteldiepte: een aanwezige rz_repr houdt voorrang. De teruggevonden HRU-CSV
  bevat die niet; daarom wordt rootzone.asc bij de aangewezen representatieve
  SVAT gebruikt, met expliciete kandidaatinterpretatie van ruwe waarden als cm.
  Waarden 5–150 ondersteunen dit fysisch; de oorspronkelijke vijfkoloms
  representatieve worteltabel is daarmee niet als gereproduceerd aangemerkt.
- dqsat: conform eigenaarbesluit van 2026-10-09 voor iedere HRU de mediaan
  van strikt positieve waarden bij alle lid-SVAT-celcentra, zonder oppervlakte-
  of bodemselectie. Nul en exacte NoData worden uitgesloten; andere negatieve
  of niet-eindige waarden en een HRU zonder positieve waarden geven een fout.
  Dezelfde berekening wordt door de bestaande DRA-producer gebruikt.
  L = 4 * dqsat is kandidaat-drainageafstand in meter, geen kolomdikte.
  De ruwe representatieve waarde, positief gemiddelde en aantallen blijven
  afzonderlijk in dqsat_hru.csv en diagnostics.json beschikbaar.
- Alleen het eerder geïdentificeerde grensvlak_NHIWQ_v2_fill.asc wordt gebruikt,
  met SHA-256 e6f13f2308ec55089d384133296fd45e6f796eeefb81260ff8ffebef83f09c3a.
  De bestaande gridmap, 2_Model_Input-boom en LWKM_tools-boom worden tot vijf
  niveaus doorzocht op deze bestandsnaam. Alleen een exacte hashmatch wordt
  gelezen. Er wordt niets verplaatst of geïnterpoleerd. Een ontbrekende bron
  stopt de uitvoering en schrijft de gecontroleerde locaties en kandidaten naar
  dqsat_source_manifest.json in controle.zip. Een eventueel expliciet gebonden
  dqsat_grid-pad heeft voorrang en wordt nooit stilzwijgend vervangen.
  dqsat_svat.inp is niet als gelijkwaardige bron aangetoond en is geen vervanging.
- Onderrand: expliciet SWBOTB=2, SWBBCFILE=1 voor de ontwikkelde BBC09 Q_ext.
  Oude vrijedrainage-/bbc-rasterkeuzes worden niet als huidige policy heringevoerd.
- Meteoregio's blijven diagnostiek; METFIL blijft HRU.met. Geen arbitraire mode
  nodig om deze bestandsverwijzing te schrijven. Beregening volgt de v0.38
  drempel >0.37 en bronmodus, met expliciete fout bij een onbesliste bronmodus.
- Gelijke centroidafstanden worden deterministisch opgelost met het kleinste
  SVAT-ID. Dit kiest geen nieuwe HRU-identiteit en wijzigt geen hydrologische weging.
- Overgenomen v0.38 ontwerpinstellingen: 20-m-profiel/dikte_id 1700, 43 nieuwe
  knopen, COFANI 1, PONDMX .2 cm, RSRO .25, tempBot 12, SWINCO 2.

Alle daadwerkelijk gebruikte rasters worden tegen de teruggestuurde hashes
gecontroleerd. Veranderingen stoppen de uitvoering. Het dqsat-raster wordt tegen zijn eerder vastgelegde bronhash gecontroleerd.

## Kwalificatiegrens

Het serverrapport bewijst aanwezigheid, leesbaarheid en geometrische dekking.
Het bewijst geen fysische gelijkwaardigheid van alle oorspronkelijke parameters.
De vierklassengewaskoppeling blijft kandidaat met 255 verschillen tegenover de
historische tabel; generieke croporg-metadata mag geen managementbron worden.
De wortelbronkeuze blijft onderscheiden van de oorspronkelijke rz_repr-tabel.

Server01 is vervangen wegens zijn onjuiste keuze van membership als primaire
oppervlaktebron. Server02 is vervangen omdat het eerdere dqsat-besluit daarin
niet correct was verwerkt. Gebruik Server03; bestaande kandidaat-SWP's moeten
opnieuw met deze versie worden afgeleid. Een ongewijzigde oude cache wordt
niet hergebruikt omdat de broncodehash is gewijzigd.

De lokale echte-brontoets van 2026-10-30 omvat alle 427.656 SVAT's / 10.242 HRU's:
geen verschil tussen server- en DRA-berekening, 515 uitgesloten nulwaarden,
geen NoData onder deze leden, 2.835 HRU-medianen anders dan de representatieve
waarde en alle 14 representatieve nullen opgelost met positieve leden. Het
bereik is dqsat 2–20 m en kandidaat-L 8–80 m. Dit is methodische consistentie,
geen kwalificatie van SWAP-respons of hydrologische productie.

De software is lokaal getest van grids tot geschreven SWP. De eerdere vier
historische SWAP-runs valideren de renderer, niet deze nieuwe nationale
parameterafleiding. Pas het server-terugrapport toont hoeveel HRU's hiermee
werkelijk zijn geproduceerd. Er is nog geen nationale SWAP-uitvoering of
hydrologische vrijgave. BBC/DRA/MET/CRP-bestanden moeten afzonderlijk met de
SWP-bestanden worden samengesteld voordat SWAP kan rekenen.
