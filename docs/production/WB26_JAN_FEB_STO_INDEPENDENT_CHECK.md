# WB26: onafhankelijk januarie/februari-onderzoek van STO-regimes

Datum 4 november 2026. Uitgevoerd op oorspronkelijke WB18-SVAT-detailgegevens voor februari 2020 en bestaande WB23-classificatie voor januari 2020. 645574 fysisch toelaatbare SVAT's.

Definities in m3/maand: R0=bdgdecstot+bdgpm+bdgpssw+bdgpsgw+bdgetact+bdgqrun+QLAT+FLF+WEL+GHB+DRN+RIV; Rsto=R0+STO. Geen qmodf, volledige MF-celvolumes. Drempel 1m3 absolute maandrest.

| Jan klasse | feb1 | feb2 | feb3 | feb4 | Jan totaal |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 alleen zonder STO | 584718 | 5 | 567 | 1548 | 586838 |
| 2 alleen met STO | 1 | 46788 | 102 | 138 | 47029 |
| 3 beide | 2852 | 38 | 3697 | 3 | 6590 |
| 4 geen van beide | 660 | 2083 | 6 | 2368 | 5117 |

99.64% van klasse 1 en 99.49% klasse 2 blijft gelijk. Klasse 4 is minder stabiel, nog 2368/5117 (46.28%) in februari; 2083 verschuiven naar klasse 2.

Som abs R0 februari 16016224m3; som abs Rsto 818568580m3. Numeriek sluitgedrag is geen bewijs van fysieke volledigheid of rechtvaardiging voor per-cel residual-gebaseerde STO-selectie.

De aangeleverde `msw1postfm.for` levert nu primaire code-evidence: `msw1postfm_qmodf` regels 118-135 definieert `qmodf` als balansrest, met `sc1` en `wbmfct`, dus niet een onafhankelijke directe som van de vier QEXT4-pakketten. In `msw1postfm_sc1`, regels 268-288 wordt `sc1lv` geselecteerd als MODFLOW-grondwaterstand onder `glk-dpbotk+dc` daalt, de bodem van **MetaSWAP-profiel**. Dit biedt een hypothese voor ruimtelijk stabiele diepe klasse 2, maar zonder per-SVAT `dpbotk` nog niet bewezen. Een eerdere WB25-proef met MODFLOW `BOT_l1` is niet dezelfde grens.

De volledige onafhankelijke vergelijking inclusief klasse per SVAT en de maand/decadische resten staat als gebruiker-downloadbaar bestand `LWKM_WB26_JanFeb2020_STO_Validatie.zip`. Stopcriterium blijft één gerichte profielbodemtoets, daarna terug naar HRU-keten.