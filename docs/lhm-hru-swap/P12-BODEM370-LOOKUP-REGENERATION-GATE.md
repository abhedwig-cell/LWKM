# Raw lookup regeneration gate

Raw source supplied in conversation:
  SVAT_INFO(1).CSV

The local execution runtime is currently failing before the file can be parsed. Do not substitute snippets for a full 120MB-table reduction.

Already persisted:
- canonical builder tools/build_bodem370_lookup.py;
- regression guards tests/test_bodem370_lookup.py;
- known realized corrections config/p12/bodem370_bofek_known_corrections.csv;
- authority contract P12-BODEM370-BOFEK-LOOKUP-AUTHORITY.md.

When runtime access succeeds, run the builder on the supplied raw CSV and require:
1. exactly one (bofek79,pawn21,grondsoort4,grondsoort2) tuple per observed bodem370;
2. observed code set = 1..370 minus {14,142,143,197,198};
3. all ten persisted corrections match;
4. write config/p12/bodem370_classification_lookup.csv;
5. record source hash and row count.

No hand-filled 365-row table is admissible.
