import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'scripts'))
from learning_curve import subsets


class LearningCurveTests(unittest.TestCase):
    def test_nested_and_complete_groups(self):
        rows=[{'id':str(i),'event':str(i//2)} for i in range(16)]
        result=subsets(rows,20261002)
        ids=[{r['id'] for r in result[f]} for f in ('0.25','0.5','1.0')]
        self.assertTrue(ids[0]<ids[1]<ids[2])
        self.assertEqual(ids[2],{r['id'] for r in rows})
        for selected in result.values():
            groups={r['event'] for r in selected}
            self.assertEqual(len(selected),len(groups)*2)

    def test_reproducible_without_mutating_input(self):
        rows=[{'id':str(i),'event':str(i)} for i in range(8)]
        saved=list(rows)
        self.assertEqual(subsets(rows,7),subsets(rows,7))
        self.assertEqual(rows,saved)

    def test_order_changes_only_subsets_not_full_training_set(self):
        rows=[{'id':str(i),'event':str(i)} for i in range(20)]
        a,b=subsets(rows,20261002),subsets(rows,20261003)
        self.assertNotEqual(a['0.25'],b['0.25'])
        self.assertEqual(a['1.0'],b['1.0'])
