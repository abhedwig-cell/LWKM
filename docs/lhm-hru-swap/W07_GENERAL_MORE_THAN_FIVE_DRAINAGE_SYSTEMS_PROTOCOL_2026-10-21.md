# W07 algemeen protocol: meer dan vijf fysieke drainagesystemen naar maximaal vijf SWAP-niveaus

**Datum:** 2026-10-21  
**Status:** bindend beslis- en kwalificatieprotocol voor kandidaatconstructie; geen automatische wetenschappelijke admission.  
**Reikwijdte:** alle bestaande en toekomstige LWKM-HRU's met meer dan vijf na bronbeleid behouden hydraulisch actieve fysieke drainagesystemen. De huidige 29 geblokkeerde HRU's zijn de eerste verplichte regressiepopulatie.

## 1. Doel en bronautoriteit

Één SWAP 4.3.1-kolom vertegenwoordigt een groep MODFLOW-laag-1-cellen, niet noodzakelijk een aaneengesloten gebied. De hydrologische respons van die celgroep moet zo goed mogelijk overeenkomen met de SWAP-HRU. LHM heeft zeven fysische bronfamilies: H1, P, S, T, MVG, PIPE en OLF. SWAP accepteert maximaal vijf niveaus. De interfacegrens is geen reden om vóór de hydrologische analyse fysieke families zonder toets te laten verdwijnen.

Voer de bestaande W07 all-member HRU-aggregatie en eigenaarbesluiten uit **vóór** dit protocol:
- DRARES > 100000 d: betreffende fysieke drainagebijdrage weglaten (niet afkappen);
- INFRES > 100000 d: betreffende infiltratietak uit, drainage behouden, SWALLO=3 waar passend;
- ontbrekende H1-infiltratiefactor: geen infiltratie voor die broncel, niet automatisch voor de hele HRU;
- bij exacte grenswaarde 100000 geen wijziging uitsluitend op grond van de >-regel.

De oorspronkelijke en na beleid behouden bronnen met conductanties, weerstand, peilen, bodemdiepte, bron-ID en actieve infiltratiestatus blijven beide traceerbaar.

Lees als reeds bestaande authority: `docs/lhm-hru-swap/P12-DRA-SEVEN-TO-FIVE-LEVEL-DESIGN-2026-10-06.md`, `tools/dra_level_compression.py`, `docs/production/WORK_C2_20261019.md`, `docs/evidence/2026-10-19-work-c2/protected-partition-diagnostics.json`, en het besluit `docs/production/W07_29_HRU_RESOLUTION_DIRECTION_2026-10-21.md`.

## 2. Voorbewerking en beslisboom

Per HRU:
1. Verifieer source- en HRU-identiteit, m²-support, positieve eindige conductanties, peilreferenties, seizoenstijden en expliciete H1-maandseries. Stel de actieve bronset samen na de bestaande verwijderings-/infiltratieregels.
2. Zijn er maximaal vijf actieve niveaus? Gebruik de bestaande gewone route en gewone tests; ga niet nodeloos samenvoegen.
3. Zijn het er meer dan vijf? Start met **alle** geldige samenvoegingen van hydraulisch compatibele open-waterbronnen volgens de bestaande klassebescherming (drain-only met drain-only, infiltrerend met infiltrerend). PIPE blijft als buisdrain apart, tenzij een toekomstige expliciete SWAP-broncodekwalificatie een andere representatie toestaat.
4. Zoek niet uitsluitend greedy naar één lokaal goedkoopste samenvoeging. Evalueer globaal alle toelaatbare partities in maximaal vijf niveaus, met deterministische bron-ID-tie-breaks. Beperk de combinatoriek met branch-and-bound maar bewijs dat er geen betere kandidaat is overgeslagen.
5. Zijn alle compatibele partities geblokkeerd? Produceer geen fictief geldig DRA-bestand; ga naar de gecontroleerde *alternatieve-equivalentie-route* van paragraaf 5. Een geval mag bewust geblokkeerd blijven.

## 3. Fysische equivalente parameters

Bij samenvoeging van fysisch verenigbare parallelle bronnen:
- `g_d,eq = Σ_i g_d,i`, `R_d,eq = 1/g_d,eq`;
- `g_i,eq = Σ_i g_i,i`, `R_i,eq = 1/g_i,eq` wanneer infiltratie is toegestaan;
- het niveau-/bodemreferentiepunt is initieel drainage-conductantiegewogen;
- H1 dynamische peilreeks en andere seizoenspeilen moeten op de gezamenlijke tijdas worden beoordeeld;
- moderne representatieve-SVAT-afstand `L = 4*dqsat` behouden binnen de vastgelegde SWAP-semantiek;
- bewaar de afzonderlijke bronnen en de geselecteerde equivalente parameters in een uitvoerbaar merge-manifest.

Het behouden van totale conductantie is noodzakelijk maar **niet voldoende**: verschillende peilen, drempels en infiltratiestatussen veroorzaken afwijkende stukgewijze fluxfuncties. Infiltratie- en drainage-respons worden daarom apart getoetst.

## 4. Objectieve vergelijking van hydrologische respons

Gebruik dezelfde grondwaterstands-/peilreferentie voor oorspronkelijke bronset en kandidaat. Bereken bij ieder relevant tijdstip/peil en over een vastgelegd bereik van ondiepe tot diepe grondwaterstanden:
- oorspronkelijke som van drainagefluxen, oorspronkelijke som van infiltratiefluxen;
- equivalente SWAP-flux per tak, totaal, absolute fout (mm/d), relatieve fout waar zinvol;
- geïntegreerde seizoens-/jaarverschillen (mm), maximale fout nabij activatiedrempels en bij extreem nat/droog;
- conductantiesom vóór/na, bronverlies, peil-/bodemverplaatsing, en eventuele verandering van SWALLO of SWDTYP.

Neem ten minste de in Work C2 vastgelegde hydraulische responsgrenzen van 0,10 m (regionaal) en 0,02 m (oppervlakkig) in de kandidaatbeoordeling mee; dit zijn bestaande grenzen voor responsequivalentie en **geen automatische tolerantie in mm/d**. Leg een afzonderlijk, vooraf vastgesteld fluxfoutbudget vast; zolang dat niet gekwalificeerd is, mag een 5-niveaukandidaat niet uitsluitend op grond van 'klein lijkende' fluxverschillen worden admitted. Gebruik naast theoretische curves waar mogelijk echte HRU-grondwaterstanden uit bestaande gekwalificeerde runs.

Nulwaarde in H1 peilvelden mag niet worden geïnterpreteerd als nulflux zonder bewezen peilreferentie. Onderscheid signalen van ontbrekende data, seizoenspeil en peil t.o.v. maaiveld.

## 5. Alternatieve-equivalentie-route voor onverenigbare klassen

Voor HRU's die onder de strikte klasse-indeling geen vijf niveaus kunnen krijgen:
1. Test in een **afzonderlijke kandidaatmodus**, niet in de standaardcompressor, of een combinatie van open-watersystemen met verschillende infiltratiestatus binnen een beperkt hydrologisch bereik met één SWAP-niveau acceptabel is. Maak expliciet welke infiltratie mogelijk verloren gaat of onterecht ontstaat.
2. Gebruik een best-fit representatie die de gecombineerde `Q_d(h,t)` en `Q_i(h,t)` benadert met behoud van de SWAP 4.3.1 interface, waar nodig door peiloptimalisatie onder fysische grenzen. Een best-fit mag de originele conductantie niet ongemerkt veranderen; afwijkingen worden apart gerapporteerd.
3. Zoek naar numeriek verwaarloosbare fysieke bijdrage op basis van daadwerkelijk gesimuleerde flux en volume, **niet** alleen een weerstand of peilwaarde. Weglaten bij DRARES ≤100000 vereist expliciete aanvullende toestemming van projecteigenaar en een gekwalificeerd foutbudget; niet automatisch uitvoeren.
4. Vermeng geen buisdrain en open water of snelle macropore niveau-index onder onzekere SWAP-codebetekenis. Dergelijke kandidaten blijven geblokkeerd tot broncodeonderzoek/kwalificatie.
5. Als geen kandidaat voldoet: registreer `NO_DEFENSIBLE_FIVE_LEVEL_REPRESENTATION`, laat de HRU buiten de productierunset en documenteer dat een nieuw modelinterfacebesluit nodig is.

Deze route is geen toestemming om de bestaande eigenaarregels of kwaliteitsgrenzen stilzwijgend te versoepelen.

## 6. Deterministische selectie en bewijs

Voor iedere HRU wordt een versievaste kandidatenmatrix geschreven met: HRU-ID, alle fysieke bron-ID's, aantal originele/actieve/geserialiseerde niveaus, onderzochte groeperingen, ongeldige combinaties en reden, klasse, peilreeks, bodem, `L`, `DRARES`, `INFRES`, `SWALLO`, `SWDTYP`, `Q_d`/`Q_i`-foutcurves, conductantiebehoud, ranking en gekozen kandidaat.

Voorkeurvolgorde:
- exact equivalente partitie zonder klassewijziging;
- minimaal onderbouwd flux-/responsverlies;
- kleinste wijziging in hydraulische parameters en oorsprong;
- deterministische keuze op bron-ID's bij numeriek gelijkwaardig resultaat.

Draai expliciete **negatieve tests** voor onverenigbare classes, identieke niveaupunten, wisselende H1-peilen, ontbrekende datum, nulconductantie, DRARES/INFRES net aan beide kanten van 100000, zes en zeven actief, en niet-reproduceerbare sortering. Verifieer dat ongewijzigde 10213 eerder geldige DRA-bestanden byte-identiek blijven.

## 7. Uitvoering en admission

Voor de 29 huidige gevallen: voer de exacte globale klasseveilige kandidaatzoektocht op alle 29 uit, daarna de aparte equivalentiediagnose op nog geblokkeerde gevallen. Maak per HRU een gekwantificeerde tabel met geselecteerde vijf-niveaukandidaat of expliciete blocker. Test kansrijke kandidaten met SWAP 4.3.1 en de bestaande gekwalificeerde 1971-forcing waar beschikbaar; toets dagbalans, GWL, drainage, infiltratie, waarschuwingen en datumdekking.

**Een serienummer '29/29 geproduceerd' is geen succes op zichzelf.** Verleen pas toelating wanneer:
- de bron en wijzigingen volledig herleidbaar zijn;
- fluxen en toegestane foutgrenzen gekwantificeerd en beoordeeld zijn;
- SWAP de bestanden technisch accepteert;
- reële modelruns de representatieve respons bevestigen;
- geen verborgen fysieke bron verdwijnt en het bestaande ownerbeleid intact blijft.

Alle code, regressie, besluitstatus en bewijsstukken komen in Git. Geen automatische `PRODUCTION_ADMITTED` op basis van een gunstige selectoruitslag.

## 8. Structurele opname in de keten

Dit protocol wordt een vaste beslisgate voor **iedere** toekomstige HRU met >5 actieve fysische drainagebronnen, niet een hardcoded uitzonderingslijst. De bestaande W07-producent krijgt een expliciete route `<=5`, `strict_safe_compression`, `diagnostic_alternative`, `blocked`. De 29-case suite blijft een regressie-oracle.

Het protocol zelf geldt als ontwerpautoriteit; eventuele numerieke relaxaties, bronverwijdering buiten de eerdere eigenaarregel en nieuwe SWAP-semantiek vereisen afzonderlijke, versievaste goedkeuring.

## 9. Verplichte oplossing voor elk geval (aanvullend projecteigenaarbesluit 2026-10-21)

**Voor iedere HRU met meer dan vijf actieve fysieke drainagesystemen moet de methode altijd een concrete oplossing voorstellen.** Een blokkade of de melding `NO_DEFENSIBLE_FIVE_LEVEL_REPRESENTATION` zonder voorstel is geen afgerond diagnoseproduct.

De procedure rapporteert altijd minstens één **beste vijf-niveaukandidaat** die syntactisch binnen de SWAP 4.3.1-interface past, met expliciete bron-naar-niveau-toewijzing, equivalente weerstanden, drainage- en infiltratiestatus, peilen, hydraulische foutcurves en een gerangschikte lijst van alternatieven waar mogelijk. Wanneer de strikt toegelaten zoekruimte leeg is, moet de kandidaat uit een afzonderlijke, duidelijk als *niet-toegelaten alternatief* gemarkeerde zoekruimte worden gekozen. Denk aan een gemengde open-waterrepresentatie, gecontroleerd verwijderen van de minst invloedrijke bijdrage of een andere fysisch gemotiveerde benadering. Deze opties mogen niet stilzwijgend de geldende regels wijzigen.

Voor ieder voorstel worden ten minste gerapporteerd: de overtreden randvoorwaarden, benodigde uitzondering of ontwerpbeslissing, maximale en gemiddelde absolute fluxafwijking, netto jaar- of seizoensvolumeafwijking, effect op infiltratie- en drainagebranches, onzekerheden, rangorde en een concrete keuzeaanbeveling. Als zelfs technisch geen geldig vijf-niveau-DRA-bestand te construeren is, moet het rapport een specifiek alternatief inclusief noodzakelijke SWAP-interfacewijziging presenteren en motiveren waarom een vijf-niveaukandidaat onmogelijk blijkt. *Niets voorstellen* is niet toegestaan.

**Voorstellen is niet hetzelfde als accepteren.** Een niet-toegelaten alternatief krijgt `PROPOSED_REQUIRES_OWNER_DECISION`, niet `PRODUCTION_ADMITTED`. De procedure mag het voorstel in diagnostische modus genereren en toetsen, maar mag het niet ongemerkt in de productiecatalogus opnemen. Afwijkingen van het besluit DRARES>100000 weglaten, INFRES>100000 geen infiltratie, bescherming van buisdrainage of eerdere foutgrenzen vergen expliciete onderbouwde goedkeuring.

**Acceptatie-eis voor de 29 huidige gevallen:** 29/29 krijgen een concrete gerangschikte voorgestelde oplossing, ook als sommige voorstellen wetenschappelijk nog niet toelaatbaar zijn. De 10213 bestaande toegelaten kandidaten blijven ongewijzigd.
