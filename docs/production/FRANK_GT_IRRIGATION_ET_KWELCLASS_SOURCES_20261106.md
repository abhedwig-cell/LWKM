# Frank: Gt, beregening, ET-componenten en kwelklasse (6 november 2026)

## Door projecteigenaar bevestigd
- `area_svat.inp`: `slk` is bodem370 en `luk` is landgebruik22 in deze LHM-variant. Gebruik direct de geverifieerde repository-lookups `config/p12/bodem370_classification_lookup.csv` en `config/preprocessing/landuse-mapping-realized-v1.csv`.
- `Beregening = Psgw + Pssw`. Beide zijn positieve MetaSWAP-budgetposten; brondecade-hoeveelheden m3/m2 dec → jaargemiddelde mm/j (factor 1000/30), met bronconventies valideren. `qspgw` is grondwateronttrekking in MF en géén extra beregeningspost.
- `Gtnr` als Gt I–VIII uit 1991–2020 berekende GHG/GLG, beide cm onder maaiveld, niet uit oude `gt.asc` als primaire bron.

## Externe Gt-definitie en implementatiecontract
Bron: WUR Handboek Melkveehouderij 2023–2024, Tabel 1.9: https://www.wur.nl/nl/show/Handboek-Melkveehouderij-2020-H1.htm ; CROW oude Gt-indeling https://kennisbank.crow.nl/public/gastgebruiker/GWF/Wegverhardingen_op_slappe_bodem_-_Scoresysteem_voor_ontwerp_en_uitvoering/III_Achtergrondinformatie_bij_drooglegging_en_waterhuishouding/21982 .
Werkdefinitie grof Gt 1..8, zonder subtype:
1: GLG<50;
2: 50<=GLG<80;
3: 80<=GLG<120 en GHG<40;
4: 80<=GLG<120 en GHG>=40;
5: GLG>=120 en GHG<40;
6: GLG>=120 en 40<=GHG<80;
7: GLG>=120 en 80<=GHG<140;
8: GLG>=120 en GHG>=140.
Grenswaarden < of >= expliciet vastleggen; officiële Tabellen presenteren bandgrenzen, exacte gelijkheid is softwarebeleid. Met GHG<=GLG als validatie; overige niet-fysische combinaties vlaggen, niet forceren. Grof schema lost alle Gt-subtypen niet op en is te kwalificeren tegen originele LHM `gt.asc` (andere groundwater-period/methode kan verschillen).

## Repository ET-broncontract
`tools/metaswap_hru/sources.csv`: originele decadische IDF’s `msw_Tact`, `msw_Eic`, `msw_Ebs`, `msw_Epd`, `msw_Esp`, `msw_Tpot`, plus `bdgETact`, `bdgPsgw`, `bdgPssw`. Voor ieder decaden-bestand in bronneninventaris, totaal 1970–2024.
`tools/metaswap_hru/README_NL.txt` en `lwkm_metaswap_hru.cpp` leggen vast (originele negatieve waterbalanstekens):
`E_SOIL_POND = Ebs + Epd`;
`E_INTERCEPTION_SPRINKLING = Eic + Esp`;
`T_ACTUAL = Tact`;
`ET_ACTUAL = Ebs+Epd+Eic+Esp+Tact`;
`IRR_TOTAL = Pssw+Psgw`;
`BDGETACT_MINUS_ET=BDGETACT-ET_ACTUAL`.
Voor Frank (positieve verdampingsgrootheden): `Verdamping gewas=-Tact`, `Verdamping interceptie=-(Eic+Esp)`, `Verdamping bodem=-(Ebs+Epd)` als **expliciete rapportagegroepering**, daarnaast individuele Ebs/Epd/Eic/Esp/Tact apart bewaren zodat latere definitiekeuzes traceerbaar zijn. `Esp` is verdamping beregeningswater (niet sneeuw). Niet zonder brondefinitie Epd als bodemverdamping voorstellen; rapportage-label moet eventuele oppervlakteplasverdamping vermelden.
`ETact` moet met de som van vijf componenten worden vergeleken, afwijkingen in aparte QA; niet residueel sluiten of componenten overschrijven.

Officiële externe uitleg: https://deltares.github.io/imod-python/_modules/imod/msw/output_control.html : ETact = Esp+Eic+Epd+Ebs+Tact.
`msw_...` IDF-bronvelden zijn m3/m2 per decade op SVAT-bronoppervlak, omzetten naar positieve mm/jaar via `-1000 * sum_{1080}(value)/30`, mits intacte dekking. 1991–2020, 1080 decades. Voor Psgw/Pssw positief zonder negatie.

## Kwelklasse4: nog geen numerieke authority
De exacte classificatiegrenzen zijn *niet* aangetoond in de geraadpleegde code/config:
- `config/hru-clustering-HRU10242.yml` en `tools/legacy/HRU_clustering_LWKM20_31082026.R` consumeren `kwelklasse4` maar berekenen deze klasse niet.
- `schemas/svat/LWKM_makeHRU-v020.md` meldt dat de legacy CSV een `kwelklasse4`-kolom heeft, zonder drempels.
- `docs/lhm-hru-swap/S0-S1-HYDROLOGICAL-CLASS-PREPROCESSING.md` beschrijft `flux2class.csv` met discrete kwelklasse-kandidaten, maar niet bewezen dat dit exact de HRU `kwelklasse4` is. `config/preprocessing/lookup-chain-manifest-v1.yml` markeert de tabellen als `file_present_values_not_yet_extracted`. Niet verwarren met `kwelwegz(scale)` uit `kwelmmd2fuzzy.csv`.
- Zoek eerst de oorspronkelijke `flux2class.csv` en/of de producer of `kwelklasse4` op NHI-server; bevestig definities op originele `SVAT_INFO_HRU`-rijen. Tot dan `kwelklasse4` leeg met QA waarschuwing.

## Volgende NHI-serverstap
Reeds gemaakte MetaSWAP-bronraster-reader gebruiken voor zes aanvullende 1991–2020 outputs (Tact,Eic,Ebs,Epd,Esp, eventueel Tpot) en beregening in dezelfde doorloop; bestaande zes-term-resultaten behouden, geen zware complete MODFLOW- of head-herberekening. IDF-dekking 1080 per variabele, NoData niet op nul. Originele serie-output apart bewaren. Daarna join met de succesvol afgeronde 16-flux-MODFLOW en GxG-klimaatproducten plus lookup-afleidingen en alleen geverifieerde klassevelden.\n