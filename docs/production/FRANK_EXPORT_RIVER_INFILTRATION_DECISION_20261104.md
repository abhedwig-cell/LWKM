# Frank-export: definitie Infiltratie bevestigd

Projecteigenaarbesluit, 4 november 2026:

**Infiltratie = totale rivierinfiltratie** over alle relevante riviersystemen, niet totale infiltratie vanuit neerslag en niet de netto aanvoer. Dit is een hydrologische flux en moet gescheiden blijven van `Fldrin1`, `Fldrin2` en `Fldrin345` in de export, tenzij de officiële productiedefinitie hun relatie bevestigt.

Beoogde eenheid sluit aan bij de bestaande SVAT-info: mm/jaar; oppervlaktebasis en tekenconventie expliciet uit de oorspronkelijke producer overnemen, niet impliciet omzetten.

De `LWKM_makeHRU v0.20` brongebonden schemabeschrijving noemt de historische kolom `wegzijgingz(mm/j)` als `plotlist%infil`, uit `Riv_infiltratie_1991-2020_sum.asc`. Dit maakt `wegzijgingz(mm/j)` een **sterke bronkandidaat** voor de gewenste totale rivierinfiltratie. Voordat het exportprogramma deze kolom als authority bindt, verifiëren: betreft `Riv_infiltratie_1991-2020_sum.asc` inderdaad de totale rivierinfiltratie (alle systemen), welke m2-basis is gebruikt, en is er geen dubbeltelling met de `Fldrin`-componenten.

`LWKM_Export_Frank_v02.zip` blijft prototype: het bijbehorende veldmappingsbestand moet in de volgende codeversie expliciet worden aangepast en met echte bronnen getest. Geen claim dat v0.2 al het veld vult.

Overige besluiten uit `FRANK_EXPORT_FIELD_DECISIONS_20261104.md` blijven gelden: `GG` is echte gemiddelde grondwaterstand; `Dynamiek=GLG-GHG`; `Fldrin345=aanvoer_sys3+sys4+sys5`; indicator vervangen en `N ???` blijven open.
