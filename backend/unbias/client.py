"""Bounded, local-only transport for the pinned experimental CPU model."""
import json
import os
from urllib.parse import urlsplit
import requests
from .adapter import adapt_unbias_v2
from .prompt import build_messages

MODEL_ID = 'vector-institute/Qwen3-8B-UnBias-Plus-SFT-Instruct-V2'
REVISION = '01a0c8e97ab44b9d2e56d86b6298f2cc74df1222'
FINGERPRINT = 'b11349-fb4b2737a'
MAX_OUTPUT = 2048
CONTEXT = 8192

class FramingUnavailable(Exception):
    pass

class FramingInputTooLong(Exception):
    pass

def enabled():
    return os.getenv('BIASCHECK_UNBIAS_ENABLED', '0') == '1'

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_json_key')
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('nonfinite_json_value')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)

def _post(session, endpoint, path, payload):
    with session.post(endpoint + path, json=payload, timeout=(5, 180),
                      allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise FramingUnavailable('model_http_error')
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 1_000_000:
                raise FramingUnavailable('model_response_too_large')
        return strict_json(data.decode('utf-8'))

def analyze(text):
    if not enabled():
        raise FramingUnavailable('disabled')
    endpoint = os.getenv('BIASCHECK_UNBIAS_ENDPOINT', 'http://127.0.0.1:8082').rstrip('/')
    parts = urlsplit(endpoint)
    if (parts.scheme != 'http' or parts.hostname not in {'127.0.0.1', '::1'}
            or parts.username or parts.password or parts.path or parts.query or parts.fragment):
        raise FramingUnavailable('invalid_local_endpoint')
    payload = dict(model='unbias-plus-v2', messages=build_messages(text), temperature=0,
                   max_tokens=MAX_OUTPUT, stream=False, chat_template_kwargs={'enable_thinking': False})
    try:
        with requests.Session() as session:
            session.trust_env = False
            preflight = _post(session, endpoint, '/v1/chat/completions/input_tokens', payload)
            count = preflight['input_tokens']
            if type(count) is not int or count < 1:
                raise ValueError('invalid_token_count')
            if count + MAX_OUTPUT + 16 > CONTEXT:
                raise FramingInputTooLong()
            output = _post(session, endpoint, '/v1/chat/completions', payload)
        if output.get('system_fingerprint') != FINGERPRINT:
            raise ValueError('runtime_fingerprint_mismatch')
        if output.get('model') != 'unbias-plus-v2':
            raise ValueError('model_alias_mismatch')
        if output.get('usage', {}).get('prompt_tokens') != count:
            raise ValueError('prompt_preflight_mismatch')
        choices = output['choices']
        if len(choices) != 1 or choices[0]['finish_reason'] != 'stop':
            raise ValueError('incomplete_response')
        message = choices[0]['message']
        if message.get('reasoning_content'):
            raise ValueError('unexpected_reasoning')
        result = adapt_unbias_v2(text, strict_json(message['content']))
    except FramingInputTooLong:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        raise FramingUnavailable('invalid_or_unavailable_model_response') from exc
    result.update(resolved_text=text, experimental=True, release_approved=False,
                  model={'id': MODEL_ID, 'revision': REVISION, 'quantization': 'Q4_K_M via Q8_0'},
                  warnings=['Experimental wording suggestions, not political-direction labels or factual verification.',
                            'Speaker attribution is unsupported. Quoted wording does not establish author endorsement.',
                            'Highlight quality has not passed independent human validation.'])
    return result
