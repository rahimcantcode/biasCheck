import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research/scripts"))
from corpus_experiment import digest, metrics
from summarize_corpus_experiment import align


class CorpusExperimentTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": "a", "label": "LEFT", "strict_agreement": True},
                     {"id": "b", "label": "CENTER", "strict_agreement": True},
                     {"id": "c", "label": "RIGHT", "strict_agreement": False}]

    def test_predictions_are_aligned_by_id(self):
        values = [{"id": "c", "prediction": "RIGHT"}, {"id": "a", "prediction": "LEFT"}, {"id": "b", "prediction": "CENTER"}]
        self.assertEqual(align(self.rows, values), ["LEFT", "CENTER", "RIGHT"])

    def test_missing_or_duplicated_predictions_rejected(self):
        for values in ([{"id": "a", "prediction": "LEFT"}], [{"id": "a", "prediction": "LEFT"}] * 3):
            with self.assertRaises(ValueError):
                align(self.rows, values)

    def test_full_and_agreed_denominators_differ(self):
        result = metrics(self.rows, ["LEFT", "CENTER", "LEFT"])
        self.assertAlmostEqual(result["accuracy"], 2 / 3)
        self.assertEqual(result["strict_agreement"]["n"], 2)
        self.assertEqual(result["strict_agreement"]["accuracy"], 1)
        self.assertEqual(result["confusion_matrix"], [[1, 0, 0], [0, 1, 0], [1, 0, 0]])

    def test_incomplete_metric_inputs_rejected(self):
        with self.assertRaises(ValueError):
            metrics(self.rows, ["LEFT"])

    def test_normalized_duplicate_hash(self):
        self.assertEqual(digest("A story\n about Taxes"), digest("a story about taxes"))


if __name__ == "__main__":
    unittest.main()
