# Next gate: independently reviewed lexical framing

This is a proposed work plan, not an approved release gate or a claim that reviewers have been recruited. The BASIL60 cases, their diagnostic/refinement outputs, and the existing 100-item annotation pilot remain development evidence. No new independent human judgments have been collected in this experiment.

## 1. Freeze the narrower task

Create a versioned rubric for **minimal evaluative lexical cues in political reporting**. It must not inherit LEFT/RIGHT labels from the existing directional-span rubric or imply fact checking, author endorsement, or informational-bias detection. Full-sentence informational framing without a defensible lexical cue is outside this extraction target.

Human reviewers mark exact, nonoverlapping Unicode-codepoint spans in the frozen text, keeping negation, qualification and enough wording to preserve meaning. They select a specific occurrence when wording repeats. Record cue type, quoted/reported versus author narration versus unknown attribution, speaker identity only when text supports it, and exact supporting attribution evidence separately from the cue. A quoted cue does not establish journalist endorsement. The current model's unknown attribution remains unknown; attribution becomes a separately evaluated capability before any author/speaker claim ships.

Every assessed passage receives CUE_PRESENT, NO_LEXICAL_CUE, or UNCERTAIN with a reason such as insufficient context or ambiguous sarcasm. NOT_ASSESSED and missing text are distinct from negative references. Neutral reporting verbs, political names, factual criticism and disagreement alone are not cues. Retain disputed boundary alternatives and explanations until adjudication.

## 2. Collect and protect the dataset

Start with a planning target of 30 pilot passages and 150 development passages; reserve a separate test collection targeting at least 300 independent event groups, including at least 100 assessed no-cue cases and sufficient quoted, negated and ambiguous cases. These are feasibility targets, not a completed power calculation. Before collection is finalized, determine sample size from desired interval widths, expected cue counts and event clustering; publish selection rules and every exclusion.

Preserve each licensed frozen article snapshot, title/date/source URL, event and duplicate-group IDs, source hashes, passage offsets, and the surrounding/full-article context actually supplied to reviewers and model. Use the same registered context policy for both. If the model sees less context, report that mismatch explicitly. Do not substitute a changing live URL for a snapshot.

Assign whole events, syndicated copies, paraphrases and curated near-duplicate groups to one split. Keep development and untouched test event-disjoint; record source/topic/date/length coverage without claiming publisher independence unless separately enforced. A custodian should hold test content and labels until the candidate is frozen. All tuning, calibration and failed attempts enter an exposure ledger; exposed test events move permanently to development.

Review rights for storage, annotation, model processing and any redistribution separately. Unclear permission blocks intake; public availability alone is insufficient. Audit exact/normalized hashes, URLs, event groups, near-duplicates and overlap with available training snapshots plus all prior research material. Document unavailable training histories and residual contamination uncertainty rather than declaring independence from an exact-match check alone.

## 3. Obtain actual independent human references

Recruit **two actual independent human annotators and a distinct human adjudicator**. AI agents, duplicate aliases, repeated passes and machine-written rationales cannot substitute. Hide model outputs, historical labels and peer decisions during initial annotation; record identity, pass, rubric hash, timestamps, prior exposure and context read.

Have both annotators independently complete the first 10 pilot cases. Preserve exports, discuss disagreements, revise guidelines, and independently re-review affected pilot items under a new version with exposure disclosed. Freeze the rubric before remaining main annotation. Report pre-adjudication presence, boundary and attribution agreement, disagreements and uncertain/unassessed counts. The adjudicator resolves conflicts with reasons; preserve both original judgments. Do not force unresolved cases into NO_LEXICAL_CUE. Existing annotation tools require a separately versioned lexical schema; their directional fields must not be repurposed silently.

## 4. Freeze and evaluate once

Before test access, register hashes for dataset/rubric/protocol, weights/runtime, both prompts and schemas, adapter, preprocessing, context policy, candidate selection, abstention policy and scoring. Select the candidate using development only. Evaluate the complete detector-plus-refiner pipeline, including misses, negatives and failures; refinement of archived accepted spans alone is insufficient.

Report one-to-one exact-span precision/recall/F1 and word-token precision/recall together, false-highlight rate on assessed no-cue cases, whole-case correctness, complete-response coverage, partial/hard failures, uncertain-case acceptance, and input coverage/truncation. Empty-reference failures are never correct negatives. Report all-input counts and success-only diagnostics separately. Publish quoted/author/unknown, negation, source/topic, length and context-sufficiency slices with support. Use preregistered event-cluster uncertainty intervals and paired comparisons; no repeated testing until a favorable result appears.

## 5. Proposed thresholds for pre-test approval

The following are discussion proposals, **not approved thresholds and not claims that present results meet them**. The owner and research supervisor must approve or replace them before unsealing the test.

| Measure | Proposed minimum gate |
|---|---|
| Exact lexical-span precision | Point estimate at least 90%; 95% lower bound at least 85% |
| Lexical word-token recall | Point estimate at least 75%; 95% lower bound at least 65% |
| False-highlight rate on assessed no-cue cases | 95% upper bound at most 5% |
| Complete responses across all submitted cases | At least 98%; partial and hard failures remain in denominator |
| Source/offset integrity | Every returned highlight matches the frozen source exactly; no fabricated attribution |

A missing denominator or unstable required interval cannot pass. Before testing, also specify slice-specific minimum support and failure limits, uncertainty/abstention acceptance, and numerical p95 latency, memory and concurrency budgets for the actual hosting target. Run a separate staging/browser check for Unicode offsets, quote display, long inputs, response races and failure messaging. Passing research metrics alone does not authorize deployment; retain a recorded release decision and the current disabled defaults until all required gates are approved and met.

Basis: `research/annotation/RUBRIC.md`, `research/team_20261003/EVALUATION_PROTOCOL.md`, the BASIL60 protocol/report, and this experiment's `PROTOCOL.md`. This plan narrows their relevant provenance, independence and evaluation safeguards to lexical framing; it creates no new human evidence.
