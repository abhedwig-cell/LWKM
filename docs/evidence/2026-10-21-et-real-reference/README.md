# Echte ET-pilotreferentie, 21 oktober 2026

Lees eerst `../../production/ET_CAL01_REAL_REFERENCE_2026-10-21.md`.
Deze map bevat echte ontvangen MetaSWAP-cijfers, geen synthetische fit en geen SWAP-validatie.

- `HRU21_reference.csv.gz` bewaart de exacte oorspronkelijke gezamenlijke CSV-bytes.
- `SHA256SUMS.txt.gz` en `source_manifest.csv.gz` bewaren de originele exportmanifesten.
- `receipt.json` is de ongewijzigde ontvangst van de bestaande ontvanger. De originele ZIP en de losse ontvangstassets zijn daaraan via hashes en bronidentiteit gekoppeld; de oorspronkelijke ZIP is niet nogmaals in Git gedupliceerd.
- `reception.json` noemt ZIP-hash, Library-identiteit, scope en blokkades.
- `reference-diagnostics.json` verklaart de diagnostische tekenhypothese. Dit bestand is geen semantische toelatingsverklaring.
- `annual-hru.csv` en `seasonal-hru.csv` bevatten de conditionele sommen. `D_` betekent oorspronkelijke bronterm maal de expliciet verklaarde tekenfactor.
- `source_hru_support.csv` bevat alle 10.242 oorspronkelijke HRU-oppervlakken; `selected-hru-support.csv` alleen de 21 pilot-HRU's.
- `member-irrigation-support.csv` en `membership-audit.json` koppelen native oppervlaktesupport en bestaande Work B-labels. De statische vlag bewijst geen historische giftkalender.
- `endpoint-year-diagnostics.csv` markeert het afwijkende jaar 2024 zonder waarden te corrigeren of een oorzaak toe te kennen.
- `pilot-readiness.csv` is de actuele ontvangst-/pakketstatus. `pilot-hrus.csv` is de ongewijzigde historische selectie; het oude veld `real_reference_received` daarin is geen actuele ontvangststatus.
- `reference-response-year-screening.csv` rangschikt uitsluitend de natuursteekproefrespons. Weerklassen en fitrollen blijven onbepaald.
- `artifact-sha256.json`, `code-sha256.json`, `environment.json` en `tests.log` leggen afgeleide bytes, code en uitvoering vast.

De numerieke analyse kan zonder de oorspronkelijke ZIP opnieuw worden berekend uit Git:

```python
from pathlib import Path
import pandas as pd
from tools.analyze_et_pilot_reference import analyze
src = Path('docs/evidence/2026-10-21-et-real-reference')
out = Path('/nieuwe/diagnostiek'); out.mkdir()
analyze(pd.read_csv(src/'HRU21_reference.csv.gz', dtype=str, keep_default_na=False),
        pd.read_csv(src/'pilot-hrus.csv'),
        pd.read_csv(src/'selected-hru-support.csv'), out)
```

Voor volledige transportverificatie blijft de originele ZIP nodig, met SHA-256
`8634f3f86b38ce100705673d5d27db270569087d775901f7596025d606f9cd8f`.
De aanvullende native-inputaudit gebruikt de oorspronkelijke producentbestanden
met hashes uit `membership-audit.json`; deze zijn ongewijzigd teruggevonden in
het eerder geleverde `LWKM_MetaSWAP_HRU_Windows_x64_1.0.0.zip`.

Er zijn geen nieuwe modelruns uitgevoerd. Geen productie-admission of bewijs
van een betere HRU-specifieke parameterkeuze.
