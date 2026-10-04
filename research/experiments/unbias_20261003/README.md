# UnBias model feasibility and diagnostic results

**Decision: keep UnBias-Plus 8B V2 as the next research candidate; do not replace or deploy either tested model.**

The official 8B candidate now runs on CPU after a documented local quantization. This work completes a new six-case feasibility screen. It does not complete the missing 30-natural-passage comparison, establish accuracy, or recover the previously claimed framing implementation.

| Diagnostic | Compact UnBIAS-NER | UnBias-Plus 8B V2, local Q4 |
|---|---|---|
| D01 | 4 highlights | 2 highlights; 69.7 s |
| D02 | 2 highlights | 0 highlights; 9.5 s |
| D03 | 4 highlights | 0 highlights; 8.1 s |
| D04 | 2 highlights | 1 highlights; 14.9 s |
| D05 | 2 highlights | 2 highlights; 26.6 s |
| D06 | 3 highlights | 2 highlights; 23.0 s |

All 12 requests completed. Every accepted span slices the unmodified source exactly. This establishes technical integrity, not that the highlights are justified.

## Findings

- NER found all four exact fixture spans but emitted 13 additional spans, including ordinary factual wording and all three negative controls. Reject it as a direct replacement.
- The 8B candidate left the factual tax passage and ordinary advocacy unmarked. It included all four intended cue occurrences inside broader spans, but matched none of the fixture's exact minimal boundaries. Literal containment is not a validated semantic score.
- It incorrectly flagged `proposed corporate tax increase`, flagged the sports control outside our narrow scope, and has no speaker-attribution output. Its explanation for the quoted tax phrase also describes it as a judgment presented as fact without establishing author endorsement.
- Repeated cues were returned using distinct surrounding text, so both occurrences aligned successfully. The adapter rejects any ambiguous repeated phrase, absent phrase or overlap, retaining a partial failure instead of inventing offsets.
- Median latency was 19.0 seconds, with 69.7 seconds for the first request and 8.1 to 26.6 seconds afterwards. Shared prompt caching affects these figures. Peak sampled server RSS was 7.75 GiB, leaving little space under the 8 GiB limit. This is not a VPS capacity or production-latency guarantee.

## What was recovered

The accessible repository contains planning commit `9357c89ff54d20e148942c7be178465714f9bad2` and older directional-stance experiments. The transcript's later framing-only API, 30 natural passages, AI reviewer exports, and 142-test claim could not be recovered. See `recovery_audit.json`. Do not relabel the older LEFT/RIGHT baseline or reuse its scores for this different target.

## Implementation and verification

- `adapter.py`: strict native schema, original-text offsets, all conflicting overlaps rejected, unknown attribution, and explicit partial failures; separate raw-offset BIO decoder.
- `run_native.py` and `owned_native_runtime.py`: private owned CPU server, pinned weights and prompt, exact token preflight, runtime fingerprint, full-completion checks, untouched inputs, complete raw outputs and failures, measured memory and latency.
- `run_ner.py`: local-only verified weight loading, no remote model code, no truncation, raw token labels and offsets saved.
- 39 independent adapter tests pass. Saved NER spans and exact-boundary counts replay identically from raw token labels. The native screen ran once, with no prompt revision, retry, or discarded case.

## Provenance

- Official weights: [vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2](https://huggingface.co/vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2/tree/01a0c8e97ab44b9d2e56d86b6298f2cc74df1222).
- Official source/prompt: [UnBias-Plus at a363e434](https://github.com/VectorInstitute/unbias-plus/tree/a363e434e73b4b4f74dac5a959139cb86f30cfd6). Copied `upstream_prompt.py` is unmodified; its Apache license is retained in `UPSTREAM_LICENSE.md`.
- CPU runtime and converter: llama.cpp b11349 / `fb4b2737a808a3fb7c2117a498f43815dc9be53e`.
- Compact fallback: [newsmediabias/UnBIAS-NER](https://huggingface.co/newsmediabias/UnBIAS-NER/tree/0aff43fa27ef142169ee9e0ae63ed756b88918d6). It is a distinct candidate from UnBias-Plus; its training provenance remains incomplete.
- Q4 weights are locally derived through Q8 requantization. Their SHA256 is `7f771dbb1739fe840655850784c1cea759185aa456cde0644bdb1425d89969c9`. Quantization can alter predictions; this does not test the original BF16 model.
- `conversion_manifest.json` records input/output hashes, converter identity, dependencies, commands, validation and memory measurements. The 16.4 GB source shards were removed only after validated Q8 conversion; they remain reproducible from the pinned source.

## Reproduction

Use a separate CPU environment matching `diagnostic_environment.txt`. Heavy weights are excluded from Git and should live outside synced workspace folders to avoid transfer duplication.

```bash
python research/experiments/unbias_20261003/fetch_models.py --candidate ner --output-dir /tmp/unbias-ner
python research/experiments/unbias_20261003/run_ner.py --model-dir /tmp/unbias-ner --output /tmp/ner-rerun.json
python research/experiments/unbias_20261003/fetch_models.py --candidate native --output-dir /tmp/unbias-v2-bf16
```

`convert_candidate.py` documents the exact bounded conversion. Recreate its pinned llama.cpp source and binary locations from the manifest before running it. It deliberately refuses to overwrite recorded stages. The converter uses lazy tensors, no temporary duplicate model, four CPU threads, and a 512 MiB Q4 buffer. Large Q8/Q4 files remain under `/tmp`.

The recorded native run is immutable. For another inference run, use `python research/experiments/unbias_20261003/owned_native_runtime.py --output-dir /tmp/native-rerun` after verified weights exist. For a new conversion, copy `convert_candidate.py` into a fresh sibling experiment folder at the same directory depth so its stage records do not overwrite this run, then copy its verified native runtime manifest back before inference. Start the owned server only after weight conversion and its checks finish. Run `python -m unittest discover -s research/experiments/unbias_20261003 -p test_adapter.py` for source-integrity tests.

## Next decision gate

Recover or explicitly rebuild a versioned natural-passage development set and a task-matched baseline. Freeze one documented adaptation for political scope, minimal boundaries and attribution before that comparison. Then evaluate on fresh independent human references. Keep the current website unchanged until the task and operational gates are met.

No training, human validation, reserved-test access, merge or production deployment occurred.

## Subsequent opt-in API integration

The user subsequently authorized an experimental API integration and smoke test.
`POST /framing` is now gated by `BIASCHECK_UNBIAS_ENABLED=1` and disabled by
default. See `docs/unbias-framing.md` and `api_smoke/` for the contract, full
HTTP response records, test environment, and limitations. Both live smoke
requests passed; 23 API tests and 39 adapter tests passed. No frontend change,
production deployment, model promotion, or human quality validation occurred.
The earlier research decision remains in force.

## Subsequent real-news evaluation

The unchanged quantized 8B API was evaluated on 60 BASIL news sentences with published human references. See [the full report](realnews_basil60/REPORT.md), [frozen protocol](realnews_basil60/PROTOCOL.md), and [text-free results](realnews_basil60/summary.json). Word-token precision was 42.1%, recall 46.1%; seven requests failed and one partially failed. Speaker attribution remains unsupported. This is archival cross-dataset evidence, not final deployment accuracy or a claim of model-training independence. The candidate remains experimental and the website was unchanged. Earlier experiment records remain historical and unmodified.
