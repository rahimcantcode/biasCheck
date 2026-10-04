import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.scripts.report_contract import require_human_provenance, require_matching_reports
from research.scripts.calibrate import fit
from research.scripts.evaluate_policy import evaluate


def fixture():
    return {'mode': 'article', 'split': 'validation',
            'annotation_provenance': {'human_reviewed': True, 'reference': 'test fixture, not actual annotation'},
            'model': {'weights_sha256': 'w', 'config_sha256': 'c', 'tokenizer_sha256': 't',
                      'aggregation': 'test', 'max_length': 512, 'stride': 64,
                      'id2label': {'0': 'LEFT', '1': 'RIGHT', '2': 'CENTER'}}}


class ReportContractTests(unittest.TestCase):
    def test_matching_contract(self):
        require_matching_reports(fixture(), fixture())

    def test_only_boolean_true(self):
        for value in ('false', 'true', 1, False, None, [], {}):
            with self.subTest(value=value):
                report=fixture()
                report['annotation_provenance']['human_reviewed']=value
                with self.assertRaises(ValueError):
                    require_human_provenance(report)

    def test_blank_or_nonstring_reference(self):
        for value in ('', '  ', 1, True, ['reference']):
            report=fixture()
            report['annotation_provenance']['reference']=value
            with self.assertRaises(ValueError):
                require_human_provenance(report)

    def test_each_model_field_must_match(self):
        for key in fixture()['model']:
            a,b=fixture(),fixture()
            b['model'][key]='changed'
            with self.subTest(field=key), self.assertRaises(ValueError):
                require_matching_reports(a,b)

    def test_missing_fields_not_equal(self):
        a,b=fixture(),fixture()
        del a['model']['weights_sha256']
        del b['model']['weights_sha256']
        with self.assertRaises(ValueError):
            require_matching_reports(a,b)

    def test_mode_mismatch(self):
        a,b=fixture(),fixture()
        b['mode']='sentence'
        with self.assertRaises(ValueError):
            require_matching_reports(a,b)

    def test_calibration_rejects_false_string_before_fitting(self):
        report=fixture()
        report['annotation_provenance']['human_reviewed']='false'
        with self.assertRaisesRegex(ValueError,'boolean'):
            fit(report)

    def test_evaluation_rejects_mismatched_model_before_inference(self):
        a,b=fixture(),fixture()
        b['model']['weights_sha256']='other'
        original=copy.deepcopy((a,b))
        with self.assertRaisesRegex(ValueError,'model mismatch'):
            evaluate(a,{},b)
        self.assertEqual((a,b),original)


if __name__=='__main__':
    unittest.main()
