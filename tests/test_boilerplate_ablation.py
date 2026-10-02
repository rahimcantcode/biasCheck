import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from boilerplate_ablation import paragraph_hash, strip_footers


class BoilerplateTests(unittest.TestCase):
    def test_no_match_preserves_bytes(self):
        text = "Title\n\nArticle  with   spacing.\n"
        self.assertEqual(strip_footers(text), (text, []))

    def test_exact_paragraph_only(self):
        footer = "Publisher copyright notice."
        hashes = {paragraph_hash(footer)}
        self.assertEqual(strip_footers("Body.\n\n" + footer, hashes)[0], "Body.")
        text = "Body quotes Publisher copyright notice. as evidence."
        self.assertEqual(strip_footers(text, hashes), (text, []))

    def test_case_whitespace_normalization(self):
        cleaned, removed = strip_footers("Body.\n\nFOOTER  TEXT", {paragraph_hash("footer text")})
        self.assertEqual(cleaned, "Body.")
        self.assertEqual(len(removed), 1)

    def test_empty_output_rejected(self):
        with self.assertRaises(ValueError):
            strip_footers("footer", {paragraph_hash("footer")})

    def test_idempotent(self):
        hashes = {paragraph_hash("footer")}
        cleaned, _ = strip_footers("Body.\n\nfooter", hashes)
        self.assertEqual(strip_footers(cleaned, hashes), (cleaned, []))
