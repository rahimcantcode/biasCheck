"""Structural controls for v5; no model correctness assertions."""
from copy import deepcopy
import json
from pathlib import Path
import ast
import pytest
from backend.phrase_pipeline_v3 import PROMPTS,validate_extraction,payload_for
from v5_experiment import arm_prompts,set_arm,load_sealed,ROOT

BASE=json.loads((ROOT/'research/checkpoints/phrase-recall-v4-20261002/results.json').read_text())
DEMOS=json.loads((ROOT/'direction_demonstrations.json').read_text())

def test_only_direction_text_changes():
    arms=arm_prompts(BASE['protocol']['prompts'],DEMOS)
    assert arms['v4']==BASE['protocol']['prompts']
    for s in ('extract','speaker'):assert arms['v4'][s]==arms['v5'][s]
    assert arms['v5']['direction'].startswith(arms['v4']['direction'])
    assert arms['v5']['direction']!=arms['v4']['direction']

def test_demonstrations_balance_and_exact_alignment():
    labels=[e['direction'] for e in DEMOS]
    assert labels.count('LEFT')==2 and labels.count('RIGHT')==2 and labels.count('NO_DIRECTION')==4
    old=[r['text'] for f in BASE['protocol']['fixture_snapshots'].values() for r in f['rows']]
    for e in DEMOS:
        assert e['source'] not in old
        c=validate_extraction(e['source'],{'spans':[{'text':e['candidate'],'context':''}],'reason':'Test'})
        assert len(c)==1 and e['source'][c[0]['start']:c[0]['end']]==e['candidate']
        assert all(e['candidate'] not in text for text in old)

def test_arm_switch_changes_only_direction_request():
    old=deepcopy(PROMPTS)
    p=deepcopy(BASE['protocol']);p['prompts']=arm_prompts(p['prompts'],DEMOS)
    src='Private forests should remain protected.'
    c=validate_extraction(src,{'spans':[{'text':src[:-1],'context':''}],'reason':'Test'})
    try:
        bodies={}
        for arm in ('v4','v5'):
            set_arm(p,arm)
            bodies[arm]={s:payload_for(s,src,[] if s=='extract' else c,p) for s in ('extract','direction','speaker')}
        assert bodies['v4']['extract']==bodies['v5']['extract']
        assert bodies['v4']['speaker']==bodies['v5']['speaker']
        a,b=deepcopy(bodies['v4']['direction']),deepcopy(bodies['v5']['direction'])
        a['messages'][0]['content']=b['messages'][0]['content']='PROMPT'
        assert a==b
    finally:PROMPTS.clear();PROMPTS.update(old)

def test_sealed_cannot_load_without_freeze(tmp_path):
    with pytest.raises(ValueError):load_sealed({'protocol':{'sealed_fixture_path':str(tmp_path/'missing')}})

def test_prepare_does_not_parse_sealed_case_file():
    tree=ast.parse((ROOT/'v5_experiment.py').read_text())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
    text=ast.unparse(fn)
    assert 'load_sealed(' not in text
    assert 'sealed_file.read_text' not in text
    assert 'sha(sealed_file)' in text
