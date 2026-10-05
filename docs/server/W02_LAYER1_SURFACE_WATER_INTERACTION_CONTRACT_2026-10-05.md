# W02 layer-1 surface-water interaction contract — 2026-10-05

## Decision

Modern LWKM production semantics require that **all RIV and DRN groundwater interaction occurring in MODFLOW layer 1 is included** in the layer-1 surface-water interaction balance.

This is a production-authority decision. It is not limited by narrower historical post-processing selections.

## LHM433 package mapping

The supplied LHM433 control INI identifies the following relevant package systems.

### RIV in layer 1

Required:
- system 1: primary regional surface water;
- system 2: secondary regional surface water;
- system 3: tertiary regional surface water;
- system 4: main surface water H1.

Production set:

`RIV_L1 = {bdgriv_sys1_l1, bdgriv_sys2_l1, bdgriv_sys3_l1, bdgriv_sys4_l1}`.

### RIV in layer 2

Separate from the layer-1 interaction:
- system 5: H2, layer 2;
- system 6: W, layer 2.

These remain valid LHM output/provenance but must not be silently summed into a product whose semantic contract is **layer-1 interaction**.

### DRN in layer 1

Required:
- system 1: pipe drainage;
- system 2: simplified surface ditches / MVG;
- system 3: overland flow / OLF.

Production set:

`DRN_L1 = {bdgdrn_sys1_l1, bdgdrn_sys2_l1, bdgdrn_sys3_l1}`.

All three must be included.

## Layer-1 interaction equation

For each cell and time interval:

`Q_RIV_L1 = sum(RIV systems 1..4 in layer 1)`

`Q_DRN_L1 = sum(DRN systems 1..3 in layer 1)`

The combined layer-1 surface-water interaction is:

`Q_SW_L1 = Q_RIV_L1 + Q_DRN_L1`

subject to the qualified sign convention of the source terms.

Positive/negative splitting, if used, must occur according to the W02 mass/flux contract and must not change the complete-system membership.

## Historical/reconstructed script issue

The current reconstructed draft `05_modflow_make_decade_waterbalance_grids.bat` sums:
- DRN systems 1..3; and
- RIV systems 1..6.

That all-system RIV summation mixes layer-2 interaction into the derived net term.

For a layer-1 balance this is not production-authoritative.

Qualified finding:

`LEGACY_RECONSTRUCTED_ALL_RIV_SYSTEM_SUM_NOT_ADMISSIBLE_AS_LAYER1_INTERACTION`.

The script may remain useful as historical/source evidence, but the modern production implementation must use the explicit layer/system mapping above.

## W01 source implication

For the first 1970-2022 source-qualification tranche:

Required RIV layer-1 files:
- 4 systems x 19,358 dates = 77,432 files.

Required DRN layer-1 files:
- 3 systems x 19,358 dates = 58,074 files.

RIV systems 5-6:
- 38,716 layer-2 files;
- retain as separate provenance if needed;
- do not include in the layer-1 net source set.

With head L1, one FLF route and the currently preregistered 12 MetaSWAP core decade families, the revised first qualification tranche is:

- 197,118 files;
- 1,142,039,024,280 bytes, approximately 1.142 TB.

This size remains provisional until FLF ownership and exact consumer binding are closed.

## Testing requirements

W02 regression must explicitly test:

1. each of RIV systems 1, 2, 3 and 4 contributes when non-zero;
2. each of DRN systems 1, 2 and 3 contributes when non-zero;
3. no layer-2 RIV contribution enters the layer-1 interaction term;
4. system-wise sum equals aggregate layer-1 interaction cell-by-cell;
5. positive/negative split recombines exactly to the unsplit interaction;
6. temporal aggregation conserves the interval sum under the qualified units/sign convention.

A test that only validates the total without independently activating each system is insufficient because an omitted system can be masked by zeros in a chosen test period.

## Status

`LAYER1_RIV_DRN_MEMBERSHIP_CONTRACT_QUALIFIED`.

Still open:
- exact sign convention and unit contract;
- corrected versus uncorrected FLF ownership;
- golden regression against historical postprocessing;
- production implementation/admission.
