import hashlib
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research'/'scripts'))
from pilot_context_audit import verified_text


class PilotContextTests(unittest.TestCase):
    def test_frozen_text_required(self):
        text='Frozen article text'
        item={'id':'example','text_sha256':hashlib.sha256(text.encode()).hexdigest()}
        self.assertEqual(verified_text(item,text),text)
        with self.assertRaises(ValueError):verified_text(item,text+' changed')
