import { API_BASE_URL } from "@/lib/constants";

export type Mode = "article" | "sentence" | "paragraph";
export type SourceType = "text" | "url";
export type Label = "LEFT" | "RIGHT" | "CENTER";

// Half-open Unicode code-point offsets into the exact resolved_text string.
// These annotations are experimental evidence, never segment-label shortcuts.
export interface EvidenceSpan {
  start: number;
  end: number;
  text: string;
  label: "LEFT" | "RIGHT";
  attribution: "author" | "quoted" | "unknown";
  status: "experimental";
  rationale?: string;
}

export interface PredictionProbabilities {
  LEFT: number;
  RIGHT: number;
  CENTER: number;
}

export interface PredictionResult {
  assessment?: string | null;
  tentative_label?: Label | null;
  score_type?: string;
  relevance_scores?: Record<string, number> | null;
  label: Label | null;
  label_id: number | null;
  raw_label: Label;
  decision: "classified" | "abstained";
  reason: string | null;
  token_count: number;
  tokens_processed: number;
  chunk_count: number;
  truncated: boolean;
  calibrated: boolean;
  probabilities: PredictionProbabilities;
}

export interface SegmentResult extends PredictionResult {
  segment_index: number;
  text: string;
  start: number;
  end: number;
}

export interface PredictResponse {
  overall: PredictionResult;
  warnings: string[];
  model: { weights_sha256: string; aggregation: string };
  source_type: SourceType;
  resolved_text: string;
  evidence_spans?: EvidenceSpan[];
  evidence_status?: "available" | "unavailable" | "invalid";
  evidence_metadata?: {
    offset_unit?: "unicode_code_point";
    evidence_source?: string;
    source_text_sha256?: string;
    reason?: string | null;
    calibrated?: boolean;
    release_approved?: boolean;
  };
  mode: Mode;
  results: SegmentResult[];
}

export async function analyzeInput(input: string, mode: Mode): Promise<PredictResponse> {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ input, mode }),
  });

  if (!response.ok) {
    const fallbackMessage = "Analysis failed. Please try again.";
    let message = fallbackMessage;
    try {
      const error = (await response.json()) as { detail?: unknown };
      if (typeof error.detail === "string") message = error.detail;
    } catch { /* Keep fallback for non-JSON upstream errors. */ }
    throw new Error(message);
  }

  const data = (await response.json()) as PredictResponse;
  if (!data.overall) throw new Error("The server needs the updated analysis API. Please update the backend first.");
  return data;
}
