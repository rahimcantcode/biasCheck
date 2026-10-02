# Routine quality checks

`.github/workflows/quality.yml` runs on ordinary pull requests and pushes to
`main` or `research/**`. Its single job uses the standard public
`ubuntu-24.04` runner (4 CPUs, 16 GB RAM), a 25-minute timeout and cancellation
of superseded runs for the same branch or pull request. Every job is guarded by
`github.event.repository.private == false`, so a future private-repository
conversion skips this workflow rather than consuming private minutes.

GitHub documents standard public runners as free; larger runners are billable.
This workflow uses no larger/self-hosted runners, uploaded artifacts, dependency
caches, deployment steps, external secrets, or new credentials. Its built-in
GitHub token has only `contents: read`, and checkout does not persist it.
See [runner specifications](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
and [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

As of this configuration update (2026-10-02), the hosted workflow has not yet
run. Local validation does not establish that a GitHub Actions run has passed.

## What a green run establishes

- All tests collected from `tests/`, including metric/abstention contracts,
  input/URL handling, annotation provenance, phrase validation, synthetic HTTP
  fixtures and the Node reviewer DOM/event fixture, pass together
- Frontend unit tests, the existing TypeScript `lint` script and a production
  Next.js build complete using the committed npm lockfile
- `npm audit --audit-level=high` finds no high or critical advisories in the full
  frontend dependency tree, including development dependencies, against the
  registry's advisory data at run time; lower-severity findings do not fail this gate
- The installed PyTorch wheel is the explicitly pinned CPU build, and installed
  Python dependency declarations are consistent (`pip check`)

These are engineering regressions and synthetic tests. They do **not** establish
political-bias accuracy, calibrated confidence, independent annotation quality,
real-model latency, live browser behavior, load capacity, or deployment readiness.
A production build is not a deployment. Release approval remains a separate
model-bound, independently evaluated decision.

## Data and model boundaries

The workflow never downloads model weights, launches a model server, invokes
authenticated inference, trains a classifier, or runs the research experiment
entry points. LFS checkout is disabled, and Hugging Face/Transformers use offline
mode. Only checked-in test fixtures are selected; local `research/data/` and
`research/checkpoints/` directories remain ignored and are not inputs to CI.
Reserved evaluation sets and private/transcript data must stay outside routine
CI and must not be added to its fixtures or logs.

`pytest-socket` restricts ordinary Python test connections to `127.0.0.1` plus
Unix sockets. Loopback is required by the suite's small synthetic HTTP server;
it is not a real inference service. This is a regression guard, not a hostile-code
sandbox: import-time code, subprocesses or an explicitly changed test can escape
that plugin's scope. Review changes to tests and dependencies accordingly.
Package installation, official runtime setup and the npm registry audit need
network access. The audit runs separately from the socket-restricted Python tests.

## Reproduce the commands

Use a clean environment with Python 3.12 and Node 22. From the repository root:

```bash
python3.12 -m venv .venv-ci
source .venv-ci/bin/activate
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export NEXT_TELEMETRY_DISABLED=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONHASHSEED=0
python -m pip install --only-binary=:all: 'torch==2.6.0+cpu' --index-url https://download.pytorch.org/whl/cpu
python -m pip install --only-binary=:all: -r requirements-test.txt
python -m pip check
python -c "import torch; assert torch.__version__ == '2.6.0+cpu' and torch.version.cuda is None, torch.__version__"
python -m pytest -q tests --disable-socket --allow-hosts=127.0.0.1 --allow-unix-socket
cd frontend
npm ci --no-audit --no-fund
npm audit --audit-level=high
npm test
npm run lint
NEXT_PUBLIC_API_BASE_URL=/api npm run build
```

The CPU installation follows [PyTorch's official versioned installation guidance](https://pytorch.org/get-started/previous-versions/).
Backend/research direct dependencies and the extra test plugin are pinned;
frontend resolution uses `package-lock.json`. Python transitive dependencies,
Python/Node patch releases within their selected lines, and the hosted runner
image are not fully locked. This is reproducible test configuration, not a claim
of bit-for-bit hermetic builds. A full platform-specific hash lock can be added
as a separately validated dependency-maintenance change.

## Official action pins

Verified against the official action release commit pages on 2026-10-02:

- [checkout v7.0.1](https://github.com/actions/checkout/commit/3d3c42e5aac5ba805825da76410c181273ba90b1)
- [setup-python v7.0.0](https://github.com/actions/setup-python/commit/5fda3b95a4ea91299a34e894583c3862153e4b97)
- [setup-node v7.0.0](https://github.com/actions/setup-node/commit/820762786026740c76f36085b0efc47a31fe5020)

Update full commit SHAs only after verifying the new official release. Do not
replace them with mutable version tags or introduce `pull_request_target`.
If repository credentials cannot publish workflow files, report that permission
blocker rather than broadening token access or bypassing the restriction.
