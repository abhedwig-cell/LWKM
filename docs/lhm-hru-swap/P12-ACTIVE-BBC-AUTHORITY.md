# P12 active BBC authority resolution

Source inspection resolves the active SWBOTB=2 producer.

Current active write:
  QBOT2 = HRUlist(kk)%qq(nt)

where:
  qq = 100 * mean((head_l2-head_l1)/c1)
and c1 is in days, so QBOT2 is cm/day.

The following alternatives are present but commented out:
- FLF
- FLF + QLAT
- diagnostic multi-column qq/flf/qlat output.

Therefore:
- current production BBC does NOT use FLF;
- current production BBC does NOT depend on modflowidf2asc's period-summed FLF unit;
- FLF support/time-normalization questions remain relevant to diagnostics, historical alternatives and water-balance analysis, but are not a blocker for reproducing current SWAP input.

modflowidf2asc independently establishes that it sums daily MODFLOW values across the requested interval without dividing by interval length. Any future reactivation of FLF as QBOT2 must therefore explicitly resolve time normalization unless the native daily values/period semantics prove otherwise.

Production priority now:
1. qualify qq aggregation and head/c1 support;
2. preserve FLF/QLAT as audited diagnostic quantities;
3. do not reactivate historical FLF boundary modes without a separate admission.
