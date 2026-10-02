# Historical phrase-stage development experiments

This is a replayable **research-only** source snapshot, never imported by the application. It preserves the completed v4/v5 experiment implementation and the v3 source baseline. Both are rejected for serving. The 38 original cases and the later 32 targeted AI-authored transfer cases are now development data; they are not independent human gold or a representative accuracy test.

## Results

| Diagnostic | v3 reused 38 | v4 reused 38 | v5 reused 38 | v4 fresh 32 | v5 fresh 32 |
|---|---:|---:|---:|---:|---:|
| Valid cases | 37/38 | 38/38 | 38/38 | 30/32 | 30/32 |
| Exact span + direction + speaker recall | 4/27 | 25/27 | 23/27 | 15/19 | 16/19 |
| Exact returned-span precision | 4/7 | 25/34 | 23/31 | 15/22 | 16/22 |
| Exact author-only recall | 2/21 | 20/21 | 18/21 | 13/15 | 14/15 |
| No-expected-span cases receiving false highlights | 0/15 | 7/15 | 4/15 | 5/16 | 4/16 |

V4 changed only extraction demonstrations. V5 changed only direction demonstrations. Direction/speaker tasks receive the same complete source. Negative cases include uncertainty, rejected beliefs and string mentions as well as ordinary nonpolitical content; this column is not a real-world nonpolitical false-label rate. V5's one additional transfer match does not establish a general improvement; it also flips two correct old LEFT decisions to RIGHT. Negation, quoted string mentions, factual reporting and repeated voices remain failure modes.

## Replay

From the repository root, run:

```sh
python -m pytest -q tests/test_phrase_stage_snapshots.py
```

This verifies every published file hash, runs the 66 historical structural tests in a subprocess with an isolated `backend` module namespace, and replays every saved v3/v4/v5 metric. It performs no model inference or dataset download. Do not add the nested tests directly to the main pytest invocation: their historical `backend` package is deliberately isolated.

## Provenance and portability

`publication_manifest.json` lists original and publication hashes. Source is preserved except removal of a hardcoded workspace-only path-scrubbing literal from both matching publisher copies and generalization of an internal reviewer identifier in metadata; no inference/metric function changed. Historical local raw-record paths contain sanitized publication records here. Their original raw and protocol hashes remain in the embedded publication notes. The source wrapper's original commands expect local raw paths and existing pinned runtime files; they are historical implementation evidence, not a ready-to-run inference command using sanitized placeholder paths. Use the replay test above to reproduce the published metrics.

The full untouched originals remain in the local research archive. Model weights, runtime binaries, credentials, caches, independent human data and unexposed tests are not included. The 89-item original corpus test and the 726-item native stance holdout remain sealed. No release or deployment approval follows from these experiments.
