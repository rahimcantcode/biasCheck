import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'scripts'))
from repetition_challenge import cases
from repetition_diagnostic import distinct_context


class ChallengeTests(unittest.TestCase):
    def test_controls_and_known_gaps_remain_explicit(self):
        probe={id:(kind,text) for id,kind,text in cases('Short title','New information.')}
        self.assertEqual(len(probe),10)
        for id in ('blank-lines','crlf','spaces-in-paragraphs'):
            self.assertEqual(distinct_context(probe[id][1]),'Short title')
        for id in ('single-newlines','spaces-only','numbered','punctuation'):
            self.assertEqual(distinct_context(probe[id][1]),probe[id][1])
        self.assertEqual(distinct_context(probe['repeat-plus-body'][1]),'Short title\n\nNew information.')

    def test_probe_generation_is_deterministic(self):
        self.assertEqual(cases('Title','Body'),cases('Title','Body'))
