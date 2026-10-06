import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/scripts'))
from oof_uncertainty import resample


class OOFUncertaintyTests(unittest.TestCase):
    def test_identical_predictions_have_zero_difference(self):
        values,counts,groups=resample([[1,1],[0,0],[1,1]],['a','a','b'],30)
        np.testing.assert_array_equal(values[:,0],values[:,1])
        np.testing.assert_array_equal(counts.sum(axis=1),2)

    def test_weights_use_rows_not_group_means(self):
        values,counts,_=resample([[1],[1],[0]],['a','a','b'],50)
        np.testing.assert_allclose(values[:,0],2*counts[:,0]/(2*counts[:,0]+counts[:,1]))

    def test_reproducible(self):
        a=resample([[1],[0]],['a','b'],20)
        b=resample([[1],[0]],['a','b'],20)
        np.testing.assert_array_equal(a[0],b[0])

    def test_bad_alignment(self):
        with self.assertRaises(ValueError):resample([[1]],['a','b'])

    def test_invalid_groups_rejected(self):
        for group in (None,'','  ',float('nan'),123,True):
            with self.subTest(group=group),self.assertRaisesRegex(ValueError,'event-string'):
                resample([[1]],[group])

    def test_empty_model_axis_rejected(self):
        with self.assertRaisesRegex(ValueError,'matrix'):
            resample(np.empty((2,0)),['a','b'])

    def test_invalid_draw_count_rejected(self):
        for draws in (True,False,0,-1,1.5,'20'):
            with self.subTest(draws=draws),self.assertRaisesRegex(ValueError,'draw count'):
                resample([[1]],['a'],draws)

    def test_one_group_is_valid_but_degenerate(self):
        values,counts,groups=resample([[1],[0]],['a','a'],5)
        np.testing.assert_array_equal(values,np.full((5,1),.5))
        np.testing.assert_array_equal(counts,np.ones((5,1)))
        self.assertEqual(groups,['a'])


if __name__=='__main__':unittest.main()
