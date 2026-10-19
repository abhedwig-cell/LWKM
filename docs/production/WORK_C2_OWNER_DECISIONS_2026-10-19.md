# LWKM Work C2: definitieve projecteigenaarbesluiten drainage, H1 en tulp

Datum: 2026-10-19
Status: inhoudelijk ontwerpbesluit; implementatie en kwalificatie open.
Dit document vervangt eerdere mondelinge DRARES-afkapregels, waaronder 1000000 dagen, en voorkomt toepassing van een tussencategorie.

## Regels
- **DRARES > 100000 dagen:** laat de betrokken fysische drainagebijdrage/het drainagerecord weg uit de uiteindelijke SWAP-representatie. **Niet begrenzen op 100000 dagen.** De weerstand is zo hoog dat uitwisseling verwaarloosbaar wordt geacht. Bewaar origineel, herkomst en weglatingsreden in diagnostiek. Laat nooit een gecomprimeerd niveau met andere actieve bijdragen geheel vervallen: verwijder uitsluitend de betreffende fysische bijdrage en herbereken/hercomprimeer desnoods.
- **INFRES > 100000 dagen:** gebruik de SWAP-optie *geen infiltratie mogelijk* voor dit drainageniveau; bepaal de exacte SWAP 4.3.1-interface- en solversemantiek vóór serialisatie. Niet enkel afkappen op 100000.
- **H1 ontbrekende infiltratiefactor:** interpreteer als *geen infiltratie mogelijk*. Een eventuele drainagefunctie blijft behouden. Maak de toepassing op betrokken cellen en HRU's herleidbaar.
- **Tulp:** sta een expliciet modern Penman-Monteith-profiel toe waar de oorspronkelijke CF voor ETref ontbreekt. Geen claim van historische CF-equivalentie.

## Drempels en testen
Strikt groter dan 100000; exact 100000 valt niet onder de weglating of infiltratie-uitschakelregel. Niet-positieve, niet-eindige of anderszins ongeldige waarden blijven fouten tenzij SWAP-broncode expliciet een andere semantiek onderbouwt.

Voer na implementatie opnieuw de volledige 10242-HRU-diagnostiek en de relevante echte SWAP 4.3.1-regressies uit. Bewaar aantallen verwijderde bijdragen, gevolgen voor conductanties en hydraulische respons, originele bronnen, gewijzigde packages, fouten en een nieuwe blockerclassificatie. Geen production admission zonder kwalificatie.
