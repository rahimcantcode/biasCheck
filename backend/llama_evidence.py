"""Opt-in llama.cpp phrase provider with exact token-capacity preflight.

No account CLI, external endpoint, credentials, tools, or automatic model download.
Weight identity is operator-declared and must match an independently checked launch
manifest; a JSON model name is not cryptographic proof of loaded weights.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from urllib.parse import urlsplit
import requests
try:
    from .evidence import (EVIDENCE_SYSTEM_PROMPT,EXTRACTION_CONTRACT,MAX_TEXT_LENGTH,
                          EvidenceValidationError,_base_response,_local_endpoint,
                          model_output_schema,validate_batch,validate_prediction)
except ImportError:
    from evidence import (EVIDENCE_SYSTEM_PROMPT,EXTRACTION_CONTRACT,MAX_TEXT_LENGTH,
                         EvidenceValidationError,_base_response,_local_endpoint,
                         model_output_schema,validate_batch,validate_prediction)


def bounded_integer(name,default,low,high):
    value=os.getenv(name,default)
    if not value or not value.isascii() or not value.isdecimal() or not low<=int(value)<=high:
        raise EvidenceValidationError(f'Invalid {name}')
    return int(value)


def read_json(session,method,url,payload,deadline):
    remaining=deadline-time.monotonic()
    if remaining<=0:raise EvidenceValidationError('Local inference deadline exceeded')
    with session.request(method,url,json=payload,headers={'Accept-Encoding':'identity'},
                         timeout=(min(2.,remaining),remaining),allow_redirects=False,stream=True) as response:
        if response.status_code!=200:raise EvidenceValidationError('Local inference request did not succeed')
        if response.headers.get('Content-Encoding','identity').lower()!='identity':raise EvidenceValidationError('Compressed responses not allowed')
        size=response.headers.get('Content-Length')
        if size is not None and (not size.isdecimal() or int(size)>1_000_000):raise EvidenceValidationError('Local response too large')
        body=bytearray()
        for piece in response.iter_content(chunk_size=1):
            if time.monotonic()>deadline:raise EvidenceValidationError('Local inference deadline exceeded')
            body.extend(piece)
            if len(body)>1_000_000:raise EvidenceValidationError('Local response too large')
    result=json.loads(body.decode('utf-8'))
    if not isinstance(result,dict):raise EvidenceValidationError('Expected a JSON response object')
    return result


def validate_completion(original,output,input_tokens,context_tokens,max_output_tokens,expected_fingerprint):
    if output.get('system_fingerprint')!=expected_fingerprint:
        raise EvidenceValidationError('Runtime fingerprint differs from configured validated runtime')
    choices=output.get('choices')
    if not isinstance(choices,list) or len(choices)!=1:raise EvidenceValidationError('Expected one model response')
    choice=choices[0]
    if not isinstance(choice,dict) or choice.get('finish_reason')!='stop':raise EvidenceValidationError('Incomplete model response')
    usage=output.get('usage',{})
    if not isinstance(usage,dict):raise EvidenceValidationError('Expected actual token usage object')
    generated=usage.get('completion_tokens')
    if usage.get('prompt_tokens')!=input_tokens:raise EvidenceValidationError('Actual prompt differs from token preflight')
    if type(generated) is not int or not 0<=generated<=max_output_tokens or input_tokens+generated>context_tokens:
        raise EvidenceValidationError('Invalid or overflowing actual token usage')
    message=choice.get('message',{})
    if (not isinstance(message,dict) or message.get('tool_calls') or message.get('reasoning_content')
            or not isinstance(message.get('content'),str)):
        raise EvidenceValidationError('Expected final structured text without tool calls or reasoning')
    return validate_batch([{'id':'article','text':original}],json.loads(message['content']))['article']


def extract_llama_evidence(original):
    result=_base_response(original);result['provider']='llama_cpp'
    started=time.monotonic()
    try:
        endpoint=_local_endpoint(os.getenv('PHRASE_EVIDENCE_ENDPOINT',''))
        model=os.getenv('PHRASE_EVIDENCE_MODEL','')
        fingerprint=os.getenv('PHRASE_EVIDENCE_RUNTIME_FINGERPRINT','')
        weights=os.getenv('PHRASE_EVIDENCE_MODEL_SHA256','')
        if (not model.strip() or len(model)>128 or any(ord(c)<32 for c in model)
                or not fingerprint.strip() or len(fingerprint)>128
                or len(weights)!=64 or any(c not in '0123456789abcdef' for c in weights)):
            raise EvidenceValidationError('Explicit model identity, fingerprint and launch-verified weight hash required')
        character_limit=bounded_integer('PHRASE_EVIDENCE_MAX_INPUT_CHARS','',1,MAX_TEXT_LENGTH)
        context_limit=bounded_integer('PHRASE_EVIDENCE_CONTEXT_TOKENS','',512,131072)
        output_limit=bounded_integer('PHRASE_EVIDENCE_MAX_OUTPUT_TOKENS','1024',1,4096)
        seconds=bounded_integer('PHRASE_EVIDENCE_TIMEOUT_SECONDS','60',1,180)
        if len(original)>character_limit:
            result['reason']='Article exceeds configured input limit; no model request made'
            return result
        payload={'model':model,'temperature':0,'seed':20261002,'max_tokens':output_limit,'stream':False,
                 'chat_template_kwargs':{'enable_thinking':False},
                 'messages':[{'role':'system','content':EVIDENCE_SYSTEM_PROMPT},
                             {'role':'user','content':json.dumps([{'id':'article','text':original}],ensure_ascii=False)}],
                 'response_format':{'type':'json_schema','json_schema':{'name':'phrase_evidence','strict':True,'schema':model_output_schema()}}}
        origin=endpoint.rsplit('/v1/chat/completions',1)[0]
        deadline=started+seconds
        with requests.Session() as session:
            session.trust_env=False
            props=read_json(session,'GET',origin+'/props',None,deadline)
            if props.get('build_info')!=fingerprint or props.get('total_slots')!=1:
                raise EvidenceValidationError('Runtime build or slot count differs from configured tested runtime')
            settings=props.get('default_generation_settings')
            if not isinstance(settings,dict):raise EvidenceValidationError('Expected runtime context settings object')
            actual_context=settings.get('n_ctx')
            if type(actual_context) is not int or actual_context!=context_limit:
                raise EvidenceValidationError('Actual per-slot model context differs from configured context')
            count=read_json(session,'POST',endpoint+'/input_tokens',payload,deadline).get('input_tokens')
            if type(count) is not int or count<1:raise EvidenceValidationError('Invalid exact prompt token count')
            result.update(input_tokens=count,context_tokens=actual_context,max_output_tokens=output_limit)
            if count+output_limit+16>actual_context:
                result['reason']='Complete article and reserved output exceed model token capacity; no generation or truncation performed'
                return result
            output=read_json(session,'POST',endpoint,payload,deadline)
        prediction=validate_completion(original,output,count,actual_context,output_limit,fingerprint)
        result.update(status='available',spans=validate_prediction(original,prediction),reason=prediction['reason'],
                      model=model,model_sha256=weights,runtime_fingerprint=fingerprint,
                      identity_source='Operator configuration; check pinned server launch manifest',
                      prompt_sha256=hashlib.sha256(EVIDENCE_SYSTEM_PROMPT.encode()).hexdigest(),
                      extraction_contract=EXTRACTION_CONTRACT,elapsed_seconds=time.monotonic()-started)
    except requests.RequestException:
        result.update(status='unavailable',spans=[],reason='Local phrase runtime unavailable or timed out; no highlights shown')
    except (EvidenceValidationError,ValueError,TypeError,UnicodeError,RecursionError):
        result.update(status='invalid',spans=[],reason='Local model identity, capacity or evidence validation failed; no highlights shown')
    return result
