# LHM / MetaSWAP / HRU area and unit contract

This contract is prerequisite to changing any historical weighting in P12.

## Distinct concepts

### 1. MODFLOW cell area
Typical LHM horizontal groundwater cell:
250 m x 250 m = 62,500 m2.

MODFLOW budget terms may be stored/reported as volumetric rates or volumes associated with this groundwater cell. Exact units must be bound per source file before conversion.

### 2. SVAT geometric area
A MetaSWAP SVAT can occupy only part of a MODFLOW cell. Its geometric area may therefore be smaller than 62,500 m2.

This area is not automatically the correct weight for every quantity.

### 3. SVAT flux intensity
MetaSWAP/SWAP-type vertical water fluxes are commonly represented as depth per time, equivalently volume per unit area per time.

A flux intensity must not be summed across SVATs without an area/representation contract.

### 4. Representation area
A SVAT calculation may represent a larger effective area than its literal polygon/fractional area when results are mapped/expanded to the parent groundwater cell or another aggregation domain.

Therefore:
geometric SVAT area != necessarily effective accounting area.

## Required typed quantities

Every P12 source variable must declare:
- source model/file;
- native unit;
- support domain: MODFLOW_CELL, SVAT_GEOMETRY, SVAT_REPRESENTATION, HRU;
- intensive vs extensive;
- time basis: instantaneous/rate/period-total;
- sign convention;
- conversion applied;
- target unit/support.

## Safe aggregation rules

No blanket area weighting.

For an intensive flux q [L/T] represented on areas A_i:
  HRU mean q = sum(q_i A_i) / sum(A_i)
only when A_i is the correct accounting/representation area.

For an extensive volumetric rate Q [L3/T]:
  HRU total Q = sum(Q_i)
and conversion to mean depth requires division by the target accounting area.

If a MODFLOW cell volume/rate is first distributed among SVATs, the distribution fractions must sum to one over the parent accounting domain before any later HRU aggregation.

## Audit implication

The historical expressions in hrulist2SWAP such as:
  qq += (h2-h1)/c1
  qq_hru = 100 * qq / nusvatwb
cannot be judged from unequal SVAT geometric areas alone.

First determine whether (h2-h1)/c1 is:
- a flux intensity already normalized to cell/SVAT area;
- a volumetric rate requiring area conversion;
- or a representative-cell quantity intentionally averaged equally.

Likewise qlat and MODFLOW budget terms require their own support/unit contracts.

## Mass-balance invariant

At each conversion boundary, preserve volume:
  source volume over accounting domain == sum(target represented volumes)
within numerical tolerance.

This invariant is stronger than reproducing a historical average formula.
