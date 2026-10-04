# UnBias reliability and lexical refinement development

This cycle diagnoses the archived BASIL60 failures and tests a separate
lexical span refinement candidate. It does not change the deployed website.

- `PROTOCOL.md`: experiment rules and disclosed contract revisions.
- `FAILURES.md` and `failure_findings.json`: targeted native/structured comparison.
- `schema_compatibility.md`: pinned runtime schema-conversion investigation.
- `refinement_v1_aborted.json` and `refinement_v2_aborted.json`: incomplete attempts.
- `refinement_contract_v1.py.txt` and `refinement_contract_v2.py.txt`: exact archived code.
- `runtime.py`, `diagnose.py`, `refine.py`, `compare.py`: reproducible local runners.

Raw news and generated completions stay in ignored research data. Public results
use source hashes and offsets. No newly recruited human annotators participated.
The repeated 60 cases are development data, not an independent accuracy test.

## Reproduction

Use the pinned local runtime and weights in the previous experiment manifest.
The immutable original cases and results must be present under
`research/data/unbias_realnews_basil`. Run each command with a new output directory.
Do not run model commands simultaneously: they own loopback port 8082.

```bash
python research/experiments/unbias_20261004/diagnose.py --output /tmp/diagnose-new
python research/experiments/unbias_20261004/diagnose.py --structured --output /tmp/structured-new
python research/experiments/unbias_20261004/refine.py --output /tmp/refinement-new
python research/experiments/unbias_20261004/compare.py \
  --cases research/data/unbias_realnews_basil/cases.json \
  --baseline research/data/unbias_realnews_basil/run_v1/results.json \
  --refinement /tmp/refinement-new/results.json --output /tmp/comparison-new.json
```

Do not treat a stopped run as completed. The scorer requires all 60 outcomes,
verified unchanged code, a completion timestamp and stopped owned runtime.
