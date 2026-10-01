from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from tools.idf_reader import read_idf


class MetadataTests(unittest.TestCase):
    def test_provenance_footer_leaves_array_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'grid.idf'
            header = struct.pack('<3i10f', 1271, 2, 1, 0, 500, 0, 250, 1, 2, -9999, 0, 250, 250)
            data = np.array([[1, 2]], dtype='<f4').tobytes()
            path.write_bytes(header + data)
            plain = read_idf(path)
            footer = struct.pack('<2i', 1, 3) + b'User: test  '
            path.write_bytes(header + data + footer)
            np.testing.assert_array_equal(plain.values, read_idf(path).values)
            path.write_bytes(header + data + footer[:-1])
            with self.assertRaises(ValueError):
                read_idf(path)
