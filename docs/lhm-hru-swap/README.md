# LHM → SVAT → HRU → SWAP

Deze map beschrijft de hydrologische LWKM-werkstroom vanaf het **eindproduct van een LHM-run** tot en met een gecontroleerd SWAP-uitvoerpakket. De volledige LHM-berekening valt buiten scope. De overdracht naar ANIMO valt eveneens buiten scope; het SWAP-handoffpakket is hier het eindpunt.

De documentatie maakt bewust onderscheid tussen twee lagen:

1. **As-is provenance**: voldoende reconstructie van de huidige LWKM 2.0 productielijn om bestaande bestanden, keuzes en hydrologische veranderingen te kunnen verklaren.
2. **Canonical workflow**: de voortaan voorgeschreven, reproduceerbare werkwijze. Deze hoeft historische omwegen en onderzoeksvarianten niet na te bootsen.

## Hoofdproducten

De canonical workflow kent zes inhoudelijke productgrenzen:

1. **LHM_EXPORT** — gecontroleerde export uit de LHM/NHI-omgeving.
2. **SVAT_BASE** — geharmoniseerde SVAT-dataset met bronwaarden en provenance.
3. **SVAT_QUALIFIED** — domeinselectie, expliciete correcties en kwaliteits-/gebruiksflags.
4. **SVAT_HRU_MAP + HRU_SCHEMA** — reproduceerbare HRU-afleiding voor de actuele HRU-methode.
5. **SWAP_INPUT** — volledig herleidbaar SWAP-invoerpakket per HRU.
6. **SWAP_OUTPUT_QA** — SWAP-resultaten met controles en formeel handoffpakket voor de volgende LWKM-stap.

Geen van deze producten overschrijft destructief zijn voorganger.

## Belangrijk ontwerpprincipe

De werkstroom is **lineair in data-afhankelijkheid, maar iteratief in ontwikkeling**.

Een onverwacht resultaat in SWAP mag leiden tot:
- een nieuwe diagnostische analyse;
- een nieuwe of aangepaste SVAT-kwalificatieregel;
- een nieuwe HRU-configuratie;
- een gewijzigde SWAP-mappingregel.

Maar zo'n bevinding wijzigt nooit stilzwijgend een bestaande run. Zij leidt tot een **nieuwe versie van configuratie + nieuwe run-id + nieuwe evidence**.

Daarmee blijven onderzoekscycli mogelijk zonder de productielijn onnavolgbaar te maken.

## Documenten

- [Workflow overview](workflow-overview.md)
- [Canonical workflow](canonical-workflow.md)
- [SVAT qualification specification](svat-qualification-spec.md)
- [Qualification and change control](qualification-and-change-control.md)
- [Data products and contracts](data-products.md)
- [As-is reconstruction status](as-is-reconstruction.md)
- [Hydrological effect decomposition](effect-decomposition.md)
- [Effect accounting and QA](effect-accounting.md)
- [Current HRU → SWAP mapping from HRUlist2SWAP v0.38](swap-mapping-current-v038.md)
- [Current SVAT source schema](../../schemas/svat/LWKM_makeHRU-v020.md)
- [Draft LHM4.3 export contract](../../manifests/lhm-export/lhm43-export-contract.yml)


- [Five-stage hydrological comparison](five-stage-hydrological-comparison.md)
- [Project-leader effect table specification](project-leader-effect-table-spec.md)
- [Effect accounting tooling](effect-accounting.md)
- [HRU10242 current production bindings](../../config/production/HRU10242-bindings.yml)
- [October-2025 SVAT qualification source reconstruction](../../config/svat-qualification/oct2025-source-reconstruction.yml)
- [HRU10242 QA configuration](../../config/qa/HRU10242-current.json)

## Scope van de huidige HRU-lijn

De actuele authority is de **HRU10242-lijn**. Oudere HRU-indelingen worden niet inhoudelijk gereconstrueerd tenzij een historisch bestand nodig is om de provenance van de actuele lijn te verklaren.


## Executable workflow checks

- `tools/check_control.py` validates operational control files against source-bound parameter schemas.
- `tools/qa_lhm_hru_swap.py` generates the first reproducible effect evidence for domain selection, correction diagnostics, qualification flags and HRU representation.
- `config/production/HRU10242-bindings.yml` is the current producer-consumer binding map.
- `config/effects/project-leader-stages.yml` is the machine-readable definition of the seven reporting stages.
