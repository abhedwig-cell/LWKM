# B to C qualification contract

## Canonical authority

C receives immutable original SVAT attributes plus an explicit boolean is_suspect and the eight reason flags.

Primary clustering input is is_suspect == false.
Suspicious targets are is_suspect == true.

The target architecture does not require svat_info_lwkm_new.csv or a pre-filled svat_donor field.

## Historical equivalence regression

The legacy R script used:

valid: svat_donor == svat
not-ok: svat_donor != svat

from svat_info_lwkm_new.csv, then reconstructed the not-ok rows from original SVAT_INFO.csv.

Before removal of the legacy artifact is admitted, run a one-to-one SVAT comparison:

legacy_notok = (svat_donor != svat)
modern_suspect = union(eight explicit flags)

Required historical-compatibility result: zero modern-only and zero legacy-only rows, unless a documented historical exception is discovered.

Any mismatch must be retained as a named fixture and explained. Do not tune the eight criteria merely to force equality without tracing the producer provenance.

## Scientific benefit

This removes a destructive and currently source-missing preprocessing stage while preserving the information actually consumed by the HRU workflow: which SVATs may enter primary clustering and which must be assigned afterward.
