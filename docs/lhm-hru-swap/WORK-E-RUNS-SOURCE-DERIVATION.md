# Work E: direct replacement for the v0.38 Runs writer

Authority: hrulist2SWAP.f90 v0.38, April 2026, recovered 2,099-line source.
This implements the parameter-table stage, not complete SWP generation.
No runtime XLS, SQLite or imported historical Runs values are used.

## All 37 legacy output fields

| Fields | v0.38 source and operation | New procedure |
|---|---|---|
| run_id | HRU list index, write block lines 1182–1247 | Explicit HRU identifier |
| scenario_id | Literal direct | Same |
| bodem_id | bfe grid mode, then bfe_repr override (1114) | bodem370/bodem_repr from HRU CSV |
| soil2_id | soil2 grid member mode, not overridden | Canonical classification of authoritative HRU soil |
| lu_id | lgn grid at selected svat_repr (1115) | HRU landgebruik22 if present, otherwise representative sample; diagnostic original source code |
| climate_id | Literal __ | Explicit config |
| SWBBCFILE, SWBOTB | bbc grid member mode; code 7 disables external BBC | Same, ambiguous modes fail |
| dqsat | dqsat grid mode within pre-override soil-mode subset | Matching authoritative HRU soil subset; explicit correction |
| BBCFIL, DRFIL, METFIL | HRU number, HRU number, HRU.met | Same |
| irrigation_id | irr_switch grid: binary majority then fraction >0.37 enables; source mode among irrigated members | Fraction >0.37; source mode, tied source modes fail |
| solute_id, rotation_id | Literal 0, max | Same |
| SWINCO | Literal 2 for both bottom branches | Same |
| GWLI | head at TimStart and glk grids; equal-member means, MIN(0,NINT((head_mean-glk_mean)*100)) | Same physical rule, Fortran half-away-from-zero rounding |
| RDS | rds grid conditional mode, then rz_repr/100 override; writer NINT(rds*100) | rz_repr in cm; optional explicitly selected representative_grid in metres |
| PONDMX | MaxPondDepth control *100 | Same |
| RSRO, tempBot | crunoff_par, tempCbotk control | Explicit config values |
| glk | glk grid equal-member mean | Same |
| area | Sum area grid, not full MODFLOW cell area | Same; separate from BBC surface convention |
| xc,yc,col,row | Member nearest equal-member coordinate centroid | Same coordinate rule; unresolved ties fail |
| nusvat | HRU membership count | Same, duplicate SVAT identity fails |
| TSTART,TEND | TimStart, TimEnd control | Explicit ISO dates in config |
| SWETR | lgn-mode-derived flag computed before representative override | Explicit four-class crop-policy table; stale flags not carried forward |
| soil_id | bodem2bofek_csv lookup | Standalone profile lookup joined to canonical soil classification |
| crop_id,croporg_id | lu2crop_csv lookup on soil2 mode and final lgn | Explicit soil2 × HRU lu4 lookup |
| dikte_id,COFANI,NUMNODNEW | Literals 1700,1,43 in writer | Same design constants |

No new scientific equivalence is claimed for corrected decisions. The old 204→205
profile treatment is not silently applied to authoritative HRU soil identity.
Hydraulic/profile binding remains subject to the existing renderer checks.

## Spatial input preparation

`python -m tools.swp_run_parameters` accepts either a sampled SVAT table, or the
membership table plus `--control` and `--base`. The latter reads exact paths from
the original control file for glk, area, dqsat, lgn, bfe, irr_switch, meteo, bbc,
and optionally rds. The initial head path is explicit `head_file` in config.
Every raster is sampled at the membership x/y coordinates, with its own extent.
Different crops are supported only when the same cell centres coincide.
Out-of-extent, non-centred and NoData cells fail; there is no interpolation.
ASCII corner/centre headers are supported; IDF uses the existing realized reader.
NumPy is needed for sampling (server 1.23.5 is sufficient).

Membership fields: svat, HRU, x, y. Already sampled tables additionally require
col,row,glk,head,area,dqsat,lgn,bfe,irr_switch,meteo,bbc and optionally rds.
HRU CSV requires HRU,svat_repr,bodem370,lu4; rz_repr is the primary root source.
The five-column representative schema alone lacks lu4, so must first be joined to
the complete HRU CSV by HRU, checking representative/soil agreement.

The provided `four_landuse_crop_candidate.csv` groups grass→1, maize→26/6,
arable→23, nature→22. This is an explicit candidate interpretation of the four
classes, not a claim that the legacy 22-code lookup did this. croporg_id=8 for
arable is a provisional generic-grain diagnostic choice and must not drive
management/root-depth decisions. The supplied soil/profile table combines P12
canonical classification with the independent bodem370_2_bofek2020 lookup sheet.
Unobserved/unclassified soil entries remain empty and cannot be used silently.

Config example (use actual paths and actual initial head date):

```json
{
  "start": "1970-01-01", "end": "2022-12-31", "climate_id": "__",
  "MaxPondDepth": 0.002, "crunoff_par": 0.25, "tempCbotk": 12,
  "head_file": "G:/actual/path/head_19700101_l1.idf"
}
```

Root-grid substitution requires adding `"root_policy":"representative_grid"`.
It is never enabled just because rz_repr is missing.

From Windows CMD in the repository root:

```cmd
E:\tools\deltaforge\deltaforge_4\python.exe -m tools.swp_run_parameters --hru HRU.csv --members HRU_MEMBERSHIP.csv.gz --soil config\swp\soil_classification_and_profile.csv --crop config\swp\four_landuse_crop_candidate.csv --config swp_config.json --control control_LHM433_HRU_SWAP_10242.inp --base G:\actual\project_root --output swp_parameters
```

From tools/native/swp use `run_parameters.cmd` with those same arguments; relative
arguments resolve against the repository root. Writes all 37 columns to
runs_candidate.csv, with diagnostics, per-HRU errors and input hashes. An
incomplete rerun removes any earlier success CSV. Failures return exit code 1.
No .swp files are generated by this stage.

## Validation and current limit

Targeted tests cover all 37 fields, unequal-area equal-member head aggregation,
root precedence, Fortran rounding, positive-head capping, soil subset rejection,
coordinate sampling, shifted cells and NoData rejection.

Real full-population identity audit: 4,224 grass, 1,035 maize, 2,158 arable,
2,825 nature. Four-class candidate crop selection differs from recovered Runs
in 255 HRUs. These are differences to investigate, not 255 proven old errors.
See docs/evidence/2026-10-29-swp-direct/four_class_audit.json.

Actual ASCII/head grids and the five-column representative root schema are not
present in the recovered local data. Consequently the spatial producer has only
fixture validation, and a real national 37-field parameter run has not occurred.
The next server action is running it against the original control-file sources,
then reviewing errors and differences before connecting the SWP renderer.
