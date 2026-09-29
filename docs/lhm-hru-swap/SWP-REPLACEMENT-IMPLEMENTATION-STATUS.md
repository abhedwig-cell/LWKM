# SWP replacement implementation status

A large implementation block now exists:

1. Datamodel authority and named profile precedence are fixed.
2. Generic render-context schema exists.
3. SQLite context builder resolves soil profile/hydraulic/texture records and fails on unresolved semantics.
4. Generic template renderer supports scalar and repeated/conditional Mustache-style blocks and fails on unresolved symbols.
5. Dependency-level fingerprints distinguish global, soil profile, hydraulics, texture, rooting, bottom and run references.
6. Dry-run planner returns skip/create/update plus exact changed dependency classes.
7. Rendering is atomic.
8. Auxiliary files remain separate operations.

Remaining semantic blockers before first admitted legacy-equivalent render:
- exact RDS authority/derivation;
- full crop-rotation/domain join;
- bottom-boundary time-series join for SWBOTB=2;
- meteo/reference semantics;
- explicit placement of ELAS and simulation dates in datamodel/profile.

These blockers concern context resolution, not rendering architecture.
