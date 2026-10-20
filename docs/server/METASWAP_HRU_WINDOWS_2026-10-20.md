# MetaSWAP to HRU: standalone Windows delivery

The compiled `tools/metaswap_hru/lwkm_metaswap_hru.exe` was executed natively on
Windows Server 2025. All 21 checks pass, including all 427,656 supplied original
SVATs and all 10,242 HRUs, the delivered CMD, and recovery after forced process
termination. This qualifies the executable and aggregation contract against
synthetic raster values; the actual 1970–2024 hydrological raster run remains
on the NHI server.

## Inputs and arithmetic

The project-owner supplied `area_svat(2).inp`,
`export_svat_HRU_NRU_10242(3).csv`, `metaswap_inventory.csv`, and the earlier
C++ package. Identities and population audit are in
`docs/evidence/2026-10-20-metaswap-windows/input-audit.json`.
The package retains complete original area/mapping bytes, renamed to stable
runtime filenames. Both original-SVAT keys and X/Y match without omissions.
The donor identifier is not substituted for the original spatial support.

Each original SVAT maps by X/Y into each IDF's own geometry, with explicit
bounds and cell-centre checks. Actual SVAT areas weight the HRU mean. Selected
SVATs sharing a raster cell remain separate weighted members. Current supplied
selection has 427,656 unique coordinates. HRU support is the selected SVAT
area, not the nominal 62,500 m² cell area.

The inventory binds 1,980 consecutive decade ends, 19700110–20241231, with nine
IDFs per period. Auxiliary area/partition files are excluded. The derived
`sources.csv` retains variable names and exact relative file paths, and is
included in runtime SHA-256 lineage. Each actual source raster is independently
hashed on the server; the inventory is not misrepresented as proof of those
unavailable raster bytes.

Project-owner units are m³/m² on each SVAT. The explicit temporal contract is
amount per decade. Factor 1,000 converts to mm/decade; no extra days multiplier
is applied. Raw signs remain intact. Derived signed components are
`Ebs + Epd`, `Eic + Esp`, and `Tact`. Total ET is their sum, irrigation is
`Pssw + Psgw`, and the comparison is `BDGETACT - total ET`. `Tpot` is retained
but is not included in actual ET. Group names explicitly identify ponding and
sprinkling evaporation. `Esp` is sprinkling evaporation, not snow sublimation.
Definitions and budget signs are documented by MetaSWAP Report 913.3 V8.1.1.4,
printed p.73, https://nhi.nu/documents/49/MetaSWAP_Report_913_3_V8.1.1.4.pdf.
This general documentation does not independently identify the unavailable
server series' temporal units or sign choices; the provided project contract
and visible comparison/QC remain distinct evidence.

Any missing selected SVAT value makes that HRU's corresponding original
variable blank. Coverage and completeness are explicit; denominators are never
renormalized to the nonmissing subset. Derived variables only require their
own input terms. Missing files and structural/geometry errors terminate with a
nonzero exit code. Per-variable NoData yields flagged CSV results and does not
by itself fail the process. Successful process completion is not complete data
coverage or production admission.

## Build, execution and dependencies

MinGW-w64 GCC 13.2.0 cross-compilation with `-O2 -static -static-libgcc
-static-libstdc++` produced a Windows PE32+ x64 console executable. The import
table contains only bcrypt.dll, KERNEL32.dll and msvcrt.dll, all Windows system
components. No Python, MinGW DLL, VC++ redistributable or other development
software is needed on the server. Python/NumPy are exclusively test/build
packaging dependencies. The compile command is in `build_cross.sh` and the
build evidence.

Local Wine was blocked by the runtime's socket restrictions. Native Windows
Actions run 39405686512 executed the exact shipped binary:
https://github.com/abhedwig-cell/LWKM/actions/runs/39405686512.
The PE SHA-256 is
`0606f5d15bc1c5bb01a1d0a91fd91c839c68daa0a6ae972fa7c79b0b451513b8`.
The smaller synthetic cases exercise weights, raster orientation, overlapping
members, leap decades, hashes, missing values, restarts and malformed IDFs.
The population case independently compares every HRU's original and derived
values to NumPy, using a lossless normalized extraction of the required
supplied input fields. It takes 3.031 s in the final native test; this is not a
measured production throughput. Its maximum CSV rounding error is about
5e-9 mm. The full original input files also pass the separate local input audit.
Native CMD execution uses a package directory containing spaces. Forced-kill
recovery and rejection of concurrent writers are explicitly exercised.

IDF support deliberately remains scoped to single-precision marker 1271,
equidistant grids, optional top/bottom fields, and the existing qualified text
footer. Other variants stop instead of being guessed. Headers and coordinate
alignment are checked independently for every raster.

## Operations and restart

Extract the ZIP contents directly into the user's LWKM_tools directory. Open
CMD there and run `run_metaswap_hru.cmd`. `%~dp0` binds package inputs and the
output path; the default source root is the project-owner's existing G: path.
An optional `LWKM_MSW_ROOT` environment variable overrides the source root
without source edits. Progress and errors are visible, and the script returns
the EXE's exit code.

Each decade commits a CSV, QC table and SHA-256 marker. Restart skips only when
code, configuration, both original SVAT input files, all nine raster sources,
and both output files match the recorded hashes. Corrupted or absent outputs
are repaired. A Windows exclusive delete-on-close lock prevents concurrent
writers and is released even after forced termination. An uncommitted partial
file is never treated as a result. Source files should remain immutable while
running; size/mtime checks catch ordinary mid-run mutations but do not create a
filesystem snapshot.

All 1,980 periods produce 20,279,160 HRU rows. The CSV header uses compact raw
variable names; units are defined uniformly as mm/decade. Coverage columns are
fractions, areas m², and `days` is the actual period length. Reserve 10 GB output
space as a practical allowance, not an exact forecast. Source raster reads and
SHA verification involve roughly 96 GB of source bytes each pass, and restart
checks still read the source files. No real-server elapsed-time claim is made.

## Reproduction and scope

`package_release.py ORIGINAL_INPUT_DIRECTORY OUTPUT_DIRECTORY` rebuilds the
single ZIP from the repository software/configuration/evidence plus the
original, SHA-bound supplied files. It checks the binary against the native
Windows test report and verifies every ZIP member against SHA256SUMS.txt.
Raw supplied input files stay in the existing file collection and release ZIP;
they are not added as separate 99 MB and 74 MB Git files. Git retains the
normalized complete selected test population and original source identities.

The release is an executable software delivery and candidate source-binding
route. It does not broaden other W00–W14 admission decisions, qualify unseen
actual raster values, or claim the genuine 1970–2024 processing has already
finished. Its next operation is the authorized server CMD invocation and
inspection of coverage, component signs and `BDGETACT_MINUS_ET`.
