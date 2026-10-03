# Experimental UnBias-Plus API

`POST /framing` is an opt-in extension of the existing FastAPI app. Its request is
`{"text":"Exact original passage"}`. It detects wording categories, not LEFT/RIGHT
political direction. The current `/predict` contract and frontend are unchanged.

Disabled by default: `BIASCHECK_UNBIAS_ENABLED=0` (or unset) returns HTTP 404 before
contacting a model. Set it to exactly `1` to enable. The default model address is
`http://127.0.0.1:8082`; `BIASCHECK_UNBIAS_ENDPOINT` accepts only literal loopback
HTTP addresses without credentials, query strings, fragments or paths. Proxy
settings and redirects are disabled. Keep this experimental service private.

Use the pinned local Q4 model and llama.cpp runtime recorded in
`research/experiments/unbias_20261003/native_runtime_manifest.json`. The client
checks the runtime fingerprint, model alias, exact prompt token count, and full
completion. These response fields are consistency checks, not cryptographic
proof of model identity: verify model and runtime checksums before launch.
The smoke runner performs those checksum checks before starting its owned server.

## Response and failure behavior

Successful responses contain `resolved_text`, a source SHA256, and exact Unicode
code-point spans with exclusive end positions. Each span has `bias_type`, `reason`
and `attribution: "unknown"`. No political label, correctness probability or
claimed speaker attribution is invented. Output is explicitly experimental and
`release_approved` is false. The model's rewrite is not applied or exposed.

- `suggestions`: accepted spans exist.
- `no_suggestions`: model completed with no suggestions, not proof of neutrality.
- `partial_failure`: some spans were rejected; rejection reasons remain visible.
- HTTP 400: whitespace-only input; HTTP 422: request schema/length violation.
- HTTP 413: exact token preflight cannot reserve the 2048-token output budget
  inside the 8192-token context. No silent truncation.
- HTTP 503: busy, unavailable model, wrong runtime, incomplete or invalid output.

The endpoint shares the existing inference lock. Run one API worker; multiple
workers would each have their own lock. The client has a 5-second connection
and 180-second read timeout and a one-megabyte response limit. A client disconnect
or timeout is not a guarantee that the runtime has cancelled inference.

## Verification and reproduction

Install the repository backend dependencies and pytest/httpx in a CPU environment.
Run from the repository root:

```bash
python -m pytest tests/test_unbias_api.py tests/test_phrase_api.py -q
python -m unittest discover -s research/experiments/unbias_20261003 -p test_adapter.py
python scripts/smoke_unbias_api.py --output /tmp/unbias-api-smoke-new
```

The smoke output directory must not already exist. The runner requires the
verified model and runtime at the manifest paths and free loopback ports 8082
and 8093. It starts both processes, sends two saved synthetic diagnostic passages
through actual HTTP `/framing`, retains complete API responses, and shuts down
both processes. It disables the API lifespan only for this isolated smoke so the
unrelated article classifier is not loaded. Thus it does not test simultaneous
classifier/model capacity, normal full-app startup, frontend rendering, production
proxy timeouts, or the deployed website. Normal app startup is unchanged.

The upstream prompt and strict adapter are copied byte-for-byte from the tested
research snapshot. Tests guard against drift; the upstream Apache license is
retained under `backend/unbias/LICENSE.md`. Changes to these copies require
updating their provenance and repeating relevant evaluation.

Six earlier diagnostics and these two smoke requests are not an accuracy study.
The natural-passage comparison, independent human validation, minimal-boundary
quality, quotation attribution and deployment capacity gates remain open.
