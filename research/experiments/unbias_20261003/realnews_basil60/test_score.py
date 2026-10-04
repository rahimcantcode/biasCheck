"""Small independent examples prevent inflated matching and attribution scores."""
import hashlib
import unittest
from score import aggregate, match_count, score_case, token_offsets, token_set, wilson


def example(text, gold, predicted, *, failure=False):
    digest = hashlib.sha256(text.encode()).hexdigest()
    case = {'id': 'unit-only', 'event_id': 'synthetic-fixture', 'stratum': 'lexical' if gold else 'unannotated',
            'publisher': 'unit', 'source_sha256': digest, 'text': text,
            'gold': [{'start': a, 'end': b, 'bias': 'lex', 'quoted': False} for a, b in gold]}
    row = {'id': case['id'], 'source_sha256': digest, 'seconds': 1, 'http_status': 503 if failure else 200}
    if not failure:
        row['response'] = {'resolved_text': text, 'source_sha256': digest, 'release_approved': False,
                           'status': 'suggestions' if predicted else 'no_suggestions', 'rejected': [],
                           'spans': [{'start': a, 'end': b, 'text': text[a:b],
                                      'bias_type': 'loaded_language', 'attribution': 'unknown'}
                                     for a, b in predicted]}
    return case, row


class ScoringTests(unittest.TestCase):
    def test_broad_prediction_cannot_claim_two_span_detections(self):
        result = score_case(*example('bad ordinary evil', [(0, 3), (13, 17)], [(0, 17)]))
        self.assertEqual(result['overlap_span']['tp'], 1)
        self.assertEqual(result['overlap_span']['fn'], 1)
        self.assertEqual(result['token']['tp'], 2)
        self.assertEqual(result['token']['fp'], 1)
        self.assertEqual(result['iou50_span']['tp'], 0)
        self.assertEqual(result['exact_span']['tp'], 0)

    def test_matching_finds_reassignment(self):
        pred = [{'a', 'b'}, {'a'}]
        gold = [{'a'}, {'b'}]
        self.assertEqual(match_count(pred, gold, lambda a, b: bool(a & b)), 2)

    def test_punctuation_gives_no_overlap_credit(self):
        tokens = token_offsets('“café”, ordinary')
        self.assertEqual(len(tokens), 2)
        self.assertEqual(token_set(tokens, [{'start': 0, 'end': 1}]), set())
        self.assertEqual(token_set(tokens, [{'start': 1, 'end': 5}]), {0})

    def test_failed_positive_stays_missed_and_failed(self):
        scored = score_case(*example('bad ordinary', [(0, 3)], [], failure=True))
        self.assertEqual(scored['token']['fn'], 1)
        report = aggregate([scored])
        self.assertEqual(report['sentence']['fn'], 1)
        self.assertEqual(report['statuses'], {'request_failure': 1})

    def test_control_highlight_is_false_positive(self):
        scored = score_case(*example('ordinary words', [], [(0, 8)]))
        report = aggregate([scored])
        self.assertEqual(report['sentence']['fp'], 1)
        self.assertEqual(report['token']['fp'], 1)
        self.assertEqual(report['attributed_predictions'], 0)

    def test_duplicate_gold_tokens_do_not_double_count(self):
        scored = score_case(*example('bad ordinary', [(0, 3), (0, 3)], [(0, 3)]))
        self.assertEqual(scored['token']['tp'], 1)
        self.assertEqual(scored['exact_span']['tp'], 1)
        self.assertEqual(scored['token']['f1'], 1)

    def test_wilson_zero_errors_does_not_mean_certainty(self):
        lower, upper = wilson(0, 20)
        self.assertAlmostEqual(lower, 0)
        self.assertGreater(upper, .15)
        self.assertLess(upper, .17)


if __name__ == '__main__':
    unittest.main()
