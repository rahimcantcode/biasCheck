import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from evaluate_structured_stance import measures, aligned


class StructuredEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": "a", "label": "LEFT"}, {"id": "b", "label": "CENTER"}, {"id": "c", "label": "RIGHT"}]

    def test_abstentions_remain_in_denominator_and_matrix(self):
        result = measures(self.rows, ["LEFT", "INSUFFICIENT", "MIXED"])
        self.assertAlmostEqual(result["released_label_agreement_all"], 1 / 3)
        self.assertAlmostEqual(result["three_way_coverage"], 1 / 3)
        self.assertEqual(result["conditional_three_way_agreement"], 1)
        self.assertEqual(sum(map(sum, result["confusion"])), 3)
        self.assertEqual(result["per_class"]["CENTER"]["recall"], 0)

    def test_all_withheld(self):
        result = measures(self.rows, ["INSUFFICIENT"] * 3)
        self.assertEqual(result["released_label_agreement_all"], 0)
        self.assertIsNone(result["conditional_three_way_agreement"])

    def test_complete_matches(self):
        result = measures(self.rows, ["LEFT", "CENTER", "RIGHT"])
        self.assertEqual(result["macro_f1_three_reference_classes_all"], 1)

    def test_reject_partial_or_invalid(self):
        for values in (["LEFT"], ["LEFT", "OTHER", "RIGHT"]):
            with self.assertRaises(ValueError):
                measures(self.rows, values)

    def test_alignment_and_duplicate_rejection(self):
        predictions = [{"id": "c", "label": "RIGHT"}, {"id": "a", "label": "LEFT"}, {"id": "b", "label": "CENTER"}]
        self.assertEqual(aligned(self.rows, predictions, "label"), ["LEFT", "CENTER", "RIGHT"])
        with self.assertRaises(ValueError):
            aligned(self.rows, [predictions[0]] * 3, "label")
