import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from training_label_provenance_cv import select_unanimous_fit


class TrainingLabelProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id": str(i), "label": label, "strict_agreement": strict}
                     for i, (label, strict) in enumerate([
                         ("LEFT", True), ("CENTER", True), ("RIGHT", True),
                         ("LEFT", False), ("RIGHT", True), ("CENTER", False)])]

    def test_filters_only_fit_rows_keeps_held_ids_unchanged(self):
        held = ["4", "5"]
        fit = select_unanimous_fit(self.rows, ["0", "1", "2", "3"], held)
        self.assertEqual([row["id"] for row in fit], ["0", "1", "2"])
        self.assertEqual(held, ["4", "5"])
        self.assertEqual(len(self.rows), 6)

    def test_held_agreement_and_labels_cannot_change_fit_selection(self):
        original = select_unanimous_fit(self.rows, ["0", "1", "2", "3"], ["4", "5"])
        self.rows[4]["strict_agreement"] = False
        self.rows[5]["label"] = "LEFT"
        self.assertEqual(original, select_unanimous_fit(self.rows, ["0", "1", "2", "3"], ["4", "5"]))

    def test_missing_class_blocks_instead_of_oversampling(self):
        self.rows[1]["strict_agreement"] = False
        with self.assertRaisesRegex(ValueError, "lacks at least one class"):
            select_unanimous_fit(self.rows, ["0", "1", "2", "3"], ["4", "5"])

    def test_rejects_overlap_duplicates_and_incomplete_partition(self):
        for fit, held in [(["0", "1", "2", "3", "4"], ["4", "5"]),
                          (["0", "1", "2", "3", "3"], ["4", "5"]),
                          (["0", "1", "2"], ["4", "5"])]:
            with self.assertRaises(ValueError):
                select_unanimous_fit(self.rows, fit, held)


if __name__ == "__main__":
    unittest.main()
