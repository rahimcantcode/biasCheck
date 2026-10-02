# Python dependency security review

Reviewed **2026-10-02**, on Python 3.12.14 / Linux, in a newly created
`.venv-security-test`. No installed package in `.venv-app` was changed. Existing
research results retain their original runtime provenance. Nothing was deployed,
and `release_approved` remains **false**.

The machine-readable record is
[`research/results/python_security_20261002.json`](../research/results/python_security_20261002.json).
It contains exact before/after installed versions, alias-deduplicated advisory
IDs, audit coverage, test results and actual-checkpoint comparison status. The
runtime change passed its original-checkpoint inference/API compatibility smoke.
That check does not establish accuracy, load capacity or deployment readiness.

## What changed

| Package | Previous installed version | Selected version |
| --- | --- | --- |
| FastAPI | 0.115.14 | 0.135.4 |
| Starlette | 0.46.2 (transitive) | 1.3.1 (explicit pin) |
| Transformers | 4.57.1 | 5.10.4 |
| PyTorch CPU | 2.6.0+cpu | 2.13.0+cpu |
| Requests | 2.32.5 | 2.33.0 |
| Protobuf | 5.29.5 | 5.29.6 |
| SentencePiece | 0.2.0 | 0.2.1 |
| setuptools | 78.1.0 | 83.0.0 |
| pytest (test/research) | 8.3.5 | 9.0.3 |
| pip (installer) | 25.0.1 | 26.2 |

These are explicitly tested security-maintenance targets, not a claim that every
package is the newest available. Official version-specific PyPI metadata was
checked before selection. FastAPI 0.115.14's dependency cap could not accept the
required Starlette fixes; [0.135.4 metadata](https://pypi.org/pypi/fastapi/0.135.4/json)
permits Starlette >=0.46.0. Starlette is pinned to avoid silently falling below
this review's baseline. PyTorch uses only its
[official CPU index](https://pytorch.org/get-started/previous-versions/#v2130).
`pip` and `setuptools` are pinned so a fresh CPU-wheel installation does not
retain the older installer/build dependencies observed during this review.

## Counts and scope

Audits used `pip-audit==2.10.1`, its PyPI advisory service, and **no ignored
advisories**. Records sharing any CVE/GHSA/PYSEC/BIT alias were grouped per package;
different aliases and duplicate feed records are not separate vulnerabilities.

- Original provided audit: 69 inventory entries, 36 raw advisory records,
  **20 distinct package/advisory groups across 7 packages**; PyTorch CPU skipped
- Expanded baseline, auditing installed site-packages including pip: 70 inventory
  entries, 48 raw records, **26 distinct groups across 8 packages**; PyTorch CPU skipped
- Supplemental base-version query for PyTorch 2.6.0: 24 raw records,
  **22 distinct advisory groups**; these are additional feed findings, not 22
  demonstrated remote vulnerabilities in this app
- Updated environment: 77 inventory entries, **76 audited and 1 explicitly
  skipped**, with **0 reported advisory records** among those audited
- Supplemental `torch==2.13.0` base-version audit: **0 reported advisories**

The `+cpu` package version is absent from PyPI, so pip-audit cannot directly audit
that wheel. Querying the corresponding upstream version closes a metadata gap;
it does **not** turn this into binary-specific assurance. The report preserves the
skip instead of hiding it with an ignore rule. A clean current database result is
not a claim of zero risk, a complete security assessment, or proof that every
previous advisory was exploitable.

Some upstream advisory records have no declared fixed version but a bounded
affected range. Absence at the selected version means **not reported by this
feed at this version**, rather than independent proof of a remediation commit.
For example, the [custom-generation advisory](https://github.com/advisories/GHSA-x9r9-c232-4q39)
lists affected versions through 5.8.1 without naming a patched version.

## Source-path exposure review

This is a review of the local repository, not an inspection of the running VPS.

- **Starlette:** HTTP serving is relevant, but the inspected app has JSON inputs
  and explicit GET/POST routes. No application `FileResponse`, `StaticFiles`,
  `HTTPEndpoint`, `request.form()`, or `request.url` trust decisions were found.
  Thus the [file-range](https://github.com/Kludex/starlette/security/advisories/GHSA-7f5h-v6xp-fcq8),
  [form-parser](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq)
  and related advisories do not establish exposure through a current route.
  Updating the framework still removes unnecessary dependency risk.
- **Requests:** the article-fetching client is reachable. The vulnerable direct
  call to `extract_zipped_paths()` was not found; the
  [maintainer advisory](https://github.com/psf/requests/security/advisories/GHSA-gc5v-m9x4-r6x2)
  distinguishes it from normal HTTP use.
- **Protobuf / SentencePiece:** no route parses attacker-supplied protobuf `Any`
  structures or accepts tokenizer/model files. The default tokenizer is local
  RoBERTa BPE. Optional model loading must keep using trusted, checked artifacts.
- **Transformers:** serving loads local sequence-classification safetensors.
  X-CLIP/GLM4 conversion, LightGlue, custom generation and untrusted Trainer
  checkpoint-resume paths are not used by the inspected serving routes. Research
  scripts do load/save models, so trusted provenance remains necessary. The
  [save_pretrained path-traversal advisory](https://github.com/advisories/GHSA-xrqw-3rrv-vx5w)
  has a declared fix in 5.10.0, covered by the selected 5.10.4.
- **PyTorch:** serving uses fixed eager RoBERTa operations and safetensors, not
  arbitrary caller-defined tensor operations, `torch.load`, PT2, TorchScript or
  distributed checkpoints. Many baseline records concern those other paths or
  invalid local operator inputs. Do not infer remote app exploitability from
  package presence alone. Follow the
  [upstream model/input trust guidance](https://github.com/pytorch/pytorch/security/policy).
- **pip / setuptools / pytest:** these are installation, build and test surfaces,
  not HTTP handlers. Source archive extraction, build file inclusion and shared
  temporary paths still matter to maintainers. Installs in this review used
  official registries and wheels only, with no downloaded build scripts.

## Compatibility checks

The first candidate exposed two real incompatibilities that mocked API tests
missed:

1. Transformers 5.10.4's RoBERTa lazy import references
   `torch.float8_e8m0fnu`, absent from PyTorch 2.6.0. The CPU runtime was upgraded;
   installed third-party code was not patched or monkeypatched.
2. Transformers v5 removed `build_inputs_with_special_tokens`. The backend keeps
   the v4 method when present. Its v5 fallback uses the tokenizer's own public
   `Encoding.truncate` / post-processor APIs and verifies the exact original
   content IDs and window partition before adding special tokens. It never
   decodes and re-tokenizes window text. Any mismatch fails closed.

Five new synthetic tests cover a tiny random RoBERTa safetensors save/load/forward
pass, the unchanged legacy builder, exact v5 window preparation, and rejected
unsafe/mismatched encodings. They run with network access blocked and require no
model download. The real local tokenizer also produced identical hashes across
v4/v5 for content IDs, windows and final input features in short, Unicode and
1,431-token/four-window examples. Model hashes, aggregation, preprocessing,
window sizes and coverage calculations were not changed. Calibration binding now
additionally requires the complete inference runtime identity described below.

The full isolated suite currently passes **561 tests plus 76 subtests**, including
the new audit-gate tests. Sixteen adapter/runtime-binding tests also pass on the
untouched legacy environment. `pip check`,
the exact CPU-build assertion, shell syntax and diff-whitespace checks pass.
Non-fatal warnings concern SentencePiece SWIG types and the deprecated
Starlette/httpx test-client bridge. No hosted CI run is claimed by these local
results. The original checkpoint's short, Unicode and 1,431-token/four-window cases passed
under both old and new environments. The maximum absolute logit difference was
**1.28323e-6**; all six-decimal scores, token coverage and withheld-label decisions
were identical. Both `/health` and `/predict` returned 200 with release approval
false. Model artifact and processing hashes matched. Both runs observed CPU,
float32, SDPA and batch size 4; library and window-preparation identities changed
as intended. Both compatibility runs used the same updated adapter/binding code;
the legacy run's raw predictions also exactly matched the saved pre-change
baseline. The new `inference_runtime` object is an additive metadata field, not
retroactively attributed to historical reports.

## Calibration is bound to the inference runtime

`model_metadata()` retains top-level library versions and adds
`inference_runtime` schema 1 with exact torch/transformers/tokenizers versions,
window-preparation implementation, observed parameter device and dtype,
observed attention implementation, and configured batch size. The identity is
read after loading the model/tokenizer. Missing, partial, unknown or mistyped
identities fail closed, including when both an old policy and old report omit
identity. Every identity field must match between calibration, held-out
assessment and serving; changing libraries or numeric execution settings
invalidates the old policy even if the checkpoint hashes are unchanged.

The calibration fitter requires this metadata **before** optimizing thresholds.
It copies the identity into a new candidate policy with `release_approved=false`.
Historical reports are preserved as historical evidence and must not be
retrofitted with fabricated runtime metadata. Regenerate evaluation/calibration
under the intended runtime instead. A legacy `decision_policy.json` will be
rejected on startup rather than silently applied to a different runtime.

## Reproduce

Follow [testing-ci.md](testing-ci.md) for fresh installation and all synthetic
tests. For the backend only, `bash backend/setup_env.sh` installs the pinned pip
bootstrap, official CPU wheel, and backend requirements. It must run in a fresh
or explicitly disposable environment, never in an experiment already in flight.

To audit the resulting environment, install `pip-audit==2.10.1` in a separate
auditor environment, then inspect the target environment's site-packages:

```bash
.venv-audit/bin/python -m pip_audit \
  --path .venv-security-test/lib/python3.12/site-packages \
  --format json --aliases --progress-spinner off --output audit-installed.json
printf 'torch==2.13.0\n' > torch-base-version.txt
.venv-audit/bin/python -m pip_audit \
  -r torch-base-version.txt --no-deps --disable-pip \
  --format json --aliases --progress-spinner off --output audit-torch-base.json
```

Retain both outputs and the CPU skip. The supplemental input is a deliberate
base-version lookup, not a replacement for the installed inventory.

## Audit-gate implementation (not enabled for outbound CI checks)

`research/scripts/audit_python_dependencies.py` automates the two audit stages
above. It obtains the actual target inventory (including pip), verifies a separate
isolated auditor and the exact CPU runtime, and requires complete name/version
coverage. Any advisory, unexpected skip, missing package, malformed result,
unexpected diagnostic or failed subprocess makes the gate fail closed. The
expected CPU-wheel skip and base-version limitation stay visible in its JSON.

Its 58 mocked-subprocess tests pass with sockets disabled; existing local audit
samples also pass its coverage checks. After explicit one-time authorization,
the wrapper's live run passed: **77 inventory entries, 76 directly audited,
zero advisories, one preserved CPU-wheel skip**, plus zero advisories for the
supplemental torch 2.13.0 query. The first authorized attempt failed closed on
an unwritable default pip cache; using a temporary writable `PIP_CACHE_DIR`
resolved it without suppressing any diagnostic. The report includes hashes of
the failed and successful raw results. The 58 focused tests were rerun after
that audit-only change; the latest full aggregate run predates it.

Only installed package names and versions were needed for these advisory queries,
not source code, model data, article text or credentials. This was a local
one-time verification, not a hosted CI result. No outbound Python audit step is
enabled in CI and recurring query authorization is not assumed. Only the gate's
offline regression tests run in the ordinary suite.

## Remaining limits

- The default original-checkpoint smoke passed, but optional PoliticalDEBATE
  inference and research training jobs have not been rerun under these dependencies.
- Package resolution is not a full hash-locked build. The report records the
  actual installed transitive versions; another installation date can differ.
- No production inventory, live endpoint penetration test, concurrency/load
  test or operating-system package audit was performed.
- Research model accuracy and deployment authorization remain separate gates.
  No historical result is relabeled as a run with the new dependencies.
