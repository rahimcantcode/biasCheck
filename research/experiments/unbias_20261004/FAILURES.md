# Targeted failure diagnosis

The eight previously failed or partially failed BASIL60 cases were reproduced in two separate diagnostic runs. Constrained JSON decoding removed hard parsing failures in this selected set, but two cases still failed exact-source validation for an individual segment. The historical 60-case evaluation remains unchanged.

| Diagnostic arm | Complete responses | Partial failures | Hard failures |
|---|---:|---:|---:|
| Existing generation, safe diagnostics added | 0 | 1 | 7 |
| Same prompt and inputs, native JSON schema enabled | 6 | 2 | 0 |

These runs call the real local model through the backend client; they are not a replacement 60-request HTTP evaluation. Six complete responses in the structured arm comprise three suggestion responses and three no-suggestion responses. A complete response is a contract outcome, not a correctness judgment.

## Observed causes

All seven reproduced hard failures reached `native_json:invalid_native_json`, with `JSONDecodeError` as the retained cause. The model returned `finish_reason=stop` in every case. Inspection of the captured native completions found six unescaped-quotation failures and one incomplete JSON object. The incomplete-object case, `415822d3-fde6-4dca-bb9e-dc6e0692eb19:p35`, ended after the final string without the closing object brace. Strict parsing correctly rejected these outputs; no permissive parser or completion repair was introduced.

The historical run saved generic service failures but did not retain failed native completions. The new reproductions therefore demonstrate a concrete failure mechanism on the same inputs; they do not retroactively prove the exact cause of each lost historical response.

The structured arm still rejected native segment index 1 as `unmatched_phrase` in each of these cases:

- `0acf2cec-34eb-4482-806d-efaf5d8a1501:p12`
- `0a21258c-2afe-48ad-ab32-1b7c1a9ec3c6:p0`

Both remain explicit partial failures. Exact-source checks were retained, with no fuzzy matching or automatic quotation normalization. The latter case also had an unmatched segment in the unconstrained diagnostic arm.

## Implementation and scope

`BIASCHECK_UNBIAS_STRUCTURED=1` opts into native schema-constrained decoding. It defaults to `0`. The detector's separate `BIASCHECK_UNBIAS_ENABLED` flag also remains required and disabled by default. The grammar constrains JSON structure, native fields, basic types, numeric bounds, and labels. The adapter still checks cross-field severity consistency, exact unique source occurrences, and overlapping spans. Structured JSON does not establish that a selected phrase is biased, appropriately sized, or attributed correctly.

The request payloads were verified equal across arms except for `response_format`; prompt and adapter hashes match. Each arm records that its bound code stayed unchanged during that run and its owned runtime process stopped afterward. These statements concern the two completed diagnostic runs, not any later experiment. Model and runtime hashes are retained in the findings manifest.

Safe diagnostics distinguish transport, outer JSON, metadata, native JSON, and native schema stages. Ordinary logs receive static allowlisted stage/code summaries; exception causes and potentially sensitive completion data are not interpolated into those logs. Synthetic diagnostic tests exercise this log-safety behavior, generic public HTTP 503 responses, malformed endpoints, preserved causes, and inference-lock release. Raw captures were enabled only in the explicit research runner.

## Evidence and limits

`failure_findings.json` contains text-free per-case statuses, source hashes, safe failure classifications, rejection indices/reasons, timing, token counts, payload/schema hashes, code bindings, and raw artifact hashes. Object hashes use the serialization convention specified in that file. Raw input/completion captures remain in ignored research data at the relative paths listed in the manifest. Source sentences and generated rationales are not reproduced here.

These eight cases were selected because they had already failed. Their results cannot establish all-60 reliability, deployment reliability, improved highlight precision, or better semantic judgments. The BASIL60 cases are now development evidence. No new human annotations or reviews were added, and deployment remains unapproved.
