import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research' / 'scripts'))
from oof_confidence_audit import audit


def row(id, gold, p):
    labels = ('LEFT', 'CENTER', 'RIGHT')
    return dict(id=id, gold=gold, prediction=labels[max(range(3), key=lambda i: p[i])],
        probabilities=dict(zip(labels, p)))


class ConfidenceTests(unittest.TestCase):
    def test_perfect_and_endpoint_bin(self):
        r = audit([row('a', 'LEFT', [1, 0, 0]), row('b', 'CENTER', [0, 1, 0])])
        self.assertEqual(r['multiclass_brier_sum'], 0)
        self.assertEqual(r['nll'], 0)
        self.assertEqual(r['ece_10_equal_width'], 0)
        self.assertEqual(r['bins'][-1]['n'], 2)
        self.assertIsNone(r['correctness_auc'])

    def test_ties_preserve_all_examples(self):
        r = audit([row(str(i), 'LEFT', [.6, .3, .1]) for i in range(5)])
        self.assertTrue(all(c['coverage'] == 1 for c in r['retained_fraction_diagnostics']))

    def test_abstentions_stay_in_class_denominator(self):
        r = audit([row('a', 'LEFT', [.9, .05, .05]), row('b', 'LEFT', [.4, .35, .25])])
        c = r['retained_fraction_diagnostics'][-1]
        self.assertEqual(c['selective_accuracy'], 1)
        self.assertEqual(c['per_class']['LEFT']['delivered_recall'], .5)
        self.assertIsNone(c['per_class']['CENTER']['delivered_recall'])

    def test_confidence_ranks_errors_above_correct(self):
        r = audit([row('a', 'RIGHT', [.9, .05, .05]), row('b', 'LEFT', [.4, .35, .25])])
        self.assertEqual(r['correctness_auc'], 0)

    def test_invalid_input(self):
        rows = [row('a', 'LEFT', [.6, .3, .1])]
        for bad in ([], rows * 2, [row('b', 'LEFT', [float('nan'), .3, .1])],
                    [row('c', 'LEFT', [.9, .3, .1])]):
            with self.assertRaises(ValueError): audit(bad)
        bad = copy.deepcopy(rows)
        bad[0]['prediction'] = 'RIGHT'
        with self.assertRaises(ValueError): audit(bad)


if __name__ == '__main__':
    unittest.main()
