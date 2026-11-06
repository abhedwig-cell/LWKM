# Frank SVAT: nieuwe basisafbakening (projecteigenaar, 6 november 2026)

Dit is de actuele opdracht voor de volgende productiegang, en vervangt conflicterende oude aanname uit `FRANK_DIRECT_NHI_PYTHON_PRODUCER_V01_20261104.md` over GG en `Fldrin`, alsook de eerder voorgestelde impliciete Flevolandtoepassing in de basisexport.

## Eerst uitsluitend SVAT-basistabel, originele LHM/MetaSWAP/MODFLOW 1991–2020

- Eén regel per **645582** originele SVAT's, ook niet-LWKM; eerste velden `SVAT,Gebied,N,Opp_svat,...`. `N=1`. ECHO Gebied gecoverd 557001 SVATs, 88581 NoData leeg, geaccepteerd.
- `GG=(GHG+GLG)/2` met beide cm beneden maaiveld; dit is een gekozen middenmaat. Optioneel een apart diagnostisch veld voor echte 14/28-gemiddelde GG, maar het door Frank gevraagde `GG` is het midden.
- GHG/GLG blijven uit 14/28 halfmaandelijkse hoofdreeks, evenals `GW5`/`GW95` uit 720 14/28-waarnemingen (niet drie decadische standen per maand). Frank's vragen over decaden slaan op Leo's toekomstige SWAP-tabel; **geen nieuwe headrun**.
- `Landuse ANIMO` tekst via bestaande LU4: gras, maïs, akkerbouw, natuur; voor LU4=0 buiten LWKM selectie geen fictieve ANIMO-tekst.
- `slk=bodem370`, `luk=landgebruik22`, lookupfamilies Git. 16 bruto MODFLOW-fluxvelden zijn op volledige celoppervlakte **62500 m2**; SVAT-basistabel toont mm/j cel-equivalent, niet valselijk actieve-SVAT-oppervlakte.
- Fldrou1=RIV1+RIV4; 2=RIV2; 3=RIV3; 4=DRN1; 5=DRN2+DRN3. Fldrin1=RIV1+RIV4; Fldrin2=RIV2; Fldrin345=RIV3. Alles ongecorrigeerd, positieve bruto-richtingsvolumes; RIV1 wordt **niet** met Flevoland verschoven in basis-SVAT. `Kwelklasse4` uit originele langjarige netto-FLF.
- Evap: `-Tact`, `-(Eic+Esp)`, `-(Ebs+Epd)`; bewaar individuele componenten. Beregening=Psgw+Pssw, Neerslag/ET/runoff uit reeds geproduceerde originele MetaSWAP; `bdgdecstot` reeds opgenomen in signed diagnostic source exports.
- `bdgqmodf` als losse hulpvariabele tonen, **geen extra onafhankelijke balansflux**; WB07 had een diagnostische producer maar de volledige 1991-2020 SVAT-publicatie uit Qmodf is niet aangetoond. Onderzoek wat aanwezig is en alleen indien nodig 1080 decade-IDFs uitlezen.
- MetaSWAP waterbalansafwijking: de brontermensom inclusief `bdgdecstot`, `bdgpm`, `bdgpssw`, `bdgpsgw`, `bdgetact`, `bdgqrun` is uit eerdere WB23 bekend. Voor de werkelijke interpretatie als MetaSWAP rest moet de juiste uitwisselings-/drainagepost worden opgenomen en tegen het oorspronkelijke koppelcontract getoetst. Niet automatisch `bdgqmodf` optellen zonder bewijs.
- Voor de overall beschikbare-termensom documenteert WB23 `R0 = (bdgdecstot+bdgpm+bdgpssw+bdgpsgw+bdgetact+bdgqrun) + (QLAT+FLF+WEL+GHB+DRN+RIV)` (alle originele getekende budgettermen op **dezelfde** MODFLOW-celvolumebasis). **Geen MODFLOW STO**, BND of qmodf in R0. Label expliciet `onverklaard deel van de balans exclusief MODFLOW-storage`, geen numerieke modelfout of wetenschappelijk toegelaten sluiting. Behoud oppervlakte- en tekencontrole, mogelijk ontbrekende balansposten benoemen.
- Flevoland **niet** toepassen op basis-SVAT; maak later aparte parallelle Flevoland-tabel met boekhoudkundige FLF/RIV1-delta en een Flevoland-indicator. Lopende correctierun mag bronproduct leveren maar niet basis overschrijven.
- SVAT donorvervanging, uitsluitingen, overige stapvarianten pas in latere tabellen; HRU-aggregatie pas na SVAT-basis en krijgt eigen support- en representatiedefinitie; Leo's SWAP-tabel is extern.
- Afgeleide Gt en GW5/95/klassen in de basis blijven zoals overeengekomen.

## Actuele acties
1. Bestaande server-CSVs inspecteren voor signed `bdgdecstot`, `bdgqmodf` en ET-totalen; indien QmodF 30-jaars ontbreekt, lichte nieuwe QModF-sourceextractie.
2. Documenteer en test twee balansrestformules, met fysieke en interne posten duidelijk gescheiden en juiste SVAT→MODFLOW-supportconversie; restitueer signbronnen zodat geen dubbele telling plaatsvindt.
3. Bouw `FRANK_SVAT_BASIS_ONCORR_1991_2020.csv`, aparte schema en manifest, met nul bronoverschrijving en fail bij ontbrekende verplichte rijen, maar behoud geaccepteerde ontbrekende Gebied. Geen Flevolandkolom tenzij afzonderlijke latere tabel.
4. Evalueer controles en gereedheid vóór HRU of correctietabellen.

De **exacte** nieuwe Franks kolomvolgorde: SVAT/HRU, Gebied, N aantal SVATs, Opp_svat/hru, landuse LHM22, ANIMO4 tekst, LU4,LU2,bodem370,bodem79,pawn21,grondsoort4,grondsoort2,Gtnr,GLG,GHG,GG,dynamiek,GW5,GW95,kwelklasse4,neerslag,beregening,ET,gewasverdamping,interceptieverdamping,bodemverdamping,runoff,ontwatering,Fldrou1..5,infiltratie,Fldrin1,Fldrin2,Fldrin345,netto kwel/wegzijging,laterale netto,onttrekkingen laag1,GHB,wegzijging,kwel,QModF,bergingsverandering MetaSWAP,waterbalansafwijking MetaSWAP,overall onverklaard balansdeel,indicator later; de ongecorrigeerde basis mag indicator=0 uitsluitend voor expliciet gekozen `Flevoland_gecorrigeerd`, en moet de vervangingsstatus niet als 0 invullen zonder betrekking op die fase.
