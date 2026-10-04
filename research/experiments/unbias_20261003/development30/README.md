# Thirty-passage synthetic development run

This is a newly authored synthetic fixture, not the missing natural-passage pilot.
Texts and narrow-task expectations were frozen before inference. Expectations are
AI-authored and have not been independently reviewed by humans. No held-out data
was opened. No task-matched 4B baseline was available, so no model superiority or
accuracy claim is supported.

The pinned quantized 8B model was tested through the real opt-in HTTP framing API.
Model and runtime checksums passed before startup. The unrelated classifier's
lifespan was bypassed, as in the earlier smoke run. Full-app capacity and website
behavior are not covered. The runner retained complete API responses, not raw
upstream model completions, and shut down its owned API and model processes.

## Findings

- All 30 requests returned HTTP 200; three responses were partial failures, not
  successful complete detections (DEV21, DEV22, DEV24).
- All six factual controls and four ordinary advocacy controls had no highlights.
- Accepted highlights overlapped 17 of 21 expected phrase occurrences. Overlap
  does not establish correct boundaries, interpretation, or attribution.
- Zero matched the exact AI-authored minimal boundaries. Some discrepancies are
  merely an added article; others encompass an entire sentence or split a phrase.
  This is not zero detection accuracy and must not be reported as such.
- Five accepted highlights did not overlap an expected span. Two were factual
  wording in political passages: “equipment” and “The order suspends a reporting
  requirement.” Three occurred in the two nonpolitical controls. Those latter
  outputs reflect a mismatch with our political-only scope, not necessarily errors
  under UnBias-Plus's broader native task.
- DEV21 and DEV22 rejected unmatched model phrases. DEV24 rejected an ambiguous
  repeated phrase. The safeguards prevented guessing positions, at a recall cost.
- Attribution remains unknown for every accepted highlight.
- Median request duration was 14.14 seconds on this CPU run, including the first
  request in the calculation; the first request took 54.09 seconds. Short invented
  passages and prompt caching make these unsuitable as production latency claims.

## Decision

Keep the candidate experimental and disabled by default. The expanded run confirms
useful sensitivity to loaded wording but also scope, boundary, quotation, and
false-positive limitations. Do not merge or replace the website model on this
basis. Next model work should freeze an explicit political scope and attribution
contract, then evaluate one documented adaptation on versioned natural passages
against a reproducible task-matched baseline. Independent human evaluation remains
necessary before credible accuracy or release claims.

## Reproduce

From the repository root, with the pinned runtime and model available:

```bash
python scripts/smoke_unbias_api.py --cases research/experiments/unbias_20261003/development30/cases.json --output /tmp/unbias-development30-new
python research/experiments/unbias_20261003/development30/summarize.py /tmp/unbias-development30-new/results.json
```

`cases.json` contains exact source hashes and reference offsets; `results.json`
contains the fixture hash, runtime identity, timings, and API responses;
`summary.json` records descriptive counts and individual highlights.
