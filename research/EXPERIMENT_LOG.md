# Working experiment log (not a final report)

## 2026-10-03: concurrent data-quality team milestone

Started an isolated `research/data-quality-team-2026-10-03` branch from
`4268bab42c1186ddcd1fee5b9b80ab4a2ae9f8a4`, with six specialist agents and a lead.
The full handoff, evidence ledger and reviewed limitations are in
[`team_20261003/README.md`](team_20261003/README.md).

Audited nine dataset resources and their distinct tasks/rights. Baly's authors
describe manual article-level AllSides labels; the entire corpus must not be
described as publisher-inherited. A targeted search of 24 accessible account
repository metadata records plus relevant code queries did not recover a second
training project or the original checkpoint's row/split lineage. That remains
unresolved, not proof that no such files exist elsewhere.

Added a development-only human adjudication validator, a corpus-intake validator
for source hashes, review targets, rights declarations, duplicate/story groups
and prior exposure, plus a proposed independent evaluation protocol. These tools
check supplied declarations and integrity, not human identity or political truth.
No completed human reviews or adjudications were created, and no sealed 89-item
or 726-item corpus input was read.

A new independent implementation replayed ten named publication records:
924 article candidate/example decisions, 230 training out-of-fold decisions,
254 phrase case/arm evaluations and 548 native stance response contracts. These
are repeated development work units, not independent sample counts. Per-ID native
stance gold is not published, so its correctness was checked only at the stated
aggregate-arithmetic level. No new model inference, training or accuracy gain is
claimed by that replay. Unanimous-only training still trades class recall rather
than establishing a general improvement.

Collected two pinned early-2026 Wikinews API snapshots as an unlabeled development
acquisition smoke. Metadata preserves actual response/text hashes, extraction
changes and source attribution. Both articles have unresolved policy-versus-
embedded-license metadata, so no intended-use clearance or training eligibility
is asserted. The intake correctly remains blocked for independent evaluation.
Raw snapshots and extracted text stay in ignored local data storage.

An opt-in live contract probe confirmed original RoBERTa weights, demo mode and
unapproved release state. Article, paragraph and sentence requests returned 200
but rewrote pasted text; empty input returned 400. These are contract observations,
not accuracy measurements. The new research backend and the live server remain
different versions. A frontend defect hiding default-engine passage estimates
was corrected without turning segment labels into phrase evidence.

Final targeted Python integration: **171 tests plus 74 subtests passed**, with
socket restrictions permitting only synthetic loopback/Unix fixtures. Exact
command, output and test-source hashes are in `team_20261003/python_verification.json`.
The application workstream separately records its frontend dependency migration,
audits, build and browser checks in `team_20261003/STAGING_READINESS.md`.
Baseline hosted CI was directly verified on `4268bab`; later branch CI must be
identified by its own commit/run. Nothing in this milestone approves a model,
merges the research branch, or deploys the VPS.


## 2026-10-02 18:00 UTC: real CPU model loop and broader human-reference evaluation

An alternate public-weights runtime now works despite the earlier authenticated
client initialization failure. Official llama.cpp b11349 was SHA-verified; original
Qwen3-4B Q4_K_M weights were pinned to revision bc640142c66e1fdd12af0bd68f40445458f3869b
and SHA7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5.
One local slot, four CPU threads, 4096-token context, disabled thinking and no
context shifting were tested. Exact token preflight, output limits, schema JSON,
oversized-prompt rejection and loopback-only transport passed real runtime checks.
Observed process RSS was about 4.6–4.7 GiB. This is not a verified VPS capacity/SLA.

Original frozen phrase run: 24/38 structurally valid outputs; only 1/27 exact
expected spans recovered. Unique-quote FORMAT-only replay raised validity to37/38,
but semantic exact recovery only to3/27 and exposed more false highlights.
The full-context v2 contract then produced34/38 valid outputs,11/27 exact spans
recovered and11/35 exact precision. Author-only precision was11/34. Twelve cases
without expected author spans received author highlights. Quotes, negation and
context sensitivity remain serious failures. Original26 and former-transfer12
are both development after inspection; descriptive IDs in the first original run
were also a leakage/parity limitation, removed using opaque IDs in v2.

All raw outputs and exact/secondary metrics are preserved in the sanitized
publication records. The original frozen v2 record is retained locally unchanged;
post-run reviewer/path sanitization is explicitly recorded. Imported-source hashes
for that v2 run were captured during inference, with honest timing, then verified
unchanged and metrics replayed. No source/label/attribution was silently corrected.
The historical neutral_cases counter denotes zero expected spans, including some
ambiguous or insufficient-context cases; it is not a nonpolitical population rate.

A distinct human-majority reference challenge was prepared from the 2026 UK
argument study: humans saw both Proposition and Locution and labelled presence
of a political stance. No stance can still be about politics. It is NOT an
absolute left/right or political-relevance dataset. Before inference, a fixed
source/duplicate-group hash split reserved726 examples and exposed274 development
examples. Episode independence is incomplete and underlying BBC rights unresolved.
Source bytes and full transcripts stay git-ignored; no production training is
claimed. The old66 development set and89 reserved corpus test were not evaluated.

Fixed zero-shot original Qwen3-4B on all274 development rows:181 matches (66.06%),
macro-F1 .6596, balanced accuracy .6937, full valid-output coverage. No-stance recall
83/162=.5123; stance recall98/112=.875. There were79 false positives and14 false
negatives. Unanimous-reference agreement92/118=.7797; disputed89/156=.5705.
A constant no-stance prediction scores162/274=.5912. This is a modest native-task
lead, not high accuracy and not product validation. Median observed local request
latency2.04s; maximum5.07s. The726 held-out inputs remain sealed.

The next controlled comparison uses the non-thinking Qwen3-4B-Instruct-2507
checkpoint, with third-party Unsloth Q4_K_M revisiona06e946bb6b655725eafa393f4a9745d460374c9
and SHA3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597.
The same v2 task prompt/schema/decoding is frozen; checkpoint, quantization publisher
and embedded template change. Completed:28/38 structurally valid responses, but zero exact or labeled/attributed
overlap matches.25/28 returned spans have unknown attribution; remaining narrator
assignments are mainly quote/negation errors. Empty prediction envelopes also
cause failures. Some phrase directions are sensible, but that does not satisfy the
full contract. This checkpoint is also rejected for serving. See the preserved
Instruct-2507 comparison; further work will separate source/speaker decisions
rather than silently relabel unknown outputs.

An actual FastAPI/old-RoBERTa/local-phrase-model smoke confirms integration, with
source text and codepoint offsets preserved. The cat example still rejects safely;
a same-sex-marriage statement yields an author LEFT span; a recipe yields no spans.
The serving provider now verifies exact prompt+output capacity and runtime identity.
No candidate is approved, deployed or promoted. Real-browser QA remains unverified.

Production dependency audit found known Next/PostCSS/sharp/nanoid advisories.
Compatible fixes and four additional development-package updates have now passed
clean npm ci,33 frontend tests, typecheck, production build and zero-vulnerability
production/full npm audits. Node>=20.9.0 is required. See the security evidence JSON.
A public-standard-runner CI workflow is prepared with read-only permissions,
pinned official actions and no secrets/deployment/artifact uploads. Its hosted run
has not yet occurred. Locally the outbound-network-restricted Python suite passes
355 tests with dependencies consistent. Engineering checks are not model accuracy.


## 2026-10-02: exact human-span collection follow-through

Extended the existing v2 pilot with a versioned exact-span workflow rather than
leaving phrase supervision uncollectable. Humans enter an exact phrase and its
occurrence, then independently select LEFT/RIGHT and AUTHOR/QUOTED/UNKNOWN.
Unicode codepoint offsets and source hashes are verified; duplicate/overlapping
or mismatched spans are rejected. NO_DIRECTIONAL_SPANS is distinct from
NOT_ASSESSED. Nothing is prefilled from model outputs or article labels.

Historical imports/restored workspaces require pinned snapshots loaded first.
Missing or changed snapshots cannot overwrite saved reviews. Offline comparison
without historical snapshots marks spans unverified and excludes them from span
agreement. Symmetric exact-span agreement is reported separately for natural and
synthetic items, same-round pairs and the blinded/frozen-text-only subset, each
with its own denominator. Neither reviewer is treated as gold.

59 targeted annotation/schema/DOM/span tests and the final aggregate of 225 Python
tests passed. Frontend verification remains 33 tests plus typecheck/build. Human
reviews remain zero.
Manual exact-phrase entry is supported; drag selection and actual-browser copy
behavior are not verified. There is no automatic pilot-export-to-production/gold
conversion: human adjudication, a source/hash-preserving conversion and a separate
independent evaluation remain required. Research-draft publication is approved;
model release and deployment remain rejected.

## 2026-10-02: bounded baselines, supervision sensitivity and phrase-evidence groundwork

### Training-only comparisons (no production promotion)

Recovered exactly the frozen 115 training rows: SHA-256
`5ebefc86e5da25784649b895753219207913cbcb042b85e7e90fdf4b84f2d1b9`.
Pinned upstream combined CSV bytes include nontraining records; recovery filters
by the known training-ID allowlist before accessing those records' text/label
fields. No validation/test JSONL was constructed or evaluated. The 66 reused
validation items and 89 reserved test items were not used for selection.

Registered before fitting: raw/known-exact-footer-clean views, word/bigram features,
LR C=1 control, LinearSVC and one-versus-rest NB-SVM C=.1/1/10, five grouped folds.
Vocabulary/IDF and NB ratios are fitted only within each training fold. Known
reviewed episode IDs are unioned transitively with event-string groups. This still
leaves 42 groups because the five training IDs already shared an event string.
Canonical group names change GroupKFold tie ordering; historical 58/115 versus the
new control's 64/115 is NOT an improvement comparison. Use same-fold controls.

Seventy fits across fourteen candidates completed with no convergence warnings.
Raw LR control: 64/115 released-label agreement, macro-F1 .4786,
LEFT/CENTER/RIGHT recall .5526/.1538/.7647. None of the other candidates exceeded
its macro-F1. All candidates' CENTER recall lies between zero and .1538. These
are weak, exploratory corpus-reference results, not independent product accuracy.
Complete protocols, fold IDs, OOF decisions/margins, dependency/model hashes,
recovery provenance and limitations are preserved in
`results/training_linear_cv_20261002.json`.

One subsequent fixed diagnostic tested the reference-disagreement issue: train
raw LR C=1 only on unanimous training items, retaining identical folds and all 115
held-out-training examples in evaluation. All five fitted subsets retained all
three classes (40–45 fit rows). Agreement fell to 51/115, macro-F1 .4455.
CENTER recall rose 4/26 to 21/26, while LEFT fell 21/38 to 16/38 and RIGHT fell
39/51 to 14/51. Predicted CENTER counts rose 10 to 69. Unanimous held-out agreement
rose 28/54 to 32/54, while disputed agreement fell 36/61 to 19/61. Filtering changes
sample size, class/topic composition, vocabulary and IDF together; this is not
proof the disputed labels are incorrect. Exploratory paired macro-F1 interval
[-.1288,.0669] spans zero. Original control results were not overwritten.
See `results/training_label_provenance_20261002.json`.

All 75 saved artifacts reloaded and reproduced all 1,725 predictions/margins.
Training rows, downloaded source snapshots and weights remain git-ignored.
CC-BY-NC-SA corpus-derived artifacts remain noncommercial research. No candidate,
threshold or cleaned view was selected for deployment. Further tuning of this
small corpus is not justified as a path to a credible high-accuracy claim; the
next dependency is task-matched independent human supervision.

### Correct evaluation and annotation contracts

Fixed a release-evaluation bug: raw-label macro-F1 and recall previously ignored
abstentions. Decision-aware metrics now count abstentions as misses, retain an
ABSTAIN column and class-specific coverage; explicitly named raw metrics remain
available separately. Policy calibration/test checkpoint, preprocessing version, mode and label
mappings must match. Exact-source input preservation changes prior normalization;
legacy policies are rejected unless recalibrated with the new input contract. NaN/infinite/wrong-shape logits are rejected rather than accidentally
passing threshold comparisons. Marginal Wilson intervals remain descriptive,
not independent-episode bounds. A frozen uncertainty handling/interval protocol
is still absent, so certification remains blocked and no policy is approved.

The existing 100-item human pilot now has an explicit v2 reviewer workflow;
v1 artifacts are preserved. Primary author framing is separate from optional
policy stance, attribution, insufficient/mixed uncertainty, prior exposure and
external-context use. Human-source and independence attestations are required but
are assertions to audit, not software proof of independence. No human judgments
were created. Pilot development material cannot become an independent final test.
The corpus context caveat is now explicit: original annotators could consult full
articles/background/party panels, and their actual extra-context usage is unknown.

### Experimental phrase highlighting and hard blockers

Implemented UTF-8 .txt input, exact original-text rendering, code-point-bound
phrase evidence, author-only blue LEFT/red RIGHT highlighting, quote/unknown
nonendorsement behavior, safe HTML rendering, overlap rejection and stale-request
guards. The article classifier never manufactures evidence from its class label.
Phrase extraction is disabled by default. A separately configured loopback-only
structured model server can process arbitrary text; an optional exact-text cache
supports research. Neither route uses an authenticated research CLI in HTTP.

Frozen 26-case actual model probe was attempted with a fixed full-context prompt.
All six CLI batches failed before inference with `Read-only file system (os error
30)` during in-process app-server initialization. Valid model outputs: zero;
semantic evaluation status is `not_run_provider_initialization_failed`, and
quality rates are null. This is an infrastructure failure, not a 0% model result.
No protected configuration/authentication path was modified. The independent
reviewer's 12 transfer diagnostics remain unrun; no self-hosted model weights,
phrase accuracy, latency or memory have been validated.

Original RoBERTa weights were recovered and loaded under pinned CPU dependencies;
SHA-256 remains `548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d`.
A real FastAPI TestClient request preserved emoji, CRLF, tabs and boundary spaces,
withheld the unapproved label and returned no fabricated highlights. That actual
JSON passed React static rendering verification. Loopback mock-provider tests
exercise complete source transport and fail-closed response validation; mocked
semantic answers do not establish real extraction quality.

Final local verification at this checkpoint: 209 Python tests passed, 33 frontend
tests passed, dependency checks passed, TypeScript checks and production build
passed. Browser visual/interactive QA is unverified: the dot cloud browser blocked
the local URL, and the frontend server process reported cancelled network
approval. No alternate route bypassed those restrictions. See
`PHRASE_EVIDENCE.md` for the exact contract, commands and deployment prerequisites.

Deployment requires the user's connected Mac/authorized SSH path, a verified
local inference provider and operational capacity, rights review, genuine human
article/phrase labels and independent quality gates. No VPS access, root-password
handling, merge, model replacement or production deployment occurred in this run.

## 2026-10-02 04:21 UTC: training-only footer augmentation CV

Ran five-fold GroupKFold on the 115 training articles (42 source event strings),
with 23 held-out articles per fold. Neither the 66-item validation file nor the
reserved test was read. Footer hashes were already known from earlier development
work, so this is not independent final evaluation. Event-string grouping still
does not establish event-family independence. No labels or frozen splits changed.

Per fold, fit word/bigram TF-IDF on original training-fold texts only and reuse
that vocabulary/IDF for baseline and augmentation. Both heads use C=1, balanced
classes, seed20261001, max_iter=1000. Augmentation supplies cleaned text plus one
copy with each known footer appended. Each copy has sample weight 1/3, preserving
original article loss mass and class proportions. All copies remain in the same
fold; no duplicated article can enter both fitted and held-out data. Two fixed
footer templates are extracted from training input, not held-out validation/test.
Ten fitted heads and their vectorizers are retained locally.

| Pooled held-out-training metric | Baseline | Augmented |
| --- | ---: | ---: |
| Original-label matches /115 | 58 | 57 |
| Original-label agreement | .5043 | .4957 |
| Macro-F1 | .4423 | .4382 |
| Unanimous matches /54 | 25 | 24 |
| All three footer variants agree /115 | 54 | 87 |
| Variant consistency | .4696 | .7565 |

Augmented LEFT/CENTER/RIGHT recalls: .6316/.1538/.5686. All 115 original items
received a prediction. Original agreement differences by fold: -1, -1, 0, +2, -1
matches (each denominator 23). For fixed pooled out-of-fold predictions, an
event-string bootstrap (5000 draws, seed20261001) gives a paired agreement
difference interval [-.0472,.0313]. Shared fitted folds, previously seen training
data and possible event-family dependence limit inference; this is not an
independent generalization interval.

The augmentation increased consistency but did not improve original-label
agreement. Among variant-consistent items, 24 baseline and 43 augmented original
predictions still disagreed with their reference labels. Stable predictions can
be wrong; no consistency score is presented as accuracy. Appending publisher
notices creates artificial stress-test views, not genuine publisher provenance or
new human-approved examples. Human reference labels apply to the original text.

GPT-6 Astra Medium reviewed the design via the terminal CLI. Advice retained in
`research/data/augmentation-advice-20261002.txt`: group-string aliases, unstratified
small folds and prior footer discovery limit independence; evaluate articles and
events, not augmented rows. No new paid compute was purchased.

Live-browser diagnostic used the first training item by existing order (not label
or score), plus three constructed variants. Original/clean returned LEFT .993377;
copyright notice returned LEFT .980073; licensing notice returned RIGHT .999490.
All were single-window, untruncated responses. The original article's reference is
CENTER, so the directional flip does not establish a corrected prediction. Four
HTTP 200 responses, no page/request errors or mobile overflow; mobile screenshot
inspected. Local Chromium fallback, WebGL disabled, not cloud. Production was not
modified; health retains original weight hash and unapproved demo status.

Artifacts: `research/checkpoints/footer-augmentation-cv-20261002/` contains the
pre-run protocol, all fold train/held IDs, ten model/vectorizer files with hashes,
original and counterfactual out-of-fold predictions, and browser input snapshots.
Sanitized `results/footer_augmentation_cv_20261002.json` adds full metrics, runtime
versions, per-fold results and uncertainty; a copy is in parent outputs.
`results/augmentation_browser_20261002.json` stores responses and screenshot hashes;
raw UI responses/screenshots are in parent `outputs/live-browser-augmentation-20261002/`.
Three augmentation tests and five exact-cleaning tests passed.

Reproduce: `python3 research/scripts/footer_augmentation_cv.py --data
research/data/pbc-snippets-20261001/train.jsonl --output <fresh-directory>`.
Decision: retain a robustness research result, reject any accuracy-improvement
claim, and do not deploy. More invariance alone has not addressed the very low
CENTER recall or the annotation/task-definition problems.

## 2026-10-02 03:12 UTC: exact-footer 2x2 training ablation

Trained matched raw and cleaned TF-IDF word/bigram logistic-regression heads with
fixed C=1, balanced classes, seed20261001, min_df=2, max_features=20000, sublinear
TF and max_iter=1000. Same settings as the prior raw baseline; vocabulary/IDF fit
on each training view only. Removed only complete paragraphs matching the two
normalized hashes recorded in the previous audit. No broad publisher-name filter,
label changes, original-file edits, test access or deployment. The selection of
these footers was development-informed, not an independently specified transform.

Affected 14/115 training and 12/66 validation items. Both full views retained all
items; unchanged items preserve their exact text. Derived cleaned JSONL files,
source/clean hashes, protocol and model weights are local in
`research/checkpoints/pbc-boilerplate-20261002/`. No exact cross-split duplicates
were introduced. Raw/raw label predictions reproduced the prior baseline exactly.

| Training view | Evaluation view | Matches /66 | Macro-F1 | Unanimous matches /33 |
| --- | --- | ---: | ---: | ---: |
| Raw | Raw | 39 | .5432 | 13 |
| Raw | Clean | 42 | .6123 | 16 |
| Clean | Raw | 40 | .5610 | 14 |
| Clean | Clean | 42 | .6074 | 16 |

Raw/clean gained four matches and lost one. Clean/clean gained six and lost three
relative to raw/raw. Among the 12 affected validation items, matches rose from
5/12 to 8/12 (raw/clean) or 9/12 (clean/clean). For the 54 unaffected items,
raw/clean stayed 34/54 while clean/clean fell to 33/54. Retraining therefore changes
more than the removed tokens' direct contribution. No winning cell was selected
for deployment. All four results are retained, not only the best metric.

Event-string-cluster bootstrap (5000, seed20261001) paired agreement difference
intervals versus raw/raw: raw/clean [0,.0988], clean/clean [-.0333,.1449]. These are
exploratory reused-validation intervals; the previous event-family dependence
caveat still applies. Annotators saw raw text, so cleaned-view agreement is a proxy
and does not establish task-matched independent accuracy. 63.6% is far below target.

GPT-6 Astra Medium reviewed the design using the terminal CLI; advice retained at
`research/data/boilerplate-advice-20261002.txt`. Important caveat: a flip establishes
sensitivity to the intervention, not a specific learned shortcut mechanism. Removal
also changes token adjacency, length and TF-IDF normalization.

Live-browser test: chose the first affected validation ID for each footer hash,
before observing live responses; evaluated raw and cleaned versions. One article
changed RIGHT (.975670) to LEFT (.995493) after removing only a copyright/reprint
paragraph, with one model window and no truncation in either version. A post hoc
repeat of that pair reproduced both overall responses exactly. Its original two
annotators were Right/Center; the cleaned prediction moves away from both, though
no human judgments on cleaned text were collected. The other article remained
RIGHT (.999483 to .998094). Thus the linear-model result does not authorize a
production-wide cleaning change.

Six total browser submissions across initial/repeat runs returned HTTP 200. No
page errors, failed requests or mobile overflow; repeat mobile screenshot visually
inspected. Local Chromium fallback, WebGL disabled, not cloud. Production health
still reports original hash 548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d,
demo mode, release unapproved. Raw UI responses/screenshots remain in parent
`outputs/live-browser-boilerplate-20261002/` and `outputs/live-browser-boilerplate-recheck-20261002/`.

Five new exact-cleaning tests and five prior corpus tests passed. Committed
`results/boilerplate_ablation_20261002.json` preserves four evaluations, raw per-ID
predictions/probabilities, changes, per-class/strict/slice metrics, model hashes,
runtime versions and bootstrap results; `boilerplate_browser_20261002.json` records
browser outputs, repeat selection and screenshot hashes. User-facing metrics copy
is in parent outputs. Full copyrighted text and fitted joblib weights remain local.

Reproduce the training cells with `python3 research/scripts/boilerplate_ablation.py
--data research/data/pbc-snippets-20261001 --baseline
research/checkpoints/pbc-snippets-tfidf-20261001/training_results.json --output
<fresh-directory>`. Tests: `python3 -m unittest discover -s tests -p
test_boilerplate_ablation.py -v`.

Decision: preserve as a modest development lead and a reproducible production
sensitivity failure, not verified high accuracy. No production preprocessing or
model replacement. Any cleaned-text candidate needs separately validated annotation
compatibility, robustness and task-matched independent evaluation.

## 2026-10-02 02:11 UTC: development split and boilerplate audit

Audited all 7,590 train/validation pairs (115 x 66) without accessing the reserved
test. Added `scripts/audit_development_overlap.py`, verifying feature alignment and
input hashes before computing normalized five-word shingle overlap and cosine
similarity using the already-frozen MiniLM vectors. Preset heuristic candidates:
cosine >=.85 OR Jaccard >=.30 OR shorter-set containment >=.50 with >=20 shared
five-grams. No pair crossed these thresholds, and no ID, normalized full-text hash
or exact normalized event string crossed partitions. These checks are not proof
of semantic independence. Top 20 lexical/semantic pairs and all nearest training
neighbors are retained for review regardless of flags.

AI-assisted inspection of the highest-cosine pair found a shared originating news
episode: allegations by Leeann Tweeden about Al Franken on a 2006 USO tour and
the ensuing ethics-probe/political response. Five training excerpts cover the
allegations and ethics-probe calls; one validation excerpt covers reactions to
Trump's response to those same allegations. Source event descriptions differ.
Closest pair cosine .7669, Jaccard .00725, so the preset detector missed this
family relationship. Texts are not exact duplicates on inspection. Define family
here as the same specific originating allegations and directly ensuing responses,
not merely shared actors or broad subject matter. This is not an exhaustive audit
or independent human adjudication, and it does not prove model exploitation.

**Correction to earlier wording:** the original split is event-string-group-disjoint,
not established event-family-independent. Historical manifests and partitions stay
unchanged. Future preparation metadata and README now explicitly qualify this.
Shared healthcare, North Korea and other topics in remaining nearest pairs do not
by themselves establish duplicate events; no further event groups were merged.

Highest lexical overlap was publisher licensing boilerplate, not shared story
content: 30 shared five-grams, Jaccard .2158. An added exact normalized paragraph
audit (minimum eight words) found a 34-word licensing paragraph in 12 training and
7 validation excerpts, plus a 12-word copyright/reprint notice in 2 training and
5 validation excerpts. These are source cues and non-story material, not automatic
label leakage proof. Because the frozen text matches what annotators saw, no
paragraph was removed and no labels were changed. Future cleaned-text datasets
would require their own version and annotation-compatibility assessment.

GPT-6 Astra Medium reviewed the interpretation through the terminal CLI. Advice
retained locally at `research/data/overlap-review-20261002.txt`: a single reviewed
family cannot establish prevalence or performance inflation; threshold misses do
not establish absence of leakage; exclusions change sample composition.

Exploratory sensitivity removes the single validation member of that reviewed
family solely for this report. Full scores remain primary; no split was rewritten,
candidate selected, or model retrained. Released-label agreement:

| Model | All 66 | Excluding reviewed family, 65 |
| --- | ---: | ---: |
| Production RoBERTa | .4697 | .4769 |
| Prior Astra prompt | .5303 | .5231 |
| TF-IDF word C=1 | .5909 | .6000 |
| Frozen MiniLM C=.1 | .5606 | .5692 |

Differences are under one percentage point and do not explain the overall failure
to meet targets. The smaller slice is neither independent nor a repaired test set.
No uncertainty interval for unseen-family generalization can be inferred from one
reviewed family's removal. Other relationships and pretraining overlap remain open.

Seven focused overlap tests passed. Two affected real excerpts were submitted
through the public browser form: HTTP 200 for both, no page errors, failed requests
or mobile overflow; mobile screenshot inspected. Production predicted RIGHT
(.999471) for the boilerplate case and LEFT (.999327) for the reviewed event case;
these are uncalibrated scores, not correctness probabilities. Local Chromium
fallback, not cloud; no deployment.

Artifacts: `results/development_overlap_20261002.json` preserves the first audit;
`development_overlap_detail_20261002.json` adds paragraph analysis;
`development_overlap_review_20261002.json` records review provenance/IDs;
`overlap_sensitivity_20261002.json` retains full and sliced metrics;
`overlap_browser_20261002.json` preserves sanitized responses/screenshot hashes.
Raw screenshots/UI responses are in parent `outputs/live-browser-overlap-20261002/`.
Reproduce audit with `python3 research/scripts/audit_development_overlap.py --data
research/data/pbc-snippets-20261001 --features research/data/minilm-snippets-features.npz
--output <fresh-path>`. Sensitivity script accepts --data (validation JSONL),
--comparison (original comparison JSON), --review (review JSON), --output.

Decision: preserve the audit and stricter metadata; no high-accuracy claim. Future
evaluation needs reviewed episode-family grouping and explicit treatment of source
boilerplate, without retroactively presenting this reused validation as independent.

## 2026-10-02 01:10 UTC: structured comparator on real validation excerpts

Ran the unchanged structured prompt from ecc32c8 on all 66 frozen validation
excerpts through GPT-6 Astra Medium. Protocol saved before inference in
`results/structured_validation_protocol_20261002.json`. Eleven sequential batches
of six, 356.6 seconds total subprocess time; hosted model weights/revision unknown.
No prompt changes, retries, relabeling, training or reserved-test access. All 66
outputs passed schema and exact-span checks. No item was silently dropped.

Implemented `scripts/evaluate_structured_stance.py` to validate hashes, input text
identity and complete ID coverage, retaining MIXED and INSUFFICIENT in both the
denominator and 3x5 confusion matrix. Secondary conditional agreement always
reports coverage. Five new evaluator tests and nine prior contract tests passed.

| Metric | Structured author stance | Previous forced-three-way Astra |
| --- | ---: | ---: |
| Released-label matches /66 | 27 | 35 |
| Released-label agreement | .4091 | .5303 |
| Macro-F1, three reference classes | .3563 | .5214 |
| Three-way output coverage | 64/66 | 66/66 |
| Conditional three-way agreement | 27/64 (.4219) | 35/66 (.5303) |
| Unanimous matches /33 | 24 | 27 |
| Disputed matches /33 | 3 | 8 |

Structured output counts: CENTER 50, LEFT 7, RIGHT 7, INSUFFICIENT 2, MIXED 0;
all 66 identified as political. LEFT/CENTER/RIGHT recall: .1579/.9048/.1923.
Confusion rows LEFT/CENTER/RIGHT, columns LEFT/CENTER/RIGHT/MIXED/INSUFFICIENT:
[[3,14,1,0,1],[1,19,1,0,0],[3,17,5,0,1]]. Eleven outputs changed from the previous
Astra labels; nine previously matching outputs became unmatched and one changed
in the opposite direction. Event-cluster bootstrap over 19 events, 5000 draws,
seed20261002: paired agreement difference interval [-.2174,-.0312]. This quantifies
reused-validation uncertainty, not independent task-matched product quality.

Error review: eight of the nine lost matches became CENTER, with rationales
distinguishing criticism, ridicule, or partisan framing from explicit policy
endorsement; the ninth withheld judgment on a critical headline plus biography.
Four lost matches were in the unanimous subset. This supports a task-definition
concern: requiring overt ideological policy endorsement can miss the broader
political framing that corpus annotators labeled. It does not prove all original
labels are correct. The source's partisan-directed disagreement resolution remains
a limitation. Prompt framing, schema, batch size (6 vs 8), and hosted-model
nondeterminism were not isolated, so no schema-specific causal claim is warranted.

Real-browser regression check on the same six saved article excerpts: six HTTP
200 responses, identical overall results to the earlier production audit; no page
errors, failed requests or horizontal overflow at mobile size. Mobile screenshot
visually inspected. Local Chromium 154.0.8037.93 fallback, WebGL disabled, not cloud.
Sanitized browser outputs/hashes: `results/structured_browser_20261002.json`;
screenshots in parent `outputs/live-browser-structured-validation-20261002/`.

Main sanitized evidence: `results/structured_validation_20261002.json` with raw
label predictions, all metrics, strata, uncertainty, hashes and run manifest;
copy in parent outputs. Full raw model outputs, evidence spans, rationales and CLI
logs remain local at `research/data/astra-structured-validation-20261002/`.
Reproduction instructions added to research README. No deployment occurred.

Decision: reject this structured prompt as a demonstrated accuracy improvement.
Its strong synthetic-control behavior did not carry over to this corpus comparison.
Retain the output validator and coverage-aware evaluator. Further work should
separately define ideological policy stance and partisan framing/affect, preserving
attribution, rather than repeatedly adjusting prompts against these 66 excerpts.
Fresh task-matched independent human evaluation remains required for release.

## 2026-10-02 00:09 UTC: structured author-stance prototype

Implemented `scripts/stance_contract.py`, an offline research comparator using
GPT-6 Astra Medium through the authorized Codex CLI. No trained weights changed.
Output separates political relevance, author stance, attributed stances, exact
evidence spans and rationale. Author stance supports LEFT/CENTER/RIGHT/MIXED/
INSUFFICIENT, so it is not directly interchangeable with the production three-way
classifier. Nonpolitical text receives political=false plus INSUFFICIENT, not
CENTER. Schema validation rejects extra fields, invalid types/labels, missing or
duplicate IDs; semantic checks reject nonexistent/empty evidence, unsupported
directional outputs and inconsistent nonpolitical fields. Exact evidence presence
does not prove a rationale is true or evidence supports the conclusion.

Fixed prompt tested on the previous six quotation controls and six additional
AI-authored controls. The additional fixture was written before reading the first
batch predictions; the prompt was not changed between batches. These are targeted
development diagnostics, not an independent human benchmark. All 12 responses
passed final schema/evidence validation. Outputs: LEFT 1, RIGHT 2, CENTER 5, MIXED 1,
INSUFFICIENT 3; two were nonpolitical and one was a political-context fragment.
No accuracy, macro-F1 or human-gold success claim is made.

| Case | Astra author stance | Relevant attribution |
| --- | --- | --- |
| Left endorsement | LEFT | None |
| Left attribution | CENTER | LEFT |
| Right endorsement | RIGHT | None |
| Right attribution | CENTER | RIGHT |
| Balanced attribution | CENTER | LEFT and RIGHT |
| Cooking quotation | INSUFFICIENT; nonpolitical | None |
| Health-care plus gun-rights endorsement | MIXED | None |
| Factual hearing | CENTER | None |
| Reject higher taxes; endorse tax cuts | RIGHT | LEFT |
| Quoted progressive witness | CENTER | LEFT |
| Taxes fragment | INSUFFICIENT | None |
| Parser instruction quoted as data | INSUFFICIENT; nonpolitical | None |

Live-browser comparison on the six additional controls: production returned LEFT
for five and abstained on the short fragment (raw LEFT .996151). The other raw
Left scores were .996848, .998535, .998927, .998175 and .996518 in fixture order.
All six form submissions HTTP 200; no page errors, failed requests or mobile
horizontal overflow. Mixed-endorsement desktop screenshot visually inspected.
Local Chromium fallback with WebGL disabled, not a cloud-browser run. No new
production deployment. These observations do not establish a causal benefit of
the structured prompt versus the previous Astra prompt, which was not rerun here.

Negative result/infrastructure repair: global Python lacked jsonschema. Initial
tests failed; the first model call finished but its local validation failed. Raw
output was retained and validated later without a repeated inference call. Its
original manifest deliberately still has an empty completed-batches list. Created
isolated `research/checkpoints/stance-runtime` with jsonschema==4.23.0; application
dependencies unchanged. Import now occurs before any paid/inference work so a
missing dependency fails early. Nine focused validator tests pass. Final validator
also revalidated both raw batches after adding two consistency checks.

Artifacts: `results/stance_contract_20261002.json` includes prompt/input/output/
validator hashes, both raw predictions, run manifests, dependency versions,
coverage, browser responses and screenshot hashes. Hosted Astra weights/hash are
not available; do not imply reproducibility of server-side weights. Raw CLI logs
are local under `research/data/astra-stance-{contract,challenge}-20261002/`.
Screenshots: parent workspace `outputs/live-browser-stance-20261002/`.

Reproduce in an isolated environment using `research/stance_requirements.txt`,
then `python research/scripts/stance_contract.py --input
research/fixtures/stance_challenge_20261002.json --output <fresh-directory>`.
Run `python -m unittest discover -s tests -p test_stance_contract.py -v` with that
same environment. No reserved corpus test access, human relabeling or training.

Decision: promising diagnostic behavior; retain research-only status. Production
integration needs fresh independently annotated passages, complete coverage and
per-class evaluation, robustness and latency/cost checks, and an approved inference
deployment route. An authenticated research CLI is not a product API service.

## 2026-10-01 23:08 UTC: annotation-policy audit and quotation probes

No training or model selection this run. Implemented `annotation_audit.py` to
reconcile unchanged previous predictions with each original annotator and the
released labels. Inputs are the 66 validation excerpts across 19 events, previous
comparison results and previous weighting results; their SHA-256 hashes and all
per-ID comparisons are in `results/annotation_audit_20261001.json`. Reserved test
not opened. Worker pairs: 21 CENTER/CENTER, 5 LEFT/LEFT, 7 RIGHT/RIGHT,
14 CENTER/LEFT, 19 CENTER/RIGHT. The 33/33 unanimous/disputed split occurred under
the original event split; it was not deliberately balanced.

| Prior model | Released-label matches /66 | Mean worker agreement | Matches neither worker /66 |
| --- | ---: | ---: | ---: |
| Production RoBERTa | 31 | .3636 | 31 |
| Astra Medium fixed prompt | 35 | .6288 | 10 |
| TF-IDF word C=1 | 39 | .4015 | 26 |
| Frozen MiniLM C=.1 | 37 | .3864 | 27 |
| Worker-distribution MiniLM C=1 | 37 | .4621 | 22 |

Astra's released-label agreement is 27/33 on unanimous items but 8/33 on disputes.
Of its 31 released-label disagreements, 21 match the original Center annotator.
TF-IDF achieves 26/33 released-label matches on disputes but only 13/33 on unanimous
items. This exposes sensitivity to the source's partisan-directed resolution rule;
it does not establish which labels are correct. Mean worker agreement gives .5
for matching either worker in a disputed pair, not full credit, and is explicitly
not product accuracy. Neither-worker matches are descriptive, not certain errors.
No labels were changed, candidates selected, or new accuracy claim made.

GPT-6 Astra Medium reviewed the interpretation via the terminal CLI. Advice is
retained locally in `research/data/annotation-audit-advice-20261001.txt`. Its
description of the 33/33 split as deliberately balanced was incorrect and is not
adopted. Its cautions about small reused data, annotation dependence and fresh
blinded human evaluation remain applicable.

Created six AI-authored diagnostic controls, fixed in
`fixtures/quotation_probe_20261001.json`, and tested each through the public site's
actual browser form in Article mode. Local Chromium fallback, WebGL disabled;
not a cloud-browser run. All six HTTP responses succeeded, no page/request errors,
and no mobile horizontal overflow. The right-endorsement desktop screenshot was
visually inspected. Every output was LEFT:

| Control | Raw Left score (uncalibrated) |
| --- | ---: |
| Left endorsement | .998116 |
| Left statement attributed without endorsement | .997602 |
| Right/free-market endorsement | .985512 |
| Right statement attributed without endorsement | .997641 |
| Balanced attribution | .998102 |
| Nonpolitical cooking quotation | .998144 |

Quotes alone do not prove neutral author framing, and these controls are not
independent human gold. Nonetheless, the explicit free-market endorsement and
nonpolitical cooking response show unresolved directional/relevance failures.
Attribution did not change the label in either paired case; this observation alone
cannot identify the model's causal mechanism. No keyword guard was added.

Raw responses, visible UI text, source-fixture and screenshot hashes, browser
version and post-probe production health are committed in
`results/quotation_probe_20261001.json`. Screenshots are retained in the parent
workspace at `outputs/live-browser-quotation-20261001/`. Production hash remains
548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d,
demo mode, release unapproved. Four focused annotation-audit tests passed.

Decision: no deployment. Next evaluation must separate author endorsement,
attributed political stance, nonpolitical material and balanced/mixed framing,
with independently blinded human labels and prespecified adjudication. Keep
representative sampling separate from curated challenge cases and report both;
do not use model output as gold or erase legitimate human disagreement.

## 2026-10-01 22:07 UTC: annotation-weight ablation

Hypothesis: raw-frequency balancing followed by disagreement downweighting can
distort effective class mass. Test annotation handling separately from encoder
training, using the existing frozen MiniLM features and unchanged train/validation
IDs. GPT-6 Astra Medium reviewed this design through the authenticated terminal
client; advice retained locally as `research/data/weighting-advice-20261001.txt`.

Ran 12 logistic-regression heads: hard labels, .25 dispute weighting, two equally
weighted original worker labels per article, and unanimous-only training, each at
C=.1,1,10. Compute class balance from effective base mass, then normalize total
sample weight to 115 in every regime; class_weight=None avoids double balancing.
Protocol written before training; select by all-validation macro-F1, with ties
favoring earlier regime/C. Same encoder, feature hashes, split hashes and seed
20261001; max_iter=1000. No reserved test data read by this run.

| Regime | C | Accuracy (66) | Macro-F1 | Unanimous accuracy (33) |
| --- | ---: | ---: | ---: | ---: |
| Hard | .1 | .5606 | .5132 | .3636 |
| Hard | 1 | .5455 | .5077 | .3939 |
| Hard | 10 | .5303 | .5106 | .4242 |
| Downweight | .1 | .5455 | .5040 | .3939 |
| Downweight | 1 | .5606 | .5331 | .4545 |
| Downweight | 10 | .5000 | .4867 | .4545 |
| Worker distribution | .1 | .5303 | .5000 | .3939 |
| Worker distribution | 1 | .5606 | .5469 | .5152 |
| Worker distribution | 10 | .5000 | .4993 | .5455 |
| Unanimous only | .1 | .5303 | .5238 | .4848 |
| Unanimous only | 1 | .4848 | .4850 | .5758 |
| Unanimous only | 10 | .4394 | .4276 | .5758 |

All three hard-label control predictions reproduce previous frozen-head runs
exactly. Selected worker-distribution C=1 recalls LEFT=.5263, CENTER=.4286,
RIGHT=.6923. Confusion in LEFT/CENTER/RIGHT order: [[10,5,4],[7,9,5],[5,3,18]].
Compared with the prior frozen baseline, accuracy is unchanged (37/66), while
macro-F1 rises .0337. Event-cluster bootstrap (5000, seed20261001) accuracy interval
is [.4259,.6949]; paired accuracy difference interval [-.1111,.1000]. This is
exploratory repeated-validation selection, not a confirmed generalization gain.
Unanimous-only has only 54 unique training articles; duplicating worker rows does
not increase independent sample size. All candidates predict all 66 items.

Artifacts: `research/checkpoints/pbc-weighting-20261001/` contains protocol,
12 joblib heads and metrics with model hashes. Sanitized metrics, raw label
predictions, per-class and strict-subset reports are committed in
`research/results/weighting_ablation_20261001.json`; article text remains local.
Reproduce with `python3 research/scripts/weighting_ablation.py --data
research/data/pbc-snippets-20261001 --features
research/data/minilm-snippets-features.npz --output <fresh-directory>`.
Five focused tests cover effective balancing, worker targets, unanimous filtering,
dispute mass, and invalid provenance/missing classes.

Verification: all five new tests plus five existing corpus tests passed. Repeated
the six real-excerpt browser interactions on https://bias.r4him.tech/ using local
Chromium (cloud-browser fallback, WebGL disabled as previously documented).
All six returned HTTP 200 and identical overall results to the earlier audit;
no page errors, failed requests or horizontal overflow at 390x844. Mobile screenshot
was visually inspected. Screenshots and raw responses are retained at
`outputs/live-browser-weighting-followup/` in the parent workspace. Functional
success does not establish classifier accuracy.

Decision: retain research-only status under corpus noncommercial restrictions;
no promotion or production deployment. Weighting alone is insufficient. Next,
investigate task-matched annotation definitions and data sources rather than
continuing to optimize these same 66 validation examples. An independently
annotated evaluation with explicit neutral/mixed/quoted-text policy remains a
release prerequisite.

## 2026-10-01: local research continuation

Recovered the existing research branch `fix/reliable-bias-analysis` at 4483e70;
`main` still contains the older application. New work is on
`research/accuracy-2026-10-01`. Production health identifies the same original
weight hash as the previous audit, aggregation v1, demo_mode=true, and
release_approved=false. Do not equate the new live response schema with a new
trained model. SSH key authentication failed; no server changes were made.

The requested GPT-6 Astra with Medium reasoning executed successfully through
`codex exec --ephemeral -m gpt-6-astra -c 'model_reasoning_effort="medium"'`.
This establishes the research subprocess configuration, not this parent chat's
model, an API deployment, or a fine-tuned classifier. Its initial research advice
is preserved in the workspace. The current computer has 8 GB RAM and an Intel
i5 CPU; initial experiments use small supervised models and cloud LLM inference.

New research corpus: https://github.com/ksolaiman/PoliticalBiasCorpus at
b193ee173936b281183ca1dc101ae4de215a0e5c. Its CC-BY-NC-SA-4.0 license restricts
these experiments to research; no derived model is approved for commercial
deployment. The 270 released human-derived labels include 139 strict agreements
and 131 Center/partisan resolutions toward the partisan label. Report these
separately. Labels are perceived political framing, not objective truth.

An initial full_text run was stopped after discovering HTML/mojibake and the
fact that annotators saw a title and three snippets. Its partial artifacts are
retained under research/data/pbc-20261001 and astra-validation-20261001, and
research/checkpoints/pbc-tfidf-20261001. Those results are invalid for the primary
matched-context comparison. No test predictions were made in that initial run.

The corrected preparation uses the title and exactly three shown snippets from
the original HIT input file. It freezes 115 training, 66 validation and 89 test
items with disjoint normalized event identifiers (seeds 20261001,20261002), and
checks exact text uniqueness. Human agreements are 54/33/52 respectively.
Publisher and semantic near-duplicate separation are NOT yet established.
Pretraining contamination is unknown. Test items must remain unused for fitting,
prompt selection or threshold tuning. The validation set is already development
data due to model comparison; do not call it an independent final test.

Predeclared comparisons: word and word+character TF-IDF with balanced logistic
regression at C in [0.1,1,10]; current live RoBERTa; frozen Astra Medium prompt.
Select supervised settings on validation macro-F1. Astra sees only IDs/text,
never reference labels, event descriptions or outlet metadata. These outputs
are model predictions, never substitute human annotations.

Working product target: >=90% accuracy and >=0.85 macro-F1, with every class
recall >=0.80, on an independently reviewed task-matched holdout; additionally
measure nonpolitical false labeling, mixed/quoted text, coverage, uncertainty,
and latency. These are research targets, not achieved scores. This small
historical corpus alone cannot certify the product even if a point target passes.

Browser environment: the desktop browser tool failed during startup. Terminal
Playwright can load the public site, but initial input interaction stalled.
A retry disables WebGL and records that condition. These are local browsers
accessing the cloud-hosted app, not cloud-hosted browser execution.

All raw news text, model weights, prompts containing text and intermediate logs
stay in ignored research/data or research/checkpoints. Publish IDs, hashes,
metrics, scripts and limitations, not raw article bodies.

### Completed validation and training

All planned 66-item live and Astra predictions completed. Six TF-IDF models and
three frozen-MiniLM classifier heads were trained on 115 items. MiniLM was pinned
to sentence-transformers/all-MiniLM-L6-v2 revision
1110a243fdf4706b3f48f1d95db1a4f5529b4d41, with downloaded file hashes retained.
Masked-mean embeddings cover all windows (254 content tokens, overlap 32), followed
by document pooling. Reference: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

| Candidate | All 66 label agreement | Macro-F1 | Agreement on 33 unanimous items |
| --- | ---: | ---: | ---: |
| Live RoBERTa | 46.97% | .4204 | 39.39% |
| Best TF-IDF (word, C=1) | 59.09% | .5432 | 39.39% |
| Best frozen MiniLM (C=.1) | 56.06% | .5132 | 36.36% |
| Astra Medium, frozen prompt | 53.03% | .5214 | 81.82% |
| Partially fine-tuned MiniLM, selected epoch 3 | 31.82% | .2081 | 60.61% |

The unanimous subset is highly imbalanced: 5 LEFT, 21 CENTER, 7 RIGHT. Astra's
macro-F1 on this subset is .7649, not .8182. Its all-item CENTER recall is .8571
versus .0952 for RoBERTa, but it often disagrees with partisan labels derived from
Center/partisan disagreements. Do not present the unanimous subset as overall
product accuracy, or use our interpretation to relabel the six remaining errors.
Some disagreements reflect party sentiment versus policy ideology: criticizing a
Republican from a restrictionist immigration position is not necessarily Left.

Exploratory event-cluster bootstrap (5,000 draws) gives a 95% interval of
[-.0392,.2656] for the best TF-IDF's accuracy difference from live; Astra's interval
is [-.0926,.2364]. Both include zero. Selecting TF-IDF on this validation set also
adds selection optimism. There is no statistically established population gain.
Of 59 live outputs with raw top score >=.95, 30 disagreed with the reference label.

Partial fine-tuning actually updated the top two MiniLM blocks and a new mean-pool
classification head for three epochs, with per-document window weights, balanced
class loss, .1 label smoothing, and .25 weighting for disputed source labels.
Validation accuracy by epoch: .3182, .2879, .3182. The candidate collapsed toward
CENTER and was rejected. Preserve the loss curves and weights; decreasing training
loss was not evidence of improved generalization. No full RoBERTa retraining occurred.

Browser verification succeeded after waiting for React hydration. Five controlled
inputs and six actual corpus article-excerpt inputs ran through the public website;
all returned 200. Six article predictions exactly matched the separate API run.
No browser page errors or mobile horizontal overflow were recorded. Screenshots
and raw results are in the workspace outputs/live-browser-hydrated and
outputs/live-browser-articles directories. Browser WebGL was disabled; graphical
background behavior with WebGL enabled is not verified by these runs. Cooking,
neutral hearing logistics and balanced healthcare reporting were assigned LEFT.
These controls are diagnostics, not independently annotated accuracy evidence.

Five new evaluation-harness tests passed; Python compilation, Node syntax, and
three-way ID/text/event split separation passed. No application/runtime code was
changed, no test-set predictions were made, and no candidate was deployed.
Full numerical evidence without article text: results/corpus_comparison_20261001.json.

Execution environments: both used Python 3.11.0 on Intel macOS. The existing
neural environment reported torch 2.2.2, transformers 4.41.2, numpy 1.26.4,
safetensors .7.0 and tokenizers .22.2. This inherited environment differs from
the branch's pinned production requirements and is not a newly verified portable
dependency specification. The sklearn environment reported scikit-learn 1.8.0,
numpy 2.4.2, scipy 1.17.0, requests 2.32.5 and joblib 1.5.3. Browser: Chromium
154.0.8037.58; terminal Codex 0.159.2. Re-run neural comparisons in a clean,
compatible pinned environment before using the checkpoints beyond research.

### Next work

1. Resolve task definition with a separate annotation layer: policy ideology,
   party sentiment, neutral reporting, mixed positions and political relevance.
   Preserve existing human labels and disagreement records; never silently replace
   a reference label to improve a score.
2. Audit a more directly supervised passage corpus before collecting more model
   scores. Candidate sources: Ideological Books Corpus
   (https://www.cs.umd.edu/~miyyer/ibc/index.html) and MITweet
   (https://aclanthology.org/2023.emnlp-main.256/). IBC has a public sample and full
   access instructions. MITweet's facet definitions are not interchangeable with
   US partisan labels. Check availability, licenses and annotation semantics first.
3. Improve neural training only after resolving label noise. Candidate follow-up:
   warm-start the head from the frozen-feature classifier and compute class weights
   from effective weighted label counts. Tune on development only.
4. Keep the 89 reserved test items untouched until a candidate meets development
   targets. Add independently reviewed contemporary passages before any claim of
   product-level high accuracy. Obtain deployable training data before promotion.

The user-authorized recurring research heartbeat now runs hourly. Its instructions
require substantive research work, preserved evidence, Astra Medium where needed,
and reports only for meaningful changes. Scheduling is not a continuously running
training process and does not establish the accuracy goal as achieved.

## 2026-09-28: initial audit and user-authorized implementation

Repository baseline: 68bdc9115b7f403cb96aff1ee2a3aae20971931e.
User authorized implementation, experiments, and eventual deployment after validation.
The old approximately 89% accuracy claim is not independently reproducible: training notebook,
data revisions, split IDs, and original evaluation checkpoint were not found in the available
repository or relevant Library searches. Do not repeat it as verified performance.

### Live API and exported checkpoint parity

Local exported model loaded with no missing, unexpected, or mismatched weights under
Transformers 4.57.1, tokenizers 0.22.2 and CPU PyTorch 2.6.0.
Weights SHA256: 548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d.
Local and live probabilities differed by at most 0.000003 over four diagnostic texts.
The neutral meeting example and dinner example returned LEFT with scores .998220 and .992506.
This points away from a VPS-only problem, but is not proof of parity with the missing training environment.

### Preliminary model comparison

60 examples from the public Baly Article-Bias-Prediction media/valid.tsv split,
20 per class, shuffled seed 20260929, content_original with at least 30 words,
first 512 tokens. Training overlap unknown for all pretrained models, so these
are exploratory diagnostics, NOT an independent final test or a model selection guarantee.

| Model | Accuracy | Macro F1 |
|---|---:|---:|
| User's exported RoBERTa | .733333 | .729798 |
| matous-volf/political-leaning-politics | .683333 | .678618 |
| matous-volf/political-leaning-deberta-large | .716667 | .723172 |

Candidate revisions: politics bd4cf012e288a9d915c2f919e78ba48c61a48dab;
DeBERTa 36e135e33c24d2a1f6dbdb0eaa774d09e8dfb079.
Candidate label IDs are 0 LEFT, 1 CENTER, 2 RIGHT per author model cards;
the user checkpoint is 0 LEFT, 1 RIGHT, 2 CENTER. Do not reuse one mapping for the other.
Both alternative models carry CC-BY-NC-4.0 licenses. Neither was deployed.

A TF-IDF/logistic regression diagnostic on the published media split scored .287776
accuracy and .272883 macro F1 on validation. Exact normalized text deduplication
removed six training rows. Source names overlapped across published training and
validation splits, so it was NOT a strictly publisher-disjoint evaluation. A corrected
domain-disjoint run was started but its result was not recovered before reset.

### Infrastructure and tests before reset

An initial implementation passed 16 regression tests and a Next.js production build.
No SSH agent or private key was configured; no VPS deployment was performed.
No transformer retraining or independent human annotation was completed.

## 2026-09-29: resumed session

The temporary workspace was reset while inactive, losing unpushed code, downloads,
and raw per-example outputs. The numbers above are recovered from the conversation's
actual tool outputs, not recreated raw results. Completed tests apply to the prior
implementation; rebuilt code must be tested again. GitHub checkpoints will now be
created incrementally. Full-document comparison and corrected TF-IDF results must
be rerun. No production changes have been made.

## Research discipline

Keep raw predictions and hashes with each run. Separate synthetic diagnostic cases,
public benchmark validation, and independently annotated final test sets. Record
negative results and licensing. Report macro F1, per-class recall, selective accuracy,
coverage, nonpolitical false-label rate, confidence intervals, and slice performance.
Never claim high accuracy from suppressed predictions or a contaminated test set.

## References

- https://github.com/ramybaly/Article-Bias-Prediction
- https://arxiv.org/abs/2010.05338
- https://huggingface.co/matous-volf/political-leaning-politics
- https://huggingface.co/matous-volf/political-leaning-deberta-large
- https://huggingface.co/mediabiasgroup/roberta-babe-ft
- https://arxiv.org/abs/1706.04599

### Reconstructed implementation and new runs

- Backend now processes complete documents with overlapping windows and explicitly records coverage. The aggregation is experimental; it is not a demonstrated accuracy improvement.
- Frontend sends the requested mode and uses a separately computed full-document overall result. It does not average sentence classifications into an article label.
- Exact passage offsets, abbreviation-aware splitting, nonduplicated article extraction, supported pinned dependencies, loading diagnostics, model hashes, input limits and model-bound calibration policies are implemented.
- Without an approved policy, predictions abstain and raw scores remain explicitly experimental. This is a reliability guard, not a trained relevance classifier or an accuracy improvement. Nonpolitical recognition remains unsolved.
- Reinstalled a corrupted CPU PyTorch shared library after a SIGBUS; import and package dependency checks then passed.
- 22 regression tests pass on the reconstructed code. Next.js production build, including TypeScript and lint checks, passed. A tiny randomly initialized RoBERTa completed one training epoch with article-window weighting and wrote a checkpoint. Its synthetic labels and 1/3 accuracy are plumbing checks only.

### Publisher-domain baseline

Pinned dataset revision: ced8111a720948e6a410e52031ace99c4e53f096.
Registrable-domain grouping corrected the initial hostname-only implementation:
blogs.wsj.com, online.wsj.com and wsj.com are one publisher group; likewise CNN subdomains.
Reserved test first, validation second, training last. Removed 2,981 training articles
whose publisher domains occur in evaluation and six exact normalized duplicates.
Final sizes: train 23,603, validation 2,356, test 1,300.
TF-IDF/logistic regression: validation accuracy .289898, macro F1 .279093.
Validation class counts: LEFT 1,640, CENTER 618, RIGHT 98. This severe imbalance
and publisher shift make accuracy alone misleading. No test predictions were used.
Data manifests, parameters, metrics and per-class results are preserved in results/.

### Paired context comparison

Reconstructed the same 60-article public validation sample, seed 20260929, 20/class.
First-512 result reproduced exactly: accuracy .733333, macro F1 .729798.
Full-document aggregation: accuracy .683333, macro F1 .671765.
CENTER recall fell from .60 to .45. Difference in accuracy full minus first: -.05.
Exploratory paired bootstrap 95% percentile interval [-.116667, 0], 10,000 resamples,
seed 20260929. This interval ignores publisher/story clustering and unknown training
contamination. It is not evidence of a reliable population improvement or definitive degradation.
All full-document examples were processed without silent truncation. Per-example scores,
logits, coverage and checkpoint hashes are preserved in context_comparison.json.
No labels were released: accepted coverage remains zero without a validated policy.
That zero coverage must not be presented as high accuracy or successful relevance handling.

### Research tooling and remaining gates

Added dataset preparation, baseline training, full-document evaluation, calibration,
offline candidate-policy evaluation and document-window transformer retraining scripts.
Calibration cannot use the test split; it requires annotation provenance and never
approves a policy. Offline policy evaluation checks exact test/validation overlap and
proposed point-estimate targets, but does not grant release approval.
Full transformer training, trained relevance handling, contemporary independent human
annotation, source/event/time leakage audit, robust confidence intervals and operational
staging are outstanding. No GPU is available here. No VPS SSH connection is configured.
The branch is a research and engineering checkpoint, not a production-ready high-accuracy
model. No merge, production deployment, or formal report has been performed.

## 2026-09-29: 100-example annotation pilot prepared

Prepared an unlabeled rubric-development pilot: 60 historical articles from 12 dataset
source identifiers and 41 topics, plus 40 original AI-authored controlled examples.
Selection uses source/topic/length diversity, excludes the earlier 60-example comparison,
and does not use inherited class labels. It does not establish independence from old
checkpoint training. All pilot items are development data and must be excluded from the
future final test. No contemporary independent evaluation set is claimed.

Added a labeling rubric covering political relevance, LEFT/CENTER/RIGHT, NONPOLITICAL,
UNCERTAIN, quotations, attribution, mixed positions, procedural reporting and lexical
false positives. The standalone reviewer hides inherited labels, verifies frozen text
hashes, keeps reviewer workspaces separate, requires reading confirmation and evidence,
and exports judgments. News text is not redistributed in the repository. The review
page can download pinned source snapshots directly from GitHub, or read the original
source folder locally. Source text is held in browser memory, not review exports.

Added a comparison tool for independent reviews: relevance agreement, five-label agreement,
Cohen's kappa, slice denominators, missing items and a disagreement/adjudication queue.
It rejects mismatched text, duplicate items and identical reviewer identities. It never
approves gold labels or substitutes machine judgments for missing human review.

Validation: all 100 frozen hashes verified; seven new annotation tests passed. JavaScript
DOM tests verified save, restore, reviewer separation, missing-text blocking, snapshot
verification, wrong-snapshot rejection and the 60-item loader with mocked network responses.
A full browser test could not run because the browser binary download was unavailable;
visual rendering and actual in-browser remote downloads remain unverified. No human
annotations have been performed, and automated UI fixtures are not included as annotations.

Next concrete action: two independent reviewers annotate the first 10 pilot items,
resolve rubric ambiguities, then independently complete or re-review under a frozen rubric.
Preserve the original judgments and document adjudication before deriving any gold labels.


## 2026-09-29: deployed controlled-input probe

Ran all 40 original controlled examples against the live article API sequentially,
2026-09-29 16:42:10 through 16:46:40 UTC. All 40 requests succeeded. All returned LEFT;
34 had top raw scores >= .95. The dinner example, glue instructions, door directions
and single word Taxes were among high-confidence LEFT results. These are diagnostic
failures of intended use, not an independently measured accuracy or population error rate.
The earlier full-news comparison found other labels, so universal class collapse is not
established. A confidence threshold alone cannot reject these high-confidence cases.
Political relevance and insufficient-context handling require their own validated stage.

The live health endpoint still returns only status=ok, so current server checkpoint
identity and runtime cannot be verified. No production code or model was changed.
Raw responses and elapsed request times are preserved in
research/results/live_controlled_probe_20260929.json; the accompanying Markdown summarizes
selected contrasts. The reproducible probe checkpoints every request and stops after
three consecutive failures. Outputs remain outside the annotation viewer.

The project owner has been shown selected model predictions in conversation. Their
judgments on exposed items cannot be described as fully blinded. The rubric now asks
reviewers to disclose prior exposure; an independent reviewer should not read diagnostic
outputs before submitting judgments. No human labels, model retraining, calibration,
release approval or final accuracy results were produced.

The temporary execution workspace was cleared; source code was recovered from GitHub.
The research notebook was recovered through its text-read interface after two byte
transfer attempts failed with HTTP 502. Existing notes were preserved and appended.

## 2026-09-29: experimental PoliticalDEBATE integration

Pinned large candidate `mlburnham/Political_DEBATE_large_v1.0` at
`1a3aff1ecb97ad93a6de598f7414b1707de7e7c3`; MIT model card reviewed previously.
Weights SHA-256 `5f83396d09cb0b802eafbe1f33f0ca03632f8dc17115051624cc4ef85b9815d4`.
Completed 40 fixed-hypothesis controlled probes; no human-gold accuracy claimed.
Preserved failures for vague criticism, partisan-name criticism, and mixed stances.
Added opt-in backend, independent-score UI, checkpoint verification, bounded
inference, and directly pinned public-IP URL transport. Real API smoke produced
nonpolitical dinner, insufficient-context Taxes, and expected tentative directions
for explicit Left/Right policy examples. Original RoBERTa remains default.
See `NLI_IMPLEMENTATION.md` for thresholds, limitations, and remaining gates.
No release approval or VPS deployment occurred. Full article comparison and final
integration verification are recorded separately as they complete.

### Completed candidate benchmark and guard follow-up

All 60 article predictions completed: PoliticalDEBATE v1 raw-label accuracy
0.483333, macro F1 0.483066, versus prior original first-window 0.733333/0.729798.
Candidate confusion LEFT/CENTER/RIGHT: [[6,12,2],[6,13,1],[4,6,10]]. Candidate is
not promoted to default. See `results/political_debate_comparison.md` for label
construct mismatch, pair-window differences and exploratory agreement coverage.
Post hoc model agreement gives 23/26 correct with 26/60 coverage, not high accuracy
on all inputs and not an enabled release policy.

Tested three additional guard hypotheses after observing failures. Retained only
mixed ideological endorsement, and only to withhold otherwise tentative Left or
Right when support >=0.8. Specificity and everyday-life guards were rejected for
observed failures. Their complete outputs remain in `nli_guards_development.json`.
Real long-input integration processed all 656 tokens across two windows and
rejected an oversized request and a localhost URL. Repeated inference was
identical in the API mode check. No final human-gold accuracy claim is made.


Final verification: 38 tests passed, final Next.js production build passed, and
real Chromium frontend-to-model checks passed on desktop/mobile with no page
errors. Busy errors and clearing in-flight responses were checked. Model-backed
checks and browser fixtures are retained in JSON; the browser script is reusable.
UI copy no longer incorrectly says every engine is RoBERTa, and help links now
open actual explanations. These checks establish functionality, not accuracy.

## 2026-10-02: decomposed phrase experiments and verified hosted checks

- The real CPU Instruct-2507 native stance-development comparison completed all 274 inputs with valid outputs: 175/274 (63.9%) human-majority matches, macro-F1 .6346. False stance calls rose to 89/162 no-stance examples versus original Qwen3-4B's 79/162. The 726 reserved rows remain unopened. This is UK argument stance presence, not U.S. article LEFT/RIGHT accuracy. Sanitized result: `results/argument_stance_instruct2507_dev_20261002.json`; response model paths alone are redacted, with generated choices/outcomes/metrics unchanged.
- V3 split exact candidate extraction, direction, and speaker tasks, each seeing full source. Across 38 reused synthetic cases it recovered only 4/27 exact spans and 2/21 author spans; 30 empty extractions caused severe recall loss. All 52 real calls and structural failures are retained. Its publisher-only tuple/list canonicalization repair is disclosed; inference was not repeated.
- V4 appended balanced extraction demonstrations while freezing downstream tasks. It recovered 25/27 exact spans but produced false highlights on 7/15 no-expected-span cases. V5 changed only direction demonstrations: old-case recovery fell to 23/27, with two formerly correct directions reversed. On a newly frozen paired 32-case targeted synthetic diagnostic, v4 recovered 15/19 and v5 16/19 exact spans; both returned 22 spans, with false highlights on 5/16 and 4/16 no-expected-span cases respectively. Both arms finished before transfer scoring. All 70 cases are now development data. These proportions are not general accuracy, and no-span conventions sometimes require human adjudication.
- Sanitized v4/v5 results and full independent AI audits are in `results/phrase_recall_v4_*` and `results/phrase_precision_v5_*`. Historical source plus hash manifest is isolated in `experiments/phrase_stages_20261002`; `tests/test_phrase_stage_snapshots.py` checks hashes, runs 66 historical tests in a subprocess, and independently replays all published suite metrics. Neither pipeline is wired to production.
- Verified remote checkpoint `b924c258295efb45a75cade64bcaec928a0b8f30` has successful hosted GitHub Actions run [37057771665](https://github.com/rahimcantcode/biasCheck/actions/runs/37057771665). Every step executed successfully: Python tests, frontend tests, npm audit, type checks and production build. This does not test real inference quality, browser interaction, or deployment capacity.
- A new all-population metric contract now distinguishes political-only selective accuracy from accepted-reference match across all inputs, with explicit UNCERTAIN acceptance and full five-row confusion matrix. No final all-population/uncertainty tolerance was invented after results; release remains blocked pending a frozen human-reviewed protocol.

Next controlled research changes model family/capability rather than continuing to tune demonstrations on the same 70 examples. The next transfer set must be frozen before candidate evaluation. Python package security remediation is proceeding in an isolated environment, with real-checkpoint compatibility required in addition to synthetic tests. No production changes or high-accuracy claim.

## 2026-10-02: Python security maintenance and runtime-bound calibration

The isolated upgraded stack passed the recorded full suite (561 tests plus 76 subtests before the final audit-cache-only fix), all 58 audit-helper regressions after that fix, and actual original-checkpoint/API compatibility checks. Torch 2.13.0+cpu, Transformers 5.10.4 and the pinned compatible framework/tokenizer dependencies replace the older tested stack; the old environment was not mutated and historical experiment provenance was not rewritten. Exact source token IDs/window boundaries/features match across tokenizer versions. Actual logit differences are at most 1.283228439e-6, with unchanged rounded scores and withheld-label decisions. Health and predict both returned 200. These are compatibility checks, not evidence of improved political accuracy.

Calibration now requires an exact versioned inference-runtime identity: library versions, window implementation, actual device/dtype/attention and batch size. Old reports without it cannot be fitted or silently accepted as equivalent. The default release remains unapproved. The added small random RoBERTa round-trip test catches a real incompatibility that mocked API tests missed during the upgrade.

The specifically authorized one-time live dependency-audit gate passed: 77 installed inventory entries, 76 directly audited and no reported advisories; the one explicit PyTorch +cpu skip remains visible, with a clean upstream base-version supplement. This is not binary-specific or zero-risk assurance. A writable temporary audit cache corrected an earlier fail-closed cache warning without suppressing diagnostics. The new gate's offline regressions run in ordinary CI; recurring outbound Python audit queries are **not** enabled or assumed authorized. Existing frontend audit scope remains unchanged.

Detailed observed versions, deduplicated original findings, exact source hashes, parity vectors, audit coverage and limitations: `results/python_security_20261002.json` and `../docs/python-security.md`. Optional NLI/training jobs, production inventory, real-browser interaction, penetration/load tests and OS/native-binary security assessment remain outside these completed checks. Nothing was deployed.

## 2026-10-04 UTC: BASIL real-news evaluation of unchanged UnBias-Plus API

Completed a frozen 60-sentence, 60-event sample with unchanged published BASIL release-2 human references: 20 lexical cases, 20 informational-only cases and 20 no-annotation controls. No machine labels were represented as human labels. No eligible candidate shared a normalized 13-word sequence with the released 5,000-row train_4 snapshot; training independence remains unproven. Original model, prompt, adapter and endpoint hashes were preserved.

All 60 real HTTP outcomes were saved: 52 complete, seven failed, one partial. Token precision 175/416 = 42.1%, recall 175/380 = 46.1%, F1 .440; 17/20 lexical cases had a human lexical word covered. One of 20 controls was highlighted, 15 returned no suggestions, and four failed. Exact boundaries matched 3/41 reference spans; lenient one-to-one overlap matched 28/41. Attribution remains unknown for all 51 accepted highlights. CPU median 15.78 seconds, first request 60.54 seconds. These short archival sentence results are not full-article, ideology or production accuracy.

Seven scoring tests passed; independent token/exact-boundary recounts and deterministic sample regeneration matched. No tuning, new human reviews, merge or deployment. Recommendation: reject the unchanged integration for production precise highlighting; retain only as a research candidate. Do not expand unchanged-model testing to seek a better score. Saved report, protocol, provenance, per-case text-free outputs, code and verification: `experiments/unbias_20261003/realnews_basil60/`. Raw source/HTTP snapshots remain in ignored local data. The prior GitHub upload block was not retried; this work is committed locally.

## 2026-10-04: targeted reliability fix and rejected lexical refiner

Instrumented reproductions of the eight failed/partial BASIL cases found seven
invalid native JSON completions (six escaping errors, one missing closing brace).
Opt-in native JSON grammar yielded six complete and two partial responses with
no hard failures on that selected set. Exact-source checks and disabled defaults
remain. This is targeted development evidence, not all-input reliability.

A second-stage minimal lexical highlight experiment retained all 60 archived
outcomes. After two explicitly archived incomplete contract/grammar attempts,
all 30 active calls in the corrected run succeeded, keeping all 51 original
highlights, narrowing none and dropping none. All token/span scores are unchanged;
median added latency was 17.86 seconds. Reject this refiner as no demonstrated
benefit. The original seven detector failures and one partial outcome remain.

The runtime oneOf conversion incompatibility was verified with pinned source and
a compiled converter probe, then fixed structurally without another semantic
prompt change. Original baseline and candidate hashes remain auditable. No new
human labels, training, deployment or high-accuracy claim. Complete evidence and
next human-reviewed data gate: `experiments/unbias_20261004/REPORT.md`.
