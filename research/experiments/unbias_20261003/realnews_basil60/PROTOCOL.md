# Frozen BASIL real-news evaluation protocol

Frozen before any predictions for this sample, 2026-10-04 UTC.

## Question and scope

Evaluate the existing, unchanged, quantized UnBias-Plus V2 through the opt-in HTTP framing API on published human-annotated news text. This is an exploratory cross-dataset check of phrase highlighting, not LEFT/CENTER/RIGHT classification, a production benchmark, or a comparison with the old article classifier.

BASIL release 2, commit `4fdbc4f68d5ddae648990063cb6dd11424d96222`, supplies the original text and prior human references. No assistant-generated labels or new human reviews are used. BASIL judges bias toward entities. Its informational-bias definition depends on whole articles and comparison between three news sources. We therefore report lexical and informational results separately. The model receives only the exact selected sentence, with no source identity or reference labels. This deliberately tests sentence-level use; informational results are context-limited and cannot establish full-article capability.

## Sample and contamination checks

Select exactly 60 body sentences: 20 containing a lexical annotation, 20 with informational annotations only, and 20 with no annotation of either type. Lexical cases may also have informational spans. Use one sentence per event triplet across all groups. Restrict to 15-80 whitespace-separated words. Validate every source span against original code-point offsets. Do not correct, relabel, or regenerate human references. Exclude any sentence containing invalid annotations and exclude titles.

Sort candidates within each stratum by SHA256 of `basil60-v1|ID`, select lexical, informational, then unannotated, skipping already-used events. Interleave final inference order by SHA256 of `basil60-order-v1|ID`. Selection is independent of predictions. This balanced diagnostic sample is not representative of the frequency of bias on the web.

Check all eligible candidates against the 5,000 released `train_4` articles identified by the V2 model card, at dataset revision `2e0a842ca594549a510ac527e2222b82d04b9784`. Exclude any candidate sharing a contiguous 13-word sequence after casefolding and Unicode-alphanumeric tokenization. Also check exact normalized sentence containment for the selected set. This is a limited textual-overlap audit, not proof of no event, paraphrase, ancestor-model, or pretraining exposure. The public training snapshot postdates the pinned model; its historical completeness cannot be certified. Preserve source hashes and all exclusion counts.

## Frozen candidate and execution

Use the pre-existing native runtime manifest, backend prompt, adapter and API without changes. Verify binary and quantized weight checksums before launch. Use temperature 0, seed 0, 8192 context tokens and the existing 2048 output budget. Start one CPU model process and one API worker, bypassing only the unrelated legacy classifier lifespan as before. No website changes, tuning, retries with changed prompts, or model selection on these rows. Save every HTTP outcome and time, including malformed, rejected, or failed responses. A partial failure remains a partial failure, even if an accepted span is useful. Stop after these 60 requests; do not enlarge the sample based on results.

## Metrics

- Primary phrase metric: micro precision, recall and F1 over Unicode word tokens intersecting accepted spans versus tokens intersecting the union of human spans. Whitespace and punctuation alone earn no credit; overlapping human spans are unioned. Report lexical-token recall separately, including lexical-only predictions as a descriptive breakdown if relevant.
- Span metrics: exact boundary matches and one-to-one overlap matches using at least one common word token. Any-overlap matches are lenient detection measures, not boundary correctness. Also report one-to-one token IoU >= 0.5. Unmatched predictions and references remain errors.
- Sentence metrics: accepted-highlight presence versus any human annotation, confusion matrix, precision/recall/F1, and per-stratum counts. Treat no-annotation controls as dataset negatives, not proof of objective neutrality. Separately report the balanced lexical/control subset.
- Failures: report HTTP failures, partial failures, rejected spans, valid complete coverage. Score accepted spans as delivered; failed calls have no delivered highlights, and the separate failure counts must accompany metrics. Show complete-success-only sensitivity if failures occur.
- Attribution: human quoted/nonquoted reference span coverage, number of accepted highlights with usable attribution, and explicit unknown coverage. No speaker accuracy claim when attribution is unsupported; do not count unknown as a correct attribution.
- Speed: first request, median, p90/p95, maximum and elapsed total on this CPU, separately noting warm-request median. Short passages, prompt caching, and isolated startup make these unsuitable as production latency claims.
- Uncertainty: Wilson 95% intervals for sentence proportions and 2,000 fixed-seed bootstrap resamples of event-distinct cases for primary token precision/recall/F1. Do not bootstrap overlapping spans as independent observations.
- Context-free constant highlight-all and highlight-none sentence baselines only. They are sanity checks, not a task-matched learned baseline.

## Interpretation and saving

Use the results to decide whether the unchanged candidate is useful enough to continue adapting, or whether its present behavior should be rejected for the proposed feature. This small archival sample cannot approve production even if scores are high. Quotation attribution and political direction remain required capabilities outside current native output. Preserve failures and limitations. Do not claim improvement over the unavailable 4B framing baseline or the old RoBERTa article classifier.

Raw articles, raw API responses, and full input snapshots remain in ignored local research data. Track reproducible code, source IDs, hashes, offsets, counts and a report without redistributing news text. Do not push the blocked batch or this new batch without resolving the existing upload permission issue.

Sources: https://github.com/launchnlp/BASIL ; https://aclanthology.org/D19-1664/ ; https://huggingface.co/vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2 ; https://huggingface.co/datasets/vector-institute/unbias-plus-dataset
