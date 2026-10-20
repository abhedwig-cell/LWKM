# Projecteigenaarbesluit: dichtstbijzijnde geldige meteorologische gridcel

Datum: 2026-10-20
Status: vastgesteld ontwerpbesluit; implementatie en kwalificatie volgen.

## Regel
Indien voor een SVAT op een bepaalde dag een vereiste meteorologische waarde ontbreekt op de aan de SVAT toegewezen meteorologische rastercel, zoek de geografisch dichtstbijzijnde rastercel met een **geldige, aanwezige waarde voor die variabele en diezelfde dag**. Gebruik die waarde voor de SVAT. Geen nulvulling en geen tijdsextrapolatie.

De ruimtelijke afstand moet in een passend geprojecteerd coördinatenstelsel worden berekend tussen de SVAT-positie en centra van de kandidaat-meteocellen. Vermijd indexafstand wanneer pixelgrootte/geometrie verschilt. Zoek over de relevante volledige meteo-support; stop niet bij de direct aangrenzende pixels als die ook ontbreken. Alleen geschikte broncellen binnen de werkelijke data-support zijn kandidaten.

## Kwaliteitsvereisten
- Valide waarde betekent niet-NODATA, eindig en conform de variabele-specifieke semantische controles; een geldige nul (zoals neerslag 0) blijft geldig.
- Gebruik voor alle kandidaten een gelijkwaardig bronproduct, dezelfde variabele, eenheid en datum; meng geen jaren of bronfamilies.
- Bepaal bij gelijke afstand een vaste reproduceerbare keuze, bijvoorbeeld rasterrij en rasterkolom in oplopende volgorde.
- Leg per vervanging SVAT-ID, datum, variabele, oorspronkelijke gridcel, gekozen gridcel, afstand en bronidentiteit vast.
- Bewaar oorspronkelijke bronrasters ongewijzigd. Pas correctie in de SVAT/meteo-toewijzing of afgeleide HRU-forcing toe.
- Bij ontbreken van iedere geldige cel voor de betreffende dag/variabele blijft het gegeven ontbrekend en faalt de productiecontrole expliciet.
- Controleer bij HRU-aggregatie dat het gebruik van een vervangende SVAT-waarde consistent is met de bestaande SVAT-oppervlaktegewichten.
- Variabele-specifieke nearest-valid vervanging kan meteorologisch verschillende broncellen combineren. Rapporteer die menging in QA; toets de samenhang van eind-MET (bijv. Tmin <= Tmax en geldige dampdruk, neerslagduur).
- Voer tests uit voor ontbrekende doelpixel, meerdere ongeldige buren, geldige nul, gelijke afstand, grenssituatie, volledig ontbrekende dag en deterministische herhaling.

## Reikwijdte
Dit besluit vervangt het eerdere fail-closed beleid voor *lokale ontbrekende rasterpixels* van meteorologische invoer, waaronder de bekende ontbrekende 2018-neerslag/ETref-pixels. Het heft ontbrekende hele bronvariabelen, dagen, tijdreeksen, bronidentiteiten en overige MET-kwalificatie niet op. Het is een ruimtelijke imputatie die expliciet geaudit moet blijven.
