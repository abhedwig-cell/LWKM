# P12 observed flux algebra in hrulist2SWAP

This document records active historical algebra only. It does not assert scientific correctness.

For each HRU and time interval, over members with issvatwb=true:

## Head / bottom exchange

hh1 = arithmetic mean of ingridr4 head values.

dh = sum(bbc3weight_i * (ingrid2r4_i - ingridr4_i)).

qq_raw = sum((ingrid2r4_i - ingridr4_i) / c1_i).

qq_output = 100 * qq_raw / nusvatwb.

The source comment says conversion m -> cm by *100 for BBC. The division by member count is active and requires a support/unit audit.

## FLF

flf_raw = sum(ingrid3r4_i).

flf_output = 100 * flf_raw / areawb_sum.

This is algebraically distinct from qq and strongly suggests ingrid3r4 has a different native support/unit from the conductance-derived qq term.

## QLAT

Active:
qlat_raw = sum(ingrid4r4_i)
qlat_output = 100 * qlat_raw / areawb_sum

Archived alternatives in comments include:
qlat_raw += ingrid4r4_i * area_i
and
qlat_output = 100 * qlat_raw / area_sum / dd

These comments are provenance only. They demonstrate that area/time normalization changed historically and make qlat a priority unit audit.

## Accounting areas

area_sum = sum(area_i) over all HRU members.
areawb_sum = sum(area_i) over issvatwb members.

These are computed via AVERAGE*n and are mathematically sums, not means.

## Audit priority

Bind native units/support for:
- MODFLOW head grids ingridr4/ingrid2r4;
- c1;
- ingrid3r4 (FLF source);
- bdgqlat_*_l1.asc;
- SVAT area and its relation to parent MODFLOW-cell accounting.

Do not harmonize the three formulas before those contracts are known.
