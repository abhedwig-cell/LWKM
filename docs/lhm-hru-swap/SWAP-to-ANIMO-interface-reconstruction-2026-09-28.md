# SWAP → ANIMO downstream interface reconstruction — 28 September 2026

Status: **INTERFACE CLASS BOUND; PRODUCTION ADAPTER OPEN**

A broad Library search did not recover the missing HRU10242 SWAP runner or production postprocessing scripts. Older LWKM process-register material explicitly records P13 SWAP execution and P14 postprocessing as not yet uploaded/documented, so their absence in the current reconstruction is consistent with the historical documentation rather than a search oversight.

## Downstream contract evidence

ANIMO documentation states that hydrology from SWAP is supplied as water balances/fluxes for the soil compartments used by ANIMO. The legacy interface includes `SWATRE.UNF` as water-quantity input from a model like SWAP.

Recent ANIMO5 architecture work independently classifies `SWAP.BUN`, `SWATRE.UNF`, `result.bun` and similar hydrology exchange files as specialized binary/unformatted runtime formats, not ordinary text configuration.

## Consequence for LWKM chain

The downstream chain must distinguish at least three separate products:

1. **SWAP native run output** per HRU;
2. **QA/postprocessing summaries** used for LHM↔SWAP comparison, plausibility checks, maps and acceptance;
3. **ANIMO hydrology exchange** containing time-dependent compartment water states/fluxes in the required binary/unformatted contract.

A CSV summary cannot substitute for item 3.

## Revised P13–P17 model

- P13: execute all accepted SWAP HRU cases and persist run status/logs/native output;
- P14a: extract canonical hydrological timeseries/compartment fluxes from SWAP output;
- P14b: derive QA summaries/maps from the same accepted extraction;
- P15: compare against LHM and qualify hydrology;
- P16: record acceptance of a named run/extraction version;
- P17: serialize the accepted hydrology into the ANIMO exchange adapter/format (legacy `SWATRE.UNF`/equivalent contract as applicable).

## Open authority

Still required from the historical production environment:

- SWAP batch/distributed runner;
- exact native SWAP outputs selected for extraction;
- extraction/postprocessing implementation;
- exact current LWKM/ANIMO binary hydrology writer and schema/version;
- failure/restart/completeness policy.

These gaps start after the now strongly bound HRU10242 → SWAP-input boundary.
