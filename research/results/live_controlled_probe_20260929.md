# Deployed controlled-input diagnostics

This is an unlabeled synthetic stress test, not a measurement of real-world accuracy.
The review page does not load this report. Reviewers should avoid these predictions until their independent judgments are submitted.

Run started: 2026-09-29T16:42:10.217254+00:00
Endpoint: https://bias.r4him.tech/api/predict
Completed responses: 40 / 40 attempted.
Observed label counts: {'LEFT': 40}
Top raw score at least .95: 34 successful responses.
Median observed request duration: 6.43 seconds.

The legacy health endpoint does not identify the checkpoint or runtime. Request durations include network and server time; they are not a controlled latency benchmark.

| Controlled case | Returned label | Top raw score |
|---|---|---|
| Dinner description | LEFT | 0.992506 |
| Conservative repair estimate | LEFT | 0.988268 |
| Liberal amount of glue | LEFT | 0.996496 |
| Left/right door directions | LEFT | 0.995681 |
| Public healthcare and progressive taxation | LEFT | 0.808399 |
| Lower taxes and deregulation | LEFT | 0.905294 |
| Attributed higher-tax quotation | LEFT | 0.986674 |
| Attributed lower-tax quotation | LEFT | 0.970259 |
| Single word: Taxes | LEFT | 0.998911 |
| Transparency criticism, Democratic mayor | LEFT | 0.994214 |
| Transparency criticism, Republican mayor | LEFT | 0.998774 |

## Interpretation limits

- Directional labels on clearly ordinary nonpolitical inputs demonstrate an intended-use failure, but this convenience sample cannot estimate the population false-positive rate.
- A very high raw score does not establish correctness or political relevance. Merely raising the confidence threshold can retain such failures.
- Historical deployment parity on a few inputs is not proof that the same checkpoint is still deployed; health provenance is missing.
- No human annotations, calibrated probabilities, final accuracy, or retraining results are produced by this script.
- Next model-development priority remains a validated relevance/insufficient-context stage followed by ideological classification, evaluated separately on human-reviewed data.
