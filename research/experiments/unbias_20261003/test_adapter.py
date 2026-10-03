"""Focused source-offset and failure-semantics tests; no model runtime needed."""
from __future__ import annotations

import copy
import hashlib
import math
import unittest

from adapter import adapt_unbias_v2, decode_bio, exact_offsets, span_metrics


def segment(phrase="reckless", **changes):
    value = {
        "original": phrase,
        "replacement": "controversial",
        "severity": "Low",
        "bias_type": "loaded_language",
        "reasoning": "An evaluative characterization.",
    }
    value.update(changes)
    return value


_DEFAULT_SEVERITY = object()


def native(*segments, severity=_DEFAULT_SEVERITY, rewrite="The policy was debated."):
    return {
        "severity": (1 if segments else 0) if severity is _DEFAULT_SEVERITY else severity,
        "biased_segments": list(segments),
        "unbiased_text": rewrite,
    }


class ExactOffsetsTests(unittest.TestCase):
    def test_unique_phrase_uses_exclusive_end(self):
        self.assertEqual(exact_offsets("A reckless policy.", "reckless"), (2, 10))

    def test_unmatched_phrase_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "^unmatched_phrase$"):
            exact_offsets("A cautious policy.", "reckless")

    def test_repeated_phrase_is_ambiguous(self):
        with self.assertRaisesRegex(ValueError, "^ambiguous_occurrence$"):
            exact_offsets("reckless then reckless", "reckless")

    def test_overlapping_literal_occurrences_are_also_ambiguous(self):
        with self.assertRaisesRegex(ValueError, "^ambiguous_occurrence$"):
            exact_offsets("aaa", "aa")

    def test_empty_and_nonstring_phrases_are_rejected(self):
        for phrase in ("", None, 1, False, [], {}):
            with self.subTest(phrase=phrase):
                with self.assertRaisesRegex(ValueError, "^empty_or_invalid_phrase$"):
                    exact_offsets("A policy.", phrase)

    def test_unicode_is_not_normalized(self):
        text = "🙂 ‘cafe\u0301’"
        self.assertEqual(exact_offsets(text, "cafe\u0301"), (3, 8))
        with self.assertRaisesRegex(ValueError, "^unmatched_phrase$"):
            exact_offsets(text, "café")


class NativeAdapterTests(unittest.TestCase):
    def assert_partial(self, result, reason):
        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual(result["spans"], [])
        self.assertEqual(result["rejected"], [{"native_index": 0, "reason": reason}])
        self.assertFalse(result["attribution_supported"])

    def test_empty_valid_result_is_no_suggestions(self):
        result = adapt_unbias_v2("A policy.", native())
        self.assertEqual(result["status"], "no_suggestions")
        self.assertEqual(result["spans"], [])
        self.assertEqual(result["rejected"], [])

    def test_unicode_quotation_and_whitespace_are_preserved(self):
        text = "\t🙂 Senator Lee said “reckless.”\n"
        result = adapt_unbias_v2(text, native(segment()))
        span = result["spans"][0]
        self.assertEqual(result["status"], "suggestions")
        self.assertEqual(span["start"], text.index("reckless"))
        self.assertEqual(span["end"], text.index("reckless") + len("reckless"))
        self.assertEqual(text[span["start"]:span["end"]], "reckless")
        self.assertEqual(span["attribution"], "unknown")
        self.assertFalse(result["attribution_supported"])
        self.assertEqual(result["offset_unit"], "unicode_codepoint")
        self.assertTrue(result["end_exclusive"])
        self.assertEqual(result["source_sha256"], hashlib.sha256(text.encode()).hexdigest())

    def test_native_explanation_does_not_create_speaker_attribution(self):
        result = adapt_unbias_v2(
            "Lee said ‘reckless’.",
            native(segment(reasoning="The author uses a loaded phrase.")),
        )
        self.assertEqual(result["spans"][0]["attribution"], "unknown")
        self.assertFalse(result["attribution_supported"])

    def test_repeated_phrase_never_becomes_empty_success(self):
        self.assert_partial(
            adapt_unbias_v2("reckless then reckless", native(segment())),
            "ambiguous_occurrence",
        )

    def test_unmatched_phrase_never_becomes_empty_success(self):
        self.assert_partial(
            adapt_unbias_v2("A policy.", native(segment())), "unmatched_phrase"
        )

    def test_empty_phrase_is_a_segment_failure(self):
        self.assert_partial(
            adapt_unbias_v2("A policy.", native(segment(""))),
            "empty_or_invalid_phrase",
        )

    def test_valid_span_survives_another_segment_failure(self):
        result = adapt_unbias_v2(
            "A reckless policy.", native(segment(), segment("made-up cue"))
        )
        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual([span["text"] for span in result["spans"]], ["reckless"])
        self.assertEqual(result["rejected"], [{"native_index": 1, "reason": "unmatched_phrase"}])

    def test_duplicate_predictions_both_rejected(self):
        result = adapt_unbias_v2("A reckless policy.", native(segment(), segment()))
        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual(result["spans"], [])
        self.assertEqual(result["rejected"], [
            {"native_index": 0, "reason": "overlap_or_duplicate"},
            {"native_index": 1, "reason": "overlap_or_duplicate"},
        ])

    def test_nested_predictions_both_rejected(self):
        result = adapt_unbias_v2(
            "A reckless policy.", native(segment("reckless policy"), segment())
        )
        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual(result["spans"], [])
        self.assertEqual({r["native_index"] for r in result["rejected"]}, {0, 1})

    def test_all_members_of_overlap_chain_rejected(self):
        result = adapt_unbias_v2(
            "abcdef", native(segment("abc"), segment("cde"), segment("ef"))
        )
        self.assertEqual(result["spans"], [])
        self.assertEqual({r["native_index"] for r in result["rejected"]}, {0, 1, 2})

    def test_adjacent_spans_are_not_overlapping(self):
        result = adapt_unbias_v2("abcdef", native(segment("abc"), segment("def")))
        self.assertEqual(result["status"], "suggestions")
        self.assertEqual([(s["start"], s["end"]) for s in result["spans"]], [(0, 3), (3, 6)])

    def test_unchanged_and_empty_replacements_are_accepted(self):
        for replacement in ("reckless", ""):
            with self.subTest(replacement=replacement):
                result = adapt_unbias_v2("reckless", native(segment(replacement=replacement)))
                self.assertEqual(result["status"], "suggestions")

    def test_top_level_schema_is_exact(self):
        valid = native(segment())
        for bad in (None, [], {**valid, "bias_found": True}, {k: v for k, v in valid.items() if k != "unbiased_text"}):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "^invalid_native_schema$"):
                    adapt_unbias_v2("reckless", bad)

    def test_severity_rejects_bool_float_nan_and_out_of_range(self):
        for severity in (True, False, 1.0, math.nan, math.inf, -1, 11, "1", None):
            with self.subTest(severity=severity):
                with self.assertRaisesRegex(ValueError, "^invalid_severity_or_segments$"):
                    adapt_unbias_v2("reckless", native(segment(), severity=severity))

    def test_inconsistent_severity_is_rejected(self):
        for value in (native(segment(), severity=0), native(severity=1)):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "^inconsistent_severity$"):
                    adapt_unbias_v2("reckless", value)

    def test_segment_collection_and_rewrite_types_are_strict(self):
        for key, bad in (("biased_segments", ()), ("biased_segments", {}), ("unbiased_text", math.nan), ("unbiased_text", None)):
            value = native()
            value[key] = bad
            with self.subTest(key=key, bad=bad):
                with self.assertRaises(ValueError):
                    adapt_unbias_v2("A policy.", value)

    def test_excess_segment_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "^invalid_native_schema$"):
            adapt_unbias_v2("reckless", native(*[segment() for _ in range(65)]))

    def test_segment_schema_is_exact(self):
        for bad in (None, [], {**segment(), "start": 0}, {k: v for k, v in segment().items() if k != "reasoning"}):
            with self.subTest(bad=bad):
                self.assert_partial(adapt_unbias_v2("reckless", native(bad)), "invalid_segment_schema")

    def test_invalid_segment_labels_are_rejected_including_containers(self):
        for key in ("severity", "bias_type"):
            for value in ("unknown", None, math.nan, [], {}):
                with self.subTest(key=key, value=value):
                    self.assert_partial(
                        adapt_unbias_v2("reckless", native(segment(**{key: value}))),
                        "invalid_segment_labels",
                    )

    def test_nonstring_segment_text_including_nan_is_rejected(self):
        for key in ("reasoning", "replacement"):
            for value in (None, math.nan, [], 1):
                with self.subTest(key=key, value=value):
                    self.assert_partial(
                        adapt_unbias_v2("reckless", native(segment(**{key: value}))),
                        "invalid_segment_text",
                    )

    def test_adapter_does_not_mutate_native_result(self):
        value = native(segment())
        before = copy.deepcopy(value)
        adapt_unbias_v2("reckless", value)
        self.assertEqual(value, before)


class BioTests(unittest.TestCase):
    def test_wordpieces_merge_using_original_text_offsets(self):
        text = "A reckless policy."
        result = decode_bio(text, [(0, 0), (0, 1), (2, 6), (6, 10), (11, 17), (17, 18), (0, 0)],
                            ["O", "O", "B-BIAS", "I-BIAS", "O", "O", "O"])
        self.assertEqual(result["spans"], [{"start": 2, "end": 10, "text": "reckless", "attribution": "unknown"}])
        self.assertEqual(result["orphan_i_count"], 0)

    def test_special_tokens_never_create_spans(self):
        result = decode_bio("plain", [(0, 0), (0, 5), (0, 0)], ["B-BIAS", "O", "I-BIAS"])
        self.assertEqual(result["status"], "no_suggestions")
        self.assertEqual(result["orphan_i_count"], 0)

    def test_original_unicode_and_whitespace_inside_span_are_preserved(self):
        text = "🙂 “reckless  tax”"
        start = text.index("reckless")
        tax = text.index("tax")
        result = decode_bio(text, [(0, 0), (start, start + 8), (tax, tax + 3), (0, 0)], ["O", "B-BIAS", "I-BIAS", "O"])
        self.assertEqual(result["spans"][0]["text"], "reckless  tax")
        self.assertEqual(result["spans"][0]["start"], start)
        self.assertFalse(result["attribution_supported"])
        self.assertEqual(result["offset_unit"], "unicode_codepoint")
        self.assertTrue(result["end_exclusive"])

    def test_orphan_i_starts_span_and_is_counted(self):
        result = decode_bio("bad plain bad", [(0, 3), (4, 9), (10, 13)], ["I-BIAS", "O", "I-BIAS"])
        self.assertEqual(result["orphan_i_count"], 2)
        self.assertEqual([(s["start"], s["end"]) for s in result["spans"]], [(0, 3), (10, 13)])

    def test_b_starts_new_span_even_when_adjacent(self):
        result = decode_bio("abcdef", [(0, 3), (3, 6)], ["B-BIAS", "B-BIAS"])
        self.assertEqual([s["text"] for s in result["spans"]], ["abc", "def"])

    def test_o_and_special_tokens_close_active_spans(self):
        result = decode_bio("bad plain bad", [(0, 3), (0, 0), (4, 9), (10, 13)], ["B-BIAS", "O", "O", "B-BIAS"])
        self.assertEqual([s["text"] for s in result["spans"]], ["bad", "bad"])

    def test_length_mismatch_is_failure_not_no_suggestions(self):
        with self.assertRaisesRegex(ValueError, "^length_mismatch$"):
            decode_bio("bad", [(0, 3)], [])

    def test_invalid_bio_label_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "^invalid_bio_label$"):
            decode_bio("bad", [(0, 3)], ["LABEL_1"])

    def test_invalid_offsets_are_rejected(self):
        offsets = [[(-1, 2)], [(0, 4)], [(1, 1)], [(2, 1)], [(0, 2), (1, 3)], [(1, 3), (0, 1)], [(False, 3)], [(0.0, 3)], [(0, 3.0)]]
        for case in offsets:
            with self.subTest(offsets=case):
                with self.assertRaisesRegex(ValueError, "^invalid_token_offsets$"):
                    decode_bio("bad", case, ["O"] * len(case))

    def test_special_offsets_require_exact_integer_types(self):
        for pair in ((False, 0), (0, False), (0.0, 0), (0, 0.0)):
            with self.subTest(pair=pair):
                with self.assertRaisesRegex(ValueError, "^invalid_token_offsets$"):
                    decode_bio("bad", [pair], ["O"])


class SpanMetricsTests(unittest.TestCase):
    def test_exact_boundaries_only_with_no_attribution_credit(self):
        expected = [{"start": 1, "end": 5, "attribution": "author"}, {"start": 10, "end": 15}]
        predicted = [{"start": 1, "end": 5, "attribution": "unknown"}, {"start": 10, "end": 14}, {"start": 20, "end": 25}]
        self.assertEqual(span_metrics(expected, predicted), {"true_positive": 1, "false_positive": 2, "false_negative": 1})

    def test_duplicate_boundaries_do_not_inflate_counts(self):
        span = {"start": 0, "end": 3}
        self.assertEqual(span_metrics([span], [span, span]), {"true_positive": 1, "false_positive": 0, "false_negative": 0})


if __name__ == "__main__":
    unittest.main()
