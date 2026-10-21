# W07 29-HRU execution handoff, 2026-10-21

This branch contains an exhaustive diagnostic five-level assignment for all 29 original C2 blockers in `docs/evidence/2026-10-21-w07/29_five_level_candidates.json`, plus a second implementation `tools/w07_autofive_full_records.py` which consumes complete physical HRU records in the same schema as `tools/run_dra_protected_population.py`.

The full-record version:
- first attempts the existing protected selector;
- if it fails, partitions open-water sources to the remaining four slots while retaining the pipe separately;
- sums drainage and infiltration conductances, preserves spacing, and builds combined explicit monthly levels where supplied;
- quantifies source-vs-equivalent branch flux deviations;
- outputs the complete `to_render_level` records in a JSON bundle.

Run:

```
python -m tools.w07_autofive_full_records --input qualified_physical_hrus.json --output w07_five_level_renderer_inputs.json
```

**Scientific/operational limit:** the Work C2 `protected-partition-diagnostics.json` alone lacks complete `dep`, `dd` and `level_series` fields, and therefore cannot produce full SWAP .DRA bytes without invoking the qualified upstream data. The new implementation intentionally refuses to invent these. A JSON renderer-input bundle is **not** a final .DRA file and does not prove model execution.

Next integrate this selector at the existing **full seven-system aggregate source** in the C2 producer and reuse its DRA renderer with 29 selected renderer-input records, preserving the 10213 unmodified output hashes. Compare and run actual SWAP 4.3.1 models; capture warnings, balance and drainage differences. Production admission remains pending until this occurs.
