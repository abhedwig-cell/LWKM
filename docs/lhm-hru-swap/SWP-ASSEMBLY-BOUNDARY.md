# Historical SWP assembly boundary

Status: PRODUCER BOUNDARY IDENTIFIED, MARTIN DATAMODEL NOT YET RECOVERED

HRUlist2SWAP v0.38 explicitly states that it does not write the final .SWP file. It writes a CSV run list intended to become the "Runs" worksheet in Datamodel.xlsx. IDs in that table reference other database worksheets such as soil and crop. The historical procedure of Martin then assembles complete SWAP input.

The production batch confirms the sequence:

1. HRU2SWAP.exe generates SVAT2SWAP10242.csv plus BBC/DRA/MET assets;
2. change directory to svats10242;
3. run do_kopybbcdra.bat;
4. external/datamodel procedure builds runnable SWAP cases.

The current Library/repository search has not recovered Datamodel.xlsx or the renderer that consumes it. Therefore byte-identical legacy .SWP generation cannot yet be implemented responsibly.

## Modern replacement boundary

The canonical replacement should not reproduce the manual Excel handoff. It should model the same information explicitly:

- Runs/case table;
- soil database keyed by soil_id;
- crop database keyed by crop_id;
- rotation/calendar database keyed by rotation_id;
- boundary assets keyed by BBCFIL/DRFIL;
- meteorology keyed by METFIL/climate;
- global/scenario defaults.

The final SWP serializer becomes a deterministic join/render step over these versioned databases.

## Admission rule

Do not invent missing legacy template text. A full writer is admitted only when either:

A. Datamodel.xlsx + renderer are recovered and golden historical cases can be compared; or
B. a SWAP-version-owned canonical template/database interface is used and generated cases pass SWAP parser/run tests, with scientific field equivalence to the historical Runs table.

The new content-addressed planner and case.spec writer remain valid regardless of which serialization route is chosen.
