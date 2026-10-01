# PoliticalDEBATE comparison, 2026-09-29

Development data, not an independent release test. Exactly the earlier 60 Baly
articles were reused, 20 per media-ideology class. Their labels describe media
ideology, not expert annotation of each author's expressed stance. Upstream
training overlap is unknown. No held-out test labels were used to train a model.

| Configuration | Accuracy | Macro F1 |
| --- | ---: | ---: |
| Original RoBERTa, first window | 73.33% | 0.7298 |
| Original RoBERTa, full-document weighted windows | 68.33% | 0.6718 |
| PoliticalDEBATE large, five fixed hypotheses, first paired window | 48.33% | 0.4831 |

The new candidate is **not a demonstrated replacement** for the original article
classifier. Short-input improvements do not imply improved article accuracy.
PoliticalDEBATE's semantic hypotheses target textual endorsement/nonalignment,
which differs from the corpus label construct. This distinction may contribute to
the result, but does not excuse or establish the cause of the lower score.

Candidate confusion matrix (gold rows and predicted columns: LEFT, CENTER, RIGHT):

| Gold | LEFT | CENTER | RIGHT |
| --- | ---: | ---: | ---: |
| LEFT | 6 | 12 | 2 |
| CENTER | 6 | 13 | 1 |
| RIGHT | 4 | 6 | 10 |

Candidate first paired window reserves space for a hypothesis and uses its own
tokenizer, so it does not consume exactly the same source span as RoBERTa's first
window. These raw-label scores ignore abstention. They do not evaluate the v2
mixed-position guard or the application’s full-document aggregation.

## Exploratory agreement analysis

Post hoc agreement between candidate and original first-window labels retains
26/60 articles (43.33% coverage), with 23/26 correct (88.46%) on this same sample.
Agreement with the original full-document labels retains 23/60 (38.33% coverage),
with 20/23 correct (86.96%). This is an exploratory selective-prediction result,
not comparable to all-input accuracy and not a validated production policy. Both
models can agree on an error. An agreement gate was not deployed or enabled.

Freeze a proposed agreement policy, then evaluate relevance, coverage, class
recall and selective error on a new, construct-matched human-labeled holdout
before adopting it. The current default remains RoBERTa with unvalidated labels
withheld; the alternative is explicitly opt-in and tentative.
