# HRU: SWP/DRA-interface ontvangen en assemblage aangesloten

16 november 2026. Vervolg op de ontvangen Server06-preflight v04. Geen nieuwe waterbalansanalyse en geen herafleiding van modelinvoer.

## Ontvangen serverrapport

Originele upload: `SWP_DRA_INTERFACE_20261116.json` (208 bytes).
SHA256 van de daadwerkelijk lokaal gelezen uploadbytes:
`0a2de18ce610d4b081b002cf94606dfc1100f2983b71a3117159c4ff3cf21550`.

```json
{
  "status": "SWP_DRA_HORIZON_MATCH",
  "swp_files": 10242,
  "dra_files": 10242,
  "failed": 0,
  "errors": [],
  "scope": "ACTUAL_SERIALIZED_HORIZONS_AND_COFANI_ONLY_NOT_HYDROLOGICAL_VALIDATION"
}
```

De aansluiting tussen de daadwerkelijk geschreven SWP-hydraulische bodemhorizonten en DRA-COFANI is daarmee volgens het ontvangen serverrapport voor alle 10242 HRU's geslaagd. Deze specifieke interfacecontrole is afgesloten. De reviewer heeft de grote SWP/DRA-populatie niet zelf lokaal geopend. Het rapport bevat geen per-bestandhashregister en kwalificeert niet de volledige syntax, tijdas of hydrologische respons.

De eerdere preflight v04 blijft geldig voor de aanwezigheid van de vier hoofdproducten en de daarin herkende lokale crop/CO2-verwijzingen. Haar uploadhash is `b1c11d87dd499455543c09a948cfbf44f977bf973fb19e2455ef95dbb5de174b`.

## Concrete vervolglevering

Distributiepakket: `LWKM_HRU_Assemblage_v01.zip` (25027 bytes).
SHA256: `810cf3b6ba547a1bf278ee098a267bf5154d9801e384abdcc48f189af4e24527`.
Nieuwe aansturing: `assemble_received_hrus.py`, SHA256 `242d70e6bdd573149b4d742338627b09bdee06491e411260598e04a941762040`.

Dit is een lokaal gebouwd en getest downloadpakket. De nieuwe aansturing, tests en pakketbestanden zijn in deze commit niet als afzonderlijke Git-bronbestanden ingecheckt. Deze commit legt de ontvangst en de exacte distributie-identiteit vast; hij claimt geen volledige repository-integratie van het nieuwe pakket.

Het pakket bevat ongewijzigde Python-W11-code van commit `276fbaf8d0571a3fe7f4c78946835fa0b0aee097`:

- `tools/assemble_swap_package.py`, Git blob `1c33fd2153e3b42f4cdd4dda5b07747d866f1d23`;
- `tools/swp_file_reference_guard.py`, Git blob `db7c5d1193ec2c37026d667cb5f9c3c721e4c045`;
- `tools/swp_full_oracle.py`, Git blob `857a500caf946ca595b89939600750be45f7e5ba`;
- `tools/swp_template_adapter.py`, Git blob `0fab65fd558ba9f7a88ffc0ec7be4c195c80ec76`.

Alle vier blobidentiteiten zijn lokaal uit de werkelijk verpakte bytes nagerekend. Dit gebruikt de bestaande Python-route, geen nieuw gebouwde Windows-EXE. De bestaande serverinterpreter `E:\tools\deltaforge\deltaforge_4\python.exe` en de standaardbibliotheek volstaan.

## Gedrag

De configuratie bindt uitsluitend de vier al ontvangen directories: SWP Server06, DRA Server01, BBC09 `work_e_bbc09_1970_2022` en MET06 decimal-server-verified. De originele ontvangen preflight en interfacecontrole zitten ongewijzigd in het pakket en worden op hun hash gecontroleerd.

De aansturing leest de daadwerkelijk aanwezige SWP-bestandsnamen, de benoemde gewasrotatietabel en ATMOFIL uit de betrokken CRP-bestanden. Bronnen worden naar de genoemde lokale doelbestandsnamen gekopieerd. Bijvoorbeeld `HRU_00001.met` naar `1.met` indien de bestaande SWP `METFIL='1.met'` noemt. De SWP wordt byte-identiek als `swap.swp` opgenomen. Ook DRA, BBC, CRP en CO2 blijven byte-identiek. Er worden geen parameters, periodes, gewasrotaties, switches of bronbestanden herschreven.

Per HRU worden de broncatalogus, bronhashes en het bestaande W11-manifest vastgelegd. W11 controleert kopie-identiteit en publiceert via een tijdelijke map. Herstart valideert de bestaande catalogus, het manifest en alle bron-/doelhashes; wijzigingen worden geweigerd, niet overschreven. Bij een fout stopt de batch met HRU-ID en foutreden; al voltooide kandidaatmappen blijven behouden. Een eigen lock voorkomt gelijktijdig schrijven.

De doelmappen zijn `LWKM_rebuilds\SWAP_HRU_Server06_1970_2022_v01\run_<HRU>`. Het kleine terugrapport is `LWKM_tools\LWKM_HRU_Assemblage_v01_resultaat\STATUS_HRU_ASSEMBLAGE.json`.

## Uitvoering en testgrens

Vanuit de uitgepakte map met de starter:

```cmd
ASSEMBLEER_HRU_RUNMAPPEN.cmd
```

De standaardopdracht assembleert alle 10242 HRU's. Een expliciete subset kan via `--hrus 1,3,7870,7871,7929`. De volledige opdracht hergebruikt eerder samengestelde, ongewijzigde pakketten na hashcontrole.

25 lokale unittest-tests zijn geslaagd, zowel in de bouwmap als opnieuw vanuit de definitieve uitgepakte ZIP. Ze omvatten echte W11-aanroepen op synthetische bestanden, juiste bestandsaliassen, meerdere gewassen met gedeelde CO2, hervatten, gewijzigde bron-/doelbytes, ontbrekende bestanden, onherkende/onvolledige rotatietabellen, andere werkdirectories, populatie/subsetrapportage en oorspronkelijke Git-blobidentiteiten.

De echte 10242 NHI-pakketten zijn in deze sessie niet geassembleerd en de Windows-CMD-starter is niet op Windows uitgevoerd. Er wordt geen SWAP-executable meegeleverd of gestart. De status blijft `PACKAGE_CANDIDATE_NOT_ADMITTED`, met `production_enabled=false` en `swap_executed=false`. Eerdere producentkwalificaties worden niet heropend; volledige modelrunacceptatie wordt evenmin uit kopie-identiteit afgeleid.
