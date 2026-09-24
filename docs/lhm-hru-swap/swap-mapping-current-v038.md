# Current HRU → SWAP mapping in HRUlist2SWAP v0.38

Status: **SOURCE-BOUND RECONSTRUCTION, NOT YET CANONICAL**  
Inspected source: `hrulist2SWAP.f90`, program version 0.38 (April 2026).

Purpose: make the scientific mapping from HRU/SVAT information to SWAP input explicit before it is redesigned as a versioned `SWAP_MAPPING` contract.

## 1. Inputs that define HRU membership and representation

The program distinguishes several relations that must stay distinct in the canonical workflow:

- `HRU2svat`: membership of SVATs in HRUs;
- `HRU2HRU_csv`: optional remapping of HRU IDs;
- `HRU2SVAT_repr_csv`: one representative SVAT plus representative root-zone/bodem information per HRU;
- `verdacht_asc`: a spatial mask that later controls which SVATs participate in some water-balance/boundary calculations;
- per-SVAT grids for land use, soil, bottom-boundary class, meteorological district, area, groundwater level, resistance and other properties.

The representative-SVAT relation is therefore not the same object as HRU membership or the water-balance selection.

## 2. Run-table mapping

The program writes a run table with these fields:

`run_id, scenario_id, bodem_id, soil2_id, lu_id, climate_id, SWBBCFILE, SWBOTB, dqsat, BBCFIL, DRFIL, METFIL, irrigation_id, solute_id, rotation_id, SWINCO, GWLI, RDS, PONDMX, RSRO, tempBot, glk, area, xc, yc, col, row, nusvat, TSTART, TEND, SWETR, soil_id, crop_id, croporg_id, dikte_id, COFANI, NUMNODNEW`.

The current source derives them as follows.

| SWAP/run field | Current v0.38 rule | Population / source | Canonical action |
|---|---|---|---|
| `run_id` | HRU sequence number | HRU | keep, but bind to stable HRU version |
| `scenario_id` | literal `direct` | code constant | move to configuration |
| `bodem_id` | initially majority BOFEK/BFE; when representative file exists, overwritten by `bfe_repr` | all HRU members, then representative schema | make representation rule explicit |
| `soil2_id` | majority `soil2` | all HRU members | explicit aggregation |
| `lu_id` | initially majority LGN; when representative file exists, overwritten with LGN of `svat_repr` | all members, then representative SVAT | explicit representation rule |
| `climate_id` | literal placeholder `__` | code constant | define or remove |
| `SWBBCFILE` | 0 when majority bottom-boundary class = 7, otherwise 1 | all members | document semantic class mapping |
| `SWBOTB` | majority bottom-boundary class | all members | explicit majority rule |
| `dqsat` | majority-like real value among members whose BFE equals selected `bfe_maj` | conditional subset | make rule + fallback explicit |
| `BBCFIL` | HRU number | generated file | retain as generated relation |
| `DRFIL` | HRU number | generated file | retain as generated relation |
| `METFIL` | generated HRU meteo filename | generated file | retain |
| `irrigation_id` | majority irrigation switch; forced active when fraction with irrigation > 0.37, then majority among positive switches | all members | **review threshold and semantics** |
| `solute_id` | literal 0 | code constant | move to configuration |
| `rotation_id` | literal `max` | code constant | move to configuration |
| `SWINCO` | set to 2 | code | move to configuration |
| `GWLI` | `MIN(0, round((hh_avg - glk_avg)*100))` | averages over all members | verify sign/reference semantics |
| `RDS` | root depth ×100; if representative schema exists, `rz_repr` ultimately controls value | representative schema when available | make authoritative source explicit |
| `PONDMX` | `MaxPondDepth * 100` | control parameter | configuration |
| `RSRO` | `crunoff_par` | control parameter | configuration |
| `tempBot` | `tempCbotk` | control parameter | configuration |
| `glk` | arithmetic mean | all HRU members | explicit aggregation |
| `area` | sum of member areas, implemented as average × count | all HRU members | explicit sum |
| `xc,yc,col,row` | arithmetic centroid is calculated, then replaced by coordinates/index of the member cell nearest that centroid | all HRU members | rename as geographic representative location |
| `nusvat` | number of HRU members | all members | retain |
| `TSTART,TEND` | control dates | configuration | retain |
| `SWETR` | 0 when initial majority LGN < 7, else 1 | majority LGN before later representative override | **potential inconsistency: not recomputed after representative LGN override** |
| `soil_id` | lookup `bodem2bofek(bfe_maj)` | selected BFE | explicit lookup version |
| `crop_id` | lookup `lu2crop(soil2_maj,lgn_maj)` | aggregated/representative classes | explicit lookup version |
| `croporg_id` | lookup `lu2croporg(soil2_maj,lgn_maj)` | aggregated/representative classes | explicit lookup version |
| `dikte_id` | literal 1700 | code constant | move to configuration |
| `COFANI` | literal 1.0 | code constant | move to configuration |
| `NUMNODNEW` | literal 43 | code constant | move to configuration |

## 3. Representative SVAT semantics

When `HRU2SVAT_repr_csv` exists, the program reads:

- HRU id;
- `svat_repr`;
- `rz_repr`;
- `bfe_repr`;
- `bodem_repr`.

Later it overrides at least:

- `bfe_maj ← bfe_repr`;
- `lgn_maj ← LGN(svat_repr)`;
- `rds_maj ← rz_repr / 100`.

This is scientific representation logic and must become part of the versioned mapping specification, not remain an implicit side effect of file existence.

## 4. Water-balance / usable-SVAT selection

The source uses the confusing pair `isverdacht` and `issvatwb`.

Two different mechanisms appear:

1. after reading HRU membership/donor information, `svat != svatdonor` temporarily sets `isverdacht = TRUE`;
2. later the program reads the grid supplied through `verdacht_asc` and **overwrites** that state:
   - grid value > 0 → `isverdacht = FALSE`;
   - otherwise → `isverdacht = TRUE`.

The HRU array then receives:

`issvatwb = isverdacht`.

This is semantically dangerous because the variable names do not transparently express "use" versus "exclude". The canonical workflow must replace this with an explicit boolean such as `use_for_swap_water_boundary`.

If an HRU ends with zero `issvatwb` members, v0.38 falls back to **all HRU members** and flags the HRU internally as a problem. That fallback must be explicit in canonical configuration and QA.

## 5. Bottom boundary construction

For each timestep the current source reads:

- MODFLOW head layer 1;
- MODFLOW head layer 2;
- `bdgflf` layer 1;
- optional `bdgqlat` layer 1.

For members selected by `issvatwb` it computes, among other diagnostics:

- mean layer-1 head;
- weighted layer-2 minus layer-1 head difference;
- `qq = Σ((head_l2 - head_l1) / c1)`;
- FLF and QLAT aggregates.

The active SWAP `.bbc` file writes `SWBOTB=2` and uses **only `qq`** as `QBOT2` in the inspected code. Alternative lines using FLF or FLF+QLAT are commented.

A second `.bbch` file is generated for `SWBOTB=3`, using:

- `RIMLAY = c1_avg`;
- an aquifer head derived from layer-1 head, weighted head difference and mean surface level.

Canonical mapping must therefore distinguish "computed diagnostic" from "actually written to active SWAP input".

## 6. Meteorological mapping

Precipitation and evaporation grids are processed per timestep.

For each HRU:

- only `issvatwb` members are included;
- values are area-weighted;
- denominator is the selected-member area `areawb_sum`.

Other meteorological variables are read from the majority meteorological district.

This is a hybrid mapping and must be represented explicitly.

## 7. Drainage mapping

The current source comments state that drainage properties should use the water-balance selection, but in the inspected block the `issvatwb` conditions are commented out and `nutp` is reset to the total number of HRU members.

Therefore the active v0.38 code derives major drainage aggregates from **all HRU members**, not only the water-boundary subset.

This difference is hydrologically relevant and must become an explicit mapping choice rather than remain an accidental code detail.

## 8. Known source-level issues to resolve before canonical admission

1. `SWETR` is calculated from majority LGN before `lgn_maj` may be overwritten by the representative SVAT.
2. Irrigation comment and active threshold differ: the active fraction threshold is 0.37.
3. The semantic polarity of `verdacht_asc → isverdacht → issvatwb` is difficult to interpret and should be replaced with positively named usage flags.
4. Drainage comments say selected members, but active code uses all members.
5. Several constants are embedded in source instead of configuration.
6. FLF and QLAT are calculated in the bottom-boundary block but are not used in the active `QBOT2` write line.
7. The exact production executable must be bound to this source commit/version before treating this mapping as production authority.

## 9. Target canonical decomposition

The replacement `SWAP_MAPPING` should have one record per SWAP input quantity:

| target | source product | source field | member policy | aggregation | representation | conversion | fallback | config version |
|---|---|---|---|---|---|---|---|---|

This will make it possible to change one mapping rule, rerun downstream steps, and quantify exactly what changed.
