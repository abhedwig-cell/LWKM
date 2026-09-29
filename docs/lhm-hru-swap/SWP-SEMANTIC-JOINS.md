# SWP semantic joins: closure strategy

The remaining context-resolution work is treated as foreign-key/domain-model reconstruction, not template reverse engineering.

## Rooting
Resolve effective RDS from the explicit datamodel relation between run, soil/crop/rotation and Wortelzone. Legacy RDS=120 is evidence only. If the current database cannot derive it, the profile/datamodel is incomplete and must be extended explicitly.

## Crop rotation
Context must contain a semantic rotation object:
- rotation id
- yearly crop/management periods
- crop definition references
- optional CO2 reference
The renderer serializes this object; it does not discover/copy CRP files.

## Bottom boundary
For SWBOTB=2 context must contain the DATE2/QBOT2 series as data, not a filename. The join from run/scenario/boundary definition is mandatory. Other SWBOTB modes have their own typed context.

## Meteo
Context stores meteo identity/data reference separately from serialized METFIL. Path naming belongs to export policy.

## Admission rule
A run is renderable only when every active SWAP switch has the corresponding typed semantic object. A switch that points to an empty legacy file is not considered resolved evidence of a meaningful auxiliary object.
