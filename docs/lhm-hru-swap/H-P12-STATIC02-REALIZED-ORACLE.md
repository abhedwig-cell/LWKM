# STATIC02 realized-oracle protocol without HRU schema CSV

The full-population impact count requires export_HRUschema_10242_copy.csv and remains pending.

The supplied 49 realized run directories can nevertheless test executable behavior.

For each run HRU:

## Final representative land use
Infer from realized SWP/crop references and/or schema-selected crop mapping where unambiguous. Do not infer from SWETR itself.

## SWETR oracle
Read realized swap.swp SWETR.
Compare:
A. expected from raster-member majority land use;
B. expected from final representative land use.

Only HRUs where A != B are discriminating cases.

## Nature/DRA oracle
Read realized .dra system 4:
- if source conductance would otherwise yield active drainage but realized DRARES is forced to 100000 with zero depth/levels, this supports is_nature=True behavior;
- distinguish from the independent drnres>20000 suppression condition before attributing to nature.

Compare nature flag under:
A. raster-member majority land use;
B. representative land use.

Only boundary-crossing and hydraulically discriminating HRUs can identify executable ordering.

## Classification

If realized files follow A in discriminating cases:
  REALIZED_EXECUTABLE_REPRODUCES_ORDERING_DEFECT.

If they follow B:
  SUPPLIED_SOURCE_DEFECT_NOT_PRESENT_IN_REALIZED_EXECUTABLE.

If no discriminating cases exist among 49:
  REALIZED_SAMPLE_NON_DISCRIMINATING.

Do not generalize from non-discriminating HRUs.
