# H-P12-STATIC03 — soil2 crop-class authority audit

Domain clarification:
  soil2 is a two-class soil grouping used for crop mapping:
  - sand/loam
  - clay/peat.

It is not the detailed SWAP hydraulic soil/profile authority. Detailed profile authority remains Piet HRU schema (bfe_repr / bodem_repr).

Legacy behavior:
- soil2_maj = member-count majority over all HRU members;
- representative land use is later overridden from Piet's svat_repr;
- crop mapping uses lu2crop(soil2_maj, representative_lgn).

This is physically plausible as a separate coarse crop-parameter class, but authority is mixed.

Candidate modern semantics:
- derive crop soil class from the authoritative representative soil or representative SVAT, then combine with representative land use.

Historical semantics:
- retain member-majority soil2 as a separately named legacy/QA value until impact is known.

Required audit:
1. establish mapping from representative soil/SVAT to soil2;
2. compare representative-derived soil2 with member-majority soil2 over all HRUs;
3. compare resulting lu2crop/lu2croporg only where soil2 differs;
4. use realized SWP/crop references as oracle where available.

Status: OPEN_AUTHORITY_AUDIT. No defect classification yet.
