# DRA source-runtime provenance qualification — 2026-10-01

Base head: f38b27bf95b41c6cd3c975318a09f5b488bb3e18.

## Qualified source finding

SUPPLIED_AVERAGE_READ_BEFORE_INITIALIZATION_CONFIRMED.

The source archive contains four Alterratools variants:
Alterratools.f90, Alterratools_011010.f90,
Alterratools_23012015.f90 and Alterratools_31082011.f90.
All four define REAL*4 FUNCTION average with the same defect for nulist>1:
the accumulation reads average before any assignment initializes it.
Neither the routine's declarations nor its entry path provide initialization.
The separate nulist=1 and nulist<=0 branches assign values, but those branches
do not initialize a subsequent invocation under portable Fortran semantics.

The active hrulist2SWAP.f90 drainage path calls AVERAGE for lengths,
conductance sums and infiltration-conductance sums. It also uses the
routine elsewhere, including ground levels and areas.
This is a concrete supplied-source defect, not proof of the linked routine
inside the historical producer or proof of its runtime values.

A compiler option or particular storage behavior could affect the observed
execution. A linked library could contain a different implementation.
No compiler, linker or binary identity is established by these source files.
Do not emulate an arbitrary initial value or reuse a prior call's result to
force-fit the oracle.

## Three semantic layers

| Layer | Qualified statement |
| --- | --- |
| Supplied source | Active all-member loops are present, but N>1 AVERAGE reads an undefined function result. Literal execution is not a portable deterministic arithmetic specification. |
| Realized executable | The 49 DRA files are valid historical outputs. Their linked AVERAGE implementation and producer build remain unidentified. No numerical discrepancy is attributed to this defect yet. |
| Modern corrected production | All-member conductance uses a deterministic sum and full 62500 m2 per member. Python's deterministic arithmetic expresses the intended qualified mathematics, not a proven exact replay of the supplied Fortran binary. |

This clarifies earlier reports that wrote AVERAGE(N,list)*N as sum(list).
That algebra requires a correctly initialized AVERAGE. The intended physical
formula remains qualified; the literal source execution needs this explicit
qualification. No historical defect becomes modern production authority.

## Archive chronology

All 49 DRA members in run_files(1).zip have ZIP timestamp
2026-03-24 20:56:36. The supplied hrulist2SWAP.f90 history labels its
v0.38 drainage-resistance fix apr-26; its source archive member timestamp
is 2026-05-21 15:49:56.

These are mutable, timezone-free ZIP wall-clock timestamps and source
history comments. They are provenance clues, not authenticated creation
times, build times or executable identities. They prevent assuming that
the March archive is automatically an exact v0.38 runtime replay.
The 241/245 SWALLO behavior comparison with supplied v0.38 remains valid
as the already qualified policy baseline. It never proves binary identity.

## Exact coverage and blocker

Inventory covered source (2).zip, run_files(1).zip and
LWKM_workflow_no_asc.zip. No HRU producer executable, object, project or
link manifest was found in their top-level members.
The only library item was source/sun2makkink/ttutil413.lib, which does not
establish the HRU producer's link.
A subsequent recursive search covered 38 recovered ZIP archive instances,
including nested archives to depth five and the recovered HRU2LSW archive.
No HRUlist2SWAP producer binary or build identity was found. Tools/SWAP/swap.exe
is the simulation engine, not the input producer. Old PreMetaSWAP executables
and projects in source/premsw.zip are a different program family. This is
not a claim about all Library files or unopened non-ZIP members. Prior
exhaustive template searches remain separately scoped.
Evidence: docs/evidence/2026-10-01/dra-producer-search.json.

The control_LHM433_HRU_SWAP_10242.inp file names the native conductance,
bottom and seasonal-level grids already used in the all-member diagnostic.
A matching filename/path does not prove the version actually consumed by
the historical executable. Its original hashes and run-linked logs remain
necessary for historical numerical attribution.

The source-runtime route is therefore qualified as
SOURCE_DEFECT_CONFIRMED_REALIZED_CAUSAL_ATTRIBUTION_BLOCKED.
No expected differences were added. STATIC04's 75 preregistered L differences,
nature's zero-expected-difference status and the four original SWALLO
residuals remain intact. Neither producer receives admission.

## Reproduction and validation

tools/audit_dra_archive_provenance.py inventories hashes, source history,
all observed AVERAGE routines, DRA timestamps and build/executable members.
Executed against all three archives: 49 DRA members, four confirmed
AVERAGE findings. The emitted routines were also manually inspected.
Python compile check passed. No Actions run was started and no historical
Fortran executable was compiled or run.

Evidence: docs/evidence/2026-10-01/dra-archive-provenance.json.

Next: search remaining recovered archive contents for run-linked producer
logs/build identities and independently bind the exact input hashes.
Modern DRA generation must retain deterministic all-member mathematics.
