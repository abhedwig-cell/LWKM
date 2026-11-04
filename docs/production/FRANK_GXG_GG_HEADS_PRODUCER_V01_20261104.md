# Frank export: grondwaterkarakteristieken GHG, GLG, GVG en GG

Datum 4 november 2026. Losstaande Python-producer op NHI-server, naast de lopende MODFLOW-brutofluxexport (v0.7).

- GHG: per hydrologisch jaar y (april y-1 t/m maart y) gemiddelde van drie hoogste standen op 14/28 van iedere maand (dus drie kleinste diepten); vervolgens gemiddelde over hydrologische eindjaren 1991 t/m 2020.
- GLG: identiek, drie laagste standen (drie grootste diepten).
- GVG: per kalenderjaar VG3 van 14 en 28 maart en 14 april; gemiddelde 1991 t/m 2020.
- GG: gemiddelde van alle dagelijks waargenomen laag-1-heads over kalenderjaren 1991 t/m 2020, niet van GHG en GLG.
- Dynamiek = GLG − GHG.
- Maaiveld per originele `area_svat.inp`; resultaten in cm onder maaiveld positief beneden maaiveld, niet geklipt boven maaiveld.
- Altijd volledige hydrologische jaren, dus eerste vereiste head **1 april 1990**, laatste **31 december 2020** (voor GG).
- Bronnen `LWKM_run_resultaten_totaal/modflow/head/head_YYYYMMDD000000_l1.IDF` zijn samengestelde laag-1-head-IDFs. De acht `p000..p007` partities per dag mogen niet direct voor een landelijke SVAT-vector worden gebruikt. Inventarisatie faalt bij ontbrekende of dubbele bron.
- Per SVAT 24/24 halfmaandstaten voor ieder hydrologisch jaar, 3/3 voor ieder VG3-jaar, alle kalenderdagen voor GG, anders indicator leeg; incomplete jaarreeksen worden niet zonder expliciete contractwijziging deels gemiddeld.
- Export: `FRANK_LHM_SVAT_GXG_GG_1991_2020.csv` met SVAT, oppervlakte, xy, GHG, GLG, GVG, GG, dynamiek en dekking plus machineleesbaar manifest.
- **Caveat**: head laag 1 is slechts een freatische grondwaterstand waar laag 1 die representeert. De vergelijking met originele MetaSWAP-GxG blijft een aparte kwalificatiestap.

Softwarepakket geleverd: `LWKM_Frank_GXG_GG_v01.zip` in de gebruikersconversatie. Python-code lokaal op echte binaire gesynthetiseerde IDF-tests over 641 dagen getest (2 SVATs), inclusief GxG, VG3, GG, 2020 leap year en fail bij ontbrekend dagbestand; ZIP-integriteit OK. **Nog geen NHI-serverresultaat**.

Start vanuit uitgepakte folder `LWKM_tools/LWKM_Frank_GXG_GG_v01`:
```cmd
CONTROLE_HEADS.cmd
CONTROLE_HEADS_2020.cmd
START_PROEF_GXG_GG_2020.cmd
START_GXG_GG_1991_2020.cmd
```
De broncheck scant bestandsnamen zonder alle IDF-rasters in te lezen. Niet alle zware routines tegelijk starten terwijl v0.7 dagelijks duizenden fluxrasters verwerkt.

Wetenschappelijke bronnen: https://www.wur.nl/nl/onderzoek/producten-diensten/grondwaterdynamiek en https://docs.geostandaarden.nl/bro/wdm/ .
