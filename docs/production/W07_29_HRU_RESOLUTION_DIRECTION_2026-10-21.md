# W07: 29 resterende drainage-HRU's, gerichte oplossingsroute

Datum 2026-10-21. Status: diagnose en uitvoeringseisen; geen automatische productietoelating.

Gebaseerd op de bestaande `docs/evidence/2026-10-19-work-c2/protected-partition-diagnostics.json` met exact 29 HRU's. Tien bevatten zes behouden fysieke systemen, negentien bevatten zeven. Alle 29 vereisen momenteel minimaal zes beschermde SWAP-niveaus binnen de bestaande mergepolicy.

## Verplichte oplossingsvolgorde
1. Reconstrueer voor ieder van 29 de afzonderlijke drainage- en infiltratiefluxrespons van alle fysieke systemen, met peilreferentie, `DEP`, seizoen-/H1-peilseries, DRARES, INFRES, SWALLO en gekwalificeerde HRU-grondwaterdiepten. **Een nul in H1 `summer/winter` mag niet als nulflux worden geïnterpreteerd zonder verificatie van de referentiebetekenis.**
2. Onderzoek eerst of de beperkingen op samenvoegen numeriek te streng zijn. Test alternatief vijf-niveaumodel over een expliciet grondwaterstandsbereik, bij alle seizoens- en peilmomenten. SWAP-niveaus kunnen niet tegelijk infiltrerende en drain-only bronnen exact reproduceren: gebruik daarom een gekwantificeerde afwijking in zowel drainage- als infiltratietak, geen stille bronverwijdering of klassewissel.
3. Houd PIPE en H1 als bronbijdrage herleidbaar. Ze hoeven niet zonder fysische onderbouwing een eigen SWAP-niveau te blijven als een bewezen equivalente gecombineerde respons bestaat; toets in dat geval expliciet SWDTYP, rapid/macropore semantiek en seizoensgedrag. Buisdrainage mag nooit met open kanaal vermengd worden als SWAP-semantiek dat verhindert.
4. Beoordeel optioneel het weglaten van een **zwakke fysieke bijdrage**, uitsluitend na het expliciete 2026-10-19-besluit DRARES>100000 voor automatische verwijdering. Een zwakke bijdrage met DRARES<=100000 vraagt nieuw afzonderlijk wetenschappelijk akkoord en een foutbudget dat gebaseerd is op daadwerkelijke fluxen/volumes. Geen stilzwijgende verruiming van bestaande beslissingen.
5. Vergelijk per HRU de berekende totale fluxen en componenten bij nat, gemiddeld en droog grondwater, dynamische peilen en de 1971-testforcing; waar mogelijk voer echte SWAP 4.3.1-modelruns uit.
6. Kies de kleinste fysisch onderbouwde wijziging, maak 29 DRA-kandidaten en laat bestaande 10213 bestanden ongewijzigd. Update source lineage, de numerieke effectcontrole, regressie en statusregister.

## Huidige evidence
Work C2 meldt 29 expliciete compressieblokkades na toepassing van INFRES>100000 zonder infiltratie, DRARES>100000 verwijderen en H1-factor ontbreekt=geen infiltratie. Bewaak die regels. De diagnostiek bevat bronpeilen, weerstand en klassen; er is nog geen wetenschappelijk gekwalificeerde vijf-niveauoplossing voor de 29. Er wordt dus niet geclaimd dat 10242 DRA's nu bruikbaar zijn.

## Acceptatie
Een 29/29 uitkomst vereist per HRU een uitgeschreven vijf-niveaucontract, nul verborgen actieve bronverwijderingen, numeriek beoordeelde fluximpact, geldige SWAP-parser/solvercompatibiliteit en echte gerichte modeluitvoering. Het sluiten van een blokkade in de selector alleen is onvoldoende.
