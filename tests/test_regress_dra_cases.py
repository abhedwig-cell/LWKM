from tools.regress_dra_cases import regress_dra


BASE="""DRAMET = 3
SWDIVD = 1
SWDISLAY = 0
NRLEVS = 5
SWINTFL = 0
SWTOPNRSRF = 0
DRARES1 = 100000
INFRES1 = 100000
SWALLO1 = 3
L1 = 100
ZBOTDR1 = 0.0
SWDTYP1 = 1
DRARES2 = 824
INFRES2 = 2498
SWALLO2 = 1
L2 = 80
ZBOTDR2 = -97.79
SWDTYP2 = 1
"""


def test_multirun_dra_exact_and_expected_difference(tmp_path):
    oracle=tmp_path/"oracle"/"run_000002000"
    candidate=tmp_path/"candidate"/"run_000002000"
    oracle.mkdir(parents=True);candidate.mkdir(parents=True)
    (oracle/"2000.dra").write_text(BASE)
    (candidate/"2000.dra").write_text(BASE)

    exact=regress_dra(oracle_root=tmp_path/"oracle",candidate_root=tmp_path/"candidate")
    assert exact["admission_candidate"]
    assert exact["cases"][0]["status"]=="PASS"

    (candidate/"2000.dra").write_text(BASE.replace("L2 = 80","L2 = 84"))
    failed=regress_dra(oracle_root=tmp_path/"oracle",candidate_root=tmp_path/"candidate")
    assert not failed["admission_candidate"]
    assert failed["cases"][0]["unexplained"]==["systems.2.L"]

    expected=tmp_path/"expected.yml"
    expected.write_text("expected_differences:\n  2000:\n    - systems.2.L\n")
    qualified=regress_dra(
        oracle_root=tmp_path/"oracle",
        candidate_root=tmp_path/"candidate",
        expected_differences=expected,
    )
    assert qualified["admission_candidate"]
    assert qualified["cases"][0]["status"]=="EXPECTED_DIFFERENCE"


def test_missing_candidate_run_blocks_admission(tmp_path):
    oracle=tmp_path/"oracle"/"run_000000001"
    candidate=tmp_path/"candidate"
    oracle.mkdir(parents=True);candidate.mkdir()
    (oracle/"1.dra").write_text(BASE)
    result=regress_dra(oracle_root=tmp_path/"oracle",candidate_root=candidate)
    assert not result["admission_candidate"]
    assert result["missing_candidate_runs"]==[1]
