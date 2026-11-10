"""Tests for run-specific MetaSWAP source inventory (no NHI dependencies)."""
import tempfile
import unittest
from pathlib import Path
from tools.lwkm_frank.inventory_run_local_metaswap import discover, write

class RunLocalMetaswapTests(unittest.TestCase):
    def test_unequal_run_data_stays_separate(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for run, body in (("run_1970_1979","aaa"),("run_1980_1989","bbb")):
                p=root/run/"metaswap"/"inp"/"area_svat.inp"
                p.parent.mkdir(parents=True)
                p.write_text(body)
            rows=discover(root,names=("area_svat.inp",))
            self.assertEqual(len(rows),2)
            self.assertEqual(len({r["sha256"] for r in rows}),2)
            self.assertTrue(all(r["status"]=="CANDIDATE_RUN_LOCAL" for r in rows))

    def test_missing_never_falls_back_to_global_install(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"run_1970_1979"/"metaswap").mkdir(parents=True)
            rows=discover(root,names=("area_svat.inp",))
            self.assertEqual(rows[0]["status"],"MISSING_RUN_LOCAL")

    def test_alternative_runs_separate_and_machine_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for run in ("run_1970_1979","run_2020_2024_MS_daily"):
                p=root/run/"metaswap"/"inp"/"area_svat.inp"
                p.parent.mkdir(parents=True)
                p.write_text("same")
            output=root/"reports"
            info=write(root,output)
            self.assertEqual(info["run_count"],2)
            self.assertTrue((output/"lhm_run_metaswap_input_inventory.json").exists())
            self.assertEqual(len(info["hashes_by_logical_file"]["area_svat.inp"]),1)

if __name__=="__main__":unittest.main()
