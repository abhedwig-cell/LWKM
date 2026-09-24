# Hydrological QA gates and knowledge rules

Status: **DRAFT AUTHORITY**

## Purpose

LWKM needs a formal hydrological quality gate between each major transformation step. Version control and provenance are necessary, but they are not sufficient: every candidate dataset/run must also be tested against explicit hydrological knowledge rules.

The gate has two functions:

1. detect values or combinations that are physically implausible or inconsistent with project expectations;
2. make deviations reproducible and reviewable rather than silently corrected.

A failed rule does **not** automatically imply that a result is wrong or must be replaced. It means the case must be shown, investigated and classified.

## Where QA occurs

The canonical workflow contains at least four distinct QA moments:

1. **SVAT_BASE QA**
   - checks the imported LHM/SVAT hydrology before downstream decisions;
2. **SVAT_QUALIFIED QA**
   - applies versioned plausibility/eligibility rules and records the affected SVATs;
3. **HRU QA**
   - checks whether the HRU representation remains hydrologically consistent with the qualified SVAT population;
4. **SWAP QA**
   - checks generated SWAP input and SWAP results against hydrological knowledge rules and against the upstream reference.

QA is therefore not a single final check. It is a sequence of gates.

## Knowledge-rule contract

Every hydrological rule must be represented as configuration/data, not hidden in ad-hoc analysis code.

Minimum fields:

- rule_id
- version
- description
- scientific rationale
- target product/stage
- target variable(s)
- exact expression
- units
- time support / period
- spatial domain
- land-use / soil / groundwater-class conditions
- exception areas
- severity
- expected action
- owner/reviewer
- source/evidence
- code/config commit
- status: EXPERIMENTAL / CANDIDATE / CANONICAL

## Rule outcomes

A rule produces one of three result classes:

- **PASS**: within accepted bounds;
- **FLAG**: outside accepted range, requires review;
- **NOT_EVALUABLE**: required input missing or semantics unresolved.

The default consequence of FLAG is **investigate**, not replace.

## Examples from current source reconstruction

The current batch logic already contains candidate rules for:

- very high upward seepage/kwel;
- very strong downward seepage/wegzijging;
- high runoff, differentiated by agriculture/non-agriculture;
- high sub-infiltration;
- upward seepage in a dry groundwater class;
- GHG above surface for agricultural land;
- older GT1/GT2 special-case rules.

These current rules are evidence for the knowledge base, but are not all automatically canonical. Some still require semantic normalization and review.

## New mandatory consistency checks

In addition to absolute plausibility thresholds, the workflow must test **cross-stage consistency**.

### Shared SVAT authority

The exact same qualified SVAT dataset must feed:
- HRU derivation;
- aggregated-HRU SWAP input;
- representative-SVAT SWAP input.

If the file/checksum/configuration differs between those consumers, the run fails the provenance gate.

### Correction consistency

For the Flevoland hydrological correction:
- corrected kwel cannot be accepted in isolation if associated drainage/ontwatering terms from the alternative LHM run also change materially;
- the correction mask and changed variables must be explicit;
- corrected and raw balance states must be compared one-to-one.

### HRU consistency

For every HRU:
- all member SVATs must refer to the same SVAT_QUALIFIED run;
- representative SVAT must exist in that same run;
- donor and representative relations must remain distinct;
- aggregation must not silently reintroduce excluded/uncorrected source values.

### SWAP input consistency

For every generated SWAP run:
- source run_id and HRU version must be recorded;
- every mapped input value must be traceable to the shared SVAT/HRU authority;
- generated input must be checked for thresholds and impossible combinations before simulation.

### SWAP output consistency

After simulation:
- numerical run status;
- mass/water balance;
- threshold rules on relevant fluxes/states;
- deviation against the upstream SVAT/HRU reference;
- spatial outlier detection;
- comparison against previous canonical run.

A flagged result is written to an exception table and never silently dropped.

## Exception register

Every QA run produces a machine-readable exception table with at least:

- run_id
- stage
- unit_type (SVAT/HRU/SWAP run)
- unit_id
- rule_id
- observed_value(s)
- threshold/expected range
- severity
- spatial location
- investigation_status
- explanation
- disposition
- linked issue/change id

This becomes the operational worklist for investigating strange results.

## Regression requirement

Every accepted change in:
- a knowledge rule;
- Flevoland correction;
- SVAT qualification;
- HRU derivation;
- SWAP mapping;

must be run against the previous canonical version.

Report at minimum:
- new flags;
- resolved flags;
- persistent flags;
- changed area;
- changed HRUs;
- hydrological deltas.

## Current authority risk for HRU10242

There is an unresolved risk that the SVAT hydrology used for the existing HRU10242 derivation may not be exactly the same hydrological state later used to build SWAP input.

In particular, it must be verified whether:
- the accepted Flevoland correction was already present in Piet's HRU input;
- any outlier/extreme-value corrections or exclusions were already embedded in that input;
- the SWAP input builder subsequently used the same version.

Until this is verified, the current HRU10242/SWAP chain is **not fully consistency-qualified**.

## Immediate action

Reconstruct the exact HRU10242 input dataset and compare its checksum/fields against:
1. raw SVAT state;
2. Flevoland-corrected state;
3. current qualified/outlier-treated state.

If needed, quantify the consequences by re-running HRU/SWAP or by a controlled retrospective comparison before declaring the current baseline consistent.
