# Frank GxG/GG v0.2: GG uit 14e/28e

Projecteigenaarbesluit 4 november 2026: gebruik voor GG hetzelfde halfmaandelijkse head-rooster als GHG en GLG, om I/O en rekentijd te beperken. De definitie is **het rekenkundig gemiddelde van alle 14e/28e-grondwaterstanden** in kalenderjaren 1991–2020, niet het dagelijkse gemiddelde en niet (GHG+GLG)/2.

De benodigde bron-IDF's zijn 720 kalendermeetmomenten (30 jaar × 24) plus 18 meetmomenten van april–december 1990 om het eerste hydrologische jaar van GHG/GLG te voltooien, totaal **738**. GVG gebruikt 14 maart, 28 maart en 14 april; die zitten al in dezelfde selectie. Ontbrekende benodigde bron-IDF's leveren fout bij broncontrole. Per SVAT worden ongeldige meetmomenten geregistreerd en een onvolledige periode niet gedeeltelijk als volledig berekend.

Software: `LWKM_Frank_GXG_GG_v02_14_28.zip` geleverd in gebruikersconversatie, synthetische binaire IDF-test geslaagd, syntax en ZIP integriteit gecontroleerd. Onderliggende code nog niet als broncode in Git geïntegreerd, nog geen echte NHI-run geverifieerd.

Uitvoering: pak uit onder `LWKM_tools`, open CMD in `LWKM_Frank_GXG_GG_v02`, voer `CONTROLE_HEADS.cmd` uit en vervolgens `START_GXG_GG_1991_2020.cmd`. Bestaande MODFLOW-fluxexport niet wijzigen. Resultaat bevat `GG_meetmomenten` en `GG_meetmomenten_vereist` in plaats van eerdere dagelijkse telling.