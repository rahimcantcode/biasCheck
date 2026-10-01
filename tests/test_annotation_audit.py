import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from annotation_audit import diagnose


class AnnotationAuditTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(id="a", label="LEFT", worker_labels=["Center", "Left"], strict_agreement=False),
                     dict(id="b", label="CENTER", worker_labels=["Center", "Center"], strict_agreement=True)]

    def test_disputed_worker_match_not_released_match(self):
        groups = diagnose(self.rows, ["CENTER", "CENTER"])["groups"]
        self.assertEqual(groups["all"]["released_agreement"], .5)
        self.assertEqual(groups["all"]["mean_worker_agreement"], .75)
        self.assertEqual(groups["disputed"]["released_errors_matching_one_worker"], 1)

    def test_neither_worker(self):
        self.assertEqual(diagnose(self.rows, ["RIGHT", "LEFT"])["groups"]["all"]["matches_neither_worker"], 2)

    def test_empty_subset_has_no_score(self):
        self.assertIsNone(diagnose(self.rows[1:], ["CENTER"])["groups"]["disputed"]["released_agreement"])

    def test_reject_invalid_provenance_or_length(self):
        with self.assertRaises(ValueError):
            diagnose(self.rows, ["LEFT"])
        self.rows[0]["strict_agreement"] = True
        with self.assertRaises(ValueError):
            diagnose(self.rows, ["LEFT", "CENTER"])
