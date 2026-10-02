import io
import sys
import unittest
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "scripts"))
from training_linear_cv import (
    LABELS, OVRNBSVM, allowlisted_csv_records, candidate_grid,
    confusion_statistics, event_family_groups, make_folds, nb_log_count_ratio,
    uncertainty, validate_folds, validate_oof, vectorizer,
)


class TrainingLinearCVTests(unittest.TestCase):
    def test_nb_formula_binary_smoothed_normalized_counts(self):
        # Repetition in a document is deliberately binarized.
        matrix = sparse.csr_matrix([[9, 1, 0], [1, 0, 0], [0, 5, 1]])
        observed = nb_log_count_ratio(matrix, [True, True, False])
        p, q = np.array([3., 2., 1.]), np.array([1., 2., 2.])
        np.testing.assert_allclose(observed, np.log(p / p.sum()) - np.log(q / q.sum()))
        np.testing.assert_array_equal(matrix.toarray(), [[9, 1, 0], [1, 0, 0], [0, 5, 1]])

    def test_nb_ratios_and_prior_counts_use_fit_rows_only(self):
        fit = sparse.csr_matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1],
                                 [1, 1, 0], [0, 1, 1], [1, 0, 1]])
        labels = ["LEFT", "CENTER", "RIGHT", "LEFT", "CENTER", "RIGHT"]
        model = OVRNBSVM().fit(fit, labels)
        before = [ratio.copy() for ratio in model.ratios_]
        for label, ratio in zip(LABELS, before):
            np.testing.assert_allclose(ratio, nb_log_count_ratio(fit, np.array(labels) == label))
        # Held observations can be transformed/predicted but cannot refit ratios.
        held = sparse.csr_matrix([[1000, 0, 0], [0, 0, 1000]])
        self.assertEqual(model.decision_function(held).shape, (2, 3))
        self.assertEqual(len(model.predict(held)), 2)
        for observed, expected in zip(model.ratios_, before):
            np.testing.assert_array_equal(observed, expected)
        self.assertEqual(model.fit_n_, 6)
        self.assertEqual(model.class_counts_, {label: 2 for label in LABELS})
        contaminated = nb_log_count_ratio(sparse.vstack([fit, held]),
                                         np.array(labels + ["LEFT", "LEFT"]) == "LEFT")
        self.assertFalse(np.allclose(contaminated, before[0]))

    def test_nb_rejects_missing_classes_and_invalid_counts(self):
        with self.assertRaises(ValueError):
            nb_log_count_ratio(sparse.eye(2), [True, True])
        with self.assertRaises(ValueError):
            nb_log_count_ratio(sparse.csr_matrix([[-1], [0]]), [True, False])
        with self.assertRaises(ValueError):
            nb_log_count_ratio(sparse.eye(2), [True, False], alpha=0)
        with self.assertRaises(ValueError):
            OVRNBSVM().fit(sparse.eye(2), ["LEFT", "RIGHT"])

    def test_vocabulary_and_idf_fit_only_on_training_fold(self):
        texts = ["shared trainword trainword", "shared trainword", "shared another"]
        for kind in ("lr", "linearsvc", "nbsvm"):
            features = vectorizer(kind)
            features.fit_transform(texts)
            original = dict(features.vocabulary_)
            before_idf = features.idf_.copy() if hasattr(features, "idf_") else None
            features.transform(["heldoutsecret heldoutsecret", "heldoutsecret shared"])
            self.assertNotIn("heldoutsecret", features.vocabulary_)
            self.assertEqual(original, features.vocabulary_)
            if before_idf is not None:
                np.testing.assert_array_equal(before_idf, features.idf_)
                self.assertAlmostEqual(features.idf_[original["trainword"]], np.log(4 / 3) + 1)

    def test_event_alias_union_is_transitive_and_normalized(self):
        rows = [{"id": "a", "event": " Event A "}, {"id": "b", "event": "event   a"},
                {"id": "c", "event": "Event B"}, {"id": "d", "event": "event b"},
                {"id": "e", "event": "Event C"}, {"id": "f", "event": "Other"}]
        groups = event_family_groups(rows, [["b", "c"], ["d", "e"]])
        self.assertEqual(len(set(groups[:5])), 1)
        self.assertNotEqual(groups[0], groups[5])
        self.assertEqual(event_family_groups(list(reversed(rows)), [["e", "d"], ["c", "b"]]), list(reversed(groups)))
        with self.assertRaises(ValueError):
            event_family_groups(rows, [["a", "reserved-id"]])

    def test_folds_preserve_aliases_and_oof_once(self):
        rows = [{"id": f"id-{i:02}", "event": f"event-{i // 2}"} for i in range(18)]
        groups, folds = make_folds(rows, [["id-00", "id-04"]])
        validate_folds(rows, groups, folds)
        held = Counter(rows[i]["id"] for _, indices in folds for i in indices)
        self.assertEqual(held, Counter({row["id"]: 1 for row in rows}))
        for train_indices, held_indices in folds:
            self.assertFalse({groups[i] for i in train_indices} & {groups[i] for i in held_indices})
        validate_oof(rows, [{"id": key} for key in held])
        with self.assertRaises(ValueError):
            validate_oof(rows, [{"id": rows[0]["id"]}] * len(rows))
        with self.assertRaises(ValueError):
            validate_folds(rows, groups, folds + [folds[0]])
        train, held = folds[0]
        with self.assertRaises(ValueError):
            validate_folds(rows, groups, [(np.append(train, train[0]), held)] + folds[1:])

    def test_extraction_discards_nonallowlisted_row_before_fields(self):
        # Nonselected malformed/poison values must never become retained records.
        content = b'docid,title,human_label\nkeep,training,Left\nreserved,DO_NOT_USE\nother,private,Right\n'
        selected = list(allowlisted_csv_records(content, {"keep"}))
        self.assertEqual(selected, [{"docid": "keep", "title": "training", "human_label": "Left"}])
        with self.assertRaises(ValueError):
            list(allowlisted_csv_records(content, {"reserved"}))

    def test_grid_is_bounded_and_word_only(self):
        candidates = candidate_grid()
        self.assertEqual(len(candidates), 14)
        self.assertEqual(len({c["name"] for c in candidates}), 14)
        for view in ("raw", "clean"):
            self.assertEqual([c["C"] for c in candidates if c["view"] == view and c["kind"] == "lr"], [1.])
            for kind in ("linearsvc", "nbsvm"):
                self.assertEqual([c["C"] for c in candidates if c["view"] == view and c["kind"] == kind], [.1, 1., 10.])
                self.assertEqual(vectorizer(kind).analyzer, "word")
                self.assertEqual(vectorizer(kind).ngram_range, (1, 2))

    def test_bootstrap_is_paired_and_deterministic(self):
        rows = [{"id": str(i), "label": LABELS[i % 3]} for i in range(9)]
        perfect = [{"id": row["id"], "prediction": row["label"]} for row in rows]
        oof = {"raw_lr_C1": perfect, "clean_lr_C1": list(reversed(perfect))}
        first = uncertainty(rows, list(range(9)), oof, draws=100)
        self.assertEqual(first, uncertainty(rows, list(range(9)), oof, draws=100))
        self.assertEqual(first["candidates"]["clean_lr_C1"]["paired_difference_intervals"]["raw_lr_C1"]["macro_f1"], [0., 0.])
        self.assertFalse(first["independent_accuracy_interval"])
        values = confusion_statistics(np.array([[1, 1, 0], [0, 1, 0], [0, 0, 1]]))
        self.assertEqual(values["recall_LEFT"], .5)
        self.assertEqual(values["agreement"], .75)


if __name__ == "__main__":
    unittest.main()
