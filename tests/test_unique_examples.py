import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.scripts.report_contract import require_unique_examples
from research.scripts.calibrate import fit
from research.scripts.evaluate_policy import evaluate


def report():
    return dict(mode='article',split='test',data_sha256='test',
        annotation_provenance=dict(human_reviewed=True,reference='synthetic test fixture'),
        model=dict(weights_sha256='w',config_sha256='c',tokenizer_sha256='t',
                   aggregation='a',max_length=512,stride=64,id2label={'0':'LEFT','1':'RIGHT','2':'CENTER'}),
        predictions=[dict(id='one',text_sha256='a'*64),dict(id='two',text_sha256='b'*64)])


class UniqueExamplesTests(unittest.TestCase):
    def test_unique_unchanged(self):
        value=report();before=copy.deepcopy(value)
        require_unique_examples(value)
        self.assertEqual(value,before)

    def test_duplicate_id(self):
        value=report();value['predictions'][1]['id']='one'
        with self.assertRaisesRegex(ValueError,'Duplicate'):require_unique_examples(value)

    def test_duplicate_hash_case_insensitive(self):
        value=report();value['predictions'][1]['text_sha256']='A'*64
        with self.assertRaisesRegex(ValueError,'Duplicate'):require_unique_examples(value)

    def test_malformed_rows(self):
        for rows in (None,[],{},[None],[dict(id=' ',text_sha256='a'*64)],[dict(id='x',text_sha256='not-a-hash')]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                require_unique_examples(dict(predictions=rows))

    def test_calibration_duplicate_before_fit(self):
        value=report();value['split']='validation';value['predictions']*=50
        with self.assertRaisesRegex(ValueError,'Duplicate'):fit(value)

    def test_evaluation_duplicate_before_inference(self):
        test=report();test['predictions']*=150
        valid=report();valid.update(split='validation',data_sha256='valid')
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            evaluate(test,dict(calibration_data_sha256='valid'),valid)

    def test_cross_split_hash_case_insensitive(self):
        test=report();valid=report();valid.update(split='validation',data_sha256='valid')
        valid['predictions']=[dict(id='other',text_sha256='A'*64)]
        with self.assertRaisesRegex(ValueError,'overlap: text_sha256'):
            evaluate(test,dict(calibration_data_sha256='valid'),valid)


if __name__=='__main__':unittest.main()
