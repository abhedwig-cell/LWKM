# LHM server post-processing migration to Python — 30 September 2026

Status:
**PYTHON COMPATIBILITY CORE IMPLEMENTED; REAL-SERVER REGRESSION PENDING**

## Scope

The historical LHM-server workflow uses a mixture of:
- Windows batch files;
- `modflowidf2asc.exe`;
- `gridcalc.exe`;
- `grid_adjust.exe`;
- archival RAR commands.

The goal is not to replace MODFLOW or MetaSWAP. Python takes over the downstream orchestration and the simple deterministic raster calculations that create LWKM source/diagnostic ASCII grids.

## Main conclusion

Most of the active post-processing can be replaced by Python without a scientific-method change.

Good Python candidates:
1. discover and validate expected daily/period IDF files;
2. read supported Deltares IDF grids;
3. aggregate MODFLOW fluxes over arbitrary periods;
4. split positive and negative flux contributions;
5. convert full-cell MODFLOW volume flux [m3] to water depth [mm];
6. average state grids;
7. combine quarter/year/season grids;
8. calculate climate-period means;
9. perform linear raster algebra for river/drain/FLF/water-balance products;
10. write ESRI ASCII grids;
11. validate geometry, coverage and file completeness;
12. write provenance and hashes.

The batch layer can ultimately be reduced to, at most, one very small server launcher that activates Python and calls the pipeline.

## Historical semantics already bound

### MODFLOW cell support

The old Fortran water-balance code uses the complete 250 x 250 m MODFLOW cell:

`Acell = 62,500 m2`.

For flux items stored as m3/day, period water depth is:

`sum(Q_day) / 62,500 * 1000 = mm over period`.

This must not be replaced by MetaSWAP active area `uopp`.

### Positive / negative contributions

Historical `idf_modflow2wb` classifies the value at every time step:
- value < 0 -> negative bucket;
- value >= 0 -> positive bucket.

The sign split therefore occurs before temporal summation.

### State variables

State items are arithmetic time means for equal full MODFLOW cells.

### Grid geometry

The Python route deliberately refuses:
- implicit resampling;
- changed grid dimensions;
- changed cell size;
- silent NODATA arithmetic.

Any of these needs an explicit, separately qualified rule.

## Implemented compatibility core

New module:

`tools/lhm_postprocess.py`

It provides:

### IDF period aggregation

```text
python -m tools.lhm_postprocess idf-aggregate \
  --input "<pattern-or-file>" \
  --kind flux_m3_day \
  --stat period \
  --output output.asc
```

or state averaging:

```text
python -m tools.lhm_postprocess idf-aggregate \
  --input "<pattern-or-file>" \
  --kind state \
  --stat mean_day \
  --output output.asc
```

### Positive / negative split

```text
python -m tools.lhm_postprocess idf-sign-split \
  --input "<pattern-or-file>" \
  --positive-output pos.asc \
  --negative-output neg.asc
```

### ASCII sum / mean

```text
python -m tools.lhm_postprocess ascii-combine \
  --input q1.asc --input q2.asc --input q3.asc --input q4.asc \
  --output year.asc
```

Add `--mean` for arithmetic means.

Tests:
- MODFLOW m3 -> mm conversion;
- positive/negative daily sign buckets;
- state time averaging;
- ESRI ASCII round trip and combination;
- explicit failure on NODATA rather than silent corruption.

## Mapping from historical scripts

| Historical element | Python target |
| --- | --- |
| `do_modflow_waterbalans*.bat` | config-driven calls to `idf-aggregate` / `idf-sign-split` |
| `modflowidf2asc.exe` | `tools/lhm_postprocess.py` for admitted IDF variant |
| `do_idf2calc_year.bat` | period definitions + ASCII combine/mean |
| `do_gridcalc_klimaat*.bat` | generic year/season/climate aggregation |
| common `gridcalc.exe` sums/means | Python raster algebra |
| `do_modflow_sumrivdrndec.bat` | explicit named derived-product formulas |
| `do_rar*.bat` | optional archival utility, outside scientific pipeline |
| `do_modflow_GVG.bat` | separate Python migration after exact GVG rule qualification |

## What should not be migrated blindly

### 1. Full GridCalc mini-language

`gridcalc.f90` contains more than simple addition/averaging, including conditional expressions and historical left-to-right evaluation.

The new workflow does not need to recreate the entire generic mini-language before useful migration can start.

Only expressions actually required by admitted LWKM products should receive typed Python functions and regression tests.

### 2. GVG defect

The historical batch uses an unbound `%mm%` variable in its visible path.

A Python implementation should use explicit dates, but that is a defect correction, not a semantics-neutral translation. It needs its own oracle/regression.

### 3. Derived river/drain script defect

`do_modflow_sumrivdrndec.bat` consumes an intermediate whose visible producer command is commented out.

Python must not silently invent the missing historical intermediate and call it identical. The intended corrected formula can be implemented as a separate modern-authority product after qualification.

### 4. Unsupported IDF layouts

The repository IDF reader currently supports the realized fixed 52-byte header, float32 raster variant used in the audited P12 data.

Other IDF variants must fail explicitly until fixtures are available.

## Recommended target architecture

```text
authoritative LHM run tree
        |
        v
run-output qualification
        |
        v
Python postprocess plan
        |
        +-- MODFLOW daily IDF -> period/year/season ASC
        +-- MetaSWAP period products -> year/season/climate ASC
        +-- named derived water-balance formulas
        +-- QA / hashes / provenance
        |
        v
immutable LWKM source snapshot
```

Scientific formulas are named and versioned. File discovery and period iteration are orchestration, not embedded science.

## Migration sequence

### PYPOST01 — compatibility core

Status: **IMPLEMENTED, CI qualification pending/current**.

- IDF reader reuse;
- flux/state aggregation;
- sign split;
- ASCII algebra;
- strict geometry gates.

### PYPOST02 — small real-server golden regression

Run both historical and Python routes over a deliberately small period, preferably one year or one month with representative RIV/DRN/FLF/head products.

For every output compare:
- dimensions and extent;
- NODATA mask;
- minimum/maximum;
- sum/mean;
- cell-wise max absolute error;
- SHA-256 where formatting can be normalized.

Admission rule:
**zero unexplained numerical differences**.

### PYPOST03 — declarative orchestration

Replace repeated batch loops with one versioned plan containing:
- source root;
- period;
- item;
- layer;
- system;
- flux/state type;
- sign-split policy;
- unit conversion;
- output name;
- dependencies.

The plan should produce a dry-run manifest before calculating.

### PYPOST04 — derived products

Migrate only required GridCalc formulas individually with tests.

Historical defects become named compatibility or corrected modes; never silent fixes.

### PYPOST05 — server admission

Run the complete relevant LHM period, compare with accepted historical outputs and then retire the old Fortran/batch route from the active LWKM post-processing path.

## Expected practical advantages

Python removes a large amount of repeated batch logic and makes:
- periods configurable instead of hard-coded year lists;
- missing days/files fatal and visible;
- provenance easier to capture;
- selective reruns possible;
- tests possible without starting a complete LHM workflow;
- Linux/local verification possible for many steps;
- scientific formulas readable as named functions rather than temporary parameter files.

It also removes the need to maintain several near-identical batch files. In particular, the FLF, corrected-FLF and misnamed LAT extraction variants should become configuration, not separate programs.

## Input still needed from project owner

No owner input is needed to continue implementation.

For real-server admission later, access is needed to:
1. one small authoritative LHM output period;
2. the exact historical outputs produced from the same period;
3. confirmation of which final derived water-balance products are still operationally required.

The first two are regression evidence rather than design input.

## Decision

Proceed with Python as the target post-processing implementation.

Keep the old batch/Fortran route temporarily as a golden oracle until each migrated product is qualified.
