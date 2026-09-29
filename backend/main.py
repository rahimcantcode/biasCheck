import os
from threading import Lock
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
try:
    from .config import get_settings
    from .model import get_model, get_tokenizer, get_policy, model_metadata, predict_text
    from .schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from .utils import resolve_input, segment_spans
except ImportError:
    from config import get_settings
    from model import get_model, get_tokenizer, get_policy, model_metadata, predict_text
    from schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from utils import resolve_input, segment_spans
ENGINE = os.getenv('BIASCHECK_ENGINE', 'roberta')
if ENGINE not in ('roberta', 'political_nli'):
    raise RuntimeError('BIASCHECK_ENGINE must be roberta or political_nli')
if ENGINE == 'political_nli':
    if __package__:
        from .nli_model import get_model, get_tokenizer, get_policy, model_metadata, predict_text
    else:
        from nli_model import get_model, get_tokenizer, get_policy, model_metadata, predict_text
_inference_lock = Lock()
logger = logging.getLogger('biaschecker.backend')
settings = get_settings()

@asynccontextmanager
async def lifespan(app):
    get_tokenizer()
    get_model()
    get_policy()
    yield

app = FastAPI(title='Bias Checker API', version='0.3.0', lifespan=lifespan)
if settings.allowed_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=False,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.get('/health', response_model=HealthResponse)
def health_check():
    policy = get_policy()
    return HealthResponse(status='ok', model=model_metadata(), release_approved=bool(policy and policy['release_approved']))

@app.post('/predict', response_model=PredictResponse)
def predict(request: PredictRequest):
    if not _inference_lock.acquire(blocking=False):
        raise HTTPException(status_code=503, detail='The model is busy. Please try again shortly.')
    try:
        return _predict(request)
    finally:
        _inference_lock.release()

def _predict(request: PredictRequest):
    try:
        source_type, text = resolve_input(request.input)
        if not text:
            raise ValueError('Please provide article text or a valid article URL.')
        spans = segment_spans(text, request.mode)
        if len(spans) > (20 if os.getenv('BIASCHECK_ENGINE') == 'political_nli' else settings.max_segments):
            raise ValueError('Too many passages. Please use article mode or shorter text.')
        overall = predict_text(text, mode='article')
        results = []
        for index, (start, end) in enumerate(spans):
            item = overall if request.mode == 'article' else predict_text(text[start:end], mode=request.mode)
            results.append(SegmentPrediction(segment_index=index, text=text[start:end], start=start, end=end, **item))
        warnings = []
        if overall.get('score_type') == 'independent_entailment':
            warnings.append('Experimental assessment: this model and its decision rules have not passed independent validation. Tentative results can be wrong, especially for sarcasm, vague criticism, quotations, and mixed positions.')
        if overall['reason'] == 'model_not_validated':
            warnings.append('This checkpoint has not passed independent validation. Political labels are withheld; experimental scores are available below.')
        if request.mode != 'article':
            warnings.append("Passage scores do not establish the author's position. Quotations and surrounding context can change their meaning.")
        warnings.append('This tool estimates U.S. political leaning in English news. It does not check factual accuracy or measure loaded language.')
        return PredictResponse(source_type=source_type, resolved_text=text, mode=request.mode,
                               overall=overall, results=results, warnings=warnings, model=model_metadata())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail='Could not retrieve the article. Please paste its text.') from exc
    except Exception as exc:
        logger.exception('Prediction failed')
        raise HTTPException(status_code=503, detail='Analysis is temporarily unavailable.') from exc
