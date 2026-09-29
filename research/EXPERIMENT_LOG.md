# Working experiment log (not a final report)

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
