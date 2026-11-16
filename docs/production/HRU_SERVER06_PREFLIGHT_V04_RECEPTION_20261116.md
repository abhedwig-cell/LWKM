# Ontvangst HRU Preflight v04, 16 november 2026

## Ontvangen serverbewijs

Bestand: `STATUS_HRU_PREFLIGHT_v04.json`, aangeleverd door de projecteigenaar.
SHA256 van de oorspronkelijke uploadbytes: `b1c11d87dd499455543c09a948cfbf44f977bf973fb19e2455ef95dbb5de174b`.
Status: `SWP_SERVER06_SOURCE_AWARE_PREFLIGHT_NOT_ADMISSION`.

Alle vier de gerapporteerde tellers zijn 10242:

- `recognized_rotation_crops_hrus`
- `atmo_links_in_crop_hrus`
- `all_four_present`
- `no_issues_within_scope`

`examples` is leeg. `sha256_mode=false`. De gerapporteerde CSV-SHA256 is `5035f1f4ad41322113b1e829615b4cb08eec56ef01b4a612c976149aa57b2f7c`; dit is geen hashregister van alle modelinvoerbestanden.

De geselecteerde producten blijven SWP Server06, DRA Server01, BBC09 uit `work_e_bbc09_1970_2022` en MET06 decimal-server-verified, op de eerder in deze branch vastgelegde werkelijke serverpaden. Er is geen nieuwe bronselectie of herberekening nodig.

## Afbakening

De aanwezigheid van de vier bestandstypen en de door de Server06-specifieke controle herkende gewas- en CO2-verwijzingen zijn bevestigd volgens het ontvangen serverrapport. De reviewer heeft in deze ontvangststap niet alle 10242 SWP- en CRP-bestanden zelf geopend.

De parser herkent vijf bekende gewasstammen; hij is geen algemene SWAP-parser. Rotatieregels zijn niet afzonderlijk aan datums getoetst. De syntax en tijdas van DRA, BBC en MET zijn door deze v04-controle niet gecontroleerd. Geen nieuwe productie- of modelrunvrijgave. `production_enabled=false` blijft staan. Deze ontvangst maakt bestaande producentkwalificaties niet ongedaan en heropent geen waterbalansonderzoek.

## Bestaande vervolgstap hergebruiken

De bestaande `tools/check_swp_dra_compatibility.py` uit SWP Server06 controleert de daadwerkelijk geserialiseerde hydraulische bodemlagen tegen de lengte van DRA-`COFANI`. De pakketbouwer `tools/package_swp_nhi_producer.py` levert hiervoor al `controleer_swp_dra.cmd`. Beide bestanden zijn opnieuw gelezen op commit `276fbaf8d0571a3fe7f4c78946835fa0b0aee097` van `work/swp-direct-hru-20261029`.

Dit is een interfacecontrole, geen tijdascontrole en geen hydrologische validatie. Gebruik de expliciete DRA Server01-map, niet de oude C2-map. De starter accepteert `--dra` en `--report`. Een geslaagd rapport moet `SWP_DRA_HORIZON_MATCH`, `swp_files=10242`, `dra_files=10242` en `failed=0` melden.

Na die aansluiting blijven de bestaande BBC/MET/DRA-kwalificaties, hun binding aan de te assembleren bestanden en het W11-catalogus-/runmapcontract het uitgangspunt. Er wordt voor deze ontvangst geen nieuwe preflight-implementatie gemaakt en geen producent aangepast.
