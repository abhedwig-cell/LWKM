# LHM MetaSWAP: vastgesteld broncode-uitgangspunt

Besluit-ID: `LWKM-LHM-SOURCE-20261110-01`  
Status: **VASTGESTELD DOOR PROJECTEIGENAAR**  
Besluitdatum: 10 november 2026, 09:52:39 CET (`2026-11-10T08:52:39Z`)  
Opdracht tot duurzame vastlegging: 10 november 2026, 09:56:52 CET

## Besluit

**De op 10 november 2026 aangeleverde `IMODFLOW.ZIP` wordt binnen LWKM behandeld als de broncode waarmee de executable voor de betreffende LHM-run is gebouwd.** Deze broncode is daarmee het vastgestelde uitgangspunt voor de analyse van `qmodf`, de MetaSWAP-waterbalans en de aansluiting op de bestaande MODFLOW-fluxreconstructie.

De grondslag is de expliciete instructie van de projecteigenaar in de conversatie over de MetaSWAP-broncode. Dit is geen nog te bevestigen werkhypothese. De koppeling tussen deze broncode en de gebruikte LHM-executable is **geen open verificatievoorwaarde en geen blokkade voor verdere analyse**. Vraag hiervoor niet opnieuw om bevestiging, een executable, een buildlog of serverhandelingen.

Dit besluit vervangt de eerdere kanttekening in die conversatie dat eerst moest worden vastgesteld of de broncodeversie overeenkwam met de executable van de historische LHM-run.

## Reikwijdte

Het besluit geldt voor de betreffende LHM-run waarop de bestaande LWKM-analyse van `qmodf` en de waterbalans betrekking heeft. Het geldt niet automatisch voor andere LHM-runs of andere broncodeleveringen.

De identiteit van de broncode is hiermee vastgesteld als projectuitgangspunt. De volledige runconfiguratie, de daadwerkelijk geactiveerde codepaden en de betekenis van afzonderlijke uitvoerbestanden worden niet uitsluitend door dit besluit vastgesteld.

## Identiteit van het aangeleverde bestand

De onderstaande waarden zijn op 10 november 2026 rechtstreeks berekend uit de aangeleverde ZIP, zonder het archief te wijzigen.

| Eigenschap | Waarde |
|---|---|
| Bestandsnaam | `IMODFLOW.ZIP` |
| Omvang | `145878162` bytes |
| SHA-256 van de volledige ZIP | `9f50b09908a91cf2459899c128390dbff9bd4aa6f4cf84872a5537488ebb2ad9` |
| Hoofdmap in het archief | `IMODFLOW/` |
| Aantal archiefrecords, inclusief mappen | `5854` |
| Aantal bestanden, inclusief SVN-administratie en overige archiefinhoud | `5253` |

Aanvullende herkenningspunten voor de broncodeanalyse; hashes zijn berekend over de ongewijzigde bestandsbytes in de ZIP:

| Pad in het archief | SHA-256 |
|---|---|
| `IMODFLOW/modmsw/msw1/msw1postfm.for` | `f2f4218de0c5d8357828b8f1833d2378fe7f2214e6839160798b32924fe29480` |
| `IMODFLOW/modmsw/msw1/msw1bd.for` | `d9963c2238cb17bbfdf68a210c2b8e90b0ec8111e586df24309acedddd034046` |
| `IMODFLOW/modmsw/simgro/simgro.for` | `6a1d6268739e537c889ac8d9eb4bd25ecc2b47b29f86eb17dd9aff7093ab2b34` |

De hashes identificeren de aangeleverde bestanden. Zij zijn geen claim dat een onafhankelijke, bit-identieke herbouw van de executable is uitgevoerd. Zo'n herbouw is voor dit besluit niet vereist. Het broncodearchief zelf is met deze vastlegging niet naar deze repository geupload; de registratie is geen vervanging voor bewaring van het oorspronkelijke archief.

## Gevolgen voor vervolgwerk

1. Volg `qmodf` in deze broncode van berekening via eventuele correcties tot het wegschrijven naar de uitvoer die in LWKM wordt gebruikt. Leg de relevante routine, variabelen en voorwaarden vast.
2. Onderzoek de geactiveerde codepaden met de instellingen van de betreffende LHM-run. Houd interne waarden en daadwerkelijk geschreven uitvoervariabelen uit elkaar.
3. Leg eenheden, tekenconventies, SVAT- en MODFLOW-oppervlakken, tijdstappen, tijdsaggregatie, drainage en berging expliciet naast elkaar voordat balansen worden vergeleken.
4. Behoud de bestaande LWKM-reconstructie en eerder vastgelegde MODFLOW-tekenconventies als vertrekpunt. Dit besluit vervangt of wijzigt die reconstructie niet.
5. Behandel een gelijkstelling van `qmodf` aan een verticale onderflux of aan `Q_ext` niet als een gevolg van dit besluit. Een dergelijke relatie vereist een inhoudelijke afleiding en toetsing.

Deze vastlegging kwalificeert de eerdere voorlopige interpretaties van de code niet automatisch als bewezen en verklaart de waterbalans niet gesloten. Zij legt vast **welke broncode leidend is**, niet wat de uiteindelijke inhoudelijke uitkomst moet zijn.

## Overdracht en wijziging

Verwijs bij vervolgwerk in ChatGPT, Work, Codex en de productieketendocumentatie naar dit besluit-ID en de ZIP-hash. Registreer een eventuele latere wijziging als een nieuw, expliciet besluit met reden en verwijzing naar deze versie. Heropen de broncode-executablekoppeling niet stilzwijgend als algemene provenancevoorwaarde.
