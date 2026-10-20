# Work B hervatting, 20 oktober 2026

Actuele D1-aanvulling: control_runs(2).zip is via de bestaande bestandsverwijzing succesvol verkregen; er is geen reupload gevraagd. De eerdere downloadblokkade hieronder is opgelost voor dit bestand. De raw-LHM/enrichment-gates worden daarmee niet zonder inhoudelijke toets gesloten. Work B is geïntegreerd in PR 11; zie het D1-herstelpunt.

De Work B-branch is samengevoegd met gezamenlijke basis `36c3dac01ccd66e2b58a250fce332df82b784fd6`. De vijfcomponentenroute en het eigenaarbesluit over dagelijkse BBC-timing blijven behouden. De samenvoeging heeft geen conflicten. Lokaal slagen 386 tests en drie subtests. Alle 65 hashes in het bestaande Work B-artifactmanifest en alle 23 codehashes zijn opnieuw gecontroleerd, zonder afwijkingen. De bestaande wetenschappelijke reconstructie en C2-modelberekeningen zijn niet opnieuw uitgevoerd.

De oude schema-copy-notitie bevatte nog een door de latere broncode-audit weerlegde interpretatie van `bfe_repr > 0`. Die tekst verwijst nu expliciet naar de actieve bronsemantiek. Dit verandert geen wetenschappelijk besluit of runwaarde. De verrijkte 43-kolomsvariant blijft onderscheiden van de gereproduceerde 36-kolomsclusterreferentie.

## Externe blokkade bij vervolgonderzoek

Het eerder aangeleverde `control_runs(2).zip` is opnieuw gevonden onder `/LWKM/control_runs(2).zip`, Library-identiteit `libfile_e9f81e9c948c81919f1a4593d483ae56`, omvang 223.897.827 bytes. Het bestand is dus niet als ontbrekend aangemerkt. Met de actuele Library-helper zijn twee downloadpogingen gedaan. Beide stoppen bij `hosted apps tools/list request failed with HTTP status 403`, voordat bestandsbytes worden geleverd. De lokale bronbestanden van de vorige sessie zijn niet meer aanwezig.

Daardoor is in deze hervatting geen nieuwe inhoudsinspectie van dit archief verricht en geen nieuwe BFE/soil2/rootzone-verrijking bewezen. Herstel van de geautoriseerde bestandsophaalroute is nodig om dit vervolgonderzoek uit te voeren; er is geen inhoudelijke reden voor opnieuw uploaden. De vier bestaande inhoudelijke gates blijven staan in `docs/evidence/2026-10-19-work-b/blocker-register.json`. Productie-admission blijft gesloten.

## Herstelpunt

Vervolg na herstel van toegang met de oorspronkelijke verrijkingsproducent en lookups. Gebruik het actuele `Datamodel_10242.xlsx` en de bestaande providercontracten; neem huidige runrijen niet zonder bewezen afhankelijkheden over voor gewijzigde HRU's. De bestaande full-source-replay hoeft alleen opnieuw wanneer inputs, code of vereiste runtime-identiteit veranderen. Deze hervatting is integratie- en regressie-evidence, geen nieuwe volledige bronreconstructie.
