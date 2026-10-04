# Independent evidence review

Reviewed on 2026-10-04 by a separate verification pass over the completed corrected run, archived baseline, immutable fixture, native completion envelopes, runtime log, runner, validator, and frozen scorer. This is an engineering evidence review, not independent human annotation or an independent model-accuracy evaluation. No inference was repeated and no scoring or model code was edited.

**Recommendation: reject this refinement candidate as an added stage for precise highlighting.** It produced no measured change in highlighted wording, boundaries, or labels on these development cases, while adding a median 17.86 seconds per active call. This conclusion concerns this tested candidate and environment; it does not establish that every possible refinement method is ineffective.

## Completeness and provenance

All 60 fixture identifiers and source hashes match the archived baseline and corrected run in their original order. The public comparison was independently recomputed in memory with the frozen scorer and matched the saved object exactly.

| Evidence | SHA256 |
|---|---|
| Immutable fixture | `8d14e9cd7b8268aea9fa5a5f4aadf0873144cc827c178fa2d965fbe8cd3eb5da` |
| Archived baseline | `ed50387d6751dbe611239229913a15b629d7abeeade1c7d56e28692ae77f22a3` |
| Corrected refinement raw results | `79b3650e5337b5a2115981c4075cb826fdb081301c6cb5ad34880010f7bc589e` |
| Public comparison | `cc79214f13d5d2465a574f20376dad121f669cfcfd26e9a706b0a988111d5d57` |
| Protocol | `d219efc8c68d9b89a0b606f67ee108bc1b67a02da2b22902c856a400b86765df` |
| Scorer, matching its recorded pre-inference binding | `c92f7e62389171552f19f007d633d9f3f4eeb39718bcf90eafac99f69aea6e5b` |

All five run-bound code files match their recorded hashes. The actual runtime executable and model weights were also rehashed and match the recorded manifest. The completed run records unchanged code, a completion timestamp, and termination of its owned runtime. These checks establish consistency of the retained evidence and current files; they are not external execution attestation.

## Actual completion and selection checks

The review parsed each of the 30 saved native completion strings using the strict JSON decoder, checked equality with the retained parsed native object, and reran the model-output validator. Every recomputed result matches the saved validated result and delivered spans. Every saved request matches the request builder applied to the full original source and archived accepted candidates.

There are 30 unique completion identifiers and 3,485 generated tokens, ranging from 63 to 220 per active call. Every completion reports normal termination, positive generation time, and token accounting consistent with its preflight and timing metadata. The runtime log contains 30 prompt-evaluation entries. The reviewed runner performs one preflight and one completion request for each active case, with no response-cache lookup, inference bypass, or automatic retry path.

This evidence supports actual model generation rather than a shortcut that merely copies the archived result. It does not justify saying that no caching occurred: 29 calls report cached prompt tokens. Reuse of prompt/KV computation differs from reusing a completed response. The runtime log does not provide a route-level HTTP access audit, so the request account rests on the reviewed code, retained envelopes and generation records together.

| Corrected-run outcome | Count |
|---|---:|
| Active refinement calls, all validated | 30 |
| Skipped because the detector accepted no spans | 23 |
| Preserved upstream request failures | 7 |
| Validated keep decisions | 51 |
| Validated narrow decisions | 0 |
| Validated drop decisions | 0 |

For every native decision, the selected original string exactly equals its parent candidate. For every resulting highlight, source coordinates, selected text and bias type equal the archived parent. Attribution remains unknown. Generated explanatory metadata is not an independently validated semantic improvement.

The original partial failure remains a partial failure, with its original rejected-span record preserved. All skipped responses remain unchanged. Refinement success therefore does not mean 60 complete pipeline outcomes: the seven original failures and one original partial failure remain.

## Metrics, latency and interpretation

The complete baseline and refinement aggregate metric objects are identical, including all-reference and lexical-only views, the 40-case lexical/control slice, and each stratum. There is no lexical precision improvement, recall improvement, or boundary improvement to attribute to this stage. No final-run active failure was withheld; consequently selective removal of failed highlights does not explain these unchanged final metrics.

Added latency includes all 30 active calls and excludes the 30 skipped records: median 17.8616 seconds, 90th percentile 29.1817 seconds, 95th percentile 31.1014 seconds, maximum 33.6047 seconds, and summed active-call time 573.1406 seconds. These are observed local research-stage timings, not newly measured end-to-end API latency. Adding them to historical detector timings is only an illustrative sequential budget.

The earlier incomplete v1 and v2 attempts remain separate disclosed failures; they were not merged into, repaired within, or silently replaced in the completed comparison. The corrected-run result must be reported alongside that development history. Native structured-decoding diagnostics are a separate arm and cannot be credited as repairs to this paired baseline.

The recommendation is supported by identical delivered highlights and material additional latency. It is not a claim of semantic correctness, neutrality, speaker-attribution accuracy, independent generalization, or deployment readiness. These exposed BASIL60 cases remain development evidence; informational bias remains outside the lexical refinement target. Production approval remains false.
