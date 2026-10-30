# Beregeningsbron: eigenaarbesluit 2026-10-30

Kies per HRU de beregeningsbron met het grootste totale werkelijke SVAT-oppervlak
uit area_svat.inp, gekoppeld op SVAT-ID en coördinaten. Bij exact gelijke
oppervlakken wint grondwater (broncode 1; oppervlaktewater is broncode 2).
De bestaande activeringsdrempel van meer dan 0,37 beregende lid-SVATs blijft
behouden. Dit besluit verandert de bronkeuze voor alle HRUs.

De eerder gestarte lokale wijziging van DRA naar SVAT-oppervlak was gebaseerd
op een misinterpretatie en is teruggedraaid vóór commit of pakketlevering.
De DRA-producer, aggregatie, kwalificatiecode en bijbehorende tests zijn exact
hersteld naar f6087165b7acc2179b1162351668157b3c6040ea.
DRA behoudt 62.500 m2 per lidcel. BBC behoudt eveneens zijn afzonderlijke
volledige-celconventie.

Tests controleren bronkeuze bij ongelijke SVAT-aantallen, oppervlakteoverwicht
voor beide bronnen, gelijke oppervlakken met ongelijke aantallen, geen beregening,
onbekende broncodes en behoud van de activeringsdrempel. De serverroute bindt
leden al aan werkelijke area_svat-waarden voordat derive wordt aangeroepen.
De nieuwe nationale bronkeuzes zijn nog niet op de server uitgevoerd.
