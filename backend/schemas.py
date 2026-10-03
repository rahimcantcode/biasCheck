from typing import Literal
from pydantic import BaseModel, Field
Mode = Literal['article', 'sentence', 'paragraph']
SourceType = Literal['text', 'url']
LabelName = Literal['LEFT', 'RIGHT', 'CENTER']

class PredictRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=100_000)
    mode: Mode = 'article'

class PredictionResult(BaseModel):
    assessment: str | None = None
    tentative_label: LabelName | None = None
    relevance_scores: dict[str, float] | None = None
    score_type: str = "class_probability"
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

class EvidenceSpan(BaseModel):
    # Python Unicode code-point positions into the exact resolved_text, end exclusive.
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    text: str = Field(min_length=1)
    label: Literal['LEFT', 'RIGHT']
    attribution: Literal['author', 'quoted', 'unknown']
    status: Literal['experimental'] = 'experimental'
    rationale: str = ''

class PredictResponse(BaseModel):
    source_type: SourceType
    resolved_text: str
    mode: Mode
    overall: PredictionResult
    results: list[SegmentPrediction]
    warnings: list[str]
    model: dict
    evidence_spans: list[EvidenceSpan] = Field(default_factory=list)
    evidence_status: Literal['available', 'unavailable', 'invalid'] = 'unavailable'
    evidence_metadata: dict = Field(default_factory=dict)

class HealthResponse(BaseModel):
    status: str
    model: dict
    release_approved: bool

class FramingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)

class FramingSpan(BaseModel):
    start: int = Field(ge=0, strict=True)
    end: int = Field(gt=0, strict=True)
    text: str
    attribution: Literal['unknown']
    reason: str
    bias_type: str
    native_index: int

class FramingResponse(BaseModel):
    status: Literal['suggestions', 'no_suggestions', 'partial_failure']
    resolved_text: str
    source_sha256: str
    spans: list[FramingSpan]
    rejected: list[dict]
    attribution_supported: Literal[False]
    offset_unit: Literal['unicode_codepoint']
    end_exclusive: Literal[True]
    experimental: Literal[True]
    release_approved: Literal[False]
    model: dict
    warnings: list[str]
