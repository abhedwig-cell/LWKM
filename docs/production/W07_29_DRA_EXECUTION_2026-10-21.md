# W07 uitvoerpad voor de 29 resterende DRA's

De C2-bronbestanden zijn groot. Het in Git aanwezige `protected-partition-diagnostics.json` mist expliciete H1-maandpeilen, `DEP` en `DD`; gebruik dus de **volledige C2-checkpoints** (de lokale uitgepakte `drainage-checkpoints.jsonl.gz` of reeds bestaande map `<C2-drainage>/hrus/*.json`).

De daadwerkelijke DRA-renderer is `tools.generate_dra.render_dra_explicit`, dezelfde als in `tools/build_owner_dra_population.py`.

Run op de omgeving waarin de Work C2-artifacts werkelijk zijn uitgepakt (Python is daarvoor nodig; voer deze stap niet rechtstreeks uit op de NHI-server zonder interpreter):

```powershell
python -m tools.w07_build_29_dra --checkpoints <C2-drainage-root> --swps <C2-SWP-root> --old-dra <C2-DRA-root> --output <NEW-W07-DRA-root>
```

De bronmap met 10213 eerdere geldige DRA's wordt alleen gelezen; alle nieuw gegenereerde bytes gaan in de andere doelmap. De uitvoer registreert per HRU oorspronkelijke checkpoint- en SWP-identiteiten, alle niveaus, gebruikte benadering en hash.

Afsluiting vereist **echte 29/29 DRA-serialisatie** en daarna SWAP 4.3.1-executies plus onafhankelijke flux- en waterbalanscontrole. Dit is nog niet aangetoond. De code heeft geen brondata, foutmarges of admission-status verzonnen.

De selector is ook via `python -m tools.run_dra_protected_population --auto-five ...` beschikbaar voor een reeds samengesteld JSON-document met volledige fysieke systemen; die route levert voorlopig renderer-input-JSON, geen definitieve DRA's.
