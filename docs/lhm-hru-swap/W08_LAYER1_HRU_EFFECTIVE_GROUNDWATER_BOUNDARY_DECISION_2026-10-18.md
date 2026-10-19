# W08-GW-L1 ontwerpbesluit: effectieve grondwaterrandvoorwaarde per HRU uit MODFLOW-laag 1

Naamgeving verduidelijkt op 2026-10-19: W08 blijft BBC; W08-GW-L1 is de expliciete subwerkstroom.

Datum: 2026-10-18
Status: vastgesteld conceptueel ontwerp; implementatie, pakketsemantiek en kwalificatie nog open.
Scope: LHM433 -> HRU -> SWAP productie; geen heropening van de afzonderlijke ontwateringsontwikkeling.

## Representatie
Een HRU is een verzameling MODFLOW-cellen met min of meer vergelijkbare hydrologische omstandigheden, niet noodzakelijk aaneengesloten. Eén SWAP-kolom moet de geaggregeerde waterbalans van die celgroep representeren. Voor deze randvoorwaardeanalyse geldt als expliciete vereenvoudiging dat SWAP MODFLOW-laag 1 representeert.

## Dagelijkse rekenregel
Reken voor iedere geselecteerde MODFLOW-laag-1-cel i en iedere dag d de vier externe componenten uit, met een uniforme tekenconventie (positief = toevoer aan laag 1):

Q_ext(i,d) = Q_FLF(i,d) + Q_LAT(i,d) + Q_GHB(i,d) + Q_WEL(i,d).

FLF betreft uitsluitend het onderste celvlak van laag 1 naar laag 2, met te verifiëren outputrichting. LAT betreft de netto uitwisseling door de horizontale celvlakken van laag 1. GHB en WEL betreffen uitsluitend de aan laag 1 toegekende pakketbijdragen. Verifieer pakketdekking, in-/uitstroomrichting, volumeeenheid en dagelijkse temporele integratie tegen originele MODFLOW-budgetten.

Som daarna over de MODFLOW-celverzameling C_h van HRU h:

Q_ext(h,d) = sum_{i in C_h} Q_ext(i,d).

Bij consistente face-fluxboekhouding heffen laterale uitwisselingen tussen twee geselecteerde cellen elkaar vanzelf op: plus in ontvangende cel en min in donorcel. Dit geldt ook als de HRU als verzameling niet aaneengesloten is; er wordt geen geometrische HRU-rand geconstrueerd. Uitwisseling met cellen buiten de verzameling blijft netto over. Bewaar per component ook bruto instroom, bruto uitstroom en nettoflux voor diagnose.

Omrekening naar een equivalente dagelijkse SWAP-flux, bij volume m3/d en representatief HRU-oppervlak A_h in m2:

q_ext(h,d) [mm/d] = 1000 * Q_ext(h,d) / A_h.

Het oppervlak en de cel-naar-HRU-membership moeten consistent zijn met de bestaande gekwalificeerde HRU-context. Bij fractionele membership of overlap moeten bijdragen eenduidig worden toegewezen en mag geen flux dubbel tellen.

## Afbakening
MetaSWAP-uitwisseling en bergingsverandering zijn NIET nodig als invoer voor het construeren van deze randvoorwaarde. SWAP berekent de onverzadigde-zone-uitwisseling en bergingsrespons zelf. Ontwatering/RIV/DRN wordt reeds afzonderlijk behandeld en wordt NIET opnieuw in Q_ext opgenomen. Overige package-termen horen niet zonder expliciet nieuw besluit in de vierledige som.

De componenten FLF, LAT, GHB en WEL blijven naast hun dagelijkse som afzonderlijk beschikbaar, met laag-, pakket-, bron- en tijdprovenance. Onttrekkingen in laag 2 of dieper worden niet rechtstreeks opgenomen.

## Interpretatie en toetsing
De som is een equivalente externe volumebalans voor de representatieve SWAP-kolom en mag voor de eerste historische reproductietoets als voorgeschreven effectieve onderrandflux worden onderzocht. Dat betekent niet dat horizontale of GHB/WEL-uitwisseling letterlijk verticale stroming is. Naast massabehoud moet later worden nagegaan of de grondwaterstands- en verdampingsrespons voldoende overeenkomt. Een mogelijke toestandsgestuurde onderrand is een afzonderlijke, later te kwalificeren vervolgstap.

Primaire kwalificatiepunten:
1. Originele MODFLOW-laag-1-boekhouding bevestigt tekens en eigendom van FLF/LAT/GHB/WEL.
2. Dagelijkse fluxen zijn op dezelfde kalenderdag/tijdbasis geïntegreerd en in dezelfde volume-eenheid.
3. Beide zijden van interne horizontale faces zijn aanwezig; er zijn geen ontbrekende of dubbelgetelde faces.
4. HRU-celmembership en HRU-oppervlak zijn herleidbaar, zonder dubbele toerekening.
5. Dagelijkse component- en totalsommen zijn reproduceerbaar en het verschil met directe geaggregeerde celbalansen is binnen vooraf vastgelegde numerieke tolerantie.
6. Geen automatische production admission op basis van alleen dit ontwerpbesluit.

## Besluit
De effectieve overige grondwaterrandvoorwaarde van elke HRU wordt opgebouwd door op dag- en laag-1-celniveau FLF + LAT + GHB + WEL te sommeren, daarna over alle aan de HRU toegewezen cellen te aggregeren en door het vertegenwoordigde oppervlak om te rekenen naar mm/d. Er wordt geen aaneengesloten HRU-polygon of expliciete buitenrand vereist. MetaSWAP, bergingsverandering en de apart behandelde ontwatering maken geen deel uit van deze invoerconstructie.
