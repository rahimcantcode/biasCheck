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

# Only these static values may reach ordinary application logs.
_DIAGNOSTIC_CODES = {
    'disabled', 'invalid_local_endpoint', 'model_http_error',
    'model_response_too_large', 'model_timeout', 'model_transport_error',
    'invalid_outer_json', 'invalid_native_json', 'duplicate_json_key',
    'nonfinite_json_value', 'invalid_token_count', 'invalid_metadata',
    'runtime_fingerprint_mismatch', 'model_alias_mismatch',
    'prompt_preflight_mismatch', 'incomplete_response', 'unexpected_reasoning',
    'invalid_native_schema', 'invalid_severity_or_segments', 'inconsistent_severity',
    'invalid_or_unavailable_model_response',
}
_DIAGNOSTIC_STAGES = {'configuration', 'transport', 'outer_json', 'metadata',
                      'native_json', 'native_schema', 'unknown'}

class FramingUnavailable(Exception):
    """Safe log summary; the original exception is retained only as __cause__."""
    def __init__(self, code, stage='unknown'):
        self.code = code if code in _DIAGNOSTIC_CODES else 'invalid_or_unavailable_model_response'
        self.stage = stage if stage in _DIAGNOSTIC_STAGES else 'unknown'
        super().__init__(f'{self.stage}:{self.code}')


def _failure(exc, stage):
    if isinstance(exc, requests.Timeout):
        return FramingUnavailable('model_timeout', 'transport')
    if isinstance(exc, requests.RequestException):
        return FramingUnavailable('model_transport_error', 'transport')
    fallback = {'outer_json': 'invalid_outer_json', 'native_json': 'invalid_native_json',
                'metadata': 'invalid_metadata', 'native_schema': 'invalid_native_schema'}
    # Do not stringify arbitrary exceptions: JSON errors and transport errors can
    # contain source text, completions, URLs or credentials.
    code = exc.args[0] if type(exc) is ValueError and len(exc.args) == 1 else None
    if not isinstance(code, str) or code not in _DIAGNOSTIC_CODES:
        code = fallback.get(stage, 'invalid_or_unavailable_model_response')
    return FramingUnavailable(code, stage)

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
    stage = 'transport'
    try:
        with session.post(endpoint + path, json=payload, timeout=(5, 180),
                          allow_redirects=False, stream=True) as response:
            if response.status_code != 200:
                raise FramingUnavailable('model_http_error', stage)
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data) > 1_000_000:
                    raise FramingUnavailable('model_response_too_large', stage)
            stage = 'outer_json'
            return strict_json(data.decode('utf-8'))
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise _failure(exc, stage) from exc


def analyze(text, diagnostics=None):
    """Analyze text; explicit research callers may retain raw diagnostics.

    The optional dictionary contains potentially sensitive input and model
    output. The HTTP endpoint never supplies it, and this module never logs it.
    """
    if not enabled():
        raise FramingUnavailable('disabled', 'configuration')
    endpoint = os.getenv('BIASCHECK_UNBIAS_ENDPOINT', 'http://127.0.0.1:8082').rstrip('/')
    try:
        parts = urlsplit(endpoint)
        port = parts.port  # Validate malformed/out-of-range ports before requests.
        if (parts.scheme != 'http' or parts.hostname not in {'127.0.0.1', '::1'}
                or parts.username or parts.password or parts.path or parts.query or parts.fragment):
            raise ValueError('invalid_local_endpoint')
    except ValueError as exc:
        raise FramingUnavailable('invalid_local_endpoint', 'configuration') from exc
    payload = dict(model='unbias-plus-v2', messages=build_messages(text), temperature=0,
                   max_tokens=MAX_OUTPUT, stream=False, chat_template_kwargs={'enable_thinking': False})
    structured = os.getenv('BIASCHECK_UNBIAS_STRUCTURED', '0') == '1'
    if structured:
        from .native_schema import response_format
        payload['response_format'] = response_format()
    if diagnostics is not None:
        diagnostics['payload'] = payload
    stage = 'transport'
    try:
        with requests.Session() as session:
            session.trust_env = False
            preflight = _post(session, endpoint, '/v1/chat/completions/input_tokens', payload)
            if diagnostics is not None:
                diagnostics['preflight'] = preflight
            stage = 'metadata'
            count = preflight['input_tokens']
            if type(count) is not int or count < 1:
                raise ValueError('invalid_token_count')
            if count + MAX_OUTPUT + 16 > CONTEXT:
                raise FramingInputTooLong()
            stage = 'transport'
            output = _post(session, endpoint, '/v1/chat/completions', payload)
        if diagnostics is not None:
            diagnostics['output'] = output
        stage = 'metadata'
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
        content = message['content']
        stage = 'native_json'
        native = strict_json(content)
        if diagnostics is not None:
            diagnostics['native'] = native
        stage = 'native_schema'
        result = adapt_unbias_v2(text, native)
    except FramingInputTooLong:
        raise
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        raise _failure(exc, stage) from exc
    result.update(resolved_text=text, experimental=True, release_approved=False,
                  model={'id': MODEL_ID, 'revision': REVISION, 'quantization': 'Q4_K_M via Q8_0',
                         'structured_output': structured},
                  warnings=['Experimental wording suggestions, not political-direction labels or factual verification.',
                            'Speaker attribution is unsupported. Quoted wording does not establish author endorsement.',
                            'Highlight quality has not passed independent human validation.'])
    return result
