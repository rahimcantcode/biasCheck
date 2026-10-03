"""Validate declarations for a new corpus, without reading held-out text elsewhere.

This is an intake check, not a rights audit, human-verification service, or release
approval. It performs no network requests and opens only the supplied manifest.
Hashes identify exact UTF-8 snapshots, not whether their labels are correct.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


SCHEMA = "biascheck-dataset-intake-v1"
SPLITS = {"pilot", "train", "development", "calibration", "final_test"}
EXPOSURES = {"pilot", "training", "development", "model_selection", "calibration"}
TASKS = {"article_author_framing", "phrase_political_framing"}
ARTICLE_LABELS = {"LEFT", "RIGHT", "CENTER", "NONPOLITICAL", "UNCERTAIN"}
UNCERTAINTY_REASONS = {"NONE", "INSUFFICIENT_CONTEXT", "MIXED_AUTHOR_POSITIONS",
                       "ATTRIBUTION_UNCLEAR", "SARCASM_OR_AMBIGUITY", "OUTSIDE_US_SCHEME", "OTHER"}
RIGHTS_USES = {"annotation", "training", "evaluation", "redistribution", "commercial"}
REVIEW_STATUSES = {"pending", "in_progress", "unresolved", "human_adjudicated",
                   "human_adjudicated_development"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalized_text_sha256(text):
    """Catch formatting/case variants; semantic or translated duplicates need review."""
    normalized = " ".join(unicodedata.normalize("NFKC", text).casefold().split())
    return text_sha256(normalized)


def _nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def _hash(value):
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _choice(value, choices):
    return isinstance(value, str) and value in choices


def _reviewer_key(value):
    return unicodedata.normalize("NFKC", value).strip().casefold()


def _source_key(value):
    if not isinstance(value, str):
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme in {"http", "https"} and parts.hostname:
            # Ignore fragments and scheme; retain queries because they can identify
            # distinct articles. Tracking-query variants need curated duplicate groups.
            return urlunsplit(("https", parts.netloc.lower(), parts.path, parts.query, ""))
        if parts.scheme == "urn" and parts.path:
            return value
    except ValueError:
        pass
    return None


def validate_manifest(manifest):
    errors = []
    blockers = []
    warnings = []

    def issue(items, code, location, message):
        items.append({"code": code, "location": location, "message": message})

    def error(code, location, message):
        issue(errors, code, location, message)

    def block(code, location, message):
        issue(blockers, code, location, message)

    def warn(code, location, message):
        issue(warnings, code, location, message)

    if not isinstance(manifest, dict):
        manifest = {}
        error("manifest_type", "$", "Manifest must be an object.")
    if manifest.get("schema_version") != SCHEMA:
        error("schema_version", "schema_version", f"Expected {SCHEMA}.")
    if not _nonempty(manifest.get("dataset_id")):
        error("dataset_id", "dataset_id", "A nonempty dataset ID is required.")
    for flag in ("release_approved", "gold_labels_approved"):
        if flag in manifest and manifest[flag] is not False:
            error("approval_claim", flag, "Intake cannot declare gold or release approval.")
    for flag in ("development_only", "final_test_eligible"):
        if flag in manifest and type(manifest[flag]) is not bool:
            error("boolean_type", flag, "Expected a JSON boolean.")

    task = manifest.get("task")
    if not isinstance(task, dict):
        task = {}
        error("task_type", "task", "An explicit versioned task definition is required.")
    if not _choice(task.get("id"), TASKS):
        error("task_id", "task.id", "Use an explicit supported text-level task.")
    for key in ("version", "scope"):
        if not _nonempty(task.get(key)):
            error("task_definition", f"task.{key}", "Required nonempty task definition.")
    if task.get("label_source") != "human_text_annotation":
        error("label_source", "task.label_source", "Publisher ratings or AI labels are not human text references.")

    records = manifest.get("records")
    if not isinstance(records, list) or not records:
        error("records", "records", "A nonempty list of records is required.")
        records = []

    ledger = manifest.get("exposure_ledger")
    if not isinstance(ledger, list):
        error("exposure_ledger", "exposure_ledger", "An explicit list of previously used records is required, even if empty.")
        ledger = []
    prior = defaultdict(lambda: defaultdict(set))
    for index, item in enumerate(ledger):
        loc = f"exposure_ledger[{index}]"
        if not isinstance(item, dict):
            error("ledger_type", loc, "Ledger entry must be an object.")
            continue
        if not _hash(item.get("text_sha256")) or not _nonempty(item.get("story_group")):
            error("ledger_identity", loc, "Ledger needs an exact text hash and story group.")
        uses = item.get("uses")
        if not isinstance(uses, list) or not uses or any(not isinstance(u, str) or u not in EXPOSURES for u in uses):
            error("ledger_uses", loc, "Declare at least one supported previous use.")
            uses = []
        for field in ("text_sha256", "normalized_text_sha256", "story_group", "duplicate_group"):
            value = item.get(field)
            if field.endswith("sha256") and value is not None and not _hash(value):
                error("ledger_hash", f"{loc}.{field}", "Expected lowercase SHA-256 hex.")
            if _nonempty(value):
                prior[field][value].update(uses)
        if item.get("source_url") is not None:
            key = _source_key(item["source_url"])
            if key is None:
                error("ledger_url", f"{loc}.source_url", "Expected an absolute source URL or URN.")
            else:
                prior["source_url"][key].update(uses)

    seen_ids = set()
    split_counts = Counter()
    groups = defaultdict(lambda: defaultdict(list))
    review_rubrics = defaultdict(list)
    for index, record in enumerate(records):
        loc = f"records[{index}]"
        if not isinstance(record, dict):
            error("record_type", loc, "Record must be an object.")
            continue
        record_id = record.get("id")
        if not _nonempty(record_id):
            error("record_id", f"{loc}.id", "A nonempty record ID is required.")
        elif record_id in seen_ids:
            error("duplicate_id", f"{loc}.id", "Record IDs must be unique.")
        else:
            seen_ids.add(record_id)
        split = record.get("split")
        if not isinstance(split, str) or split not in SPLITS:
            error("split", f"{loc}.split", "Use one declared split per record.")
            split = "invalid"
        split_counts[split] += 1
        if record.get("task") != task.get("id"):
            error("record_task", f"{loc}.task", "Record task must match the manifest task.")
        if not _choice(record.get("kind"), {"natural", "synthetic"}):
            error("record_kind", f"{loc}.kind", "Declare natural or synthetic origin.")
        if record.get("kind") == "synthetic" and split in {"calibration", "final_test"}:
            error("synthetic_holdout", loc, "Synthetic examples belong in development/stress tests, not the human population benchmark.")
        if record.get("kind") == "synthetic":
            block("synthetic_reference", loc, "Synthetic examples cannot establish independent human population accuracy.")

        for flag in ("development_only", "final_test_eligible"):
            if flag in record and type(record[flag]) is not bool:
                error("boolean_type", f"{loc}.{flag}", "Expected a JSON boolean.")
        if split in {"calibration", "final_test"} and (record.get("development_only") is True or manifest.get("development_only") is True):
            error("development_only_holdout", loc, "Development-only material cannot enter calibration or final test.")
        if split == "final_test" and (record.get("final_test_eligible") is False or manifest.get("final_test_eligible") is False):
            error("ineligible_final_test", loc, "This record or corpus explicitly disallows final-test use.")
        for flag in ("release_approved", "gold_labels_approved"):
            if flag in record and record[flag] is not False:
                error("approval_claim", f"{loc}.{flag}", "Intake cannot declare approval.")

        text = record.get("text")
        declared_hash = record.get("text_sha256")
        if not _nonempty(text):
            error("text", f"{loc}.text", "Exact nonempty source text is required for local hash verification.")
            normalized_hash = None
        else:
            normalized_hash = normalized_text_sha256(text)
            if declared_hash != text_sha256(text):
                error("text_hash_mismatch", f"{loc}.text_sha256", "Declared hash does not match exact UTF-8 text.")
        if not _hash(declared_hash):
            error("text_hash", f"{loc}.text_sha256", "Expected lowercase SHA-256 hex.")
        story = record.get("story_group")
        if not _nonempty(story):
            error("story_group", f"{loc}.story_group", "A curated event/story group is required.")
        duplicate = record.get("duplicate_group")
        if duplicate is not None and not _nonempty(duplicate):
            error("duplicate_group", f"{loc}.duplicate_group", "Use a nonempty duplicate group or null.")

        exposure = record.get("exposure")
        if not isinstance(exposure, dict):
            exposure = {}
            error("exposure", f"{loc}.exposure", "Explicit exposure declarations are required.")
        for key in sorted(EXPOSURES):
            if type(exposure.get(key)) is not bool:
                error("exposure_boolean", f"{loc}.exposure.{key}", "Expected a JSON boolean.")
        disallowed_exposures = EXPOSURES - ({"calibration"} if split == "calibration" else set())
        if split in {"calibration", "final_test"} and any(exposure.get(key) is True for key in disallowed_exposures):
            error("exposed_holdout", loc, "Previously exposed data cannot be used for independent calibration/final testing.")
        if split == "pilot" and exposure.get("pilot") is not True:
            error("pilot_exposure", loc, "Pilot membership itself implies pilot exposure.")
        if split == "development" and exposure.get("development") is not True:
            error("development_exposure", loc, "Development membership itself implies development exposure.")

        source = record.get("source")
        if not isinstance(source, dict):
            source = {}
            error("source", f"{loc}.source", "Explicit source provenance is required.")
        source_key = _source_key(source.get("url"))
        if source_key is None:
            error("source_url", f"{loc}.source.url", "Expected an absolute source URL or URN.")
        if not _nonempty(source.get("publisher")):
            error("source_publisher", f"{loc}.source.publisher", "Publisher or creator is required.")
        try:
            if not isinstance(source.get("acquired_at"), str):
                raise ValueError
            datetime.fromisoformat(source["acquired_at"].replace("Z", "+00:00"))
        except ValueError:
            error("source_date", f"{loc}.source.acquired_at", "Expected an ISO-8601 acquisition date/time.")
        for key in ("rights_basis", "rights_reference"):
            if not _nonempty(source.get(key)):
                error("rights_provenance", f"{loc}.source.{key}", "Document the basis and supporting reference, or explicitly state unresolved.")
        rights_status = source.get("rights_status")
        if not _choice(rights_status, {"documented", "unresolved", "prohibited"}):
            error("rights_status", f"{loc}.source.rights_status", "Use documented, unresolved, or prohibited.")
        if rights_status != "documented":
            block("rights_unresolved", loc, "Rights are not declared documented for this record.")
        uses = source.get("allowed_uses")
        if not isinstance(uses, list) or any(not isinstance(u, str) or u not in RIGHTS_USES for u in uses):
            error("rights_uses", f"{loc}.source.allowed_uses", "Use explicit supported permitted-use names.")
            uses = []
        required_use = "training" if split == "train" else "evaluation"
        if "annotation" not in uses or required_use not in uses:
            block("rights_use_missing", loc, f"Declared uses must permit annotation and {required_use} before that work.")

        identities = {"text_sha256": declared_hash, "normalized_text_sha256": normalized_hash,
                      "story_group": story, "duplicate_group": duplicate, "source_url": source_key}
        for field, value in identities.items():
            if _nonempty(value):
                groups[field][value].append((split, loc))
                if split in {"calibration", "final_test"} and prior[field].get(value, set()) & disallowed_exposures:
                    error("prior_exposure_overlap", loc, f"{field} matches previously used material in the exposure ledger.")

        review = record.get("review")
        if not isinstance(review, dict):
            review = {}
            error("review", f"{loc}.review", "Explicit review status is required.")
        status = review.get("status")
        if not _choice(status, REVIEW_STATUSES):
            error("review_status", f"{loc}.review.status", "Unknown review status.")
        if not _choice(status, {"human_adjudicated", "human_adjudicated_development"}):
            block("unfinished_human_review", loc, "Incomplete or unresolved review is not a completed human reference.")
        else:
            reviewers = review.get("reviewer_ids")
            if not isinstance(reviewers, list) or len(reviewers) < 2 or any(not _nonempty(r) for r in reviewers):
                error("independent_reviewers", f"{loc}.review.reviewer_ids", "At least two distinct human reviewer IDs are required.")
                reviewers = []
            elif len({_reviewer_key(r) for r in reviewers}) != len(reviewers):
                error("independent_reviewers", f"{loc}.review.reviewer_ids", "A repeated reviewer ID is not independent review.")
            adjudicator = review.get("adjudicator_id")
            if not _nonempty(adjudicator) or _reviewer_key(adjudicator) in {_reviewer_key(r) for r in reviewers}:
                error("adjudicator", f"{loc}.review.adjudicator_id", "A distinct human adjudicator must sign off the references.")
            provenance = review.get("provenance")
            if not isinstance(provenance, dict):
                provenance = {}
                error("review_provenance", f"{loc}.review.provenance", "Review provenance is required.")
            for flag, expected in (("human_attested", True), ("blind_to_model_outputs", True), ("ai_generated_labels", False)):
                if provenance.get(flag) is not expected:
                    error("review_attestation", f"{loc}.review.provenance.{flag}", "Missing or conflicting explicit human-review attestation.")
            for field in ("artifact_sha256", "rubric_sha256"):
                if not _hash(provenance.get(field)):
                    error("review_artifact", f"{loc}.review.provenance.{field}", "Pin the annotation artifact and rubric by SHA-256.")
            if _hash(provenance.get("rubric_sha256")):
                review_rubrics[provenance["rubric_sha256"]].append(loc)
            if not _nonempty(provenance.get("artifact_reference")):
                error("review_artifact", f"{loc}.review.provenance.artifact_reference", "A retrievable annotation-artifact reference is required.")
            if status == "human_adjudicated_development" and split in {"calibration", "final_test"}:
                error("pilot_review_holdout", loc, "An adjudicated development pilot remains development material.")
            reference = review.get("reference")
            if not isinstance(reference, dict):
                reference = {}
                error("reference_missing", f"{loc}.review.reference", "Adjudicated review must provide task-matched targets.")
            if task.get("id") == "article_author_framing":
                if not _choice(reference.get("label"), ARTICLE_LABELS):
                    error("article_reference_label", f"{loc}.review.reference.label", "An explicit article label is required; missing or nonpolitical labels never default to CENTER.")
                reason = reference.get("uncertainty_reason")
                if (not _choice(reason, UNCERTAINTY_REASONS)
                        or (reference.get("label") == "UNCERTAIN") != (reason != "NONE")):
                    error("article_uncertainty_reason", f"{loc}.review.reference.uncertainty_reason", "UNCERTAIN needs a rubric reason, including MIXED_AUTHOR_POSITIONS when applicable; resolved labels require NONE.")
            elif task.get("id") == "phrase_political_framing":
                if reference.get("spans_assessed") is not True:
                    error("spans_not_assessed", f"{loc}.review.reference.spans_assessed", "A human must explicitly assess spans, including an empty-span decision.")
                spans = reference.get("spans")
                if not isinstance(spans, list):
                    spans = []
                    error("phrase_reference_spans", f"{loc}.review.reference.spans", "An explicit span list is required; [] means assessed and no directional evidence.")
                occupied = []
                for span_index, span in enumerate(spans):
                    span_loc = f"{loc}.review.reference.spans[{span_index}]"
                    if not isinstance(span, dict):
                        error("span_type", span_loc, "Span must be an object.")
                        continue
                    start, end = span.get("start"), span.get("end")
                    if (type(start) is not int or type(end) is not int or not isinstance(text, str)
                            or not 0 <= start < end <= len(text)):
                        error("span_offsets", span_loc, "Use ordered in-range Unicode code-point offsets; end is exclusive.")
                    else:
                        if span.get("text") != text[start:end]:
                            error("span_text_mismatch", span_loc, "Span text must equal the exact source slice.")
                        if any(start < previous_end and previous_start < end for previous_start, previous_end in occupied):
                            error("overlapping_spans", span_loc, "This annotation contract requires nonoverlapping spans.")
                        occupied.append((start, end))
                    if not _choice(span.get("direction"), {"LEFT", "RIGHT"}):
                        error("span_direction", span_loc, "Directional phrase references require LEFT or RIGHT.")
                    if not _choice(span.get("attribution"), {"author", "quoted", "unknown"}):
                        error("span_attribution", span_loc, "Explicit author, quoted, or unknown attribution is required.")

    if len(review_rubrics) > 1:
        error("rubric_version_mismatch", "records[*].review.provenance.rubric_sha256", "A manifest task/version must use one frozen adjudication rubric; mixed rubric versions need separate re-reviewed manifests.")

    for field, values in groups.items():
        for members in values.values():
            splits = {split for split, _ in members}
            if len(splits) > 1:
                error("cross_split_overlap", ", ".join(loc for _, loc in members), f"Shared {field} crosses splits {sorted(splits)}.")
            elif len(members) > 1 and field in {"text_sha256", "normalized_text_sha256"}:
                warn("within_split_duplicate", ", ".join(loc for _, loc in members), f"Repeated {field}; do not count these as independent examples.")

    freeze = manifest.get("evaluation_freeze")
    if not isinstance(freeze, dict):
        freeze = {}
        block("evaluation_not_frozen", "evaluation_freeze", "No candidate/protocol freeze has been declared.")
    for field in ("protocol_sha256", "candidate_sha256"):
        if not _hash(freeze.get(field)):
            block("evaluation_not_frozen", f"evaluation_freeze.{field}", "An exact protocol and candidate hash is required before final evaluation.")
    if freeze.get("test_opened") is not False:
        block("test_not_sealed", "evaluation_freeze.test_opened", "A sealed final test must be declared before candidate evaluation.")
    for split in ("calibration", "final_test"):
        if not split_counts[split]:
            block("missing_evaluation_split", "records", f"No {split} records are declared.")
    independence = manifest.get("independence_audit")
    if (not isinstance(independence, dict) or independence.get("status") != "reviewed"
            or not _nonempty(independence.get("reviewer_id"))
            or not _hash(independence.get("artifact_sha256"))):
        block("independence_not_audited", "independence_audit", "Curated story/duplicate groups and exposure-ledger completeness need a documented independent audit.")

    warn("declarations_not_proof", "$", "Human identity, independence, blinding, rights, and exposure are declarations; this program does not independently verify them.")
    warn("near_duplicate_limit", "$", "Story groups, semantic duplicates, translated copies, source-query variants, and outside exposure need independent audit.")
    warn("heldout_handling", "$", "The program reads only this manifest. A held-out custodian should run it locally; do not expose final-test text or labels to model developers.")
    return {"validator_schema": SCHEMA, "structurally_valid": not errors,
            "declared_final_evaluation_prerequisites_met": not errors and not blockers,
            "release_approved": False, "gold_labels_approved": False,
            "human_provenance_verified": False, "rights_verified": False,
            "record_count": len(records), "split_counts": dict(sorted(split_counts.items())),
            "errors": errors, "prerequisite_blockers": blockers, "warnings": warnings,
            "release_requirements_outside_this_check": [
                "Independent review of rights and human annotation provenance",
                "Task-matched performance, uncertainty intervals, calibration, and coverage evaluation",
                "Browser, security, load, deployment, and rollback verification",
                "Recorded human release decision"]}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(path):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=reject_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--require-declared-evaluation-prerequisites", action="store_true",
                        help="Also fail on incomplete declared prerequisites; never approves release.")
    args = parser.parse_args(argv)
    try:
        report = validate_manifest(load_manifest(args.manifest))
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"structurally_valid": False, "release_approved": False,
                          "input_error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2, allow_nan=False))
    if not report["structurally_valid"]:
        return 1
    if args.require_declared_evaluation_prerequisites and not report["declared_final_evaluation_prerequisites_met"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
