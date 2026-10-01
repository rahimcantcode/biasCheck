# Experimental political entailment implementation

Date: 2026-09-29. This is a working research build, not a high-accuracy release.

## What changed

- Opt-in `BIASCHECK_ENGINE=political_nli` uses PoliticalDEBATE large at revision
  `1a3aff1ecb97ad93a6de598f7414b1707de7e7c3`. Original RoBERTa remains available and default.
- Checkpoint and tokenizer SHA-256 values are pinned in `backend/nli_checkpoint.json`;
  download and startup both verify them. Loading rejects missing/unexpected weights
  and wrong entailment class mapping. The model has two entailment classes, not
  three political classes. Entailment is class 0.
- Six fixed hypotheses separately score politics, government policy, liberal
  support, conservative support, and political reporting without taking a side.
  Outputs are independent support scores, not a normalized three-way posterior.
- Overlapping windows cover the full input. Pair capacity reserves the hypothesis
  tokens. Inputs beyond 12 windows are rejected before model inference. Mean
  window scores are an unvalidated aggregation choice. Opposite tentative
  directions across windows produce a mixed/conflicting result.
- Development rules: fewer than 12 tokens gives insufficient context; maximum
  politics/policy score below 0.5 gives nonpolitical; otherwise a tentative label
  requires score at least 0.8 and margin at least 0.4. These are conservative
  engineering defaults, not calibrated thresholds or evidence of measured risk.
  Version 2 withholds tentative Left/Right when mixed-endorsement support is at
  least 0.8. This guard was developed after inspecting the v1 failures.
- No candidate output is a validated label. `label=null`, `calibrated=false`, and
  `release_approved=false` remain intentional. The UI exposes `tentative_label`
  separately and shows nonpolitical/context/uncertainty outcomes clearly.
- Article, sentence, and paragraph modes retain exact offsets and separate overall
  document analysis. Candidate passage assessments are inspectable as plain text.
- One request runs at a time; additional requests return a busy response. At most
  20 passages are accepted for the candidate. CPU inference can take minutes.
- URL transport now connects to a DNS-checked public IP directly, retains the
  original hostname for TLS certificate checks, rechecks redirects, caps bytes,
  and bounds download time. No environment proxy can silently re-resolve the host.

## Evidence and limitations

`political_debate_controlled_v1.json` retains all 40 original development cases.
The model no longer universally predicts Left on those cases. Ordinary daily-life
examples receive extremely low politics/policy scores. Explicit progressive and
conservative statements can be distinguished. This is an unlabeled synthetic
probe, not a human-gold accuracy evaluation.

Known v1 failures include S34 (Republican mayor transparency criticism receives
high Left support), S30 (vague negative policy criticism receives high Right
support), and S28 (mixed positions receive predominantly Right support). The
current uncertainty rules do not reliably solve all of them. S35 has conflicting
high class support, illustrating why entailment outputs cannot be normalized and
called confidence. Quotation and sarcasm handling is not guaranteed.

The 60-article comparison uses exactly the earlier sample. It only evaluates the
first paired-token window, whereas the application processes full text. This
corpus uses media-ideology labels; its label construct differs from explicit
textual endorsement. Training overlap is unknown. Neither its accuracy nor the
controlled examples establish deployment accuracy. The BBC data source was
recorded for a future topic-relevance proxy; no BBC evaluation is claimed.

`nli_api_smoke.json` records actual model-backed API calls for dinner, a one-word
input, and two policy positions. These verify integration only. Unit tests verify
context/relevance/conflict rules, URL destination pinning and TLS hostname use,
private redirect rejection, and the existing pipeline/research behavior.

## Remaining release requirements

1. Compare candidate and original on independent, human-labeled text that matches
   the desired construct: expressed stance versus media framing must be separate.
2. Tune hypotheses/thresholds on development data only, then freeze them before a
   held-out evaluation. Report per-class precision/recall, coverage and selective
   error, relevance confusion, calibration, latency, and memory.
3. Include nonpolitical text, quotations, sarcasm, mixed positions, and long inputs.
   Deduplicate and audit source/event/time overlap. Do not relabel failures to fit
   model predictions or treat AI-generated expected labels as expert gold.
4. Loaded-language detection remains a separate, unimplemented task. Do not call
   these outputs factuality or word-level bias detections. BABE was researched,
   not integrated or validated in this build.
5. Verify the actual VPS resources and staging behavior, then deploy frontend and
   backend together. This workspace has no VPS connection; no deployment occurred.


## Follow-up guard experiment

`nli_guards_development.json` records three additional hypotheses on the same 40
controlled cases, explicitly reused for development. A mixed-endorsement guard
receives high support on S28, while retaining low scores on the clear policy
statements. It also fires on attributed quotations and some nonaligned statements,
so it only withholds an otherwise tentative Left/Right result; it never assigns
Center or overrides nonpolitical/context checks. This is not a calibrated detector.

The proposed specific-ideology gate was rejected: it scored S30 (unspecified
negative policy criticism) at about 0.993 while rejecting S19 (labor support).
The everyday-life hypothesis was also not integrated: it failed to consistently
recognize the daily-life controls. Preserve these negative results; adding more
hypotheses is not automatically an improvement. The v1 five-hypothesis article
benchmark remains unchanged for comparability.


## Completed integration verification

- 38 automated tests passed with one upstream Starlette/AnyIO deprecation warning.
- Next.js production build and TypeScript checks passed.
- Real Chromium browser drove the built frontend against the real FastAPI/model:
  nonpolitical dinner, short-context Taxes, tentative Right, mixed positions,
  sentence diagnostics, mobile width, stale-request clearing, and busy errors.
  No browser page errors were recorded. Desktop/mobile screenshots were inspected.
- A 656-token input was processed in two windows without tail truncation. An
  over-limit request and a localhost URL were rejected.
- The default current Playwright browser download failed with a truncated archive;
  browser testing used Chrome for Testing 131.0.6778.204 instead. This is functional
  development testing, not certification against every supported browser version.
- Final article comparison is in `results/political_debate_comparison.md`.
  Candidate article accuracy is worse than original; no production promotion.

The reusable browser test is `scripts/browser_smoke.cjs`. It requires Playwright
available to Node, the frontend already built, the candidate downloaded, and the
backend dependencies installed. Set `BIASCHECK_TEST_PYTHON` for a nondefault venv
and `BIASCHECK_TEST_BROWSER` for an existing compatible Chromium executable.
It starts and stops its own local frontend/backend. `BIASCHECK_TEST_ARTIFACTS`
controls screenshot output; the default is ignored local research data.
