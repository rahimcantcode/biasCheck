"""V4 intervention/isolation invariants; no semantic accuracy claims."""
import ast
from pathlib import Path
import json
from backend.phrase_pipeline_v3 import PROMPTS, payload_for, validate_extraction
from research.scripts.probe_phrase_pipeline_v3 import evaluate_all, stable_hash

ROOT = Path(__file__).resolve().parents[1]
BASE = json.loads((ROOT / 'research/checkpoints/phrase-pipeline-v3-20261002/results.json').read_text())
DEMO = json.loads((ROOT / 'demonstrations.json').read_text())

def functions(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

def test_inference_functions_are_identical_to_v3():
    assert functions(ROOT/'backend/phrase_pipeline_v3.py') == functions(ROOT/'baseline_source/backend/phrase_pipeline_v3.py')
    current = functions(ROOT/'research/scripts/probe_phrase_pipeline_v3.py')
    prior = functions(ROOT/'baseline_source/research/scripts/probe_phrase_pipeline_v3.py')
    for name in ['sha','stable_hash','exact_diagnostic','evaluate_all','run_case','verify_runtime_props','publish']:
        assert current[name] == prior[name], name

def test_prompt_only_appends_extraction_demonstrations():
    old = BASE['protocol']['prompts']
    assert PROMPTS['direction'] == old['direction']
    assert PROMPTS['speaker'] == old['speaker']
    assert PROMPTS['extract'].startswith(old['extract'])
    suffix = PROMPTS['extract'][len(old['extract']):]
    for ex in DEMO:
        assert json.dumps({'source':ex['source']},ensure_ascii=False) in suffix
        assert json.dumps({k:ex[k] for k in ['spans','reason']},ensure_ascii=False) in suffix

def test_demonstrations_align_and_are_balanced_novel_complete_texts():
    assert len(DEMO) == 8
    assert sum(bool(e['spans']) for e in DEMO) == 4
    texts = [r['text'] for f in BASE['protocol']['fixture_snapshots'].values() for r in f['rows']]
    for ex in DEMO:
        assert ex['source'] not in texts
        out = {k:ex[k] for k in ['spans','reason']}
        assert len(validate_extraction(ex['source'],out)) == len(ex['spans'])
        assert all(s['text'] not in text for s in ex['spans'] for text in texts)

def test_evaluator_replays_baseline_exactly():
    for name, suite in BASE['suites'].items():
        replay = evaluate_all(BASE['protocol']['fixture_snapshots'][name]['rows'],suite['predictions'],suite['attempts'])
        assert stable_hash(replay) == stable_hash(suite['metrics'])

def test_same_downstream_requests_and_source_only_extraction_content():
    p = BASE['protocol']
    source = 'We should preserve old-growth forests.'
    candidates = validate_extraction(source, {'spans':[{'text':source[:-1],'context':''}],'reason':'Test fixture'})
    for stage in ['extract','direction','speaker']:
        body = payload_for(stage,source,[] if stage=='extract' else candidates,p)
        content = json.loads(body['messages'][1]['content'])
        assert content['source'] == source
        assert set(content) == ({'source'} if stage=='extract' else {'source','candidates'})
        if stage != 'extract':
            assert body['messages'][0]['content'] == p['prompts'][stage]
        assert body['seed'] == p['seed'] and body['temperature'] == p['temperature']
