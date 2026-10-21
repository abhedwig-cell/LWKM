# Lossless pilot transfer

The full CSV archive exceeds 1 GB. This read-only native selector exports the
frozen 21 pilot HRUs from every calendar decade, with combined and receiver
compatible per-decade tables. Defaults require all 1980 periods, 1970-2024.
It shares CSV, SHA256, identity and calendar helpers with the existing native
acceptor. It does not create a second SWAP generator or modify model inputs.

Local qualification includes synthetic leap-decade continuity, source corruption,
missing periods/HRUs, duplicates, coverage contradictions, existing destinations,
raw numeric text, missing-value propagation, hashes, and unchanged input bytes.
The actual supplied 20241210.csv (10242 HRUs) was checked against its archived
marker and all 21 selected rows compared field-for-field. See JSON timings and
source hash. The supplied support covers 427656 SVATs and 25514516032 m2;
this native support is preserved, not replaced with older Work B areas.

The Windows workflow builds with MSVC static runtime and executes the same
suite on native Windows, including the actual PowerShell ZIP wrapper. Linux
qualification is independent; Wine could not start in this runtime because its
server socket was prohibited. Release artifacts come from native Windows CI.

CSV and QC bytes are checked against existing markers, with repeated checks
against concurrent writes. Raster hashes are preserved as provenance, not
recomputed. Integrity is not source semantic admission, hydrological boundary
qualification, calibration, or evidence of independent validation. The entire
1970-2024 CSV population remains on the user's server; only one actual decade
was available here. Incomplete data can be exported losslessly and are explicitly
counted; downstream receipt and scientific gates remain mandatory.
