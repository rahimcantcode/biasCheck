import { API_BASE_URL } from "@/lib/constants";

export type Mode = "article" | "sentence" | "paragraph";
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
}

export interface PredictResponse {
  source_type: SourceType;
  resolved_text: string;
  mode: Mode;
  results: SegmentResult[];
}

export async function analyzeInput(input: string, mode: Mode): Promise<PredictResponse> {
  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    // Article view needs passage predictions, not a single truncated article label.
    body: JSON.stringify({ input, mode: mode === "article" ? "sentence" : mode }),
  });

  if (!response.ok) {
    const fallbackMessage = "Analysis failed. Please try again.";
    try {
      const error = (await response.json()) as { detail?: string };
      throw new Error(error.detail ?? fallbackMessage);
    } catch {
      throw new Error(fallbackMessage);
    }
  }

  const data = (await response.json()) as PredictResponse;
  return { ...data, mode };
}
