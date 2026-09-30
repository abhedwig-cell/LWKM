# LHM upstream run qualification for LWKM

## Scope boundary

The LHM/MODFLOW run is an upstream product.

LWKM is NOT responsible for:
- restart mechanics between MODFLOW sub-runs;
- reproducing restart transitions;
- certifying MODFLOW numerical correctness.

LWKM IS responsible for refusing an incomplete or evidently failed upstream run as source authority.

## Implemented gate route

Implementation:
- `tools/lhm_upstream_qualification.py`;
- CLI entry in `tools/lwkm_source_cli.py`.

Command:

```text
python -m tools.lwkm_source_cli qualify \
  --controls <authoritative-LHM-run-tree> \
  --profile config/server/lhm433-lwkm-transfer-profile.yml \
  [--bundle <bundle.zip>] \
  [--output qualification.json]
```

The gate report is machine-readable and preserves Q0, Q1, Q2 and Q3 separately. A Q1 failure therefore does not get misreported as a Q0 parsing failure.

## Gate levels

### Q0 CONFIGURED

PASS requires:
- at least one `control_run_YYYY_YYYY.ini`;
- valid period syntax in every control filename;
- every control file is readable/parseable as a control source.

Q0 deliberately does not decide whether the periods form a continuous chain.

### Q1 PERIOD_COMPLETE

PASS requires:
- controls ordered by period;
- no overlaps;
- no gaps.

The control chain is provenance evidence. LWKM does not simulate or repair restart transitions.

### Q2 OUTPUT_COMPLETE

PASS is driven by the versioned transfer profile.

For every period:
- required static control keys must resolve to physical files;
- every configured annual source family must be present for every year;
- configured wildcards must match at least one physical file;
- the authoritative run root must be identifiable;
- every required raw run-output family must match at least one physical file.

Q2 therefore uses the same dependency contract as source collection. It does not rely on a second hand-maintained output list.

### Q3 EXECUTION_EVIDENCE

Current automated minimum:
- every required raw run-output file still exists;
- no required output is zero bytes;
- where output filenames contain valid `YYYYMMDD` timestamps, the latest dated output must reach the end of its control period.

If no dated output evidence exists, Q3 is reported as PARTIAL rather than silently passed.

Available process logs/exit codes can strengthen Q3, but the current qualifier does not invent success from their absence.

A failed final-timestamp or zero-byte check is a Q3 failure. It is not “repaired” by LWKM.

### Q4 LWKM_SOURCE_QUALIFIED

Q4 requires:
1. Q0-Q3 all PASS;
2. a supplied source bundle verifies successfully.

With `--bundle`, the CLI performs the bundle verification and reports Q4 PASS only when both conditions hold.

Without a bundle, qualification can stop at Q3 with Q4 PENDING.

## Test coverage

Synthetic CI covers:
- complete two-period Q0-Q3 pass;
- Q1 failure on a control-period gap;
- Q3 failure on zero-byte required output;
- Q3 failure when dated outputs stop before period end;
- full CLI route through verified-bundle Q4.

This is an implementation qualification only. Real NHI admission still requires running the same commands against the authoritative LHM run tree and retaining the resulting qualification report.

## Optional stronger checks

Useful when inexpensive:
- sanity-range checks on head grids;
- expected snapshot count per source family;
- grid geometry/extent consistency;
- explicit process log / exit-status ingestion;
- adjacent sub-run boundary-state comparison as a diagnostic.

A boundary-state mismatch is reported upstream. LWKM does not repair the restart.

## Interpretation

Qualification is execution/provenance qualification, not an independent hydrological validation of LHM.

Q4 means:
“the upstream run is sufficiently complete, evidenced and reproducibly packaged for LWKM consumption.”

It does not mean:
“MODFLOW or MetaSWAP have been independently proven numerically correct.”
