# Returned NHI source inventory accepted: location evidence

Input: swp_broninventarisatie.zip, supplied by the project owner on 2026-10-29.
The archive is processed by tools/accept_swp_source_inventory.py, producing
config/swp/server_locations_20261029.json. No server source is moved or renamed.

Observed: all ten originally classified source roles have one existing physical
file. Three additional roles are bound from the complete references: irrigation,
dqsat_svat, and luse_svat; together with the actual start-date head this gives
13 distinct logical source bindings (the model steady-state setup head is not
used as the dynamic start-date head). The raw report has 4,975 references.

Current INI discovery found zero files in its bounded search. Eight previously
uploaded control files still provide traceable configured references whose
physical files exist on the server. Do not misreport these as rediscovered INIs.

Confirmed static source folder:
E:\LHM_4.3.3\Data\2_Model_Input\metaswap\grid

Confirmed files include UOPP.ASC, ahn_f250_cm.asc, lgn250.asc, bodem.asc,
rootzone.asc, metestat.asc and beregen.asc. MODFLOW drainage and activity IDFs
and MetaSWAP input tables are referenced separately at their actual locations.

The dynamic initial head is:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\modflow\head\head_19700101000000_l1.idf

Both initial-head meanings remain distinct: HEAD_STEADY-STATE_l1.idf is the model
setup input; the dated daily result is the candidate for the historical SWP start.

## Remaining data check

The inventory checks paths and metadata, not geometry, raw values or units.
In particular ahn_f250_cm.asc and rootzone.asc must not be passed to the old
meter-based adapter without explicit unit handling. dqsat_svat.inp is available;
there is no reason to invent a local dqsat grid or move it into BasicData.

The package LWKM_WorkE_SWP_Broncontrole.zip reads the confirmed locations and
samples all 427,656 qualified SVAT coordinates. It records grid headers, exact
cell-centre coverage, NoData counts, raw-value ranges, and hashes of grid files.
UOPP is compared with the existing qualified SVAT area. Two groundwater-depth
unit hypotheses are reported without choosing or applying a conversion.
Small previews of the dqsat/luse input tables expose their actual format.
This is real data inspection, not a repeat of directory inventory.

Unpack under LWKM_tools and open CMD in the directory containing the starter:

```cmd
controleer_swp_bronnen.cmd
```

It uses the established Python and NumPy installation. No path arguments.
It prints progress for each source and returns swp_broncontrole.zip. Only the
small report needs to be returned; source grids are read in place. No models
run and existing BBC outputs are untouched.

Metadata existence alone does not qualify a source's physical meaning. The
next producer change must explicitly consume confirmed server sources with
verified units, representative HRU authority and the four-class policy.
