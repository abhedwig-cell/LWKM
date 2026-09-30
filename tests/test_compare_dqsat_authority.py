import numpy as np
import pandas as pd

from tools.compare_dqsat_authority import compare_dqsat_authority, read_ascii_grid


def _write_grid(path):
    path.write_text(
        "\n".join(
            [
                "ncols 2",
                "nrows 2",
                "xllcorner 0",
                "yllcorner 0",
                "cellsize 250",
                "NODATA_value -9999",
                "5 10",
                "7 7",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_compare_dqsat_authority_matches_fortran_lower_tie_and_204_repair(tmp_path):
    grid_path = tmp_path / "dqsat.asc"
    _write_grid(grid_path)
    grid = read_ascii_grid(grid_path)

    relation = pd.DataFrame(
        {
            "svat_orig": [1, 2, 3, 4],
            "HRU": [1, 1, 2, 2],
            "x": [125, 375, 125, 375],
            "y": [375, 375, 125, 125],
            "bodem370_orig": [10, 10, 204, 205],
        }
    )
    schema = pd.DataFrame({"HRU": [1, 2], "svat_repr": [2, 3]})

    result = compare_dqsat_authority(schema, relation, grid).set_index("hru")

    # HRU 1 has a 5/10 frequency tie. Alterratools keeps the lowest sorted value.
    assert result.loc[1, "legacy_dqsat"] == 5
    assert result.loc[1, "representative_dqsat"] == 10
    assert bool(result.loc[1, "discriminating"])

    # HRUlist2SWAP repairs raw BFE 204 to 205 before the BFE majority/dqsat selection.
    assert result.loc[2, "legacy_bfe_majority"] == 205
    assert result.loc[2, "legacy_dqsat"] == 7
    assert result.loc[2, "representative_dqsat"] == 7
    assert not bool(result.loc[2, "discriminating"])


def test_read_ascii_grid_rejects_wrong_shape(tmp_path):
    path = tmp_path / "bad.asc"
    path.write_text(
        "ncols 2\nnrows 2\nxllcorner 0\nyllcorner 0\ncellsize 250\n"
        "NODATA_value -9999\n1 2\n",
        encoding="utf-8",
    )
    try:
        read_ascii_grid(path)
    except ValueError as exc:
        assert "expected" in str(exc)
    else:
        raise AssertionError("wrong raster shape was accepted")
