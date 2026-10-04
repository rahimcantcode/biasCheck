import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/scripts'))
from hierarchy_cv import combine


class HierarchyTests(unittest.TestCase):
    def test_center_boundary(self):
        label,scores=combine(.5,{'LEFT':.9,'RIGHT':.1})
        self.assertEqual(label,'CENTER')
        self.assertAlmostEqual(sum(scores.values()),1)

    def test_hard_gate_differs_from_joint_argmax(self):
        label,scores=combine(.49,{'LEFT':.6,'RIGHT':.4})
        self.assertEqual(label,'LEFT')
        self.assertEqual(max(scores,key=scores.get),'CENTER')

    def test_invalid_distribution(self):
        with self.assertRaises(ValueError):
            combine(.3,{'LEFT':.8,'RIGHT':.8})

    def test_nonfinite(self):
        with self.assertRaises(ValueError):
            combine(float('nan'),{'LEFT':.8,'RIGHT':.2})


if __name__=='__main__':
    unittest.main()
