import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research.scripts.calibrate import fit


def report():
    mapping = {'0': 'LEFT', '1': 'RIGHT', '2': 'CENTER'}
    return dict(split='validation', mode='article', data_sha256='d'*64,
        annotation_provenance=dict(human_reviewed=True, reference='Synthetic test fixture, not human evidence'),
        model=dict(id2label=mapping, weights_sha256='w', config_sha256='c', tokenizer_sha256='t',
            aggregation='test', max_length=512, stride=64),
        predictions=[dict(id=str(i), text_sha256=format(i,'064x'), gold=mapping[str(i % 3)],
            logits=[3. if j == i % 3 else -2. for j in range(3)], token_count=40) for i in range(120)])


class OptimizerTests(unittest.TestCase):
    def test_invalid_requirements_rejected_before_optimization(self):
        for name in ('target','min_coverage'):
            for value in (True,False,np.bool_(True),None,'0.9',[],0,-.1,1.01,float('nan'),float('inf'),float('-inf')):
                with self.subTest(name=name,value=value),patch('research.scripts.calibrate.minimize_scalar') as optimizer:
                    with self.assertRaisesRegex(ValueError,name):
                        fit(report(),**{name:value})
                    optimizer.assert_not_called()

    def test_valid_requirements_retained_without_release(self):
        for target,coverage in ((.9,.8),(1,1),(np.float64(.95),np.float32(.75))):
            with self.subTest(target=target,coverage=coverage):
                result=fit(report(),target=target,min_coverage=coverage)
                self.assertEqual(result['requested_accuracy'],float(target))
                self.assertEqual(result['requested_min_coverage'],float(coverage))
                self.assertIs(result['release_approved'],False)

    def test_unsuccessful_fit_rejected_even_with_usable_temperature(self):
        with patch('research.scripts.calibrate.minimize_scalar', return_value=SimpleNamespace(success=False, x=0., fun=.01)):
            with self.assertRaisesRegex(ValueError, 'optimization'): fit(report())

    def test_nonfinite_or_out_of_bounds_result(self):
        for x, fun in [(float('nan'), .01), (float('inf'), .01), (0., float('nan')), (0., float('inf')), (4., .01), (-4., .01)]:
            with self.subTest(x=x, fun=fun), patch('research.scripts.calibrate.minimize_scalar',
                return_value=SimpleNamespace(success=True, x=x, fun=fun)):
                with self.assertRaisesRegex(ValueError, 'optimization'): fit(report())

    def test_invalid_softmax_rejected(self):
        for scores in (np.full((120,3), np.nan), np.full((120,3), 2.)):
            with patch('research.scripts.calibrate.softmax', return_value=scores):
                with self.assertRaisesRegex(ValueError, 'probabilities'): fit(report())

    def test_real_optimizer_still_produces_unapproved_candidate(self):
        result = fit(report())
        self.assertIs(result['release_approved'], False)
        self.assertEqual(result['validation_coverage'], 1.)
        self.assertTrue(np.isfinite(result['temperature']))

    def test_missing_reference_class_rejected(self):
        for absent in ('LEFT','CENTER','RIGHT'):
            r=report()
            replacement='LEFT' if absent!='LEFT' else 'RIGHT'
            index={v:int(k) for k,v in r['model']['id2label'].items()}[replacement]
            for row in r['predictions']:
                if row['gold']==absent:
                    row['gold']=replacement
                    row['logits']=[3. if j==index else -2. for j in range(3)]
            with self.subTest(absent=absent),self.assertRaisesRegex(ValueError,'all three political classes'):
                fit(r)

    def test_candidate_retains_reference_class_counts(self):
        result=fit(report())
        self.assertEqual(result['validation_class_counts'],{'LEFT':40,'CENTER':40,'RIGHT':40})


if __name__ == '__main__': unittest.main()
