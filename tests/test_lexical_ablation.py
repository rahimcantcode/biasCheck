import sys
import unittest
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/scripts'))
from unigram_cv import candidate_vectorizer


class LexicalAblationTests(unittest.TestCase):
    def test_only_requested_setting_changes(self):
        baseline=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
        original=baseline.get_params()
        for ablation,parameter,value in [('unigram','ngram_range',(1,1)),('binary_tf','binary',True)]:
            result=candidate_vectorizer(baseline,ablation)
            self.assertEqual(result.get_params(),dict(original,**{parameter:value}))
            self.assertEqual(baseline.get_params(),original)

    def test_unknown_ablation_rejected(self):
        with self.assertRaises(ValueError): candidate_vectorizer(TfidfVectorizer(),'invalid')
