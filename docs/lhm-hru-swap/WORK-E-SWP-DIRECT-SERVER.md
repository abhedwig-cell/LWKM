# Direct SWP server candidate

One route now connects original control-file sources to HRU parameters and SWP:
`swp_direct_pipeline` → `swp_run_parameters` → `swp_direct_render`.
The renderer uses an independently exported lookup catalog; server runtime needs
Python and NumPy, neither XLS nor SQLite nor openpyxl.

## Windows CMD

Unpack LWKM_WorkE_SWP_Direct into the usual LWKM_tools directory. From the
unpacked directory containing start_swp_direct.cmd, first inventory the sources:

```cmd
start_swp_direct.cmd --control "FULL_PATH_TO_ORIGINAL_CONTROL.inp" --base "DIRECTORY_RELATIVE_PATHS_IN_CONTROL_REFER_TO" --hru data\hrus.csv --members data\membership.csv.gz --output swp_direct --inventory-only
```

Both quoted paths must be the real server paths, not these placeholders.
`--base` is the working directory from which the original Fortran control file's
relative paths resolve. Inventory writes swp_direct/source_inventory.json with
exact paths and missing files. It detects only exact start-date heads, with the
two original filename variants. If needed supply `--head "FULL_PATH_TO_HEAD.idf"`.
Use --start YYYY-MM-DD and --end YYYY-MM-DD to override the control period.
No closest-day head substitution is performed. An explicit --head remains an
operator-supplied date binding; verify its date against --start.

For production of candidate files, remove --inventory-only and supply the
original five-column representative schema:

```cmd
start_swp_direct.cmd --control "FULL_PATH_TO_ORIGINAL_CONTROL.inp" --base "DIRECTORY_RELATIVE_PATHS_IN_CONTROL_REFER_TO" --hru data\hrus.csv --members data\membership.csv.gz --representatives "FULL_PATH_TO_export_HRUschema_10242_copy.csv" --output swp_direct
```

This joins representative root depth by HRU and checks representative SVAT and
soil agreement. If the original representative schema cannot be recovered,
--root-from-grid explicitly selects the rootzone raster at the designated
representative SVAT instead. It is a separate source choice, never automatic.

The output has parameters/runs_candidate.csv, per-HRU diagnostics/errors, SWP
files under swp/ and a SWP output manifest. Repeated rendering reuses identical
files. This does not stage BBC/DRA/MET/CRP assets or execute SWAP on the server.
Candidate SWP files must be assembled with those files before model execution.

## What has actually been tested

- Complete fixture route: ASCII grids → member samples → 37 run fields → SWP.
- Repeated fixture run reuses the unchanged SWP.
- Four actual historical cases 7870,7871,7876,7929, with independent lookup
  catalog and newly rendered SWP, ran SWAP 4.3.1 from 1971-01-01 to 1971-12-20.
  All reached normal completion and finite daily output. Maximum independently
  reconstructed daily water-balance residual was 0.000204941 mm, below 0.001 mm.
- Those four replays intentionally use historical parameter snapshots only as
  renderer QA, not as input to the new server parameter production route.
- Crop dates remain unmodified, even beyond the simulation end date. Clipping
  CROPEND caused premature harvest and water-balance jumps in the first replay;
  this was corrected and regression-tested before the successful replay.

The full 10,242-HRU grid derivation has not been run on real server sources.
The four-class crop table is a candidate mapping, with 255 differences from
historical crop assignments. This remains open for scientific review. No national
SWAP production or hydrological admission is claimed.

The package contains the recovered complete HRU CSV (soil and lu4 authority) and
the qualified membership/coordinates. The five-column root schema, original
control and original physical grids must be read from the existing server data.
The running BBC09 production is independent of this package.
