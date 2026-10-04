"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, Check, Eye, EyeOff, ScanSearch } from "lucide-react";

import type { Label, PredictResponse, SegmentResult } from "@/lib/api";
import { buildArticleParts } from "../lib/article";

interface ResultsPanelProps {
  data: PredictResponse | null;
  loading: boolean;
  error: string | null;
}

const LABELS: Label[] = ["LEFT", "CENTER", "RIGHT"];
const NAMES = { LEFT: "Left", CENTER: "Center", RIGHT: "Right" };
const TEXT_COLORS = { LEFT: "text-blue-300", CENTER: "text-slate-200", RIGHT: "text-red-300" };
const BAR_COLORS = { LEFT: "bg-blue-400", CENTER: "bg-slate-500", RIGHT: "bg-red-400" };

// A fresh response mounts a fresh reader, clearing the previous passage selection.
export function ResultsPanel({ data, loading, error }: ResultsPanelProps) {
  if (loading) {
    return (
      <section aria-busy="true" aria-label="Analyzing article" className="mx-auto max-w-5xl rounded-[2rem] border border-white/10 bg-[#0d1320] p-7 sm:p-12">
        <p role="status" className="mb-10 flex items-center gap-3 text-sm text-slate-300">
          <span className="h-2 w-2 animate-pulse rounded-full bg-blue-300" />
          Reading your article and mapping its political leaning…
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
          Analyze an article to see its political leaning directly in the text.
          Left in blue. Right in red. Center stays neutral.
        </p>
      </section>
    );
  }

  return <ArticleReader key={`${data.resolved_text}:${data.model.revision}`} data={data} />;
}

function ArticleReader({ data }: { data: PredictResponse }) {
  const [showColors, setShowColors] = useState(true);
  const [selected, setSelected] = useState<SegmentResult | null>(null);
  const parts = useMemo(() => buildArticleParts(data.resolved_text, data.results), [data]);
  const summary = data.summary;
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
              {summary.total_sentences.toLocaleString()} sentences
              <span aria-hidden="true" className="mx-2 text-slate-600">·</span>
              Sentence analysis
            </p>
          </div>
          {summary && (
            <div className="shrink-0 sm:text-right">
              <p className="text-[10px] uppercase tracking-[0.18em] text-slate-500">Overall sentence leaning</p>
              <p className={`mt-1 text-lg font-medium ${overall ? TEXT_COLORS[overall] : "text-slate-200"}`}>
                {overall ? NAMES[overall] : "Tie"}
              </p>
            </div>
          )}
        </div>
        {summary && (
          <div className="mt-6" aria-label="Sentence count breakdown">
            <div className="mt-4 flex h-1.5 overflow-hidden rounded-full" aria-hidden="true">
              {LABELS.map((label) => <span key={label} className={BAR_COLORS[label]} style={{ width: `${summary.shares[label] * 100}%` }} />)}
            </div>
            <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-xs text-slate-400">
              {LABELS.map((label) => <span key={label}>{NAMES[label]} <span className={TEXT_COLORS[label]}>{summary.counts[label]} ({(summary.shares[label] * 100).toFixed(1)}%)</span></span>)}
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">Each sentence counts once. The most common model label determines the overall leaning.</p>
          </div>
        )}
      </header>

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/[0.06] bg-white/[0.015] px-6 py-4 sm:px-10">
        <div aria-label="Text color legend" className="flex flex-wrap gap-x-5 gap-y-2 text-xs">
          {LABELS.map((label) => (
            <span key={label} className={`flex items-center gap-2 ${TEXT_COLORS[label]}`}>
              <span aria-hidden="true" className={`h-1.5 w-1.5 rounded-full ${BAR_COLORS[label]}`} />
              {NAMES[label]}
            </span>
          ))}
        </div>
        <button
          type="button"
          aria-pressed={showColors}
          onClick={() => { setShowColors(!showColors); setSelected(null); }}
          className="flex min-h-9 items-center gap-2 rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-white/25 hover:bg-white/5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-blue-300"
        >
          {showColors ? <Eye className="h-3.5 w-3.5" /> : <EyeOff className="h-3.5 w-3.5" />}
          Color bias
        </button>
      </div>

      <div className="px-6 py-9 sm:px-10 sm:py-12">
        <article aria-label="Analyzed article" className="mx-auto max-w-3xl whitespace-pre-wrap break-words font-serif text-[18px] leading-[1.95] text-slate-200 sm:text-[20px]">
          {parts.map((part, index) => {
            const result = part.result;
            if (!result || !showColors) return <span key={index}>{part.text}</span>;
            const confidence = (result.probabilities[result.label] * 100).toFixed(1);
            const description = `${NAMES[result.label]} leaning, ${confidence}% model score`;
            const active = selected === result;
            return (
              <span
                key={index}
                role="button"
                tabIndex={0}
                aria-label={`${description}: ${part.text}`}
                aria-pressed={active}
                title={description}
                onClick={() => setSelected(active ? null : result)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setSelected(active ? null : result);
                  }
                  if (event.key === "Escape") setSelected(null);
                }}
                className={`cursor-pointer rounded-sm decoration-1 underline-offset-[5px] transition-colors hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-400 ${TEXT_COLORS[result.label]} ${active ? "bg-white/5 underline" : ""}`}
              >
                {part.text}
              </span>
            );
          })}
        </article>
      </div>

      <footer className="border-t border-white/[0.08] bg-white/[0.015] px-6 py-5 sm:px-10">
        <p aria-live="polite" aria-atomic="true" className="text-xs leading-6 text-slate-400">
          {selected ? (
            <><span className={`font-medium ${TEXT_COLORS[selected.label]}`}>{NAMES[selected.label]} leaning</span><span className="mx-2 text-slate-600">·</span>{(selected.probabilities[selected.label] * 100).toFixed(1)}% model score for this sentence.</>
          ) : showColors ? "Select any sentence to inspect its prediction. Center text keeps its natural color." : "Plain reading view. Turn on Color bias to see the predictions in the text."}
        </p>
      </footer>
    </section>
  );
}
