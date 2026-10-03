# Data-quality team checkpoint, 2026-10-03

This is a working research ledger, not a final academic report or an approved model release. Its purpose is to make the current work reproducible and keep observed results separate from historical reports, proposed experiments, and unmet dependencies.

## Starting state and scope

- Starting commit: `4268bab42c1186ddcd1fee5b9b80ab4a2ae9f8a4`.
- Working branch: `research/data-quality-team-2026-10-03`.
- User authorization: coordinate concurrent specialist agents to improve BiasCheck, with particular attention to data quality, annotation, and valid evaluation.
- Current task: improve the research foundation and complete the work possible without inventing human annotations, opening sealed holdouts, or assuming production access.
- The original RoBERTa remains the default classifier at the starting commit. No alternative model has independently validated product accuracy or release approval.
- Recent commits establish repository activity. Neither those commits nor the historical hourly research schedule establishes that Dot is currently running. No active Dot process is confirmed by this checkpoint.

This branch starts from the existing research work. It does not imply that its changes have been merged into the production branch or deployed to Hostinger.

## Team and integration boundaries

| Role | Responsibility | Primary output |
| --- | --- | --- |
| Lead engineer and coordinator | Task boundaries, integration, final validation, and release decisions | Coordinated branch and final status |
| Dataset engineer | Source semantics, rights evidence, provenance, and split risks | Dataset audit and registry |
| Annotation researcher | Precise task definition and a feasible human-review workflow | Annotation pilot protocol |
| ML engineer | Reproducible baseline evidence and a bounded comparison plan | Baseline audit and comparison tooling |
| Evaluation engineer | Frozen protocol, denominators, leakage checks, and release prerequisites | Evaluation specification and validation tooling |
| Application engineer | Practical reviewer workflow and application verification | Tested workflow improvements |
| Research recorder and independent reviewer | Evidence classification, claim review, and unresolved concerns | This ledger and [REVIEW.md](REVIEW.md) |

Agents work concurrently on separate assigned files. The lead integrates their work after review. An AI reviewer is a software/research reviewer, not an independent human annotator. Existing human labels must not be silently corrected to agree with a model.

## Evidence at the starting commit

The following results are **historical repository evidence**, not experiments rerun for this checkpoint. Their original context and limitations remain authoritative.

| Evidence | Recorded result | Interpretation and source |
| --- | --- | --- |
| Historical 66-item development comparison | Original live RoBERTa 31/66 reference matches; best TF-IDF 39/66; frozen MiniLM 37/66; Astra Medium 35/66; partially fine-tuned MiniLM 21/66 | Small reused development set, disputed reference labels and context/episode concerns. No established population-level improvement. [Original record](../EXPERIMENT_LOG.md#completed-validation-and-training), [numerical artifact](../results/corpus_comparison_20261001.json) |
| Original high-score failures on that comparison | 30 of 59 RoBERTa outputs with top raw score at least .95 disagreed with the reference | A high softmax score is not reliable correctness confidence. Same historical comparison, not representative production traffic. |
| Qwen3 V5 targeted synthetic phrase transfer | 16/19 exact span+direction+speaker recovery; 16/22 exact emitted-span precision; false highlights in 4/16 cases expecting no spans | Different denominators measure different tasks. All 70 synthetic examples across development and transfer are now development data. [V5 result](../experiments/phrase_stages_20261002/V5_RESULT.md) |
| Existing 100-item human pilot | 60 natural historical articles and 40 AI-authored controlled examples; zero completed human reviews at the starting commit | Prepared annotation material, not gold labels. Historical training overlap is unknown. [Reviewer workflow](../annotation/README.md) |
| Latest recorded Python security checkpoint | 561 tests plus 76 subtests before a final audit-cache-only fix; 58 helper regressions after it; actual checkpoint compatibility checks | Software and compatibility evidence, not political accuracy. [Security record](../../docs/python-security.md) |

The historical claim of approximately 89% model accuracy is not independently reproduced by this repository audit. The exact original training manifest and split lineage are not recovered. A dataset paper, an inherited label, and a production-quality reference label are not interchangeable sources of supervision.

The old 66-item corpus validation split and 70 synthetic phrase cases are already development material. The reserved 89-item corpus partition and 726 argument-stance rows are not inputs to this team's work. No release claim can be based solely on passing historical software tests, suppressing predictions, or selecting a favorable subset.

## Current session ledger

Each entry below identifies what was actually observed. Exact commands and integration outcomes are completed after the corresponding checks finish.

| Status | Item | Evidence or limitation |
| --- | --- | --- |
| Observed | Local branch starts at the stated commit | `git branch --show-current`, `git rev-parse HEAD`, and a clean initial `git status --short` were inspected |
| Observed | Six specialist roles and a lead assigned | Separate file ownership was communicated; no specialist is authorized to fabricate human reviews or access sealed holdouts |
| Observed by lead | Baseline hosted CI is successful | GitHub run [37066293070](https://github.com/rahimcantcode/biasCheck/actions/runs/37066293070), push event for `4268bab`, completed successfully at 2026-10-02 21:22:19 UTC; individual steps included Python tests, frontend tests, npm audit, type checks, and build. This is baseline CI, not this branch's new CI result |
| Observed | Historical metric replay added | Recomputed saved development predictions from 10 explicitly listed publication files; no model inference or sealed corpus reads. See [baseline analysis](BASELINE_ANALYSIS.md) and [machine-readable summary](baseline_summary.json) |
| Observed | Dataset audit and source registry prepared | Nine resource entries, native task/rights distinctions, and two unlabeled Wikinews seeds. The original training mixture remains unidentified. See [data audit](DATA_AUDIT.md) |
| Observed by dataset engineer | Bounded training-provenance search completed | Searched 24 accessible account repository metadata records and targeted relevant code terms; no separate original classifier/training repository or source manifest found. Deleted, inaccessible, unindexed or differently owned repositories are outside that negative result |
| Observed | Two real archival sources acquired by lead | Two article revisions from one publisher, not a balanced dataset; raw/extracted hashes retained. Both item-rights reviews and extraction review remain pending. See [intake record](WIKINEWS_INTAKE.md) |
| Observed | Human adjudication validator implemented | Source-bound third-human handoff preserves independent originals, uncertainty and unresolved items; all output stays development-only. Zero human reviews/adjudications added. See [annotation handoff](ANNOTATION_PILOT.md) |
| Observed by application engineer | Current live API responds but fails the research branch's exact-source contract | At 2026-10-03 13:57:45 UTC, health passed, three modes returned HTTP 200 but rewrote submitted source text, and empty input returned controlled HTTP 400. See [recorded smoke probe](live_contract_probe.json) |
| Observed | Proposed evaluation protocol and validated intake contract | Native article semantics, complete exposure history, source hashes, reviewer provenance and explicit prerequisite blockers. See [evaluation protocol](EVALUATION_PROTOCOL.md). This is a reviewed proposal, not a frozen final-test registration |
| Observed by lead | Combined targeted Python integration passed | 171 tests plus 74 subtests, Python 3.12.14, external sockets disabled with loopback/Unix sockets permitted for synthetic fixtures. Exact command, output and test hashes: [verification record](python_verification.json) |
| Observed by application engineer | Default-model passage UI and frontend dependency fixes | Sentence/paragraph estimates are visible for RoBERTa; support and abstention wording remain explicit. Tailwind migration removed the flagged dependency chain, and full/production npm audits report zero findings. See [staging review](STAGING_READINESS.md) |
| Observed by application engineer; artifacts inspected by reviewer | Post-migration local browser checks passed | Chromium 134 at desktop/mobile widths exercised all three modes, exact displayed source, keyboard highlight selection, toggle, Clear, and passage display. Predictions were intercepted synthetic fixtures. See [browser record](frontend_browser_smoke.json) |
| Proposed | Human-reviewed development pilot and later independent evaluation | Real reviewers, adjudication, source rights, and a frozen task are required |
| Blocked | A high-accuracy product claim or automatic model promotion | No new independently adjudicated reference dataset or final evaluation exists |
| Not performed | Production deployment | No claim of a changed VPS, live model, or publicly available research UI |

The live smoke observed the original model weight hash
`548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d`,
`demo_mode: true`, `release_approved: false`, Transformers 4.57.1 and
PyTorch 2.6.0+cpu. That response establishes observed API metadata, not a complete
production inventory or current checkout identity. Each mode check stopped at
the first failed exact-source assertion. The run therefore does not verify later
coverage/evidence fields and did not score political labels or accuracy.

## Intended research sequence

1. Audit existing supervision and distinguish author framing, publisher identity, policy position, quotation, and factual accuracy.
2. Resolve practical annotation instructions using independent human pilot reviews. Preserve disagreement and exposure history.
3. Acquire rights-reviewed natural text with source, event, date, exact-content hashes, and context provenance. Keep related stories together when defining splits.
4. Freeze the development comparison protocol and reserve a separate final evaluation before candidate selection.
5. Compare a small number of candidates with identical inputs and complete per-example records. Measure article labels, phrase fidelity, false political labels, attribution, abstention, and latency separately.
6. Train or change inference only in response to measured development failures. Freeze the selected candidate before final evaluation.
7. Validate browser interaction, capacity, and deployment/rollback behavior in staging after the candidate qualifies.

Targets discussed in historical notes are aspirations. They are not achieved metrics, and a draft protocol is not a pre-registered final-test decision merely because it has been written down. The [independent review](REVIEW.md) records limitations and remaining prerequisites.

## Checkpoint outcome

The data-quality foundation, adjudication handoff, baseline replay, intake
validator, passage UI correction, dependency remediation, and bounded local
verification are complete for this checkpoint. The review found substantive
provenance and source-boundary defects during development and verified their
corrections. This does not resolve the model's political accuracy. No new model
was trained or selected, no genuine human labels were added, and production was
not deployed. Human rubric review and rights-reviewed natural references are
the next dependency for a meaningful candidate comparison.
