from typing import Dict, List, Literal

from pydantic import BaseModel, Field


Mode = Literal["article", "sentence", "paragraph"]
SourceType = Literal["text", "url"]
LabelName = Literal["LEFT", "RIGHT", "CENTER"]


class PredictRequest(BaseModel):
    input: str = Field(..., min_length=1, description="Raw article text or a URL.")
    mode: Mode = "article"


class PredictionResult(BaseModel):
    label: LabelName
    label_id: int
    probabilities: Dict[LabelName, float]


class SegmentPrediction(PredictionResult):
    segment_index: int
    text: str


class PredictResponse(BaseModel):
    source_type: SourceType
    resolved_text: str
    mode: Mode
    results: List[SegmentPrediction]


class HealthResponse(BaseModel):
    status: str
