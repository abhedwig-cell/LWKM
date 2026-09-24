# Werknotitie LWKM 2.0: workflow van LHM naar SWAP via HRU's

**Datum:** 24 september 2026  
**Status:** concept voor bespreking

## Doel

De afgelopen jaren is de route van LHM-resultaten naar LWKM-SWAP stapsgewijs opgebouwd. Daardoor staan data, scripts, selectieregels en tussenproducten nu op verschillende plekken. De inhoudelijke lijn is grotendeels aanwezig, maar de reproduceerbaarheid en traceerbaarheid kunnen beter.

De huidige reconstructie wordt daarom gebruikt om twee dingen tegelijk te bereiken:

1. de huidige LWKM 2.0-keten voldoende reconstrueren om bestaande resultaten en hydrologische veranderingen te kunnen verklaren;
2. een strakke, versieerbare workflow vastleggen die voortaan de standaard wordt.

De volledige LHM-berekening valt buiten deze workflow. Het startpunt is een afgeronde LHM-run; het eindpunt is een gecontroleerd SWAP-uitvoerpakket voor overdracht naar de volgende LWKM-stap.

## Hoofdworkflow

```text
LHM-run op NHI/LHM-server
        │
        ▼
1. LHM_EXPORT
   gecontroleerde selectie en overdracht van benodigde LHM-data
        │
        ▼
2. SVAT_BASE
   LHM-uitvoer + modelinvoer + ruimtelijke basisgegevens
   samengebracht per SVAT
        │
        ▼
3. SVAT_QUALIFIED
   domeinselectie + correcties + plausibiliteitsregels
        │
        ▼
4. HRU_DERIVATION
   SVAT → HRU10242 + representatieve SVAT + kwaliteitsinformatie
        │
        ▼
5. SWAP_INPUT_BUILD
   expliciete vertaling van HRU/SVAT-informatie naar SWAP-invoer
        │
        ▼
6. SWAP_RUN + QA
   rekenen, waterbalans, plausibiliteit en vergelijking met LHM
        │
        ▼
overdracht naar ANIMO
```

De datastroom is lineair. De ontwikkeling is iteratief: wanneer downstream een probleem zichtbaar wordt, wordt teruggegaan naar de stap waar de oorzaak zit. Een wijziging levert vervolgens een nieuwe kandidaatversie op, niet een handmatig aangepast eindbestand.

## 1. LHM_EXPORT

Op de LHM-server is veel meer uitvoer beschikbaar dan LWKM nodig heeft. In plaats van de complete LHM-uitvoer over te zetten, definiëren we een reproduceerbaar exportpakket met alleen de noodzakelijke gegevens.

Daarin zitten onder meer GHG/GLG, waterbalansfluxen, kwel/wegzijging, drainage, runoff, infiltratie, beregening en de tijdsafhankelijke MODFLOW-informatie die nodig is voor SWAP-randvoorwaarden.

Per bestand worden versie, periode, eenheid, bron, producerend script en checksum vastgelegd.

## 2. SVAT_BASE

Binnen de LWKM-omgeving worden de benodigde modeluitvoer, modelinvoer en aanvullende ruimtelijke informatie bij elkaar gebracht in één dataset per SVAT.

De bestaande route via `LWKM_makeHRU` doet hier al een belangrijk deel van. De huidige interface bevat onder meer SVAT-id, oppervlak, GHG/GLG, hydrologische fluxen, bodem, landgebruik en verschillende kwaliteitsvelden.

In de nieuwe structuur blijven oorspronkelijke waarden behouden. Afgeleide waarden, correcties en selecties worden apart geregistreerd.

## 3. SVAT_QUALIFIED

Hier worden drie soorten beslissingen expliciet uit elkaar gehouden.

**Domeinselectie.** Welke SVATs horen bij LWKM? Het bestaande veld `isLWKM` is hiervoor een sterke kandidaat.

**Inhoudelijke correcties.** Bekende modelartefacten, zoals de huidige correctie rond Flevoland/kwel, worden als expliciete correctie vastgelegd met bronwaarde, gecorrigeerde waarde, reden en versie.

**Plausibiliteitscontrole.** Hydrologisch vreemde SVATs worden gemarkeerd. In de bestaande scripts zijn al regels aanwezig voor onder meer extreme kwel, wegzijging, runoff, subinfiltratie en GHG boven maaiveld.

Belangrijk is dat signaleren en handelen worden gescheiden. Een verdachte SVAT wordt niet automatisch vervangen. Per downstream toepassing wordt vastgelegd of de SVAT mag worden gebruikt en, indien nodig, welke vervangingsregel geldt.

## 4. HRU_DERIVATION

Na kwalificatie volgt een zelfstandige HRU-procedure. Voor de huidige lijn is **HRU10242** de authority.

De huidige methode groepeert SVATs op bodem-, landgebruik- en hydrologische kenmerken, gebruikt GHG en netto kwel in de clustering, koppelt rest-SVATs aan donoren en kiest een representatieve SVAT per HRU.

De belangrijkste producten zijn:

- `SVAT_HRU_MAP`: koppeling van iedere SVAT aan een HRU;
- `HRU_SCHEMA`: eigenschappen en representatieve informatie per HRU;
- HRU-raster;
- kwaliteitsmaten, onder meer purity en afwijkingen in GHG/netto kwel.

De HRU-stap verandert de SVAT-basis niet, maar voegt een nieuwe representatielaag toe.

## 5. SWAP_INPUT_BUILD

De overgang van HRU naar SWAP is een eigen modelleringsstap.

De huidige `HRUlist2SWAP`-code gebruikt verschillende regels voor bodem, landgebruik, worteldiepte, drainage, meteorologie en onderrandvoorwaarden. Een deel komt van een representatieve SVAT, een deel uit gemiddelden of meerderheidsregels binnen de HRU.

Deze regels worden daarom uit de programmatuur gehaald en vastgelegd in een versieerbare **SWAP_MAPPING**. Zo is per SWAP-invoerveld zichtbaar:

- welke bron wordt gebruikt;
- welke SVATs meetellen;
- hoe wordt geaggregeerd;
- welke eenheidsconversie geldt;
- welke fallback geldt.

## 6. SWAP_RUN + QA

Na het aanmaken van de SWAP-invoer worden de HRU's doorgerekend.

De QA kijkt niet alleen of een run technisch slaagt, maar ook naar:

- waterbalans;
- hydrologische plausibiliteit;
- afwijkende HRU's;
- verschillen ten opzichte van de LHM/SVAT-referentie.

Daarbij proberen we afwijkingen toe te schrijven aan de juiste stap: oorspronkelijke LHM-hydrologie, selectie/correctie, HRU-representatie, SWAP-inputmapping of SWAP zelf.

De onderzoekslus wordt:

**OBSERVE → LOCALIZE → PROPOSE → CANDIDATE RUN → COMPARE → ACCEPT/REJECT → PERSIST**

## Hydrologische effecten per stap

De projectleider wil de relevante veranderingen tussen de stadia kunnen kwantificeren. De huidige opzet maakt daarvoor het volgende onderscheid:

| Stadium | Effect dat we willen bepalen |
|---|---|
| LHM4.3 | hydrologische uitgangstoestand |
| LHM4.3 lbn | effect van selectie landbouw + natuur |
| LHM4.3 cor | effect van inhoudelijke correcties |
| LHM4.3 rep | effect van kwaliteits-/vervangingsbeleid |
| LWKM SVATs | 1:1 verschil LHM versus SWAP voor representatieve SVATs |
| LWKM HRU's | effect van HRU-aggregatie en representatie |
| LWKM rep | eventuele vervanging/correctie op HRU-niveau |

Per stap worden waar relevant aantallen, oppervlak, gebiedsgewogen gemiddelden, MAE/RMSE, extremen en ruimtelijke verschillen gerapporteerd.

## Versiebeheer

De workflow wordt vastgelegd in:

`abhedwig-cell/LWKM`

Iedere kandidaat- of productierun krijgt een manifest met onder meer:

- LHM-bronversie;
- inputbestanden en checksums;
- codecommit;
- configuratieversies;
- HRU-versie;
- SWAP-versie;
- QA-status.

De basisregel is:

> Geen waarde in een canonical product verandert zonder dat zichtbaar is welke input, configuratie, code of expliciete correctie is gewijzigd.

## Huidige stand

De reconstructie is inmiddels ver genoeg om de hoofdlijn goed te beschrijven. Op dit moment zijn onder meer vastgelegd:

- de nieuwe canonical workflow;
- een exportcontract voor LHM-data;
- het huidige SVAT-datamodel uit `LWKM_makeHRU v0.20`;
- HRU10242 als actuele HRU-lijn;
- de HRU-clusteringsmethodiek;
- de huidige HRU → SWAP-mapping uit `HRUlist2SWAP v0.38`;
- de bestaande hydrologische kwalificatieregels;
- een versieerbare wijzigings- en onderzoekslus;
- een eerste QA-tool om effecten tussen workflowstappen reproduceerbaar te berekenen.

Nog open zijn vooral de exacte productiecontrol van de SVAT-opbouw, de feitelijke R-bron van HRU10242, de precieze Flevoland-correctie, het formele vervangingsbeleid voor verdachte hydrologie en de koppeling met de actuele SWAP-output-QA.

De kern is daarmee niet meer: **hoe hebben we alle historische stappen ooit uitgevoerd?**

De kern wordt: **welke gecontroleerde producten en beslissingen zijn nodig om van een LHM-run reproduceerbaar naar een gekwalificeerde SWAP-run te komen?**
