# BASIL real-news evaluation

This directory evaluates the already-pinned quantized 8B candidate on 60 original news sentences with published human references. The candidate prompt, adapter, endpoint and website are not modified. Read `PROTOCOL.md` for the frozen task and limits, `sample_manifest.json` for provenance and sample identities, and `REPORT.md` for the completed findings once generated.

The reference labels are BASIL release 2's original human annotations. No new humans have reviewed the sample, and no machine-generated labels are represented as human labels. The sample contains 60 separate event IDs. Forty sentences have human bias annotations; twenty have none. Lexical versus informational group membership is kept separate because the latter depends more strongly on broader context.

The 5,000-row released fine-tuning snapshot contains no shared normalized 13-word sequence with any of the 6,135 eligible BASIL candidate sentences. None of the selected 60 sentences is an exact normalized substring of a training article. This check does not establish absence of paraphrases, event overlap, undisclosed training data, or base-model pretraining exposure. The training snapshot is newer than the model snapshot.

## Reproduce

From the repository root, choose a NEW data directory under ignored `research/data/`:

```bash
python research/experiments/unbias_20261003/realnews_basil60/fetch_sources.py --data research/data/basil60-reproduction
python research/experiments/unbias_20261003/realnews_basil60/prepare.py --data research/data/basil60-reproduction
python -m unittest discover -s research/experiments/unbias_20261003/realnews_basil60 -p test_score.py -v
python research/experiments/unbias_20261003/realnews_basil60/run.py --cases research/data/basil60-reproduction/cases.json --output research/data/basil60-reproduction/run_v1
python research/experiments/unbias_20261003/realnews_basil60/score.py --cases research/data/basil60-reproduction/cases.json --results research/data/basil60-reproduction/run_v1/results.json --output research/data/basil60-reproduction/summary.json
```

The model and runtime must exist at the paths in the parent `native_runtime_manifest.json`. The prior conversion/runtime documentation describes those artifacts. Backend dependencies, including FastAPI, uvicorn, requests, and PyTorch, are required; the completed run uses the existing CPU environment. Loopback ports 8082 and 8093 must be free. The runner checks model/runtime hashes and source text, captures every API response/failure, and shuts down its own processes. It bypasses startup of the unrelated legacy article classifier, so simultaneous model capacity and deployed site behavior remain untested.

Scoring requires exactly the full frozen case order, a completed run, matching source hashes, and terminated owned processes. Raw source text and responses stay in ignored local research data. The tracked result contains IDs, offsets, labels, metrics, timing and source bindings, not copied news articles or generated rewrites. Sample preparation refuses to overwrite a differing fixture or manifest. If changing the candidate, protocol, or sample, use a new experiment instead of overwriting this one.

Seven small scoring tests cover one-to-one span matching, oversized highlights, punctuation-only overlap, failures, negative controls, duplicate reference spans, and nonzero uncertainty with zero observed false positives. They validate measurement logic, not model quality.

## Sources

- [BASIL release 2](https://github.com/launchnlp/BASIL/tree/4fdbc4f68d5ddae648990063cb6dd11424d96222)
- [Fan et al., 2019, In Plain Sight](https://aclanthology.org/D19-1664/)
- [Pinned model card](https://huggingface.co/vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2/tree/01a0c8e97ab44b9d2e56d86b6298f2cc74df1222)
- [Released training dataset snapshot](https://huggingface.co/datasets/vector-institute/unbias-plus-dataset/tree/2e0a842ca594549a510ac527e2222b82d04b9784)

This is evaluation of publicly released research data, not a declaration of blanket permission to redistribute news articles or train a commercial model on them.
