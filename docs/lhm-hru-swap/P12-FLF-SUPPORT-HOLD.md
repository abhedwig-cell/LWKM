# FLF support conversion hold

Historical behavior is known:
  flf_hru = 100 * sum(bdgflf_i) / areawb_sum

The source also states that time-dependent bottom conditions are constructed only for issvatwb=true members.

What is NOT yet established:
- whether bdgflf native values are cell-total m3/day, period volumes, or another MODFLOW budget representation at this stage;
- whether areawb_sum is intentionally the physical receiving SWAP/MetaSWAP area;
- whether the denominator was inherited pragmatically from HRUlist2MetaSWAP;
- whether full MODFLOW area (N*62,500 m2) would be the correct denominator for another accounting question.

Therefore historical formula is preserved but not endorsed as corrected physics.

Canonical redesign should retain:
- native FLF sum / recoverable volume;
- number of source MODFLOW cells;
- full MODFLOW accounting area;
- selected MetaSWAP/SWAP active area;
- historical normalized FLF.

Derived depth representations can then be explicit views rather than destructive conversions.
