# Proposed independent evaluation protocol

Date: 2026-10-03. Status: proposal for review, not an approved preregistration or
release gate. No new accuracy result is reported here. No existing sealed 89-row
or 726-row holdout was opened for this work. The protocol is for a new,
task-matched human corpus; those existing holdouts have different limitations and
must not be repurposed without an explicit documented decision.

## What this milestone supplies

- A task, split, annotation, and reporting specification for a human benchmark.
- A standard-library intake validator, `research/scripts/validate_dataset_manifest.py`.
- Adversarial tests in `tests/test_dataset_manifest.py`.
- `dataset_manifest.example.json`, an AI-authored synthetic schema example with
  no human labels. It is explicitly development-only and is not a benchmark.

This work does not train a model, assign independent human reference labels,
establish legal permissions, approve a release, or show improved model accuracy.
An engineering test passing is not a political-accuracy measurement.

## 1. Freeze the task before collecting evaluation labels

Primary scope: contemporary English passages about U.S. politics and naturally
occurring nonpolitical/control text. The unit presented to the model must be the
same exact passage shown to reviewers. Source reputation is not a reference
label. An author's expressed framing is distinct from the content of a quotation.
Whole articles, paragraphs, and isolated sentences are different input conditions:
report them separately and do not assume an article reference transfers to every
sentence. Excerpts must preserve enough context to interpret speakers.

Article reference vocabulary follows the existing pilot-v2 primary framing
contract. The protocol and rubric may evolve through human review, but any
semantic change requires a new version and re-review, never automatic relabeling:

| Reference | Meaning and boundary |
|---|---|
| LEFT / RIGHT | Direction supported by the author's policy position or framing in the supplied text |
| CENTER | Enough political context and substantively nonaligned, balanced, or consistently centrist author framing; never a fallback for missing evidence or no explicit policy stance |
| NONPOLITICAL | No relevant political framing task is present |
| UNCERTAIN | Relevance or author framing cannot be resolved, including irreconcilably mixed author positions; preserve the explicit uncertainty reason |

Quoted partisan speech in otherwise descriptive reporting does not automatically
make the author's framing partisan. Descriptive political reporting can be CENTER
when the full context supports substantive nonalignment under the current rubric;
mere absence of a stated policy position does not suffice. Mixed author framing
uses UNCERTAIN with `uncertainty_reason="MIXED_AUTHOR_POSITIONS"`. Optional issue
policy stance can separately be MIXED, but never overwrites the framing label.
No six-class taxonomy is introduced by this intake tool. These reference
categories are not a claim that the currently deployed API already returns all of
them. A mapping to product outputs must be approved and versioned before scoring.

Phrase references are a separate task. Each phrase uses Unicode code-point
`start` and exclusive `end` offsets into the exact source, the exact substring,
LEFT or RIGHT direction, and attribution `author`, `quoted`, or `unknown`.
`spans_assessed=true, spans=[]` means the reviewer assessed the full passage and
found no directional evidence. Missing spans mean unassessed, not a negative
reference. The intake contract uses nonoverlapping spans. A different span
convention requires a new version and compatible scorer.

## 2. Obtain independent human references

Use the existing reviewer tooling and the updated [annotation pilot](ANNOTATION_PILOT.md).
Begin with the rubric pilot, then a diverse natural-text pilot before expanding.
Two humans annotate independently, blind to model outputs and each other's
answers. A distinct human adjudicator resolves disputes, confirms exact source
snapshots, and signs the finalized annotations. Preserve both original reviews,
all disagreements, the resolution, reviewer declarations, and artifact hashes.
Retain UNCERTAIN when context is inadequate rather than forcing consensus.

Report pre-adjudication article agreement, a category confusion table, and
direction/attribution/offset disagreement for phrases. Report agreement by input
length and task subgroup. High raw agreement dominated by one category is not
sufficient evidence of a usable rubric. AI suggestions and AI-authored references
remain visibly identified development material; they cannot count as two human
reviewers or as independent test truth.

The new adjudication artifact format preserves development-only flags. Converting
it to an intake record does not remove those flags or turn pilot references into
an untouched final test. A separately reviewed conversion must preserve IDs,
source hashes, rights restrictions, original reviews, and those exclusions.

## 3. Rights and provenance are explicit prerequisites

For every exact text snapshot, record original URL or stable URN, publisher/creator,
acquisition date, raw UTF-8 SHA-256, rights basis, supporting reference, and
permitted uses. Permission to read, annotation/evaluation rights, model-training
rights, redistribution rights, and commercial-use rights are not interchangeable.
Preserve attribution, source links, revision IDs, and required notices.

Public availability and a repository license do not establish rights in embedded
article text. An unresolved or contradictory rights statement remains unresolved;
do not relabel it as documented to satisfy the validator. The validator only
checks declarations and is not legal verification. Commercial training or release
needs its own rights review beyond this research-evaluation check.

See [DATA_AUDIT.md](DATA_AUDIT.md) for source-specific limitations and the registry.
No blanket claim is made that all historical article labels were inherited from
publishers; audit each source's actual annotation method.

## 4. Split by independent story and preserve exposure history

| Split | Permitted purpose | Prohibited use |
|---|---|---|
| Pilot | Develop rubric, reviewer UI, and annotation procedure | Final accuracy evidence |
| Train | Fit model parameters after rights review | Final-test claims |
| Development | Compare candidates, prompts, preprocessing, and failure fixes | Independent final evaluation |
| Calibration | Fit frozen candidate's calibration and predeclared acceptance rule | Selecting model architectures or prompts |
| Final test | One planned evaluation of the fully frozen candidate and decision rule | Tuning, relabeling toward predictions, or repeated selection |

Group all versions and excerpts of an article together, then group related event
stories, syndicated copies, paraphrases, and translations. Assign whole groups
to one split. A publisher can appear in several splits under this proposed
story-disjoint design; a publisher-disjoint generalization test would be a
separate explicitly named experiment. Stratify at group level for topics,
source diversity, dates, input lengths, and reference categories once permissible.
Freeze sampling rules and report exclusions so curation cannot silently favor a
candidate.

Maintain an exposure ledger of previous pilot, training, development,
model-selection, and calibration use. It must include IDs/hashes and groups even
when the old material is absent from the new manifest. Explicit record exposure
flags alone cannot prevent a renamed old example entering the test. The program
checks exact hashes, normalized-text hashes when available, story/duplicate groups,
and source URLs across splits and against that ledger. Its text normalization
only catches Unicode compatibility, case, and whitespace variants. Semantic or
translated duplicates and tracking-URL variants require a curated audit. Do not
claim independence merely because no exact duplicate was found.

Prior calibration-only use is permitted for the calibration split, because that
split is used to fit the same preregistered frozen candidate's decision rule. It
is forbidden in final test. Training, pilot, development, or model-selection use
disqualifies a record from both calibration and final test. This exception does
not authorize reusing calibration data to choose a different model or prompt;
the exposure history must reflect any such use. As with other declarations, the
validator cannot independently prove the history or candidate identity is honest.

An independent custodian should hold final-test content, labels, and the complete
manifest. Model developers receive an aggregate inventory and integrity hashes.
The validator reads only its input manifest and emits no source text; the
custodian can run it locally. Do not send sealed content to this team to prove
that the validator works. Raw text is needed by the custodian for its hash check.

## 5. Preregister selection and uncertainty handling

Before final evaluation, record exact hashes for the rubric, dataset manifests,
protocol, candidate weights/provider version, prompt, tokenizer, preprocessing,
runtime, calibration artifact, and abstention rule. Freeze a finite candidate
budget and select using development evidence only. Define any classifier-to-
reference mapping before looking at test outcomes. Record random seeds, hardware,
per-input runtime/errors, input-length truncation, and model outputs.

Calibration may tune only the fixed candidate's predeclared calibration/decision
rule. Final-test failures cannot be silently removed. If any test is used to guide
a change, document the exposure, retire it to development, and obtain a new final
test. Report all prespecified candidates, negative results, and protocol deviations.

No numerical production thresholds are approved by this document. Before test
unsealing, Rahim and the research supervisor should sign a target table specifying
minimum class/phrase performance, maximum false directional highlights and
uncertain acceptance, minimum coverage, acceptable latency/memory, and required
uncertainty bounds. Existing exploratory targets remain provisional. A threshold
must not be chosen after seeing the final-test result.

Sample size must be planned from the desired uncertainty width, expected class
counts, and number of independent story clusters. The proposed approximately
100-passage pilot is for rubric development and feasibility, not proof of a tight
population accuracy bound. Do not set test size by repeatedly checking whether a
score has crossed a desired threshold.

## 6. Required accuracy reporting

Article reporting distinguishes reference uncertainty from model abstention. Do
not count `ABSTAIN` as a correct LEFT/RIGHT/CENTER prediction or merge it silently
with the reference UNCERTAIN category.

| Quantity | Required denominator and interpretation |
|---|---|
| Decision-aware class recall and macro-F1 | Prespecified adjudicable reference classes LEFT/RIGHT/CENTER/NONPOLITICAL; abstentions count as false negatives for those classes. Publish per-class support. Report UNCERTAIN references and their reasons separately. |
| All-input decision table | All five reference rows and all supported output columns plus ABSTAIN and ERROR; never hide out-of-scope examples. A missing supported output remains visible. |
| Coverage | Accepted decisions divided by every submitted benchmark input, including errors in the denominator |
| Accepted-reference agreement | Correct accepted decisions on adjudicable references divided by all accepted decisions, including acceptance of UNCERTAIN references and wrong nonpolitical assignments |
| Full-population correct accepted rate | Correct accepted decisions on adjudicable references divided by every input; reference-UNCERTAIN abstentions are shown separately as desirable uncertainty handling, not directional accuracy |
| Uncertain acceptance | Accepted decisions on reference-UNCERTAIN inputs divided by all reference-UNCERTAIN inputs |
| False political-label rate | LEFT/RIGHT/CENTER predictions on NONPOLITICAL references divided by all NONPOLITICAL references; also report the narrower LEFT/RIGHT false-direction rate |
| Calibration | Reliability diagram, Brier/log loss if probabilities cover the registered label space, and prespecified binning; report cohort, coverage, and calibration-set identity |

For each adjudicable class, false positives include wrong accepted predictions
from every reference row, including UNCERTAIN. False negatives include its
abstentions and errors. The macro average uses the fixed registered class set,
not a favorable subset selected after evaluation. An absent required reference
class or undefined denominator must be reported and cannot silently satisfy its
release criterion.

Publish ordinary raw argmax metrics only as clearly named diagnostics alongside
decision-aware metrics. An LLM relevance score or token probability is not an
article-class probability. Do not calculate a five-class Brier score by pretending
a three-class model supplies meaningful probability mass for unsupported labels.

Phrase metrics must jointly assess extraction, direction, and attribution:

- Exact precision: one-to-one matches with correct source boundaries, direction,
  and attribution divided by all returned spans. Duplicate predictions cannot
  earn repeated credit. Unmatched spans are false positives.
- Exact recall: those matches divided by all assessed reference spans. Missing
  or rejected outputs remain false negatives where reference spans exist.
- Exact F1 and whole-case exact match, with explicit counts. Zero denominators
  are reported as undefined, not fabricated perfect precision/recall.
- Whole-case exact match additionally requires a valid response that covers the
  complete intended input. A timeout, invalid response, abstention, or truncated
  unassessed output on an empty-reference case is not a correct negative. Report
  valid complete-output coverage over all phrase cases alongside extraction scores.
- False-highlight case rate: assessed empty-reference cases with any returned
  directional span divided by all assessed empty-reference cases.
- Author-only versus quoted/unknown results and attribution confusion; report
  how often a quotation is wrongly promoted into an author position.
- Optional overlap-tolerant/character-level scores are secondary, with the overlap
  criterion and one-to-one assignment frozen in advance. They never replace exact
  scoring after boundaries perform poorly.

Every table names whether its inputs are natural human-reviewed references,
synthetic stress cases, or previously exposed development material. Never pool
these into one headline product-accuracy value.

## 7. Statistical and operational evidence

Report point estimates and 95% uncertainty intervals. For correlated articles,
use a preregistered story-cluster bootstrap rather than treating every sentence
or phrase as independent. One proposed implementation resamples complete story
groups 5,000 times with a fixed seed, recomputes all metrics, and reports percentile
intervals. This is a design proposal, not a calculation performed in this milestone.
Document too-few-cluster or rare-class instability; do not discard inconvenient
zero-support resamples or publish a misleading narrow interval. Plan stratified
cluster resampling or a suitable alternative before collection when rare classes
make the ordinary bootstrap unsuitable.

Compare candidates using paired resampling of the same groups and the same
registered metric. Report the interval for their difference, not just separate
point estimates. If multiple final comparisons are planned, preregister how
multiplicity is handled. A modest development-score difference does not establish
a reliable improvement. Uncertainty intervals cannot fix selection leakage or a
nonrepresentative sample.

Separately test negation, quotations, reported facts, ambiguous context, ordinary
nonpolitical text, long articles, unsupported languages, Unicode, and malformed
responses. Label synthetic challenge results as robustness evidence, not natural
population accuracy. Stress-set exposure does not make a new test independent.

On the actual staging/VPS target, measure end-to-end p50/p95 latency, peak memory,
timeouts, errors, concurrency, and complete input coverage using a fixed workload.
Check real browser upload, exact text highlighting, response races, accessibility,
and all three input-length modes. Model correctness, software contracts, and
operational readiness are three separate reports. No inference throughput has
been measured by the new manifest validator.

## 8. Intake schema and command behavior

Run from the repository root:

```bash
python3 research/scripts/validate_dataset_manifest.py research/team_20261003/dataset_manifest.example.json
python3 research/scripts/validate_dataset_manifest.py research/team_20261003/dataset_manifest.example.json --require-declared-evaluation-prerequisites
python3 -m unittest discover -s tests -p test_dataset_manifest.py
```

The synthetic example passes structural intake (exit 0). The second command
intentionally returns exit 2 because human review, natural holdouts, independence
audit, and a frozen evaluation are incomplete. Malformed structure or leakage
returns exit 1. Duplicate JSON keys and nonfinite constants are rejected.

Each manifest declares its versioned text-level task and explicit exposure ledger.
Each record declares ID, matching task, natural/synthetic origin, split, exact
text/hash, story group, optional curated duplicate group, all five explicit
boolean exposure flags (`pilot`, `training`, `development`, `model_selection`,
`calibration`), source
provenance, use permissions, and review status. Empty or unresolved provenance
never satisfies prerequisites. Article source URLs are grouped, not publishers.

For `human_adjudicated` or `human_adjudicated_development` review, require two
distinct normalized reviewer IDs, a distinct adjudicator ID, human/blinding/no-AI
attestations, pinned annotation and rubric artifacts, and task-matched references.
For the article task, `review.reference.label` is an explicit vocabulary value and
`uncertainty_reason` follows the v2 vocabulary: NONE for resolved labels;
INSUFFICIENT_CONTEXT, MIXED_AUTHOR_POSITIONS, ATTRIBUTION_UNCLEAR,
SARCASM_OR_AMBIGUITY, OUTSIDE_US_SCHEME, or OTHER for UNCERTAIN. Completed references
for a single manifest task/version must have the same frozen rubric SHA-256;
incompatible rubric versions require separate re-reviewed manifests.
For phrases, `review.reference.spans_assessed` must be true and
`review.reference.spans` must be an explicit list of exact-source spans with
`start`, `end`, `text`, `direction`, and `attribution`. Missing labels, unassessed
spans, invalid offsets, source mismatches, and overlapping spans are rejected.
Identity normalization only catches obvious repeated aliases; it cannot prove
that two IDs are two independent people.

`independence_audit` requires `status="reviewed"`, `reviewer_id`, and
`artifact_sha256` to satisfy declared prerequisites. `evaluation_freeze` requires
`protocol_sha256`, `candidate_sha256`, and `test_opened=false`. This intake check
does not inspect those external artifacts or prove the freeze actually happened.

`declared_final_evaluation_prerequisites_met` means only that required declarations
are internally consistent. The program always returns `release_approved=false`,
`gold_labels_approved=false`, `human_provenance_verified=false`, and
`rights_verified=false`. Actual provenance audit, performance evidence, operational
QA, and a recorded release decision remain outside the program. CLI success is
not an authorization to publish articles, train commercially, or deploy a model.
