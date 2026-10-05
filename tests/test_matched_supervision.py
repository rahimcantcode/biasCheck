import sys
import unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research' / 'scripts'))
from matched_supervision import sample_ids


class MatchedTests(unittest.TestCase):
    def setUp(self):
        self.rows = {str(i): {'label': ('LEFT','CENTER','RIGHT')[i % 3]} for i in range(15)}
        self.train = list(self.rows)[:12]
        self.counts = {'LEFT': 2, 'CENTER': 3, 'RIGHT': 1}

    def test_counts_and_no_held_rows(self):
        ids = sample_ids(self.rows, self.train, self.counts, 42, 0)
        self.assertEqual(dict(Counter(self.rows[i]['label'] for i in ids)), self.counts)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(ids) <= set(self.train))

    def test_deterministic(self):
        self.assertEqual(sample_ids(self.rows, self.train, self.counts, 42, 0),
                         sample_ids(self.rows, self.train, self.counts, 42, 0))

    def test_impossible_count(self):
        with self.assertRaises(ValueError):
            sample_ids(self.rows, self.train, {**self.counts, 'LEFT': 5}, 42, 0)


if __name__ == '__main__': unittest.main()
