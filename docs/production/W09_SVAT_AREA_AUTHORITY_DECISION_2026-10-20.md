# LWKM W09 projecteigenaarbesluit: actuele SVAT-oppervlakten

Datum: 2026-10-20
Status: vastgesteld bronautoriteitsbesluit voor meteorologische HRU-weging.

De projecteigenaar bevestigt uitdrukkelijk dat **`area_svat(3).inp` de correcte oppervlakteversie** is voor de actuele SVAT-naar-HRU meteorologische weging. Deze versie is leidend boven de oudere, afwijkende Work B-referentie bij de constructie van W09 meteogridgewichten.

## Bronnen en bestaand bewijs
- `area_svat(3).inp` SHA-256: `352f2d0210c7a6b653f29469a90a2e4ec3ea4d216b06c33ed2bf1d8faa2192cc`.
- `export_svat_HRU_NRU_10242(4).csv` SHA-256: `13f4f129957e24ce6f9380dc4e72cc9bdada59620dc4a0a5464bf6e8b319f7f4`.
- Rastertemplate `precipitation_19700101.asc`, SHA-256: `bbf423df8513b3b46779c96bad12f850fa6f7b0df0f9f5d99c1a5fd92dc3375e`.
- Gegenereerde gewichtentabel `hru_meteogrid_weights.csv`, SHA-256: `6133a918a0a05bd4b1b384fc88a1d13df7bd49d26c1723b242b319a667712f7c`.
- 427656 SVATs, 10242 HRUs, 277190 HRU-gridcombinaties; gewichtsommen binnen numerieke tolerantie.

De geselecteerde oppervlakte uit `area_svat(3).inp` is 25.514.516.032 m². De eerder vastgelegde Work B-oppervlakte is 25.511.141.709 m². Het verschil van 3.374.323 m² is een **bekend bronversieverschil**, en blokkeert W09 niet langer op het punt van autoriteitskeuze. De historische oorsprong van het verschil wordt hiermee niet bewezen; behoud beide cijfers en provenance voor audit.

## Effect
- Gebruik de nieuwe oppervlaktebron bij de vaste HRU-per-meteogrid-gewichten.
- Herbereken de oppervlaktefracties niet dagelijks.
- Registreer upstream-bestandsidentiteiten, bronversie en de bewuste afwijking van Work B.
- Het eerdere label `CANDIDATE_PENDING_AREA_PROVENANCE_RECONCILIATION` kan worden vervangen door `OWNER_AREA_AUTHORITY_CONFIRMED_PENDING_INTEGRATED_MET_QA` voor deze gewichtentabel, mits de hashes en de vastgelegde numerieke tests opnieuw worden gecontroleerd.
- Dit besluit verklaart niet automatisch de volledige meteorologische productieketen of SWAP-MET-uitvoer production-admitted.
