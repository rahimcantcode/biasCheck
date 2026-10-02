import json
import pytest
from research.scripts.run_argument_stance_local import payload,decode,FINGERPRINT


def response():
    return {'system_fingerprint':FINGERPRINT,'usage':{'prompt_tokens':200,'completion_tokens':12},'choices':[{'finish_reason':'stop','message':{'content':'{"id":"article","label":1}'}}]}

def test_payload_preserves_both_context_fields_and_blinds_id():
    row={'id':'reference-hint-id','proposition':'Rephrased claim.','locution':'Exact original\r\nwords.'}
    body=payload(row,'Frozen UK native-task prompt')
    shown=json.loads(body['messages'][1]['content'])
    assert shown=={**row,'id':'article'}
    assert 'reference-hint-id' not in json.dumps(body)
    assert body['max_tokens']==64


def test_label_columns_never_enter_model_context():
    with pytest.raises(ValueError):payload({'id':'1','proposition':'x','locution':'y','gold':1},'prompt')


def test_native_integer_label_not_boolean():
    assert decode(response(),200)==1
    r=response();r['choices'][0]['message']['content']='{"id":"article","label":true}'
    with pytest.raises(ValueError):decode(r,200)

@pytest.mark.parametrize('change',['truncated','tokens','wrong_id','extra_keys','reasoning','runtime'])
def test_native_failures_are_rejected(change):
    r=response()
    if change=='truncated':r['choices'][0]['finish_reason']='length'
    if change=='tokens':r['usage']['prompt_tokens']=201
    if change=='wrong_id':r['choices'][0]['message']['content']='{"id":"other","label":1}'
    if change=='extra_keys':r['choices'][0]['message']['content']='{"id":"article","label":1,"confidence":0.99}'
    if change=='reasoning':r['choices'][0]['message']['reasoning_content']='unrequested'
    if change=='runtime':r['system_fingerprint']='other'
    with pytest.raises(ValueError):decode(r,200)

@pytest.mark.parametrize('content',[None,[],1,'{"id":"article","label":0,"label":1}','{"id":"article","label":NaN}'])
def test_ambiguous_or_nontext_json_is_invalid(content):
    r=response();r['choices'][0]['message']['content']=content
    with pytest.raises(ValueError):decode(r,200)
