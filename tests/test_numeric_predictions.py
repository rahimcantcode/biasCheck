import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.scripts.report_contract import require_numeric_predictions
from research.scripts.calibrate import fit


def fixture():
    return dict(split='validation',annotation_provenance=dict(human_reviewed=True,reference='synthetic fixture'),
        model=dict(id2label={'0':'LEFT','1':'RIGHT','2':'CENTER'}),
        predictions=[dict(id='a',text_sha256='a'*64,gold='CENTER',logits=[-1,0,2.5],token_count=40)])


class NumericPredictionTests(unittest.TestCase):
    def test_valid_unchanged(self):
        r=fixture();before=copy.deepcopy(r)
        require_numeric_predictions(r);self.assertEqual(r,before)

    def test_nonfinite_and_malformed_logits(self):
        for value in ([0,0,float('nan')],[0,0,float('inf')],[0,0,True],[0,'1',2],[],[1,2],[[1],2,3],None):
            r=fixture();r['predictions'][0]['logits']=value
            with self.subTest(value=value),self.assertRaises(ValueError):require_numeric_predictions(r)

    def test_invalid_tokens(self):
        for value in (-1,1.5,True,'40',None):
            r=fixture();r['predictions'][0]['token_count']=value
            with self.subTest(value=value),self.assertRaises(ValueError):require_numeric_predictions(r)

    def test_mapping_rejected(self):
        for mapping in ({'0':'LEFT','1':'LEFT','2':'RIGHT'},{'1':'LEFT','2':'RIGHT','3':'CENTER'},{'0':None,'1':'RIGHT','2':'CENTER'},None):
            r=fixture();r['model']['id2label']=mapping
            with self.assertRaises(ValueError):require_numeric_predictions(r)

    def test_negative_rows_also_checked(self):
        r=fixture();r['predictions'][0].update(gold='NONPOLITICAL',logits=[0,1,float('nan')])
        with self.assertRaises(ValueError):require_numeric_predictions(r)

    def test_unknown_reference(self):
        r=fixture();r['predictions'][0]['gold']='CENTRE'
        with self.assertRaises(ValueError):require_numeric_predictions(r)

    def test_fit_rejects_before_optimizer(self):
        r=fixture();r['predictions'][0]['logits']=[0,1,float('nan')]
        with self.assertRaisesRegex(ValueError,'finite numeric'):fit(r)

    def test_valid_synthetic_fit_stays_unapproved(self):
        r=fixture();r.update(mode='article',data_sha256='d'*64)
        r['model'].update(weights_sha256='w',config_sha256='c',tokenizer_sha256='t',
                          aggregation='test',max_length=512,stride=64)
        r['predictions']=[]
        for i in range(120):
            logits=[-2.,-2.,-2.];logits[i%3]=3.
            r['predictions'].append(dict(id=str(i),text_sha256=format(i,'064x'),
                gold=r['model']['id2label'][str(i%3)],logits=logits,token_count=40))
        policy=fit(r)
        self.assertIs(policy['release_approved'],False)
        self.assertEqual(policy['validation_coverage'],1.)


if __name__=='__main__':unittest.main()
