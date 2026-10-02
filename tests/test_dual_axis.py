import sys
import unittest
import csv
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from dual_axis_training import rating, decode, recover


class DualAxisTests(unittest.TestCase):
    def test_democrat_sign_is_inverted(self):
        self.assertEqual(rating("0", "-5"), (0., 1.))
        self.assertEqual(decode(*rating("0", "-5")), "LEFT")

    def test_republican_positive_is_right(self):
        self.assertEqual(decode(*rating("5", "0")), "RIGHT")

    def test_equal_negative_does_not_force_direction(self):
        self.assertEqual(decode(*rating("-5", "5")), "CENTER")

    def test_threshold_boundary(self):
        self.assertEqual(decode(.125, 0), "CENTER")
        self.assertEqual(decode(.126, 0), "RIGHT")
        self.assertEqual(decode(0, .126), "LEFT")

    def test_invalid_scale_rejected(self):
        with self.assertRaises(ValueError):
            rating("4", "0")

    def test_allowlist_skips_unrelated_ratings_and_identifiers(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ratings.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["Input.docid", "Answer.q1", "Answer.q2", "AssignmentStatus", "WorkerId"])
                writer.writerow(["unrelated", "INVALID", "INVALID", "Submitted", "private-id"])
                writer.writerow(["keep", "0", "0", "Approved", "private-id-a"])
                writer.writerow(["keep", "0", "0", "Submitted", "private-id-b"])
            result = recover(path, [{"id": "keep", "worker_labels": ["Center", "Center"]}])
            self.assertEqual(set(result), {"keep"})
            self.assertEqual(len(result["keep"]), 2)
            self.assertNotIn("WorkerId", result["keep"][0])
            with self.assertRaises(ValueError):
                recover(path, [{"id": "keep", "worker_labels": ["Left", "Center"]}])
