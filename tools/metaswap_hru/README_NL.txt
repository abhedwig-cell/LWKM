LWKM MetaSWAP naar HRU, versie 1.0.0
===================================

INSTALLEREN EN STARTEN
Pak de INHOUD van deze ZIP uit in:
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools
De EXE en run_metaswap_hru.cmd moeten direct naast elkaar staan.
De submap data bevat alle benodigde SVAT-invoer; niets opnieuw downloaden.

Open een CMD-venster in die directory en voer uit:

run_metaswap_hru.cmd

Of open CMD elders en voer eerst uit:
cd /d "G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_tools"
run_metaswap_hru.cmd

Geen Python, compiler, PowerShell-script of aanvullende VC++-runtime nodig.
Bestemd voor 64-bit Windows, Windows 10/11 of Server 2016 en nieuwer.
Dit is een gekozen ondersteuningsdoel; niet elke Windows-versie is getest.

Bronmap (standaard, al ingesteld in CMD):
G:\Projecten\2025\Release_LHM433\modelruns\runs_LWKM\LWKM_run_resultaten_totaal\metaswap

Alle uitvoer komt in metaswap_hru_output naast het CMD-bestand.
Bij een andere bronlocatie kan zonder broncodewijziging eerst:
set "LWKM_MSW_ROOT=D:\andere\metaswap"
run_metaswap_hru.cmd

BEREIK
sources.csv bindt de aangeleverde inventaris: 1.980 opeenvolgende decades,
januari 1970 t/m december 2024, 17.820 bron-IDF's, negen per decade.
Area-/partitiebestanden uit de inventaris zijn geen tijdstappen en tellen niet mee.
Alle 10.242 HRU's krijgen een regel per decade: 20.279.160 resultaatregels.
De gebruiker hoeft geen sources.csv of rij-/kolomkoppeling te maken.
Nieuwe jaren na 2024 vereisen een opnieuw geïnventariseerd sources.csv.

RUIMTE EN VOORTGANG
Reserveer praktisch ten minste 10 GB vrije uitvoerruimte; de exacte grootte
hangt af van de waarden. Elke oorspronkelijke IDF is circa 5,4 MB. De gehele
bronreeks omvat circa 96 GB. Hashen en uitlezen veroorzaken extra I/O.
De console meldt per decade de voortgang en aantallen onvolledige HRU's.
Een echte productiedoorlooptijd is zonder toegang tot de server niet gemeten.
Er draait één proces; rasters worden één voor één ingelezen.

KOPPELING EN GEWICHTEN
427.656 originele SVAT's uit de aangeleverde SVAT-HRU-tabel; alle aanwezig
in area_svat.inp, zonder coördinaatverschillen. De volledige area_svat-bron
heeft 645.582 records; niet-geselecteerde SVAT's tellen niet mee.
De donor-SVAT is geen vervanger voor de ruimtelijke hydrologische support.
Per geselecteerde originele SVAT wordt het werkelijke oppervlak uit kolom 2
gebruikt, met X/Y uit kolommen 10/11 van de 14-veldenbron.
Per IDF wordt zelfstandig gecontroleerd:
col = floor((X-xmin)/dx); row = floor((ymax-Y)/dy).
Rijen lopen van noord naar zuid; indexen zijn nulgebaseerd. Het SVAT-punt
moet op het celcentrum liggen en binnen de rastergrenzen vallen.
Meerdere SVAT's in één cel zijn toegestaan en blijven afzonderlijk gewogen.

HRU-waarde = 1000 * som(SVAT-oppervlak * IDF-waarde) / som(SVAT-oppervlak).
De noemer is het geselecteerde SVAT-oppervlak, niet aantal cellen * 62.500 m2.

EENHEDEN, TEKENS EN FORMULES
De projecteigenaar geeft m3/m2 op SVAT-oppervlak als broneenheid.
Het ingestelde contract is een hoeveelheid per decade: maal 1000 levert
mm per decade. Er wordt NIET nogmaals met het aantal dagen vermenigvuldigd.
De datum in de bestandsnaam is het einde van de decade (10, 20, maandultimo).
De laatste decade heeft 8, 9, 10 of 11 dagen. Voor mm/dag: deel door days.

Alle negen originele variabelen blijven bewaard met hun oorspronkelijke teken:
MSW_EBS, MSW_EIC, MSW_EPD, MSW_ESP, MSW_TACT, MSW_TPOT, PSSW, PSGW, BDGETACT.
Ook de afgeleide termen behouden de algebraïsche brontekens:
E_SOIL_POND = MSW_EBS + MSW_EPD (bodem plus plaswater)
E_INTERCEPTION_SPRINKLING = MSW_EIC + MSW_ESP (interceptie plus beregeningsverdamping)
T_ACTUAL = MSW_TACT (expliciete derde component, kopie van originele transpiratie)
ET_ACTUAL = E_SOIL_POND + E_INTERCEPTION_SPRINKLING + T_ACTUAL
IRR_TOTAL = PSSW + PSGW
BDGETACT_MINUS_ET = BDGETACT - ET_ACTUAL

Esp betekent sprinkling evaporation, niet sneeuwsublimatie. De groepering
Eic+Esp is een expliciete rapportagekeuze; de originele termen blijven apart.
De MetaSWAP-budgetconventie kent negatieve ET en positieve beregening.
De code draait tekens niet automatisch om en gebruikt geen absolute waarden.
Een negatieve ET_ACTUAL is dus geen rekenfout. Een positieve consumptie wordt
bij dat broncontract verkregen als -ET_ACTUAL. Het verschil met BDGETACT
wordt niet weg-gecorrigeerd; afwijkende bronconventies blijven zichtbaar.
*_qc.csv telt positieve/negatieve SVAT-waarden per variabele.

Bron voor begrippen en budgettekens: MetaSWAP Report 913.3 V8.1.1.4,
tabel met waterbalansvariabelen, gedrukte pagina 73:
https://nhi.nu/documents/49/MetaSWAP_Report_913_3_V8.1.1.4.pdf
De m3/m2-keuze en decadische hoeveelheid in dit pakket volgen de aangeleverde
projectinstructie. De IDF-bestandsnaam alleen bewijst die semantiek niet.

ONTBREKENDE WAARDEN
NoData, NaN en oneindige waarden worden niet op nul gezet.
Een originele HRU-variabele blijft leeg zodra één geselecteerde SVAT daarvoor
geen geldige waarde heeft. De noemer wordt niet verkleind tot geldige pixels.
coverage_VARIABELE geeft het geldige oppervlak gedeeld door het totale
HRU-oppervlak. complete=1 alleen als alle negen variabelen volledig zijn.
Een afgeleide term vereist uitsluitend zijn eigen geldige bronvariabelen;
andere geldige termen blijven zichtbaar. Een numerieke nul blijft een nul.
Ontbrekende bestanden, dubbele SVAT's, ongeldige geometrie of ontbrekende
variabelen stoppen met een foutmelding en een niet-nul exitcode.
Onvolledige HRU-waarden door NoData geven geldige CSV's met complete=0;
een succesvolle procesexit is dus geen verklaring dat alle HRU's compleet zijn.

HERSTART EN IDENTITEIT
Start na onderbreken hetzelfde CMD opnieuw. Elke decade heeft een CSV,
een kwaliteitsbestand en een .sha256-controlebestand. Een resultaat wordt
alleen overgeslagen als de SHA-256 van EXE, beide SVAT-bestanden, sources.csv,
alle negen bron-IDF's, resultaat en kwaliteitsbestand overeenkomen.
Ontbrekende of gewijzigde resultaten worden opnieuw berekend.
Wijzigingen in gedeelde configuratie/membership/EXE maken alle decades ongeldig.
Ook bij herstart worden de bronbestanden volledig gehasht; dat kost I/O.
Een .partial-bestand is geen voltooid resultaat en mag blijven staan.
De exclusieve Windows-bestandslock vervalt automatisch bij procesbeëindiging;
twee processen kunnen niet tegelijk dezelfde uitvoermap gebruiken.
Wijzig bronbestanden niet tijdens een run. Grootte/mtime worden na uitlezen
nogmaals gecontroleerd; dit is geen snapshot van gelijktijdig wijzigende bronnen.

UITVOER
YYYYMMDD.csv: 10.242 HRU-regels; kolommen zoals hierboven; alle watertermen mm/decade.
YYYYMMDD_qc.csv: positieve en negatieve SVAT-waarden, per variabele.
YYYYMMDD.sha256: code/config/source/output-identiteiten.
hru_support.csv: aantal SVAT's en werkelijk oppervlak per HRU.
run_identity.txt: code- en configuratiehashes, eenhedencontract.
run.log: voortgang, onvolledige HRU-aantallen en fouten, aangevuld bij herstart.
SHA256SUMS.txt in het pakket identificeert de geleverde bestanden.

data/ bevat de volledige originele area_svat en SVAT-HRU-bestanden onder
praktische vaste namen. Hun hashes corresponderen met de aangeleverde bytes.
De tests gebruiken daarnaast een compacte, herleidbare extractie van de
benodigde velden van alle 427.656 geselecteerde SVAT's; niet donor-gemiddelden.

TEST EN GRENZEN
Zie evidence/test_results.json en evidence/WINDOWS_QUALIFICATION.txt voor de
werkelijk uitgevoerde binaire Windows-test en de geteste executable-hash.
Synthetische IDF's testen de rekenlogica, coördinaten, weging, ontbrekende
waarden en herstart. De volledige aangeleverde membership wordt daarbij
tegen onafhankelijk berekende HRU-uitkomsten gecontroleerd.
De echte 17.820 bron-IDF's staan alleen op de NHI-server en zijn hier niet
uitgevoerd. Dit pakket claimt geen voltooide echte productierun of wetenschappelijke
toelating van alle resultaten vóór inspectie van de serveruitvoer.
De IDF-reader is afgeleid van de bestaande C++-reader en de repositoryreader.
Ondersteund: 1271 single precision, equidistante grids, optioneel top/bottom
header en gekwalificeerde tekstfooter. Andere IDF-varianten stoppen expliciet.
