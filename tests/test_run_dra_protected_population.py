import json
from tools.run_dra_protected_population import run

def system(name,level):
    cls=("drain_only_open" if name in ("MVG","OLF") else
         "pipe" if name=="PIPE" else "infiltration_capable_open")
    return {"source_id":name,"hydraulic_class":cls,
            "medium":"drain_tube" if name=="PIPE" else "open_channel",
            "drainage_conductance":.1,
            "infiltration_conductance":.05 if name in ("P","S","T","H1") else 0.,
            "dep":level,"peil_sum":level,"peil_win":level,"dd":40.}

def test_arbitrary_hru_ids_and_reordering(tmp_path):
    data={"schema_version":1,"hrus":[
        {"hru":"other-99","systems":[system("P",1)]},
        {"hru":"x-3","systems":[system("S",2),system("T",2)]}]}
    source=tmp_path/"source.json"; source.write_text(json.dumps(data))
    first=run(source,tmp_path/"output")
    assert first["status"]=="QUALIFICATION_PASS"
    assert first["hru_count"]==2
    data["hrus"].reverse()
    data["hrus"][0]["systems"].reverse()
    source.write_text(json.dumps(data))
    second=run(source,tmp_path/"output")
    assert [r["fingerprint"] for r in first["results"]]==[
        r["fingerprint"] for r in second["results"]]

def test_failed_hru_blocks_qualification(tmp_path):
    data={"schema_version":1,"hrus":[
        {"hru":17,"systems":[system("P",1)]},
        {"hru":18,"systems":[{"source_id":"S"}]}]}
    source=tmp_path/"source.json";source.write_text(json.dumps(data))
    result=run(source,tmp_path/"out")
    assert result["status"]=="QUALIFICATION_FAIL"
    assert result["failed_hru_count"]==1
    assert len(result["results"])==2

def test_change_invalidates_one_fingerprint(tmp_path):
    data={"schema_version":1,"hrus":[
        {"hru":"a","systems":[system("P",1)]},
        {"hru":"b","systems":[system("P",2)]}]}
    source=tmp_path/"source.json";source.write_text(json.dumps(data))
    first=run(source,tmp_path/"out")
    data["hrus"][1]["systems"][0]["peil_sum"]=3
    source.write_text(json.dumps(data))
    second=run(source,tmp_path/"out")
    assert first["results"][0]["fingerprint"]==second["results"][0]["fingerprint"]
    assert first["results"][1]["fingerprint"]!=second["results"][1]["fingerprint"]
