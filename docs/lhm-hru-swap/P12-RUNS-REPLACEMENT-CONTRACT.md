# P12 Runs-record replacement contract

The historical Fortran writes a Runs CSV for Martin's downstream R/template procedure. The modern generator replaces this handoff with a typed run record.

## Field-by-field authority

run_id
  HRU id. DIRECT.

scenario_id
  historical constant/direct scenario token. CONFIG.

bodem_id
  legacy bfe_maj; modern = authoritative representative soil/profile from Piet schema. AUTHORITY.

soil2_id
  legacy member majority; modern = canonical lookup from authoritative representative bodem370. LOOKUP.

lu_id
  authoritative representative land use from Piet-selected representative SVAT. AUTHORITY.

climate_id
  template/config token; meteorological file producer remains independent. CONFIG.

SWBBCFILE / SWBOTB / SWINCO
  derived from BBC class/boundary mode. PRODUCER DERIVATION.

dqsat
  legacy pre-override BFE selection defect; modern value must bind to representative-soil semantics after oracle qualification. OPEN CORRECTED DERIVATION.

BBCFIL / DRFIL / METFIL
  references to separately generated producer outputs. FILE REFERENCE.

irrigation_id
  calibrated >0.37 source-member fraction, then majority type among irrigated members. INDEPENDENT AGGREGATE.

solute_id / rotation_id
  historical config/template fields. CONFIG unless later model requirements prove otherwise.

GWLI
  legacy initial groundwater level from equal-member mean head minus mean ground. LEGACY DERIVATION, scientific/support audit open.

RDS
  authoritative rz_repr from Piet schema, converted cm as renderer requires. AUTHORITY.

PONDMX / RSRO / tempBot
  control parameters MaxPondDepth, crunoff_par, tempCbotk. CONFIG.

glk
  legacy equal-member mean ground elevation. INDEPENDENT AGGREGATE, support audit open.

area
  sum uopp over HRU members. ACTIVE_SVAT_AREA SUM.

xc / yc / col / row
  legacy display anchor: arithmetic centroid of member centers snapped to nearest actual member. DISPLAY METADATA, not hydrological representative authority.

nusvat
  number of HRU source members. METADATA.

TSTART / TEND
  simulation config. CONFIG.

SWETR
  modern derive from authoritative representative land use. CORRECTED DERIVATION.

soil_id
  legacy bodem2bofek(bfe_maj). Modern must use canonical corrected soil lookup, not the divergent historical external table. LOOKUP.

crop_id / croporg_id
  lookup from representative soil2 + representative land use. LOOKUP.

dikte_id
  historical constant 1700. CONFIG until template semantics are reviewed.

COFANI
  historical constant 1.0 in Runs; DRA writes one 1.0 per horizon. CONFIG.

NUMNODNEW
  historical constant 43. CONFIG; should not remain magic number without template/schema definition.

## Modern typed record groups

IDENTITY:
  run_id, scenario

REPRESENTATION:
  bodem/profile, soil2, landuse, root depth, SWETR, crop

BOUNDARY:
  BBC mode/file, dqsat, GWLI

FORCING:
  MET file

DRAINAGE:
  DRA file

IRRIGATION:
  irrigation id

GEOMETRY/METADATA:
  uopp total, display anchor, member count

SIMULATION CONFIG:
  dates, ponding/runoff/bottom-temperature, numerical/template constants

## Renderer rule

The direct SWP renderer consumes this typed record plus typed referenced producer records.
It must not:
- perform HRU majorities;
- derive soil classes;
- derive land-use flags;
- regenerate BBC/DRA/MET;
- modify unrelated inputs.

This is the contract that replaces the R {{}} substitution layer.
