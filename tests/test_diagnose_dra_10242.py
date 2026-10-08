import struct
from pathlib import Path

import numpy as np
import pandas as pd

from tools.diagnose_dra_10242 import (
    _assert_ascii_matches_idf,
    _build_h1_level_matrix,
    _comparison_stats,
    _coordinates_to_row_col,
    _derive_lhm_bottom_candidates,
    _h1_stage_files,
    _month_key,
    _merge_review_metrics,
    _read_dqsat,
    _read_membership,
    _read_relation_context,
    _read_static04_snapshot,
    diagnose,
)


def _write_idf(path: Path, value: float, nodata: float = -9999.0) -> None:
    header=struct.pack(
        "<3i10f",
        1271, 1, 1,
        0.0, 250.0, 0.0, 250.0,
        value, value, nodata, 0.0, 250.0, 250.0,
    )
    path.write_bytes(header + struct.pack("<f", float(value)))


def test_membership_named_columns(tmp_path: Path):
    p=tmp_path/"membership.csv"
    pd.DataFrame({
        "SVAT":[1,2],
        "HRU":[10,11],
        "NRU":[20,21],
        "NRUcode":["a","b"],
        "svat_donor":[1,2],
        "ignored":[9,9],
    }).to_csv(p,index=False)
    df=_read_membership(p)
    assert list(df.columns)==["svat","hru","nru","nrucode","svatdonor"]
    assert df["hru"].tolist()==[10,11]


def test_representative_dqsat_autodetect(tmp_path: Path):
    p=tmp_path/"dqsat.csv"
    pd.DataFrame({
        "HRU":[1,2],
        "representative_dqsat":[10.0,20.0],
    }).to_csv(p,index=False)
    assert _read_dqsat(p)=={1:10.0,2:20.0}


def test_h1_month_key():
    assert _month_key(Path("peilh_20010201.idf"))=="2001-02-01"


def test_h1_months_are_stream_aggregated_per_hru(tmp_path: Path):
    p1=tmp_path/"peilh_20000101.idf"
    p2=tmp_path/"peilh_20000201.idf"
    _write_idf(p1,8.0)
    _write_idf(p2,7.0)

    members=pd.DataFrame({
        "hru":[1],
        "row":[0],
        "col":[0],
        "glk":[10.0],
        "H1_cdr":[2.0],
    })
    dates,matrix,failures=_build_h1_level_matrix(members,[p1,p2])
    assert dates==["2000-01-01","2000-02-01"]
    np.testing.assert_allclose(matrix[1],[2.0,3.0])
    assert failures=={}


def test_h1_missing_stage_is_bound_to_affected_hru(tmp_path: Path):
    p=tmp_path/"peilh_20000101.idf"
    _write_idf(p,-9999.0)
    members=pd.DataFrame({
        "hru":[7],
        "row":[0],
        "col":[0],
        "glk":[10.0],
        "H1_cdr":[2.0],
    })
    _,_,failures=_build_h1_level_matrix(members,[p])
    assert 7 in failures



def test_bottom_authority_comparison_includes_tertiary_lhm_peil_as_rbot():
    members=pd.DataFrame({
        "P_bottom":[1.0],"P_bottom_lhm_sum":[1.0],"P_bottom_lhm_win":[1.0],
        "S_bottom":[2.0],"S_bottom_lhm_sum":[2.0],"S_bottom_lhm_win":[2.0],
        "T_bottom":[3.0],"T_bottom_lhm_sum":[4.0],"T_bottom_lhm_win":[5.0],
    })
    members=_derive_lhm_bottom_candidates(members)
    out=_comparison_stats(members)
    assert "T" in out
    spread=out["T"]["seasonal_bottom_spread"]
    assert spread["different_gt_1e_6"] == 1
    assert spread["max_abs_difference_m"] == 1.0
    assert out["T"]["baseline_static_candidate"] == "equal_season_mean"



def test_authoritative_relation_supplies_membership_and_coordinates(tmp_path: Path):
    p=tmp_path/"relation.csv"
    pd.DataFrame({
        "svat_orig":[1,2],
        "HRU":[10,11],
        "NRU":[20,21],
        "NRUcode":["a","b"],
        "svat_donor":[1,2],
        "x":[125.0,375.0],
        "y":[625.0,625.0],
        "bodem370_orig":[1,2],
    }).to_csv(p,index=False)
    membership,coords,full=_read_relation_context(p)
    assert membership["svat"].tolist()==[1,2]
    assert coords.to_dict("records")==[
        {"svat":1,"x":125.0,"y":625.0},
        {"svat":2,"x":375.0,"y":625.0},
    ]
    assert "bodem370_orig" in full.columns



def test_static04_snapshot_accepts_new_partition_size(tmp_path: Path):
    p=tmp_path/"static04.csv"
    pd.DataFrame({
        "hru":[1,2],
        "representative_dqsat":[8.0,7.0],
        "discriminating":[False,True],
    }).to_csv(p,index=False)
    result=_read_static04_snapshot(p)
    assert result["hru"].tolist()==[1,2]
    assert result["representative_dqsat"].tolist()==[8.0,7.0]



def test_static04_snapshot_requires_unique_hru_domain(tmp_path: Path):
    p=tmp_path/"snapshot.csv"
    pd.DataFrame({
        "hru":[1,1],
        "representative_dqsat":[10.0,20.0],
        "discriminating":[False,True],
    }).to_csv(p,index=False)
    try:
        _read_static04_snapshot(p)
    except ValueError as exc:
        assert "duplicate HRU" in str(exc)
    else:
        raise AssertionError("expected duplicate HRU snapshot to fail")


def test_static04_snapshot_preserves_discriminating_column(tmp_path: Path):
    p=tmp_path/"snapshot.csv"
    pd.DataFrame({
        "hru":range(1,10243),
        "representative_dqsat":[10.0]*10242,
        "discriminating":[False]*10241+[True],
    }).to_csv(p,index=False)
    out=_read_static04_snapshot(p)
    assert len(out)==10242
    assert int(out["discriminating"].sum())==1



def test_ascii_geometry_must_match_drainage_idf():
    from types import SimpleNamespace
    idf=SimpleNamespace(
        ncol=1200,nrow=1300,xmin=0.0,xmax=300000.0,
        ymin=300000.0,ymax=625000.0,dx=250.0,dy=250.0,
    )
    good=SimpleNamespace(
        ncols=1200,nrows=1300,xllcorner=0.0,yllcorner=300000.0,
        cellsize=250.0,
    )
    _assert_ascii_matches_idf(good,idf,label="good")
    bad=SimpleNamespace(
        ncols=1200,nrows=1300,xllcorner=125.0,yllcorner=300000.0,
        cellsize=250.0,
    )
    try:
        _assert_ascii_matches_idf(bad,idf,label="bad")
    except ValueError as exc:
        assert "geometry" in str(exc)
    else:
        raise AssertionError("expected shifted AHN grid to fail")



def test_h1_stage_selection_requires_gap_free_months(tmp_path: Path):
    _write_idf(tmp_path/"peilh_20000101.idf",1.0)
    _write_idf(tmp_path/"peilh_20000301.idf",1.0)
    try:
        _h1_stage_files(tmp_path,"2000-01-01","2000-03-01")
    except ValueError as exc:
        assert "not gap-free monthly" in str(exc)
        assert "2000-02-01" in str(exc)
    else:
        raise AssertionError("expected missing H1 month to fail")


def test_static04_snapshot_normalizes_text_boolean(tmp_path: Path):
    p=tmp_path/"snapshot.csv"
    pd.DataFrame({
        "hru":range(1,10243),
        "representative_dqsat":[10.0]*10242,
        "discriminating":["false"]*10241+["true"],
    }).to_csv(p,index=False)
    out=_read_static04_snapshot(p)
    assert out["discriminating"].dtype == bool
    assert int(out["discriminating"].sum()) == 1



def test_ordering_metrics_contract_is_named_in_runner_source():
    # Cheap guard: the population runner must persist the evidence required by
    # the SWAP DIVDRA ordering authority note.
    source=Path("tools/diagnose_dra_10242.py").read_text(encoding="utf-8")
    assert '"all_levels_same_L"' in source
    assert '"level_order"' in source
    assert '"hru_with_equal_L_ordering_tie"' in source
    assert '"DEEPEST_FIRST_THEN_MEDIUM_THEN_LINEAGE"' in source



def test_merge_review_metrics_report_population_and_h1_pairs():
    s=pd.DataFrame([
        {"active_physical_systems":0},
        {"active_physical_systems":6},
        {"active_physical_systems":7},
    ])
    m=pd.DataFrame([
        {
            "left":"H1","right":"P","cost":1.0,
            "max_drainage_infiltration_level_gap_m":0.10,
            "max_source_level_separation_m":0.20,
            "bottom_depth_separation_m":0.05,
        },
        {
            "left":"P","right":"H1","cost":3.0,
            "max_drainage_infiltration_level_gap_m":0.30,
            "max_source_level_separation_m":0.40,
            "bottom_depth_separation_m":0.15,
        },
        {
            "left":"MVG","right":"OLF","cost":2.0,
            "max_drainage_infiltration_level_gap_m":0.0,
            "max_source_level_separation_m":0.10,
            "bottom_depth_separation_m":0.02,
        },
    ])
    out=_merge_review_metrics(s,m)
    assert out["zero_active_hru"]==1
    assert out["six_active_hru"]==1
    assert out["seven_active_hru"]==1
    assert out["h1_merge_event_count"]==2
    assert out["top_merge_pairs"][0]=={"pair":"H1 | P","count":2}
    assert out["merge_cost_quantiles"]["max"]==3.0
    tension=out["merge_level_representation_tension"]
    centroid=tension["drainage_infiltration_centroid_gap"]
    assert centroid["acceptance_threshold"] is None
    assert centroid["events_with_positive_gap"]==2
    assert centroid["all_merge_quantiles"]["max"]==0.30
    assert centroid["h1_merge_quantiles"]["max"]==0.30
    activation=tension["source_activation_level_span"]
    assert activation["events_with_positive_span"]==3
    assert activation["all_merge_quantiles"]["max"]==0.40
    assert activation["h1_merge_quantiles"]["max"]==0.40
    assert tension["bottom_depth_span"]["all_merge_quantiles"]["max"]==0.15



def test_full_diagnostic_rejects_wrong_h1_bundle_sha_before_reading_relation(tmp_path: Path):
    relation=tmp_path/"missing_relation.csv"
    h1=tmp_path/"h1.zip"
    remaining=tmp_path/"remaining.zip"
    h1.write_bytes(b"wrong-h1")
    remaining.write_bytes(b"remaining")
    try:
        diagnose(
            relation,
            h1,
            remaining,
            tmp_path/"out",
            stage_start="1971-01-01",
            stage_end="2022-01-01",
            dqsat_snapshot=tmp_path/"missing_static04.csv",
        )
    except ValueError as exc:
        assert "H1/MVG bundle SHA mismatch" in str(exc)
    else:
        raise AssertionError("expected wrong H1 bundle identity to fail closed")



def test_lhm_seasonal_bottom_candidates_use_equal_season_mean_and_bounds():
    members=pd.DataFrame({
        "P_bottom_lhm_sum":[8.0],
        "P_bottom_lhm_win":[6.0],
        "S_bottom_lhm_sum":[5.0],
        "S_bottom_lhm_win":[5.0],
        "T_bottom_lhm_sum":[4.0],
        "T_bottom_lhm_win":[2.0],
    })
    out=_derive_lhm_bottom_candidates(members)
    assert out.loc[0,"P_bottom_lhm_mean"] == 7.0
    assert out.loc[0,"P_bottom_lhm_deepest"] == 6.0
    assert out.loc[0,"P_bottom_lhm_shallowest"] == 8.0
    assert out.loc[0,"P_bottom"] == 7.0
    assert out.loc[0,"T_bottom_lhm_mean"] == 3.0


def test_bottom_comparison_does_not_require_historical_j_grids():
    members=pd.DataFrame({
        "P_bottom_lhm_sum":[8.0],"P_bottom_lhm_win":[6.0],
        "S_bottom_lhm_sum":[5.0],"S_bottom_lhm_win":[5.0],
        "T_bottom_lhm_sum":[4.0],"T_bottom_lhm_win":[2.0],
    })
    members=_derive_lhm_bottom_candidates(members)
    out=_comparison_stats(members)
    assert out["P"]["historical_j"]["available"] is False
    assert out["P"]["seasonal_bottom_spread"]["max_abs_difference_m"] == 2.0


def test_bottom_comparison_uses_historical_j_when_recovered():
    members=pd.DataFrame({
        "P_bottom_lhm_sum":[8.0],"P_bottom_lhm_win":[6.0],"P_bottom_historical_j":[7.0],
        "S_bottom_lhm_sum":[5.0],"S_bottom_lhm_win":[5.0],"S_bottom_historical_j":[5.0],
        "T_bottom_lhm_sum":[4.0],"T_bottom_lhm_win":[2.0],"T_bottom_historical_j":[3.0],
    })
    members=_derive_lhm_bottom_candidates(members)
    out=_comparison_stats(members)
    assert out["P"]["historical_j"]["available"] is True
    assert out["P"]["historical_j"]["comparison"]["mean"]["max_abs_difference_m"] == 0.0



def test_full_diagnostic_accepts_exact_idf_cell_centre(tmp_path: Path):
    grid=tmp_path/"grid.idf"
    _write_idf(grid,1.0)
    coords=pd.DataFrame({"svat":[1],"x":[125.0],"y":[125.0]})
    out=_coordinates_to_row_col(coords,grid)
    assert int(out.loc[0,"row"]) == 0
    assert int(out.loc[0,"col"]) == 0


def test_full_diagnostic_rejects_offcentre_svat_coordinates(tmp_path: Path):
    grid=tmp_path/"grid.idf"
    _write_idf(grid,1.0)
    coords=pd.DataFrame({"svat":[1],"x":[126.0],"y":[125.0]})
    try:
        _coordinates_to_row_col(coords,grid)
    except ValueError as exc:
        assert "exact IDF-cell centres" in str(exc)
    else:
        raise AssertionError("expected off-centre SVAT coordinate to fail closed")
