# Failure diagnosis and lexical span refinement

Prepared before new model calls on 2026-10-04. Parent code: `3aeb251`.

The original BASIL60 run remains immutable. Its seven failed and one partially
failed requests are selected for an instrumented diagnostic, without changing
the upstream prompt or decoding. Newly observed causes do not establish the
unrecorded causes of the original failures. No failed original outcome is replaced.

First, capture native envelopes and exception stages locally for those eight
cases. Public artifacts contain only identifiers, hashes, codes and counts.
Raw news text and model responses remain in ignored research data. Ordinary
server logs must not contain input text, generated text or exception snippets.

If malformed structure is reproduced, test a strictly constrained native JSON
schema on those same eight cases as a separately identified development arm.
No permissive JSON repair, fuzzy source matching, automatic retry or altered
gold label is permitted. Exact-source rejection stays a partial failure.

In parallel, implement a separate second-pass lexical refinement candidate.
It receives the entire original supplied sentence and accepted detector spans.
Each candidate receives exactly one keep/narrow/drop decision. A narrowed span
must be an exact contiguous substring uniquely located inside its verified
parent. No stopword trimming, fixed-length cropping, invented source text or
automatic speaker attribution is allowed. Attribution remains unknown.

Compare refinement with all 60 archived outcomes. Only records with accepted
spans need a model call. All missing/failed detector outputs remain failures;
an upstream partial failure cannot become complete success. If refinement fails,
withhold its highlights and record failure rather than a successful empty answer.
Do not rerun cases to pick the best answer. A detector-output refinement cannot
recover detector misses. Report precision, recall, boundaries, failures and added
latency together, separating lexical, informational and unannotated groups.

The refinement targets evaluative lexical wording, not informational asymmetry.
BASIL's broader native labels and sentence-only context are imperfect references
for that task. Report lexical-only and all-reference measures distinctly. These
60 exposed cases are development evidence, not a new independent accuracy test.
Any later generalization test needs a separately frozen, event-disjoint sample
with task-matched annotations and adequate context. No production deployment or
high-accuracy claim follows from these diagnostics.

## Bounded revision before the second refinement run

The first contract generated an action alongside a highlight. All six active
calls in the first ten processed rows contradicted that contract and failed
validation. The attempt was stopped and its incomplete evidence archived; it
is not a completed evaluation. Version two generates the highlight text, type
and reason only. The code derives keep, narrow or drop and applies the original
strict validator. No examples or reference labels were added. This is the only
planned contract revision; all version two outcomes will be retained.

## Runtime schema compatibility correction

The pinned llama.cpp converter processes oneOf alternatives before sibling
properties and required fields. Version two consequently generated objects
missing required identifiers and reasons. That attempt was stopped and archived
as incomplete. The correction repeats the full required object schema inside
each alternative, preserving the exact prompt, validator and semantic task.
This is a runtime compatibility fix, not an additional prompt-tuning round.
The corrected schema will be checked against the pinned converter before the
full paired run. No failed attempt is removed from the development record.
