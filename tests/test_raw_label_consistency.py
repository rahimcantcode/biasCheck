import copy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.scripts.evaluate_policy import evaluate
from research.scripts.report_contract import raw_label_from_logits


def fixtures(logits,raw):
    model=dict(weights_sha256='w',config_sha256='c',tokenizer_sha256='t',aggregation='test',
               max_length=512,stride=64,id2label={'0':'LEFT','1':'RIGHT','2':'CENTER'})
    test=dict(model=model,split='test',mode='article',data_sha256='test',
        annotation_provenance=dict(human_reviewed=True,reference='synthetic fixture'),
        predictions=[dict(id='test',text_sha256='a'*64,gold='RIGHT',logits=logits,
                          raw_label=raw,token_count=40)])
    valid=copy.deepcopy(test);valid.update(split='validation',data_sha256='valid')
    valid['predictions'][0].update(id='valid',text_sha256='b'*64)
    policy=dict(calibration_data_sha256='valid',validated_modes=['article'],release_approved=False)
    return test,policy,valid


class RawLabelTests(unittest.TestCase):
    def simulate(self,logits,raw,abstain=False):
        args=fixtures(logits,raw);before=copy.deepcopy(args)
        backend=types.ModuleType('backend.model')
        backend.validate_policy=lambda *args: None
        backend.classify_scores=lambda logits,*args: (np.asarray(logits), 'test_abstention' if abstain else None)
        # Isolate report assembly/metrics; not a numerical backend inference test.
        with patch.dict(sys.modules,{'backend.model':backend}):result=evaluate(*args)
        self.assertEqual(args,before)
        self.assertIs(result['release_approved'],False)
        return result

    def test_stale_correct_label_cannot_inflate_raw_accuracy(self):
        r=self.simulate([5,0,-1],'RIGHT')
        self.assertEqual(r['metrics']['raw_accuracy'],0)
        self.assertEqual(r['predictions'][0]['raw_label'],'LEFT')
        self.assertEqual(r['predictions'][0]['source_report_raw_label'],'RIGHT')

    def test_stale_wrong_label_does_not_reduce_raw_accuracy(self):
        r=self.simulate([0,5,-1],'LEFT')
        self.assertEqual(r['metrics']['raw_accuracy'],1)

    def test_abstention_keeps_raw_and_delivered_separate(self):
        r=self.simulate([0,5,-1],'LEFT',True)
        self.assertEqual(r['metrics']['raw_accuracy'],1)
        self.assertEqual(r['metrics']['delivered']['correct_fraction'],0)
        self.assertIsNone(r['predictions'][0]['label'])

    def test_missing_raw_label_reconstructed(self):
        r=self.simulate([0,5,-1],None)
        self.assertEqual(r['predictions'][0]['raw_label'],'RIGHT')

    def test_mapping_and_tie_order(self):
        self.assertEqual(raw_label_from_logits(dict(logits=[2,2,0]),
            {'0':'CENTER','1':'LEFT','2':'RIGHT'}),'CENTER')


if __name__=='__main__':unittest.main()
