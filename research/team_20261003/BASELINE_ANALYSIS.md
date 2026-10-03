# Baseline replay and next model experiment

Date: 2026-10-03. Source state: research branch based on `4268bab`.

## What this work establishes

The existing accuracy problem is reproduced in the saved predictions. It is not
resolved by better JSON formatting, a high number of software tests, or simply
discarding all disputed training labels. Both task/data quality and model
capability remain plausible constraints. These records do not isolate a single
cause or establish current production accuracy.

The new standard-library replay command is:

```sh
python research/scripts/summarize_research_baselines.py \
  --output research/team_20261003/baseline_summary.json
```

It reads exactly ten named publication files and records their SHA-256 hashes.
It independently recomputes 924 article model/example comparisons, 230
out-of-fold model/example comparisons, and 254 phrase experiment/case comparisons.
These are repeated evaluations on small development sets, **not 1,408 independent
examples**. It also checks 548 saved native-stance responses for valid output
structure and aggregate prediction counts.

The script does not import serving code, make model calls, download data or
weights, train anything, access the 89-item or 726-item sealed partitions, modify
historical records, or promote a model. Historic suite names containing
`sealed_transfer` refer to the already published 32 synthetic cases. Those cases
are now development material.

Validation performed:

```sh
.venv-team/bin/python -m pytest -q tests/test_research_baselines.py
```

Result: **11 tests passed**. Tests cover fixed denominators, failed negative cases,
wrong direction/speaker, Unicode occurrences, duplicate/unknown IDs, changed or
missing reported metrics, attempt/prediction status mismatches, and the explicit
publication-only read list. These are audit tests, not model-quality evidence.

## Article classification: 66 reused development examples

The complete generated JSON retains all 14 candidates. The table highlights
previously discussed configurations; it does not select a new winner.

| Historical candidate | Reference matches | Agreement | Macro-F1 | CENTER recall |
|---|---:|---:|---:|---:|
| Original live RoBERTa record | 31/66 | 47.0% | 0.4204 | 2/21 |
| Word TF-IDF, C=1.0 | 39/66 | 59.1% | 0.5432 | 4/21 |
| Frozen MiniLM, C=0.1 | 37/66 | 56.1% | 0.5132 | 4/21 |
| Astra Medium frozen prompt | 35/66 | 53.0% | 0.5214 | 18/21 |
| Fine-tuned MiniLM epoch 3 | 21/66 | 31.8% | 0.2081 | 19/21 |

The original model misses 19 of 21 CENTER references. Conversely, the fine-tuned
model's high CENTER recall accompanies poor overall performance. Neither strong
performance on one class nor an aggregate percentage is sufficient for selection.

Recorded RoBERTa confusion matrix, independently reconstructed from saved rows:

| Reference / prediction | LEFT | CENTER | RIGHT |
|---|---:|---:|---:|
| LEFT | 14 | 1 | 4 |
| CENTER | 6 | 2 | 13 |
| RIGHT | 8 | 3 | 15 |

The source corpus is historical and research-only under its recorded
CC-BY-NC-SA-4.0 license. Human annotators may have used more context than the
reconstructed excerpts supplied to the model. Later source audits also identify
label-resolution and event-overlap concerns. These constrain the interpretation
of reference disagreement. The replay verifies arithmetic, not that every
reference is correct or that splits are independent.

The historical report of 30 disagreements among 59 predictions scored at least
95% is an important confidence warning, but is **not independently recomputed by
this new script**: the selected publication's per-example rows omit scores. Its
summary count is not treated as a newly verified measurement.

## Label-quality sensitivity: 115 training examples, out-of-fold predictions

| Training inclusion rule | Matches | Macro-F1 | LEFT recall | CENTER recall | RIGHT recall |
|---|---:|---:|---:|---:|---:|
| All fit-fold labels | 64/115 | 0.4786 | 21/38 | 4/26 | 39/51 |
| Unanimous fit-fold labels only | 51/115 | 0.4455 | 16/38 | 21/26 | 14/51 |

All 115 evaluation examples remain in both denominators. Filtering to unanimous
labels changes sample size and class composition as well as agreement quality.
It sharply increases CENTER recall while reducing directional recall and total
agreement. **This is not evidence that disputed examples are useless, nor a
causal demonstration that label noise explains the original model's errors.**

The actionable data intervention is adjudication with preserved disagreement and
balanced topic/source coverage. Automatically deleting every disagreement is not
supported by this experiment. Retraining on a very small, skewed subset is also
not a convincing replacement for the original training corpus.

## Phrase extraction: separate task, synthetic development evidence

A correct span must match the exact source position, LEFT/RIGHT direction, and
speaker attribution. Invalid responses remain uncovered cases. Empty valid
responses and failed responses are not interchangeable.

| Experiment / cases | Covered | Recovered expected spans | Correct returned spans | No-expected-span cases with false highlights |
|---|---:|---:|---:|---:|
| Qwen3-4B v2, reused 38 | 34/38 | 11/27 | 11/35 | 9/15 |
| Instruct-2507 v2, reused 38 | 28/38 | 0/27 | 0/28 | 6/15 |
| Instruct-2507 v3, reused 38 | 37/38 | 4/27 | 4/7 | 0/15 |
| Instruct-2507 v4, reused 38 | 38/38 | 25/27 | 25/34 | 7/15 |
| Instruct-2507 v5, reused 38 | 38/38 | 23/27 | 23/31 | 4/15 |
| V4, formerly unseen synthetic 32 | 30/32 | 15/19 | 15/22 | 5/16 |
| V5, same synthetic 32 | 30/32 | 16/19 | 16/22 | 4/16 |

V3's zero false-highlight count conceals very low recovery. V4 substantially
increases extraction but also adds false highlights. V5 trades some false
highlights for regressions on previously correct phrases. Its 84.2% span recall
and 72.7% span precision on the 32 cases are different metrics, neither overall
product accuracy nor evidence from human gold. All 70 distinct synthetic cases
are exposed development data now.

Seven V5 transfer cases are not exact successes. The saved failures include:

- Different speakers using the same phrase: source-context validation fails.
- Negated and quoted occurrences: a missed span and false highlight.
- Simple rejection: a false highlight under the frozen synthetic convention.
- Reported policy facts: one invalid result and one false highlight.
- A quoted string mentioned as text: a false highlight.
- Repeated negated occurrences: two false highlights.

The simple-rejection convention itself needs human rubric review. A plausible
alternative interpretation is not automatically a model failure. More broadly,
synthetic exact boundaries can be debatable, and phrase extraction must not be
presented as an explanation of the separate RoBERTa article classifier.

## Native stance presence: a different question

| Historical candidate | Reported reference matches | False stance calls on no-stance references |
|---|---:|---:|
| Qwen3-4B | 181/274, 66.1% | 79/162 |
| Qwen3-4B Instruct-2507 | 175/274, 63.9% | 89/162 |

These are UK argument stance-presence results, not U.S. LEFT/CENTER/RIGHT
classification. Publication records include each generated response but omit
per-ID reference labels. The new audit verifies the response contracts, counts
predicted labels, and checks those counts against confusion-matrix columns and
reported aggregate arithmetic. It **cannot independently verify which individual
predictions match human labels**. The reported accuracy is therefore explicitly
aggregate-only in the generated JSON. No transcript text or sealed labels were
retrieved to fill this gap.

## Bounded next model experiment, conditional on the new human references

1. Finalize one shared rubric for author framing, source attribution, no
   expressed position, mixed positions, and uncertainty. Do not silently equate
   historical CENTER with nonpolitical or no author stance. Retain original
   historical results under their original task definitions.
2. Complete independent human pilot reviews and adjudication. The pilot may be
   used for development and rubric refinement, not later relabeled as an
   untouched test set. Keep source text, reviewer context, topic/event groups,
   rights, and text/span hashes with each item.
3. Before evaluating candidates, freeze the new development sample and register
   all arms, budgets, prompt/code/model hashes, and stopping rules. The evaluator
   owns the final test partition. Include explicit author/quotation, negation,
   neutral reporting, mixed opinions, and nonpolitical strata.
4. Compare the existing model where its labels are compatible, a simple
   supervised baseline if enough adjudicated training data exists, and one
   stronger instruction model under a common task contract. For phrase quality,
   retain the frozen V5 pipeline as a reference arm and change model capability
   in one bounded arm. An approximately 8B candidate can be investigated only
   after license, actual machine memory, context, and latency checks; no specific
   checkpoint or serving feasibility is asserted here.
5. Measure label quality, phrase precision/recall, attribution, invalid and
   abstention rates, subgroup errors, latency, and memory separately. Show
   coverage alongside selective accuracy. Preserve every output and failed
   case. Use event/source-aware uncertainty and paired comparisons appropriate
   to the frozen protocol, rather than choosing an attractive single score.
6. Consider supervised fine-tuning only after the error analysis shows sufficient
   examples of the failures to learn from. Preserve minority or disputed
   positions through adjudication and uncertainty, not automatic deletion.
   Recalibrate after changing the model or runtime. Final evaluation occurs once
   after the candidate and acceptance criteria are frozen.

No new model winner is selected here. The concrete deliverable is a replayable,
audited baseline and a model experiment that the new human data can support.
Human review and task-matched data are the current dependency; more prompt
tuning on the same 70 examples would not resolve it.

## Evidence files

- `research/team_20261003/baseline_summary.json`: generated counts, metrics,
  per-class details, error IDs/categories, and input hashes.
- `research/results/corpus_comparison_20261001.json`: all 14 historical article
  candidates and their per-example predictions/references.
- `research/results/training_label_provenance_20261002.json`: retained
  references and both out-of-fold prediction sets.
- `research/experiments/phrase_stages_20261002/`: frozen synthetic fixtures,
  recorded outputs, historical source, and existing full replay tests.
- `research/results/argument_stance_*_dev_20261002.json`: raw stance responses
  and aggregate evaluation records, with the verification limit stated above.
