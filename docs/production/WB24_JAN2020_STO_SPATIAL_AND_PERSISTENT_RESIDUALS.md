# WB24: ruimtelijke en decadische diagnose januari 2020 (4 november 2026)

Berekening is uitgevoerd op de in deze conversatie aangeleverde WB23-SVAT-matrix met R0, R0+STO en r1..r3/s1..s3; geen nieuwe modelrun. Toegelaten SVATs 645574, R0=S6+Q4+DRN+RIV, geen qmodf. De oorspronkelijke WB18 januaridecades ondersteunen de WB23-analyse. Bij de huidige toets is februari niet integraal geverifieerd, dus geen generalisatie naar andere maanden.

Klasse | n | fraction cell exact 1.0
---|---:|---:
alleen zonder STO|586838|19.91%
alleen met STO|47029|81.29%
beide|6590|9.07%
geen van beide|5117|54.49%

De klasse 'alleen met STO' concentreert geografisch o.a. in 10-km-vakken rond x=210–240 km/y=330–360 km; ook elders. Niet afleiden dat regio per se een ander fysisch model heeft zonder gegevens over land/bodem/rekenschema.

Bij 'alleen met STO' is R0+STO binnen 0.4 m³ voor 80.70%/99.20%/99.47% van de SVATs in D1/D2/D3. Dit bevestigt een duidelijke regimeverschil bij vergelijking van onafhankelijke tijdstappen. Bewijst geen fundamentele STO-regel.

Van de 5117 resterende 'geen van beide'-SVATs zijn **277** gevallen geïdentificeerd met in alle drie decades dezelfde teken van R0, dagrest in alle drie >10 m³/d en CV van dagrest <5%. Voorbeelden:
- SVAT 428409, x191625,y408375, R0 per 10,10,11 dagen: +8661.181867,+8661.174094,+9527.247613 m³; gemiddelde +866.116 m³/d.
- SVAT 615346, x219875,y352375: +7792.083892,+7781.909678,+8560.450983 m³.
- SVAT 286187, x154625,y463375: +7658.811445,+7658.812103,+8424.694200 m³.

In deze 277 cases komt R0 relatief sterk overeen met Q4 (Pearson ca 0.960 over SVATs) en is DRN+RIV in 97.1% kleiner dan 1 m³ over de maand. Dit is correlatie, **geen** bewijs dat Q4 fout is. Bepaal welke van QLAT/FLF/WEL/GHB de dagconstante bijdrage draagt en vergelijk met originele cell budget output en tekencontracten.

Diagnostische output van de huidige analyse: `LWKM_WB24_Januari2020_STO_RuimtelijkeDiagnose.zip` (in de gebruikersconversatie), met ESRI ASCII-grid op volledige MODFLOW grid 1124x1300, 250m, RD, klassecode 1 zonder/2 met/3 beide/4 geen, -9999. Voorts regionale 10km-tabel en 5117 uitzonderingen inclusief flag persistent_daily_offset.

**Niet doen**: op grond van minimale residu STO per SVAT aan/uit schakelen in SWAP-productieketen, of in feite fysische fluxen corrigeren. Eerst brondefinitie en cross-validatie voor februari.
