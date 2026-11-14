# W09: native meteorological HRU aggregation

C++17, one standalone Windows x64 EXE (MSVC /MT). No Python or Internet on NHI server.

**Verified:** GitHub Actions W09 Windows x64 run 39566162383 (success), 10242-HRU synthetic day smoke. Canonical unit tests also succeeded for head 2dba1ff1a9356aa57151fce2ee02be02239f099c. The Windows binary is published as the workflow artifact `lwkm-w09-native-windows-x64`; obtain it from https://github.com/abhedwig-cell/LWKM/actions/runs/39566162383.

Copy the binary alongside `run_all.cmd` and `w09_config.ini`, and provide the owner-approved `hru_meteogrid_weights.csv` plus the LHM ASCII template. Check and adapt all `path_*` entries and **verify all units/scales** before running on NHI.

The application produces yearly **HRU daily candidate tables**, not final SWAP MET files. Production admission remains blocked pending original LHM variable naming/units, actual raster availability, SHA-256 of every consumed input, resumability and complete 1970-2022 execution. No full NHI production run is claimed. Future refinements should avoid invalidating completed unchanged years and should verify output hashes.

For the corrected precipitation-duration rule, WET is first determined per meteogrid cell and then area-weighted; rain=0 => 0, rain>0 with usable raw duration => raw value, otherwise 0.1. This is a comparison/aggregation convention; downstream SWAP-MET preflight must still be applied and investigate any HRU-level rain/WET inconsistency.
