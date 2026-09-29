# Reproducible bias-classifier experiments

These are working research notes and tools, not a final report or an approved model release.
Scope: English U.S. political news ideology. Political leaning is separate from factual accuracy and loaded language. Nonpolitical input and insufficient evidence are not CENTER.

## Completed evidence

See EXPERIMENT_LOG.md and results/. Results from the old session are explicitly marked when raw outputs were lost. New experiments preserve per-example predictions without redistributing article text. The public Baly dataset may overlap existing checkpoint training, so its scores are exploratory. No independent human-reviewed final test has been completed.

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
5. Proposed targets: macro F1 >= .85, each ideology recall >= .80, accepted-label accuracy >= .90 at coverage >= .80, nonpolitical false-label rate <= .05. These are goals, not achieved performance. Report denominators, confidence intervals and slice results. Acceptance thresholds and sample sizes must be agreed before final testing.
6. Test operational behavior in staging: actual model load, hashes, repeatability, frontend/API compatibility, long inputs, response time, memory, health checks, URL-fetch egress restrictions and rollback. Deploy frontend and backend together because the response contract changed.

No automated policy approval, VPS deployment, relevance model, final accuracy claim or formal report is included in this branch.
