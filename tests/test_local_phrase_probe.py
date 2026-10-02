import copy
import json
import pytest
from research.scripts.probe_local_phrase_evidence import payload_for,decode_response
from backend.evidence import EVIDENCE_SYSTEM_PROMPT,model_output_schema

ROW={'id':'a','text':'My cat is pretty and taxing the rich is good.'}
PROTOCOL={'model':'local-model','temperature':0,'seed':20261002,'output_token_limit':1024,
          'prompt':EVIDENCE_SYSTEM_PROMPT,'schema':model_output_schema()}

def output():
    p={'id':'a','spans':[{'text':'taxing the rich is good','occurrence':0,'label':'LEFT','attribution':'author','reason':'Synthetic expected fixture'}], 'reason':'Synthetic fixture'}
    return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'predictions':[p]})}}], 'usage':{'prompt_tokens':50}}

def test_no_expected_judgments_are_passed_to_model():
    r={**ROW,'expected':['PRIVATE TEST EXPECTATION']};b=payload_for(r,PROTOCOL)
    assert json.loads(b['messages'][1]['content'])==[ROW]
    assert 'PRIVATE TEST EXPECTATION' not in json.dumps(b)
    assert b['chat_template_kwargs']=={'enable_thinking':False}
    assert b['max_tokens']==1024 and b['seed']==20261002

def test_exact_valid_response():
    assert decode_response(ROW,output(),50)['spans'][0]['text']=='taxing the rich is good'

@pytest.mark.parametrize('mutation',['tokens','truncated','missing','tool','fabricated'])
def test_bad_outputs_are_not_valid_semantic_results(mutation):
    r=output()
    if mutation=='tokens':r['usage']['prompt_tokens']=49
    if mutation=='truncated':r['choices'][0]['finish_reason']='length'
    if mutation=='missing':r['choices']=[]
    if mutation=='tool':r['choices'][0]['message']['tool_calls']=[{'x':'test'}]
    if mutation=='fabricated':r['choices'][0]['message']['content']=r['choices'][0]['message']['content'].replace('taxing the rich is good','invented evidence')
    with pytest.raises(ValueError):decode_response(ROW,r,50)
