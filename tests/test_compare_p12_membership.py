import csv
from pathlib import Path
from tools.compare_p12_membership import structural_audit,summary

def test_structural_audit(tmp_path:Path):
    p=tmp_path/"x.csv"
    with p.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["HRU","svat_orig","svat_donor","label"]); w.writeheader()
        w.writerows([
          {"HRU":1,"svat_orig":1,"svat_donor":1,"label":"valid"},
          {"HRU":1,"svat_orig":2,"svat_donor":1,"label":"Toegevoegd"},
          {"HRU":2,"svat_orig":3,"svat_donor":3,"label":"Restgroep"},
        ])
    rows=structural_audit(p); s=summary(rows)
    assert s["n_hrus"]==2
    assert s["n_changed_selection"]==1
    assert s["n_historical_fallback"]==1
    assert s["n_zero_corrected"]==0
