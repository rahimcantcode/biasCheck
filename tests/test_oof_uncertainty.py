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


if __name__=='__main__':unittest.main()
