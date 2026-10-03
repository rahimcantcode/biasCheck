# Human annotation and adjudication handoff

Prepared 2026-10-03. **Completed human reviews added by this work: 0. Completed human adjudications: 0.** No new gold labels, accuracy result, training run, or production approval is claimed.

## Decision

Use the existing 100-item v2 pilot to improve and test the annotation rules before collecting a new evaluation set. It already contains 60 historical natural articles and 40 AI-authored controls, with exact frozen text hashes and a browser reviewer. Do not create another near-duplicate pilot or assume all of these items are independent of old checkpoint training. The historical article rights still need review before redistribution or new training.

The new `research/annotation/validate_adjudication.py` closes a specific missing boundary: it validates an explicit **third human's** adjudication against two original v2 human review exports and their exact source snapshots. It produces provenance-bearing **development records only**, including unresolved rows. It does not turn reviewer agreement into a label, hide disagreements, manufacture independent humans, or approve model evaluation/training/production use.

The earlier rubric permits third-human adjudication or documented consensus. This first adapter deliberately implements only the third-distinct-human route. A consensus workflow must retain its own documentation until a separately reviewed adapter supports it. Do not put a participant's second alias into the third-human field.

## What the two reviewers do

1. Read `research/annotation/RUBRIC.md` and use `research/annotation/Bias_Checker_Review_Pilot.html`. Assign stable, distinct aliases to two actual people. Machine-written labels or rationales are not human reviews.
2. Use the same frozen text. Historical article snapshots come from the pinned `ramybaly/Article-Bias-Prediction` revision `ced8111a720948e6a410e52031ace99c4e53f096`. The reviewer loads these with hash verification. Do not substitute today's live page, a summary, a headline, or remembered event context.
3. Independently complete P001 through P010, export both initial passes, and only then discuss ambiguous rules. Record the agreed rubric interpretation and a shared freeze ID. If the instructions actually change, version the rubric and update the workflow before using the new version; this adapter accepts the existing v2 semantics only.
4. Re-review the calibration items if required, using the same person IDs, a new pass ID, and `post_discussion_rereview`. Disclose any remembered model, legacy, or peer answers. Complete the remaining pilot under `frozen_main` with the same freeze ID. Preserve earlier exports.
5. Judge author framing separately from the optional policy position. A quoted partisan position is not automatically the author's position. Keep NONPOLITICAL, CENTER, and UNCERTAIN distinct.
6. For the phrase task, select exact Unicode codepoint spans with direction and speaker attribution. Keep negation and qualifiers. Select `NO_DIRECTIONAL_SPANS` only after assessing the text and finding none. `NOT_ASSESSED` is missing annotation, not a negative example.
7. Export files frequently and retain originals. The local browser workspace is not a backup. Do not share model answers with a reviewer before independent annotation. Disclose any outside context already read instead of deleting the affected record.

The 100 pilot items remain development material permanently. Review consistency is a diagnostic of the rubric, not proof of political truth. Keep historical natural articles and synthetic controls separate in reporting.

## Compare, then create an empty adjudication document

Run from the repository root using a standard Python 3 environment. These scripts need no model, API key, or third-party Python package. Replace filenames and the snapshot folder with the actual local locations.

```bash
python3 research/annotation/compare_reviews.py \
  --first review-A-v2.json --second review-B-v2.json \
  --manifest research/annotation/pilot_manifest_v2.json \
  --snapshots research-data/data/jsons --output agreement-v2.json

python3 research/annotation/validate_adjudication.py \
  --first review-A-v2.json --second review-B-v2.json \
  --manifest research/annotation/pilot_manifest_v2.json \
  --snapshots research-data/data/jsons \
  --template --output adjudication-v2-unresolved.json
```

The template binds the manifest and both complete export objects with canonical SHA-256 digests. It includes every manifest item, including missing or skipped reviews. Every item starts with `status: "unresolved"` and `adjudication: null`, even if both reviewers agree. The tool never prefills a proposed decision or rationale.

Keep that initial file, and save a separate working copy such as `adjudication-v2-human.json`. Do not modify the original manifest or reviewer exports to make a disagreement disappear. Changing any input review requires a new bound document and renewed human review of the changed evidence.

## What the adjudicator does

A third actual person reads the complete exact frozen text plus both original reviews and independently takes responsibility for each final development decision. They may retain UNCERTAIN, leave the item unresolved, or revise spans with an explanation. They are not a blinded reviewer after seeing those reviews, and their metadata must say so.

For an unresolved item, leave the template unchanged. For an adjudicated item, set its status to `adjudicated` and replace the null `adjudication` with an object containing **exactly** these fields:

| Field | Required content |
|---|---|
| `adjudicator_id` | Stable alias, 2 to 40 letters/numbers/underscores/hyphens, different from both reviewer IDs ignoring case |
| `adjudicator_kind` | `human` |
| `annotation_method` | `manual` |
| `completed_at` | Actual ISO 8601 completion time with timezone, at or after both input export timestamps |
| `full_text_read` | `true`, after actually reading the entire frozen text |
| `both_reviews_considered` | `true`, after reading both supplied reviews |
| `text_context` | Same complete-frozen-text scope and SHA-256; boolean `external_context_used`; `external_context_notes` explaining any outside material used |
| `prior_exposure` | Boolean `model_predictions`, `legacy_labels`, and `other_reviewer_answers`; the last must be `true`; explanatory `notes` of at least 10 characters |
| `resolution` | All judgment and span fields listed below, decided manually by the adjudicator |

`text_context` uses the existing v2 keys `scope`, `text_sha256`, `external_context_used`, and `external_context_notes`. Its scope is `complete_frozen_text`. External-context notes must contain at least 10 characters when external context was used. This disclosure does not erase the original reviewers' disclosures.

The `resolution` must contain exactly these fields, with values from the v2 rubric:

```text
relevance
author_framing
label
issue_policy_stance
attribution
context_sufficiency
uncertainty_reason
confidence
rationale
span_status
span_protocol_version
evidence_spans
```

The final `label` must follow relevance and author framing, never the optional policy position. The human `rationale` must contain at least 15 characters and explain the evidence and disagreement resolution. Use `span_protocol_version: 1` explicitly. A span-assessed negative requires `span_status: "NO_DIRECTIONAL_SPANS"` and an empty span array; unassessed remains `NOT_ASSESSED`. Each nonempty span uses the existing keys `start`, `end`, `text`, `source_text_sha256`, `direction`, and `attribution` with exact source/codepoint matching. Quoted evidence may have a different direction from author framing.

This is a strict manual JSON handoff, not yet an adjudication GUI. The existing reviewer GUI remains the easiest place for independent reviewers to select and verify spans. An adjudicator must not simply copy a review because a model recommended it.

## Validate the completed or partially completed document

```bash
python3 research/annotation/validate_adjudication.py \
  --first review-A-v2.json --second review-B-v2.json \
  --manifest research/annotation/pilot_manifest_v2.json \
  --snapshots research-data/data/jsons \
  --adjudication adjudication-v2-human.json \
  --output adjudicated-pilot-development-v1.json
```

An adjudicated item requires two completed reviews and the exact source snapshot, including when no spans were selected. Missing reviews, skipped reviews, or unavailable text can remain unresolved. Bad hashes, wrong offsets, duplicate IDs, malformed source spans, absent provenance, an adjudicator reusing either reviewer identity, or mismatched artifact digests fail validation. Duplicate JSON keys and non-finite numbers are rejected. Outputs use exclusive creation and cannot overwrite prior artifacts.

Output schema: `biascheck-adjudicated-pilot-v1`. Each record retains source identity and hash, original reviews, disagreements, review and adjudicator exposure/context limitations, and the explicit adjudication. The output omits full article text. Each record has `status` equal to `unresolved` or `human_adjudicated_development` and an independently checked `source_verified` field.

All top-level and per-record scopes are fixed to:

```json
{
  "development_only": true,
  "final_test_eligible": false,
  "gold_labels_approved": false,
  "release_approved": false
}
```

These are not caller-selected switches. Self-asserted approval or final-test scope in the input is rejected. The converter preserves human UNCERTAIN decisions, different review rounds/freezes, post-discussion exposure, and missing phrase assessment. No downstream evaluator should turn these into confident political labels or eligible final-test examples.

## What validation does and does not establish

Software verifies record consistency and source fidelity. It cannot authenticate real human identity, prove that someone actually read the text, guarantee honesty, decide whether a political judgment is correct, or grant corpus rights. Hashes bind the supplied artifacts; they are not digital identity signatures. Preserve original exports and the human recruitment/review record separately.

Before any training or evaluation use, review corpus permissions, training overlap, human-review quality, and the intended construct. A new final evaluation needs licensed/permissioned contemporary natural text, event/source/time separation, new independent human reviews, precommitted sampling and metrics, and a locked candidate. Passing this converter does not satisfy those requirements.

## Verification for this change

The tests contain explicitly synthetic fixture people and labels solely to exercise software contracts. They are not added to the pilot or counted as completed human work.

```bash
python3 -m pytest tests/test_adjudication.py tests/test_annotation.py tests/test_annotation_spans.py -q
```

Coverage includes unresolved agreements/disagreements, preserved UNCERTAIN labels, exact Unicode source spans and negation, missing sources/reviews, provenance tampering, exposure preservation, case-insensitive identity collisions, chronology, scope escalation rejection, duplicate JSON keys, CLI behavior, and refusal to overwrite artifacts. Test outcomes belong to software validation, never model accuracy.
