# LWKM-ARCH01 — ownership and timing authority

Status: **PROSPECTIVE BASELINE**
Scope: SWAP5 ⇄ ANIMO5 ⇄ WOFOST 8.1
Primary coupling interval under test: **1 day**

## Purpose

ARCH01 defines who owns each coupled quantity, when that quantity becomes authoritative, and which model may change it. It deliberately precedes implementation of the N-coupling.

A daily coupling interval is the initial hypothesis, not a permanently fixed design choice. It must be falsified if sub-daily exchange proves necessary for conservation or materially changes the coupled response.

## Ownership rule

A coupled variable has exactly one scientific owner at any instant. Other components may consume a snapshot or submit a demand/response, but they do not silently overwrite the owner's state.

The orchestrator owns sequencing, transactions, provenance and acceptance. It does not own soil-water physics, biogeochemistry or crop physiology.

## Prospective ownership matrix

| Quantity / process | Scientific owner | Producer | Consumer(s) | Initial authority |
|---|---|---|---|---|
| Soil water state | SWAP5 | SWAP5 | ANIMO5, WOFOST where required | SWAP accepted state |
| Water fluxes through soil boundaries/layers | SWAP5 | SWAP5 | ANIMO5 | SWAP accepted interval flux |
| Actual transpiration / water uptake | SWAP5, subject to WOFOST reconciliation | SWAP5 | WOFOST, ANIMO5 | OPEN |
| Potential transpiration / crop water demand | WOFOST/SWAP interface | WOFOST or SWAP forcing path | SWAP5 | OPEN |
| Root depth / root distribution | crop-growth authority with mapping contract | WOFOST 8.1 | SWAP5, ANIMO5 | OPEN |
| Soil mineral N state | ANIMO5 | ANIMO5 | WOFOST | ANIMO accepted state |
| N transformations and losses | ANIMO5 | ANIMO5 | LWKM accounting | ANIMO accepted interval |
| Crop N demand | WOFOST 8.1 | WOFOST | ANIMO5 | timing OPEN |
| Plant-available N | ANIMO5 for soil availability | ANIMO5 | WOFOST | OPEN definition |
| Actual crop N uptake | UNRESOLVED | coupled negotiation | ANIMO5, WOFOST | MUST BE RESOLVED |
| N-limitation / growth response | WOFOST 8.1 | WOFOST | SWAP5 indirectly | interface semantics open |
| Biomass, LAI, phenology | WOFOST 8.1 | WOFOST | SWAP5, ANIMO5 as required | WOFOST accepted state |
| Coupling schedule / transaction | LWKM | LWKM | all | LWKM |
| Retry / rollback decision | LWKM under component contracts | LWKM | all | LWKM |
| Scientific component state commit | respective component | component | LWKM | component contract |

## Demand, availability, uptake

ARCH01 forbids collapsing these into one variable:

1. crop N demand is a crop-model request;
2. soil N availability is an ANIMO-side statement about what can potentially be supplied;
3. actual N uptake is the conserved exchange flux represented consistently in ANIMO and WOFOST;
4. N stress/growth response is the WOFOST physiological consequence of realized N supply.

Current evidence does not yet justify assigning actual N uptake unilaterally to either ANIMO5 or WOFOST. NCOUPLE must resolve this with equations, units, timing and mass-balance tests.

## Candidate daily transaction

This is a preregistration target, not yet admitted behaviour.

At the start of day d, only states committed at the end of day d-1 are authoritative.

### A — bind start state

LWKM binds the committed SWAP5 hydrological state, ANIMO5 biogeochemical state, WOFOST crop state, external forcing and provenance. No component may consume another component's partially advanced day-d state as committed.

### B — establish crop and hydrological demands

A trial crop/hydrology exchange establishes crop structural state and water-demand quantities needed by SWAP5 for day d. Final call order remains open until the existing SWAP-WOFOST 8.1 contract is reconciled.

### C — hydrology trial

SWAP5 advances day d internally with its own sub-daily stepping and returns an accepted candidate interval containing the hydrological states and fluxes required by ANIMO5. A rejected SWAP trial does not advance coupled time.

### D — biogeochemical/N trial

ANIMO5 consumes only the qualified hydrological exchange for the same physical interval and evaluates N state, transformations, losses and potential supply/uptake constraints.

### E — crop N response

WOFOST receives the explicitly defined realized N exchange or supply constraint and computes N limitation and crop-growth response.

If that crop response materially changes the day-d hydrological demand used in phase C, a one-pass daily sequence is not self-consistent. NCOUPLE must test iteration, lagged coupling, predictor-corrector or another explicit policy rather than silently accepting circular dependence.

### F — coupled acceptance

Only after all participating components satisfy their acceptance contracts may LWKM commit the coupled day.

Commit must be atomic at coupling level. A failure after one component has advanced cannot leave mixed day-d/day-(d-1) authoritative states.

## Timing vocabulary

Every exchange field must eventually declare one of:

* START_STATE(d)
* INTERVAL_FORCING(d→d+1)
* TRIAL_RESPONSE(d→d+1)
* ACCEPTED_INTERVAL_FLUX(d→d+1)
* END_STATE(d+1)
* NEXT_INTERVAL_FORCING(d+1→d+2)

Labels such as "current", "daily value" or "available N" are not sufficient API semantics.

## Conservation contract

For every accepted interval, LWKM must reconstruct water exchanged across component boundaries without double counting internal SWAP fluxes.

For nitrogen, N removed from ANIMO soil stores as plant uptake must equal N credited to the crop through the coupled uptake exchange, except for explicitly declared transformations or numerical residuals. A stress factor is not a substitute for this conserved N exchange.

Rollback must restore both component state and coupling-ledger state.

## Fail-closed conditions

No production admission while any of these remain unresolved:

* actual N uptake has two owners or no owner;
* plant-available N lacks an executable definition;
* units, sign conventions or temporal support are implicit;
* WOFOST N response alters same-day water demand without explicit circular-coupling policy;
* one component can commit while another subsequently rejects;
* mass accounting cannot distinguish internal component fluxes from cross-model exchange;
* root representation differs without an explicit mapping;
* an exchange consumes trial state as committed state.

## Frozen by ARCH01

* component physics remains component-owned;
* LWKM owns orchestration, not scientific process equations;
* coupled state transitions are transactional;
* N demand, N availability, actual uptake and N stress are distinct;
* actual uptake is conserved explicitly;
* exchange fields carry temporal semantics;
* daily coupling is the first hypothesis to test;
* component-internal sub-daily stepping remains allowed and expected.

## Open authorities

1. exact SWAP5-WOFOST 8.1 water/crop ownership contract;
2. mathematical definition of ANIMO plant-available N;
3. authority and negotiation rule for actual N uptake;
4. root-profile mapping between WOFOST, SWAP5 and ANIMO5;
5. whether daily one-pass coupling is scientifically sufficient;
6. whether same-day N feedback requires iteration or can be lagged;
7. exact rollback capability exposed by ANIMO5 and WOFOST 8.1.

## Admission gate to LWKM-NCOUPLE

NCOUPLE implementation may start only after this authority package exists:

* N_demand definition and units;
* N_supply/availability definition and units;
* N_uptake_actual single-owner/negotiation rule;
* start/end/interval timing for each;
* crop-N mass ledger equation;
* root mapping rule;
* same-day versus next-day feedback rule;
* one minimal dry/N-limited oracle;
* one non-limited control oracle.

The next work unit is **LWKM-ARCH02 / N-AUTHORITY RECONCILIATION**: bind the existing SWAP5-WOFOST contract and ANIMO5 semantics to these open fields before writing the coupled implementation.
