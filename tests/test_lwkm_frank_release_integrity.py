"""Regression checks for the immutable Frank producer release registry."""
import json
import unittest
from pathlib import Path
from tools.lwkm_frank.release_integrity import PRODUCERS,SHARED,check

class ReleaseRegistryTest(unittest.TestCase):
    def test_identity_registry_is_complete(self):
        root=Path(__file__).resolve().parents[1]
        meta=json.loads((root/"config/production/frank_original_producers_sha256_v01.json").read_text())
        self.assertEqual(len(meta["files"]),12)
        self.assertEqual(set(meta["files"]),set(PRODUCERS)|set(SHARED))
        self.assertTrue(all(len(d)==64 and set(d)<set("0123456789abcdef") for d in meta["files"].values()))

    def test_missing_files_fail_closed(self):
        root=Path(__file__).resolve().parents[1]
        registry=root/"config/production/frank_original_producers_sha256_v01.json"
        rows=check(root/"nonexistent-original-producers",registry)
        self.assertEqual(len(rows),12)
        self.assertTrue(all(not r["valid"] for r in rows))

if __name__=="__main__":unittest.main()
