"""Adversarial intake-contract tests. Fixtures are generated, not human references."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "research" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from validate_dataset_manifest import (SCHEMA, load_manifest, normalized_text_sha256,
                                       text_sha256, validate_manifest)


def record(name="dev", split="development"):
    text = f"Generated unit-test fixture {name}: a council met on Tuesday."
    return {
        "id": name, "task": "article_author_framing", "kind": "natural",
        "split": split, "text": text, "text_sha256": text_sha256(text),
        "story_group": f"event-{name}", "duplicate_group": None,
        "exposure": {"pilot": split == "pilot", "training": split == "train", "development": split == "development", "model_selection": False, "calibration": False},
        "source": {"url": f"https://example.invalid/{name}", "publisher": "UNIT TEST FIXTURE ONLY",
                   "acquired_at": "2026-10-03", "rights_status": "documented",
                   "rights_basis": "Generated test fixture, not a real declaration",
                   "rights_reference": "urn:test:generated", "allowed_uses": ["annotation", "evaluation", "training"]},
        "review": {"status": "pending"},
    }


def manifest(records=None):
    return {"schema_version": SCHEMA, "dataset_id": "unit-test-fixture-only",
            "task": {"id": "article_author_framing", "version": "test-v1",
                     "scope": "UNIT TEST ONLY", "label_source": "human_text_annotation"},
            "release_approved": False, "gold_labels_approved": False,
            "exposure_ledger": [], "records": records if records is not None else [record()]}


def declare_review(item):
    item["review"] = {
        "status": "human_adjudicated", "reviewer_ids": ["TEST-reviewer-1", "TEST-reviewer-2"],
        "adjudicator_id": "TEST-adjudicator",
        "reference": {"label": "NONPOLITICAL", "uncertainty_reason": "NONE"},
        "provenance": {"human_attested": True, "blind_to_model_outputs": True,
                       "ai_generated_labels": False, "artifact_sha256": "a" * 64,
                       "rubric_sha256": "b" * 64, "artifact_reference": "urn:test:simulated-review"}}


def declared_complete_manifest():
    value = manifest([record("calibration", "calibration"), record("final", "final_test")])
    value["evaluation_freeze"] = {"protocol_sha256": "c" * 64, "candidate_sha256": "d" * 64, "test_opened": False}
    value["independence_audit"] = {"status": "reviewed", "reviewer_id": "TEST-auditor", "artifact_sha256": "e" * 64}
    for item in value["records"]:
        declare_review(item)
    return value


class DatasetManifestTests(unittest.TestCase):
    def codes(self, value, section="errors"):
        return {item["code"] for item in validate_manifest(value)[section]}

    def test_unfinished_intake_valid_but_never_ready(self):
        result = validate_manifest(manifest())
        self.assertTrue(result["structurally_valid"])
        self.assertFalse(result["declared_final_evaluation_prerequisites_met"])
        self.assertIn("unfinished_human_review", {x["code"] for x in result["prerequisite_blockers"]})
        self.assertFalse(result["release_approved"])

    def test_complete_declarations_do_not_prove_humans_rights_or_release(self):
        result = validate_manifest(declared_complete_manifest())
        self.assertTrue(result["declared_final_evaluation_prerequisites_met"], result)
        for field in ("release_approved", "gold_labels_approved", "human_provenance_verified", "rights_verified"):
            self.assertIs(result[field], False)
        self.assertIn("declarations_not_proof", {x["code"] for x in result["warnings"]})

    def test_same_publisher_allowed_across_independent_stories(self):
        result = validate_manifest(declared_complete_manifest())
        self.assertTrue(result["structurally_valid"])

    def test_hash_matches_exact_unicode_and_whitespace(self):
        value = manifest()
        item = value["records"][0]
        item["text"] = "Cafe\u0301 \U0001f600\nThe hearing opens.\n"
        item["text_sha256"] = text_sha256(item["text"])
        self.assertTrue(validate_manifest(value)["structurally_valid"])
        item["text"] = item["text"].strip()
        self.assertIn("text_hash_mismatch", self.codes(value))

    def test_cross_split_exact_and_normalized_duplicates(self):
        for variant in ("A tax proposal.", " A TAX\nproposal. ", "Ａ tax proposal."):
            with self.subTest(variant=variant):
                value = manifest([record("a", "train"), record("b", "final_test")])
                for item, text in zip(value["records"], ["A tax proposal.", variant]):
                    item["text"] = text
                    item["text_sha256"] = text_sha256(text)
                self.assertIn("cross_split_overlap", self.codes(value))

    def test_cross_split_event_and_duplicate_groups(self):
        for field in ("story_group", "duplicate_group"):
            with self.subTest(field=field):
                value = declared_complete_manifest()
                for item in value["records"]:
                    item[field] = "same-event-or-copy"
                self.assertIn("cross_split_overlap", self.codes(value))

    def test_same_article_url_with_fragment_crosses_splits(self):
        value = declared_complete_manifest()
        value["records"][0]["source"]["url"] = "http://example.invalid/story#one"
        value["records"][1]["source"]["url"] = "https://example.invalid/story#two"
        self.assertIn("cross_split_overlap", self.codes(value))

    def test_within_split_duplicate_warns_without_fabricating_independence(self):
        value = manifest([record("a"), record("b")])
        value["records"][1]["text"] = value["records"][0]["text"]
        value["records"][1]["text_sha256"] = value["records"][0]["text_sha256"]
        result = validate_manifest(value)
        self.assertTrue(result["structurally_valid"])
        self.assertIn("within_split_duplicate", {x["code"] for x in result["warnings"]})

    def test_prior_exposure_ledger_catches_relabelled_record_id(self):
        for key in ("text_sha256", "normalized_text_sha256", "story_group", "source_url", "duplicate_group"):
            with self.subTest(key=key):
                value = declared_complete_manifest()
                item = value["records"][1]
                item["duplicate_group"] = "copy-final"
                entry = {"text_sha256": "f" * 64, "story_group": "old-event", "uses": ["pilot"]}
                entry[key] = (normalized_text_sha256(item["text"]) if key == "normalized_text_sha256"
                              else item["source"]["url"] if key == "source_url" else item[key])
                value["exposure_ledger"] = [entry]
                self.assertIn("prior_exposure_overlap", self.codes(value))

    def test_ledger_missing_or_unusable_is_not_silent(self):
        for ledger in (None, {}, [{"uses": []}]):
            with self.subTest(ledger=ledger):
                value = manifest()
                value["exposure_ledger"] = ledger
                self.assertFalse(validate_manifest(value)["structurally_valid"])

    def test_exposed_holdout_rejected(self):
        for field in ("pilot", "training", "development", "model_selection", "calibration"):
            with self.subTest(field=field):
                value = declared_complete_manifest()
                value["records"][1]["exposure"][field] = True
                self.assertIn("exposed_holdout", self.codes(value))

    def test_calibration_only_reuse_allowed_for_calibration_not_final_test(self):
        value = declared_complete_manifest()
        item = value["records"][0]
        item["exposure"]["calibration"] = True
        value["exposure_ledger"] = [{"text_sha256": item["text_sha256"], "story_group": item["story_group"], "uses": ["calibration"]}]
        self.assertTrue(validate_manifest(value)["declared_final_evaluation_prerequisites_met"])
        value["exposure_ledger"][0]["uses"].append("training")
        self.assertIn("prior_exposure_overlap", self.codes(value))
        value["exposure_ledger"] = []
        item["exposure"]["training"] = True
        self.assertIn("exposed_holdout", self.codes(value))
        value = declared_complete_manifest()
        final = value["records"][1]
        value["exposure_ledger"] = [{"text_sha256": final["text_sha256"], "story_group": final["story_group"], "uses": ["calibration"]}]
        self.assertIn("prior_exposure_overlap", self.codes(value))

    def test_false_as_string_is_not_false(self):
        value = declared_complete_manifest()
        value["records"][1]["exposure"]["pilot"] = "false"
        value["records"][1]["final_test_eligible"] = "false"
        self.assertIn("exposure_boolean", self.codes(value))
        self.assertIn("boolean_type", self.codes(value))

    def test_development_artifact_cannot_be_promoted(self):
        for field, setting, expected in (("development_only", True, "development_only_holdout"),
                                         ("final_test_eligible", False, "ineligible_final_test")):
            for root_level in (True, False):
                with self.subTest(field=field, root_level=root_level):
                    value = declared_complete_manifest()
                    target = value if root_level else value["records"][1]
                    target[field] = setting
                    self.assertIn(expected, self.codes(value))

    def test_adjudicated_pilot_status_remains_development(self):
        value = declared_complete_manifest()
        value["records"][1]["review"]["status"] = "human_adjudicated_development"
        self.assertIn("pilot_review_holdout", self.codes(value))

    def test_synthetic_benchmark_rejected(self):
        value = declared_complete_manifest()
        value["records"][1]["kind"] = "synthetic"
        self.assertIn("synthetic_holdout", self.codes(value))

    def test_incomplete_or_unresolved_human_review_blocks_prerequisites(self):
        for status in ("pending", "in_progress", "unresolved"):
            with self.subTest(status=status):
                value = declared_complete_manifest()
                value["records"][1]["review"]["status"] = status
                result = validate_manifest(value)
                self.assertTrue(result["structurally_valid"])
                self.assertFalse(result["declared_final_evaluation_prerequisites_met"])

    def test_independence_cannot_be_one_reviewer_twice_or_self_adjudication(self):
        for change in ({"reviewer_ids": ["same", "same"]}, {"reviewer_ids": [" SAME ", "same"]},
                       {"adjudicator_id": "TEST-reviewer-1"}, {"adjudicator_id": " test-REVIEWER-1 "}):
            with self.subTest(change=change):
                value = declared_complete_manifest()
                value["records"][1]["review"].update(change)
                self.assertFalse(validate_manifest(value)["structurally_valid"])

    def test_adjudicated_article_must_have_explicit_task_matched_reference(self):
        for reference in (None, {}, {"label": None}, {"label": "NEUTRAL"}, {"label": "MIXED"}, {"spans": []}):
            with self.subTest(reference=reference):
                value = declared_complete_manifest()
                value["records"][1]["review"]["reference"] = reference
                self.assertIn("article_reference_label", self.codes(value))
        for label in ("LEFT", "RIGHT", "CENTER", "NONPOLITICAL", "UNCERTAIN"):
            value = declared_complete_manifest()
            value["records"][1]["review"]["reference"]["label"] = label
            if label == "UNCERTAIN":
                value["records"][1]["review"]["reference"]["uncertainty_reason"] = "MIXED_AUTHOR_POSITIONS"
            self.assertTrue(validate_manifest(value)["structurally_valid"])

    def test_uncertain_is_explicit_and_mixed_not_silently_relabelled(self):
        for label, reason in (("UNCERTAIN", "NONE"), ("UNCERTAIN", None), ("LEFT", "MIXED_AUTHOR_POSITIONS")):
            with self.subTest(label=label, reason=reason):
                value = declared_complete_manifest()
                value["records"][1]["review"]["reference"] = {"label": label, "uncertainty_reason": reason}
                self.assertIn("article_uncertainty_reason", self.codes(value))

    def test_same_task_cannot_silently_mix_adjudication_rubrics(self):
        value = declared_complete_manifest()
        value["records"][1]["review"]["provenance"]["rubric_sha256"] = "f" * 64
        self.assertIn("rubric_version_mismatch", self.codes(value))

    def test_all_exposure_flags_are_required_not_assumed_false(self):
        for flag in ("pilot", "training", "development", "model_selection", "calibration"):
            value = declared_complete_manifest()
            del value["records"][1]["exposure"][flag]
            self.assertIn("exposure_boolean", self.codes(value))

    def phrase_manifest(self):
        value = declared_complete_manifest()
        value["task"]["id"] = "phrase_political_framing"
        for item in value["records"]:
            item["task"] = "phrase_political_framing"
            item["review"]["reference"] = {"spans_assessed": True, "spans": []}
        return value

    def test_empty_phrase_reference_requires_explicit_assessment(self):
        value = self.phrase_manifest()
        self.assertTrue(validate_manifest(value)["structurally_valid"])
        for reference in ({"spans": []}, {"spans_assessed": False, "spans": []},
                          {"spans_assessed": True}, {"label": "NONPOLITICAL"}):
            with self.subTest(reference=reference):
                changed = copy.deepcopy(value)
                changed["records"][1]["review"]["reference"] = reference
                self.assertFalse(validate_manifest(changed)["structurally_valid"])

    def test_phrase_reference_exact_unicode_source_direction_and_attribution(self):
        value = self.phrase_manifest()
        item = value["records"][1]
        item["text"] = "\U0001f600 Raise taxes."
        item["text_sha256"] = text_sha256(item["text"])
        span = {"start": 2, "end": 13, "text": "Raise taxes", "direction": "LEFT", "attribution": "author"}
        item["review"]["reference"]["spans"] = [span]
        self.assertTrue(validate_manifest(value)["structurally_valid"])
        for change, code in (({"start": 3}, "span_text_mismatch"),
                             ({"start": True}, "span_offsets"), ({"end": 100}, "span_offsets"),
                             ({"text": "raise taxes"}, "span_text_mismatch"),
                             ({"direction": "CENTER"}, "span_direction"),
                             ({"attribution": None}, "span_attribution")):
            with self.subTest(change=change):
                changed = copy.deepcopy(value)
                changed["records"][1]["review"]["reference"]["spans"][0].update(change)
                self.assertIn(code, self.codes(changed))
        item["review"]["reference"]["spans"].append(dict(span))
        self.assertIn("overlapping_spans", self.codes(value))

    def test_ai_or_unblinded_review_cannot_claim_human_reference(self):
        for field, setting in (("human_attested", False), ("ai_generated_labels", True),
                               ("blind_to_model_outputs", False), ("human_attested", "true")):
            with self.subTest(field=field, setting=setting):
                value = declared_complete_manifest()
                value["records"][1]["review"]["provenance"][field] = setting
                self.assertIn("review_attestation", self.codes(value))

    def test_unresolved_rights_and_missing_use_block_candidate_evaluation(self):
        for change in ({"rights_status": "unresolved"}, {"allowed_uses": ["redistribution"]}):
            with self.subTest(change=change):
                value = declared_complete_manifest()
                value["records"][1]["source"].update(change)
                self.assertFalse(validate_manifest(value)["declared_final_evaluation_prerequisites_met"])

    def test_freeze_and_independence_audit_are_prerequisites(self):
        for key in ("evaluation_freeze", "independence_audit"):
            with self.subTest(key=key):
                value = declared_complete_manifest()
                del value[key]
                self.assertFalse(validate_manifest(value)["declared_final_evaluation_prerequisites_met"])
        value = declared_complete_manifest()
        value["evaluation_freeze"]["test_opened"] = True
        self.assertIn("test_not_sealed", self.codes(value, "prerequisite_blockers"))

    def test_explicit_task_and_text_level_label_source(self):
        value = manifest()
        value["task"]["label_source"] = "publisher_rating"
        value["records"][0]["task"] = "unknown"
        self.assertIn("label_source", self.codes(value))
        self.assertIn("record_task", self.codes(value))

    def test_approval_claim_is_rejected(self):
        for key in ("release_approved", "gold_labels_approved"):
            for level in ("root", "record"):
                with self.subTest(key=key, level=level):
                    value = manifest()
                    target = value if level == "root" else value["records"][0]
                    target[key] = True
                    self.assertIn("approval_claim", self.codes(value))

    def test_malformed_fields_fail_without_crashing_or_modifying_input(self):
        changes = [("task", {"id": []}), ("records", [False]), ("records", []),
                   ("exposure_ledger", [None])]
        for key, setting in changes:
            with self.subTest(key=key, setting=setting):
                value = manifest()
                value[key] = setting
                original = copy.deepcopy(value)
                self.assertFalse(validate_manifest(value)["structurally_valid"])
                self.assertEqual(value, original)
        for field in ("kind", "split", "review", "source", "text", "id", "exposure"):
            with self.subTest(field=field):
                value = manifest()
                value["records"][0][field] = []
                self.assertFalse(validate_manifest(value)["structurally_valid"])
        for container, field in (("source", "rights_status"), ("review", "status")):
            value = manifest()
            value["records"][0][container][field] = {}
            self.assertFalse(validate_manifest(value)["structurally_valid"])

    def test_report_does_not_echo_source_text(self):
        value = manifest()
        result = json.dumps(validate_manifest(value))
        self.assertNotIn(value["records"][0]["text"], result)

    def test_strict_json_rejects_duplicate_keys_and_nonfinite_constants(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            for raw in ('{"records":[],"records":[]}', '{"number":NaN}', '{"number":Infinity}'):
                with self.subTest(raw=raw):
                    path.write_text(raw)
                    with self.assertRaises(ValueError):
                        load_manifest(path)

    def test_cli_has_distinct_intake_and_prerequisite_failure_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest()))
            command = [sys.executable, str(SCRIPTS / "validate_dataset_manifest.py"), str(path)]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run(command + ["--require-declared-evaluation-prerequisites"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(json.loads(result.stdout)["release_approved"])
            path.write_text('{"records": NaN}')
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)


if __name__ == "__main__":
    unittest.main()
