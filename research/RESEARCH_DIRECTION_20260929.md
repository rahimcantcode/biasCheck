# Research direction: relevance, stance, and wording

Working notes, 2026-09-29. This is a proposed experiment plan, not a final report,
implementation, or claim of achieved accuracy.

## Decision

Next candidate: mlburnham/Political_DEBATE_large_v1.0 as an NLI-based political
relevance and stance baseline. It is a different checkpoint and training objective
from the matous-volf political-leaning DeBERTa previously compared. Keep the existing
RoBERTa as a baseline; do not replace production before comparative evaluation.

Separate the decisions: relevance/context sufficiency, political stance, and sentence
loaded language. Do not equate CENTER with irrelevant or uncertain. Distinguish speaker
stance from the article author's framing. Do not blindly average sentence labels.

Political DEBATE is trained on political topic/stance and other NLI tasks. The author
recommends large for zero/few-shot use and reports MIT licensing. These are reasons to
benchmark it, not proof it solves our task. Hypothesis design and fine-tuning require
validation. Large-model CPU latency must be measured on our VPS before deployment.
Source: https://huggingface.co/mlburnham/Political_DEBATE_large_v1.0
Paper: https://arxiv.org/abs/2409.02078

APSI demonstrates relevance-first NLI stance analysis with Political DEBATE. Its FAQ
reports only 20 validation texts per dimension and warns about hypothesis dependence.
Do not adopt its numeric threshold or claim its evaluation establishes our accuracy.
Source: https://apsi.sc.hpi.de/faq/

## Sentence highlighting

BABE provides expert word/sentence annotations. The published roberta-babe-ft checkpoint
is for lexical/loaded-language bias, explicitly not political leaning or factuality,
and has a noncommercial license. Use it as a research benchmark only unless deployment
rights are compatible. Sentence classification alone does not localize specific phrases;
phrase highlighting needs span supervision or separately validated attribution.
Sources:
- https://aclanthology.org/2021.findings-emnlp.101/
- https://huggingface.co/mediabiasgroup/roberta-babe-ft

## Existing labels and assisted training

Manual annotation by the user is not a prerequisite for running new baselines. Existing
expert-labeled benchmarks can support initial experiments for their own tasks, provided
training overlap and split provenance are checked. Preserve a separate contemporary,
independently reviewed final evaluation for claims about this product.

The 2025 annolexical paper reports promising classifiers trained on LLM annotations and
evaluated on human benchmarks, with behavioral limitations. This supports testing machine
labels for training augmentation, not treating AI labels as independent gold evaluation.
Source: https://aclanthology.org/2025.findings-naacl.75/

Penn's Media Bias Detector describes LLM article/sentence analysis and ongoing human
verification. This motivates an optional full-context LLM comparison. It does not prove
an LLM is automatically more accurate; its definition of leaning may also encode topic
associations that differ from our authorial-framing rubric.
Source: https://mediabiasdetector.seas.upenn.edu/methodology/

## Evaluation design

Use unseen publishers, deduplicated story/event groups and a temporal holdout. The Baly
paper explicitly evaluates unseen media to reduce source-recognition shortcuts. Never
reuse a checkpoint's training examples as independent test evidence. Report class recall,
macro F1, relevance errors, accepted accuracy and coverage separately. Calibrate after
classification improves; temperature scaling alone cannot correct a wrong argmax.
Sources:
- https://aclanthology.org/2020.emnlp-main.404/
- https://arxiv.org/abs/1706.04599

## Concrete next experiments

1. Pin Political DEBATE model revision and verify label mapping/loading. Construct short,
symmetric hypotheses separating topic relevance from author-endorsed policy positions.
2. Compare with RoBERTa on matched article and short-input sets. Include nonpolitical hard
negatives, procedural political reporting, quotations, negation and mixed positions.
Treat our 40 controlled cases as development diagnostics, not a held-out accuracy test.
3. Evaluate BABE-compatible sentence classification separately on documented held-out
expert labels. Do not report BABE lexical-bias scores as LEFT/RIGHT accuracy.
4. If needed, fine-tune on task-matched data; machine-assisted labels may augment training.
Keep human-reviewed evaluation independent from teacher models and training data.
5. Tune abstention and calibration on validation, freeze the pipeline, then evaluate the
final held-out set. Only a passing candidate proceeds to VPS latency/staging checks.

No model was downloaded, trained, swapped, or deployed in this research-only step.
