# LWKM W11 server-side SWAP package builder

Windows x64 **self-contained .NET 8 single-file EXE** compiled on Windows Actions. No Python, installed .NET, Internet, or compiler required on NHI server.

Input `catalogue.json` (schema_version=1, profile_id, start/end, expected_population, runs array with hru_id and named assets). Each asset requires path, sha256, logical_id, qualification_status and semantic_contract. The builder copies existing SWP, DRA, BBC, MET, CRP and other declared model assets. It does **not** derive scientific SWAP parameters, regenerate datasets, run SWAP, or automatically grant scientific admission.

Use `run_packages.cmd` with qualified inputs on NHI. Catalogue paths are relative to catalogue.json or absolute. Required per-run assets include swap.swp and at least one .dra, .bbc and .met. Additional files required by SWP must be explicitly present in the catalogue; full SWAP parser/preflight remains a **separate local admission gate**. Unknown extra assets are not inferred. The output includes one manifest.json per run and build-status.json with any blocked HRUs. The build checks each source SHA256 before use, copies into temporary same-volume folder, checks copied hashes, atomically publishes run_00001, and verifies all cached bytes before reuse.

The catalogue allows a subset of expected_population; missing HRUs should be explicitly registered as upstream blockers. By default non-PRODUCTION_ADMITTED sources are rejected. `--allow-research-inputs` is for explicitly controlled research use only, never scientific admission.

Important remaining gates: bind actual daily MET/BBC input products and all SWP referenced assets, Windows build and adversarial tests, final package semantic preflight, verified catalogue coverage of 10242 HRUs, 29 C2 drainage exemptions, on-server run and end-to-end SWAP smoke. Never treat an assembled directory as a qualified SWAP model without those gates.
