import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/scripts'))
from summarize_attribution_diagnostic import paired_change, summarize


class AttributionDiagnosticTests(unittest.TestCase):
    def test_same_label_can_have_distribution_shift(self):
        a = dict(probabilities=dict(LEFT=.6, CENTER=.3, RIGHT=.1),
                 label='LEFT', raw_label='LEFT', decision='classified')
        b = dict(a, probabilities=dict(LEFT=.9, CENTER=.05, RIGHT=.05))
        result = paired_change(a, b)
        self.assertFalse(result['released_label_changed'])
        self.assertAlmostEqual(result['total_variation'], .3)

    def test_abstention_is_not_hidden(self):
        a = dict(probabilities=dict(LEFT=.6, CENTER=.3, RIGHT=.1),
                 label='LEFT', raw_label='LEFT', decision='classified')
        result = paired_change(a, dict(a, label=None, decision='abstained'))
        self.assertTrue(result['decision_changed'])
        self.assertTrue(result['released_label_changed'])
        self.assertFalse(result['raw_label_changed'])

    def test_missing_case_rejected(self):
        with self.assertRaises(ValueError):
            summarize([dict(id='one', text='example')], dict(cases=[]))

    def test_changed_text_rejected(self):
        with self.assertRaises(ValueError):
            summarize([dict(id='one', text='example')], dict(cases=[
                dict(id='one', status=200, result=dict(resolved_text='changed'))]))


if __name__ == '__main__':
    unittest.main()
