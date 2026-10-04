"""Render completed, verified metrics without copying the underlying news text."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def pct(value):
    return f'{value*100:.1f}%'


def interval(value):
    return f'{pct(value[0])} to {pct(value[1])}'


if __name__ == '__main__':
    d = json.loads((HERE/'summary.json').read_text())
    m = json.loads((HERE/'sample_manifest.json').read_text())
    a = d['overall']
    rows = d['rows']
    assert len(rows) == 60 and d['release_approved'] is False
    failures = a['statuses'].get('request_failure', 0)
    partials = a['statuses'].get('partial_failure', 0)
    lex = d['by_stratum']['lexical']
    info = d['by_stratum']['informational']
    controls = d['by_stratum']['unannotated']
    lex_hits = sum(r['lexical_covered_tokens'] > 0 for r in rows if r['stratum']=='lexical')
    info_hits = sum(r['token']['tp'] > 0 for r in rows if r['stratum']=='informational')
    clean = sum(r['status']=='no_suggestions' for r in rows if r['stratum']=='unannotated')
    t = d['latency_seconds']
    ci = d['token_stratified_event_bootstrap95']
    result = f'''# UnBias-Plus real-news evaluation

Completed {d['completed_utc']}. Candidate: pinned Qwen3-8B-UnBias-Plus-SFT-Instruct-V2, locally converted Q4_K_M via Q8_0.

**Recommendation: do not deploy the unchanged candidate as the website's precise political-framing highlighter.** It detects some annotated wording, but broad spans, missed references, API failures and unsupported speaker attribution remain material limitations. The experimental endpoint remains disabled by default and the website was not changed.

This evaluates the existing integration on **60 real news sentences from 60 events**, using BASIL's published human annotations. It is a small, stratified, archival evaluation of agreement with those references, not an overall real-world accuracy figure or a LEFT/RIGHT classifier test.

| Test group | Passages | Result |
|---|---:|---|
| Lexical bias, including loaded wording | 20 | At least one human-labeled lexical word covered in {lex_hits}/20 passages; any highlight returned in {lex['sentence']['tp']}/20 |
| Informational bias only | 20 | At least one human-labeled word covered in {info_hits}/20 passages; any highlight returned in {info['sentence']['tp']}/20 |
| No human bias annotation | 20 | {controls['sentence']['fp']}/20 received highlights; {clean}/20 completed cleanly with no suggestions; {controls['statuses'].get('request_failure',0)} requests failed |
| API reliability, all groups | 60 | Complete responses: {d['complete_success_count']}; partial failures: {partials}; failed requests: {failures} |

Absence of a BASIL annotation is a reference negative, not proof of objective neutrality. Failed negative requests are not successful neutral readings. The delivered-output sentence confusion matrix treats failures as no delivered highlights; the reliability-adjusted correct-complete count below avoids giving failed negatives credit.

## How precise are the highlights?

| Measurement against published human spans | Result |
|---|---:|
| Word-token precision | {pct(a['token']['precision'])} ({a['token']['tp']} matching / {a['token']['tp']+a['token']['fp']} highlighted tokens) |
| Word-token recall | {pct(a['token']['recall'])} ({a['token']['tp']} covered / {a['token']['tp']+a['token']['fn']} reference tokens) |
| Word-token F1 | {a['token']['f1']:.3f} |
| Lexical word-token recall alone | {pct(a['lexical_token_recall'])} ({a['lexical_covered_tokens']}/{a['lexical_reference_tokens']}) |
| Exact span boundary matches | {a['exact_span']['tp']} matches; {a['exact_span']['tp']+a['exact_span']['fp']} predicted spans; {a['exact_span']['tp']+a['exact_span']['fn']} reference spans |
| One-to-one word-overlap matches, lenient | {a['overlap_span']['tp']}/{a['overlap_span']['tp']+a['overlap_span']['fn']} reference spans |
| One-to-one span token IoU at least 0.5 | {a['iou50_span']['tp']}/{a['iou50_span']['tp']+a['iou50_span']['fn']} reference spans |

Precision is agreement of highlighted tokens with reference tokens. It is not model confidence, and tokens outside human spans are not automatically proven neutral. A very broad highlight can have good recall but poor precision. Exact boundary misses are also not equivalent to wholly incorrect bias detection. The matching implementation prevents one broad highlight from claiming multiple independent span detections.

| Token agreement within each group | Precision | Recall |
|---|---:|---:|
| Lexical-containing sentences, against all their reference spans | {pct(lex['token']['precision'])} | {pct(lex['token']['recall'])} |
| Informational-only sentences, context-limited | {pct(info['token']['precision'])} | {pct(info['token']['recall'])} |

The group breakdown matters: long informational reference spans can contribute many more tokens than short lexical cues. The overall micro score therefore cannot describe lexical highlighting on its own.

Conditional 95% percentile intervals from 2,000 stratified, event-level bootstrap samples: precision {interval(ci['precision'])}; recall {interval(ci['recall'])}; F1 {ci['f1'][0]:.3f} to {ci['f1'][1]:.3f}. These reflect uncertainty in this sampled corpus, not all future news.

## Quotations and attribution

The sample has {a['quoted_reference_spans']} human spans marked as quoted. Accepted highlights cover at least one word in {a['quoted_covered_spans']} of them, compared with {a['nonquoted_covered_spans']}/{a['nonquoted_reference_spans']} nonquoted reference spans. This is reference coverage, not a quotation-classification score.

**{a['attributed_predictions']} of {a['predicted_spans']} accepted highlights have usable speaker attribution.** The native adapter reports unknown attribution. No speaker-attribution accuracy can be claimed. Highlighting a quotation does not establish that the journalist endorses it.

## Sentence-level detection and failures

Across the artificially balanced groups, the delivered-output confusion matrix is TP={a['sentence']['tp']}, FP={a['sentence']['fp']}, FN={a['sentence']['fn']}, TN={a['sentence']['tn']}. Sentence precision is {pct(a['sentence']['precision'])}; recall is {pct(a['sentence']['recall'])}; F1 is {a['sentence']['f1']:.3f}. Control highlight rate is {pct(a['sentence']['false_positive_rate'])}, with Wilson 95% interval {interval(a['sentence']['fpr_wilson95'])}.

Only **{a['complete_correct_sentence_count']}/60 requests both completed without partial/request failure and agreed with reference bias presence**. In the separate 40-case lexical/control slice, {d['balanced_lexical_control']['complete_correct_sentence_count']}/40 both completed correctly and agreed with reference bias presence. Its delivered-output accuracy alone is {pct(d['balanced_lexical_control']['sentence']['accuracy'])}, but that credits failed negative requests as no delivered highlight and must not be reported as successful service accuracy. Constant always-highlight or never-highlight baselines each score 50% on this balanced slice. These are trivial sanity baselines, not a comparison with another trained model. The old article classifier predicts a different target, so no superiority claim is made.

Sentence-level agreement measures whether any highlight was returned, not whether that highlight covers the correct words. The phrase metrics above are essential for interpreting it.

Rejected individual spans: {a['rejected_spans']}. API request failures are recorded as HTTP/service failures, not silently converted to no-suggestion success. The client exposes a generic invalid-or-unavailable-response reason; the run does not preserve native completions for failed requests, so the precise cause cannot be assigned to generation, schema checking or runtime transport from these records alone. Failure diagnosis requires a separate, labeled diagnostic and must not replace these recorded outcomes.

Complete-success-only sensitivity metrics are retained in `summary.json` when failures occur. They exclude failed cases and should not replace the all-request view.

## Response time

| CPU timing | Seconds |
|---|---:|
| First request | {t['first']:.2f} |
| Median, all requests | {t['median']:.2f} |
| Median, excluding first request | {t['warm_median']:.2f} |
| 90th percentile | {t['p90']:.2f} |
| 95th percentile | {t['p95']:.2f} |
| Maximum | {t['maximum']:.2f} |
| Total including startup | {t['total_including_startup']:.2f} |

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

1. [BASIL release 2](https://github.com/launchnlp/BASIL/tree/{m['basil_revision']})
2. [Fan et al. (2019), In Plain Sight](https://aclanthology.org/D19-1664/)
3. [UnBias-Plus V2 model card](https://huggingface.co/vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2)
4. [Released training snapshot](https://huggingface.co/datasets/vector-institute/unbias-plus-dataset/tree/{m['training_dataset_revision']})
'''
    (HERE/'REPORT.md').write_text(result)
    print('REPORT.md generated from completed summary.json.')
