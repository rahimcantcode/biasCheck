import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'scripts'))
from context_sensitivity import views,total_variation


class ContextSensitivityTests(unittest.TestCase):
    def test_partition_preserves_content(self):
        text='Title\n\nFirst\n\nSecond\n\nThird'
        parts=views(text)
        self.assertEqual(parts['full'],text)
        self.assertEqual(parts['title']+'\n\n'+parts['body'],text)

    def test_invalid_structure_rejected(self):
        for text in ('Title','Title\n\nBody','Title\n\n\n\nSecond\n\nThird'):
            with self.assertRaises(ValueError):views(text)

    def test_total_variation(self):
        self.assertEqual(total_variation({'A':1,'B':0},{'B':1,'A':0}),1)
        self.assertEqual(total_variation({'A':1},{'A':1}),0)
        with self.assertRaises(ValueError):total_variation({'A':1},{'B':1})
