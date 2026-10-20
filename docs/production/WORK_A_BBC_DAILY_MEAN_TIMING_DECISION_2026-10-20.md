# Projecteigenaarbesluit BBC-timing, 2026-10-20

Status: vastgesteld ontwerpbesluit voor de LWKM-productieroute. Vervangt de eerdere blokkade die variërende daggemiddelde BBC-fluxen afwees wegens SWAP-interpolatie.

## Besluit
Per HRU en kalenderdag wordt de daggemiddelde effectieve grondwaterflux (mm/d) rechtstreeks als datumwaarde in de SWAP 4.3.1 BBC-tijdreeks geschreven. De daggemiddelde flux is de over de HRU-leden geaggregeerde FLF + FRF + FFF + GHB + WEL van MODFLOW-laag 1, na bestaande tekenconversies en omrekening met HRU-oppervlak.

SWAP kan tussen BBC-datumwaarden interpoleren. De projecteigenaar accepteert dat de door SWAP geïntegreerde dagflux daardoor afwijkt van de opgegeven daggemiddelde bronflux. Maak hiervoor geen additionele temporele reconstructie, trapfunctiebenadering of volumecorrectie; dit is geen productiestopper.

## Wat wel behouden blijft
- Een datumwaarde is een daggemiddelde bronflux, niet aantoonbaar een exact dagvolume na SWAP-interpolatie.
- Gebruik de reeds gekwalificeerde BBC-syntaxis, datumvolgorde en begin/einddekking; verzin geen ontbrekende waarden en extrapoleer niet buiten de bronperiode.
- Bewaar de originele dagelijkse broncomponenten en hun som met herkomst/hashes.
- Registreer de mogelijke interpolatieafwijking als expliciete geaccepteerde benadering, niet als bewezen nulverschil.
- Houd overige onafhankelijke bron- en packagekwalificatiegates intact.

## Uitvoeringsopdracht
Pas de Work A BBC-serializer en negatieve tests aan: variërende valide daggemiddelden zijn toegestaan onder dit expliciete owner-profiel. Verwijder uitsluitend de temporal reconstruction blocker; laat NODATA, ontbrekende dagen, ontbrekende bronkwalificatie en modelinterfacefouten fail-closed. Genereer en test meerdaagse BBC-bestanden en werk status, runbook en overdracht aan Leo bij.
