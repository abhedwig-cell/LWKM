# Frank Fldrou mapping, definitief projecteigenaarbesluit 2026-11-06

Dit document vervangt de eerdere tussenstand waarin DRN2 nog buiten de vijf velden stond. **Alle zeven originele fysieke drainagestromen worden in vijf Frank-velden opgenomen.**

Bronvelden zijn positieve bruto drainagevolumes (m3 per volledige MODFLOW-cel over 1991–2020). Uit de bestaande v0.7-uitvoer:

- `Fldrou1 = RIV_SYS1_ONTWATERING + RIV_SYS4_ONTWATERING` (primair + H1).
- `Fldrou2 = RIV_SYS2_ONTWATERING` (secundair).
- `Fldrou3 = RIV_SYS3_ONTWATERING` (tertiair).
- `Fldrou4 = DRN_SYS1_ONTWATERING` (buisdrainage).
- `Fldrou5 = DRN_SYS2_ONTWATERING + DRN_SYS3_ONTWATERING` (maaiveldgreppels + overland flow).

`Ontwatering_totaal = Fldrou1+Fldrou2+Fldrou3+Fldrou4+Fldrou5`.

Vereist: behoud alle zeven oorspronkelijke fluxcomponenten en controleer algebraïsche sluiting van bronvolumes tegen Fldrou1..5 en het totaal. Zet pas na optellen om naar mm/jaar op basis van volledige MODFLOW-celoppervlakte `62500 m2` en 30 kalenderjaren: `1000/(62500*30)`. Dit zijn MODFLOW-cel-equivalenten, niet onafhankelijk per SVAT gemeten fluxen. Vermijd dubbeltelling als meerdere SVAT's binnen dezelfde MF-cel liggen.

`Fldrin1`, `Fldrin2` en `Fldrin345` vallen buiten dit besluit; alle afzonderlijke RIV-infiltratiestromen blijven beschikbaar en hun koppeling moet separaat worden bewaakt.

Deze commit is een versievaste **specificatiewijziging**; geen claim dat het huidige server-assemblagescript al is aangepast of op de NHI-server uitgevoerd.
