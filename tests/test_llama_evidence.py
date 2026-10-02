"""Token-capacity/runtime checks use mock responses, not claimed model accuracy."""
import json
from unittest.mock import patch
import pytest
from backend.evidence import extract_phrase_evidence
from backend.llama_evidence import validate_completion

TEXT='my cat is pretty and taxing the rich is good'
FP='b11349-fb4b2737a'
ENV={'PHRASE_EVIDENCE_PROVIDER':'llama_cpp','PHRASE_EVIDENCE_ENDPOINT':'http://127.0.0.1:8081/v1/chat/completions',
     'PHRASE_EVIDENCE_MODEL':'Qwen/Qwen3-4B-GGUF','PHRASE_EVIDENCE_MODEL_SHA256':'a'*64,
     'PHRASE_EVIDENCE_RUNTIME_FINGERPRINT':FP,'PHRASE_EVIDENCE_MAX_INPUT_CHARS':'10000',
     'PHRASE_EVIDENCE_CONTEXT_TOKENS':'4096','PHRASE_EVIDENCE_MAX_OUTPUT_TOKENS':'1024'}
PROPS={'default_generation_settings':{'n_ctx':4096},'build_info':FP,'total_slots':1}

def completion():
    pred={'id':'article','spans':[{'text':'taxing the rich is good','occurrence':0,'label':'LEFT','attribution':'author','reason':'Synthetic test fixture'}],'reason':'Synthetic fixture'}
    return {'system_fingerprint':FP,'usage':{'prompt_tokens':532,'completion_tokens':80},
            'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'predictions':[pred]})}}]}

def test_identical_payload_counted_then_generated_with_explicit_budget():
    with patch.dict('os.environ',ENV,clear=True),patch('backend.llama_evidence.read_json',side_effect=[PROPS,{'input_tokens':532},completion()]) as request:
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='available' and r['input_tokens']==532 and r['max_output_tokens']==1024
    assert r['model_sha256']=='a'*64 and r['runtime_fingerprint']==FP
    calls=request.call_args_list
    assert calls[0].args[2]=='http://127.0.0.1:8081/props'
    assert calls[1].args[2].endswith('/input_tokens') and calls[2].args[2].endswith('/chat/completions')
    assert calls[1].args[3] is calls[2].args[3]
    assert calls[2].args[3]['chat_template_kwargs']=={'enable_thinking':False}
    assert json.loads(calls[2].args[3]['messages'][1]['content'])==[{'id':'article','text':TEXT}]


def test_full_prompt_plus_output_margin_rejected_before_generation():
    with patch.dict('os.environ',ENV,clear=True),patch('backend.llama_evidence.read_json',side_effect=[PROPS,{'input_tokens':3060}]) as request:
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='unavailable' and r['spans']==[] and request.call_count==2
    assert 'no generation or truncation' in r['reason']

@pytest.mark.parametrize('change',[{'build_info':'other'},{'total_slots':2},{'default_generation_settings':{'n_ctx':2048}},{'default_generation_settings':{'n_ctx':True}},
                                  {'default_generation_settings':None},{'default_generation_settings':[]},{'default_generation_settings':'bad'}])
def test_actual_runtime_mismatch_stops_before_source_tokenization(change):
    with patch.dict('os.environ',ENV,clear=True),patch('backend.llama_evidence.read_json',return_value={**PROPS,**change}) as request:
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='invalid' and request.call_count==1

@pytest.mark.parametrize('key,value',[
 ('PHRASE_EVIDENCE_MODEL_SHA256',''),('PHRASE_EVIDENCE_RUNTIME_FINGERPRINT',''),
 ('PHRASE_EVIDENCE_ENDPOINT','https://outside.example/v1/chat/completions'),
 ('PHRASE_EVIDENCE_CONTEXT_TOKENS',''),('PHRASE_EVIDENCE_MAX_OUTPUT_TOKENS','8192'),
 ('PHRASE_EVIDENCE_TIMEOUT_SECONDS','0')])
def test_invalid_configuration_makes_no_network_call(key,value):
    with patch.dict('os.environ',{**ENV,key:value},clear=True),patch('backend.llama_evidence.read_json') as request:
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='invalid' and request.call_count==0

@pytest.mark.parametrize('mutation',['fingerprint','input_tokens','output_tokens','truncated','reasoning','tools'])
def test_actual_generation_must_match_preflight(mutation):
    r=completion()
    if mutation=='fingerprint':r['system_fingerprint']='wrong'
    if mutation=='input_tokens':r['usage']['prompt_tokens']=531
    if mutation=='output_tokens':r['usage']['completion_tokens']=1025
    if mutation=='truncated':r['choices'][0]['finish_reason']='length'
    if mutation=='reasoning':r['choices'][0]['message']['reasoning_content']='unexpected reasoning'
    if mutation=='tools':r['choices'][0]['message']['tool_calls']=[{'x':'test'}]
    with pytest.raises(ValueError):validate_completion(TEXT,r,532,4096,1024,FP)


def test_original_character_limit_sends_no_source():
    with patch.dict('os.environ',{**ENV,'PHRASE_EVIDENCE_MAX_INPUT_CHARS':'10'},clear=True),patch('backend.llama_evidence.read_json') as request:
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='unavailable' and request.call_count==0

@pytest.mark.parametrize('usage',[None,[],"bad"])
def test_malformed_usage_fails_closed_without_attribute_error(usage):
    output=completion();output['usage']=usage
    with patch.dict('os.environ',ENV,clear=True),patch('backend.llama_evidence.read_json',side_effect=[PROPS,{'input_tokens':532},output]):
        r=extract_phrase_evidence(TEXT)
    assert r['status']=='invalid' and r['spans']==[]
