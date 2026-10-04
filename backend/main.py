import logging
from contextlib import asynccontextmanager
from threading import Lock
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
try:
    from .config import get_settings
    from .model import get_model, get_tokenizer, model_metadata, predict_sentences
    from .schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from .summary import summarize_predictions
    from .utils import resolve_input, sentence_spans
except ImportError:
    from config import get_settings
    from model import get_model, get_tokenizer, model_metadata, predict_sentences
    from schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from summary import summarize_predictions
    from utils import resolve_input, sentence_spans

logger = logging.getLogger('biaschecker.backend')
settings = get_settings()
inference_lock = Lock()

@asynccontextmanager
async def lifespan(app):
    get_tokenizer()
    get_model()
    yield

app = FastAPI(title='Bias Checker API', version='0.2.0', lifespan=lifespan)
if settings.allowed_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.get('/health', response_model=HealthResponse)
def health_check():
    return HealthResponse(status='ok', model=model_metadata())

@app.post('/predict', response_model=PredictResponse)
def predict(request: PredictRequest):
    if not inference_lock.acquire(blocking=False):
        raise HTTPException(status_code=503, detail='The model is busy. Please try again shortly.')
    try:
        source_type, text = resolve_input(request.input)
        if not text.strip():
            raise ValueError('Please paste article text or enter a valid article URL.')
        if len(text) > 100_000:
            raise ValueError('Please use an article with at most 100,000 characters.')
        # Accept old client mode names, but always perform the same sentence workflow.
        spans = sentence_spans(text)
        if not spans:
            raise ValueError('No sentences were found. Please paste article text.')
        if len(spans) > settings.max_segments:
            raise ValueError(f'Please use at most {settings.max_segments} sentences at a time.')
        predictions = predict_sentences([text[start:end] for start, end in spans])
        results = [SegmentPrediction(segment_index=i, text=text[start:end], start=start, end=end, **prediction)
                   for i, ((start, end), prediction) in enumerate(zip(spans, predictions, strict=True))]
        return PredictResponse(source_type=source_type, resolved_text=text, mode='sentence',
                               results=results, summary=summarize_predictions(predictions), model=model_metadata())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=400, detail='Could not retrieve the article. Please paste its text.') from exc
    except Exception as exc:
        logger.exception('Prediction failed')
        raise HTTPException(status_code=503, detail='Analysis is temporarily unavailable.') from exc
    finally:
        inference_lock.release()
