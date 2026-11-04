# Frank MODFLOW v0.7: positieve DRN-budgetflux afkappen met audit

Projecteigenaarbesluit, 4 november 2026: DRN is fysisch uitsluitend ontwatering. Indien een origineel dagelijks DRN-IDF toch een positieve getekende celwaarde bevat, **registreer deze als anomalie, vervang door exact nul en verwerk de overige dagen door**. Niet stoppen. Geen positieve DRN als infiltratie classificeren.

Implementatie: `LWKM_Frank_LHM_Server_v07_DRN_POSITIEF_NUL.zip`, lokaal getest op synthetische dagelijkse fluxen, broncode in pakket, nog geen NHI-run geverifieerd.

- Per DRN-systeem en dag/cel voor accumulatie: `q_corrected=min(q_original,0)`, daarna `DRN_ontwatering=max(-q_corrected,0)`; `DRN_signed += q_corrected`.
- Audit met datum, DRN-systeem, aantal geraakte SVAT-rijen, aantal **unieke** MODFLOW-cellen, som positieve bronvolumes (zowel sampled SVATs als unieke cellen), maximum, eerste SVAT en rasterpositie. Audit-CSV in de outputdir; controleaggregaat in manifest en checkpoint.
- 4× RIV-ontwatering, 4× RIV-infiltratie, 3× DRN-ontwatering, FLF-kwel en FLF-wegzijging, netto LAT/WEL/GHB = 16 uitvoerfluxen; andere fysische fluxen niet veranderd.
- Cacheversie en outputdirectory specifiek v0.7: geen hergebruik van oude jaarresultaten zonder correcte audit.
- Synthetische regressietests: positieve DRN van 0.0003 m3/d leidt tot nul in netto én ontwatering, precies één audititem, replay over checkpoint correct; bestaande 16-veld- en MetaSWAP-test PASS.
- Voor wetenschappelijke beoordeling blijft bij grotere aantallen/volumes de positieve DRN-bronafwijking een openstaand modelgegevensprobleem, geen stilzwijgende correctie van bronbestand.

Gebruik CMD vanuit uitgepakte `LWKM_Frank_LHM_Server_v07` onder `LWKM_tools`: `CONTROLE_MODFLOW_2020.cmd` gevolgd door `START_MODFLOW_PROEF_2020.cmd`. De check-only controle valideert bronbeschikbaarheid, niet anomalie-waarden (die worden tijdens de run vastgesteld). Na controle klimaatrun.