# W01 execution guide — LHM-server provenance freeze

Date: 2026-10-02

## Server bootstrap choice

On the actual LHM server, Python/py is not available from PATH.

Therefore the primary bootstrap for the first server session is Windows PowerShell:

`tools/server/lwkm_w01.ps1`

The PowerShell path currently implements Q0 and Q1 only. That is intentional: the first real server session must stop after the inventory has been reviewed.

The Python route remains available on environments where Python exists, and Q3/Q4 can continue to reuse the repository bundle implementation after Q1 has been closed. No Python installation is required merely to perform the first provenance inventory.

Authority:
- `docs/server/LHM_SOURCE_PROVENANCE_AND_COLLECTION_2026-10-02.md`
- `docs/governance/LWKM_FILE_QUALIFICATION_POLICY_2026-10-02.md`
- `docs/governance/LWKM_PRODUCTION_CHAIN_QUALIFICATION_PROTOCOL_2026-10-02.md`

Executable tooling:
- `tools/server/lwkm_w01.py`
- `config/source/lhm-server-source-spec-v1.csv`

The tool uses only the Python standard library.

Q3-Q4 reuse the repository's existing tested low-level bundle module `tools/lwkm_source_bundle.py`; the W01 orchestrator does not define a competing ZIP format.

## Operating rule for the first server session

Run only Q0 and Q1 first.

Do **not** run Q2-Q4 until:
1. the Q0 roots are confirmed;
2. Q1 has been reviewed;
3. missing and ambiguous source identities have been resolved;
4. the source specification has been updated when the actual server layout differs from the draft.

Q0 and Q1 do not modify source files.

## 0. Check PowerShell

From the existing Command Prompt, run:

```bat
powershell -NoProfile -Command "$PSVersionTable.PSVersion.ToString()"
```

Windows PowerShell 5.1 or newer is suitable.

The script is invoked with a process-local execution-policy bypass. This does not change the server's persistent execution-policy setting:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File tools\server\lwkm_w01.ps1 -Command q0 ...
```

If `powershell` itself is not recognized, stop and report that result before changing or installing anything on the server.

Python is not required for Q0/Q1.

## 1. Prepare one repository checkout or tool directory

The following two files must be available together with their repository-relative versions recorded:

```text
tools\server\lwkm_w01.ps1
config\source\lhm-server-source-spec-v1.csv
```

The Python orchestrator `tools\server\lwkm_w01.py` is the equivalent route for environments with Python, but is not required on this LHM server for Q0/Q1.

Use the current `work/lhm-hru-swap-workflow-v1` branch.

Do not edit the script on the server.

If the source specification needs correction after Q1, change it in Git first and rerun Q1 with the new version.

## 2. Identify the two initial roots

The executable source spec currently uses two explicit roots:

### RUN

The directory tree containing the authoritative raw LHM/MODFLOW run output.

This should be as narrow as possible while still containing the required dynamic LHM products.

### PROJECT

The project/work tree containing the run-bound `BasicData`, HRU/LWKM configuration and historical runtime material used for the target production state.

RUN and PROJECT may point to the same directory if that is how the server is organized. They may also be on different drives.

Do not choose a broad drive root such as `D:\` unless genuinely necessary.

## 3. Choose a provenance output directory

Use a location outside RUN and PROJECT.

Example:

```text
D:\LWKM_provenance
```

Nothing under this directory is source authority. It is the controlled provenance workspace.

## 4. Choose a run ID

Use a stable descriptive identifier.

Example only:

```text
LHM433_1971_2021_CURRENT
```

Do not put a changing timestamp in the identity if the intent is to refer to one scientific run state. A date can be added later to collection metadata automatically.

## 5. Q0: capture run/root identity

From the repository root:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File tools\server\lwkm_w01.ps1 ^
  -Command q0 ^
  -Root "RUN=<ABSOLUTE_LHM_RUN_ROOT>","PROJECT=<ABSOLUTE_LWKM_PROJECT_ROOT>" ^
  -OutputRoot "D:\LWKM_provenance" ^
  -RunId "LHM433_1971_2021_CURRENT" ^
  -ModelVersion "<CONFIRM_THIS>" ^
  -SimulationStart "1971-01-01" ^
  -SimulationEnd "2021-12-31" ^
  -CompletedRun ^
  -RestartHistory "<SHORT_NOTE_IF_KNOWN>" ^
  -Notes "<OPTIONAL_NOTE>"
```

Do not use `--completed-run` unless the selected run state is genuinely stable and no longer changing.

Output:

```text
D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest\q0-run.json
```

### Review Q0 manually

Open `q0-run.json` and verify:
- server hostname;
- RUN root;
- PROJECT root;
- model version;
- period;
- completed-run assertion;
- restart history.

If anything is wrong, do not proceed.

## 6. Q1: inventory without copying

Run:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File tools\server\lwkm_w01.ps1 ^
  -Command q1 ^
  -Q0Path "D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest\q0-run.json" ^
  -SpecPath "config\source\lhm-server-source-spec-v1.csv" ^
  -OutputDir "D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest"
```

Q1 recursively inventories the declared roots. It does not copy or alter source data.

Outputs:

```text
q1-inventory.csv
q1-summary.json
lhm-server-source-spec-v1.csv
```

Possible result:

### Q1_PASS

Every required logical item was found without an unresolved singleton ambiguity.

This does not yet mean the files are semantically qualified.

### Q1_FAIL

Expected during the first real run if:
- required files are missing;
- the draft path hint is wrong;
- multiple candidate copies exist;
- an expected historical artifact was never present in these roots.

A Q1 failure is evidence, not a reason to bypass the gate.

## 7. What to return for review after the first server session

Bring back only:

```text
q0-run.json
q1-summary.json
q1-inventory.csv
```

These files contain metadata and paths, not the large source datasets themselves.

We then review:
1. whether the declared roots are correct;
2. every missing required ID;
3. every duplicate/ambiguous ID;
4. whether the draft source spec contains files that are actually derived;
5. whether additional basis files are consumed downstream but missing from the spec;
6. temporal coverage of the dynamic sets.

Only after this review is Q1 eligible for admission.

## 8. Q2: stage and hash, only after reviewed Q1 PASS

Do not run this during the first inventory session unless Q1 has already been explicitly reviewed.

Example:

```bat
py -3 tools\server\lwkm_w01.py q2 ^
  --q0 "D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest\q0-run.json" ^
  --q1-summary "D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest\q1-summary.json" ^
  --inventory "D:\LWKM_provenance\LHM433_1971_2021_CURRENT\00_manifest\q1-inventory.csv" ^
  --spec "config\source\lhm-server-source-spec-v1.csv" ^
  --bundle-root "D:\LWKM_provenance\LHM433_1971_2021_CURRENT_Q2"
```

Q2:
- copies selected files;
- preserves their source-relative identity under their provenance class/root;
- computes source SHA-256;
- checks that source size/mtime did not change while hashing/copying;
- computes staged SHA-256;
- fails if source and staged bytes differ.

Main output:

```text
00_manifest\files.csv
```

Each staged member receives file-level `PROVENANCE_BOUND`, not automatic semantic admission.

## 9. Q3: build ZIP

After Q2 PASS:

```bat
py -3 tools\server\lwkm_w01.py q3 ^
  --plan "D:\LWKM_provenance\LHM433_1971_2021_CURRENT_Q2\00_manifest\resolved-bundle-plan.json" ^
  --zip-path "D:\LWKM_provenance\LWKM_LHM_SOURCE_LHM433_1971_2021_CURRENT_Q4.zip"
```

Outputs include:
- ZIP;
- `.zip.sha256`;
- `.zip.q3.json`.

The archive supports ZIP64.

## 10. Q4: verify by fresh extraction

Run:

```bat
py -3 tools\server\lwkm_w01.py q4 ^
  --zip-path "D:\LWKM_provenance\LWKM_LHM_SOURCE_LHM433_1971_2021_CURRENT_Q4.zip"
```

Q4:
- extracts to a new temporary directory;
- performs ZIP CRC test;
- re-hashes every manifest data file;
- checks sizes;
- checks missing files;
- rejects undeclared data files.

PASS state:

```text
LHM_SOURCE_Q4_IMMUTABLE_SNAPSHOT
```

This qualifies bundle integrity. It still does not automatically make every member semantically production-admitted.

## 11. Current source-spec caveat

`lhm-server-source-spec-v1.csv` is intentionally a draft derived from recovered control/workflow evidence.

It is expected that the first Q1 run will improve it.

High-priority findings to resolve on the server include:
- exact locations of dynamic head/BDGFLF/BDGQLAT sets;
- `lengte_p_250.asc`;
- `lengte_s_250.asc`;
- `lengte_t_250.asc`;
- historical `verdacht.asc`;
- historical `HRU2SWAP.exe`;
- `HRUSWAP_test.log`;
- exact historical `swap_wwl.swp`.

Do not mark a different same-named copy as selected merely because it lets Q1 pass.

## 12. First-session stop criterion

The first server session is complete when:

- Q0 accurately describes the authoritative roots;
- Q1 has produced an inventory;
- every Q1 missing/ambiguous finding is understood well enough to classify the next action.

No source ZIP is required yet.

That is deliberate: first establish source identity, then collect bytes.
