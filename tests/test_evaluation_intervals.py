import unittest
from research.scripts.evaluate import summarize, wilson


class IntervalTests(unittest.TestCase):
    def test_known_interval(self):
        r=wilson(50,100)
        self.assertAlmostEqual(r['lower'],.40383153,places=7)
        self.assertAlmostEqual(r['upper'],.59616847,places=7)

    def test_edges_empty_and_invalid(self):
        self.assertAlmostEqual(wilson(0,100)['upper'],.0369935,places=7)
        self.assertAlmostEqual(wilson(100,100)['lower'],.9630065,places=7)
        self.assertIsNone(wilson(0,0)['lower'])
        for k,n in [(-1,2),(3,2),(True,2),(1,False),(1.0,2),(0,-1)]:
            with self.assertRaises(ValueError): wilson(k,n)

    def test_abstention_and_negative_denominators(self):
        rows=[dict(gold='LEFT',raw_label='LEFT',label='LEFT',decision='classified'),
              dict(gold='LEFT',raw_label='LEFT',label=None,decision='abstained'),
              dict(gold='NONPOLITICAL',label='RIGHT',decision='classified')]
        r=summarize(rows)['marginal_intervals']
        self.assertEqual((r['raw_accuracy']['successes'],r['raw_accuracy']['n']),(2,2))
        self.assertEqual((r['coverage']['successes'],r['coverage']['n']),(1,2))
        self.assertEqual((r['selective_accuracy']['successes'],r['selective_accuracy']['n']),(1,1))
        self.assertEqual(r['per_class']['LEFT']['delivered_recall']['successes'],1)
        self.assertIsNone(r['per_class']['CENTER']['raw_recall']['lower'])
        self.assertEqual(r['nonpolitical_false_label_rate']['n'],1)

    def test_empty_summary(self):
        self.assertIsNone(summarize([])['marginal_intervals']['raw_accuracy']['lower'])
