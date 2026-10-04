import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.scripts.evaluate import summarize
from research.scripts.evaluate_policy import point_estimate_gates


def row(gold, raw, accepted=True):
    return {'gold':gold,'raw_label':raw,'decision':'classified' if accepted else 'abstained','label':raw if accepted else None}


class DeliveredMetricsTests(unittest.TestCase):
    def test_unknown_reference_not_silently_dropped(self):
        for gold in ('CENTRE', '', None, 'MIXED'):
            with self.subTest(gold=gold), self.assertRaisesRegex(ValueError,'reference label'):
                summarize([row('LEFT','LEFT'),row(gold,'RIGHT')])

    def test_negative_and_uncertain_decisions_validated(self):
        for gold in ('NONPOLITICAL','UNCERTAIN'):
            for decision,label in [('error',None),('classified',None),('abstained','LEFT')]:
                with self.subTest(gold=gold,decision=decision), self.assertRaises(ValueError):
                    summarize([dict(gold=gold,raw_label='LEFT',decision=decision,label=label)])

    def test_invalid_raw_label_rejected(self):
        with self.assertRaisesRegex(ValueError,'raw political'):
            summarize([{**row('LEFT','LEFT'),'raw_label':'UNKNOWN'}])

    def test_valid_negative_counts_preserved(self):
        result=summarize([row('NONPOLITICAL','LEFT'),row('NONPOLITICAL','RIGHT',False),row('UNCERTAIN','LEFT',False)])
        self.assertEqual(result['n'],3)
        self.assertEqual(result['nonpolitical_n'],2)
        self.assertEqual(result['nonpolitical_false_label_rate'],.5)
        self.assertIsNone(result['coverage'])

    def test_perfect_raw_with_abstentions_is_not_perfect_delivery(self):
        result=summarize([row(label,label,False) for label in ('LEFT','CENTER','RIGHT')])
        self.assertEqual(result['raw_accuracy'],1)
        self.assertEqual(result['delivered']['macro_f1'],0)
        self.assertEqual(result['delivered']['correct_fraction'],0)
        self.assertEqual(result['delivered']['confusion_matrix'],[[0,0,0,1],[0,0,0,1],[0,0,0,1]])

    def test_missing_class_coverage_is_undefined(self):
        result=summarize([row('LEFT','LEFT')])
        self.assertIsNone(result['delivered']['per_class_coverage']['RIGHT'])

    def test_false_positive_and_abstention_are_distinct(self):
        result=summarize([row('LEFT','RIGHT'),row('RIGHT','RIGHT',False),row('CENTER','CENTER')])
        self.assertEqual(result['delivered']['per_class']['RIGHT']['precision'],0)
        self.assertEqual(result['delivered']['per_class']['RIGHT']['recall'],0)
        self.assertAlmostEqual(result['delivered']['correct_fraction'],1/3)

    def test_selective_success_cannot_replace_raw_accuracy(self):
        rows=[]
        for label in ('LEFT','CENTER','RIGHT'):
            rows.extend(row(label,label) for _ in range(85))
            rows.extend(row(label,'RIGHT' if label!='RIGHT' else 'LEFT',False) for _ in range(15))
        rows.extend(row('NONPOLITICAL','LEFT',False) for _ in range(100))
        gates=point_estimate_gates(summarize(rows))
        self.assertTrue(gates['selective_accuracy'])
        self.assertTrue(gates['coverage'])
        self.assertFalse(gates['raw_accuracy'])

    def test_inconsistent_decision_rejected(self):
        invalid=row('LEFT','LEFT');invalid['label']=None
        with self.assertRaises(ValueError):summarize([invalid])

    def test_class_abstention_cannot_hide_behind_aggregate_coverage(self):
        rows=[row(label,label,label!='LEFT' or i<50) for label in ('LEFT','CENTER','RIGHT') for i in range(100)]
        rows.extend(row('NONPOLITICAL','LEFT',False) for _ in range(100))
        gates=point_estimate_gates(summarize(rows))
        self.assertTrue(gates['raw_accuracy'])
        self.assertTrue(gates['coverage'])
        self.assertTrue(gates['selective_accuracy'])
        self.assertFalse(gates['delivered_per_class_recall'])
