# WB23 januari 2020: niet-sluitende SVAT's

Datum: 2026-11-03. Analyse lokaal uitgevoerd op de originele WB18 januaridecadebestanden en de WB22 maandelijkse SVAT-diagnose.

Balans: R0 = (bdgdecstot+bdgpm+bdgpssw+bdgpsgw+bdgetact+bdgqrun) + (QLAT+FLF+WEL+GHB+DRN+RIV). qmodf uitgesloten, STO apart getoetst. Volledige MODFLOW-celvolumes, niet oppervlakteschaling. 645574 toelaatbare SVATs.

| Klasse (abs fout <= 1m3/januari) | SVATs | som abs(R0) m3 |
|---|---:|---:|
| Alleen zonder STO | 586838 | 22200 |
| Zowel zonder als met STO | 6590 | 156 |
| Alleen met STO | 47029 | 14952061 |
| Geen van beide | 5117 | 1614915 |

Bij 47029 van de 52146 aanvankelijk niet-sluitende SVATs geldt R0 ≈ -STO. STO universeel toevoegen verslechtert totaal van 16.589 naar 288.293 miljoen m3 absolute SVAT-rest. Het blijkt dus niet verantwoord STO universeel als hulpterm weg te laten of altijd op te nemen. Wat precies de koppelboekhouding is, blijft onbewezen.

Bij 5117 overige SVATs toont de analyse per decade (grens 0.4m3) 2177 met patroon 222 (noch R0 noch R0+STO in alle drie), 1093 met 211 (in D2 en D3 sluit STO wel) en 490 met 221 (in D3 sluit STO wel). Bij afwijkende voorbeelden: SVAT428409 heeft R0 circa +8661.18, +8661.17 en +9527.25 m3 op 10,10,11 dagen, een dagconstante afwijking van circa 866 m3/dag. SVAT420920, 615346 en 286187 tonen eveneens dagen-evenredige resten, met Q4-componenten soms veel groter dan de onverzadigde-zone-termen.

De 784 SVATs met fraction_svat<1% van nominale 62500m2 sluiten vrijwel alle zonder STO; een algemene SVAT-area-schaling is geen oplossing voor de overige tekortkomingen.

Aanbevolen technische vervolgtoets: vergelijk bij 10-20 aanhoudende uitschieters de dagelijkse oorspronkelijke QLAT (FRF+FFF), FLF, WEL en GHB met de originele laag-1 celbudgetbalans en de oorspronkelijke dag-IDFs. Voor het STO-regime onderzoek naar koppeladministratie en gebieds-/celtypen, eventueel ruimtelijk plotten. Geen automatische wissel van STO per cel invoeren op basis van beste residu: dat zou cirkelredenering zijn.

Uitvoer en classificatie: `LWKM_WB23_Januari2020_NietSluitendeSVATs.zip` (door gebruiker te downloaden uit de conversatie).