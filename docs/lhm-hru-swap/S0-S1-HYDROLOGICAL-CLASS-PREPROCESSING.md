# Hydrological class and fuzzy preprocessing

Two different classification families exist and must not be conflated.

## Discrete grid2class products

grid2class applies ordered lookup-table ranges; values outside the table become NoData and overlapping ranges are resolved by the last matching row.

Recovered producers include:
- ghg_lb + gxg2class.csv -> ghg_class.asc
- glg_lb + gxg2class.csv -> glg_class.asc
- dynamiek_lb + dyn2class.csv -> dynamiek_class.asc
- wegzijging + flux2class.csv -> wegzijging_class.asc
- buisdrainage + flux2class.csv -> buisdrainage_class.asc
- runoff + roff2class.csv -> runoff_class.asc
- kwel + flux2class.csv -> kwel_class.asc
- rivdrn_netto + flux2class.csv -> rivdrn_class.asc
- kwelwegz_mmd + kwelflux2class.csv -> kwelwegz_class.asc
- bdgrivdrn_net_l1_sum + ontw2class.csv -> bdgrivdrn_net_class.asc

These class grids mainly support historical diagnostics and suspicious-cell selection blocks. They are not automatically identical to the fuzzy-scale columns exported to SVAT_INFO.

## Fuzzy grid2scale products consumed by LWKM_makeHRU

- ghg -> ghg2fuzzy.csv -> ghg_fuzzyclass.asc -> ghg(scale)
- glg -> glg2fuzzy.csv -> glg_fuzzyclass.asc -> glg(scale)
- kwelwegz_mmd -> kwelmmd2fuzzy.csv -> kwel_fuzzyclass.asc -> kwelwegz(scale)
- rivdrn_netto_sum -> ontw2fuzzy.csv -> bdgrivdrn_net_fuzzyclass.asc -> summer discharge scale/class chain
- qlatwb_mmd -> kwelmmd2fuzzy.csv -> qlat_fuzzyclass.asc -> qlat(scale)

The actual lookup CSV bytes remain an input dependency. Producer identity and lookup filenames are reconstructed; exact class boundaries require those lookup files or regression against realized outputs.

## Canonical target

Implement range/fuzzy transforms directly on tabular SVAT variables. Do not persist intermediate ASCII class rasters unless needed for spatial QA/export. Preserve lookup tables as versioned data assets.
