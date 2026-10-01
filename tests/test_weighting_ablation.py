import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from weighting_ablation import REGIMES, weighted_targets


class WeightingTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"label": label, "worker_labels": [label, label], "strict_agreement": True}
                     for label in ("LEFT", "CENTER", "RIGHT")]
        self.rows.append({"label": "LEFT", "worker_labels": ["Center", "Left"], "strict_agreement": False})

    def test_fixed_total_and_equal_class_mass(self):
        for regime in REGIMES:
            _, labels, weights, _ = weighted_targets(self.rows, regime)
            self.assertAlmostEqual(weights.sum(), 4.)
            for label in ("LEFT", "CENTER", "RIGHT"):
                self.assertAlmostEqual(weights[np.array(labels) == label].sum(), 4 / 3)

    def test_workers_are_preserved(self):
        ids, labels, _, masses = weighted_targets(self.rows, "worker_distribution")
        self.assertEqual([y for i, y in zip(ids, labels) if i == 3], ["CENTER", "LEFT"])
        self.assertEqual(masses, {"LEFT": 1.5, "CENTER": 1.5, "RIGHT": 1.})

    def test_unanimous_filter(self):
        ids, _, _, _ = weighted_targets(self.rows, "unanimous_only")
        self.assertEqual(ids.tolist(), [0, 1, 2])

    def test_downweight_mass(self):
        _, _, _, masses = weighted_targets(self.rows, "downweight_disputes")
        self.assertEqual(masses["LEFT"], 1.25)

    def test_invalid_annotations_and_missing_class(self):
        with self.assertRaises(ValueError):
            weighted_targets(self.rows[:2], "hard")
        self.rows[-1]["strict_agreement"] = True
        with self.assertRaises(ValueError):
            weighted_targets(self.rows, "hard")


if __name__ == "__main__":
    unittest.main()
