import sys
import unittest
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from hybrid_cv import hybrid, validate_split


class HybridTests(unittest.TestCase):
    def test_equal_energy_blocks(self):
        matrix = hybrid(csr_matrix([[1., 0.]]), np.array([[0., 1.]]))
        self.assertEqual(matrix.shape, (1, 4))
        self.assertAlmostEqual(float(matrix.multiply(matrix).sum()), 1)
        self.assertAlmostEqual(float(matrix[:, :2].multiply(matrix[:, :2]).sum()), .5)

    def test_invalid_features(self):
        with self.assertRaises(ValueError):
            hybrid(csr_matrix([[1.]]), np.ones((2, 1)))
        with self.assertRaises(ValueError):
            hybrid(csr_matrix([[1.]]), np.array([[np.nan]]))

    def test_split_integrity(self):
        rows = [{"id": "a", "event": "one"}, {"id": "b", "event": "two"}]
        validate_split(rows, ["a"], ["b"])
        for train, held in ((["a"], ["a"]), (["a", "a"], ["b"]), (["a"], [])):
            with self.assertRaises(ValueError):
                validate_split(rows, train, held)
        rows[1]["event"] = "one"
        with self.assertRaises(ValueError):
            validate_split(rows, ["a"], ["b"])
