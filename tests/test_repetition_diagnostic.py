import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'scripts'))
from repetition_diagnostic import diagnose,distinct_context,repetition_context


class RepetitionTests(unittest.TestCase):
    def test_repeating_adds_no_distinct_paragraph_words(self):
        r=diagnose('\n\n'.join(['Same short headline']*8))
        self.assertEqual(r['word_count'],24)
        self.assertEqual(r['distinct_paragraph_word_count'],3)
        self.assertEqual(r['duplicate_paragraph_n'],7)

    def test_whitespace_normalization(self):
        r=diagnose('One  paragraph\n\nOne paragraph')
        self.assertEqual(r['distinct_paragraph_n'],1)

    def test_case_and_negation_not_collapsed(self):
        r=diagnose('US policy\n\nus policy\n\nnot US policy')
        self.assertEqual(r['distinct_paragraph_n'],3)

    def test_empty_is_not_full_retention(self):
        r=diagnose(' \n\n ')
        self.assertEqual(r['paragraph_n'],0)
        self.assertIsNone(r['retained_word_fraction'])

    def test_distinct_input_preserved_byte_for_byte(self):
        text='  US policy\n\n\nSecond   paragraph\n'
        self.assertEqual(distinct_context(text),text)

    def test_repeated_context_reduces_to_first_occurrence(self):
        self.assertEqual(distinct_context('One  headline\n\nOne headline\n\nDifferent'),
                         'One  headline\n\nDifferent')

    def test_whole_input_cycles_ignore_whitespace_only(self):
        for separator in (' ','\n','\n\n','\r\n'):
            self.assertEqual(repetition_context(separator.join(['One headline']*8)),'One headline')

    def test_partial_cycle_preserved(self):
        self.assertEqual(repetition_context('One headline One headline Extra'),'One headline One headline Extra')

    def test_negation_and_case_prevent_cycle(self):
        for text in ('Policy approved Policy not approved','US policy us policy'):
            self.assertEqual(repetition_context(text),text)

    def test_empty_periodic_view(self):
        self.assertEqual(repetition_context(''),'')

    def test_periodic_falls_back_to_paragraph_context(self):
        self.assertEqual(repetition_context('One headline\n\nOne headline\n\nNew evidence'),
                         'One headline\n\nNew evidence')
