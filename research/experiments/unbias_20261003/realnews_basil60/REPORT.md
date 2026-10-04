# UnBias-Plus real-news evaluation

Completed 2026-10-04T01:14:07.361011+00:00. Candidate: pinned Qwen3-8B-UnBias-Plus-SFT-Instruct-V2, locally converted Q4_K_M via Q8_0.

**Recommendation: do not deploy the unchanged candidate as the website's precise political-framing highlighter.** It detects some annotated wording, but broad spans, missed references, API failures and unsupported speaker attribution remain material limitations. The experimental endpoint remains disabled by default and the website was not changed.

This evaluates the existing integration on **60 real news sentences from 60 events**, using BASIL's published human annotations. It is a small, stratified, archival evaluation of agreement with those references, not an overall real-world accuracy figure or a LEFT/RIGHT classifier test.

| Test group | Passages | Result |
|---|---:|---|
| Lexical bias, including loaded wording | 20 | At least one human-labeled lexical word covered in 17/20 passages; any highlight returned in 17/20 |
| Informational bias only | 20 | At least one human-labeled word covered in 11/20 passages; any highlight returned in 12/20 |
| No human bias annotation | 20 | 1/20 received highlights; 15/20 completed cleanly with no suggestions; 4 requests failed |
| API reliability, all groups | 60 | Complete responses: 52; partial failures: 1; failed requests: 7 |

Absence of a BASIL annotation is a reference negative, not proof of objective neutrality. Failed negative requests are not successful neutral readings. The delivered-output sentence confusion matrix treats failures as no delivered highlights; the reliability-adjusted correct-complete count below avoids giving failed negatives credit.

## How precise are the highlights?

| Measurement against published human spans | Result |
|---|---:|
| Word-token precision | 42.1% (175 matching / 416 highlighted tokens) |
| Word-token recall | 46.1% (175 covered / 380 reference tokens) |
| Word-token F1 | 0.440 |
| Lexical word-token recall alone | 81.8% (27/33) |
| Exact span boundary matches | 3 matches; 51 predicted spans; 41 reference spans |
| One-to-one word-overlap matches, lenient | 28/41 reference spans |
| One-to-one span token IoU at least 0.5 | 9/41 reference spans |

Precision is agreement of highlighted tokens with reference tokens. It is not model confidence, and tokens outside human spans are not automatically proven neutral. A very broad highlight can have good recall but poor precision. Exact boundary misses are also not equivalent to wholly incorrect bias detection. The matching implementation prevents one broad highlight from claiming multiple independent span detections.

| Token agreement within each group | Precision | Recall |
|---|---:|---:|
| Lexical-containing sentences, against all their reference spans | 16.9% | 87.2% |
| Informational-only sentences, context-limited | 88.7% | 40.2% |

The group breakdown matters: long informational reference spans can contribute many more tokens than short lexical cues. The overall micro score therefore cannot describe lexical highlighting on its own.

Conditional 95% percentile intervals from 2,000 stratified, event-level bootstrap samples: precision 28.8% to 56.4%; recall 28.8% to 64.3%; F1 0.296 to 0.582. These reflect uncertainty in this sampled corpus, not all future news.

## Quotations and attribution

The sample has 19 human spans marked as quoted. Accepted highlights cover at least one word in 16 of them, compared with 13/22 nonquoted reference spans. This is reference coverage, not a quotation-classification score.

**0 of 51 accepted highlights have usable speaker attribution.** The native adapter reports unknown attribution. No speaker-attribution accuracy can be claimed. Highlighting a quotation does not establish that the journalist endorses it.

## Sentence-level detection and failures

Across the artificially balanced groups, the delivered-output confusion matrix is TP=29, FP=1, FN=11, TN=19. Sentence precision is 96.7%; recall is 72.5%; F1 is 0.829. Control highlight rate is 5.0%, with Wilson 95% interval 0.9% to 23.6%.

Only **43/60 requests both completed without partial/request failure and agreed with reference bias presence**. In the separate 40-case lexical/control slice, 31/40 both completed correctly and agreed with reference bias presence. Its delivered-output accuracy alone is 90.0%, but that credits failed negative requests as no delivered highlight and must not be reported as successful service accuracy. Constant always-highlight or never-highlight baselines each score 50% on this balanced slice. These are trivial sanity baselines, not a comparison with another trained model. The old article classifier predicts a different target, so no superiority claim is made.

Sentence-level agreement measures whether any highlight was returned, not whether that highlight covers the correct words. The phrase metrics above are essential for interpreting it.

Rejected individual spans: 1. API request failures are recorded as HTTP/service failures, not silently converted to no-suggestion success. The client exposes a generic invalid-or-unavailable-response reason; the run does not preserve native completions for failed requests, so the precise cause cannot be assigned to generation, schema checking or runtime transport from these records alone. Failure diagnosis requires a separate, labeled diagnostic and must not replace these recorded outcomes.

Complete-success-only sensitivity metrics are retained in `summary.json` when failures occur. They exclude failed cases and should not replace the all-request view.

## Response time

| CPU timing | Seconds |
|---|---:|
| First request | 60.54 |
| Median, all requests | 15.78 |
| Median, excluding first request | 15.19 |
| 90th percentile | 34.01 |
| 95th percentile | 35.48 |
| Maximum | 60.54 |
| Total including startup | 1083.04 |

These are isolated CPU API timings on short, 15-80-word sentences with prompt caching. They include failed requests. They do not predict full-article latency, concurrent service capacity, startup of both website models, or a production proxy's timeouts.

## What this establishes and what it does not

- References came from prior human annotation, unchanged. BASIL's paper describes two annotators working independently and then discussing disagreements. No new human review or assistant-authored gold labels were added here.
- The source contains 300 articles and 7,984 body sentences. Release 2 has 1,723 valid body spans plus three title spans, unlike the original paper's 1,727-span total. All body offsets validated. Titles were excluded. Source publisher counts in this sample are Fox News 20, New York Times 23 and Huffington Post 17; dates span 2010-2019.
- No eligible sentence shared a normalized 13-word sequence with the released 5,000-article V2 training snapshot; none of the selected 60 was an exact normalized training substring. This cannot rule out base-model exposure, undisclosed data, paraphrases or event overlap. The training snapshot postdates the pinned model.
- BASIL is about bias toward entities; UnBias has a broader native taxonomy. Human annotators saw full articles and compared reporting across three sources, while this test sends one sentence. Informational-bias results are especially limited by that context mismatch.
- The candidate and protocol were frozen before inference. No prompt or endpoint changes were made, and all 60 requests were retained. Seven measurement tests passed. The tests validate scoring mechanics, not the model.
- The balanced sample is too small and too old to establish deployment accuracy. It also cannot evaluate whether the system identifies LEFT versus RIGHT or whether nonpolitical material is properly excluded.

## Recommended action

Keep production unchanged. The current candidate is unsuitable as-is for precise, attributed political highlighting. Its lexical sensitivity is a reason to retain it as a research candidate, not to ship it.

If continuing development, first diagnose the recorded API failures and narrow oversized spans, then add an explicitly evaluated attribution stage. Any adapted version must be evaluated separately with appropriate article context on a new, frozen set; these 60 cases now become development evidence. Do not keep testing the identical candidate merely to seek a more favorable score.

## Saved evidence

- `PROTOCOL.md`: frozen selection, candidate and measurement rules.
- `sample_manifest.json`: source revisions, hashes, IDs, original reference offsets and overlap audit.
- `summary.json`: complete per-case, text-free prediction offsets, metrics, failures and timings.
- `prepare.py`, `run.py`, `score.py`, `test_score.py`: reproducible selection, real API execution and scoring.
- Full input snapshots and API responses are retained under ignored local research data, bound by hashes. They are not redistributed in this report.

The evaluation is saved locally in the repository. No GitHub upload was attempted in this turn because the previous batch's upload remains blocked. No merge or deployment occurred.

## Sources

1. [BASIL release 2](https://github.com/launchnlp/BASIL/tree/4fdbc4f68d5ddae648990063cb6dd11424d96222)
2. [Fan et al. (2019), In Plain Sight](https://aclanthology.org/D19-1664/)
3. [UnBias-Plus V2 model card](https://huggingface.co/vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2)
4. [Released training snapshot](https://huggingface.co/datasets/vector-institute/unbias-plus-dataset/tree/2e0a842ca594549a510ac527e2222b82d04b9784)
