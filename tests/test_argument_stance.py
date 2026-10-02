"""Synthetic unit tests only: do not load held-out or legacy benchmark text."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "research/scripts/prepare_argument_stance.py"
spec = importlib.util.spec_from_file_location("prepare_argument_stance", SCRIPT)
stance = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stance)


def item(i, label=0, votes=None, proposition=None, locution=None):
    votes = votes if votes is not None else [label] * 3
    return {"id": i, "label": label, "votes": votes, "unanimous": len(set(votes)) == 1,
            "proposition": proposition or f"Context for {i}", "locution": locution or f"Spoken words for {i}"}


class ArgumentStanceTests(unittest.TestCase):
    def test_join_preserves_both_fields_without_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / stance.SAMPLE
            sample.parent.mkdir(parents=True)
            with sample.open("w", newline="") as out:
                w = csv.DictWriter(out, fieldnames=["META_id", "Proposition", "Locution"])
                w.writeheader()
                w.writerow({"META_id": "row", "Proposition": "Named policy context", "Locution": "That must change"})
            label = root / stance.LABELS
            with label.open("w", newline="") as out:
                w = csv.DictWriter(out, fieldnames=["meta_id", "a1_label", "a2_label", "a3_label", "judgements_maj", "a1_id", "model_score"])
                w.writeheader()
                w.writerow({"meta_id": "row", "a1_label": "1", "a2_label": "0", "a3_label": "1", "judgements_maj": "1", "a1_id": "private", "model_score": "0.4"})
            rows = stance.load_joined(root)
            self.assertEqual(rows[0]["proposition"], "Named policy context")
            self.assertEqual(rows[0]["locution"], "That must change")
            self.assertEqual(rows[0]["votes"], [1, 0, 1])
            self.assertFalse(rows[0]["unanimous"])
            self.assertNotIn("a1_id", rows[0])
            self.assertNotIn("model_score", rows[0])
            label.write_text(label.read_text().replace("row,1,0,1,1", "row,1,0,1,0"))
            with self.assertRaisesRegex(ValueError, "majority"):
                stance.load_joined(root)

    def test_exact_field_duplicate_groups_stay_together(self):
        rows = [item("a", proposition="A shared context!"), item("b", proposition="a SHARED context"), item("c")]
        groups, audit = stance.group_rows(rows)
        self.assertEqual(groups["a"], groups["b"])
        self.assertNotEqual(groups["a"], groups["c"])
        split = stance.split_groups(groups)
        self.assertEqual(split["a"], split["b"])
        self.assertGreater(audit["exact_field_edges"], 0)
        reverse, _ = stance.group_rows(list(reversed(rows)))
        self.assertEqual(groups, reverse)
        self.assertEqual(split, stance.split_groups(reverse))

    def test_near_duplicate_grouping(self):
        a = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty"
        b = a + " again"
        rows = [item("a", proposition=a), item("b", proposition=b)]
        groups, audit = stance.group_rows(rows)
        self.assertEqual(groups["a"], groups["b"])
        self.assertEqual(audit["near_field_edges"], 1)
        self.assertFalse(stance.near_duplicate("a short phrase", "another short phrase"))

    def test_source_nodesets_and_named_archives_grouped(self):
        rows = [item(c) for c in "abcde"]
        provenance = {"a": [("episode_one", "nodeset1", "2020-01-01")],
                      "b": [("episode_one", "nodeset2", "2021-12-01")],
                      "c": [("qt30", "nodeset2", "2022-01-01")],
                      "d": [("qt30", "nodeset3", "2022-01-01")],
                      "e": []}
        groups, audit = stance.group_rows(rows, provenance)
        self.assertEqual(groups["a"], groups["b"])
        self.assertEqual(groups["b"], groups["c"])
        self.assertNotEqual(groups["c"], groups["d"])
        self.assertNotEqual(groups["d"], groups["e"])
        self.assertEqual(audit["source_match_counts"]["unmatched"], 1)
        split = stance.split_groups(groups)
        for left in groups:
            for right in groups:
                if groups[left] == groups[right]:
                    self.assertEqual(split[left], split[right])

    def test_source_index_requires_both_context_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / stance.SOURCE_GRAPHS / "qt30"
            folder.mkdir(parents=True)
            data = {"nodes": [{"nodeID": "1", "type": "L", "text": "Speaker: Spoken words"},
                               {"nodeID": "2", "type": "YA", "text": "Asserting"},
                               {"nodeID": "3", "type": "I", "text": "Contextual proposition", "timestamp": "2022-01-01"}],
                    "edges": [{"fromID": "1", "toID": "2"}, {"fromID": "2", "toID": "3"}]}
            (folder / "nodeset1.json").write_text(json.dumps(data))
            index, _ = stance.source_index(root)
            self.assertIn(("contextual proposition", "spoken words"), index)
            self.assertNotIn(("contextual proposition", "other words"), index)

    def test_all_input_denominator_for_missing_invalid_and_abstain(self):
        gold = [item("a", 0), item("b", 1), item("c", 1, [1, 0, 1]), item("d", 0)]
        result = stance.evaluate(gold, [{"id": "a", "label": 0}, {"id": "b", "label": "abstain"}, {"id": "c", "label": "1"}])
        m = result["metrics"]["all"]
        self.assertEqual(m["n_all_inputs"], 4)
        self.assertEqual(m["accuracy_all_inputs"], .25)
        self.assertEqual(m["balanced_accuracy_all_inputs"], .25)
        self.assertAlmostEqual(m["macro_f1_all_inputs"], 1 / 3)
        self.assertEqual(m["valid_prediction_coverage"], .25)
        self.assertEqual(m["invalid_n"], 2)
        self.assertEqual(m["abstain_n"], 1)
        self.assertEqual(result["metrics"]["disputed"]["n_all_inputs"], 1)
        self.assertEqual(result["metrics"]["unanimous"]["n_all_inputs"], 3)
        self.assertEqual(result["metrics"]["human_yes_votes_2"]["n_all_inputs"], 1)
        self.assertIsNone(result["metrics"]["human_yes_votes_2"]["balanced_accuracy_all_inputs"])

    def test_duplicate_ids_invalidate_instead_of_choose_best(self):
        result = stance.evaluate([item("a", 1)], [{"id": "a", "label": 0}, {"id": "a", "label": 1}])
        self.assertEqual(result["metrics"]["all"]["invalid_n"], 1)
        self.assertEqual(result["invalid_reasons"], {"duplicate_id": 1})

    def test_unknown_ids_and_unassignable_records_are_reported(self):
        result = stance.evaluate([item("a")], [None, [], {"id": "unknown", "label": 0}, {"id": "a", "label": True}])
        self.assertEqual(result["unknown_id_records"], 1)
        self.assertEqual(result["unassignable_or_parse_error_records"], 2)
        self.assertEqual(result["metrics"]["all"]["invalid_n"], 1)

    def test_null_and_extra_schema_fields_invalid(self):
        for pred in ({"id": "a", "label": None}, {"id": "a", "label": 0, "political": False}, {"id": "a"}):
            self.assertEqual(stance.evaluate([item("a")], [pred])["metrics"]["all"]["invalid_n"], 1)

    def test_parse_failures_not_silently_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "predictions.jsonl"
            path.write_text('{"id":"a","label":0}\nnot json\n{"id":"b","label":\n')
            predictions = stance.load_predictions(path)
            result = stance.evaluate([item("a"), item("b", 1)], predictions)
            self.assertEqual(result["output_records"], 3)
            self.assertEqual(result["unassignable_or_parse_error_records"], 2)
            self.assertEqual(result["metrics"]["all"]["n_all_inputs"], 2)
            self.assertEqual(result["metrics"]["all"]["accuracy_all_inputs"], .5)

    def test_full_correct_score_and_confusion(self):
        gold = [item("a", 0), item("b", 1)]
        result = stance.evaluate(gold, [{"id": "a", "label": 0}, {"id": "b", "label": 1}])
        for name in ("accuracy_all_inputs", "balanced_accuracy_all_inputs", "macro_f1_all_inputs", "valid_prediction_coverage"):
            self.assertEqual(result["metrics"]["all"][name], 1)
        self.assertEqual(result["metrics"]["all"]["class_support"], {"0": 1, "1": 1})

    def test_bad_gold_fails_closed(self):
        for gold in ([], [item("a"), item("a")], [item("a", 1, [0, 0, 0])]):
            with self.assertRaises(ValueError):
                stance.evaluate(gold, [])

    def test_extra_output_records_break_contract_even_with_full_coverage(self):
        result = stance.evaluate([item("a")], [{"id": "a", "label": 0}, {"id": "other", "label": 1}, None])
        self.assertEqual(result["metrics"]["all"]["valid_prediction_coverage"], 1)
        self.assertFalse(result["output_contract_valid"])
        self.assertTrue(result["all_inputs_have_binary_prediction"])

    def test_generation_error_cannot_smuggle_valid_label(self):
        result = stance.evaluate([item("a")], [{"id": "a", "label": 0, "error": "generation failed"}])
        self.assertEqual(result["metrics"]["all"]["invalid_n"], 1)
        self.assertEqual(result["invalid_reasons"], {"generation_error": 1})

    def test_gold_hash_and_original_candidate_bind_reserved_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gold = root / "renamed_not_holdout.jsonl"
            predictions = root / "predictions.jsonl"
            sealed = root / "test_reserved.sealed_inputs.jsonl"
            stance.write_jsonl(gold, [item("a")])
            stance.write_jsonl(predictions, [{"id": "a", "label": 0}])
            stance.write_jsonl(sealed, [{"id": "a", "proposition": "Context", "locution": "Words"}])
            protocol = root / "protocol.json"
            stance.write_json(protocol, {"partitions": {"test_reserved": {"gold_sha256": stance.sha256(gold.read_bytes())}},
                                        "prepared_file_sha256": {sealed.name: stance.sha256(sealed.read_bytes())}})
            candidate = root / "candidate.json"
            freeze = {"candidate_id": "one", "model_id": "model", "model_revision": "frozen-revision",
                      "prompt_sha256": "a" * 64, "decoding": {"temperature": 0}, "runtime": "unit-test",
                      "protocol_sha256": stance.sha256(protocol.read_bytes())}
            stance.write_json(candidate, freeze)
            with self.assertRaisesRegex(ValueError, "candidate freeze"):
                stance.evaluate_files(gold, predictions, protocol, root)
            with self.assertRaisesRegex(ValueError, "not been released"):
                stance.evaluate_files(gold, predictions, protocol, root, candidate)
            stance.release_test(root, protocol, candidate)
            result = stance.evaluate_files(gold, predictions, protocol, root, candidate)
            self.assertEqual(result["partition"], "test_reserved")
            self.assertEqual(result["metrics"]["all"]["accuracy_all_inputs"], 1)
            with self.assertRaisesRegex(ValueError, "already released"):
                stance.release_test(root, protocol, candidate)
            freeze["candidate_id"] = "two"
            stance.write_json(candidate, freeze)
            with self.assertRaisesRegex(ValueError, "original test release"):
                stance.evaluate_files(gold, predictions, protocol, root, candidate)
            gold.write_text(gold.read_text() + "\n")
            with self.assertRaisesRegex(ValueError, "unknown or tampered"):
                stance.evaluate_files(gold, predictions, protocol, root, candidate)

    def test_prompt_is_native_binary_and_two_field(self):
        self.assertIn("Proposition", stance.PROMPT)
        self.assertIn("Locution", stance.PROMPT)
        self.assertIn("UK political debate", stance.PROMPT)
        self.assertIn("label 0 does not mean nonpolitical", stance.PROMPT)


if __name__ == "__main__":
    unittest.main()
