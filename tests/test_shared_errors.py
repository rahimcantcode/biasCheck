import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/scripts'))
from shared_errors import align, counts


class SharedErrorTests(unittest.TestCase):
    def test_duplicate_ids_rejected(self):
        row=dict(id='a',fold=0,prediction='CENTER')
        with self.assertRaises(ValueError):align([row,row],['a'],{'a':0})

    def test_wrong_fold_rejected(self):
        with self.assertRaises(ValueError):align([dict(id='a',fold=1,prediction='LEFT')],['a'],{'a':0})

    def test_missing_id_rejected(self):
        with self.assertRaises(ValueError):align([],['a'],{'a':0})

    def test_consensus_can_be_wrong(self):
        result=counts([dict(correct_n=0,predictions=dict(a='LEFT',b='LEFT')),
                       dict(correct_n=1,predictions=dict(a='CENTER',b='RIGHT'))])
        self.assertEqual(result,dict(n=2,all_wrong=1,all_correct=0,any_correct=1,disagreement=1))


if __name__=='__main__':unittest.main()
