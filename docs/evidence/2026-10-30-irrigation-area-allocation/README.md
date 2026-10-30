# Landelijke beregeningstoekenning, 2026-10-30

De eigenaar heeft de landelijke oppervlakteregel goedgekeurd: rangschik HRUs
op beregend SVAT-oppervlak / totaal HRU-oppervlak en selecteer de prefix waarvan
het cumulatieve HRU-areaal het dichtst bij het totale beregende SVAT-areaal ligt.
Geen beregende SVATs betekent geen beregening. Bij gelijke aandelen sorteert
HRU-ID oplopend; bij gelijke absolute areaalafwijking wint het kleinere areaal.
Bronkeuze blijft de grootste beregende SVAT-oppervlakte, met grondwater bij gelijkheid.

summary.json is een lokale herberekening uit het ontvangen Server04-rapport
controle(2).zip en area_svat(2).inp. Het oppervlaktebestand heeft exact dezelfde
hash als alle zes in het serverrapport geregistreerde periodebestanden. De
membership-hash komt eveneens overeen. Het doelareaal is dus gebaseerd op de
serverwaarden; er is geen nieuwe server- of SWAP-uitvoering geclaimd.

Reproduceer met tools.audit_irrigation_area_allocation:
python -m tools.audit_irrigation_area_allocation --report REPORT.zip --area AREA.inp
--membership MEMBERSHIP.csv.gz --output OUTPUT (op één commandoregel).

78 tests slagen: exacte prefixkeuze, oppervlakte- en bronweging, nul/all-irrigation,
exacte decimale oppervlakken, deterministische gelijke standen, populatiecontrole,
server generatie/hervatten, renderer, DRA-ongewijzigd en SWP/DRA-interface.
De beregeningstoekenning staat in de parametertabel en diagnostiek. De bestaande
renderer verbindt irrigation_id nog niet met het uiteindelijke beregeningsmanagement;
daarvoor is aanvullende aansluiting nodig vóór modeluitvoering met beregening.
De SWP-manifest meldt irrigation_management_connected=false expliciet.

De eerdere fout in automatische DRA-mapselectie is hersteld. De DRA-formule en
het volledige-celoppervlak zijn niet gewijzigd. Totaaloppervlaktebehoud bewijst
geen bron- of regionale equivalentie; de bronverschuiving staat in summary.json.
