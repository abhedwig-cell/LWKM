# Basis-cropfiles voor LWKM

Vastgelegd op verzoek van de projecteigenaar, 30 oktober 2026. Deze vier bestanden vormen de uitgangsversie voor het genereren en later per HRU kalibreren van cropfiles.

| lu / lu4 | Landgebruik | Basisbestand |
|---:|---|---|
| 1 | Grasland | [gras_maaien.crp](gras_maaien.crp) |
| 2 | Mais | [snijmais.crp](snijmais.crp) |
| 3 | Bouwland | [fictief.crp](fictief.crp) |
| 4 | Natuur | [gras_beweiding.crp](gras_beweiding.crp) |

Zie ook [de landgebruikafspraak](../../../docs/landgebruik.md).

## Herkomst en integriteit

Bron: `root.zip`, pad `root/Ab/Template/Gewas/`. De bestanden zijn byte voor byte overgenomen, inclusief oorspronkelijke regeleinden. De oudere bestanden onder `3.0.0/` zijn niet gebruikt.

| Bestand | SHA-256 |
|---|---|
| gras_maaien.crp | d2536bce068f0e7f5e2ad09f2998c82cceea8d83e8f30cdf35e457b4b68873fa |
| snijmais.crp | 7a31ec8eea38997dc72d12d95a9823b0658c5f1bb0586e01e09472efba7c5ebc |
| fictief.crp | b94676df6ac0a62e234f32939c31cb222dfafc94b72fa4fa35f096477b49d87e |
| gras_beweiding.crp | b3dd73b356ac577a814085c59c97d1efa7c4d92ff544febaee20cd625243af08 |

## Gebruik

Dit zijn templates; ze zijn nog niet allemaal zelfstandig uitvoerbaar. Bij generatie van een cropfile per HRU moeten de resterende templatevelden worden ingevuld en de volgende projectafspraken worden toegepast:

- `SCHEDULE = 1` als beregening aan de HRU is toegekend, anders `SCHEDULE = 0`.
- Een verwijzing naar het CO2-bestand toevoegen of het bestaande `ATMOFIL`-templateveld invullen. Het bronbestand `atmospheric_1975-2020.co2` bevat jaarlijks 360,80 ppm voor 1970 t/m 2025; de bestandsnaam geeft de dekking niet correct weer.
- Kalibratie vindt later plaats in afzonderlijke cropfiles per HRU, met herleidbaarheid naar deze basisversie.

Het vastleggen van deze bronbestanden verandert de generatieprocedure niet en vormt geen kwalificatie van een uitgevoerde SWAP-run.
