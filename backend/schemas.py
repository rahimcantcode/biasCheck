from typing import Literal
from pydantic import BaseModel, Field
Mode = Literal['article', 'sentence', 'paragraph']
SourceType = Literal['text', 'url']
LabelName = Literal['LEFT', 'RIGHT', 'CENTER']

class PredictRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=100_000)
    mode: Mode = 'article'

class PredictionResult(BaseModel):
    label: LabelName | None
    label_id: int | None
    raw_label: LabelName
    probabilities: dict[LabelName, float]
    decision: Literal['classified', 'abstained']
    reason: str | None
    token_count: int
    tokens_processed: int
    chunk_count: int
    truncated: bool
    calibrated: bool

class SegmentPrediction(PredictionResult):
    segment_index: int
    text: str
    start: int
    end: int

class PredictResponse(BaseModel):
    source_type: SourceType
    resolved_text: str
    mode: Mode
    overall: PredictionResult
    results: list[SegmentPrediction]
    warnings: list[str]
    model: dict

class HealthResponse(BaseModel):
    status: str
    model: dict
    release_approved: bool
