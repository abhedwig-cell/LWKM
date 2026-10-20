# LWKM besluit 2026-10-20: KNMI wind en neerslagduur buiten NHI-server

Status: eigenaarbesluit, nog te implementeren/kwalificeren.

## Architectuur
NHI-server heeft geen internet en geen Python. Download KNMI-daggegevens buiten NHI, maak gehashte lokale dagtabellen met stationlocaties, windsnelheid (KNMI FG in 0,1 m/s) en neerslagduur (KNMI DR in 0,1 uur), en lever die offline over als compact bestand. Server leest deze via zelfstandige EXE/consoleverwerking indien server-side integratie nodig is; geen netwerkcall op NHI.

De bestaande LHM-neerslagrasters zijn gezaghebbend voor neerslaghoeveelheid. KNMI dient uitsluitend voor wind en neerslagduur. Controleer SWAP 4.3.1 ALTW-meethoogtecontract (KNMI wind 10m) voordat productie toegelaten wordt.

## Harde SWAP-consistentie
Per HRU-dag: als rain_mm == 0 moet WET = 0; als rain_mm > 0 moet 0 < WET <= 1. Negatieve, ongeldige of ontbrekende neerslag is een fout, geen nul.

Voor rain == 0: zet WET = 0, ongeacht positieve KNMI-stationsduur, en audit correctie.
Voor rain > 0: kies eerst geografisch dichtstbijzijnde geldige station met DR > 0 op diezelfde dag; ook als oorspronkelijke dichtstbijzijnde station DR = 0 heeft. Wanneer geen geschikte waarneming bestaat, gebruik niet stilzwijgend DR=0: markeer een expliciete positieve fallback volgens een nog te besluiten en te kwalificeren methode, of blokkeer het betrokken record tot die methode bepaald is.

KNMI-DR / 240 = WET (dagfractie); KNMI-FG / 10 = wind m/s. Gebruik per dag valide stationgegevens en reproduceerbare afstand/tie-break. Bewaar station-ID, afstand, correctie/fallbackvlag, bronhash en datum. Geen vermenging van dagen.

Verschillen tussen lokale rasterneerslag en stationsneerslag zijn geen reden het raster te wijzigen.

## Test
Controleer vier combinaties regen nul/positief en DR nul/positief, ontbrekende DR, grenswaarden, geen stations met positieve DR, geldige nulwind, datumdekking 1970-2022, stationswisselingen, en SWAP-MET-preflight. Zonder gekwalificeerde fallback geen productie-admission.
