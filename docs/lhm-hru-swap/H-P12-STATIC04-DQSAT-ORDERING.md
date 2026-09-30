# H-P12-STATIC04 — dqsat representative-soil ordering defect

## Finding

Legacy source:
1. computes bfe_maj as member-raster majority;
2. selects dqsat values only from members with bfe == that majority;
3. sets dqsat_maj = MAJORITYR4(selected dqsat);
4. later, when Piet HRU schema exists, overrides bfe_maj = bfe_repr;
5. does not recompute dqsat_maj.

Thus final HRU can combine:
- representative BFE/profile from Piet;
- dqsat derived from a different legacy majority-BFE population.

## Downstream impact

dqsat_maj is:
- written to the Runs/SWP intermediate as field dqsat;
- used in DRA as L = 4*dqsat_maj whenever system length > 0.

Therefore mismatch can affect both static SWP input and drainage geometry.

## Classification

DEFECT_CONFIRMED_AUTHORITY_ORDERING at supplied-source level.

Realized executable impact remains to be tested.

## Correct schema-first semantics

Resolve representative soil/BFE first.
Then derive dqsat from the authoritative representative soil/SVAT contract.

Open scientific detail:
- whether dqsat should be taken directly from representative_svat;
- or from a deterministic soil lookup / representative-soil population.

Do not decide this by legacy member majority. Bind from upstream HRU/soil semantics and realized output.

## Oracle

The supplied dqsat raster and realized DRA L values provide a direct test:
  where L != 100, realized dqsat_used = L/4.
Compare that value against:
A. legacy majority-BFE dqsat_maj;
B. representative-soil/SVAT dqsat candidate.

This can identify executable behavior independently of the Runs CSV.
