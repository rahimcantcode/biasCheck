# Application and staging review, 2026-10-03

## Scope and decision

Reviewed the actual backend, frontend, deployment files, test configuration and
the live API. Work started from `4268bab42c1186ddcd1fee5b9b80ab4a2ae9f8a4` on
`research/data-quality-team-2026-10-03`. No deployment, service restart,
environment edit, model download, training, or phrase-provider activation was
performed by this workstream. The live service and the development checkout are
different states and must not be described as one verified release.

**Decision: development integration is progressing, but a high-accuracy or
production-ready release is not established.** The new contract probe is ready
for staging. The frontend fix below is locally verified. Human reference labels,
model selection, deployment capacity, and end-to-end staging acceptance remain
separate concerns. The new build-dependency advisory was addressed by the
supported migration described below.

## Independently observed live behavior

The recorded run began at `2026-10-03T13:57:45.340853+00:00` (08:57 Chicago).
It issued one health GET and exactly four sequential POSTs against
`https://bias.r4him.tech/api`. An earlier health-only check also succeeded.
No retries, concurrent traffic, private data, extraction URLs, or load test
were sent. Fixtures are the library/recipe plain-text controls in
`scripts/staging_probe.py`, including tabs, CRLF, boundary whitespace, accents,
and a non-BMP Unicode character. The article control is deliberately long.

| Check | Observation | Interpretation |
|---|---|---|
| Health | HTTP 200, `status=ok` | Service reachable at observation time |
| Release | `release_approved=false`, `demo_mode=true` | Experimental presentation mode remains active |
| Model | RoBERTa weights `548cc7ca4e33a3a76bba015a2ca940d1111d50c5594a9b6b27b4e7bf1719090d` | Original classifier, not a newly promoted model |
| Runtime | Transformers 4.57.1, Torch 2.6.0+cpu | Different from updated research dependency pins |
| Article | HTTP 200, exact source comparison failed; 10.859 s | Live API rewrites submitted text |
| Sentence | HTTP 200, exact source comparison failed; 0.842 s | Same source-contract mismatch |
| Paragraph | HTTP 200, exact source comparison failed; 0.618 s | Same source-contract mismatch |
| Empty spaces | HTTP 400; 0.191 s | Controlled input rejection works |

Evidence: [`live_contract_probe.json`](live_contract_probe.json).

The checks fail at the first contract mismatch. Therefore this live run does
**not** establish token coverage, highlighting behavior, or the later evidence
schema checks. The script has since gained two diagnostic observation fields;
the preserved JSON is the actual earlier output, not reconstructed output.
The single-request times include network and server time and are not latency
percentiles or capacity estimates. No accuracy percentage is derived from them.
The API does not expose a git commit, so its exact deployed commit was not proven.

The development checkout already preserves pasted text in
`backend/utils.py:resolve_input`. The source mismatch demonstrates that the live
service does not meet that new contract; it is not evidence that the new branch's
implementation was deployed and then failed.

## Concrete UI defect fixed

The default RoBERTa engine computed sentence/paragraph results, but
`ResultsPanel.tsx` displayed the passage inspector only for the experimental NLI
engine. This left passage mode controls without visible individual estimates.

The inspector now displays both engines' returned passage results. It preserves
abstention, explains insufficient context and unvalidated modes, labels
uncalibrated class scores, and keeps tentative entailment scores distinct.
It never turns segment labels into colored phrase spans. Original article
highlighting still requires separately supplied exact-source phrase evidence.
Article mode does not gain a duplicate passage inspector.

Five focused rendering tests cover those behaviors, including withheld labels
and absence of manufactured highlights. These are UI contract tests, not model
accuracy measurements. The separate browser checks below exercise the rendered
interface with intercepted synthetic API responses.

## Current local verification

Environment: Python 3.12.14, Node 24.19.0, npm 11.9.0, Next.js 15.5.24.
Hosted CI selects Node 22, so this local environment is not identical to CI.

| Command/check | Current outcome |
|---|---|
| `npm ci --no-audit --no-fund --cache /tmp/biascheck-npm-cache` | Clean lockfile install passed after migration, 65 packages |
| `npm test` | Passed; Node 24's default reporter summarized five test files after the fix |
| `node --test --test-isolation=none --test-reporter=tap .test-build/tests/*.test.js` | All **38 named tests** passed, including five added passage tests |
| `npm run lint` | TypeScript check passed |
| `NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_API_BASE_URL=/api npm run build` | Production build passed; four static pages generated |
| `.venv-team/bin/python -m pytest -q tests/test_staging_probe.py` | **30 tests passed** including a local HTTP fixture |
| Full-tree `npm audit --audit-level=high` | Initially failed with five high findings; **zero findings after migration** |
| Production-only `npm audit --omit=dev --audit-level=high` | Zero reported vulnerabilities before and after migration |
| Local Chromium browser smoke, before and after migration | Desktop and mobile viewport checks passed with synthetic API responses |

The default sandbox blocked network/socket access. Dependency installation,
live checks, audit, and the six loopback transport tests used explicitly
authorized network execution. Twenty-four pure probe tests passed without it.
The lightweight team environment did not initially include `pytest-socket`, so
that plugin's flags were not claimed for this workstream's local test run.

The coordinator independently verified hosted baseline run
[37066293070](https://github.com/rahimcantcode/biasCheck/actions/runs/37066293070)
as successful on `4268bab`. That historical result is separate from local new
changes and from advisory databases that may have changed afterward. The stale
"workflow has not yet run" text in `docs/testing-ci.md` was corrected by the
coordinator. No new commit's hosted run is claimed here.

## Dependency advisory discovered and addressed during this review

The initial full npm audit reported **GHSA-vfj7-8cjw-p6xm / CVE-2026-93687**,
a stack-exhaustion issue in `braces <=3.0.3`. The five package findings are the
affected dependency chain through braces, chokidar, micromatch, fast-glob and
Tailwind CSS. They are not five independently discovered exploits.

The [GitHub-reviewed advisory](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm)
was checked on 2026-10-03 and lists no patched version. `npm view braces version`
returned `3.0.3`. Thus there is no available narrow supported version override
that removes this finding. npm proposes Tailwind 4.3.3, a major migration that
requires stylesheet compatibility and visual checks. Blind `npm audit fix
--force` and advisory suppression were not used.

The frontend now pins `tailwindcss` and `@tailwindcss/postcss` to **4.3.3**,
with compatible `tailwind-merge` **3.7.0**. The old autoprefixer dependency and
v3 config were removed. The old theme is represented in CSS with its exact
custom colors, every used v3 palette value, sans font stack, glow shadow, and
hero radial background. Resets now occupy the base cascade layer. Renamed
radius, shadow, blur and outline classes preserve their old scale and
forced-colors intent, and the default button pointer cursor is explicit.
Source scanning is scoped to app/components/lib, avoiding generated test files.

Clean `npm ci`, both audits, all 38 frontend tests, types and the production
build passed afterward. Independent source review and in-memory PostCSS
compilation verified 17 representative selectors, including custom theme
utilities, highlight radius, focus outline, and backdrop blur. Evidence:
[`frontend_dependency_audit.json`](frontend_dependency_audit.json).

This is not a pixel-identical migration: v4 now generates numeric-opacity
classes such as `/8` and `/12` that v3 had silently ignored, and gradients use
the new default interpolation. The supported browser floor is Safari 16.4+,
Chrome 111+, and Firefox 128+. References:
[official upgrade guide](https://tailwindcss.com/docs/upgrade-guide),
[official PostCSS setup](https://tailwindcss.com/docs/installation/using-postcss),
[tailwind-merge compatibility](https://github.com/dcastil/tailwind-merge).

Production-only audit reported zero findings. Static analysis shows submitted
article text is rendered as React text and is not supplied as a glob pattern to
the frontend build toolchain. That narrows the evident exposure to build/dev
inputs; it is not a blanket statement that the deployed site has no security
risks. The full-tree CI audit gate remains in place. Its passing local result
now comes from a new audit, not yesterday's evidence.

## Local browser verification

The optional `scripts/frontend_visual_smoke.cjs` was executed against a local
production Next.js build on `127.0.0.1:3015`, first with the prior CSS build and
then after restarting the migrated build. Chromium **134.0.6998.35** was used
at **1440 x 1000** and **390 x 844** viewports. The final run began at
`2026-10-03T14:17:12.253Z`. This is local headless browser verification, not cloud
browser, physical phone, Safari, Firefox, or production inference verification.

The browser intercepted every prediction request with a clearly synthetic
response and blocked external page requests. At both widths it verified all
three mode controls, exact displayed Unicode/newline source text, one supplied
phrase highlight, Enter/Escape selection, visible RoBERTa passage estimates,
plain-text toggle and Clear. It found no horizontal overflow or JavaScript
page errors. The input widths, background, link color, highlight radius and
highlight text color remained consistent across the migration. Desktop and
mobile result screenshots were visually inspected for clipping and layout.

Evidence: [`frontend_browser_smoke.json`](frontend_browser_smoke.json),
[desktop screenshot](browser_desktop_results.png), and
[mobile screenshot](browser_mobile_results.png). The pictures show synthetic
scores and phrases supplied by the test, not model predictions.

The bundled Playwright browser download initially returned invalid archives.
An isolated Playwright 1.51.1 installer succeeded through its built-in official
Microsoft download fallback. It was installed under `/tmp`, not added to app
dependencies. The temporary browser only visited this local test interface.
Example rerun once a compatible Playwright/browser is available:

```bash
# First start the built frontend on localhost:3015 in another terminal.
node scripts/frontend_visual_smoke.cjs /tmp/biascheck-browser-smoke
```

`BIASCHECK_BROWSER_EXECUTABLE` optionally selects an installed browser binary.
The helper uses locally installed Playwright or the workspace runtime package;
it is intentionally not an automatic CI browser download.

## Probe usage and limits

Health only, default unapproved release expectation:

```bash
python3 scripts/staging_probe.py --base-url http://127.0.0.1:8000
```

Opt into up to four sequential synthetic POSTs on a staging API:

```bash
python3 scripts/staging_probe.py \
  --base-url https://staging.example/api \
  --run-predictions \
  --expect-release unapproved \
  --expect-evidence unavailable \
  --output staging-contract-result.json
```

The probe checks exact source and segment offsets, complete reported token
coverage, multiple article windows, abstention consistency, finite scores,
model identity, phrase source hashes/offsets when available, controlled empty
input rejection, and expected release/provider state. A healthy model with
poor political predictions can pass all these checks. Conversely, an older
API can fail the new contract while still serving ordinary requests.

Redirects and credential-bearing URLs are refused; responses are limited to
2 MB. Timeout values are bounded. The total budget is checked before each
request, and the socket timeout is an idle timeout rather than a hard process
kill, so a malicious trickling server is outside its wall-clock guarantee.
The probe is intended for an explicitly selected, trusted staging service.

## Operational constraints and remaining acceptance work

- `backend/main.py` permits one active prediction per process and returns 503
  to additional requests. There is no queue or throughput claim. Multiple
  workers would duplicate model memory and each have its own lock.
- Nginx waits up to 1,200 seconds for backend reads. The frontend request has no
  cancellation timeout. Slow inference can occupy the sole inference slot even
  after a user changes the input, although stale responses are guarded from UI
  publication. Profile this before a public multiuser launch.
- RoBERTa allows up to 64 windows and 150 segments. Political NLI limits the
  article to 12 windows and a request to 20 segments. Accepted 100,000-character
  text can still exceed a model's smaller processing limit and receive an error.
- The selected deployment uses systemd, localhost service binds and nginx.
  Closing SSH does not stop systemd-managed services. No SSH/deployment access
  or current VPS memory/CPU capacity was checked during this review.
- The build, server-rendered tests, and the bounded desktop/mobile browser
  interactions above are verified. Browser uploads, delayed network races,
  actual backend integration, HTTPS routing to staging, graceful restart,
  timeout UX, concurrency, memory pressure, and rollback on Hostinger remain
  unverified. Browser fixtures cannot establish real phrase-provider behavior.
- Phrase evidence remains disabled by default. Enabling it requires a pinned
  reviewed model, resource testing and measured human-reference quality. A
  complete JSON schema or valid source offsets are not semantic validation.

The deployment sequence is to stage a fixed
commit with the provider disabled, run this probe, verify the integrated UI in a real
browser, measure resource/concurrency behavior, and retain a rollback commit.
Model release approval still requires the independent data/evaluation work
documented by the other team roles.
