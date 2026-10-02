# Reproducible bias-classifier experiments

These are working research notes and tools, not a final report or an approved model release.
Scope: English U.S. political news ideology. Political leaning is separate from factual accuracy and loaded language. Nonpolitical input and insufficient evidence are not CENTER.

## October 2 implementation and evaluation contract

The primary target is the **article author's political framing in the supplied
text**, not merely explicit endorsement of a policy. Relevance, whose view is
expressed, insufficient evidence and mixed positions are distinct axes. No stated
policy preference does not establish centrist ideology. Phrase evidence is a
separate task; an article-level label is never inherited as a phrase-level label.

The 66 corpus validation items have been reused for development. Do not perform
another winner-selection round on them. The 89 reserved items remain sealed;
training-only grouped experiments can proceed without opening those files. The
new bounded linear comparison joins the previously reviewed shared-episode
training aliases before group assignment, but this is not an exhaustive episode
audit or a new independent benchmark. CC-BY-NC-SA corpus-derived artifacts remain
noncommercial research until deployment rights are resolved.

The original PoliticalBiasCorpus annotation interface displayed title and three
excerpts, and also encouraged annotators to consult full articles and event
background (with party-principle context available). Actual extra-context usage
is unknown. The model's snippet reconstruction therefore does not establish fully
matched human/model information. Historical result files are retained unchanged.
Source: [pinned annotation interface](https://github.com/ksolaiman/PoliticalBiasCorpus/blob/b193ee173936b281183ca1dc101ae4de215a0e5c/mturk_task_templates/BiasLabelMain.html#L103-L108).

Evaluation schema v3 keeps `raw_macro_f1`, `raw_per_class` and
`raw_confusion_matrix` separate from decision-aware `macro_f1`, `per_class` and
`decision_confusion_matrix`. These class metrics use only LEFT/CENTER/RIGHT
reference rows. Abstention counts as a missed correct prediction for class
recall/F1. `political_selective_accuracy` uses accepted political-reference rows;
`political_coverage` uses all political-reference rows. The legacy
`selective_accuracy`, `accepted_n`, `eligible_n` and `coverage` names remain
political-only aliases, not all-input metrics.

`all_accepted_n` counts every classified input, and `all_input_coverage` divides
that count by all inputs. This is classified-label coverage: a valid abstention
is a processed response but does not count as an accepted label.
`all_accepted_reference_match` divides exact accepted
label/reference matches by every accepted input, including NONPOLITICAL and
UNCERTAIN. UNCERTAIN is not reliable negative gold, so a nonmatch there does not
establish a classification error. Report its `uncertain_acceptance_rate`
separately; the legacy `uncertain_false_label_rate` is only an alias for that
acceptance rate. `accepted_reference_match_excluding_uncertain` uses the explicit
`non_uncertain_accepted_n` denominator, retaining accepted NONPOLITICAL false
labels and excluding UNCERTAIN. Exclusion does not establish the validity of the
remaining references. The `full_population_decision_confusion_matrix` contains
all five reference rows and LEFT/CENTER/RIGHT/ABSTAIN prediction columns, even
for empty input. These rates describe the supplied evaluation mix, not
representative traffic. Calibration/test model bindings, preprocessing versions,
label mappings and modes must match; malformed or nonfinite logits fail closed.
Marginal Wilson intervals are diagnostic only and do not account for correlated
episodes or repeated model selection.

The historical point-estimate goals are provisional. Before independent testing,
freeze the full protocol: task/input context, human annotation provenance,
candidate/checkpoint/prompt/preprocessing, coverage policy, per-class and slice
supports, independent cluster counts, an all-population accepted-label criterion,
uncertainty acceptance treatment, minimum meaningful improvement and interval
decision rules. No all-population or uncertainty threshold may be invented after
viewing final-test outcomes. The evaluator's `uncertainty_protocol_frozen` and
`all_population_acceptance_criterion_frozen` gates deliberately remain false
until a reviewed protocol is implemented. It never approves a release. A perfect
raw classifier cannot pass product recall by abstaining on its difficult class, and 89 old corpus
items cannot certify contemporary end-to-end performance.

See [phrase evidence implementation](PHRASE_EVIDENCE.md) for the experimental
highlighting contract and its separate inference and fidelity blockers.

## Completed evidence

October 2 audit correction: PoliticalBiasCorpus partitions are disjoint by
normalized **event string**, not demonstrated independent event families. A shared
Franken-allegations episode crosses train/validation under different subevent
descriptions, and publisher boilerplate crosses both partitions. Frozen partitions
and old results remain unchanged. See `results/development_overlap_review_20261002.json`
and the experiment log; the reviewed exclusion sensitivity is not a new benchmark.

See EXPERIMENT_LOG.md and results/. Results from the old session are explicitly marked when raw outputs were lost. New experiments preserve per-example predictions without redistributing article text. The public Baly dataset may overlap existing checkpoint training, so its scores are exploratory. No independent human-reviewed final test has been completed.

## Structured stance comparator

The offline Astra Medium comparator separates author stance from attributed
positions. It is not wired into production and its outputs are not human labels.
Use an isolated Python environment with `research/stance_requirements.txt`.
The preserved October 2 protocol is `results/structured_validation_protocol_20261002.json`.

```bash
python research/scripts/stance_contract.py --input research/data/pbc-snippets-20261001/validation_blind.json --output research/data/NEW-STRUCTURED-RUN
python research/scripts/evaluate_structured_stance.py --data research/data/pbc-snippets-20261001/validation.jsonl --directory research/data/NEW-STRUCTURED-RUN --previous research/results/corpus_comparison_20261001.json --output research/results/NEW-STRUCTURED-COMPARISON.json
python -m unittest discover -s tests -p 'test_*stance*.py' -v
```

The evaluator retains MIXED and INSUFFICIENT in the denominator and five-column
confusion matrix. Conditional three-way agreement is only a secondary metric with
explicit coverage. It verifies raw-output hashes, exact evidence spans, all IDs
and blinded/reference text identity. Released-label agreement is not independent
product accuracy, particularly given the corpus's disputed-label resolution.

## Environment and data

From the repository root, use Python 3.12. Install CPU PyTorch from its CPU wheel index first, then `pip install -r research/requirements.txt` and `pip check`. GPU runners need the matching PyTorch build. Use a separate virtual environment. Never patch installed package compatibility checks.

```bash
git clone https://github.com/ramybaly/Article-Bias-Prediction ../research-data
git -C ../research-data checkout ced8111a720948e6a410e52031ace99c4e53f096
python research/scripts/prepare_data.py --repository ../research-data --output research/data --manifest research/results/data_manifest.json
python research/scripts/train_baseline.py --data research/data --output research/results
python research/scripts/compare_context.py --repository ../research-data --output research/results/context_comparison.json
```

Data preparation reserves published test domains first, validation second, training last, grouping subdomains by registrable domain using the bundled public suffix data. Exact normalized duplicates are removed. Publisher-domain separation does not prove separation of media ownership, syndicated stories, near duplicates, events, or time. Those audits remain outstanding. Test is prepared for reproducibility but its predictions are not used to select models or tune thresholds. Raw article text and trained weights are git-ignored. Dataset rights need review before any redistribution or commercial training.

The corrected split has 23,603 training, 2,356 validation, and 1,300 test articles. Validation is skewed (1,640 LEFT, 618 CENTER, 98 RIGHT). Macro F1 and per-class recall are necessary; overall accuracy alone is misleading.

## Retraining

```bash
python research/scripts/train_transformer.py --base FacebookAI/roberta-base --revision EXACT_BASE_COMMIT --data research/data --output research/checkpoints/run-001 --device cuda
```

Replace EXACT_BASE_COMMIT with the verified immutable model revision. An empty output directory is required. The script uses article-normalized window losses, deterministic seeds, gradient clipping, AdamW, validation macro-F1 checkpoint selection and early stopping. It never opens test.jsonl. All windows are processed; articles over the serving window limit fail explicitly. Window labels inherited from article labels are noisy. This is a reproducible starting experiment, not evidence that this objective improves accuracy. A tiny random model smoke run verified training and checkpoint serialization only. Full transformer retraining has not been run on this CPU-only session.

## Evaluation and calibration

New evaluation reports and calibration policies must include complete
`inference_runtime` schema 1 metadata: exact torch/transformers/tokenizers,
window-preparation implementation, observed device/dtype/attention backend and
batch size. Calibration checks it before fitting; offline policy evaluation and
serving require exact identity equality. Missing or partial legacy identities
are rejected even when both sides omit them. Keep historical reports unchanged;
regenerate evaluation under the intended runtime rather than assigning newer
versions to old results. See [Python security review](../docs/python-security.md).


```bash
python research/scripts/evaluate.py --input research/data/valid.jsonl --model bias_model --split validation --output research/results/current_validation.json
python research/scripts/calibrate.py --validation research/results/human_validation.json --output research/checkpoints/candidate_policy.json
```

Evaluation JSONL requires unique id, text, label (LEFT/CENTER/RIGHT/NONPOLITICAL/UNCERTAIN), and preferably source/source_group. Keep annotation provenance separately and pass `--annotation-record`. A real provenance record contains `human_reviewed: true` and a reference to the completed annotation log. Never create that assertion for unreviewed data. Calibration requires documented human-reviewed validation, uses validation logits only, and refuses to produce a policy if the requested accuracy/coverage pair is unattainable. It always leaves `release_approved: false`.

Before approval, evaluate candidate thresholds offline on a separate frozen human-reviewed test set, preserving candidate decisions and coverage. The current evaluator reports deployed policy decisions, which correctly remain abstentions for unapproved models. Use `evaluate_policy.py --test TEST_REPORT --validation VALIDATION_REPORT --policy CANDIDATE_POLICY --output OUTPUT_JSON` for an offline threshold simulation. It checks exact test/validation overlap, model binding and proposed point-estimate gates, but never approves a policy. Confidence intervals, source/event/time audits and a trained relevance stage remain outstanding. Do not flip release_approved to bypass those steps.

## Annotation and release gates

1. Collect contemporary, licensed English news across publishers, dates, topics and genres, plus nonpolitical hard negatives. Deduplicate exact text, near duplicates and syndicated/event clusters. Freeze separate annotation, validation and final-test manifests before model selection.
2. Use two independent annotators with adjudication. Record agreement, disputed cases, spans and rationales. Distinguish the author's framing from quoted views; record mixed/ambiguous texts as UNCERTAIN. CENTER requires sufficient relevant evidence, not an absence of political keywords.
3. Train and validate political relevance separately from ideology. Include recipes, sports, local events, ordinary policy descriptions, quotations, satire, short inputs, long articles and mixed viewpoints. Preserve a relevance test set.
4. Calibrate on validation only. Freeze checkpoint, preprocessing, aggregation, thresholds and accepted modes. Sentence-level support needs sentence-specific annotation and evaluation; an article benchmark does not validate it.
5. Proposed targets: macro F1 >= .85, each ideology recall >= .80, political-only accepted-label accuracy >= .90 at political-reference coverage >= .80, nonpolitical false-label rate <= .05. These are goals, not achieved performance. Report denominators, confidence intervals and slice results. All-population accepted-label and uncertainty criteria, acceptance thresholds and sample sizes must be agreed before final testing.
6. Test operational behavior in staging: actual model load, hashes, repeatability, frontend/API compatibility, long inputs, response time, memory, health checks, URL-fetch egress restrictions and rollback. Deploy frontend and backend together because the response contract changed.

No automated policy approval, VPS deployment, relevance model, final accuracy claim or formal report is included in this branch.

## Deployed controlled-input diagnostics

`python research/scripts/probe_live_pilot.py --output research/results/live_controlled_probe_YYYYMMDD.json` probes the 40 original controlled examples sequentially and checkpoints each response. It stops after three consecutive failures. `summarize_live_probe.py --input RESULT_JSON --output SUMMARY_MD` summarizes completed observations without computing accuracy. These predictions are intentionally outside the reviewer interface. Reviewers should not inspect them before annotation; disclose any prior exposure in the evidence notes. This is development diagnostics, not independent evaluation.
# October 1 research continuation

See `EXPERIMENT_LOG.md` and `results/corpus_comparison_20261001.json` for the
matched-context live, Astra, TF-IDF, frozen MiniLM and partial fine-tuning runs.
No candidate passed the high-accuracy goal. All new artifacts are research-only.

Reproduction entry points (run from repository root with the recorded dependencies):

```bash
python research/scripts/corpus_experiment.py prepare --input /path/to/PoliticalBiasCorpus --output research/data/new-corpus
python research/scripts/corpus_experiment.py train --input research/data/new-corpus --output research/checkpoints/new-tfidf
python research/scripts/astra_baseline.py --input research/data/new-corpus/validation_blind.json --output research/data/new-astra
python research/scripts/live_corpus_probe.py --input research/data/new-corpus/validation.jsonl --output research/data/new-live.json
python research/scripts/embedding_experiment.py download --output research/checkpoints/new-minilm
python research/scripts/embedding_experiment.py encode --data research/data/new-corpus --checkpoint research/checkpoints/new-minilm --output research/data/new-features.npz
python research/scripts/embedding_experiment.py train --data research/data/new-corpus --features research/data/new-features.npz --output research/checkpoints/new-head
python research/scripts/finetune_minilm.py --data research/data/new-corpus --checkpoint research/checkpoints/new-minilm --output research/checkpoints/new-finetune
python -m unittest discover -s tests -p test_corpus_experiment.py -v
```

Pin the source corpus to the commit recorded in the log. The Astra experiment
requires an authenticated Codex client and uses account inference capacity.
Its prompt is fixed in the script; only ID/text records are supplied. It is an
offline research comparator, not a production API implementation.
The summarizer currently uses the October 1 experiment directory names.
The browser runner uses `NODE_PATH` for Playwright, `BIASCHECK_TEST_BROWSER` for
Chromium, and optional `BIASCHECK_DISABLE_WEBGL=1` for the documented fallback.
It takes an ID/text JSON array and a screenshot/output directory as arguments.
