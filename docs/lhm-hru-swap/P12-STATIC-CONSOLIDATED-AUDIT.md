# P12 static producer audit — consolidated closure pass

This pass audits the complete static aggregation/output block rather than individual variables.

## Authority-order defects confirmed

### LANDUSE
Legacy majority lgn is used to derive SWETR and isnatuur before lgn is overridden from Piet schema.
Downstream:
- SWETR in Runs;
- isnatuur suppresses DRA system 4.
Status: STATIC02 confirmed source defect.

### DQSAT
Legacy majority BFE is used to select dqsat before BFE is overridden from Piet schema.
Downstream:
- dqsat in Runs;
- DRA L=4*dqsat where length>0.
Status: STATIC04 confirmed source defect.

### SOIL2
Legacy member-majority soil2 is retained after representative soil is established.
Earlier reconstruction establishes soil2 as deterministic lookup-derived class from bodem370 hierarchy.
Modern path: representative soil -> canonical lookup -> soil2.
Status: legacy authority reduction superseded, impact audit pending.

### RDS
Legacy fallback loop has control-flow defect but rds is later overwritten by rz_repr in current representative mode.
Status: confirmed defect, overridden in current configured path.

## Independent aggregates that remain valid concepts

### METEO district
All-member category majority. Realized validated 49/49.

### Irrigation
Calibrated source-member fraction >0.37, then majority irrigation type among irrigated members.
0.37 confirmed calibrated by project owner. Preserve historical definition unless calibration provenance says otherwise.

### AREA
area_sum=sum(uopp) all HRU members.
areawb_sum=sum(uopp) selected water-balance members.
Keep support names explicit.

### BBC class and c1 mixed-boundary path
bbc_maj = category majority.
c1_avg = inverse(mean(1/c1)) within majority BBC class; bbc3weight proportional to 1/c1.
Mathematically coherent for parallel resistance. Separate from prescribed-flux QBOT2 membership issue.

### Coordinates
Legacy computes arithmetic centroid of source-cell centers, then snaps to nearest actual HRU member and exports that member's x/y/row/col.
This is a representative output/location convention, not Piet's hydrological representative SVAT.
Rename to display_anchor_svat/location to avoid authority confusion.

### hh_avg / glk_avg / GWLI
hh_avg and glk_avg are equal-member means over all HRU source cells.
GWLI = min(0, round((hh_avg-glk_avg)*100)).
This is a historical initial groundwater-level construction, not yet qualified scientifically. OPEN_SUPPORT_AUDIT: assess whether full-cell equal mean is intended and whether initial state should instead follow a coupled/representative state.

### infil_avg / SWALLO
infil_avg is equal-member mean over all source cells.
DRA output sets SWALLO=3 if:
- sy>3, OR
- INFRES>20000, OR
- infil_avg<10;
otherwise SWALLO=1.
The meaning/unit/support of source infil raster must be bound before modernization. OPEN_SEMANTIC_AUDIT.

## Comment/code mismatches

- irrigation comment says 30%; calibrated code is 37%. Documentation defect.
- drainage comment says resistance >5000 disables; active code threshold is >20000. This is a second stale-comment defect and must not be mistaken for model behavior.
- drainage comment says only water-balance cells; active code intentionally uses all members, confirmed by project owner.

## Schema-first dependency order

1. Piet HRU schema authority:
   representative_svat, representative soil/BFE, root depth, land use.
2. canonical soil lookup:
   bodem370 -> BOFEK79 -> PAWN21 -> grondsoort4 -> grondsoort2.
3. derive representation-dependent flags:
   SWETR, is_nature, crop ids, soil2.
4. independent spatial aggregations:
   meteo district, irrigation, uopp totals, drainage, BBC, display anchor, initial-state diagnostics.
5. producer-specific output records.
6. renderers only format.

No derived variable may be calculated from a provisional majority and survive an authority override.
