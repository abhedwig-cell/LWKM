# P12 accounting domains

P12 must expose at least two HRU-level accounting views rather than forcing all fluxes onto one denominator.

## HRU_MODFLOW_CELLS

Represents the set of original 250 x 250 m LHM groundwater cells grouped into an HRU.

For equal-sized MODFLOW cells, an intensive MODFLOW-cell quantity is aggregated by equal cell mean. Historical qq/nusvatwb is consistent with this view when the selected members correspond one-to-one to distinct source LHM cells.

## HRU_METASWAP_ACTIVE_AREA

Represents the sum of uopp of the MetaSWAP SVATs grouped into an HRU.

Surface intensities such as precipitation and evaporation are aggregated with uopp weights.

## Cross-domain quantities

FLF and derived coupling terms cross these domains. Their conversion must explicitly state whether a MODFLOW-cell volume is being expressed as depth over:
- full MODFLOW area; or
- MetaSWAP active area.

Those two numbers are different when uopp < 62,500 m2 and neither is universally the 'correct' one. The correct denominator depends on the receiving model/accounting question.

Canonical outputs should therefore retain enough information to reconstruct both volume and depth representations instead of storing only one pre-normalized number.
