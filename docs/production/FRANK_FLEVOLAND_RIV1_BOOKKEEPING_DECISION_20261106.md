# Definitief projecteigenaarbesluit: Flevoland FLF en RIV1 als boekhoudkundige correctie

Datum: 2026-11-06. De projecteigenaar bevestigt dat zowel de historische Flevoland-kwel/FLF-correctie als de gelijke, tegengestelde RIV1-aanpassing **boekhoudkundig** zijn. Het betreft **geen wijziging van de fysische MODFLOW-uitvoer**. Kleine omslagen van ontwatering naar infiltratie na de compensatie zijn toegestaan en worden niet op nul afgekapt.

## Getekende definitie

Positief = toevoer naar MODFLOW-laag 1; eenheden en ruimte-/tijdsupport vóór optellen expliciet gelijkmaken.

- `delta_flf = flf_corrected - flf_original`.
- `riv1_net_corrected = riv1_net_original - delta_flf`.
- Controle: `delta_flf + delta_riv1 = 0`.
- Na correctie `riv1_infil_corrected=max(riv1_net_corrected,0)`, `riv1_drain_corrected=max(-riv1_net_corrected,0)` voor een **langjarig gemiddelde getekende nettoflux**. Infiltratie/ontwatering omslag mag blijven bestaan.
- `Fldrou1 = RIV1_drain_corrected + RIV4_drain` en `Fldrin1 = RIV1_infil_corrected + RIV4_infil` uitsluitend in de als `BOOKKEEPING_CORRECTED` gemarkeerde weergave. RIV2/3 en DRN1/2/3 blijven ongewijzigd.
- Originele 16 MODFLOW-velden altijd behouden. Correctieveldsupport, delta, waarde vóór/na, switch-vlag en bronbestand in afzonderlijke tabel vastleggen.

**Essentiële beperking:** bruto 30-jaars ontwatering/infiltratie uit dagelijkse gesplitste RIV1-fluxen is niet terug te halen door enkel het 30-jaars nettoresultaat te splitsen. De max/min van langjarig netto is niet de som van dagelijkse max/min. De gecorrigeerde grootheden mogen derhalve nooit ongelabeld de dagelijkse bruto-historie vervangen. Voor een exacte correctie van dagelijkse bruto-ontwatering/infiltratie is een expliciete tijdsverdeling van de boekhoudkundige deltas nodig; die is hier niet voorgeschreven. Rapporteer de lange-termijn netto-gecorrigeerde componenten als afzonderlijke **net-split/bookkeeping** velden en verwar ze niet met de historische bruto-fluxen.

## Flevoland-support

Historiografie: `docs/lhm-hru-swap/flevoland-correction-design-note.md` noemt sparse corrected `kwel(mm/j)` vs original `kwel_org(mm/j)` op 4677 SVATs. Oude waterbalansoverdracht `docs/handoff/LWKM_WATERBALANS_WB5_HANDOFF_2026-10-14.md` noemt de RIV1-compensatie als afzonderlijke diagnosevariant, niet fysische run.

De Deltares-correctie is een langjarig gemiddelde op historische SVAT/actief-support. Huidige MODFLOW-FLF-v07 is celvolume op volledige MODFLOW-cel. **Niet** direct `delta_kwel_mm_y` bij `FLF_m3` optellen en dezelfde compensatie bij RIV1-m3 aftrekken voordat support is verenigd en de originele waarden zijn vergeleken.

Controle vereist: twee historische rasters of `SVAT_INFO_HRU` original/corrected kwel; 4677 affected SVATs in geselecteerde historische population; area-based volume diagnostics; semantiek/tekens/conversies; bronbestand-hashes; vergelijking oorspronkelijke kwel met v07 FLF. Geen directe bronoverschrijving. Bij onvoldoende identificatie eerst QA en afzonderlijke correctierelatie exporteren, geen misleidende complete netto-gecorrigeerde brute FLDROU-waarden.

Dit besluit vervangt eventuele eerdere suggesties om een omslag naar infiltratie niet toe te staan. Het verandert niet de mapping van vijf Frank-systemen uit `FRANK_FLDROU_SYSTEM_MAPPING_20261106.md`.
