import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from audit_development_overlap import shingles, overlap, shared_paragraphs


class DevelopmentOverlapTests(unittest.TestCase):
    def test_case_and_punctuation(self):
        self.assertEqual(shingles("One, TWO three four five!"), shingles("one two three four five"))

    def test_short_text_does_not_look_duplicate(self):
        self.assertEqual(overlap(shingles("a b"), shingles("a b"))["jaccard"], 0)

    def test_exact(self):
        self.assertEqual(overlap(shingles("one two three four five six"), shingles("one two three four five six"))["jaccard"], 1)

    def test_containment_distinct_from_jaccard(self):
        score = overlap(shingles("a b c d e"), shingles("a b c d e f g"))
        self.assertEqual(score["shorter_containment"], 1)
        self.assertAlmostEqual(score["jaccard"], 1 / 3)

    def test_disjoint(self):
        self.assertEqual(overlap(shingles("a b c d e"), shingles("f g h i j"))["shared_5grams"], 0)

    def test_paragraphs_require_cross_split_and_minimum_length(self):
        text = "one two three four five six seven eight"
        groups = shared_paragraphs({"train": [{"id": "a", "text": text + "\n\nshort"}],
                                   "validation": [{"id": "b", "text": text.upper() + "\n\nshort"}]})
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["train"], ["a"])
        self.assertEqual(groups[0]["validation"], ["b"])

    def test_same_split_only_not_reported(self):
        self.assertEqual(shared_paragraphs({"train": [{"id": "a", "text": "one two three four five six seven eight"}], "validation": []}), [])
