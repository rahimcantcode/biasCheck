import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    from .config import get_settings
    from .model import get_model, get_tokenizer, predict_text
    from .schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from .utils import resolve_input, segment_text
except ImportError:  # pragma: no cover - supports `uvicorn main:app` from backend/
    from config import get_settings
    from model import get_model, get_tokenizer, predict_text
    from schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
    from utils import resolve_input, segment_text


logger = logging.getLogger("biaschecker.backend")
settings = get_settings()


app = FastAPI(
    title="Bias Checker API",
    description="Political bias analysis API powered by a fine-tuned RoBERTa model.",
    version="0.1.0",
)

if settings.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def warm_model() -> None:
    # Warm the tokenizer and model on startup so the first request feels less cold.
    logger.info("Starting Bias Checker backend with model directory: %s", settings.model_dir)
    get_tokenizer()
    get_model()


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        source_type, resolved_text = resolve_input(request.input)
        if not resolved_text:
            raise ValueError("Please provide article text or a valid article URL.")

        segments = segment_text(resolved_text, request.mode)
        if not segments:
            raise ValueError("No analyzable content was found after preprocessing.")

        results = []
        for index, segment in enumerate(segments):
            prediction = predict_text(segment)
            results.append(
                SegmentPrediction(
                    segment_index=index,
                    text=segment,
                    label=prediction["label"],
                    label_id=prediction["label_id"],
                    probabilities=prediction["probabilities"],
                )
            )

        return PredictResponse(
            source_type=source_type,
            resolved_text=resolved_text,
            mode=request.mode,
            results=results,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prediction request failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
