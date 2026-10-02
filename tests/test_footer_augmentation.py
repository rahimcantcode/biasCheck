import sys
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from footer_augmentation_cv import augment, variants


class AugmentationTests(unittest.TestCase):
    def test_views_preserve_content(self):
        self.assertEqual(variants("Body", ["Footer A", "Footer B"]), ["Body", "Body\n\nFooter A", "Body\n\nFooter B"])

    def test_original_loss_mass_preserved(self):
        rows = [{"text": "A", "label": "LEFT"}, {"text": "B", "label": "RIGHT"}]
        texts, labels, weights = augment(rows, ["F1", "F2"])
        self.assertEqual(len(texts), 6)
        masses = defaultdict(float)
        for label, weight in zip(labels, weights):
            masses[label] += weight
        self.assertEqual(dict(masses), {"LEFT": 1., "RIGHT": 1.})

    def test_no_original_mutation(self):
        row = {"text": "Body", "label": "CENTER"}
        augment([row], ["Footer A", "Footer B"])
        self.assertEqual(row, {"text": "Body", "label": "CENTER"})
