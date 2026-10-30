# Landgebruik voor SWAP

Projecteigenaarbesluit van 30 oktober 2026.

Voor de HRU's geldt de volgende vierklassenindeling. `lu` verwijst hier naar `lu4`, niet naar `landgebruik22` of het historische veld `lu_id` in het datamodel.

| lu / lu4 | Landgebruik | Cropfile-template |
|---:|---|---|
| 1 | Grasland | `gras_maaien.crp` |
| 2 | Mais | `snijmais.crp` |
| 3 | Bouwland | `fictief.crp` |
| 4 | Natuur | `gras_beweiding.crp` |

Deze indeling is leidend voor de toewijzing van de vier cropfiles aan HRU's. De bestandsnaam `gras_beweiding.crp` verandert de betekenis van klasse 4 niet: die klasse is natuur.

## Controle van de gekoppelde populatie

`lu4 = 5` mag niet voorkomen bij SVAT's die aan een HRU gekoppeld zijn. Een dergelijke koppeling moet worden gerapporteerd en onderzocht; de klasse mag niet stilzwijgend worden omgezet of de koppeling verwijderd.

Controle van `export_svat_HRU_NRU_10242(5).csv` op 30 oktober 2026: 427.656 unieke oorspronkelijke SVAT's zijn gekoppeld aan 10.242 HRU's. Zowel `lu4_orig` als `lu4_donor` bevat uitsluitend waarden 1 t/m 4; klasse 5 komt niet voor.

| lu4_orig | Aantal gekoppelde oorspronkelijke SVAT's |
|---:|---:|
| 1 | 182.969 |
| 2 | 43.641 |
| 3 | 101.014 |
| 4 | 100.032 |
| Totaal | 427.656 |

De controle betreft deze exportversie. `SVAT_INFO.CSV` uit `root.zip` sluit niet volledig op deze export aan en mag niet zonder aanvullende afstemming als vervangende bron voor de gewastoewijzing worden gebruikt.
