# W09 C++17 standalone aggregation checkpoint (2026-10-21)

A self-contained C++17 source package has been built locally as `lwkm_w09_native_source_v1.zip` (conversation artifact). Its rekenkern reads eight daily LHM ASCII grids (`RD1, EV24, TN, TX, Q, FG, WIND, WET_RAW`) plus the real fixed 277190 HRU-grid weight links. It outputs HRU daily MET-candidate CSV in canonical column order, applying spatial nearest-valid and rain-conditioned WET policy at meteogrid level.

Actual local Linux compilation succeeded. With eight synthetic 300x325 raster inputs for 2020-01-01 and the real weights table it wrote 10242 HRU-day values (plus header); sample rain=3 mm, wind=4 m/s, WET=.25 and ETref=2. A missing subsequent day fails closed. A one-day interval run completes.

**No Windows x64 executable was built**: there is no Windows cross-compiler in this environment. The provided `build_windows.cmd` requires MinGW-w64 on a build computer. There is no claim of NHI Windows execution or production admission. Source code and CMD are currently in the conversation ZIP and not yet committed into the Git repository.

Remaining before production: Windows x64 build and native test, actual file naming and unit metadata checks (particularly TN/TX/Q/FG), real raster date coverage and formats, SHA-256 input/output manifest, reliable resume and exact WET spatial compatibility, full-period benchmark and downstream SWAP-MET smoke. Do not confuse the resulting HRU-day CSV with complete SWAP `.met` output.