# UnBias improvement cycle: findings and decision

2026-10-04. Scope: experimental evaluative wording highlights, not political direction, factual verification, or author-endorsement detection.

## Decision

Retain the opt-in structured-output reliability change for further research. **Reject the second-stage refiner as a useful improvement in its tested form.** It preserved all 51 existing highlights, with no narrowing or dropping, and added a median 17.86 seconds per active request. No measured highlight-quality metric improved. No production deployment, training, or new human annotation occurred.

## Reliability diagnosis

The eight previously failed or partial BASIL cases were reproduced using the same detector prompt and source texts. Seven hard failures reproduced: six native JSON quotation-escaping errors and one missing closing object brace. These newly captured responses reveal a concrete mechanism, but the lost historical completions cannot be retroactively diagnosed with certainty.

| Selected eight-case diagnostic | Complete | Partial | Hard failure |
|---|---:|---:|---:|
| Original decoding, instrumented client | 0 | 1 | 7 |
| Same prompt, native JSON schema enabled | 6 | 2 | 0 |

The structured arm still rejected two unmatched source phrases. No fuzzy matching, permissive JSON repair, or concealed retry was introduced. `BIASCHECK_UNBIAS_STRUCTURED=1` is opt-in and the framing endpoint remains separately disabled by default. Safe internal failure stages/codes now support diagnosis without source text in ordinary logs. This selected sample does not establish all-input or deployment reliability. Details and hashes: `FAILURES.md` and `failure_findings.json`.

## Paired lexical refinement experiment

The refiner received each complete original sentence and its accepted detector spans, with no reference annotations. It was asked to select minimal faithful lexical cues, preserving qualifications and negation. Only accepted spans could be kept, narrowed or dropped; detector misses could not be recovered. All 60 archived outcomes remained in the comparison.

| Corrected run outcome | Count |
|---|---:|
| Active refinement calls, all succeeded | 30 |
| No accepted spans, skipped unchanged | 23 |
| Original hard detector failures, preserved | 7 |
| Validated keep / narrow / drop decisions | 51 / 0 / 0 |
| Resulting complete / partial / hard-failure pipeline outcomes | 52 / 1 / 7 |

All returned highlight coordinates are unchanged. The corrected run introduced no extra failures. It did not repair the seven detector failures or the original partial response. Pipeline statuses are derived from archived detector outcomes plus new refinement calls, **not a fresh 60-request HTTP run**. Generated cue types and rationales were not independently semantically validated.

### Primary narrow-task comparison

The 40 lexical/control cases comprise 20 BASIL lexical cases and 20 unannotated controls. Only published lexical spans count as references here; this differs from the older report's mixed lexical/informational scoring.

| Lexical references on lexical/control cases | Baseline | Refined |
|---|---:|---:|
| Highlight-token precision | 27/265 = 10.2% | 27/265 = 10.2% |
| Lexical-token recall | 27/33 = 81.8% | 27/33 = 81.8% |
| Exact span matches | 0/20 references | 0/20 references |
| Delivered highlights | 33 | 33 |
| Complete, correct sentence-presence outcomes | 31/40 | 31/40 |

The low token precision despite substantial lexical-token recall reflects excessive highlighted text around reference cues. Presence correctness is a different, easier measure and is not precise-highlight accuracy. BASIL unannotated text is not guaranteed neutral; these archival sentence annotations are imperfect references for the proposed task.

### Historical broad-reference comparison

| All 60 cases, all BASIL reference types | Baseline | Refined |
|---|---:|---:|
| Highlight-token precision | 175/416 = 42.1% | 175/416 = 42.1% |
| Highlight-token recall | 175/380 = 46.1% | 175/380 = 46.1% |
| Exact span matches | 3/41 references | 3/41 references |
| Delivered highlights | 51 | 51 |
| Complete, correct sentence-presence outcomes | 43/60 | 43/60 |

Informational bias is outside the lexical refinement target, so this table preserves historical comparability rather than defining the release task. Precision is conditional on delivered highlights; it must always be read with failures and recall. Here no refinement calls failed and no highlights changed, so failure-based selection cannot explain a supposed gain: there was no gain. The conditional sensitivity in `SENSITIVITY_PLAN.md` was unnecessary.

The 30 active CPU calls added 573.14 seconds in total; median 17.86, p95 31.10, maximum 33.60 seconds. These are refinement-stage timings, not new end-to-end web latency. The runtime's recorded process high-water field is not a validated whole-model memory measurement and is not used as capacity evidence.

## Failed attempts and implementation lesson

The first contract asked the model for both an action and a selected phrase. Six active calls contradicted the action contract; that incomplete attempt was stopped after ten total rows. The revised contract generated a selection and let code derive the action. Its first seven active calls omitted required fields; it was stopped after eleven total rows.

Inspection and a compiled probe of the pinned llama.cpp converter proved that its `oneOf` handling ignored sibling required fields. Repeating the complete object constraints inside each alternative corrected the grammar. The semantic prompt and validators stayed unchanged for the final run. Both stopped attempts, code snapshots and failure counts are preserved separately and are not pooled into the completed comparison. See `schema_compatibility.md`.

## Evidence and limits

The model was pinned UnBias-Plus V2, locally converted through Q8_0 to Q4_K_M, on the recorded llama.cpp CPU runtime. No claim of full-precision equivalence follows. The original fixture, baseline, scorer and candidate code hashes were verified; the completed run recorded unchanged bound code and shutdown of its owned runtime. `comparison.json` retains text-free paired outcomes and metrics. Raw source and completion captures remain in ignored research data.

The local affected suites passed 173 tests plus 62 subtests across the recorded commands, including an actual runtime grammar-conversion regression. These checks establish implementation behavior, not semantic accuracy. Live HTTP smoke and hosted CI outcomes are recorded separately in `verification.json`.

All 60 cases have now been exposed during development. No new independent accuracy claim, training-independence guarantee, or human review was created. Attribution remains unknown. We have not established why this model retained every candidate; the result supports rejecting this refiner, not a general claim that every possible refinement model must fail.

## Next action

Use the task-specific data and human-review gate in `NEXT_GATE.md`. First freeze a minimal lexical-cue rubric with real independent reviewers and retained article context. Build event-disjoint development and untouched test sets, then compare a task-matched trained extractor or a different controlled extraction candidate on development. Freeze the selected complete detector pipeline before independent testing. Evaluate attribution separately before showing any speaker or author-endorsement claim. Do not spend another accuracy cycle repeating the unchanged rejected refiner.
