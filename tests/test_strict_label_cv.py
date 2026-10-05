import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research' / 'scripts'))
from strict_label_cv import supervised_ids


class StrictTests(unittest.TestCase):
    def setUp(self):
        self.rows = {k: dict(label=v, strict_agreement=True) for k, v in [('a','LEFT'),('b','CENTER'),('c','RIGHT')]}
        self.rows['d'] = dict(label='RIGHT', strict_agreement=False)
        self.rows['held'] = dict(label='LEFT', strict_agreement=True)

    def test_only_training_unanimous(self):
        self.assertEqual(supervised_ids(self.rows, ['a','b','c','d']), ['a','b','c'])

    def test_invalid_flag(self):
        self.rows['d']['strict_agreement'] = 'false'
        with self.assertRaises(ValueError): supervised_ids(self.rows, ['a','b','c','d'])

    def test_missing_class(self):
        self.rows['c']['strict_agreement'] = False
        with self.assertRaises(ValueError): supervised_ids(self.rows, ['a','b','c','d'])


if __name__ == '__main__': unittest.main()
