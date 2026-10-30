# Cropfiles en CO2 naast iedere SWP

Projecteigenaarbesluit en implementatie, 30 oktober 2026.

De directe SWP-generator schrijft voortaan `swp/<HRU>/<HRU>.swp`. In dezelfde directory staan de benodigde cropfiles en `atmospheric_1975-2020.co2`. `CROPFIL` bevat een lokale bestandsstam; `ATMOFIL` bevat `'atmospheric_1975-2020'`, met de door SWAP toegevoegde extensie `.co2`. Er zijn geen verwijzingen naar een gedeelde gewasdirectory.

De vier basisbestanden staan onder `templates/crops/base/`. Het CO2-bronbestand staat onder `templates/atmosphere/` en is ongewijzigd overgenomen uit `root.zip`, `root/Ab/met/atmospheric_1975-2020.co2`. Het bevat ieder jaar 1970 t/m 2025, steeds 360,80 ppm (referentie 1995). De bestandsnaam blijft behouden. De generator controleert de jaardekking van elke run.

De bestaande rotatiedatums en gewastypen blijven behouden. Voor de maisrotatie met vanggewas is ook het oorspronkelijke `vanggewas.crp` uit dezelfde bron opgeslagen onder `templates/crops/auxiliary/`; dit is een aanvullend rotatiebestand, geen vijfde landgebruiksklasse.

Bij generatie wordt `SCHEDULE` in de lokale cropfiles 1 bij een niet-nul `irrigation_id`, anders 0. CO2-verwijzingen worden ingevuld of toegevoegd; bestaande assimilatieschakelaars blijven behouden. Dit is geen herkalibratie.

Het manifest bevat hashes van alle gebruikte basisbestanden en van iedere gegenereerde SWP, cropfile en lokale CO2-kopie. Herhaald genereren controleert alle bestanden en herstelt afwijkende gegenereerde bestanden. Gebruik daarom voor latere HRU-kalibratie een afzonderlijke werk-/runmap: opnieuw genereren kan die wijzigingen overschrijven.

Beide serverpakketbouwers nemen de templates en het nieuwe hulpmodule mee. De SWP/DRA-interfacecontrole zoekt SWP-bestanden ook in de HRU-submappen.

Gebruik een nieuwe outputdirectory bij overgang van de oude platte SWP-indeling. BBC, DRA en MET moeten bij het samenstellen van uitvoerbare runs nog op de door de SWP aangewezen locaties beschikbaar worden gemaakt; deze wijziging assembleert die bestanden niet.

Validatie: 55 gerichte tests geslaagd, waaronder beide beregeningsbronnen en geen beregening, alle vier basisgewassen, vanggewas, CO2-jaardekking, ongewijzigde rotatie, CLI-generatie, hergebruik en herstel van een gewijzigd lokaal cropbestand. Er is geen nieuwe SWAP-modelrun uitgevoerd.
