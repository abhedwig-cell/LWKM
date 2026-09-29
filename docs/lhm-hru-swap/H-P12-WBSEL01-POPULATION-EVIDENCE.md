# H-P12-WBSEL01 population evidence from canonical 10,242-HRU export

Source: export_svat_HRU_NRU_10242.csv supplied 2026-09-29.

File structure:
- 427,656 data memberships plus header;
- HRU ids run through 10,242;
- explicit columns svat_orig, HRU, svat_donor and label.

Exact indexed label counts:
- valid | HRU group size OK | NRU group size OK: 369,752
- Toegevoegd: 57,791
- Restgroep: 113
Total: 427,656.

Observed examples establish:
- valid rows normally have svat_orig == svat_donor;
- Toegevoegd rows have svat_orig != svat_donor in inspected cases;
- Restgroep can contain both donor-equal and donor-different memberships.

Therefore at least the 57,791 Toegevoegd memberships (13.516% of all memberships) form a large, explicit non-donor population. Historical hrulist2SWAP sets these non-donor memberships to isverdacht=TRUE and then uses isverdacht as issvatwb.

This means the suspected inversion is not a four-cell edge case. For any HRU containing non-donor memberships, the historical code selects the non-donor subset for QBOT2/meteo instead of falling back to all members. HRUs with no non-donor members fall back to all.

Exact distinct-HRU impact still requires grouped execution over the 74 MB CSV. Do not infer the number of affected HRUs from membership count.

Interpretation:
- defect likelihood is upgraded;
- production correction remains held until grouped numerical impact and historical intent are checked;
- the four historical filter_LWKM discrepancies are a separate issue and must not be conflated with these 57,791 HRU donor substitutions/additions.
