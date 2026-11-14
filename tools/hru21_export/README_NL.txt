LWKM HRU21 Export 1.0.0, Windows x64

1. Pak de programmamap LWKM_HRU21_Export uit onder LWKM_tools, naast
   LWKM_MetaSWAP_HRU_Windows_x64_1.0.0.
2. Open CMD in de uitgepakte programmamap en voer uit:
   run_hru21_export.cmd
3. Upload de nieuw gemaakte HRU21_export_....zip naar ChatGPT.

Andere locatie van de bestaande CSV-bestanden? Gebruik:
   run_hru21_export.cmd "G:\pad\naar\metaswap_hru_output"

Standaard worden alle 1980 kalenderdecades van 19700110 tot en met 20241231
verwacht. De CSV-bestanden worden alleen gelezen, niet opnieuw berekend.
Geen Python of installatie nodig. Windows PowerShell is nodig voor de ZIP.
Laat het bestaande MetaSWAP-exportprogramma eerst volledig afronden.

De 21 pilot-HRU's liggen vast in pilot-hrus.csv. Er worden geen nieuwe HRU's
of gebiedsgemiddelden gemaakt. Alle oorspronkelijke kolommen en numerieke
teksten blijven behouden, inclusief teken, lege velden en dekkingsgraden.

HRU21_reference.csv: gezamenlijke tabel met decade_end als eerste kolom.
reference/: afzonderlijke geselecteerde decadetabellen, bijbehorende nieuwe
hashmarkers en de steunoppervlakken van de 21 HRU's; geschikt voor de
bestaande ontvangstsoftware. source_markers/: oorspronkelijke markers en QC.
source_manifest.csv, source_hru_support.csv en source_run_identity.txt:
herkomst en controle over de volledige bronpopulatie.

Een ontbrekende decade, afwijkende hash of inconsistente tabel stopt de
export. Er wordt dan geen ZIP gemaakt. Een gedeeltelijke uitvoermap blijft
staan ter diagnose. Een volgende start gebruikt een nieuwe map. Bestaande
uitvoer wordt nooit overschreven. Onvolledige bronwaarden blijven leeg;
export_status.txt vermeldt het aantal onvolledige geselecteerde HRU-decades.
COMPLETE.txt betekent dat de bestandsexport voltooid is, geen wetenschappelijke
toelating. Oorspronkelijke rasterbestanden worden niet opnieuw gehasht.
Er is nog geen volledige 1970-2024 CSV-reeks lokaal ontvangen of gekalibreerd.

Beperkte periode voor een proef (beide grenzen zijn decade-einddatums):
   run_hru21_export.cmd "G:\pad\naar\metaswap_hru_output" 20241210 20241210
