import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research' / 'scripts'))
from ensemble_oof import combine


def sample(scores, fold=0):
    return {'id':'example','fold':fold,'prediction':max(scores,key=scores.get),'probabilities':scores}


class EnsembleTests(unittest.TestCase):
    def test_average_uses_class_names_not_insertion_order(self):
        a=sample({'LEFT':.8,'CENTER':.1,'RIGHT':.1})
        b=sample({'RIGHT':.5,'CENTER':.1,'LEFT':.4})
        result=combine(a,b)
        self.assertEqual(result['prediction'],'LEFT')
        self.assertAlmostEqual(result['probabilities']['LEFT'],.6)
        self.assertFalse(result['components_agree'])

    def test_mismatched_fold_rejected(self):
        a=sample({'LEFT':1.,'CENTER':0.,'RIGHT':0.})
        with self.assertRaises(ValueError):combine(a,{**a,'fold':1})

    def test_invalid_probability_rejected(self):
        a=sample({'LEFT':1.,'CENTER':0.,'RIGHT':0.})
        for value in (float('nan'),2.,-.1):
            b={**a,'probabilities':{'LEFT':value,'CENTER':0.,'RIGHT':0.}}
            with self.assertRaises(ValueError):combine(a,b)

    def test_fixed_tie_order(self):
        a=sample({'LEFT':1.,'CENTER':0.,'RIGHT':0.})
        b=sample({'LEFT':0.,'CENTER':0.,'RIGHT':1.})
        self.assertEqual(combine(a,b)['prediction'],'LEFT')
