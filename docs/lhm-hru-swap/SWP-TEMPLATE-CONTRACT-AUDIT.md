# SWP template contract audit

Status:
**R2 HISTORICAL TEMPLATE CONTRACT RECOVERED; RUN-2000 SERIALIZATION GATE CLOSED**

## Raw evidence

Recovered from raw-readable `Datamodel_9830.zip`:
- `swap_wwl.swp`
- SHA-256 `d960f7ede8074672f8f8d6c938df0554383f631e75dfdb67ea33bfe15cc5beab`;
- `swap_tools.log`
- SHA-256 `e691dfd5984c9ee4c5c3ed5a8e658fec9b79ece00b8159e516565db11549752c`;
- `control.inp`;
- `Datamodel_10242.sqlite`.

The historical control explicitly uses:
- `FILXLS = ./Datamodel_10242.xlsx`;
- `FILSQL = ./Datamodel_10242.sqlite`;
- `FILSWP = swap_wwl.swp`;
- `RUNID = ALL`;
- `CREATE = Yes`;
- `RUN = No`.

Thus this archive records a real historical SWAPtools input-generation route, not a free-standing template sample.

## Template surface

The recovered `swap_wwl.swp` contains **50 distinct Mustache symbols**, not 27.

Dynamic sections:
- `TABLE_CROPROTATION`;
- `TABLE_SOILPROFILE`;
- `TABLE_SOILHYDRFUNC`;
- `TABLE_SOILTEXTURES`;
- `SWITCH_SWINCO_OPTION_2`;
- `SWITCH_SWINCO_OPTION_3`;
- `SWITCH_SWDRA_OPTION_1`;
- `SWITCH_SWBOTB_OPTION_2`;
- `SWITCH_SWBOTB_OPTION_5`.

Important scalar symbols include:
- TSTART / TEND;
- INLIST_CSV;
- NUMNODNEW / DZNEW;
- METFIL;
- GWLI;
- PONDMX / RSRO / RSOIL;
- RDS;
- DRFIL;
- SWBBCFILE / BBCFIL / SWBOTB.

The historical template itself hard-codes several settings that are not legitimate current scientific authority, most importantly:
- `SWETR = 0`.

That hard-coded SWETR cannot represent all current 10,242 Runs because 3,080 require SWETR=1.

## Recovered create_SWAP serialization effects

Direct substitution of the recovered template with the qualified run-2000 context reproduces all qualified run-scientific scalar values, but initially differs from the realized SWP in table serialization.

The historical template section bodies do not contain explicit table-header rows. The realized `swap.swp` does.

Observed table headers injected by the historical SWAPtools path:
- CROPSTART CROPEND CROPNAME CROPFIL CROPTYPE;
- ISUBLAY ISOILLAY HSUBLAY NCOMP;
- ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS;
- PSAND PSILT PCLAY ORGMAT.

These are serialization effects, not scientific decisions.

They are now explicit in:
`tools/swp_template_adapter.py`.

## Hidden template policy made explicit

The adapter also parameterizes five historically hard-coded active assignments:
- SWETR;
- SWWBA;
- PERIOD;
- SWAUN;
- SWODAT.

SWETR remains scientific run context.

The four output controls plus INLIST_CSV are renderer/output profile policy and are bound explicitly in:
`config/swp-profiles/LWKM_2026.yml`.

The run-2000 realized output policy is:
- SWWBA = 1;
- PERIOD = 1;
- SWAUN = 0;
- SWODAT = 0;
- detailed WATBAL/ETTERMS/GWL/CROP/WOFOST/GRASS output list.

These values are not promoted to 49-run-global truth yet. Their status is:
`RUN_2000_REALIZED_ORACLE_QUALIFIED_CANDIDATE`.

## Run-2000 serialization result

Inputs:
- recovered `Datamodel_10242.sqlite`;
- run_id 2000;
- recovered historical `swap_wwl.swp`;
- explicit R2 template adapter;
- explicit run-2000 output profile.

Oracle:
- raw realized `swap.swp`
- SHA-256 `6b47cec011749041bc99e78322ed99a4116b798ec67536969074984f96a49796`.

Result after adaptation:

**0 differences across all 112 active assignment keys.**

Also:
- crop rotation: 56 / 56 rows semantically identical;
- soil profile: 9 / 9 rows semantically identical;
- soil hydraulic table: 4 / 4 rows semantically identical;
- soil texture table: 4 / 4 rows semantically identical.

Classification:
**RUN_2000_DIRECT_SERIALIZATION_GATE_CLOSED**.

This is stronger than the earlier reduced semantic gate because it checks every active scalar assignment in the file, not only the selected scientific subset.

## What this does not prove

This result does not make the recovered historical template current production authority.

Remaining reasons:
1. current `Template.zip` raw bytes are still blocked;
2. 49-run realized SWP set is still blocked;
3. historical template had hidden policy that is now explicit but only one-run-qualified for output settings;
4. upstream intentional scientific corrections must still be classified in the multi-run gate.

## Production rule

The direct Python path may use the historical template only through the explicit adapter contract:
- no hidden SWETR=0;
- no hidden output switches;
- explicit table headers;
- scientific values from typed context;
- output-only settings from an explicit render profile;
- unknown template symbols fatal.

Do not copy SWAPtools execution, ZIP or post-processing side effects into the renderer.
