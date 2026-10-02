# Experimental phrase highlighting

## Implemented capability

After Analyze, the reader can show blue LEFT and red RIGHT marks on the original
article using separately supplied phrase evidence. Article, paragraph and sentence
modes use the same article-level span coordinate system. No sentence or article
class is expanded into an invented phrase explanation. The document-level
classifier and phrase classifier may disagree; this is visible experimental
evidence, not an explanation of RoBERTa's internal computation.

Plain text can be pasted or loaded from a UTF-8 `.txt` file. The API preserves its
exact whitespace and Unicode; HTML extraction remains a separate URL operation.
Preserving plain text changes the earlier normalization contract. Model metadata and calibration policies now bind `plain_text_exact_url_article_extraction_v2`; old policies without matching preprocessing must be regenerated, not reused.

Offsets are zero-based Unicode code points, end exclusive, into `resolved_text`.
The browser uses code-point slicing, checks every substring and bounds, drops
overlapping evidence, renders escaped text, and preserves paragraph breaks. It
colors only author-attributed evidence; quoted/unknown positions are not silently
shown as the author's ideology. Relevance, quotation, negation and semantic
faithfulness still require a capable model and independent human evaluation.

The response adds `evidence_spans`, `evidence_status`, and `evidence_metadata`.
Each span has `start`, `end`, `text`, `label`, `attribution`,
`status: experimental`, and a brief `rationale`. The metadata binds the exact text
SHA-256, offset unit, model/source and unapproved/un-calibrated status. Missing,
invalid, mismatched or unavailable evidence leaves the original article plain.
The UI requires an available, code-point-indexed envelope before coloring.

## Providers and remaining setup

`PHRASE_EVIDENCE_PROVIDER=disabled` is the default. An article submitted to the app
does not trigger the development account's Codex CLI or an external model API.

`cache` reads an explicitly configured `PHRASE_EVIDENCE_CACHE`. Entries bind full
original source text and a frozen extraction contract. This is an offline research
demonstration capability, not arbitrary-article inference or production readiness.
The preserved October 2 probe produced no valid cache entries because the model
client failed before inference; do not interpret its missing predictions as model
accuracy or use the empty cache to claim working extraction.

`local_structured` supports new text through a separately provisioned self-hosted
OpenAI-compatible structured-output server. It requires all three values:

```
PHRASE_EVIDENCE_ENDPOINT=http://127.0.0.1:8081/v1/chat/completions
PHRASE_EVIDENCE_MODEL=<verified-local-model-id>
PHRASE_EVIDENCE_MAX_INPUT_CHARS=<tested-full-context-bound>
```

Only literal loopback HTTP hosts and the exact chat-completions path are accepted.
There are no credentials, external hosts, proxy inheritance, redirects or tools.
The adapter sends the full original text with the same extraction instructions,
requires a complete structured answer and validates its source quotes and
occurrences. Timeout, oversized input/output and malformed responses yield no
highlights. It does not truncate articles to force a result. The configured
character limit is an operator contract, not proof of a model's token capacity:
the selected server must reject oversized prompts rather than silently truncate
or shift away context, with space for its chat template and output budget.

[llama.cpp's server](https://github.com/ggml-org/llama.cpp/tree/master/tools/server)
is an example of a CPU/GPU server with OpenAI-compatible routes and schema-bound
JSON. No serving engine, model weights or GPU have been installed for this
feature, and no self-hosted model's phrase fidelity or latency is established.
Actual VPS CPU, RAM, free disk and accelerators are not recorded in the repo.
The older deployment guide's 8 GB refers to a development machine, not verified
VPS capacity. Do not infer that another generative model fits alongside RoBERTa.

Before activation: inspect the authorized host, choose and pin a rights-cleared
model/server revision, measure memory and latency at the intended context and
concurrency, run actual phrase inference and end-to-end browser checks, then pass
independent article/relevance/attribution/span quality gates. A hosted API would
require a separate authorized provider, budget, privacy review and secure
credential setup; this branch does not create that access or route users' text
through the research account.

## Verification and interpretation

Synthetic tests cover the user's neutral-cat-plus-tax expression, neutral
prefix/suffix, negation, quotations, mixed views, repeated phrases, emoji, CRLF,
combining marks, HTML-like text, invalid offsets and unavailable evidence. These
are contract tests with specified outputs, not independently labeled political
accuracy. New input/mode/Clear actions invalidate older requests so a late answer
cannot be attached to a newer article.

The October 2 actual extraction attempt used a frozen 26-case diagnostic and
fixed full-context prompt. All six CLI batches failed before inference with
`failed to initialize in-process app-server client: Read-only file system
(os error 30)`. No protected credential or runtime path was changed. A separate
12-case transfer suite was prepared without observing model outputs but remains
unrun for the same blocker. Actual phrase semantics remain untested.

Original RoBERTa loading and a real FastAPI TestClient request succeeded with the
known checkpoint hash, exact source preservation and phrase extraction disabled.
HTTP-provider mocks, API contract tests and static React rendering exercise
integration independently. They do not prove a real local generative model works.
The dot cloud browser rejected the local URL with `ERR_BLOCKED_BY_CLIENT`; the
frontend server process later reported cancelled network approval. No alternate
route was used, and visual/interactive browser QA is unverified.

Measure span precision and recall, neutral-input false-highlighting, attribution
errors, document coverage and minimality on independently human-annotated natural
text. An empty highlighter cannot pass via undefined precision, and exact substring
matching alone does not establish a correct political interpretation. Current
research is not a production release or a high-accuracy claim.

## Later October 2 update: actual CPU inference now works

The earlier account-client failure is preserved as historical evidence. A separate
public-weights route now runs real local inference: verified Qwen3-4B Q4_K_M with
pinned llama.cpp b11349, using roughly 4.6–4.7 GiB process RSS on the cloud test
machine. No research-account proxy or external model API is involved.

`local_phrase_baseline_20261002.json` preserves the first 38 actual short-input
responses. A second contract iteration is preserved in
`phrase_contract_v2_20261002_publication.json`. Valid formatting improved from
24/38 to 34/38, but only 11/35 returned spans matched the exact phrase, direction
and attribution. Twelve cases without expected author spans received author
highlights. These are development fixtures, not independent human truth; the
historical `neutral_cases` metric means no expected spans and includes ambiguous
negation/insufficient-context cases. Do not call it a population nonpolitical rate.
Neither candidate is approved for serving. V2 stays outside the serving path.

The actual app-to-model smoke succeeds through the `llama_cpp` provider and
preserves its honest failures: the cat example was rejected, a same-sex-marriage
statement produced an author-attributed LEFT span, and a recipe produced no spans.
This establishes an arbitrary-text inference path, not high phrase accuracy.

The `llama_cpp` provider adds an exact prompt-token preflight using the identical
chat payload, verifies actual per-slot context and runtime build, reserves output
plus a safety margin, and checks actual token usage and complete output. Its
configuration additionally requires `PHRASE_EVIDENCE_CONTEXT_TOKENS`,
`PHRASE_EVIDENCE_RUNTIME_FINGERPRINT` and a launch-verified
`PHRASE_EVIDENCE_MODEL_SHA256`. Output budget defaults to 1024 tokens and can be
bounded explicitly with `PHRASE_EVIDENCE_MAX_OUTPUT_TOKENS`. The weight hash is an
operator assertion tied to a verified launcher, not proof supplied by a JSON model
name. The whole provider remains disabled by default.

Reproducible setup is described by `research/local_phrase_runtime.json` and
`research/scripts/setup_local_phrase_runtime.py`. The latter fetches immutable
HTTPS artifacts, checks byte sizes/SHA-256 and safely extracts the Linux x64
runtime. `research/scripts/local_cpu_runtime.py` owns one loopback-only process,
verifies installed bytes before launch, and does not inherit account tokens.
Model/license references and quantization publisher are explicit. A newer
Unsloth-published Q4_K_M of Qwen3-4B-Instruct-2507 is a separate candidate, not an
approved replacement. It is not a Qwen-published GGUF.

A separate, human-labelled UK argument dataset now has 274 development and 726
reserved examples. Original Qwen3-4B matched 181/274 majority judgments (66.1%,
macro-F1 .660) on whether a stance is expressed. This is neither political-topic
relevance nor absolute LEFT/RIGHT, and the sample was model-condition-selected.
Its 726 reserved examples and the old 89-item corpus holdout remain unevaluated.
Underlying transcript rights and complete episode independence remain unresolved.
