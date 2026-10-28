# W07 DRA closure audit — 2026-10-27

## Owner target
One offline Windows CMD/EXE on NHI, consuming original LHM sources, creating a uniquely identified SWAP method-3 DRA for every HRU 1..10242 including the 29 difficult cases; no Python on server, no separately precomputed renderer catalogue.

## Verified code/evidence
- PR #19: W07 five-level diagnostics for all 29 original blockers, plus full-record protected partition/merge and `tools/w07_build_29_dra.py` that needs full C2 checkpoints. The reduced 29 diagnostics do **not** include complete H1 month, DEP and DD and are insufficient for final DRA bytes.
- PR #20: native Windows .NET self-contained build, method-3 renderer, direct raw IDF reader, SVAT-to-HRU seven-source aggregation, automatic partition fitting for >5 active sources, SWP horizon extraction, monthly H1 stage input and status register. These exist in current native branch code and passed synthetic smoke at least. Earlier production-contract prose saying *not implemented* is older than the current native code: reconcile documentation against exact branch head, do not let obsolete status override code.
- Existing 10,213 C2 DRA files are described as qualified in historical handoff, but their exact hashes/bytes and availability as a deployable NHI bundle have **not** been checked in this review.
- No evidence presently seen for actual **29/29** real-source DRA serialization or actual **10242/10242** server product. Tests in PR #20 use a one-HRU artificial fixture with deliberately incomplete population.

## Material gaps identified by source review
- `RawDrainage.Inspect` returns a diagnostic note expressly saying RIV completeness rules and seasonal bottom handling are not yet applied. Its simplified P/S/T bottom averaging is not validated against C2.
- Input still requires original source paths, `members_csv`, representative `dqsat_csv`, `swp_root`, AHN ASCII and a complete monthly H1 series; none is demonstrated as an out-of-box parameterless production package.
- `DirectDra.Fit` checks candidate hydraulic deviations, but the program marks all products `RAW_SOURCE_DRA_CANDIDATE_NOT_ADMITTED`, not scientifically admitted. No acceptance envelope/rejection gate for approximation error is implemented. Correctly cannot claim all 29 admitted merely because a candidate is serializable.
- Old W07 release narrative is inconsistent: inspect exact executable branch/head and test evidence, not only documentation.

## Recommended single closure implementation
1. Freeze evidence: exact C2 manifest/10213 DRA hashes and 29 full checkpoints, SWP profiles, server static sources. Record immutable SHA256.
2. Make `W07Dra --from-raw` numerical parity with C2 at original seven-source aggregation BEFORE compression. Fix seasonal RIV source and denominator semantics, missing-value policies and exact depth/level conventions.
3. For 29 HRUs, apply current `Fit`/C2 protected algorithm to full seven-source records, preserve PIPE and dynamic H1. Measure actual drain/infiltration and net flux error over representative groundwater heads/months. Reject scientifically unacceptable fits rather than silently admit.
4. Package the 10213 original, byte-qualified DRA products unchanged where their hashes are supported; derive or repair the 29; optionally regenerate all only after exact C2 comparison.
5. Single Windows x64 startup without Python, with complete trusted path config and preflight, immutable output. Release gate: IDs 1..10242 exactly once, parsable DRA files, 10213 matching accepted hashes, 29 individually audited, SWAP 4.3.1 end-to-end model runs including extrema.
6. Treat any generated-but-unqualified files as candidates, not production release.

## Checked refs
PR #19 and #20 changed-file listings and source code, `tools/native/w07/DirectDra.cs`, `RawDrainage.cs`, `Program.cs`, `SwpHorizonReader.cs`, `DIRECT_SERVER_RUN.md`, W07 29 execution handoff.

**As of 2026-10-27 there is not sufficient source evidence to assert a finished, server-tested 10242/10242 DRA procedure.**
