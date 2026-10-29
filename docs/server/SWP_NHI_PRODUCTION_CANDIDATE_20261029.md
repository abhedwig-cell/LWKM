# SWP rechtstreeks uit NHI-serverbronnen

De teruggestuurde broncontrole is verwerkt: 427.656 SVAT's, 10.242 HRU's,
geen rasterleesfouten, alle punten op celcentra. De dagelijkse headuitsnede
heeft 1.124 kolommen versus 1.200 voor de statische invoer. Dat geeft geen
ontbrekende SVAT-punten en vereist geen interpolatie of verschuiving.

## Uitvoeren

Pak LWKM_WorkE_SWP_Server01.zip uit onder de gebruikelijke LWKM_tools-map.
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
- SVAT-oppervlakken: bestaande gekwalificeerde membership, afkomstig van de
  SVAT-afleiding. UOPP.ASC is bewust geen vervangende bron: 5.579 NoData en een
  maximumverhouding 38,595504 tegenover de gekwalificeerde SVAT-oppervlakken.
  Er worden geen SVAT's wegens UOPP-NoData weggelaten. BBC houdt onafhankelijk
  de eerder voorgeschreven volledige MODFLOW-celoppervlakken.
- Worteldiepte: een aanwezige rz_repr houdt voorrang. De teruggevonden HRU-CSV
  bevat die niet; daarom wordt rootzone.asc bij de aangewezen representatieve
  SVAT gebruikt, met expliciete kandidaatinterpretatie van ruwe waarden als cm.
  Waarden 5–150 ondersteunen dit fysisch; de oorspronkelijke vijfkoloms
  representatieve worteltabel is daarmee niet als gereproduceerd aangemerkt.
- dqsat_svat.inp wordt op SVAT-ID gelezen, niet op rijnummer. De waarde van de
  representatieve SVAT is uitsluitend aanvullende metadata bij SWBOTB=2.
  Er wordt geen lokale dqsat-grid gereconstrueerd.
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
gecontroleerd. Veranderingen stoppen de uitvoering. INP-waardetabel wordt
gecontroleerd op dubbele/ontbrekende SVAT-ID's en krijgt een bronhash.

## Kwalificatiegrens

Het serverrapport bewijst aanwezigheid, leesbaarheid en geometrische dekking.
Het bewijst geen fysische gelijkwaardigheid van alle oorspronkelijke parameters.
De vierklassengewaskoppeling blijft kandidaat met 255 verschillen tegenover de
historische tabel; generieke croporg-metadata mag geen managementbron worden.
De wortelbronkeuze blijft onderscheiden van de oorspronkelijke rz_repr-tabel.

De software is lokaal getest van grids tot geschreven SWP. De eerdere vier
historische SWAP-runs valideren de renderer, niet deze nieuwe nationale
parameterafleiding. Pas het server-terugrapport toont hoeveel HRU's hiermee
werkelijk zijn geproduceerd. Er is nog geen nationale SWAP-uitvoering of
hydrologische vrijgave. BBC/DRA/MET/CRP-bestanden moeten afzonderlijk met de
SWP-bestanden worden samengesteld voordat SWAP kan rekenen.
