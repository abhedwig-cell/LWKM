# LWKM productieketen: architectuur en contracten

Actuele aanvulling: [Work C, uitvoering en kwalificatie](WORK_C_20261019.md). Onderstaande oorspronkelijke sessieresultaten blijven als historische context behouden.

Versie 19 oktober 2026. Operationele reconstructie met uitgevoerde kandidaatberekeningen; geen nieuwe integrale production admission.

De keten begint bij de expliciet gekozen LHM433-bronbestanden en eindigt bij een gecontroleerd SWAP-resultaat. De repository definieert de transformaties. De feitelijke bronbytes worden geïdentificeerd met SHA-256 en hun oorspronkelijke rol. Een teruggevonden historisch invoerbestand is bruikbaar als oracle, maar wordt daarmee geen moderne bron.

## Gegevens en verantwoordelijkheden

| Grens | Invoer | Uitvoer | Doorslaggevende controle |
|---|---|---|---|
| W01 | Deltares total-results tree en eigenaar-geleverde INI-bestanden | Consumentgebonden Q4-bronset | Identiteit, volledigheid, herextractie |
| W02 | Geselecteerde budgetten, toestanden en schematisatie | Afgeleide rasters | Geometrie, NODATA, eenheden, golden comparison |
| W03-W05 | SVAT-attributen, selectie, donorregels | HRU-membership en representanten | Unieke leden, herhaalbaarheid, oppervlaksluiting |
| W06 | Datamodel en lookups | Typed contexten | Verplichte joins en velden |
| W07 | Zeven fysieke ontwateringssystemen | Maximaal vijf SWAP-niveaus | Behoud conductantie, bronlineage en hydraulische klassen |
| W08 | Expliciet gekozen BBC-formulering | Onderrandbestand | Teken, support, kalender en parser |
| W09-W10 | Meteobronnen, context en versieprofiel | MET en SWP | Eenheden, tijdsdekking, alle actieve velden |
| W11 | Gekwalificeerde assets | Immutable runpakket | Bestandsreferenties en hashes |
| W12-W14 | Runpakketten en gepinde executable | Resultaten en admission evidence | Werkelijke uitvoering, kalender, balans en regressie |

Zes werkstromen A-F en hun interfaces staan machineleesbaar in `config/governance/lwkm-production-status-20261019.json`. De huidige implementaties raken dezelfde generator- en uitvoeringsinterfaces en zijn daarom op één afzonderlijke integratiewerkbranch samengebracht. Er zijn geen conflicterende parallelle productiewijzigingen gestart.

## Ruimtelijke support

Een HRU representeert een verzameling cellen. Deze verzameling hoeft niet aaneengesloten te zijn. De fysieke support hangt af van de grootheid. De uitgevoerde SVAT-selectie vertegenwoordigt 25.511.141.709 m2 actieve oppervlakte. Dat oppervlak mag niet automatisch worden gebruikt voor een MODFLOW-volumebalans die volledige cellen van 62.500 m2 representeert. Evenmin mag donorvervanging het oppervlak dubbel tellen.

De nieuwe grondwateraggregator accepteert voorlopig uitsluitend unieke, volledige MODFLOW-cellen die elk aan precies één HRU zijn toegewezen. Fractionele of overlappende toewijzing wordt geweigerd. Dat is een bewuste grens van de implementatie, totdat een onderbouwd verdelingscontract beschikbaar is.

## W08 en W08-GW-L1

W08 blijft de BBC-werkstroom. W08-GW-L1 is een subwerkstroom voor de effectieve overige grondwaterrandvoorwaarde:

`Q_ext = Q_FLF + Q_LAT + Q_GHB + Q_WEL`.

Alle componenten worden eerst per dag en cel genormaliseerd naar positief bij toevoer aan laag 1. Daarna wordt over de HRU-celverzameling gesommeerd. Bij consistente faceboekhouding valt intern lateraal transport weg. De omrekening luidt `q_mm_d = 1000 * Q_m3_d / A_m2`.

De implementatie bewaart per component bruto instroom, bruto uitstroom, netto volume en netto mm/d. MetaSWAP-uitwisseling, bergingsverandering en RIV/DRN zitten niet in deze som. De SWAP-kolom representeert in deze constructie laag 1. De omzetting is een equivalente volumebalans; zij bewijst niet dat laterale flux fysisch verticaal is.

De eerder gekozen qq-BBC, `100 * mean((head_l2-head_l1)/c1)` in cm/d, blijft een afzonderlijke route. Beide formuleringen mogen niet worden opgeteld. Ook is een tabel van dagelijkse gemiddelde fluxen nog niet automatisch een gekwalificeerde SWAP-tijdfunctie: dagstempeling en interpolatie moeten aan de parser worden getoetst.

## Moderne SWP-route

De huidige Template/wwl.swp wordt aan zijn exacte hash gebonden. De nieuwe adapter is een afzonderlijk modern kandidaatprofiel en claimt geen reconstructie van het ontbrekende historische swap_wwl.swp. Hij maakt tabelkoppen, hydraulische ELAS, reële getaltypen, bestandsreferenties, SWETR en SWDIVIDE expliciet.

Voor de technische demonstratie zijn LAT=52.1, ALT=1.9, ALTW=10 en DTMAX=0.04 overgenomen uit het historische voorbeeld. Deze vaste instellingen zijn nog geen ruimtelijk gekwalificeerde productieparameterisatie voor heel Nederland. Uitvoerbeleid gebruikt WATBAL, ETTERMS en GWL. Het in het werkboek gevraagde VOLACT wordt door de geleverde executable niet herkend.

De builder schrijft alleen gewijzigde SWP-bytes opnieuw. Elke kandidaatdirectory behoudt een expliciete incomplete-pakketstatus. De bestaande W11-assembler blijft verantwoordelijk voor echte pakketvorming, inclusief alle verplichte nevenbestanden. De huidige bestandsreferentiecontrole is een gerichte preflight en geen volledige SWAP-parser.

## Uitvoering en kwalificatie

De geleverde Linux SWAP 4.3.1-binary is gepind op SHA-256 `e3b45c1fe66a614c1caead4b2fc0684a09165672a32d8d3bf4eac00498767862`. Zijn bronprogramma roept bij normale voltooiing expliciet Exit(100) aan. Een exitcode nul alleen is dus geen bewijs van succes. De runner vereist normale voltooiing en parseerbare, eindige dagelijkse uitvoer. Productiekwalificatie vraagt daarnaast expliciete invoer-admission, volledige tijdsdekking en fysische toetsing.

De recursive W00-gate controleert status, consument, identiteit, bronbewijs en ouderbestanden. Hij is geïmplementeerd en getest, maar nog niet in iedere bestaande productie-ingang afgedwongen. Daarom blijft W00 als volledige ketengate open.

## Historische en moderne routes

Historische equivalentie en moderne fysische geschiktheid hebben afzonderlijke gates. Onverklaarde verschillen blijven zichtbaar. Moderne ontwikkeling mag een eigen versieprofiel gebruiken en onderzoek uitvoeren met expliciet geclassificeerde bronbestanden, maar mag die uitkomsten niet stilzwijgend als admitted produceren.

Voor het moderne pakketprofiel is de betekenis van bestandsstammen expliciet: DRFIL krijgt .dra en BBCFIL krijgt .bbc; METFIL bevat de extensie zelf. Dit gebeurt via een versiegebonden extensiebeleid, niet door willekeurige bestandszoekacties.
