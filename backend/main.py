from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model import get_model, get_tokenizer, predict_text
from schemas import HealthResponse, PredictRequest, PredictResponse, SegmentPrediction
from utils import resolve_input, segment_text


app = FastAPI(
    title="Bias Checker API",
    description="Political bias analysis API powered by a fine-tuned RoBERTa model.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warm_model() -> None:
    # Warm the tokenizer and model on startup so the first request feels less cold.
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
