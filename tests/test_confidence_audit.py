import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from confidence_audit import align, summarize


def example(id, reference="LEFT", prediction="LEFT", scores=None):
    row = {"id": id, "label": reference, "strict_agreement": True}
    response = {"id": id, "response": {"overall": {"raw_label": prediction,
        "probabilities": scores or {"LEFT": 1., "CENTER": 0., "RIGHT": 0.}}}}
    return row, response


class ConfidenceAuditTests(unittest.TestCase):
    def test_perfect_endpoint_and_empty_threshold(self):
        row, response = example("a")
        report = summarize(align([row], [response]))
        self.assertEqual(report["top_label_ece_10_bins"], 0)
        self.assertEqual(report["brier_multiclass_sum"], 0)
        self.assertEqual(report["bins"][-1]["n"], 1)
        self.assertIsNone(report["confidence_correctness_auc"])
        self.assertEqual(summarize([]), {"n": 0})

    def test_tied_ranking_and_oracle_coverage_round_up(self):
        pairs = [example(str(i), reference="LEFT" if i < 2 else "RIGHT") for i in range(6)]
        report = summarize(align([r for r, _ in pairs], [v for _, v in reversed(pairs)]))
        self.assertEqual(report["confidence_correctness_auc"], .5)
        self.assertEqual(report["oracle_at_minimum_coverage"]["minimum_retained"], 5)
        self.assertEqual(report["oracle_at_minimum_coverage"]["agreement_upper_bound"], .4)
        self.assertAlmostEqual(report["brier_multiclass_sum"], 4 / 3)
        self.assertTrue(report["nll_epsilon_1e_12"] > 0)

    def test_empty_selection_is_not_perfect_accuracy(self):
        row, response = example("a", scores={"LEFT": .4, "CENTER": .3, "RIGHT": .3})
        report = summarize(align([row], [response]))
        self.assertIsNone(report["thresholds"][0]["agreement"])
        self.assertEqual(report["thresholds"][0]["coverage"], 0)

    def test_inclusive_threshold_and_bin_boundary(self):
        row, response = example("a", scores={"LEFT": .9, "CENTER": .05, "RIGHT": .05})
        report = summarize(align([row], [response]))
        self.assertEqual(report["bins"][9]["n"], 1)
        self.assertEqual(report["thresholds"][2]["n"], 1)
        self.assertAlmostEqual(report["top_label_ece_10_bins"], .1)

    def test_rank_direction(self):
        pairs = [example("correct", scores={"LEFT": .8, "CENTER": .1, "RIGHT": .1}),
                 example("wrong", reference="RIGHT")]
        report = summarize(align([r for r, _ in pairs], [v for _, v in pairs]))
        self.assertEqual(report["confidence_correctness_auc"], 0)

    def test_abstention_does_not_count_as_displayed_match(self):
        row, response = example("a")
        response["response"]["overall"].update(label=None, decision="abstained")
        report = summarize(align([row], [response]))
        self.assertEqual(report["matches"], 1)
        self.assertEqual(report["displayed_decisions"]["coverage"], 0)
        self.assertIsNone(report["displayed_decisions"]["agreement"])

    def test_rejects_duplicate_or_missing_ids(self):
        row, response = example("a")
        for rows, responses in (([row, row], [response, response]), ([row], [])):
            with self.assertRaises(ValueError):
                align(rows, responses)

    def test_rejects_invalid_simplex_and_argmax(self):
        for scores in ({"LEFT": float("nan"), "CENTER": 0, "RIGHT": 0},
                       {"LEFT": .9, "CENTER": .9, "RIGHT": 0},
                       {"LEFT": .1, "CENTER": .8, "RIGHT": .1}):
            row, response = example("a", scores=scores)
            with self.assertRaises(ValueError):
                align([row], [response])
