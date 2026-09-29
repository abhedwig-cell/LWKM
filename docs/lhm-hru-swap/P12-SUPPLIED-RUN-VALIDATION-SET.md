# Supplied realized run validation set

run_files.zip contains 49 realized HRU run directories, HRU ids 7866..7945 with gaps.

Each includes at least:
- populated .bbc;
- populated .dra;
- populated .met;
- swap.swp;
- crop/CO2 assets.

Membership composition against export_svat_HRU_NRU_10242.csv:
- 40/49 HRUs contain at least one donor-different (matched-target) member;
- 9/49 contain donor-equal members only and therefore exercise historical fallback-to-all.

Examples:
- HRU 7876: 57 members = 42 donor sources + 15 matched targets.
- HRU 7875: 45 = 17 donor + 28 target.
- HRU 7877: 28 = 27 donor + 1 target.
- HRU 7869: 25 = 25 donor + 0 target (fallback control).

This is a useful targeted validation population for WBSEL01 because both historical branches are represented.

Realized BBC files contain three numeric columns after DATE2, unlike the currently supplied source's active one-value write. Treat these files as executable-oracle fixtures with unresolved exact executable provenance.

The SWP references BBCFIL and DRFIL by HRU id and uses SWBOTB=2/SWDRA=1, confirming these populated files are consumed run inputs.
