import { API_BASE_URL } from "@/lib/constants";

export type Mode = "sentence";
export type SourceType = "text" | "url";
export type Label = "LEFT" | "RIGHT" | "CENTER";

export interface PredictionProbabilities {
  LEFT: number;
  RIGHT: number;
  CENTER: number;
}

export interface SegmentResult {
  segment_index: number;
  text: string;
  label: Label;
  label_id: number;
  probabilities: PredictionProbabilities;
  start: number;
  end: number;
}

export interface ArticleSummary {
  total_sentences: number;
  counts: Record<Label, number>;
  shares: PredictionProbabilities;
  label: Label | null;
  method: "sentence_vote";
}

export interface PredictResponse {
  source_type: SourceType;
  resolved_text: string;
  mode: Mode;
  results: SegmentResult[];
  summary: ArticleSummary;
  model: { model_id: string; revision: string; license: string };
}

export async function analyzeInput(input: string): Promise<PredictResponse> {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ input, mode: "sentence" }),
  });

  if (!response.ok) {
    const fallbackMessage = "Analysis failed. Please try again.";
    let message = fallbackMessage;
    try {
      const error = (await response.json()) as { detail?: unknown };
      if (typeof error.detail === "string") message = error.detail;
    } catch { /* Keep fallback for non-JSON errors. */ }
    throw new Error(message);
  }

  const data = (await response.json()) as PredictResponse;
  if (!data.summary || data.mode !== "sentence") {
    throw new Error("The server needs the sentence-analysis update. Please update the backend first.");
  }
  return data;
}
