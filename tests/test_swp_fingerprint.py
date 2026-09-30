from copy import deepcopy

from tools.swp_fingerprint import dependency_fingerprints, changed_dependencies


def _ctx():
    return {
        "run_id":2000,
        "run":{
            "soil_id":3015,
            "crop_id":1,
            "croporg_id":1,
            "rotation_id":"max",
        },
        "TSTART":"1971-01-01",
        "TEND":"2021-12-31",
        "PONDMX":0.2,
        "RSRO":0.25,
        "NUMNODNEW":43,
        "DZNEW":"5.0 5.0",
        "INLIST_CSV":"'VOLACT,GWL,WATBAL'",
        "METFIL":"'2000.met'",
        "SWETR":0,
        "TABLE_CROPROTATION":[{"CROPSTART":"1970-01-01","CROPEND":"1970-12-31","CROPNAME":"'gras'","CROPFIL":"'gras'","CROPTYPE":2}],
        "SWINCO":2,
        "GWLI":-47.0,
        "TABLE_SOILPROFILE":[{"ISUBLAY":1,"ISOILLAY":1,"HSUBLAY":25.0,"NCOMP":25}],
        "TABLE_SOILHYDRFUNC":[{"ORES":0.02,"ELAS":1e-6}],
        "TABLE_SOILTEXTURES":[{"PSAND":0.87,"PSILT":0.10,"PCLAY":0.03,"ORGMAT":0.057}],
        "RDS_effective":40.0,
        "RSOIL":600.0,
        "SWDRA":1,
        "DRFIL":"'2000'",
        "SWBBCFILE":1,
        "SWBOTB":2,
        "BBCFIL":"'2000'",
    }


def _changed(mutator):
    before=dependency_fingerprints(_ctx())
    after_ctx=deepcopy(_ctx())
    mutator(after_ctx)
    after=dependency_fingerprints(after_ctx)
    return changed_dependencies(before,after)


def test_meteo_reference_and_swetr_invalidate_forcing():
    assert _changed(lambda c:c.__setitem__("METFIL","'2001.met'"))==["forcing_ref"]
    assert _changed(lambda c:c.__setitem__("SWETR",1))==["forcing_ref"]


def test_crop_rotation_is_separate_dependency():
    assert _changed(lambda c:c["TABLE_CROPROTATION"][0].__setitem__("CROPFIL","'mais'"))==["crop_rotation"]


def test_bbc_and_dra_references_invalidate_their_classes():
    assert _changed(lambda c:c.__setitem__("BBCFIL","'2001'"))==["bottom_ref"]
    assert _changed(lambda c:c.__setitem__("DRFIL","'2001'"))==["drainage_ref"]


def test_initial_and_simulation_controls_are_not_hidden():
    assert _changed(lambda c:c.__setitem__("GWLI",-50.0))==["initial_condition"]
    assert _changed(lambda c:c.__setitem__("DZNEW","5.0 10.0"))==["simulation"]


def test_soil_hydraulics_and_rooting_remain_separate():
    assert _changed(lambda c:c["TABLE_SOILHYDRFUNC"][0].__setitem__("ELAS",2e-6))==["soil_hydraulics"]
    assert _changed(lambda c:c.__setitem__("RDS_effective",120.0))==["rooting"]
