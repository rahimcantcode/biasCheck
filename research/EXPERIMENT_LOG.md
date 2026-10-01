# Working experiment log (not a final report)

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
