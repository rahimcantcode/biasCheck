import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research' / 'scripts'))
from feature_coverage_audit import coverage


class CoverageTests(unittest.TestCase):
    def test_occurrences_are_not_distinct_counts(self):
        r = coverage(['a','a','b','a b'], {'a': 0, 'a b': 1})
        self.assertEqual(r['retained_occurrences'], 3)
        self.assertEqual(r['retained_distinct'], 2)
        self.assertEqual(r['occurrence_fraction'], .75)

    def test_empty_is_not_zero_coverage(self):
        self.assertIsNone(coverage([], {})['occurrence_fraction'])

    def test_unknown_and_full_coverage(self):
        self.assertEqual(coverage(['x'], {})['occurrence_fraction'], 0)
        self.assertEqual(coverage(['x'], {'x': 0})['occurrence_fraction'], 1)


if __name__ == '__main__': unittest.main()
