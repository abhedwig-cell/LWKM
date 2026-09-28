# SVAT donor lifecycle

Source audit of LWKM_makeHRU v0.20 corrects an important workflow interpretation.

## Before HRU clustering

For every SVAT, LWKM_makeHRU initializes:

svatdonor = 0

Suspicious status is encoded independently from the eight selection flags. No donor replacement is performed here.

The CSV used to construct HRUs therefore contains the original SVAT attributes plus qualification flags. Qualification and donor assignment are separate concepts.

## After HRU clustering

Later in the same executable, if export_csv exists, LWKM_makeHRU reads:

svatnr, HRUnr, NRUnr, NRUcode, svatdonr

from export_svat_HRU_NRU_10242.csv and assigns svatdonor back to the SVAT record.

The comment explicitly states that this is used to determine discharge per HRU and distinguishes SVATs included in the HRU classification through svat_orig = svat_donor.

Therefore the realized donor relation is an output of the HRU clustering/assignment workflow and is only fed back into LWKM_makeHRU for downstream aggregation. It is not an input transformation used to create the suspicious-cell set.

## Canonical consequence

B qualification:
- preserve original SVAT values;
- attach flags/reasons;
- no donor substitution.

C HRU:
- create primary clusters from qualified cells;
- assign remainder/suspicious cells through donor/extra routes;
- emit explicit SVAT -> HRU and SVAT -> donor relations.

Downstream aggregation may use those relations explicitly. Never overwrite original SVAT attributes to emulate a donor.
