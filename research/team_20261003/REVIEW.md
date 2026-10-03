# Independent integration review, 2026-10-03

Reviewer role: research recorder and AI reproducibility reviewer. This review checks artifacts and claims; it does not create human reference labels, approve commercial rights, or certify model accuracy.

Starting commit: `4268bab42c1186ddcd1fee5b9b80ab4a2ae9f8a4`.

## Review scope

- Check new team artifacts against the existing code, manifests, experiment records, and assigned scope.
- Check that historical metrics are not described as new runs or independent product accuracy.
- Check article framing, policy stance, publisher identity, phrase attribution, and nonpolitical text are not collapsed into one supervision target.
- Check all test and evaluation claims include the actual scope and denominators.
- Check data rights, exact source identity, event grouping, exposure, and missing human review remain visible.
- Do not inspect sealed holdout content or use its outcomes to select a candidate.

## Initial substantive findings

| Finding | Consequence | Resolution or status |
| --- | --- | --- |
| The original approximately 89% accuracy and claimed merged training corpus do not have a recovered reproducible manifest in the reviewed records | Cannot use that score as the current system's validated performance or prove current examples are independent of training | Preserve as an unverified historical claim; require recovered training lineage or explicitly document unknown contamination |
| Historical 66-item validation and 70 phrase examples have already influenced model or prompt development | Additional tuning on them cannot create an independent final test | Treat them as development diagnostics; sealed partitions remain outside this team's scope |
| PoliticalBiasCorpus annotators could use context beyond the supplied snippets | Some model/reference disagreement could reflect unmatched information | Preserve source judgments; do not relabel them to match model output; record the exact reading context for new human reviews |
| The existing 100-item pilot has no completed genuine human reviews | Its schema and interface cannot supply accuracy evidence by themselves | Human pilot completion and adjudication remain explicit dependencies |
| Development protocol and operating thresholds are not yet validated product criteria | Post hoc selection of tolerated error would inflate release claims | Separate draft specifications from frozen reviewed criteria and from achieved results |
| Recent commits and a historical schedule do not prove an agent is actively working in the background | “Dot is working now” would be an unsupported status claim | Report repository activity only unless live task/process evidence is obtained |
| Existing `docs/testing-ci.md` said hosted checks had not run, conflicting with later repository evidence | Readers could mistake stale documentation or a PR-only workflow lookup for absent baseline CI | Lead directly queried baseline commit workflow runs and inspected successful steps in [run 37066293070](https://github.com/rahimcantcode/biasCheck/actions/runs/37066293070); corrected the stale paragraph. The push-event run at `4268bab` is not a new-branch CI result |

## Integration findings and checks

The findings below record the review and its resolutions. Unresolved production
differences remain explicit rather than being treated as a research-branch pass.

| Finding | Evidence and consequence | Resolution or status |
| --- | --- | --- |
| Initial historical-metric replay silently skipped absent published metric keys | `agree()` could describe a malformed publication as verified even when a comparison field was missing | Resolved: ML engineer requires published keys, with an explicit known legacy coverage exception and regression |
| Phrase replay initially checked fixture IDs without binding prediction presence to successful attempts | A tampered publication could retain a prediction attached to a failed attempt | Resolved: successful validated attempt IDs must equal prediction IDs; tampering regression added |
| Dataset intake reviewer identity comparisons initially used case-sensitive aliases | `A` and `a` could satisfy a declaration of separate reviewers, inconsistent with the existing reviewer workflow | Resolved in validator: normalized case-insensitive comparison and regression; real identity remains self-attested |
| ML review reproduced ignored training/calibration exposure flags and incompatible rubric hashes in declared evaluation prerequisites | A final-test record could retain disqualifying exposure or mismatched human labeling semantics while the declaration check reported prerequisites met | Resolved: all five typed exposure flags are required; final-test records reject every prior use, calibration rejects pilot/training/development/model-selection use, and one manifest task/version must use one frozen rubric hash; adversarial regressions added |
| The first exposure correction also rejected legitimate current-protocol calibration use on calibration rows | After fitting its intended frozen candidate, a calibration set could be incorrectly rejected as if it were final-test leakage | Resolved: calibration-only history is permitted only on the calibration split. Documentation restricts it to the same frozen candidate/registered rule; final test still rejects it. The validator checks declarations, not historical identity truth |
| A proposed primary MIXED label and narrower CENTER meaning differed from the existing v2 rubric | A silent bridge would reinterpret completed v2 reviews without a reviewed version boundary | Resolved: protocol and intake retain v2 CENTER and UNCERTAIN with explicit MIXED_AUTHOR_POSITIONS reason; future semantics require a versioned change |
| New collector parser retained its root depth after the article container closed | A later same-depth footer paragraph could enter the extracted text if no heading had stopped extraction | Resolved: lead added closed-root and out-of-root-heading handling with two regressions. This is a source-boundary correction, not human validation of natural-text extraction |
| New intake heading said “two-source” while both items came from Wikinews | Could imply publisher diversity the intake does not have | Resolved: heading now says “two-article”; source diversity remains absent |
| Adjudication adapter supports only a third distinct human, while existing rubric also permits documented consensus | Reviewers might otherwise try to use an unsupported consensus export or a second alias | Resolved in handoff: third-person route is explicit; a consensus adapter is not implemented, and aliases are not identity authentication |
| New historical replay cannot reproduce individual stance-reference matches from public records | Published stance outputs omit per-ID human gold | Scope is explicit: raw response contracts/prediction totals and aggregate arithmetic only; no claim of independent stance-accuracy replay |
| The original training corpus could reside outside this application repository | An application-only search would not justify “the original data is unavailable” | Dataset engineer completed a bounded search of 24 accessible account repository metadata records and relevant code terms. It found no separate training source; documents retain the distinction between not found in that search and nonexistent everywhere |
| Live deployment rewrites submitted source text | Research highlighting requires exact source offsets and hashes | Unresolved operational difference: recorded HTTP probe fails on exact-source checks in article, sentence and paragraph modes. Do not deploy only the research frontend or infer evidence fidelity from HTTP 200 |
| Application review found sentence/paragraph results hidden for the default RoBERTa engine | `ResultsPanel` rendered passage diagnostics only for the NLI engine, preventing users from inspecting requested default-engine results | Resolved: both engines expose computed passage results, with abstained/tentative states preserved. Five focused rendering regressions added; 38 frontend tests, type checks and production build passed |
| A fresh frontend advisory check reports a new high-severity `braces` advisory | The older clean audit is not evidence that the current dependency tree is still advisory-free; five findings describe a dependency chain, not five unrelated vulnerabilities | Resolved in the research branch by a supported Tailwind 4.3.3/PostCSS plugin migration and tailwind-merge 3.7.0. The resulting full and production npm audits report zero findings; no advisory suppression or forced incompatible fix. Actual browser verification is recorded separately |

Observed reviewer command:

```bash
.venv-team/bin/python -m pytest -q tests/test_wikinews_pilot.py tests/test_research_baselines.py
```

Result: **21 passed in 0.18 seconds**. This covers the 10 synthetic source-parser
checks and 11 historical-publication replay checks, including the resolved
findings above. It is not a new inference run or model-accuracy evaluation.

An additional reviewer check after intake hardening:

```bash
.venv-team/bin/python -m pytest -q tests/test_dataset_manifest.py tests/test_wikinews_pilot.py
```

Final result after the calibration-history clarification: **43 passed plus 74 subtests in 0.24 seconds**. This includes 33 intake
tests and the same 10 source-parser tests. Do not add overlapping test counts to
invent a unique suite total. The collector adapter uses the validator's complete
exposure schema. Its two real unlabeled items remain structurally acceptable but
blocked from evaluation readiness, as intended.

The ML engineer also reported successful regeneration of `baseline_summary.json`
from 10 explicit publication paths. Coverage is 924 saved article predictions,
230 out-of-fold predictions, 254 phrase case/arm evaluations, and 548 saved stance
response contracts. Those are replay work units across reused examples, not
1,956 independent test examples, a new dataset, or new human labels.

## Combined integration evidence

The lead's final targeted Python integration run passed **171 tests plus 74
subtests in 3.71 seconds** on Python 3.12.14. The exact eight-file command,
stdout, exit code, and test-source hashes are preserved in
[python_verification.json](python_verification.json). It includes the latest
calibration-history refinement, all five new Python test files and three
existing annotation regression files. `pytest-socket` disabled external sockets
while permitting loopback and Unix sockets for the synthetic transport fixture.
This is the unique combined targeted run; the earlier overlapping reviewer runs
are not added to its count. It is not a rerun of every historical repository test.

The actual two-article intake was rechecked with the final validator: structurally
valid and still blocked from declared final-evaluation readiness. No rights,
human annotation, or frozen-protocol status was promoted to make the check pass.

The annotation researcher separately reviewed the Tailwind migration and compiled
17 representative selectors without a CSS compatibility blocker. The application
engineer reports a clean locked reinstall, 38 named frontend tests, type checks,
and a production build passing. The recorded before/after dependency audits in
[frontend_dependency_audit.json](frontend_dependency_audit.json) show five high
full-tree findings before migration and zero full/production findings afterward.
This is an advisory snapshot, not a security guarantee or deployed change.
Post-migration browser verification passed locally in Chromium 134 at
1440 x 1000 and 390 x 844. The recorded before/after browser checks used intercepted
synthetic API responses, exercised all three modes, exact displayed text,
keyboard highlight selection, toggle, Clear and the RoBERTa passage inspector,
and reported no horizontal overflow or JavaScript page errors. The recorder read
[frontend_browser_smoke.json](frontend_browser_smoke.json) and independently
inspected both final screenshots for layout and visible fixture disclosure.
They show synthetic scores, not model predictions. Upload, network races,
real backend integration, other browsers, physical phones, VPS load and rollback
are not established by these checks. The migration also raises the documented
browser floor and is not claimed pixel-identical.

## Review conclusion

No remaining blocker was found for preserving this work as a reviewed research
checkpoint. The assigned local research tools, UI correction and dependency
remediation have bounded verification and explicit evidence. Source and task
semantics, test counts and historical metrics are qualified accurately. The
review does **not** approve a production model or establish high accuracy.

Repository publication and hosted CI for the resulting commit are the
coordinator's subsequent integration steps. The known live API source mismatch,
current-model quality, incomplete human references and item-rights reviews,
unfrozen final-test protocol, and unmeasured production capacity remain open.

## Remaining limitations

No independent human annotation, final model benchmark, current production inventory check, operational capacity certification, deployment, or approved replacement model is established by this review. Passing software tests verifies the covered behavior only. Source and license assessments still require per-item context where applicable; a permissive source-level license does not establish valid labels or event independence.
