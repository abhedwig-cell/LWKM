# W09 MET herstel, 27 oktober 2026

## Vastgestelde bronnen (authority)
- De door projecteigenaar aangeleverde `LWKM_W09_Windows_x64_qualified_smoke(1).zip` bevat **reeds een werkende Windows x64 EXE**, `lwkm_w09_meteo.exe` (385536 bytes), `run_all.cmd`, `w09_config.ini`, `hru_meteogrid_weights.csv` en `precipitation_19700101.asc`.
- De bestaande configuratie gebruikt `E:\LHM_4.3.3\Data\2_Model_Input\meteo\` met variabelen RD1, EV24, TN, TX, Q, FG, WIND en WET_RAW. Deze paden zijn bekend en mogen niet opnieuw als ontbrekende context worden behandeld.
- Bestaande W09 schrijft `met_YYYY.csv` voor alle HRU's, terwijl SWAP een meteorologisch bestand per HRU vereist.
- De oorspronkelijke nearest-valid-rastercelprocedure loopt voor iedere ontbrekende pixel over alle geldige pixels en is bij veel no-data pixels zeer duur.
- MET03/MET05 bevatten een lokaal op Linux geteste C++-vervanging; **er is nog geen geverifieerde Windows EXE van MET03/MET05**. Niet als serverklaar presenteren.
- De BBC-route gebruikt een launcher plus PowerShell `Add-Type -OutputAssembly` voor C#-broncode op de NHI-server. Dit werkt voor C#, niet voor de W09 C++-broncode. Voor W09 bestaat bovendien een eerdere bewezen native Windows GitHub Actions route met MSVC `/MT` (PR #17).

## Projecteigenaarbesluit
Lever voortaan **een volledig, parameterloos startbaar Windows-pakket** met ingebouwde bekende paden; direct per HRU een SWAP-meteobestand voor de volledige tijdreeks, geen `met_YYYY.csv` als eindproduct. Leg code, build, test en evidence vast in Git. Herhaal geen bekende vragen over configuratie.

## Verplichte releasepoorten
1. Bouw native Windows x64 EXE uit de MET03/05 code in GitHub Actions met MSVC `/MT`.
2. Rooktest op Windows: exacte HRU-populatie, tweede dag wordt aangevuld, geen jaarlijkse CSV's als eindresultaat.
3. Vergelijk op identieke ASCII-invoer enkele HRU-dagwaarden met de oude W09.
4. Test formaat daadwerkelijk in gebruikte SWAP-versie; een bestand met extensie `.met` is niet automatisch geldig SWAP-formaat.
5. Test paden/read-only brondata en prestatieprofiel op NHI; bewaar logs, hashes, exacte commit en run-resultaat.
6. Keur pas als productie goed na alle bovenstaande tests.

## Risico's
- `w09_met_config.ini` bevat nog `scale_*=1`: eenheidsbevestiging nodig.
- De vorige MET05-output is **alleen lokaal Linux-getest**.
- BBC07H heeft wel bewezen servercompilatie en HRU-mapping, maar is nog niet volledig productiesuccesvol.
