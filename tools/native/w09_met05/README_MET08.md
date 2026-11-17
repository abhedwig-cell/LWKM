# MET08: primary MET producer source correction

17 November 2026. This changes the original C++ producer, not the running MET07 HUM-only repair.

The delivered MET06 producer used the fifth zero-based input field FG as HUM. The primary source is now explicitly HUM, bound to prepared LHM `UG/UG_{date}.asc`, actual vapour pressure, kPa, scale 1. WIND retains its separate existing source. Raw KNMI relative humidity is not accepted. Existing `path_FG` or `scale_FG` keys are rejected, including configurations that also contain the new keys. Duplicate configuration keys fail. Missing metadata, wrong quantity/unit, rescaling and non-UG paths are refused before output creation.

Both `tools/native/w09_met05/src/w09_direct_met.cpp` (direct MET) and `tools/native/w09/w09.cpp` (older CSV route) share `tools/native/w09_common/hum_source_contract.hpp`. All original valid HUM raster values must be finite and in 0..10 kPa before any nearest-valid filling; all-NoData fails. HRU aggregates are checked again. Neither clipping nor weight renormalization is introduced. The original donor tie rule and non-HUM calculations/serialization remain unchanged. The direct producer records its version and explicit HUM source contract in MANIFEST.txt. Manifest line endings are corrected, not MET formatting.

The example configurations now use UG and separate MET08 output names. Build both producers with C++17, without fast-math (GCC `-ffp-contract=off`, MSVC `/fp:strict`). The existing Windows build workflow has been updated to build and test both executables and publish an identifiable MET08 artifact. A workflow definition is not proof of a completed Windows build; consult its actual run result.

Run the compiled-binary tests:

```text
python tools/native/w09_met05/tests/test_hum_contract.py DIRECT_EXE LEGACY_CSV_EXE
```

35 local tests passed with compiled Linux GCC binaries. These exercise 10242 synthetic HRUs, sparse IDs, distinct wind/humidity, unit/source/legacy guards, range bounds, NoData donors, existing outputs, and the legacy CSV route. The compact fixture contains true HRU-1 member values and unchanged weights extracted from two complete uploaded rasters; its replay geometry and other weather variables are synthetic. Separately, the complete received FG/UG/WIND rasters were replayed locally with the original and fixed compiled producers. On 1970-01-01 HUM changes 3.600000 -> 0.263000; on 1970-02-20 it changes 10.300000 -> 0.724000. Every other serialized weather token matches the original in those replays. The other five source families in that comparison were synthetic. No new SWAP run or full-period native producer run is claimed.

Evidence and scope: `MET_HUM_BRONBEWIJS.zip` SHA256 1fc6ac9edfc95f5ebd54de1434d95a29c4c4b7a3010f6a1fbb24419cb9915507; original direct C++ blob dff2def188f53a0cf50dbcbdb9b2f90c86cc9053; original CSV C++ blob 15dbf31ef4e6fb22c177e6b977d1fed5082249a3. These source identities were checked before editing. The source contract follows the diagnosis and six successful MET07 full-period SWAP trials documented under PR #27. Those trials used the HUM-only repair, not this newly rebuilt C++ producer. The six full corrected-MET hashes remain a server-side full-period qualification target; they have not been independently reproduced here.

Deployment is separate. Do not replace an executable or configuration underneath a running process. The current national MET07 correction continues unchanged and does not call these native producers. Existing MET06 executables and historical ZIPs are not retroactively changed by a Git commit. Use the corrected source/configuration pair for future builds, deploy a separately identified MET08 executable, and keep old output as historical evidence. Do not start another national production now just to install the source correction. No water-balance investigation, SWP/DRA/BBC changes, main merge, or production admission is implied.
