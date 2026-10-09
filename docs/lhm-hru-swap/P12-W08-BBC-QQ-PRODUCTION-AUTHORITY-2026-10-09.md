# W08 BBC production authority — 2026-10-09

Status: OWNER-CONFIRMED MODERN PRODUCTION SEMANTICS; NUMERICAL ADMISSION PENDING.

The project owner confirmed on 2026-10-09:
- The **qq** BBC variant is the correct production route.
- Historical BBC output with **three numerical columns** is a **test/diagnostic variant**, not the desired modern production format.

For SWBOTB=2 the intended QBOT2 formula is:
`QBOT2 = 100 * mean((head_l2 - head_l1) / c1)`, yielding cm/day when head is metres and c1 is days, subject to the exact historical support and averaging contract.

The active implementation candidate is `tools/generate_bbc.py` and its `aggregate_qbot2` / `render_bbc` functions. Preserve water-boundary SVAT selection semantics. Do not activate FLF or FLF+QLAT alternative modes or interpret the three diagnostic columns as required production BBC fields.

Qualification still required:
1. Validate selection of `issvatwb` members, fallback behavior, and the support of the average.
2. Reject invalid/nonpositive `c1`, non-finite heads, mismatched member indices, and missing dates explicitly.
3. Verify cm/day conversion, sign, and time-series completeness.
4. Compare `qq` values against qualified historical or independent reference calculations; classify the three-column oracle as diagnostic, not an expected production identity.
5. Test SWAP BBC parser/interface and preserve source lineage and file qualification.

This owner confirmation closes the *choice of BBC formula*, not W08 production admission.
