# LWKM waterbalans: projecteigenaarbesluit 2026-11-02

Voor deze LHM/MetaSWAP-toepassing wordt **geen drainage in MetaSWAP berekend**, dus `qdr = 0`. De laag-1-grondwaterberegeningsonttrekking `qspgw` is alleen potentieel relevant voor de SVAT die volgens `scap_svat.inp` op MODFLOW-laag 1 is aangesloten: SVAT **207543**. Voor alle andere SVATs is de laag-1-onttrekkingsbijdrage `qspgw = 0`.

Volgens de besproken MetaSWAP-relatie `qsat = qmodf + qdr + qspgw` volgt voor deze toepassing `qsat = qmodf + qspgw`, en buiten SVAT 207543 `qsat = qmodf`.

**Controleprotocol:** vergelijk `bdgqmodf` per kalenderdecade, jaar en 1991–2020 met de overeenkomstige selectie van dagelijkse MODFLOW-laag-1-stressen. Gebruik gelijke cel-/SVAT-ondersteuning, volumes, tekenafspraken en bronselectie. De enige mogelijke laag-1-beregeningscorrectie isoleren voor SVAT 207543; bevestig het daadwerkelijke decadevolume voordat een correctie wordt aangebracht. MODFLOW-berging blijft onbekend. Onverklaarde verschillen niet automatisch compenseren. Het onderscheid tussen `qmodf` en `qsat` blijft expliciet.
