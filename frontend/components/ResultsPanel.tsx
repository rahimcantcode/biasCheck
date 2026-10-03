"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Check, Eye, EyeOff, ScanSearch } from "lucide-react";

import type { EvidenceSpan, Label, PredictResponse } from "@/lib/api";
import { buildArticleParts } from "../lib/article";
import { ArticleText } from "./ArticleText";

interface ResultsPanelProps {
  data: PredictResponse | null;
  loading: boolean;
  error: string | null;
}

const LABELS: Label[] = ["LEFT", "CENTER", "RIGHT"];
const ASSESSMENTS: Record<string, string> = { nonpolitical: "No political content detected", insufficient_context: "More context needed", uncertain: "Uncertain", mixed_or_conflicting: "Mixed or conflicting signals" };
const WITHHELD_REASONS: Record<string, string> = {
  insufficient_context: "There is not enough context for a final label.",
  uncertain: "The model's signals are too uncertain for a final label.",
  model_not_validated: "This model has not passed independent validation.",
  mode_not_validated: "This analysis mode has not passed independent validation.",
  experimental_model_not_validated: "This experimental model has not passed independent validation.",
};
const NAMES = { LEFT: "Left", CENTER: "Center", RIGHT: "Right" };
const TEXT_COLORS = { LEFT: "text-blue-300", CENTER: "text-slate-200", RIGHT: "text-red-300" };
const BAR_COLORS = { LEFT: "bg-blue-400", CENTER: "bg-slate-500", RIGHT: "bg-red-400" };

// A fresh response mounts a fresh reader, clearing the previous phrase selection.
export function ResultsPanel({ data, loading, error }: ResultsPanelProps) {
  if (loading) {
    return (
      <section aria-busy="true" aria-label="Analyzing article" className="mx-auto max-w-5xl rounded-[2rem] border border-white/10 bg-[#0d1320] p-7 sm:p-12">
        <p role="status" className="mb-10 flex items-center gap-3 text-sm text-slate-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-blue-300" />
          Reading your article and checking political content. Long articles can take several minutes…
        </p>
        <div aria-hidden="true" className="mx-auto max-w-3xl space-y-8 motion-safe:animate-pulse">
          {[0, 1, 2].map((paragraph) => (
            <div key={paragraph} className="space-y-3">
              <div className="h-3 w-full rounded bg-white/[0.07]" />
              <div className="h-3 w-full rounded bg-white/[0.07]" />
              <div className="h-3 w-4/5 rounded bg-white/[0.07]" />
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section role="alert" className="mx-auto flex max-w-5xl items-start gap-4 rounded-[2rem] border border-red-400/20 bg-red-500/5 p-7">
        <AlertTriangle className="mt-1 h-5 w-5 shrink-0 text-red-300" />
        <div>
          <h2 className="text-lg font-semibold text-white">Analysis failed</h2>
          <p className="mt-1 text-sm leading-6 text-red-100/90">{error}</p>
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="mx-auto max-w-5xl rounded-[2rem] border border-dashed border-white/10 bg-white/[0.02] p-8 text-center sm:p-12">
        <ScanSearch className="mx-auto mb-4 h-6 w-6 text-slate-400" />
        <h2 className="text-xl font-semibold text-white">A clearer way to read the news</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-7 text-slate-400">
          Analyze an article to explore its political leaning and any supported expressions in the original text.
          Phrase annotations are experimental. Text without supported phrase evidence stays plain.
        </p>
      </section>
    );
  }

  return <ArticleReader key={`${data.mode}:${data.resolved_text}:${data.model.weights_sha256}`} data={data} />;
}

function ArticleReader({ data }: { data: PredictResponse }) {
  const [showColors, setShowColors] = useState(true);
  const [selected, setSelected] = useState<EvidenceSpan | null>(null);
  const phraseEvidenceAvailable = data.evidence_status === "available" && data.evidence_metadata?.offset_unit === "unicode_code_point";
  const parts = useMemo(() => buildArticleParts(data.resolved_text, phraseEvidenceAvailable ? data.evidence_spans : []), [data, phraseEvidenceAvailable]);
  const highlightCount = parts.filter(part => part.evidence).length;
  const summary = { ...data.overall, totalWords: data.resolved_text.trim() ? data.resolved_text.trim().split(/\s+/).length : 0 };
  const overall = summary?.label;

  return (
    <section aria-labelledby="article-reader-title" className="mx-auto max-w-5xl overflow-hidden rounded-[2rem] border border-white/10 bg-[#0d1320] shadow-[0_24px_90px_rgba(0,0,0,0.25)]">
      <header className="border-b border-white/[0.08] px-6 py-7 sm:px-10 sm:py-9">
        <div className="mb-4 flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.2em] text-slate-400">
          <Check className="h-3.5 w-3.5 text-slate-300" />
          Analysis complete
        </div>
        <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
          <div>
            <h2 id="article-reader-title" className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">Your article, in perspective.</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              {summary?.totalWords.toLocaleString() ?? 0} words
              <span aria-hidden="true" className="mx-2 text-slate-600">·</span>
              {data.mode === "article" ? "Complete article" : data.mode === "paragraph" ? "Paragraph" : "Sentence"} analysis
            </p>
          </div>
          {summary && (
            <div className="shrink-0 sm:text-right">
              <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Overall leaning</p>
              <p className={`mt-1 text-lg font-medium ${overall ? TEXT_COLORS[overall] : "text-slate-200"}`}>
                {overall ? NAMES[overall] : summary.tentative_label ? `Tentative ${NAMES[summary.tentative_label]}` : summary.assessment ? ASSESSMENTS[summary.assessment] ?? summary.assessment : "No reliable label"}
              </p>
              {summary.reason === "demo_estimate" && <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-amber-200/80">Experimental estimate</p>}
            </div>
          )}
        </div>
        <p className="mt-4 text-xs text-slate-400">{data.overall.tokens_processed.toLocaleString()} of {data.overall.token_count.toLocaleString()} tokens processed in {data.overall.chunk_count} window(s).</p>
        <div className="mt-4 space-y-2">{data.warnings.map(warning => <p key={warning} className="text-sm leading-6 text-amber-100/80">{warning}</p>)}</div>
        {summary && (
          <details className="mt-6">
            <summary className="w-fit cursor-pointer text-xs text-slate-400 transition hover:text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300">
              Inspect experimental scores
            </summary>
            <div className="mt-4 hidden" aria-hidden="true">
              {LABELS.map((label) => <span key={label} className={BAR_COLORS[label]} style={{ width: `${summary.probabilities[label] * 100}%` }} />)}
            </div>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400">
              {LABELS.map((label) => <span key={label}>{NAMES[label]} <span className={TEXT_COLORS[label]}>{(summary.probabilities[label] * 100).toFixed(1)}%</span></span>)}
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">Experimental model support scores, not probabilities of correctness. Entailment scores are independent and need not total 100%. Center means nonaligned political reporting, not factual accuracy or absence of bias.</p>
          </details>
        )}
      </header>

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] bg-white/[0.015] px-6 py-4 sm:px-10">
        <div aria-label="Experimental phrase highlight legend" className="flex flex-wrap gap-x-5 gap-y-2 text-xs">
          {(["LEFT", "RIGHT"] as const).map((label) => (
            <span key={label} className={`flex items-center gap-2 ${TEXT_COLORS[label]}`}>
              <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${BAR_COLORS[label]}`} />
              {NAMES[label]}-leaning expression
            </span>
          ))}
          <span className="text-slate-400">Plain text: no supported author-stance annotation</span>
        </div>
        <button
          type="button"
          aria-pressed={showColors}
          disabled={highlightCount === 0}
          onClick={() => { setShowColors(!showColors); setSelected(null); }}
          className="flex min-h-9 items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-white/25 hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {showColors ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
          Highlight expressions
        </button>
      </div>

      <div className="px-6 py-9 sm:px-10 sm:py-12">
        <div className="mx-auto mb-7 max-w-3xl rounded-xl border border-white/10 bg-white/[0.02] px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-300">Experimental phrase annotations</p>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            {highlightCount > 0
              ? `${highlightCount} model-suggested author expression${highlightCount === 1 ? "" : "s"} found. Blue marks a Left-leaning expression; red marks a Right-leaning expression. Select a highlight to inspect it.`
              : phraseEvidenceAvailable
                ? "No supported author expressions are available to highlight. The original text is shown without highlights, even if an overall model estimate appears above."
                : "No supported phrase-level evidence is available for this article. Phrase analysis is unavailable, so the original text stays plain. An overall model estimate cannot identify specific expressions."}
          </p>
          <p className="mt-2 text-xs leading-5 text-slate-500">Annotations are experimental and may be wrong. Quoted views and uncertain attribution stay plain. Unhighlighted text does not establish neutrality, and highlights do not establish factual accuracy or the author’s overall politics.</p>
        </div>
        <ArticleText parts={parts} showHighlights={showColors} selected={selected} onSelect={setSelected} />
      </div>

      {data.mode !== "article" && (
        <details className="border-t border-white/10 px-6 py-5 sm:px-10">
          <summary className="cursor-pointer text-sm text-slate-300">Inspect experimental passage estimates</summary>
          <p className="mt-3 text-xs leading-6 text-slate-400">Passage estimates can be wrong, and quoted views may differ from the author's position. These scores do not identify specific biased expressions and are not probabilities of correctness.</p>
          <ol className="mt-4 space-y-5">
            {data.results.map(result => (
              <li key={result.segment_index} className="rounded-lg border border-white/10 p-4 text-sm">
                <p className="font-medium text-slate-200">{result.decision === "classified" && result.label
                  ? `Experimental ${NAMES[result.label]} estimate`
                  : result.tentative_label
                    ? `Tentative ${NAMES[result.tentative_label]}`
                    : ASSESSMENTS[result.assessment ?? result.reason ?? ""] ?? "No reliable label"}</p>
                {result.decision === "abstained" && <p className="mt-1 text-xs text-slate-400">Final label withheld. {WITHHELD_REASONS[result.reason ?? ""] ?? "The available context does not support a final label."}</p>}
                <p className="mt-2 whitespace-pre-wrap text-slate-400">{result.text}</p>
                <p className="mt-2 text-xs text-slate-500">{result.score_type === "independent_entailment" ? "Independent model support" : result.calibrated ? "Model support scores" : "Uncalibrated model support"}: {LABELS.map(label => `${NAMES[label]} ${(result.probabilities[label] * 100).toFixed(1)}%`).join(" / ")}</p>
              </li>
            ))}
          </ol>
        </details>
      )}
      <footer className="border-t border-white/[0.08] bg-white/[0.015] px-6 py-5 sm:px-10">
        <p aria-live="polite" aria-atomic="true" className="text-xs leading-6 text-slate-400">
          {selected?.label ? (
            <><span className={`font-medium ${TEXT_COLORS[selected.label]}`}>Experimental {NAMES[selected.label]}-leaning expression</span><span className="mx-2 text-slate-600">·</span>Attributed to the author. {selected.rationale || "No additional explanation was provided."}</>
          ) : highlightCount === 0 ? "No supported author expressions to highlight. Your original text is preserved above." : showColors ? "Select a highlighted expression to inspect its experimental annotation." : "Plain reading view. Turn on Highlight expressions to see experimental annotations."}
        </p>
      </footer>
    </section>
  );
}
