from pathlib import Path
from tools.lhm_run_chain_provenance import parse,compare_controls
def test_alias_resolution(tmp_path):
    p=tmp_path/"a.ini"
    p.write_text("%model% = e:\\LHM\n%data% = %(%model%)s\\Data\nc1 = %(%data%)s\\c.idf\n")
    d={x.key:x.resolved for x in parse(p)}
    assert d["c1"]=="e:\\LHM\\Data\\c.idf"
def test_stable_vs_varying(tmp_path):
    a=tmp_path/"a.ini"; b=tmp_path/"b.ini"
    a.write_text("x = same\ny = one\n"); b.write_text("x = same\ny = two\n")
    r=compare_controls([a,b])
    assert "x" in r["stable"] and "y" in r["varying"]
