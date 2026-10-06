# Working experiment log (not a final report)

## 2026-10-06 18:04 UTC heartbeat: duplicate snapshot review guard

Added validation of every manifest text SHA-256 and rejection of duplicate text
fingerprints under distinct item IDs, case-insensitively. Previously only duplicate
manifest IDs were checked. This prevents exact snapshots being double-counted in
review coverage/agreement, including unreviewed manifest items. Near duplicates
and source/event independence remain outside this check. README updated.

All 32 annotation tests passed, including seven new cases for duplicate hashes
and malformed hashes on unreviewed items. Existing pilot verified: 100 items,
100 unique valid hashes. No real reviews or gold labels added. Report preserved
at research/results/manifest_guards_20261006.json and copied to outputs.

Public-site local Chrome/Playwright fallback recipe smoke returned unchanged
LEFT .997309, HTTP 200, exact input/UI, no page/request errors or mobile overflow.
Raw evidence outputs/live-browser-manifest-guards-20261006. Cloud browser
unavailable. Engineering-only run: no Astra ML task, training, deployment or
reserved-test access. Independent high accuracy remains unestablished.

## 2026-10-06 15:07 UTC heartbeat: resampling input guards

Hardened event-cluster resampling: reject a zero-column model matrix, missing or
blank/non-string event groups (including NaN), and boolean/noninteger draw counts.
Kept one-group inputs valid but tested their degenerate constant estimates. These
checks address malformed research inputs, not grouping validity or independence.

Eight resampling tests passed. Recomputed the recent four-model experiment and
verified exact equality of every saved 5000x4 accuracy value and 5000x42 draw count.
The new guards leave prior valid results unchanged. No retraining, re-selection or
new statistical conclusion. Verification hashes/report:
research/results/resampling_guards_20261006.json, also copied to outputs.

Public-site local Chrome/Playwright fallback recipe smoke unchanged: LEFT .997309,
HTTP 200, exact input/UI, no page/request errors or mobile overflow. Evidence:
outputs/live-browser-resampling-guards-20261006; cloud browser unavailable.
Engineering-only run, no Astra ML subtask, deployment or reserved-test access.
Independent high accuracy remains unestablished.

## 2026-10-06 13:13 UTC heartbeat: uncertainty for recent negative candidates

Reused existing event-string cluster bootstrap on frozen training OOF predictions
for baseline, ComplementNB, binary TF and min_df=1. Verified row IDs, labels/text
hashes, fold assignments and exact baseline predictions/scores across all source
reports. 115 rows, 42 groups; 5,000 uniform cluster draws with replacement,
seed 20261004, sample-weighted accuracy. No retraining or model selection.

All three observed deltas are -7/115 (-.06087). Conditional paired 95% percentile
intervals: ComplementNB [-.14458,.01205], binary TF [-.12389,0], rare terms
[-.125,0]. Each includes/touches zero. Baseline accuracy interval [.38888,.61538].
These are not significance tests or generalization guarantees: saved predictions,
overlapping training folds, imperfect event grouping, disputed noncommercial labels
and repeated development remain limitations. No positive improvement established;
do not upgrade the prior negative findings into formal inferiority claims.

Astra Medium critique saved. Four resampling tests passed; verified the 5000x42
count matrix sums to 42 per draw and all paired-difference arrays match. Preserved
normalized aligned source input, hashes, draw counts and full replicates under
research/checkpoints/recent-uncertainty-20261006; summary
research/results/recent_uncertainty_20261006.json (also outputs).

Public-site local Chrome/Playwright fallback recipe smoke unchanged, LEFT .997309,
HTTP 200, exact text/UI, no page/request errors or mobile overflow. Evidence:
outputs/live-browser-recent-uncertainty-20261006. Cloud browser unavailable.
Smoke is not candidate evaluation. No deployment or reserved-test access.

## 2026-10-06 12:12 UTC heartbeat: expose annotation attrition

Extended validated two-reviewer comparison with per-reviewer reviewed/skipped/
missing counts and IDs, reviewed fractions by item kind, overall paired fraction,
and paired counts by kind. Existing agreement and unapproved-gold behavior remain
unchanged. Coverage is calculated only after supplied annotations pass validation;
no inference about absent reviews or reviewer independence is made.

All 25 annotation tests passed, including three new cases: partial coverage with
skips, empty manifest, and no completed reviews. Synthetic demonstration explicitly
marked not human evidence: 1/100 paired, agreement 1.0, reviewer A reviewed/skipped/
missing 1/1/98, reviewer B 1/0/99. This prevents agreement being read without its
coverage denominator; it is not a classifier result or human annotation progress.
Preserved research/results/review_coverage_20261006.json, copied to outputs.

Public-site local Chrome/Playwright fallback recipe smoke unchanged: LEFT .997309,
HTTP 200, exact input/UI checks, no page/request errors or mobile overflow.
Raw evidence outputs/live-browser-review-coverage-20261006. Cloud browser
unavailable. Engineering-only run, no Astra ML task, training, real labels,
deployment or reserved-test use. Independent high accuracy remains unestablished.

## 2026-10-06 11:11 UTC heartbeat: rare-term vocabulary experiment

Fixed min_df=1 versus baseline 2, all other TF-IDF and balanced logistic regression
settings cloned. Five training-only fits on frozen event folds, no tuning or
validation/test access. Vocabulary grew from 1,972-2,103 to 11,261-11,908 features,
remaining below the 20,000 cap. Astra Medium reviewed dimensionality/normalization
confounds and repeated-development limitations.

Candidate 51/115 correct (.44348), macro-F1 .32762 versus baseline 58/115
(.50435), macro-F1 .44234. Recall LEFT 18/38, CENTER 0/26, RIGHT 33/51; strict
agreement slice 20/54 versus 25/54. Two errors corrected, nine introduced.
Reject as an improvement. This and preceding negative lexical ablations support
deprioritizing further small TF-IDF variants on these reused folds, not claiming
that all lexical models fail. Label/task quality and independent human evaluation
remain unresolved; corpus is research-only with noncommercial/disputed labels.

Five parameter/fold tests passed. Five saved hashes verified, all 115 prediction
vectors reproduced after reload at atol=1e-12. Full parameters, splits, probabilities
and checkpoints preserved under research/checkpoints/rare-terms-20261006; report
research/results/rare_terms_20261006.json (also outputs), method critique retained.

Public-site local Chrome/Playwright fallback smoke on recipe-space unchanged:
LEFT .997309, HTTP 200, exact input/UI, no page/request errors or mobile overflow.
Raw evidence outputs/live-browser-rare-terms-20261006. Cloud browser unavailable.
This tests unchanged production, not the candidate. No deployment or reserved-test
access; independent high accuracy remains unestablished.

## 2026-10-06 10:10 UTC heartbeat: remove shared context from negation probes

Derived four policy-only texts by removing the exact shared committee-meeting
second sentence from the frozen negation probes. No other edits; article mode,
one request each, compared with preserved earlier full-passage responses. Astra
Medium reviewed the follow-up and cautioned about prior-result selection and
between-run drift even with unchanged model fingerprints.

All policy-only labels remain LEFT. LEFT scores: public-health affirmative .998403,
negated .998078; corporate-tax affirmative .956399, negated .807743. Removing the
second sentence reduced the negated corporate-tax LEFT score by .189435. The
corporate pair's negation score difference is now .148656, compared with .001032
in full passages; public-health difference .000325 versus .000184. Thus the
earlier tiny score changes do not generalize across these input lengths/contexts.
No inference of correct labels, causal mechanism or general negation failure.

Exact submitted/returned text and unchanged model metadata verified. Tokens now
19/20/18/19 versus 39/40/38/39. All four HTTP 200, no page/request errors or mobile
overflow; 13 browser harness tests passed. Local Chrome/Playwright fallback, no
cloud browser available. Raw responses/screenshots:
outputs/live-browser-negation-context-20261006. Derived inputs/method under
research/data/negation-context-*, complete comparison report
research/results/negation_context_20261006.json (also outputs).
AI-authored diagnostic only; no tuning, deployment or reserved-test access.

## 2026-10-06 09:08 UTC heartbeat: frozen negation sensitivity probes

Submitted two AI-authored policy pairs in article mode, differing only by insertion
of "not" after "should". Both retain an identical neutral committee-meeting second
sentence. Inputs frozen before requests; one request each, no repeats/tuning.
Astra Medium reviewed the method. No human gold or opposite-label oracle: rejecting
one policy does not establish another ideology, and conjunction scope can be ambiguous.

All four returned LEFT. Public-health pair LEFT scores .998833 -> .998649;
corporate-tax/deregulation pair .998210 -> .997178. Maximum absolute class-score
changes .000184 and .001032; token counts 39->40 and 38->39. Exact texts, only-not
transformation and unchanged model fingerprints verified. These two local responses
show small score changes, not a general negation failure, correctness or accuracy.

All four HTTP 200 with exact input/UI checks; no page/request errors or mobile
overflow. Local Chrome/Playwright fallback, cloud browser unavailable. Thirteen
browser harness tests passed. Raw responses/screenshots:
outputs/live-browser-negation-20261006. Frozen inputs/method critique under
research/data/negation-*, complete report research/results/negation_probes_20261006.json
(also outputs), including score deltas, model/input/screenshot hashes and caveats.
No model changes, deployment, reserved-test access or high-accuracy claim.

## 2026-10-06 08:07 UTC heartbeat: shared UNCERTAIN slice reporting

General evaluation validated UNCERTAIN rows but omitted their label-assignment
rate; only policy evaluation added it separately. Moved this reporting into the
shared summarize function: uncertain_n, uncertain_false_label_rate and its marginal
Wilson interval. Removed duplicate policy-only calculation. Empty slices return
null rate/bounds, not apparent perfect handling. Explicit definition: fraction of
UNCERTAIN-reference rows given any political label, not proof of which class is
correct; UNCERTAIN is not CENTER. Political denominators remain unchanged.

Three new tests cover mixed slices, empty slice and all-labeled/all-abstained
cases. All 37 focused/new/existing tests passed. Synthetic three-row demonstration
records 1/2 UNCERTAIN rows labeled while political eligible_n stays 1. This is
contract scaffolding, not human evaluation or measured accuracy. Preserved in
research/results/uncertain_metrics_20261006.json, copied to outputs.

Public-site local Chrome/Playwright fallback repeated recipe-space: HTTP 200,
LEFT .997309, exact input/UI, no page/request errors or mobile overflow. Raw
responses/screenshots outputs/live-browser-uncertain-metrics-20261006. No cloud
browser available. This smoke does not validate reference uncertainty handling.
Engineering-only run: no Astra ML subtask, training, new gate, deployment or
reserved-test access. Independent high accuracy remains unestablished.

## 2026-10-06 07:07 UTC heartbeat: binary term-frequency ablation

Ran five fixed training-fold fits with binary=True in the cloned baseline TF-IDF
vectorizer, otherwise unchanged settings and balanced logistic regression. Existing
unigram runner now accepts an explicit ablation option, retaining unigram default.
Vocabulary and IDF arrays matched baseline exactly in every fold. Vectorizers fit
training folds only; validation and reserved test untouched. Astra Medium reviewed
the method and noted changed document normalization/effective regularization,
preventing an isolated causal claim about repeated terms.

Binary TF: 51/115 correct (.44348), macro-F1 .38069 versus baseline 58/115
(.50435), macro-F1 .44234. Recall LEFT 18/38, CENTER 3/26, RIGHT 30/51 versus
22/38, 4/26, 32/51. Strict-agreement slice 20/54 versus 25/54. Two baseline errors
corrected, nine successes regressed. Reject as an improvement on this development
comparison; no tuning or deployment. Corpus remains research-only/noncommercial,
with disputed labels and repeatedly used folds, not independent accuracy evidence.

Five tests passed for ablation parameter isolation/default behavior and fold guards.
Reloaded five models, verified hashes and reproduced all 115 probability vectors
at absolute tolerance 1e-12. Retained full scores, split IDs, parameters, runtime,
protocol and model hashes under research/checkpoints/binary-tf-20261006. Report:
research/results/binary_tf_20261006.json (also outputs). Method critique retained.

Public-site local Chrome/Playwright fallback repeated the two selected training
errors from the event audit: LEFT .996359 and LEFT .999042, unchanged. Both HTTP
200 with exact input/UI checks; no page/request errors or mobile overflow. Evidence:
outputs/live-browser-binary-tf-20261006. No cloud browser available. These are
production smoke checks, not candidate evaluation or representative accuracy.

## 2026-10-06 06:06 UTC heartbeat: marginal uncertainty reporting

Added 95% Wilson intervals with exact numerators/denominators to evaluation
summaries for raw accuracy, political coverage, selective accuracy, nonpolitical
false-label rate, and raw/delivered per-class recall. Empty denominators produce
null bounds; abstentions remain failures for delivered recall. Formula reference:
https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm (NIST).

These are explicitly marginal IID binomial diagnostics, not cluster-adjusted or
simultaneous bounds. They do not provide independent evidence on reused development
data, establish human provenance, or address macro-F1 uncertainty. Point-estimate
gates and release_approved=False behavior unchanged. Astra Medium method review
retained. Four new unit tests cover known values, boundary/invalid counts, missing
classes and abstention denominators. All 34 focused/new/existing metric tests passed.

Synthetic contract demonstration: 90/100 correct yields interval .82563-.94477,
illustrating why a 90% point estimate is not a 90% lower bound. This is generated
test data, not a measured model result or human evaluation. Saved as
research/results/interval_demo_20261006.json and copied to outputs.

Public-site local Chrome/Playwright fallback repeated frozen recipe-space smoke:
LEFT .997309, HTTP 200, exact input/UI checks, no page/request errors or mobile
overflow. Raw evidence: outputs/live-browser-intervals-20261006. No cloud browser
available. This smoke tests unchanged production, not interval validity or accuracy.
No model training, deployment, reserved-test access or high-accuracy claim.

## 2026-10-06 05:05 UTC heartbeat: event-level error concentration

Audited frozen baseline OOF predictions against training rows only: 115 examples,
42 event strings, 57 errors. Sorted events by descending error count, lexical
tie-break fixed before analysis. The top five contain 24/57 errors (42.1%) and
36/115 rows (31.3%). Errors occur in 29 events. CENTER has 22 errors across 17 of
18 events containing CENTER examples, so the deficit is not confined to one event.
Largest error-count groups: Las Vegas response (6/13), Scaramucci leaks (5/6),
election-result reactions (5/6), Indiana law (4/5), contractor minimum wage (4/6).
These shorthand descriptions are not replacements for the preserved event strings.

This is descriptive post-model error ranking, not a prevalence estimate, causal
claim or evidence that labels are wrong. Larger events have more error opportunities;
event strings may not be independent families. Reused development predictions and
disputed noncommercial corpus labels cannot establish independent accuracy.
Astra Medium method critique retained. No tuning, relabeling or reserved-test use.

Added research/scripts/event_error_audit.py with checks for complete unique IDs,
reference/hash agreement and single held-out fold per event. Three unit tests
passed, including zero-error share, mismatched rows and cross-fold event rejection.
Full event counts, row IDs, source model hashes and provenance preserved in
research/results/event_errors_20261006.json and copied to outputs.

Public browser checks selected, post hoc, the first ID-sorted CENTER baseline
error in each of the top two events: 1b8a9395-94b4-4183-9b16-f12bd692aadd and
259b95ba-221b-42c2-b490-a318b5c75b00. Production returned LEFT .996359 and
LEFT .999042. Both HTTP 200, exact inputs and rendered text; no browser/request
errors or mobile overflow. Local Chrome/Playwright fallback, not cloud browser.
Raw outputs/screenshots: outputs/live-browser-event-errors-20261006. These are
selected corpus disagreements, not a representative production error rate.
No deployment or model replacement; human review remains necessary.

## 2026-10-06 04:04 UTC heartbeat: validate calibration requirements

Reproduced an input-contract defect on the synthetic calibration fixture: target=-1,
target=True, min_coverage=-1 and min_coverage=False all returned candidate policies.
They remained release_approved=False; no deployment gate was bypassed. Nevertheless,
invalid requirements should not be accepted as calibration objectives.

Added fail-fast validation for both parameters: finite nonboolean real numbers in
(0,1]. Candidate policies now retain requested_accuracy and requested_min_coverage
for auditability. Defaults and release protection unchanged. Added tests covering
24 invalid parameter cases and three valid pairs (including numeric upper bound
and NumPy scalar inputs). Optimizer must not run for invalid values. All 23 tests
across calibration optimizer, numerical predictions and unique-example guards
passed. The fixture's human-reviewed flag is synthetic test scaffolding, not human
annotation evidence. No generated fixture was promoted into research gold.

Public-site local Chrome/Playwright smoke repeated the frozen recipe-space example:
HTTP 200, exact returned text, LEFT .997309, no page/request errors or mobile
overflow. Raw evidence outputs/live-browser-calibration-requirements-20261006;
report research/results/calibration_requirements_20261006.json (also outputs).
Cloud browser unavailable; used established local fallback. This is unchanged
production, not a test of candidate calibration or independent accuracy.

Engineering-only run: no ML training/Astra subtask, production change, or reserved
test access. Numerical validation strengthens the experiment contract but does not
establish accuracy, annotation provenance or release readiness.

## 2026-10-06 03:03 UTC heartbeat: fixed Complement Naive Bayes comparison

Tested ComplementNB(alpha=1, norm=False, fit_prior=True; remaining defaults
recorded) against balanced logistic regression on the same 115 training rows and
five frozen event-group folds. Reused each training-only TF-IDF vectorizer exactly;
five classifier fits, no tuning or validation/test access. Astra Medium reviewed
the protocol and highlighted confounding changes in estimator/class weighting,
repeated development use and disputed labels. This is research-only under the
corpus noncommercial license, not evidence of independent high accuracy.

Candidate: 51/115 correct (.44348), macro-F1 .34294, versus baseline 58/115
(.50435), macro-F1 .44234. Recall LEFT 16/38, CENTER 1/26, RIGHT 34/51, versus
22/38, 4/26, 32/51. Strict-agreement slice 19/54 versus 25/54. Three baseline
errors corrected, ten baseline successes regressed. Reject this fixed candidate
as an improvement; no hyperparameter search in this run.

Preserved split IDs, all OOF class scores, model hashes, runtime, parameters and
method critique. Reloaded all five saved candidates and reproduced all 115 score
vectors at absolute tolerance 1e-12; hashes verified. Three existing fold-guard
tests passed. Script: research/scripts/complement_nb_cv.py. Checkpoints/protocol:
research/checkpoints/complement-nb-20261006. Full report:
research/results/complement_nb_20261006.json, also copied to outputs.

Public-site browser smoke at 03:04:39-03:04:44 UTC used local Chrome/Playwright
fallback, not a cloud browser. Frozen recipe-space diagnostic still returned
LEFT .997309; exact input and UI checks passed, no browser/request errors or
mobile overflow. Raw responses/screenshots: outputs/live-browser-complement-nb-20261006.
This checks unchanged production, not the candidate or representative accuracy.
No deployment; reserved test untouched.

## 2026-10-06 02:01 UTC heartbeat: fail closed on browser audit response errors

Fixed an evidence-collection gap: valid-JSON HTTP errors previously could finish
the browser audit without a nonzero exit. Non-2xx prediction responses now fail
after preserving the status, raw body and parsed JSON. Added exact resolved-text
verification for direct-text fixtures. URL fixtures may supply a frozen
expected_resolved_text; without one, input_verification is explicitly
not_checked_url rather than falsely claiming extracted-text identity.

Expanded mocked regression coverage from seven to thirteen scenarios: JSON 503,
JSON 422, changed direct text, URL with no reference, matching URL reference and
mismatching URL reference. All thirteen passed, including saved failure evidence
and browser closure. No production HTTP failures were deliberately induced.

Ran the stricter harness against the public site using the three frozen sentence
formatting probes. All HTTP 200, exact inputs, correct modes and rendered text;
full result objects exactly match the earlier saved audit. Known RIGHT/RIGHT/LEFT
pattern persists. No page/request errors or mobile horizontal overflow. Local
Chrome/Playwright fallback because cloud browser unavailable and agent-browser CLI
absent. Preserved raw responses/screenshots under
outputs/live-browser-audit-contract-20261006 and hashes/results in
research/results/browser_audit_contract_20261006.json (also copied to outputs).

Engineering-only improvement: no new accuracy evidence, training, Astra ML task,
normalization or deployment. Reserved test untouched. Repeated synthetic examples
verify the harness, not independent model quality. URL extraction requires a
separate frozen reference to meet the new input-identity check.

## 2026-10-06 01:01 UTC heartbeat: broader frozen formatting panel

Created four new AI-authored two-sentence examples and fixed the inputs/comparisons
before browser requests: redistribution, deregulation, recipe, attributed opposing
arguments. These names describe construction intent, not human annotations. Each
was tested in sentence mode with blank-line, newline and space separators, in that
order, one request each. No repeat or input replacement after results. The panel
is an exploratory follow-up to a selected earlier flip, not independent validation.
GPT-6 Astra Medium provided a preserved pre-run method critique emphasizing these
selection limits and the inability of single requests to exclude backend drift.

| Example | Overall labels (blank-line/newline/space) | Largest class-score change |
| --- | --- | ---: |
| redistribution | LEFT / LEFT / LEFT | .085027 |
| deregulation | RIGHT / RIGHT / RIGHT | .147889 |
| recipe | LEFT / LEFT / LEFT | .002693 |
| attributed-disagreement | LEFT / LEFT / LEFT | .000839 |

Zero of four examples flipped labels. All eight individual sentence texts and
score vectors were invariant across their three versions. Full-text token counts
decreased by one per separator change (44/43/42, 41/40/39, 50/49/48, 50/49/48).
The deregulation RIGHT score ranged from .849429 to .997318 despite stable label.
The recipe received LEFT scores .994616/.996541/.997309; stability is not evidence
of correct nonpolitical handling. No accuracy, population flip-rate or causal claim.

Actual public-site run 01:02:10-01:02:31 UTC, local Chrome 154.0.8037.98 via
Playwright fallback (no cloud browser discovered; agent-browser CLI absent).
All 12 HTTP 200, exact returned texts, valid offsets, same model metadata,
completed mode/UI checks and screenshots. No page/request errors or mobile
horizontal overflow. Recipe-space screenshot visually inspected: recipe is
displayed with LEFT overall and colored passages. Seven mocked persistence/mode
tests passed. No deployment, normalization or reserved-test access.

Frozen spec/inputs/method: research/data/formatting-panel-*-20261006.* and
research/data/formatting-panel-20261006.json. Full scores, hashes, per-example
comparisons: research/results/formatting_panel_20261006.json, copied to outputs.
Raw browser evidence: outputs/live-browser-formatting-panel-20261006. The negative
flip result limits generalization of the previous finding; task-matched human
evaluation remains necessary before any release claim.

## 2026-10-06 00:00 UTC heartbeat: sentence scores invariant under separator changes

Followed the formatting diagnostic with three frozen sentence-mode inputs derived
from the prior article inputs. Actual public browser run: 00:06:23-00:06:34 UTC.
Used local Chrome 154.0.8037.98 through Playwright; cloud browser unavailable.
All three returned HTTP 200, two passages, correct requested mode, exact input
text, valid offsets and unchanged model metadata. No browser/request errors or
mobile horizontal overflow. Seven mocked browser persistence/mode tests passed.

For blank-line, newline and space separators respectively, overall labels remain
RIGHT (.963345), RIGHT (.964275), LEFT (.961676); all overall fields exactly match
the preceding article-mode outputs. Every first sentence has the same LEFT score
.997521, every second sentence the same RIGHT score .989956, with identical full
score vectors and 20/24 token counts. Second-sentence offsets correctly shift from
132..280 to 131..279. Full-text token counts are 46, 45 and 44.

Local backend/main.py:64 computes overall directly from full text; line 67
separately predicts each sentence. This supports investigating the full-text path,
not a claim that the overall label aggregates sentence scores. The Astra Medium
method critique proposed passage-to-overall mapping as a possibility, but that
mechanism is not supported by this local code. Server source identity was not
verified; model fingerprints alone do not prove it. No causal mechanism or correct
label established. This is one AI-authored, previously selected diagnostic, not
human gold, an independent sample, or an accuracy estimate.

Preserved inputs and method critique under research/data/formatting-sentence-*,
full diagnostic report research/results/formatting_sentence_20261006.json, and raw
responses/screenshots in outputs/live-browser-formatting-sentence-20261006. Report
contains hashes of inputs, prior/current raw audits, screenshots and local code.
No normalization, model replacement or deployment; reserved test untouched.
Next useful step: broader preregistered formatting probes before considering any
normalization, preserving meaningful paragraph boundaries and human evaluation.

## 2026-10-05 23:00 UTC heartbeat: reproduced whitespace-driven label flip

Derived three article-mode inputs from the frozen two-policy mode probe. Changed
only its sole paragraph separator: blank line, single newline, or space. Verified
identical word sequence before submission; all returned resolved text matched its
submitted variant. Inputs frozen in research/data/formatting-probes-20261005.json
with provenance/source hash; AI-authored diagnostics, not human gold.

| Separator | Label | LEFT score | RIGHT score | Tokens |
| --- | --- | ---: | ---: | ---: |
| Blank line | RIGHT | .027243 | .963345 | 46 |
| Single newline | RIGHT | .025680 | .964275 | 45 |
| Space | LEFT | .961676 | .026161 | 44 |

First public-browser run 23:02:00-23:02:34 UTC. After observing the flip, repeated
the blank-line and space variants in a fresh browser, 23:02:54-23:03:09 UTC. Both
returned EXACT same score vectors and full model metadata as the first run.
Five total HTTP 200 submissions, article mode honored, unchanged model across
all cases, complete captures; no page errors/failed requests or mobile overflow.

This demonstrates reproducible formatting sensitivity for one selected passage,
not a population error rate, proof of wrongness, or evidence for a particular
correct label. The repeat was triggered by the finding, not an independent
preregistered evaluation. No whitespace-normalization fix deployed: that could
simply select a different wrong label and requires broader evaluation. No training,
dataset split access or release approval. Astra Medium reviewed the initial
single-run method (before the repeat decision); research/data/formatting-method-20261005.txt.

Seven existing harness regression scenarios passed. Verified input/resolved-text
identity, word-sequence identity, shared model metadata and exact repeat scores.
Raw responses/screenshots outputs/live-browser-formatting-20261005 and
outputs/live-browser-formatting-repeat-20261005. Repeat input retained in
research/checkpoints/formatting-20261005/repeat.json. Sanitized report with input,
text and screenshot hashes plus all raw score vectors:
research/results/formatting_probes_20261005.json, also copied to outputs.
Local Chrome/Playwright fallback; agent-browser unavailable, no cloud browser
tool. Production unchanged; independent human accuracy remains unproven.

## 2026-10-05 21:58 UTC heartbeat: same-text cross-mode diagnostic

Extended live browser harness with an optional per-input mode (default article),
explicit UI mode selection, requested_mode evidence, and a failure if a successful
response returns a different mode. Raw evidence is saved before that check.
Seven mock-browser scenarios passed, including paragraph selection and a
sentence-request/article-response mismatch. Existing failure-capture tests retained.

Froze one AI-authored two-paragraph text across Article, Sentence and Paragraph
inputs. First paragraph advocates wealth taxes/universal healthcare; second
advocates corporate-tax cuts/deregulation. No human gold labels or accuracy metric.
Public browser 22:00:14-22:00:23 UTC returned HTTP 200 for all three with identical
model metadata/text, requested modes honored and expected 1/2/2 segments. Verified
all segment offsets reproduce source text; visible result headers matched modes.

Overall RIGHT .963345 in all modes. Sentence and paragraph outputs both showed
first passage LEFT .997521 and second RIGHT .989956. Thus a full-text single label
can hide conflicting passage predictions. This is an observability finding on
one synthetic text, not proof that the overall label is wrong, calibrated, fair,
or representative; aggregation/context and units of analysis differ. No mixed
override or deployment introduced. Astra Medium no-tools critique saved in
research/data/mode-probe-method-20261005.txt.

Inputs research/data/mode-probes-20261005.json; report
research/results/mode_probes_20261005.json retains complete passage scores/offsets,
model/input/screenshot hashes and mode evidence, also copied to outputs. Raw
responses/screenshots outputs/live-browser-mode-probes-20261005. No page errors,
failed requests or mobile overflow. Local Chrome/Playwright fallback; agent-browser
unavailable, no cloud browser tool. No training, corpus split access, release
approval or high-accuracy claim; production unchanged.

## 2026-10-05 20:42 UTC heartbeat: calibration reference-class coverage

Reproduced a calibration gap with 120 synthetic rows: replacing an entire class
with another correctly predicted class still allowed a candidate. Added a check
that political validation rows include LEFT, CENTER and RIGHT before optimization.
Candidate policies now retain validation_class_counts. Existing total minimum,
optimizer bounds, threshold search and release_approved=False remain unchanged.

The missing-class regression failed before the patch; 29 selected tests passed
afterward (optimizer, numeric reports, provenance and unique examples). New tests
exercise each missing class and verify the saved 40/40/40 synthetic class counts.
No human annotations were generated. Presence is only a necessary condition, not
sufficient sample size, representative coverage or proof of each-class accuracy;
independent evaluation and uncertainty analysis remain necessary.

Engineering-only run: no real calibration report or corpus split accessed, no
model training, no Astra ML review requested, no deployment or accuracy claim.

Actual browser audit 21:20:06-21:20:29 UTC, later than trigger: two frozen cases
HTTP 200, unchanged LEFT .993377 / RIGHT .997867, complete captures, no page
errors/failed requests or mobile overflow. Local Chrome/Playwright fallback;
agent-browser unavailable, no cloud browser tool. Raw responses/screenshots:
outputs/live-browser-calibration-classes-20261005. Sanitized fingerprints/hashes:
research/results/calibration_classes_browser_20261005.json. Repeated production
smoke only; not evidence of improved accuracy.

## 2026-10-05 19:33 UTC heartbeat: per-category reviewer agreement

Extended annotation/compare_reviews.py without changing existing raw agreement,
kappa, skipped/missing handling or gold_labels_approved=False. Added fixed-order
confusion tables (rows reviewer A, columns B), per-category marginal counts and
matching counts, plus symmetric positive agreement 2*matches/(A_count+B_count).
Jointly absent categories have null, not perfect or zero agreement. Applies to
five leaning labels, three relevance labels, and existing source-kind slices.
Neither reviewer is treated as ground truth; this metric is not accuracy.

22 annotation tests passed, including four new tests covering a minority-category
disagreement hidden by high overall agreement, symmetry under swapping reviewers,
empty pairs, and undefined kappa for a single unanimously used category. Saved
research/results/reviewer_agreement_synthetic_20261005.json explicitly as synthetic,
human_reviewed=False, gold_labels_approved=False. It demonstrates 90% aggregate
agreement with zero CENTER positive agreement; it is not a human review result.
No actual annotations manufactured or approved. Astra Medium no-tools critique:
research/data/reviewer-agreement-method-20261005.txt. Missing/skipped selection can
still distort paired agreement and reviewer independence requires human review.

No training or dataset split access, no deployment, no model-accuracy claim.

Public-browser smoke actually ran 20:14:32-20:14:55 UTC, later than trigger: two
frozen cases HTTP 200, unchanged LEFT .993377 / RIGHT .997867, complete captures,
no page errors/failed requests or mobile overflow. Local Chrome/Playwright
fallback; agent-browser unavailable, no cloud browser tool. Raw evidence in
outputs/live-browser-reviewer-agreement-20261005; sanitized model fingerprints
and screenshot hashes research/results/reviewer_agreement_browser_20261005.json.
This smoke does not validate the annotation metric or establish accuracy.

## 2026-10-05 18:17 UTC heartbeat: fixed unigram-only ablation

Five fixed fits on the same 115-row training-only event-string folds. Cloned each
baseline vectorizer, changed only ngram_range from (1,2) to (1,1), and refitted
on fold-training text only. Cloned all balanced logistic classifier parameters
unchanged (C=1, random_state=20261001). No validation/test reads or search.
Convergence warnings treated as errors; none raised, 8-14 iterations.

Unigram-only 56/115=.48696 accuracy, macro-F1 .43995, versus baseline 58/115=.50435
and .44234. Recalls LEFT 22/38 unchanged; CENTER 5/26 versus 4/26; RIGHT 29/51
versus 32/51. Unanimous held-out subset 26/54 versus 25/54. Two corrected and four
regressed examples. Reject candidate: no aggregate improvement or high accuracy.

Candidate vocabulary sizes 1110-1178 versus baseline 1972-2103. Neither approaches
the 20000 feature cap, so cap competition is not binding here; TF-IDF row
normalization still changes weights. This compares whole pipelines, not an
isolated causal contribution of bigram information. Low held-out bigram coverage
alone did not predict an improvement from removing bigrams. Small, repeatedly
examined development folds and disputed noncommercial corpus labels remain limits.

research/scripts/unigram_cv.py; checkpoints/unigram-cv-20261005 holds five models,
protocol and results. research/results/unigram_cv_20261005.json retains data/fold
hashes, train/held IDs, parameters, vocab sizes, model hashes, 230 predictions/
probabilities and paired error changes; copied to outputs. Verified all five
model hashes, classifier parameter equality, sole vectorizer parameter difference,
unigram-only vocabularies, OOF coverage and probability argmax labels. Six existing
coverage/fold tests passed. Astra Medium critique saved in
research/data/unigram-method-20261005.txt.

Public-browser smoke 18:18:51-18:18:57 UTC: two frozen examples HTTP 200 with
unchanged LEFT .993377 / RIGHT .997867. Complete captures, no page errors/failed
requests or mobile overflow. Local Chrome/Playwright fallback; agent-browser
unavailable, no cloud browser tool. Repeated smoke only, not candidate validation.
Raw evidence outputs/live-browser-unigram-20261005; sanitized hashes and model
fingerprints research/results/unigram_browser_20261005.json. Production unchanged;
no deployment or independent high-accuracy claim.

## 2026-10-05 16:08 UTC heartbeat: reject failed calibration optimization

Reproduced an offline calibration bug with a synthetic report and mocked optimizer:
success=False with a finite x=0 still produced a candidate policy. Added checks
requiring optimizer success, finite objective/solution, and a solution within the
existing log-temperature bounds [-3,3]. Also reject invalid calibrated score
shape, nonfinite/out-of-range probabilities, and non-unit row sums before threshold
search. Existing optimizer bounds and threshold-search settings are unchanged.

Regression failed before the patch (expected ValueError not raised), then 27
selected tests passed: four new optimizer tests plus numeric, provenance and
unique-example checks. New tests cover failed optimization, nonfinite/out-of-bound
results, invalid softmax output and a real successful synthetic fit that still
produces release_approved=False. Fixtures are synthetic, not human evidence.
No existing corpus reports or reserved test accessed; no new training, calibration
of a real candidate, deployment or approval. Engineering-only work, no Astra ML
review requested. This prevents invalid experiment artifacts, not an accuracy gain.

Actual live-browser smoke 18:15:10-18:15:38 UTC, later than trigger: two frozen
examples HTTP 200 with unchanged LEFT .993377 / RIGHT .997867. Complete captures,
no page errors/failed requests or mobile overflow. Local Chrome/Playwright fallback
(agent-browser unavailable; no cloud browser tool). Raw evidence:
outputs/live-browser-optimizer-guard-20261005; sanitized model/screenshot hashes:
research/results/optimizer_guard_browser_20261005.json. Repeated smoke only;
independent human evaluation and high accuracy still unproven.

## 2026-10-05 15:00 UTC heartbeat: frozen vocabulary coverage audit

Audited all 115 training-only OOF rows using their verified saved fold vectorizers
and classifiers. Counted analyzer-emitted word unigram/bigram occurrences present
in each training vocabulary, plus distinct feature counts and sparse nnz. No
refitting, vocabulary changes, threshold selection, validation/test access or
deployment. Every prediction and probability vector exactly reproduced the prior
full-supervision baseline; retained distinct feature counts equaled sparse nnz.

Mean per-document retained occurrence fractions (not raw-word coverage):

| Slice | n | All features | Unigrams | Bigrams |
| --- | ---: | ---: | ---: | ---: |
| All | 115 | .4181 | .6828 | .1509 |
| LEFT reference | 38 | .4135 | .6854 | .1394 |
| CENTER reference | 26 | .4004 | .6598 | .1385 |
| RIGHT reference | 51 | .4305 | .6927 | .1658 |
| Correct vs corpus | 58 | .4335 | .6982 | .1662 |
| Incorrect vs corpus | 57 | .4025 | .6671 | .1353 |

Bigrams have low vocabulary survival; incorrect predictions have modestly lower
coverage. CENTER is not uniquely devoid of features. These descriptive differences
do not identify min_df as the cause of errors: unseen wording, tokenization,
feature caps, topics, length and disputed labels also matter. No evidence here
that changing vocabulary will improve independent accuracy. Empty analyzer outputs
are represented as null fractions, not zero; none occurred in these 115 rows.

New feature_coverage_audit.py and three count/empty/unknown-feature tests; six tests
passed including existing fold/feature checks. Verified all 115 reproduced
probability vectors and feature count identities. Artifact
research/results/feature_coverage_20261005.json retains data/fold/model hashes,
train/held IDs, settings, per-row counts, raw predictions/probabilities and summaries;
copied to outputs. Astra Medium no-tools critique saved as
research/data/feature-coverage-method-20261005.txt.

Public-browser smoke 15:03:06-15:03:37 UTC: unchanged two frozen predictions,
HTTP 200, complete UI/captures, no page errors/failed requests or mobile overflow.
Local Chrome/Playwright fallback; agent-browser unavailable, no cloud browser tool.
Not candidate accuracy evidence. Raw responses/screenshots:
outputs/live-browser-feature-coverage-20261005. Sanitized model/screenshot
fingerprints: research/results/feature_coverage_browser_20261005.json. Production
unchanged; corpus research-only/noncommercial and independent human evaluation
still required before any high-accuracy claim.

## 2026-10-05 12:24 UTC heartbeat: preserve non-JSON HTTP evidence

Hardened live_browser_audit.cjs: persist case ID/HTTP status before reading the
body, then persist response text before JSON decoding. Track body_read and
json_decode separately from UI/capture status. A failed body read now retains
status; malformed JSON (e.g. a gateway HTML response) retains status and body
instead of discarding the case. Existing parsed result remains compatible for
successful runs. Failed runs remain nonzero with explicit incomplete stages.

Five mock-browser tests passed: success, rendering timeout, screenshot timeout,
non-JSON 502 body, and body-read failure. Browser cleanup and earlier response
writes verified. Real public smoke 12:25:25-12:25:31 UTC: both frozen examples
HTTP 200 with complete body/decode/UI/capture states. Verified saved response text
decodes to the stored result. Predictions unchanged (LEFT .993377 / RIGHT .997867),
no page errors/failed requests or mobile overflow. No actual production HTTP
failure was observed or induced; failure coverage is mocked.

Raw response text, parsed outputs and screenshots preserved in
outputs/live-browser-http-evidence-20261005. Sanitized report with response-text/
screenshot hashes and model fingerprints: research/results/http_evidence_browser_20261005.json.
Local Chrome/Playwright fallback; agent-browser unavailable and no cloud browser
tool found. Repeated probes are harness smoke only, not independent accuracy.
Engineering-only run: no ML training, Astra review, dataset split access, policy
change or deployment. High accuracy remains unproven; human evaluation outstanding.

## 2026-10-05 10:55 UTC heartbeat: matched supervision controls

Completed 25 fits: five seeds 20261005-20261009 x five frozen development folds.
Sampled without replacement within each full training class to exactly match the
prior unanimous-only supervised class counts (40-46 examples per fold). RNG
SeedSequence([seed,fold]); retained original training order after selection.
Same verified fold-local vectorizers and cloned balanced logistic parameters as
the prior experiment. All fold-training text remains in representation fitting;
only supervised selections change. Convergence warnings treated as errors; none
raised. No validation, reserved test, relabeling, search or deployment.

| Seed | Correct/115 | Macro-F1 | Unanimous correct/54 | Disputed correct/61 | CENTER recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20261005 | 39 | .31905 | 28 | 11 | 22/26 |
| 20261006 | 32 | .25103 | 24 | 8 | 18/26 |
| 20261007 | 27 | .19324 | 23 | 4 | 20/26 |
| 20261008 | 41 | .33999 | 26 | 15 | 19/26 |
| 20261009 | 34 | .28566 | 24 | 10 | 20/26 |

Matched-control accuracy 23.5-35.7%, below unanimous-only 44/115=38.3% and full
supervision 58/115=50.4%. Controls predict CENTER 74-89/115, versus 78 unanimous-
only and 10 full-supervision. Thus excessive CENTER predictions also occur with
random supervision at matched size/class composition; they are not unique to
unanimous-only selection. Unanimous selection beats these five random selections,
but this is descriptive, not a p-value or causal label-noise estimate. Remaining
topic, difficulty, annotator and selection confounds persist; seeds share rows and
folds overlap. All candidates inadequate; corpus remains research-only/noncommercial.

research/scripts/matched_supervision.py and checkpoints/matched-supervision-20261005
retain protocol, 25 models, selections and results. Committed report
research/results/matched_supervision_20261005.json links source/data/fold hashes,
all train/held/supervised IDs, model hashes/parameters, unanimous counts and 575
raw predictions/probabilities. Copied to outputs. Verified 25 model hashes,
without-replacement training-only selection and exact class counts, and 575 argmax
labels. Nine tests passed (matched selection, unanimous selection and fold/feature
checks). Astra Medium no-tools critique: research/data/matched-supervision-method-20261005.txt.

Public-browser smoke 10:56:56-10:57:02 UTC: two frozen examples HTTP 200, unchanged
LEFT .993377 / RIGHT .997867, complete UI/captures, no errors/failed requests or
mobile overflow. Local Chrome/Playwright fallback; agent-browser unavailable,
no cloud browser tool found. Repeated smoke is not candidate evaluation. Evidence:
outputs/live-browser-matched-supervision-20261005 and sanitized fingerprints/
screenshot hashes research/results/matched_supervision_browser_20261005.json.
No release approval or high-accuracy claim; independent human evaluation absent.

## 2026-10-05 06:58 UTC heartbeat: withhold disputed supervision

Five fixed fits, one per frozen training-only event-string fold. Cloned each
saved balanced logistic estimator (C=1, unchanged parameters), then fit only on
unanimous-label fold-training rows: supervised counts 42/40/44/46/44, versus 92
full-training rows each. Kept frozen vectorizers fitted on ALL fold-training text,
including excluded-label texts; no held-out text used for fitting. This tests
withholding disputed supervision, not removing those texts from representation.
Convergence warnings treated as errors; none raised, 7-10 iterations.

| OOF metric on unchanged 115 rows | Full supervision | Unanimous-only supervision |
| --- | ---: | ---: |
| Correct | 58 | 44 |
| Accuracy | .50435 | .38261 |
| Macro-F1 | .44234 | .37638 |
| LEFT recall | 22/38 | 13/38 |
| CENTER recall | 4/26 | 22/26 |
| RIGHT recall | 32/51 | 9/51 |
| Unanimous held-out subset correct | 25/54 | 31/54 |
| Disputed held-out subset correct | 33/61 | 13/61 |

Candidate predicts CENTER 78/115 with precision 22/78=.28205. Nineteen corrected
versus 33 regressed examples. Reject candidate: improved CENTER recall and the
unanimous slice come with substantial degradation elsewhere. Disputed-slice
macro-F1 uses fixed three-class averaging; that slice contains zero CENTER
references, so its reported zero recall is not an estimate for CENTER examples.
Neither unanimous agreement nor disputed aggregation is unquestioned human truth.

No causal attribution to noise: exclusion also changes training size, topic/class
mix, balanced class weights, and effective regularization at fixed C. Repeated
development folds and related event families limit inference. No validation or
reserved-test access, relabeling, hyperparameter search or deployment. Corpus and
candidate remain research-only/noncommercial; release approval false.

research/scripts/strict_label_cv.py; checkpoints/strict-label-cv-20261005 contains
five models, protocol and report. research/results/strict_label_cv_20261005.json
preserves source/fold hashes, train/held/supervised/excluded IDs, counts, parameters,
model hashes, 230 OOF probability vectors, confusion matrices and paired changes;
also copied to outputs. Verified five candidate hashes, all exclusion/partition
conditions, unique complete OOF coverage and probability argmax labels. Six tests
passed (three new supervision-selection tests plus three existing split/feature
tests). Astra Medium no-tools critique: research/data/strict-fit-method-20261005.txt.

Actual public browser audit occurred 10:52:15-10:52:33 UTC, later than trigger.
Local Chrome/Playwright fallback (agent-browser unavailable; no cloud browser
tool found). Two frozen probes returned HTTP 200 and unchanged production LEFT
.993377 / RIGHT .997867, with complete UI/capture states, no page errors/failed
requests or mobile overflow. Repeated smoke only, not candidate evaluation.
Raw responses/screenshots outputs/live-browser-strict-fit-20261005; sanitized
model fingerprints and screenshot hashes research/results/strict_fit_browser_20261005.json.
Independent human evaluation/high accuracy remain outstanding.

## 2026-10-05 05:51 UTC heartbeat: order diagnostics and durable browser responses

Fixed live_browser_audit.cjs to save each parsed prediction response before UI
verification or screenshots, with separate pending/complete capture states. On
failure it records the active case's error before attempting a failure screenshot.
Previously a screenshot timeout could discard an already received prediction.
Three mock-browser tests passed: successful capture, render timeout and screenshot
timeout. Tests confirm the response is already saved, incomplete captures are not
reported complete, failed runs exit nonzero, and browser cleanup happens. This is
research-harness reliability work, not a production change or model improvement.

Frozen two new AI-authored order pairs before browser execution. Attributed
pro-tax and anti-tax quotations swap order with their speaker IDs intact; two
mixed-policy sentences swap with the final framing sentence unchanged. Verified
identical word multisets within each pair. No human gold or accuracy calculation.

| Probe | Production label | LEFT class score |
| --- | --- | ---: |
| Quotes: tax increase first | LEFT | .998645 |
| Quotes: tax cut first | LEFT | .998841 |
| Mixed: health/union first | LEFT | .999196 |
| Mixed: tax cuts/restrictions first | LEFT | .999169 |

No label changes; second-minus-first LEFT score deltas +.000196 and -.000027.
All model metadata identical across four responses. This is local order stability
in two selected examples only. It does not establish accurate attribution,
ideological symmetry, correct mixed-position handling or calibrated confidence.
One observation per input cannot isolate stochastic variation or support general
robustness claims. Astra Medium no-tools method critique saved in
research/data/order-probe-method-20261005.txt.

Real public form audit ran 05:53:18-05:53:28 UTC: four HTTP 200 responses, complete
UI verification and screenshots, no page errors/failed requests, mobile overflow
false. Local Chrome/Playwright fallback; agent-browser CLI unavailable, no cloud
browser tool found. Inputs research/data/order-probes-20261005.json. Raw responses,
visible text and screenshots: outputs/live-browser-order-20261005. Sanitized
report research/results/order_probes_20261005.json includes input/script/text/
screenshot hashes, model fingerprints, probability vectors and paired deltas;
also copied to outputs. No training, corpus split access, policy changes or
deployment. Independent human evaluation/high-accuracy evidence still absent.

## 2026-10-05 04:51 UTC heartbeat: OOF confidence and new browser probes

Audited frozen training-only class-weight comparison predictions, not validation
or reserved test data. New oof_confidence_audit.py leaves the older production
confidence audit intact. No fitting, threshold selection, or release approval.
For fixed retained fractions 1/.8/.6/.4/.2, used ceil(fraction*N)-th highest
confidence and retained all ties. Recall denominators include abstentions.

Balanced model: correctness-ranking AUC .56594, multiclass Brier (sum over
classes) .63723, natural-log NLL 1.05447 (probability floor 1e-15), ten fixed-width
bin top-label ECE .12054. At 80% coverage, accuracy among retained predictions
is 48/92=.52174, and all four correct CENTER predictions have been rejected:
delivered CENTER recall 0/26. Even at 20% coverage, retained accuracy is only
15/23=.65217, with CENTER recall still zero. Full-coverage accuracy 58/115.

Unweighted model: AUC .54068, Brier .64441, NLL 1.06660, ECE .05897. Its lower
ECE does not make it a better classifier: raw accuracy and macro-F1 are worse,
and 20%-coverage accuracy is 10/23=.43478. Do not optimize ECE alone. These are
descriptive, bin-dependent development diagnostics with no uncertainty intervals,
disputed labels and repeated fold inspection; not independent product accuracy.

Source report hash links all 230 probabilities to prior model hashes/split IDs.
Output includes bins, all ten retained-ID sets, actual coverage and per-reference-
class retained counts. Verified source hash, bin totals and all retained-ID/count
sets. Sixteen tests passed across new OOF audit, existing production confidence
audit, and split/feature tests. Astra Medium no-tools critique saved in
research/data/confidence-audit-method-20261005.txt. Report:
research/results/confidence_audit_20261005.json, also copied to outputs.

Three new AI-authored diagnostics (no human gold) tested through the public form:
recipe LEFT .997732; fictional opposed attributed quotes LEFT .998199; mixed-policy
passage LEFT .999138. All HTTP 200, unchanged production weights. These targeted
examples expose relevance/attribution/mixed-position concerns, not a measured
error rate or benchmark. No AI labels were promoted to human annotations.

Actual first browser run 05:25:10-05:42:58 UTC retained two responses/screenshots
then failed during screenshot capture; no mobile check completed in that run.
Remaining-probe retry 05:48:54-05:49:07 completed, no page errors/failed requests,
mobile overflow false; mobile screenshot visually inspected. Both runs preserved
under outputs/live-browser-confidence[-retry]-20261005, including failure.png.
Local Chrome/Playwright fallback (no cloud browser tool; agent-browser unavailable).
Inputs: research/data/confidence-browser-probes-20261005.json. Sanitized responses,
model fingerprints, screenshot hashes and failure metadata:
research/results/confidence_browser_20261005.json. No deployment; human evaluation
and independent high-accuracy evidence still outstanding.

## 2026-10-05 03:42 UTC heartbeat: fixed class-weight ablation

Tested one fixed change: class_weight='balanced' to None in the frozen word
TF-IDF logistic-regression pipeline. Cloned each reference estimator so all other
parameters remained identical (C=1, max_iter=1000, random_state=20261001).
Reused hash-verified fold-local vectorizers and the same five event-string folds,
115 training records only. Also refitted all five balanced controls: held-out
probabilities reproduced their frozen references within atol/rtol 1e-10. Ten fits
total, 8-16 iterations; convergence warnings configured as errors, none raised.

| Training-only OOF metric | Balanced | Unweighted |
| --- | ---: | ---: |
| Correct / 115 | 58 | 54 |
| Accuracy | .50435 | .46957 |
| Macro-F1 | .44234 | .31586 |
| LEFT recall | 22/38 | 10/38 |
| CENTER recall | 4/26 | 0/26 |
| RIGHT recall | 32/51 | 44/51 |
| Unanimous-label subset correct / 54 | 25 | 18 |

Unweighted predicts LEFT 20, CENTER 0, RIGHT 95. Twelve corrected versus sixteen
regressed examples. Removing weights worsens CENTER performance and macro-F1;
reject this candidate. This isolates weighting in this fixed small pipeline, not
a general conclusion about weighting or independent high accuracy. Repeatedly
used development folds, overlapping fits, disputed label aggregation and related
event families limit inference. No validation/test read, tuning, relabeling,
paid compute, deployment, or release approval. Corpus remains research-only.

Artifacts: research/scripts/class_weight_cv.py;
research/checkpoints/class-weight-cv-20261005 contains protocol, ten model files
and full results. research/results/class_weight_cv_20261005.json retains train/
held IDs, text fingerprints, all parameters, model hashes, 230 OOF predictions/
probabilities, confusion matrices and paired-change IDs; copied to outputs.
Verified ten checkpoint hashes, 230 argmax/sum checks, complete unique OOF
coverage, and that class_weight is the sole parameter difference. Three existing
split/feature tests passed. Astra Medium critique through requested terminal
route saved in research/data/class-weight-method-20261005.txt, no tools used.

Public browser audit 03:43:17-03:43:42 UTC used local Chrome/Playwright fallback
(no cloud browser tool found; agent-browser CLI unavailable). Frozen two targeted
examples again HTTP 200 with unchanged LEFT .993377 / RIGHT .997867; no page
errors, failed requests or mobile overflow. These are repeated production smoke
checks, not candidate evaluation. Raw browser evidence/screenshots in
outputs/live-browser-class-weight-20261005; sanitized fingerprints and screenshot
hashes in research/results/class_weight_browser_20261005.json.

## 2026-10-04 22:57 UTC heartbeat: raw-label scoring consistency

Fixed offline policy evaluation to reconstruct raw labels from validated logits
and the model's id2label mapping, instead of trusting a potentially stale stored
raw_label. Original labels remain in source_report_raw_label for audit. Ties
use first-index argmax; abstentions remain separate from raw predictions. Inputs
are not mutated and release_approved remains false. This prevents stale labels
from either inflating or depressing reported raw accuracy; it is not a model gain.

43 selected research/report-contract/metric tests passed, including five new
consistency tests for both stale-label directions, abstention, null source label,
and custom mapping/ties. Integration fixtures mock backend classification and
policy validation to isolate report assembly; they do not verify numerical model
inference. No corpus split, training run, or independent human evaluation was
performed. No Astra ML review was requested for this engineering-only change.

Public browser audit actually ran October 5, 00:43:37-00:44:00 UTC (later than the
trigger). Used existing local Chrome/Playwright fallback; no cloud browser was
available and agent-browser CLI was unavailable. Two frozen targeted examples
again returned HTTP 200, LEFT .993377 and RIGHT .997867 respectively. No page
errors, failed requests, or mobile horizontal overflow. Repeated selected errors
are smoke checks only, not a representative accuracy estimate. Raw responses and
screenshots: outputs/live-browser-raw-consistency-20261004; sanitized model
fingerprints and screenshot hashes: research/results/raw_consistency_browser_20261004.json.
Production unchanged; no deployment or high-accuracy claim.

## 2026-10-04 21:55 UTC heartbeat: corrupted-training-label controls

Ran five fixed controls, seeds 20261004-20261008. For each frozen development fold,
shuffled only its training labels with SeedSequence([seed,fold]); held labels
unchanged, training class counts preserved. Reused verified fold-local word TF-IDF
artifacts, balanced logistic C=1, max_iter=1000, random_state=20261001. 25 fits total,
8-15 iterations, no convergence warnings observed. No parameter search, validation
or reserved test read; original corpus labels/files unchanged.

| Seed | Matches/115 | Accuracy | Macro-F1 |
| --- | ---: | ---: | ---: |
| 20261004 | 46 | .4000 | .31864 |
| 20261005 | 41 | .35652 | .31898 |
| 20261006 | 46 | .4000 | .30575 |
| 20261007 | 42 | .36522 | .33374 |
| 20261008 | 46 | .4000 | .31552 |

Original unshuffled baseline: 58/115 (.50435), macro-F1 .44234. Baseline exceeds
all five corrupted-label controls descriptively. This is not an inferential
permutation test or p-value: folds overlap, shuffles are fold-local rather than
a single globally permuted dataset, only five seeds were used, and prevalence
information is preserved. Cannot establish no leakage, causality or high accuracy.
Controls are not deployment candidates. Research-only noncommercial corpus.

Protocol, all permutation indices/shuffled training labels, held/train IDs, 575
OOF predictions with probabilities, 25 checkpoints and model hashes retained in
research/checkpoints/shuffle-control-20261004. Report committed as
research/results/shuffle_control_20261004.json and copied to user outputs. Verified
all 25 checkpoint hashes/permutations and 575 probability-argmax predictions;
three existing split/feature tests passed. Astra Medium no-tools method critique
completed through requested terminal route; research/data/shuffle-method-20261004.txt.

Two repeated frozen targeted public-browser probes returned HTTP 200, unchanged
LEFT/RIGHT results, no page errors/failed requests/mobile overflow. Local Chromium
fallback, cloud/agent-browser CLI unavailable as previously checked. Raw evidence
outputs/live-browser-shuffle-control-20261004; sanitized model/screenshot hashes
research/results/shuffle_control_browser_20261004.json. Production unchanged.

## 2026-10-04 18:58 UTC heartbeat: numeric calibration input contract

Added shared numeric-report checks before calibration optimization and policy
classification. Require complete string-index 0/1/2 mapping to LEFT/RIGHT/CENTER
exactly once, three finite numeric logits per row, recognized reference labels,
and nonnegative integer token counts. Booleans are rejected as logits/counts;
strings, NaN/infinity, wrong vector dimensions and malformed class maps fail.
Checks cover negative and uncertain rows too, before calibration filters them.
No changes to model behavior, decision thresholds or dataset labels.

Eight new tests include rejection before the optimizer and a positive synthetic
120-row calibration fixture that still yields full coverage and release_approved
false. The synthetic fixture stays in test memory and is not human evidence or
a research accuracy result. All 38 selected regression tests passed in 13.66s
(research, report contract, delivered metrics, unique examples, numeric reports).
An earlier run of the seven rejection tests plus existing suite passed 37 tests;
the positive control was then added. No dependencies installed. git diff --check
passed. No validation/test dataset was opened, and no training or new Astra ML
review is claimed. This is offline calibration/evaluation integrity work.

Public-browser smoke repeated two frozen targeted examples: HTTP 200, unchanged
LEFT/RIGHT outputs. Local Chromium fallback, agent-browser CLI/cloud unavailable
as previously checked; zero page errors, failed requests or mobile overflow. Raw
evidence outputs/live-browser-numeric-contract-20261004, sanitized model and PNG
hashes research/results/numeric_contract_browser_20261004.json. Production unchanged.

## 2026-10-04 17:56 UTC heartbeat: conditional OOF uncertainty analysis

Resampled the frozen six-approach shared-error report (word, semantic, hybrid,
character, hierarchy, ensemble), not the later SVM report. Used only the 115
training rows, verified their hashes/IDs/reference labels and aligned predictions.
5,000 paired event-string cluster bootstrap draws, seed 20261004: uniformly draw
42 groups with replacement, retain every row in each selected group, calculate
sample-weighted accuracy and candidate-minus-word differences. No retraining,
parameter adjustment, validation/test access or model selection.

| Approach | Difference vs word (percentage points) | 95% percentile interval |
| --- | ---: | ---: |
| Semantic | 0 | [-9.09, 9.66] |
| Hybrid | +0.87 | [-7.35, 8.77] |
| Character | -2.61 | [-8.97, 4.20] |
| Hierarchy | -2.61 | [-7.26, 2.48] |
| Ensemble | +2.61 | [-5.05, 10.29] |

All five difference intervals include zero. Ensemble accuracy percentile interval
is [.42982,.62265], versus word [.38888,.61538]. This does not support a robust
improvement claim. These are conditional exploratory intervals, not independent
product confidence bounds: overlapping fitted folds, related events across group
strings, disputed labels, repeated comparisons and training variability remain
unaccounted for. No statistical significance claim or equivalence claim.

Saved every replicate's group draw counts, accuracies and paired differences in
research/checkpoints/oof-uncertainty-20261004/replicates.npz. Report includes artifact
hashes, group/model ordering, row IDs/groups, settings and limitations:
research/results/oof_uncertainty_20261004.json, also copied to outputs. Existing
source report links raw predictions, fold IDs and model artifacts. Four tests
passed for reproducibility, pairing, row weighting and malformed alignment.
GPT-6 Astra Medium no-tools method critique completed via requested terminal
route; research/data/oof-uncertainty-method-20261004.txt. Parent model unchanged.

Two repeated targeted public-browser smoke probes returned HTTP 200 and unchanged
LEFT/RIGHT outputs. Local Chromium fallback, cloud/agent-browser CLI unavailable
as previously checked. No page errors/failed requests/mobile overflow. Raw
responses/screenshots outputs/live-browser-oof-uncertainty-20261004; sanitized
model/screenshot hashes research/results/oof_uncertainty_browser_20261004.json.
Production unchanged; these browser probes are not part of bootstrap evidence.

## 2026-10-04 15:22 UTC heartbeat: fixed linear SVM rejected

Actual execution resumed around 17:50 UTC. Tested LinearSVC against the stored
word logistic baseline, reusing identical fold-local vocabulary/IDF transforms
on 115 training rows and five frozen event-string folds. Verified training and
baseline hashes, split membership and complete unique OOF coverage. No validation
or reserved test read. Fixed C=1, balanced classes, squared_hinge, l2, dual=auto,
tol=1e-4, max_iter=10000, seed=20261001; no parameter search. All five fits completed
in 26-28 iterations with no convergence warnings observed.

SVM: 53/115 reference-label matches (.46087), macro-F1 .39604, recall LEFT .52632,
CENTER .11538 (3/26), RIGHT .58824. Baseline remains 58/115 (.50435), macro-F1 .44234,
CENTER 4/26. SVM corrected zero baseline errors and regressed five. Unanimous-label
subset: 21/54 versus baseline 25/54. Full coverage without abstentions. Negative
result for this fixed representation/configuration, not a claim about all SVMs.
No promotion or threshold tuning; noncommercial disputed corpus remains research-only.

Preserved raw decision scores (not probabilities), predictions, model hashes,
fold IDs, settings, protocol and five checkpoints under
research/checkpoints/svm-cv-20261004. Report research/results/svm_cv_20261004.json
also copied to user outputs. Three existing feature/split regression tests passed;
all 115 saved predictions verified against their maximum raw decision scores.
GPT-6 Astra Medium completed a no-tools method critique via requested terminal
route, saved research/data/svm-method-20261004.txt; parent model unchanged. It
cautioned that decision-score scales need not be comparable between folds.

Public browser smoke repeated the prior two targeted CENTER-reference misses:
HTTP 200, unchanged LEFT .993377 and RIGHT .997867. Local Chromium fallback,
agent-browser CLI/cloud browser unavailable as previously checked. Zero page
errors/failed requests/mobile overflow. Raw evidence outputs/live-browser-svm-20261004;
model fingerprints and screenshot hashes research/results/svm_browser_20261004.json.
These checks concern unchanged production, not online candidate validation.

## 2026-10-04 13:40 UTC heartbeat: reject duplicate evaluation evidence

Completed the duplicate-evidence check begun before intervening heartbeat
messages; no separate experiments are claimed for those wakeups. Calibration and
policy evaluation now require nonempty prediction arrays, object rows, nonblank
string IDs and valid 64-hex text SHA-256 values. Duplicate IDs or text hashes
within either report are rejected, including differently cased hash strings.
Cross-report text-hash comparison also normalizes hexadecimal case.

Checks run before calibration sample counting and policy scoring. Lightweight
policy report checks now precede backend import, allowing malformed/overlapping
reports to fail without loading inference dependencies. Existing policy binding
still executes before any classification. No changes to policy thresholds,
production inference, dataset labels or model weights. Exact byte-hash uniqueness
does not establish semantic/source/event independence; paraphrases remain outside
this check, and supplied hashes/provenance remain assertions requiring audit.

Seven new tests cover preserved valid input, duplicate IDs, hash-case duplicates,
empty/malformed rows, 100 repeated calibration rows, 300 repeated test rows and
case-insensitive cross-split overlap. All 30 selected tests passed in 12.39s:
test_research.py, test_report_contract.py, test_delivered_metrics.py,
test_unique_examples.py. Used system Python plus existing local tld/pytest paths;
no dependency installation this run. No backend import warning in this run, but
that does not resolve the earlier numerical Torch/NumPy compatibility warning.
git diff --check passed. No actual validation or reserved test examples read.
This was an engineering integrity fix, not ML training or an Astra model review.

Public browser smoke: three frozen repetition probes HTTP 200, unchanged known
withheld/LEFT/CENTER outputs. No page errors/failed requests/mobile overflow.
New browser skill was read; agent-browser CLI was not installed and no cloud
browser was available, so used existing local Chromium/Playwright fallback.
Raw responses and screenshots in outputs/live-browser-unique-evidence-20261004;
sanitized model fingerprints and screenshot hashes in
research/results/unique_evidence_browser_20261004.json. No deployment performed.

## 2026-10-04 09:54 UTC heartbeat: shared development-error audit

Execution began around 10:04 UTC. Compared saved OOF predictions from six fixed
approaches: word, semantic, hybrid, equal-weight ensemble, character, CENTER-first
hierarchy. Verified training-data hashes, ensemble component hash, complete unique
115 IDs, matching held-fold assignments and exact train/held memberships. Reference
folds also pass event-string disjointness checks. No new offline predictions,
training, label edits, validation access or reserved test access.

Across 115 examples: all six correct on 34, all six wrong on 34, at least one
correct on 81, and predictions disagree on 57. Categories are not disjoint:
different wrong labels can disagree. These are agreements with existing corpus
reference labels, not product accuracy or independent human adjudication.

| Reference slice | N | All six wrong | At least one correct |
| --- | ---: | ---: | ---: |
| LEFT | 38 | 10 | 28 |
| CENTER | 26 | 16 | 10 |
| RIGHT | 51 | 8 | 43 |
| Unanimous source labels | 54 | 18 | 36 |
| Disputed source labels | 61 | 16 | 45 |

No CENTER example was correct under all six approaches. Shared failures therefore
extend to unanimously annotated examples; disagreement between source reviewers
alone cannot explain them. Conversely, unanimity is not proof of truth and
all-model-wrong does not establish bad annotation. Models share data and are not
independent annotators. The 81 any-correct count is retrospective oracle coverage,
not achievable accuracy or an upper bound on future models.

GPT-6 Astra Medium completed no-tools methodological critique via requested
terminal route; response research/data/error-audit-method-20261004.txt. Four tests
passed for duplicate/missing IDs, wrong folds and wrong consensus. All row IDs,
text hashes, reference labels, annotation-agreement status and six predictions
retained in research/results/shared_errors_20261004.json and user-facing outputs.
Input reports preserve underlying raw scores, model hashes and dataset provenance.
No model promotion; corpus remains noncommercial research-only.

Targeted public-browser test selected the first two all-six-wrong CENTER-reference
rows in training order. Production returned LEFT .993377 for 010d924f-4636-45ce-a97e-703055a109ad
and RIGHT .997867 for 091773c9-9457-4534-b764-d19057a39204. This selection explicitly
uses existing labels/errors and cannot estimate accuracy. Both HTTP 200; local
Chromium fallback (cloud browser unavailable), zero errors/failed requests/mobile
overflow. Raw evidence outputs/live-browser-shared-errors-20261004; sanitized
report research/results/shared_errors_browser_20261004.json. Production unchanged.

## 2026-10-04 06:23 UTC heartbeat: prevent silent metric denominator loss

Fixed summarize() accepting unknown reference labels by silently excluding them
from political/negative metrics. It now rejects unknown labels (including typos
and unsupported MIXED rather than silently mapping them). It validates delivered
decision/label consistency for NONPOLITICAL and UNCERTAIN rows as well as political
rows, and rejects invalid raw predictions on political examples. Valid negative
rows remain counted; no model thresholds or behavior changed.

Added four tests covering unknown references, malformed negative/uncertain
decisions, invalid raw predictions and preserved valid-negative denominators.
An initial test accidentally made both raw and delivered labels invalid and hit
the earlier delivered-label check; corrected the fixture to isolate raw validation.

Recovered the previously blocked selected research tests by installing the
repository-pinned tld==0.13.2 with --no-deps into research/checkpoints/report-test-deps,
not system or production packages. Ran system Python with existing local pytest
and backend package paths appended: tests/test_research.py, test_report_contract.py,
test_delivered_metrics.py. All 23 passed in 32.88s. One Torch/NumPy _ARRAY_API warning
occurred during backend import; no numerical model inference was tested by this
suite, so runtime inference compatibility is not established. No training or
evaluation dataset examples were loaded. git diff --check passed.

Repeated two frozen live public-site browser probes using local Chromium fallback
(no cloud browser available). Both HTTP 200, same LEFT results as previous runs,
no page errors/failed requests/mobile overflow. No new classifier finding. Raw
responses/screenshots: outputs/live-browser-metric-contract-20261004. Sanitized
model fingerprints and PNG hashes: research/results/metric_contract_browser_20261004.json.
Production unchanged. No new Astra ML review or accuracy improvement claimed;
this run repairs metric integrity and closes the selected-suite collection gap.

## 2026-10-04 05:22 UTC heartbeat: stricter calibration/evaluation report contract

Fixed two offline validation risks. Both calibration and policy evaluation
previously accepted truthy strings/numbers as human_reviewed, including "false".
They now require literal boolean True plus a nonblank string provenance reference.
Evaluation now also requires validation/test reports to match analysis mode,
weight/config/tokenizer hashes, aggregation, max_length, stride and id2label.
Missing model fields fail closed. Checks occur before backend inference import.
These fields remain supplied assertions, not authentication of actual human work.

Shared report_contract.py prevents differing checks in calibration and evaluation.
No change to production inference, thresholds, datasets or model weights. Release
approval remains false. Updated the existing reused-test fixture to include its
analysis mode so it reaches its intended identical-dataset rejection.

Eight new unit tests passed under system Python, including fit/evaluate entry
point rejection before work, unchanged inputs on rejection, each model field,
label-map differences, mode mismatch, nonboolean provenance, missing fingerprints
and blank/nonstring reference. Six delivered-metric regression tests passed.
Broader tests/test_research.py collection could not run: legacy runtime lacked
tld/scipy/sklearn; system runtime with existing pytest/backend paths still lacked
tld. No dependencies installed or environment files changed. Broader suite is
explicitly unverified. git diff --check passed.

Three frozen public-browser repetition probes returned HTTP 200, reproducing
the known withheld/LEFT/CENTER pattern. No new accuracy finding. Local Chromium
fallback, no cloud browser available; no page errors, failed requests or mobile
overflow. Raw screenshots/responses outputs/live-browser-report-contract-20261004;
sanitized model and screenshot hashes research/results/report_contract_browser_20261004.json.
This was an engineering integrity fix, no new Astra ML review or model training
claimed. Validation/test examples, including reserved corpus test, were not read.

## 2026-10-04 01:14 UTC heartbeat: CENTER-first hierarchy rejected

Actual execution resumed around 05:19 UTC. Trained a fixed two-stage classifier
inside each of the five frozen training-only event-string folds. Reused complete
fold-local word TF-IDF transformation (vocabulary and IDF) after verifying artifact
hashes. Stage one balanced binary CENTER/partisan used all fold training rows;
stage two balanced LEFT/RIGHT used only partisan rows. Both logistic C=1, lbfgs,
max_iter=1000, random_state=20261001. Fixed CENTER gate >=.5; otherwise conditional
LEFT/RIGHT argmax. No threshold search. No validation or reserved test read.

Saved joint scores CENTER=p, LEFT=(1-p)*qLEFT, RIGHT=(1-p)*qRIGHT; these sum to one
but are not calibrated and intentionally need not share the hard-gate argmax.
All 115 rows received OOF predictions (100% coverage, no abstentions).

| Training-only OOF | Word baseline | Hierarchy |
| --- | ---: | ---: |
| Corpus-label matches | 58/115 | 55/115 |
| Macro-F1 | .44234 | .35797 |
| LEFT recall | .57895 | .57895 |
| CENTER recall | .15385 (4/26) | 0 (0/26) |
| RIGHT recall | .62745 | .64706 |
| Unanimous-label matches | 25/54 | 20/54 |

Only one row was predicted CENTER; its corpus label was RIGHT. CENTER-labeled
rows' gate scores ranged .31706-.48346 (mean .43112); LEFT mean .41320, RIGHT
mean .42804. Candidate failed the intended recall objective and is not promoted.
This does not rule out hierarchical methods generally. Do not retune .5 from
these held-out outcomes. No convergence warning observed; fits took 6-7 iterations.

GPT-6 Astra Medium method-only critique completed through the requested terminal
route, with no tools/files/network; saved research/data/hierarchy-method-20261004.txt.
It stressed gate-error propagation, uncalibrated balanced-model scores and the
development-only nature of the comparison. No parent model change claimed.
Four tests passed for boundary, hard-gate/joint-score distinction and malformed
probabilities. Checkpoints, protocol, split IDs, model hashes and all raw scores:
research/checkpoints/hierarchy-cv-20261004. Committed report:
research/results/hierarchy_cv_20261004.json. Corpus remains research-only due to
noncommercial license and disputed labels; no independent high accuracy claimed.

Local Chromium fallback repeated the prior frozen two-row live-browser smoke
test; both HTTP 200, same LEFT outputs, zero page errors/failed requests/mobile
overflow. It tested unchanged production, not the candidate. Raw evidence in
outputs/live-browser-hierarchy-20261004, sanitized model and screenshot hashes in
research/results/hierarchy_browser_20261004.json. No deployment performed.

## 2026-10-03 22:53 UTC heartbeat: training-fold overlap audit

Audited 115 training rows across the five frozen event-string group folds, without
validation/test reads, label-based selection, retraining or split changes. Checked
feature alignment, source/fold hashes, normalized finite 384-dimension train-only
MiniLM vectors, and unique complete held-ID coverage. Each unordered cross-fold
pair was evaluated once: 5,290 pairs. Lexical scores use lowercase regex word
tokens, unique contiguous five-grams, Jaccard and shared-count/minimum-set-size
containment. Computed raw and fixed-footer-stripped lexical scores; semantic
embeddings remained raw. Empty shingle sets are explicitly rejected; none occurred.

Fixed flags: cosine >= .85 OR clean Jaccard >= .30 OR clean containment >= .50
with >=20 shared five-grams. Zero flagged pairs, zero exposed rows in each fold.
Maximum cosine .66331327; maximum clean Jaccard .01156069 (two shared five-grams).
This is a negative overlap screen, not proof of event-family independence or an
explanation for poor model performance. Thresholds were not adjusted after results.

GPT-6 Astra Medium gave a no-tools method critique through the requested terminal
route. Saved research/data/fold-overlap-method-20261003.txt. It cautioned against
calling flags leakage or nonflags independence; clarified empty-shingle handling.
An initial run and the subsequent explicit-empty-check run gave identical counts.
Seven existing overlap-helper regression tests passed. All pair records retained
in research/checkpoints/fold-overlap-20261003/all_pairs_verified.json, with its hash
and top ten semantic/lexical pairs in research/results/fold_overlap_20261003.json.
No model accuracy or new human annotations claimed.

Public-site browser smoke test selected the highest-cosine pair without labels:
1c61bd7b-4273-42ac-a1b2-0661ec6212b1 and 35492fcc-28c7-499f-8822-711352bbcca0.
Both returned HTTP 200 / LEFT, scores .779822 and .998497. Production remains
unchanged. Local Chromium fallback, no cloud browser available; no page errors,
failed requests or mobile overflow. Raw responses and screenshots retained in
outputs/live-browser-fold-overlap-20261003; sanitized model fingerprints and PNG
hashes in research/results/fold_overlap_browser_20261003.json.

## 2026-10-03 21:42 UTC heartbeat: fixed character-feature training experiment

Trained five character TF-IDF/logistic models on the existing 115-row training
partition only. Reused frozen five event-string group folds from footer CV;
verified input hash and baseline artifact hashes, partition completeness and
event-string disjointness. Vocabulary fitted inside each training fold only.
No validation or reserved test read. Event-family independence is not established.

Fixed settings before training: char_wb ngrams 3-5, min_df=2, max_features=30000,
sublinear_tf=True; logistic C=1, balanced classes, lbfgs, max_iter=1000,
random_state=20261001. No search. Fold vocabularies 12293/12081/12028/12431/12658;
iterations 9/8/12/10/11, no convergence warnings observed. Stored all five joblib
models locally, protocol before fitting, hashes, split IDs and every OOF score.

| Training-only grouped OOF | Word baseline | Character candidate |
| --- | ---: | ---: |
| Corpus-label matches | 58/115 | 55/115 |
| Accuracy | .50435 | .47826 |
| Macro-F1 | .44234 | .42247 |
| LEFT recall | .57895 | .55263 |
| CENTER recall | .15385 | .15385 |
| RIGHT recall | .62745 | .58824 |
| Unanimous-label matches | 25/54 | 26/54 |

Character candidate corrected 7 and regressed 10 baseline predictions. Negative
overall development result; no promotion or parameter adjustment. One extra
unanimous-subset match does not override the overall result. Corpus labels are
disputed and noncommercial; all models remain research-only. These reused small
development folds cannot establish independent high accuracy.

GPT-6 Astra Medium completed method-only critique using the requested terminal
route, with tools/files/network prohibited; response saved in
research/data/character-cv-method-20261003.txt. It highlighted small-sample
instability, event-family overlap, possible style/entity artifacts and label
uncertainty. No parent-model change claimed.

Artifacts: research/checkpoints/character-cv-20261003, committed report
research/results/character_cv_20261003.json, reusable research/scripts/character_cv.py.
Live public-site browser smoke test used first two training rows, both HTTP 200
and LEFT (.993377/.994163); production unchanged, not candidate validation.
Local Chromium fallback, no cloud browser available; zero errors/failed requests
or mobile overflow. Raw responses/screenshots in outputs/live-browser-character-cv-20261003,
sanitized fingerprinted report research/results/character_cv_browser_20261003.json.
Three existing feature/split-helper regression tests passed; git diff --check passed.

## 2026-10-03 20:25 UTC heartbeat: paired stance and attribution diagnostic

After P005's pro-market LEFT result, froze six AI-authored inputs before execution:
original P005, explicit rejection, neutral quotation, neutral-preface variant,
original P006 safety-net endorsement, and neutral quotation of P006. Exact inputs
in research/data/attribution-diagnostic-20261003.json. No human labels assigned.
This small selected diagnostic cannot establish accuracy, generalization, or the
cause of sensitivity. No tuning, candidate selection or reserved-test access.

Requested method-only critique using codex exec --ephemeral -m gpt-6-astra with
model_reasoning_effort="medium", read-only sandbox, explicit no-tools/no-files/
no-network instruction. It completed without tool use; saved response in
research/data/attribution-method-review-20261003.txt. Parent model unchanged.
Astra cautioned against correctness claims and recommended reporting full score
distributions, including the original-versus-neutral-preface comparison.

Real public-site form submissions via local Chromium fallback (cloud browser
unavailable), 20:26:08-20:26:17 UTC: all six HTTP 200, all LEFT, zero abstentions.
LEFT scores: original .945672, rejection .995734, quote .999112, neutral preface
.974841, safety-net .997547, safety-net quote .999091. No label or decision flips.
Total variation from market original: rejection .050062, quotation .053440,
preface .0291685, safety-net endorsement .051875. Safety-net quotation TV .001544.
These describe outputs only; they are not accuracy, recall, or evidence that
quotation must always receive a particular political label. Wording and stance
effects are confounded, and raw softmax is not calibrated correctness.

All response model metadata matched: production weights 548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d;
tokenizer bundle 4082d391a9b2de9138b4f835f8d9d8711314e4de08a973a6ea2ded651b529917.
No truncation, page errors, failed requests or mobile overflow; inspected mobile
screenshot. Raw responses, text and screenshots in outputs/live-browser-attribution-20261003.
Summary preserves every score, text/input/audit/screenshot hash and full model
metadata in research/results/attribution_diagnostic_20261003.json. Reusable summary
script rejects changed inputs, incomplete/duplicate cases and changed metadata;
four focused tests passed. Production unchanged; no model improvement claimed.

## 2026-10-03 18:33 UTC heartbeat: prevent silent annotation storage failure

Found a concrete review integrity bug: both save and skip handlers ignored the
store() failure result, cleared dirty, and replaced the storage-error message
with success. Fixed using separate storagePending state: failed writes retain
an explicit warning and unload protection, survive item navigation, and block
workspace replacement. All in-memory records remain exportable. A later
successful write persists the full answer map and clears the pending state.
Download initiation does not falsely clear persistence warnings.

Six local Chromium browser checks passed: save failure, navigation/unload guard,
workspace-switch protection, skip failure, export recovery and full-map retry.
Two synthetic test records existed only in an isolated browser and transient
download, were clearly marked AUTOMATED TEST ONLY, and were not retained as
annotations, evidence labels or human gold. Human reviews completed remains zero.
Seven offline-bundle regression checks and 18 annotation pytest tests also passed.
git diff --check passed. Reviewed storage-warning screenshot; other desktop/mobile
regression images and exact viewer hash retained in outputs/review-storage-20261003
and outputs/review-storage-bundle-regression-20261003. Test summaries committed in
research/results/review_storage_20261003.json and review_storage_bundle_20261003.json.

Used local Chromium fallback for actual public-site form tests (cloud browser
not available). Frozen pilot controlled examples P005 and P006 were selected as
the first two controlled items in manifest order, without examining predictions.
P005 advocates private enterprise/lower taxes/fewer regulations and returned
LEFT .945672; P006 advocates a stronger public safety net/wealth taxes and returned
LEFT .997547. These are AI-authored diagnostic examples, not human gold or an
accuracy estimate. Raw responses and screenshots retained under
outputs/live-browser-review-storage-20261003; sanitized summary and hashes in
research/results/review_storage_browser_20261003.json. Production unchanged.

Updated local reviewer deliverable and README; no model/dataset changes, training,
reserved test access, new Astra review or deployment claimed. This bounded
engineering run safeguards future human annotation, not measured ML accuracy.

## 2026-10-03 15:15 UTC heartbeat: offline human-review preparation

Implemented an offline snapshot-bundle importer in the existing review page.
It accepts only the complete frozen 100-ID manifest, validates every text hash,
rejects duplicate/unknown/missing IDs, and stages all records before changing
loaded texts. Unsaved judgments survive import. No labels or predictions are
imported, and no human judgments were created during tests. Pilot remains
development-only; this does not supply independent accuracy evidence.

Local Chromium 154 (cloud browser unavailable) verified four atomic rejection
cases, successful 100-item import, draft preservation and displayed article
content. Zero HTTP requests during offline import, zero page errors, no mobile
horizontal overflow. Desktop/mobile screenshots retained and mobile inspected.
Bundle, manifest and generated-viewer hashes recorded in
research/results/offline_review_20261003.json. Test timestamps reflect actual
execution (18:31 UTC), later than the heartbeat's start timestamp.

Annotation tests: 18 pytest checks passed in stance-runtime; 4 audit unittest
checks passed in system Python. Initial combined pytest collection failed because
stance-runtime lacks numpy; reran separately with existing appropriate runtimes,
without changing dependencies. git diff --check passed.

Live public-site form checks repeated the three frozen headline repetition
probes: one copy withheld, four LEFT, eight CENTER. All HTTP 200, no page errors,
failed requests or mobile overflow. This reconfirms an existing failure, not a
new finding or gold-label metric. Sanitized evidence in
research/results/offline_review_browser_20261003.json; raw responses and PNGs in
outputs/live-browser-offline-review-20261003. Production unchanged.

User-facing local reviewer HTML and offline snapshots copied to outputs; article
snapshots remain local and are not committed or publicly deployed. README now
documents bundle validation and reuse restrictions. No model training, new Astra
review, reserved test access, commercial-use clearance or release claimed.

## 2026-10-03 12:04 UTC: broader frozen-pilot context audit

Audited the opt-in periodic/distinct-paragraph candidate on the existing unlabeled
rubric pilot: 60 historical articles and 40 AI-authored controlled examples. The
expected ../research-data checkout was absent, so retrieved only the 60 manifest
IDs from pinned ramybaly/Article-Bias-Prediction revision
ced8111a720948e6a410e52031ace99c4e53f096. Read content_original, not inherited bias
labels; verified stripped historical text and controlled text against every
manifest SHA-256. All 100 verified, zero failures or substituted snapshots.
Local retained texts are research-only and not committed/redistributed.

Historical articles: two context views changed, zero new minimum-context
exclusions, zero originally short. P019 changed 1496->1488 tokenizer tokens;
P093 changed 505->481. Controlled examples: zero changed views or new exclusions;
P016 was already below the original minimum. All tokenizer files matched the
previous production-bound fingerprint. Candidate threshold remains 12, unchanged.
One focused frozen-text integrity test passed. These are compatibility counts,
not human-reviewed false-positive rates, political accuracy or semantic relevance.
The pilot is development-only, and human_reviewed remains false.

Saved per-item counts, IDs, frozen hashes, source links, failures, source revision
and summary in research/results/pilot_context_20261003.json. Exact verified texts
and browser selection are local in research/checkpoints/pilot-context-20261003/.
No model fitting, calibration, PoliticalBiasCorpus reserved-test use, or deployment.
Dataset reuse rights still require review before redistribution/commercial use.
This engineering audit makes no new model-review or high-accuracy claim.

Local Chromium fallback submitted the first three verified historical pilot
articles (P001/P002/P003) to production. All HTTP 200, labels LEFT/LEFT/RIGHT,
token counts 1534/1046/1535, windows 4/3/4, no truncation. No page errors,
failed requests or mobile overflow. Raw outputs/screenshots retained at
outputs/live-browser-pilot-context-20261003, with sanitized results and screenshot
hashes in research/results/pilot_context_browser_20261003.json. These functional
checks have no human gold labels and are not accuracy evidence. Candidate remains
offline; numbered/punctuation repetition gaps and human-validation needs persist.

## 2026-10-03 10:34 UTC: exact whole-input repetition shadow extension

Added an opt-in periodic context view to the research runners; default paragraph
candidate remains available and previous results unchanged. The new view detects
only complete, exact word-sequence cycles across the entire input, preserving
case, punctuation and order. It returns one shortest cycle, or falls back to
the existing distinct-paragraph view. No classifier inputs or production code
changed. Thirteen repetition/challenge tests pass, including partial-cycle,
negation, case and empty-input controls.

On the fixed ten-case development challenge, single-newline and space-only
copies now reduce from 87/80 to 10 context tokens and would be withheld. The
three exact-paragraph variants still reduce to 10. Numbered/punctuation variants
remain unhandled (110/101 tokens). Body-only stays 85; repeated-title-plus-body
retains 97 tokens of context. These post hoc cases are not independent validation,
and avoiding exclusion of two additional-context controls does not establish a
human false-positive rate. No broader semantic-equivalence detector is claimed.

Shadow audit of all 115 training records still changes one context view with zero
new short-context exclusions. Tokenizer constituent hashes and live probe token
counts verified as before. Results: research/results/periodic_challenge_20261003.json
and research/results/periodic_guard_training_20261003.json. Exact constructed
texts retained in research/checkpoints/repetition-periodic-20261003/.

Local Chromium fallback repeated the three previous live format cases. Production
still returns LEFT/LEFT/CENTER with unchanged scores because the candidate is
not deployed. HTTP 200 throughout; no page errors, failed requests or mobile
overflow; mobile screenshot inspected. Raw evidence: outputs/live-browser-periodic-20261003;
sanitized results and screenshot hashes: research/results/periodic_browser_20261003.json.
No fitting, validation/reserved-test use, calibration or deployment. This is an
engineering extension, not a model-accuracy improvement or a new ML model review.
Corpus restrictions and missing independent human evaluation remain unchanged.

## 2026-10-03 08:10 UTC: repetition-format challenge and CRLF repair

Constructed ten deterministic development cases from the first training title
and its body: single headline, three exact-paragraph formats, four known-gap
formats, body alone, and repeated title plus body. No political gold labels
assigned. Reused and verified all tokenizer files from the previous shadow run.
An added test failed because CRLF paragraph splitting retained a carriage return
in the first distinct paragraph (11 context tokens instead of 10). Fixed the
research-only splitter to consume CRLF separators. Eight repetition/challenge
tests now pass; initial and corrected offline runs are both retained locally.

Corrected shadow counts: blank-line, CRLF and within-paragraph whitespace
variants all reduce to 10 tokens. Single-newline, space-only, numbered and
punctuation-varied repetitions retain 87/80/110/101 tokens and evade the narrow
candidate. Body-only remains 85 tokens; repeated-title-plus-body reduces from
181 to 97, preserving additional context rather than rejecting all repetition.
This is a ten-case post hoc challenge, not an independent robustness rate,
false-positive estimate or proof of semantic sufficiency. The candidate is not
approved as a general solution and remains disconnected from production.

Local Chromium fallback tested single-newline, space-only and repeated-plus-body
inputs on production. All HTTP 200; results LEFT (.996872), LEFT (.999442), and
CENTER (.696730), respectively. No page errors, failed requests or mobile
overflow; mobile screenshot inspected. The first two confirm continued
classification of formatting variants of the short repeated headline. The last
is a context diagnostic, not a human-labeled correctness judgment.

Evidence: research/results/repetition_challenge_20261003.json and
research/results/repetition_challenge_browser_20261003.json; exact constructed
texts retained under research/checkpoints/repetition-challenge-crlf-fixed-20261003/;
initial pre-fix results under research/checkpoints/repetition-challenge-20261003/.
Raw browser responses/screenshots: outputs/live-browser-repetition-challenge-20261003.
No fitting, validation/reserved-test access, political relabeling or deployment.
This run extends engineering tests; no new ML model review claimed. Corpus
restrictions and missing independent human product evaluation remain unchanged.

## 2026-10-03 07:02 UTC: distinct-paragraph context shadow candidate

Implemented an offline-only minimum-context candidate following the repeated-
headline failure. Model input/scores are not changed. The candidate compares
min(original token count, token count of first occurrences of distinct paragraphs)
against the existing demo threshold of 12. Duplicate matching collapses whitespace
but preserves case and punctuation. Inputs without duplicate paragraphs remain
byte-for-byte unchanged. This is not semantic novelty detection or an adopted
production rule. Six repetition tests passed, including unchanged-input and
first-occurrence preservation cases.

Used the local RoBERTa tokenizer with the legacy isolated runtime (transformers
4.41.2). Initial validation incorrectly compared a tokenizer.json single-file
hash to production's bundle fingerprint and failed closed before evaluation.
Corrected the fingerprint calculation to the exact production convention:
SHA256 of sorted filename+file-hash concatenation. All constituent file hashes
are retained. Bundle matches production 4082d391a9b2de9138b4f835f8d9d8711314e4de08a973a6ea2ded651b529917.
Local original token counts reproduce all three live probes exactly (10/46/94).
Distinct-paragraph context is 10 tokens for all three; the candidate would withhold
the four/eight-copy cases that production classified. It leaves the original
short-headline abstention unchanged.

Applied the candidate only to 115 training records: one context view changes,
but zero additional inputs fall below the minimum. This is not a validated
false-positive rate or human coverage guarantee. Legitimate quotations/refrains,
same-paragraph repetition and paraphrases remain untested limitations. No
classifier training, validation/reserved-test use, threshold search, calibration
or deployment. All corpus/licensing and missing independent-human-evaluation
caveats remain. No new ML model review is claimed for this engineering test.

Full shadow records, view hashes, inputs, tokenizer files and runtime version:
research/results/context_guard_shadow_20261003.json. Fresh local Chromium browser
checks reproduced all three production outputs exactly; the live flaw remains
because the candidate is not deployed. No page errors, failed requests or mobile
overflow; mobile screenshot inspected. Raw evidence is outputs/live-browser-context-shadow-20261003;
sanitized results and screenshot hashes are research/results/context_shadow_browser_20261003.json.

## 2026-10-03 05:55 UTC heartbeat: repeated-headline context-guard failure

Tested the first ordered training headline as one, four and eight identical
paragraphs through the real production browser. No political gold labels were
assigned to these constructed inputs. Local Chromium fallback results:

| Copies | Model tokens | Decision | Displayed label | Maximum raw score |
| --- | ---: | --- | --- | ---: |
| 1 | 10 | abstained: insufficient_context | none | LEFT .998968 |
| 4 | 46 | classified: demo_estimate | LEFT | .998627 |
| 8 | 94 | classified: demo_estimate | CENTER | .999207 |

Exact repetition crosses the token-count guard without supplying new distinct
paragraph content; the label also changes at eight copies. This is one narrow
failure case, not an estimate of accuracy or general attack prevalence. All
HTTP responses were 200; no browser errors, failed requests or mobile overflow.
Mobile screenshot inspected. Raw responses/screenshots are retained at
outputs/live-browser-repetition-20261003, and sanitized responses, view hashes,
diagnostics and screenshot hashes at research/results/repetition_browser_20261003.json.

Implemented research-only repetition telemetry: split on blank lines, collapse
within-paragraph whitespace, preserve case/punctuation, count exact duplicate
paragraphs and words in distinct paragraphs. It does not modify text or model
decisions and does not equate word counts with model tokens. Four unit tests
passed. Applied to all 115 original training records: one already contains an
exact duplicate paragraph. Full diagnostic records and input hash are stored in
research/results/repetition_training_20261003.json. Distinct paragraphs do not
prove semantic novelty, and legitimate quotations/refrains can repeat. Therefore
no deduplication-based rejection policy was deployed or approved.

Requested GPT-6 Astra Medium method review through the terminal client. That
subprocess expanded beyond the requested review-only scope into source and a
legacy training-row read plus a failed network health request. It was terminated
(exit 143) rather than allowed to continue; no completed review is claimed.
Observed access was training/source only, not reserved-test data. Main experiment
used the current snippet-training title and browser independently. No model fitting,
validation/reserved-test evaluation, calibration or production change occurred.
Corpus remains disputed/noncommercial research-only. Independent human product
evaluation and demonstrated high accuracy remain missing.

## 2026-10-03 01:00 UTC heartbeat: title/body context sensitivity

Ran 345 held-fold predictions through the five frozen word-model baselines:
full title+three snippets, title only, and three body snippets only, for all
115 training records. All records had exactly four nonempty paragraphs; the
splitter rejects unexpected structure. Original texts were not changed. No
refitting, validation, reserved-test use or threshold tuning. Artifact and input
hashes, fold membership and complete OOF coverage checked. Full predictions
exactly reproduce the prior 58/115 baseline. Three focused tests passed.

Title-only changed 43/115 labels (.3739), with mean probability total variation
.05710 versus full. Removing the title changed 8/115 (.0696), mean variation
.00875. Neither view produced any zero-feature rows. This suggests the body
snippets contribute substantially for this frozen word model; it does not prove
semantic understanding, absence of shortcuts, or passage-level accuracy.
Removing content changes the evidence, so flips are not inherently errors.
Only full inputs receive reference-label metrics. No article labels were
inherited by the title/body views, and no altered-view accuracy was computed.

GPT-6 Astra Medium reviewed the method via terminal client; advice is local in
research/data/context-ablation-advice-20261003.txt. Reused training folds and
disputed noncommercial corpus remain development-only; event-string separation
does not establish event-family independence. All 345 probability vectors,
text-view hashes, IDs, model hashes and source provenance are preserved in
research/results/context_sensitivity_20261003.json; local browser inputs are
research/checkpoints/context-sensitivity-20261003/browser_views.json.

Production browser diagnostic used local Chromium fallback on the first ordered
training record's three views. Full (97 tokens) and body (85 tokens) were LEFT;
the 10-token title returned HTTP 200 but abstained with insufficient_context,
despite raw LEFT probability .998968. This confirms one minimum-context guard
case, not political accuracy or general robustness. All three requests succeeded;
no page errors, failed requests or mobile overflow. Mobile screenshot inspected.
Raw evidence: outputs/live-browser-context-20261003; sanitized results and screenshot
hashes: research/results/context_browser_20261003.json. No deployment or model
change. Independent task-matched human evaluation remains missing.

## 2026-10-02 23:59 UTC heartbeat: learning-curve ordering sensitivity

Added a group-seed parameter to the existing learning-curve runner, preserving
default 20261002 and all model settings. Ran three prespecified additional base
seeds 20261003, 20261004 and 20261005, each plus zero-based fold index. Forty-five
new fits completed, with complete 115-article OOF coverage at every fraction.
No missing-class failures, reseeding, hyperparameter selection, validation or
reserved-test access. Three subset-integrity tests passed. All full-fraction
predictions exactly reproduce the original 58/115 baseline.

| Base seed | .25 groups matches /115 | .50 groups matches /115 | Full matches /115 |
| --- | ---: | ---: | ---: |
| 20261002 (previous) | 31 | 38 | 58 |
| 20261003 | 50 | 50 | 58 |
| 20261004 | 51 | 58 | 58 |
| 20261005 | 53 | 51 | 58 |

Quarter-group agreement ranges .2696-.4609 (macro-F1 .2435-.3989); half-group
agreement ranges .3304-.5043 (macro-F1 .2688-.4171). The last ordering worsens
from quarter to half, so the initial steep curve was not representative of all
these orderings. Qualify the earlier observation: sample composition and group
ordering substantially influence this small-data result. These descriptive ranges
are NOT confidence intervals, and the runs reuse the same examples/folds rather
than independent evaluation samples. No prediction about attaining 90% follows.

GPT-6 Astra Medium reviewed the replication protocol via the terminal client;
local advice is research/data/learning-replicates-advice-20261003.txt. All previous
task mismatch, disputed-label, noncommercial corpus and event-family leakage
caveats remain. No production release, calibration or threshold change. The
candidate models remain research-only; independent human product gold is absent.

All 45 fitted artifacts, pre-fit protocols, raw predictions, actual subset IDs,
label counts and model hashes are retained locally under
research/checkpoints/learning-replicate-{20261003,20261004,20261005}/.
research/results/learning_replicates_20261003.json records hashes of those full
run records, every curve, actual sample counts, runtime and convergence metadata.
Local Chromium fallback repeated the three prior ensemble-disagreement smoke
cases: HTTP 200 for all, no page errors, failed requests or mobile overflow.
Mobile screenshot inspected. Raw evidence is outputs/live-browser-learning-replicates-20261003;
sanitized outputs and screenshot hashes are research/results/learning_replicates_browser_20261003.json.
These repeated browser checks are functional, not new accuracy evidence.

## 2026-10-02 22:41 UTC heartbeat: nested grouped learning curve

Trained 15 word-based logistic models across the five frozen training folds.
For each fold, sorted source event strings were shuffled once using NumPy
default_rng(20261002+fold), with zero-based fold numbering. Nested prefixes
of ceil(25%), ceil(50%) and 100% of training groups retain whole groups.
Refit TF-IDF separately on every subset: word1,2, min_df2, max_features20000,
sublinear_tf, default L2 normalization. Logistic C1, balanced classes, max_iter1000,
random_state20261001, default lbfgs. Held-out fold remains identical across sizes.
All subsets contained all three classes; no reseeding or substitutions occurred.

| Training event-group fraction | Articles per fold | OOF matches /115 | Macro-F1 |
| --- | --- | ---: | ---: |
| .25 | 27,25,18,35,35 | 31 (.2696) | .2435 |
| .50 | 36,42,57,55,51 | 38 (.3304) | .2688 |
| 1.00 | 92,92,92,92,92 | 58 (.5043) | .4423 |

All full-size OOF predictions exactly reproduced the previous word baseline.
Maximum solver iterations was 14. Two focused unit tests passed for whole-group
nesting, coverage, determinism and input preservation. Saved per-fold scores,
actual label/group counts, vocabulary sizes, subset IDs, raw OOF probabilities,
runtime versions and model hashes in research/results/learning_curve_20261002.json.
All 15 fitted models and pre-fit protocol are retained locally under
research/checkpoints/learning-curve-20261002/. Source input/fold hashes verified.

This curve is sensitive to both sample size and changing topic/class composition.
One ordering per fold cannot estimate ordering uncertainty or justify extrapolating
to 90% accuracy; group fractions are not article fractions. Fold scores are not
independent replicates. GPT-6 Astra Medium reviewed the method via the terminal
client; advice is research/data/learning-curve-advice-20261002.txt. No validation
or reserved-test use, calibration, model selection or production deployment.
Corpus revision b193ee173936b281183ca1dc101ae4de215a0e5c remains noncommercial,
research-only and label-disputed; exact event-string grouping does not prove
event-family independence. Independent human product evaluation remains absent.

Local Chromium fallback repeated production smoke tests on ordered training
examples 4-6: all HTTP 200 and LEFT, no page errors, failed requests or mobile
overflow. Mobile screenshot inspected. Raw evidence is retained in
outputs/live-browser-learning-curve-20261002; sanitized outputs and screenshot
hashes in research/results/learning_curve_browser_20261002.json. These checks
do not evaluate the undeployed learning-curve models or establish accuracy.

## 2026-10-02 21:38 UTC heartbeat: fixed soft-voting ensemble

Evaluated a fixed 50/50 probability average of the saved word and semantic OOF
heads on all 115 training articles. No new fitting, calibration, weight search,
validation or reserved-test access. Input hashes, unique complete ID alignment,
matching fold IDs, probability simplex and argmax consistency are checked. Class
columns align by name, with predetermined LEFT/CENTER/RIGHT tie order. Four unit
tests passed. Source head hashes, fold IDs, encoder provenance, raw ensemble
probabilities and metrics are preserved in research/results/ensemble_oof_20261002.json.

The ensemble matched 61/115 (.5304, macro-F1 .4992), versus 58/115 for either
component, and 27/54 unanimous examples versus 25/54. Left/Center/Right recall
is .5526/.3077/.6275. Against the word head it corrected 13 errors and introduced
10, a three-article net gain on repeatedly explored training data, not independent
evidence of improvement. No deployment or high-accuracy claim is justified.

Components agreed on 70/115 articles (.6087 coverage), with only 41/70 reference
matches (.5857). Both were wrong on 40 articles. Either-component-correct count
is 75/115: a hindsight perfect-selection diagnostic, not attainable performance
or an upper bound on probability averaging (which can choose a third class).
Model agreement is not validated confidence and discarding disagreements does
not establish accuracy. No abstention policy was adopted.

GPT-6 Astra Medium reviewed the design through the terminal client; local advice
is research/data/ensemble-advice-20261002.txt. Balanced-class probabilities remain
uncalibrated, exact event-string grouping is not proven event-family independence,
and disputed noncommercial corpus labels are not task-matched independent gold.
All candidate outputs remain research-only. Local Chromium fallback submitted
the first three training-order component disagreements to production: all HTTP
200 and LEFT, with no page errors, failed requests or mobile overflow. Mobile
screenshot inspected. This is functional production smoke coverage, not testing
of the undeployed ensemble. Raw responses/screenshots are retained at
outputs/live-browser-ensemble-20261002; sanitized results and screenshot hashes
are research/results/ensemble_browser_20261002.json.

## 2026-10-02 20:25 UTC: delivered-label metrics and release-check gap

The offline policy evaluator gated 90% selective accuracy but not 90% raw
accuracy; its F1/recall gates described raw predictions, not delivered labels.
Added an explicit raw-accuracy gate and delivered macro-F1/per-class recall
gates (.85/.80). Existing metrics retain their definitions for compatibility.
New delivered metrics keep every eligible example, treating abstention as a
false negative for its reference class, with a 3x4 confusion matrix and coverage
by true class. No ABSTAIN target class is averaged into political macro-F1.
Inconsistent classified/abstained labels now fail evaluation. Backend imports
are deferred until policy simulation so pure metric/gate tests need no model.

Six focused tests passed: complete abstention with perfect raw predictions,
missing-class coverage, wrong labels versus abstention, selective-success/raw-
failure, inconsistent decisions, and class-specific abstention hidden by overall
coverage. GPT-6 Astra Medium reviewed the method via the terminal client; advice
is local at research/data/delivered-metrics-advice-20261002.txt. Selective accuracy
and coverage are distinct from all-example delivered correctness. In particular,
.90 selective accuracy at .80 coverage only guarantees .72 delivered correctness.
These gates do not claim 90% delivered correctness or population guarantees.

Applied the metrics retrospectively to the hash-matched 66 stored development
responses: raw agreement 31/66=.4697, delivered correct fraction 30/66=.4545,
selective agreement 30/65=.4615, coverage 65/66=.9848, delivered macro-F1 .4102.
Delivered Left/Center/Right recall is .6842/.0952/.5769. Only coverage passes
the illustrative gates; sample-size and nonpolitical requirements also fail.
No actual independent test, calibration, training, threshold change or deployment
occurred. Corpus labels remain disputed/research-only, and reserved test untouched.

Saved ID-aligned predictions, metadata, input hashes and metrics at
research/results/delivered_metrics_20261002.json. Local Chromium fallback rechecked
the prior confidence diagnostic trio on the public site: HTTP 200 for all, with
the same two classified cases and one abstention. No page errors, failed requests
or mobile overflow; mobile screenshot inspected. Raw evidence is in
outputs/live-browser-delivered-20261002; sanitized results and screenshot hashes
are research/results/delivered_browser_20261002.json. This is production smoke
coverage, not a new accuracy sample. Independent human evaluation remains missing;
the evaluator continues to return release_approved=false unconditionally.

## 2026-10-02 19:18 UTC heartbeat: human-review import integrity

Shifted this bounded run from marginal classifier variants to evaluation-data
integrity. The existing pilot importer accepted reviewer aliases as independent,
nonempty but invalid completion timestamps, and duplicate manifest IDs. Added
regression cases first: 10 failed and 8 passed on the old implementation. After
the fix all 18 passed. Before/after JUnit evidence is retained under research/data/
review-integrity-{before,after}-20261002.xml; hashes and counts are recorded in
research/results/review_integrity_20261002.json.

Distinct-reviewer checking now compares Unicode NFKC-normalized, trimmed,
casefolded keys. Original identities are preserved in exports/reports, and exact
row/header identity consistency remains required. Completion timestamps for
reviewed and skipped items must parse as calendar-valid timezone-aware ISO
datetimes. Duplicate manifest IDs fail validation even for identical contents.
README documents these compatibility rules and limits. No pilot text, IDs,
rubric, annotation provenance or labels changed. Human review count remains zero;
these checks cannot authenticate people, prove independence or truthful timestamps,
or make consensus into independent gold. Pilot remains development-only.

GPT-6 Astra Medium reviewed the source-only validation design using the terminal
client; advice is research/data/review-integrity-advice-20261002.txt. Initial test
commands found pytest absent in global and legacy Python; installed pinned
pytest 8.3.5 in the existing isolated research/checkpoints/stance-runtime environment,
without modifying either other runtime. Test output records Python/tool environment.
No model training, calibration, reserved-test use, or production deployment.

Public-site smoke checks used the local Chromium fallback on the same three
ordered training examples as the dual-axis run. All returned HTTP 200 and the
same LEFT/LEFT/CENTER scores; no page errors, request failures or mobile overflow.
Mobile screenshot inspected. Raw responses/screenshots are in
outputs/live-browser-review-integrity-20261002; sanitized outputs and screenshot
hashes are included in the integrity result. These are functional checks only,
not classifier accuracy evidence. High accuracy remains unproven, with independent
task-matched human judgments still the central missing evaluation input.

## 2026-10-02 18:13 UTC: fixed lexical/semantic hybrid training CV

Trained ten new classifier heads: five semantic-only and five hybrid models,
using the same 115 training IDs and five frozen event-string-grouped folds as
the footer experiment. Reused five hash-verified word-model baselines and their
fold-local TF-IDF vocabularies. Settings were fixed before fitting: logistic
C=1, balanced classes within each training fold, seed 20261001, max_iter=1000,
lbfgs. Hybrid features concatenate TF-IDF and frozen MiniLM vectors, each scaled
by 1/sqrt(2). All word rows were checked to be nonzero and unit L2 norm in every
fold; semantic rows were finite unit vectors. Equal block norms do not establish
equal influence or equivalent regularization across representations.

Only the training member of the existing NPZ was loaded. Its full container and
metadata were hashed, but validation vectors were not indexed. No validation
partition or reserved test was opened. Source/feature hash and ID alignment,
split uniqueness, event-string separation and complete OOF coverage were checked.
Frozen encoder revision/pooling/windowing, runtime versions, model hashes,
fold IDs and all 345 OOF predictions/probability vectors are retained.

| Training OOF result | Word | Semantic | Hybrid |
| --- | ---: | ---: | ---: |
| Released-label matches /115 | 58 | 58 | 59 |
| Agreement | .5043 | .5043 | .5130 |
| Macro-F1 | .4423 | .4794 | .4847 |
| Unanimous matches /54 | 25 | 25 | 25 |
| Center recall | .1538 | .3462 | .3077 |

Against word predictions, semantic corrected 17 errors and regressed 17;
hybrid corrected 12 and regressed 11. An interim commentary mistakenly said
8/7 for hybrid; corrected immediately after calculating the saved-prediction
counts. Maximum solver iterations across all heads was 16, below the limit.
The one-example net gain does not establish improvement or justify deployment.
No settings search, calibration or threshold changes followed. Three focused
tests passed (feature scaling/validation and split-integrity checks).

GPT-6 Astra Medium reviewed the design through the installed terminal client;
local advice is research/data/hybrid-cv-advice-20261002.txt. This remains exploratory
training OOF evidence affected by prior development choices, disputed labels,
possible shared event families and unknown encoder pretraining overlap. Corpus
revision b193ee173936b281183ca1dc101ae4de215a0e5c and noncommercial research-only
restrictions remain unchanged. Independent human product evaluation is missing.

Evidence: research/results/hybrid_cv_20261002.json; fitted models and pre-fit
protocol in research/checkpoints/hybrid-cv-20261002/. A one-off report-enrichment
command initially failed with a SyntaxError before writing; corrected and rerun.
Production was not changed. Local Chromium fallback (154.0.8037.95) submitted
ordered training examples 4-6 to the public site. All returned HTTP 200 and LEFT;
no page errors, failed requests or mobile overflow. Mobile screenshot inspected.
This is functional production smoke coverage, not evaluation of the new models.
Raw responses/screenshots: outputs/live-browser-hybrid-20261002; sanitized browser
summary and screenshot hashes: research/results/hybrid_browser_20261002.json.

## 2026-10-02 16:53 UTC: deployed confidence and abstention audit

Audited all 66 stored development responses against their hash-matched snippet
references. No training, calibration, threshold selection, or reserved-test
access. Added a fail-closed alignment/simplex/argmax validator and fixed-threshold
confidence audit with eight unit tests. GPT-6 Astra Medium reviewed the design
through the terminal client; advice is retained locally in
research/data/confidence-audit-advice-20261002.txt. No competing research process
or pre-existing uncommitted changes was found before work began.

Raw argmax agreement is 31/66 (.4697), while mean maximum score is .9761.
Displayed decisions differ: production classified 65/66 (.9848 coverage), with
30/65 reference matches (.4615), and abstained on one raw-correct prediction.

| Fixed maximum-score threshold | Retained | Matches | Coverage | Agreement |
| --- | ---: | ---: | ---: | ---: |
| .50 | 65 | 30 | .9848 | .4615 |
| .80 | 64 | 30 | .9697 | .4688 |
| .90 | 61 | 29 | .9242 | .4754 |
| .95 | 59 | 29 | .8939 | .4915 |
| .99 | 53 | 25 | .8030 | .4717 |
| .999 | 24 | 8 | .3636 | .3333 |

Top-label ECE with ten fixed equal-width bins is .5217; confidence/correctness
rank AUC is .4286 (ties receive half credit). Multiclass Brier sum is 1.0417
(range 0-2); natural-log NLL is 3.6076, using rounded stored probabilities and
a 1e-12 clipping floor. ECE is a noisy descriptive statistic on this small set,
not a population estimate. Unanimous subset results are separately preserved:
13/33 raw matches, mean score .9615, ECE .5980, rank AUC .3346. Subgroup coverage
denominators are the subgroup size, not the full corpus.

Even an oracle selecting correct predictions first cannot exceed 31/53=.5849
agreement while retaining at least 80% of these 66 unchanged predictions.
This finite-sample bound is not an achievable confidence policy or a bound on
future models. Raising confidence thresholds is not supported as a remedy.
Two-annotator disagreement, source/task mismatch and repeated development use
remain caveats; this is not independently demonstrated product accuracy.

Public-site browser recheck selected the highest-score mismatch, highest-score
match, and lowest-score case from this audit (explicit diagnostic selection).
Local Chromium fallback was used because no cloud-browser tool was exposed.
All three returned HTTP 200 and exactly reproduced stored scores. The low-score
case displayed "No reliable label"; high-score cases remained classified.
No page errors, failed requests, or mobile overflow; mobile screenshot inspected.
Raw audit/screenshots: outputs/live-browser-confidence-20261002. Sanitized browser
summary and screenshot hashes: research/results/confidence_browser_20261002.json.

Metric formulas, full ID-aligned probabilities, displayed decisions and source/
model hashes are retained in research/results/confidence_audit_20261002.json.
Original corpus revision b193ee173936b281183ca1dc101ae4de215a0e5c, source labels,
splits and noncommercial restrictions remain unchanged. No deployment or release
approval. Next model work must improve task-matched discrimination, not merely
increase abstention or present high scores as validated confidence.

## 2026-10-02 05:59 UTC: original human-rating dual-axis baseline

Recovered 230 original party-sentiment ratings for the 115 training IDs from
the corpus main-task CSV. The main annotation template encodes Republican
positive sentiment positively but Democratic positive sentiment negatively:
Republican valence = q1/5, Democratic valence = -q2/5. Decoding their difference
reproduces every saved individual worker label. Decoding the true mean axes
also reproduces all 115 released training labels. This is a mapping check,
not predictive accuracy. No worker identifiers were retained.

The source CSV initially failed UTF-8 decoding; Latin-1 was used to recover
ASCII IDs and numeric fields. The full source CSV was scanned and hashed,
with rating processing restricted to the training-ID allowlist. Nontraining
ratings were not retained or used. Neither validation nor reserved-test
partition files were opened. Retained source assignment statuses are 145
Approved and 85 Submitted; no new human adjudication occurred.

Reused the previous five event-string-grouped folds and verified hashes of
their fitted TF-IDF vectorizers. Fit five two-output Ridge heads (alpha=1,
solver=lsqr) on mean human valences. The fixed, untuned Center threshold is
absolute axis difference <= .125, half the .25 minimum nonzero two-worker
mean difference increment. All 115 articles have one out-of-fold prediction.

| Training cross-validation metric | Dual-axis Ridge | Prior logistic |
| --- | ---: | ---: |
| Released-label matches /115 | 34 | 58 |
| Agreement | .2957 | .5043 |
| Macro-F1 | .2855 | .4423 |

Ridge predicts Center for 81/115 articles. Left/Center/Right recall is
.1842/.6923/.1765. Republican/Democratic valence MAE is .2700/.2478,
worse than the always-neutral baseline (.2478/.2304). Reject this candidate;
no threshold search or deployment. This negative result does not establish
that party-affect modeling in general cannot work. GPT-6 Astra Medium reviewed
the bounded method through the installed terminal client; review is retained
locally at research/data/dual-axis-advice-20261002.txt.

Evidence: research/results/dual_axis_cv_20261002.json contains rating provenance,
fold IDs, hashes, parameters, raw predictions and runtime versions. Five fitted
models and protocol are local in research/checkpoints/dual-axis-cv-20261002/.
Six new unit tests cover sign, threshold, invalid ratings, training-ID filtering
and label reconstruction. Corpus revision b193ee173936b281183ca1dc101ae4de215a0e5c
and its noncommercial license still apply; all candidate artifacts are research-only.
Event-string grouping does not establish event-family independence.

Production browser testing used local Chromium 154.0.8037.95, not a cloud browser.
The first three ordered training examples returned HTTP 200 and LEFT/LEFT/CENTER;
there were no page errors, failed requests or mobile overflow. Mobile screenshot
was visually inspected. Raw audit/screenshots are in outputs/live-browser-dual-axis-20261002;
sanitized summary and screenshot hashes are research/results/dual_axis_browser_20261002.json.
This is functional smoke coverage, not an accuracy estimate. No high-accuracy
claim or production change is warranted; independent human evaluation remains missing.

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
