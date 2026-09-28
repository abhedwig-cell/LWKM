# HRU10242 reproduction attempt — 28 September 2026

Status: **RUNTIME BLOCKED, SOURCE AUTHORITY UNCHANGED**

## Bound inputs

The exact HRU10242 source inputs remain bound by prior inspection:

- `SVAT_INFO.csv`: 552,705 rows, SHA-256 `5f7b657508a4dc885bd60fae93051239046b27788388d6e8832621eaa85fe192`;
- `svat_info_lwkm_new.csv`: 427,656 rows, SHA-256 `5ea4d24a0ce38c802cb1dbf63e30239664965438fbcc55690acced447a248821`;
- `xyLDGBclus.csv`: 560,887 rows, SHA-256 `c659530fb69e32af5fe309b7ae80e20b470e88094b92569f851a32321182d21e`;
- R source member `Rscripts/HRU_clustering/HRU_clustering_LWKM20_31082026.R`, SHA-256 `6e5055241590be6bf7f7afe53a2eaf3f03ab3e0627cb9a82bbae138b73eb599e`.

## Attempt in current chat runtime

The three large CSV inputs are discoverable in Library with their expected names and versions. The current Files backend does not expose an authorized raw-byte materialization path for these Project/Library records, and direct line reads fail internally.

Therefore an exact R rerun cannot be performed in this chat runtime without falsely substituting another copy.

## Consequence

This is a runtime access blocker, not a scientific blocker and not evidence against the existing source binding.

The following remain valid:

- exact input checksums from the earlier successful inspection;
- exact R source checksum and parameters;
- observed current target of 10,242 HRUs;
- source semantics already documented.

The reproduction gate remains open until the bound bytes can be mounted/read in a runtime that can execute R.
