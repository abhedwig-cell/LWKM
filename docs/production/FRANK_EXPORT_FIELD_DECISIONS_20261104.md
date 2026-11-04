# Frank-export: aanvullende veldbesluiten 4 november 2026

Projecteigenaar bevestigt in chat:
- `Infiltratie`: eerdere suggestie over infiltratie aanvaard. **De exacte bron/eenduidige definitie moet nog gecontroleerd worden**. In de bestaande 75-kolomsschema's verwijst de historische header `wegzijgingz(mm/j)` naar `Riv_infiltratie_1991-2020_sum.asc`, dus *rivierinfiltratie-indicator* en niet zonder meer algemene infiltratie. Behandel dit als voorstel, niet als bevestiging van een technisch broncontract.
- `Fldrin345`: som van `aanvoer_sys3(mm/j)` t/m `aanvoer_sys5(mm/j)`, bevestigd.
- `GG`: **gemiddelde grondwaterstand**, bevestigd. Niet gelijkstellen aan `(GHG+GLG)/2` zonder aanvullende onderbouwing. Alleen invullen vanuit een expliciete GG-bron in eenheden ten opzichte van maaiveld; anders leeg met verklaring.
- `Dynamiek`: verschil tussen GLG en GHG, bevestigd. Wanneer beide als diepte in cm onder maaiveld zijn uitgedrukt: `GLG - GHG` (cm), doorgaans positief, mits dezelfde periode en conventie.
- `Indicator vervangen Svats`, `N ???` en overige onzekere semantiek blijven open voor overleg met Frank en Leo; **geen gefingeerde waarden**.

Deze notitie vult `FRANK_STAGE_COMPARISON_EXPORT_CONTRACT_20261104.md` aan. Bestaande v0.1-prototype-export is niet bewezen hierop bijgewerkt; een configuratieversie en regresstest zijn nodig vóór echte export.
