# Auxiliary SWAP file lifecycle correction

User domain knowledge resolves the interpretation of zero-byte run-specific files such as 12.met and 12.bbc.

They are not evidence that the auxiliary semantic data are absent. The legacy workflow creates target files and a later Fortran program writes/populates their substantive contents.

Therefore the earlier statement that zero-byte MET/DRA/BBC files are simply unwanted meaningless side effects is withdrawn.

## Correct lifecycle

1. Datamodel defines the run and references/parameters.
2. R/SWAPtools prepares SWP and auxiliary target paths/files.
3. Fortran producer(s) generate substantive run-specific auxiliary content such as MET and BBC (and potentially DRA depending on workflow).
4. SWAP consumes the completed input set.

## Replacement architecture

Keep two workstreams separate:

A. SWP renderer
- datamodel -> generic context -> SWP
- does not itself generate MET/BBC/DRA content.

B. Auxiliary producers
- datamodel/source time series -> MET/BBC/DRA/etc
- each producer has its own dependency fingerprint and incremental output.
- legacy Fortran may initially remain authoritative while its contract is reconstructed.

A run is not considered executable until all required auxiliary producer outputs are complete. A zero-byte placeholder is a lifecycle state, not a valid completed semantic object.

## Immediate consequence

Do not remove auxiliary targets merely because they are initially empty. Instead, remove unnecessary *eager regeneration*: create/update only the auxiliary files whose producer inputs changed.
