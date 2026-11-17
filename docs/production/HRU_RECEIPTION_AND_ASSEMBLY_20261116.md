# LWKM HRU-productie: ontvangst en assemblage (16 november 2026)

## Besluit en scope
De uitgebreide eerdere waterbalansdiagnostiek wordt niet opnieuw uitgevoerd. De vastgestelde QModF-source-authority uit IMODFLOW.ZIP en de eerdere niet-closure status blijven gelden. Ontbrekende STO/BND zijn geen aanleiding om de HRU-productie stil te zetten of fluxen te fitten.

## Gecontroleerde input
Run-lokale area_svat.inp SHA256 352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc; mod2svat.inp SHA256 c84dcc76ef9e32e5ee3fc8bda0e27ef45b8f5765ed875e7bc7c84a25baf9e8dd. 645582 SVATs; 643532 met laag-1-link, 2050 glastuinbouwverwijzingen met laag 0. 36317 aanvullende links naar lagen 2 t/m 8 worden niet als extra SVAT-volumes dubbel geteld. Bronselectie januari 2020: 424 IDFs; de latere waarden- en maskeraudits zijn exploratief, niet als volledige modelclosure geaccepteerd.

## Productievolgorde
1. Bestaande SWP Server06-opzet: per HRU SWP + passende crop- en CO2-assets; noteer dat het kandidaatbestanden zijn.
2. Bestaande DRA Server01-producer voor de volledige tijdas, met eigen 5-level regels; behoud kandidaatstatus.
3. Ontvang bestaande BBC-output op basis van gehele MODFLOW-celoppervlakte van 62500 m2 en MET-output. Herbereken geen reeds geproduceerde bestanden als ontvangsten volstaan.
4. Ontvangstcontrole van SWP/DRA/BBC/MET voor 10242 HRUs, inclusief detectie van ontbrekende bestanden of dubbele bestandsidentiteiten. De eerste ontvangstcontrole v01 vond nul door foutieve standaardpaden, ondanks bestaande uitvoer. De NHI-directory-survey van 16-11-2026 vond 10242 SWP Server06 HRU-mappen met CO2, 10242 DRA Server01, 10242 BBC09 voor 1970-2022 en 10242 MET06. De lokale read-only ontvangstcontrole v02 bindt expliciet de vier vastgestelde bronmappen; exacte per-HRU aanwezigheid en inhoud blijven een aparte servergate. Pakket LWKM_HRU_ReceiveGate_v02.zip is lokaal getest (2 unittest-tests PASS), niet als Git-code ingediend.
5. Pas daarna W11 assembler met expliciete broncatalogus en SHA256/qualification-status toe; geen automatische productievrijgave voor alleen aanwezige kandidaatbestanden. Vervolgens SWAP format/preflight en een afgebakende echte modelrun.

## Gekozen serverdirectories (relatief aan LWKM_tools)\n- SWP: LWKM_WorkE_SWP_Server06\\LWKM_WorkE_SWP_Server06\\swp_server06_productie\\swp\n- DRA: LWKM_WorkE_DRA_Server01\\LWKM_WorkE_DRA_Server01\\dra_server_productie\\dra\n- BBC: LWKM_WorkE_BBC09\\LWKM_WorkE_BBC09\\work_e_bbc09_1970_2022\\bbc\n- MET: LWKM_W09_MET06_decimal_server_verified\\LWKM_W09_MET05_Windows_x64_Server\\w09_met_output\n\n## Gates
Niet automatisch promoveren naar productie: bron- en producthashes, SWP crop- en CO2-verwijzingen, SWP/DRA bodemlaagconsistentie, BBC celoppervlak en schema, MET tijdas, W11 asset-catalogus, en foutloze SWAP smoke. Er wordt geen hydrologische sluiting geclaimd.

## Beschikbare ontwikkelingsbranches
PR #25 (SWP/DRA direct), PR #20 (native DRA), PR #18 (W11 packager), PR #21 (MET) zijn open en moeten afzonderlijk geïntegreerd en gevalideerd worden; deze notitie verandert geen wetenschappelijke producent of open PR-inhoud.
