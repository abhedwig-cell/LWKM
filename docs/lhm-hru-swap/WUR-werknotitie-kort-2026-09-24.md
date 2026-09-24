# Werknotitie LWKM 2.0
## Workflow van LHM naar SWAP via HRU's

**Datum:** 24 september 2026  
**Status:** concept voor bespreking

### Waarom deze workflow nu wordt vastgelegd

De route van LHM-resultaten naar SWAP is in de afgelopen jaren stap voor stap ontwikkeld. Daardoor staan data, scripts, selectieregels en tussenproducten nu op verschillende plekken. Inhoudelijk is veel aanwezig, maar het is niet altijd direct zichtbaar welke stap welke verandering veroorzaakt.

De huidige inzet is daarom tweeledig:

1. voldoende reconstrueren hoe de huidige LWKM 2.0-keten tot stand komt;
2. tegelijk een strakke, reproduceerbare werkwijze vastleggen die voortaan als standaard kan dienen.

De volledige LHM-berekening valt buiten deze workflow. Het startpunt is een afgeronde LHM-run. Het eindpunt is een gecontroleerd SWAP-uitvoerpakket dat kan worden overgedragen aan de volgende LWKM-stap.

---

## Hoofdlijn

```text
LHM-run op NHI/LHM-server
        │
        ▼
1. LHM_EXPORT
   selecteren en bundelen van benodigde LHM-resultaten
        │
        ▼
2. SVAT_BASE
   modeluitvoer + modelinvoer + ruimtelijke informatie per SVAT
        │
        ▼
3. SVAT_QUALIFIED
   domeinselectie + correcties + plausibiliteitscontrole
        │
        ▼
4. HRU_DERIVATION
   SVATs groeperen tot HRU10242
        │
        ▼
5. SWAP_INPUT_BUILD
   HRU/SVAT-informatie vertalen naar SWAP-invoer
        │
        ▼
6. SWAP_RUN + QA
   rekenen + waterbalans + plausibiliteit + vergelijking met LHM
        │
        ▼
overdracht naar ANIMO
```

De datastroom is lineair. De ontwikkeling is iteratief. Wanneer later in de keten een probleem zichtbaar wordt, gaan we terug naar de stap waar de oorzaak zit. Een wijziging levert vervolgens een nieuwe kandidaatversie op, niet een handmatig aangepast eindbestand.

---

## 1. LHM_EXPORT

Op de LHM-server is veel meer uitvoer beschikbaar dan LWKM nodig heeft. In plaats van de complete LHM-uitvoer over te zetten, maken we een gecontroleerd exportpakket.

Daarin zitten alleen de gegevens die downstream nodig zijn, bijvoorbeeld:

- GHG en GLG;
- relevante waterbalanscomponenten;
- kwel en wegzijging;
- drainage, runoff, infiltratie en beregening;
- benodigde MetaSWAP- en MODFLOW-grootheden;
- tijdsafhankelijke MODFLOW-informatie voor SWAP-randvoorwaarden;
- ruimtelijke basisgegevens en classificaties.

Per product worden versie, periode, eenheid, bronbestand, producerend script en checksum vastgelegd.

**Nieuwe standaard:** LHM is upstream authority. LWKM begint bij een gecontroleerde export.

---

## 2. SVAT_BASE

Binnen de LWKM-omgeving worden alle benodigde gegevens per SVAT samengebracht.

De huidige route via `LWKM_makeHRU` doet dit voor een belangrijk deel al. De actuele SVAT-interface bevat onder meer:

- SVAT-id, coördinaten en oppervlak;
- GHG en GLG;
- neerslag en verdamping;
- runoff;
- afvoer en aanvoer;
- kwel en wegzijging;
- drainage en beregening;
- bodem en landgebruik;
- hydrologische klassen;
- verschillende kwaliteits- en selectiesignalen.

In de nieuwe structuur worden bronwaarden niet meer destructief overschreven. Afgeleide waarden, correcties en selecties blijven herkenbaar als aparte informatie.

**Nieuwe standaard:** één canonieke SVAT-basis met behoud van herkomst.

---

## 3. SVAT_QUALIFIED

Hier worden drie soorten beslissingen strikt uit elkaar gehouden.

### Domeinselectie

Welke SVATs horen bij LWKM? Het huidige veld `isLWKM` is hiervoor een sterke kandidaat.

### Correcties

Bekende modelartefacten worden expliciet gecorrigeerd. Een voorbeeld is de kwelcorrectie rond Flevoland. Bij zo'n correctie leggen we bronwaarde, gecorrigeerde waarde, reden, gebied en versie vast.

### Plausibiliteitscontrole

Hydrologisch vreemde situaties worden gemarkeerd. In de huidige scripts bestaan al criteria voor onder andere:

- zeer hoge kwel;
- sterke wegzijging;
- extreme runoff;
- hoge subinfiltratie;
- kwel bij droge grondwaterstanden;
- GHG boven maaiveld bij landbouw.

Belangrijk: **signaleren is niet hetzelfde als vervangen.**

Een gemarkeerde SVAT kan bijvoorbeeld wel bruikbaar zijn voor bodem/landgebruik, maar niet voor een bepaalde hydrologische randvoorwaarde.

**Nieuwe standaard:** diagnose, gebruiksbesluit en eventuele vervanging worden afzonderlijk vastgelegd.

---

## 4. HRU_DERIVATION

Na kwalificatie volgt een zelfstandige HRU-procedure.

Voor de huidige lijn is **HRU10242** de authority.

Een harde ontwerpregel is dat **dezelfde gekwalificeerde SVAT-informatie zowel de basis vormt voor de HRU-afleiding als voor de latere opbouw van SWAP-invoer**. Er mag dus niet ongemerkt een andere versie van correcties, selectie of hydrologische invoer tussen deze twee stappen terechtkomen.

De methode gebruikt onder andere bodem, landgebruik, GHG en netto kwel, clustert SVATs en koppelt rest-SVATs waar nodig aan donoren. Per HRU wordt daarnaast een representatieve SVAT gekozen.

Belangrijkste producten:

- `SVAT_HRU_MAP`: welke SVAT hoort bij welke HRU;
- `HRU_SCHEMA`: kenmerken per HRU;
- representatieve SVAT;
- HRU-raster;
- kwaliteitsmaten, zoals purity en afwijkingen in GHG/netto kwel.

**Nieuwe standaard:** de HRU-procedure verandert de SVAT-basis niet, maar voegt een expliciete representatielaag toe.

---

## 5. SWAP_INPUT_BUILD

De overgang van HRU naar SWAP is een eigen modelleringsstap.

We willen hierbij **twee parallelle SWAP-representaties** kunnen opbouwen:

1. **HRU-SWAP:** één SWAP-model per HRU, opgebouwd uit de informatie van alle SVATs binnen die HRU volgens expliciete aggregatieregels;
2. **representatieve-SVAT SWAP:** één SWAP-model voor de representatieve SVAT die tijdens de HRU-afleiding is gekozen.

Die representatieve SVAT is onderdeel van het HRU-resultaat. De huidige HRU-methodiek kiest daarvoor een feitelijke SVAT die zo representatief mogelijk ligt ten opzichte van de HRU-kenmerken. Beide varianten zijn relevant voor vergelijking en kunnen downstream richting ANIMO worden gebruikt.

De huidige `HRUlist2SWAP`-code gebruikt verschillende regels voor bodem, landgebruik, worteldiepte, drainage, meteorologie en onderrandvoorwaarden. Sommige waarden komen van een representatieve SVAT, andere worden gemiddeld of via meerderheidsregels bepaald.

Die regels worden voortaan vastgelegd in een aparte **SWAP_MAPPING**.

Per SWAP-invoerveld wordt expliciet gemaakt:

- welke bron wordt gebruikt;
- welke SVATs meetellen;
- hoe wordt geaggregeerd;
- welke eenheidsconversie geldt;
- welke fallback geldt.

**Nieuwe standaard:** wetenschappelijke mappingregels staan niet alleen verborgen in programmatuur.

---

## 6. SWAP_RUN + QA

Na het genereren van SWAP-invoer worden de HRU's doorgerekend.

De controle kijkt niet alleen of SWAP technisch draait, maar ook naar:

- waterbalans;
- hydrologische plausibiliteit;
- afwijkende HRU's;
- verschillen ten opzichte van de LHM/SVAT-referentie.

Een afwijking moet zoveel mogelijk worden teruggebracht naar de juiste oorzaak:

- LHM-brondata;
- selectie/correctie;
- HRU-representatie;
- SWAP-inputmapping;
- SWAP zelf.

De ontwikkellus wordt:

**OBSERVE → LOCALIZE → PROPOSE → CANDIDATE RUN → COMPARE → ACCEPT/REJECT → PERSIST**

---


## Kwaliteitsbeoordeling als vaste stap

Naast versiebeheer en reproduceerbaarheid komt er in iedere hoofdtransitie een expliciete **hydrologische QA-gate**.

Daarin worden kennisregels automatisch getoetst, bijvoorbeeld grenzen aan kwel, wegzijging, runoff, grondwaterstanden of combinaties daarvan. Een overschrijding betekent niet automatisch dat een resultaat wordt verwijderd of vervangen. De berekening wordt zichtbaar gemarkeerd, waarna onderzocht kan worden of het gaat om een fysisch bijzondere situatie, een fout in de brondata, een inconsistentie in de keten of een regel die aangepast moet worden.

De kennisregels worden zelf versieerbare configuratie. Daardoor is altijd reproduceerbaar:
- welke norm gold;
- welke SVATs/HRU's/runs niet voldeden;
- welke uitzonderingen golden;
- wat na onderzoek met de afwijking is gedaan.

Een extra harde QA-regel wordt dat de HRU-afleiding en de SWAP-inputopbouw aantoonbaar dezelfde `SVAT_QUALIFIED` bronversie moeten gebruiken.

Voor de huidige HRU10242-lijn moet daarom nog achteraf worden vastgesteld of Piet bij de HRU-afleiding dezelfde Flevoland-gecorrigeerde en op uitschieters behandelde SVAT-data heeft gebruikt als later bij de SWAP-opbouw. Als dat niet zo is, moet het effect daarvan worden gekwantificeerd en zo nodig opnieuw worden doorgerekend.


## Effecten die we per stap willen kwantificeren

| Stadium | Betekenis |
|---|---|
| **LHM4.3** | hydrologische uitgangstoestand |
| **LHM4.3 lbn** | effect van selectie landbouw + natuur |
| **LHM4.3 cor** | effect van inhoudelijke correcties |
| **LHM4.3 rep** | effect van kwaliteits-/vervangingsbeleid |
| **LWKM SVATs** | 1:1 vergelijking LHM versus SWAP voor representatieve SVATs |
| **LWKM HRU's** | effect van HRU-aggregatie en representatie |
| **LWKM rep** | eventuele vervanging/correctie op HRU-niveau |

Per stap willen we waar relevant rapporteren:

- aantal SVATs/HRU's;
- vertegenwoordigd oppervlak;
- aantal en oppervlak gewijzigde eenheden;
- gebiedsgewogen gemiddelden;
- MAE/RMSE;
- extremen en percentielen;
- ruimtelijke ligging van verschillen.

---


## Opslag, werkplekken en overdracht

De workflow draait fysiek op meerdere plekken: de NHI/LHM-server, de centrale W:-schijf, de grote werkruimte van Leo en een externe/gedistribueerde omgeving voor de SWAP-berekeningen. Dat hoeft geen probleem te zijn zolang **de authority niet over die plekken versnipperd raakt**.

Daarom wordt onderscheid gemaakt tussen:
- **authoritative source packages**, die bewaard moeten blijven;
- **canonical products**, die formeel zijn geaccepteerd;
- **working copies**, die alleen voor verwerking bestaan;
- **QA/evidence**, waarmee een run is beoordeeld.

Niet alle grote tussenbestanden hoeven blijvend op de W:-schijf te staan. Wel moeten de bronbestanden, manifests, code/configuratie en benodigde QA-evidence voldoende zijn om afgeleide producten opnieuw te maken.

Iedere overdracht wordt een formeel handoffpunt. Een bestand is dus niet correct overgedragen omdat iemand weet dat het “daar ergens staat”. De ontvangende stap controleert run-id, manifest, verwachte bestanden en checksums en registreert welke exacte inputversie is gebruikt.

Productiescripts mogen vervolgens alleen uit zo'n geaccepteerd pakket lezen. Daarmee voorkomen we dat dezelfde veronderstelde invoer als verschillende kopieën op W:, Leo of een lokale werkdirectory uiteen gaat lopen.

De gedistribueerde SWAP-berekening wordt later eveneens als formeel extern handoffpunt opgenomen: een gemanifesteerd SWAP-inputpakket gaat naar de rekeneenheid en een gemanifesteerd resultaatpakket komt terug. De huidige nabewerking op Leo tot een compacte SWAP-resultaat-CSV hoort vervolgens weer expliciet bij de LWKM-keten.


## Waar staan we nu?

De reconstructie is inmiddels ver genoeg om de hoofdlijn betrouwbaar te beschrijven.

Reeds vastgelegd:

- canonical workflow LHM → SVAT → HRU → SWAP;
- concept LHM-exportcontract;
- huidige 75-koloms SVAT-interface uit `LWKM_makeHRU v0.20`;
- HRU10242 als actuele HRU-authority;
- technische HRU-clusteringsmethodiek;
- huidige HRU → SWAP-mapping uit `HRUlist2SWAP v0.38`;
- belangrijkste hydrologische kwalificatieregels;
- versieerbare wijzigings- en onderzoekslus;
- eerste QA-tool voor effectvergelijkingen;
- runmanifest en Git-versiebeheer.

Nog te binden:

1. exacte productiecontrol van `LWKM_makeHRU`;
2. het feitelijke R-script van HRU10242;
3. exacte Flevoland-correctie;
4. formeel beleid voor gebruik/vervanging van hydrologisch verdachte SVATs;
5. actuele SWAP-output- en balanscontrole;
6. eerste volledige effecttabel met echte cijfers.

---

## Kernboodschap

Veel inhoudelijke onderdelen bestonden al. Het probleem was vooral dat ze historisch over bestanden, scripts en locaties verspreid zijn geraakt.

De nieuwe werkwijze maakt iedere stap expliciet:

**bron → product → configuratie → QA → versie**

Daardoor kunnen we straks een nieuwe LHM-versie, aangepaste selectieregels, een andere HRU-indeling of gewijzigde SWAP-mapping invoeren zonder opnieuw een ondoorzichtige keten op te bouwen.

De huidige reconstructie is daarmee niet alleen documentatie van LWKM 2.0, maar de basis voor een beheerste volgende versie.
