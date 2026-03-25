"use client";

import { useMemo } from "react";

import { AlertTriangle, BarChart3, FileSearch, ScanSearch } from "lucide-react";

import { SegmentCard } from "@/components/SegmentCard";
import { PredictResponse } from "@/lib/api";
import { LABEL_STYLES } from "@/lib/constants";

interface ResultsPanelProps {
  data: PredictResponse | null;
  loading: boolean;
  error: string | null;
}

export function ResultsPanel({ data, loading, error }: ResultsPanelProps) {
  const dominantLabel = useMemo(() => data?.results[0]?.label, [data]);

  if (loading) {
    return (
      <section className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
        <div className="mb-6 flex items-center gap-3">
          <div className="h-10 w-10 animate-pulse rounded-2xl bg-white/10" />
          <div className="space-y-2">
            <div className="h-4 w-32 animate-pulse rounded bg-white/10" />
            <div className="h-3 w-56 animate-pulse rounded bg-white/5" />
          </div>
        </div>
        <div className="space-y-4">
          {[0, 1, 2].map((item) => (
            <div key={item} className="rounded-3xl border border-white/8 bg-white/[0.02] p-5">
              <div className="mb-4 h-4 w-24 animate-pulse rounded bg-white/10" />
              <div className="mb-2 h-3 w-full animate-pulse rounded bg-white/5" />
              <div className="mb-6 h-3 w-5/6 animate-pulse rounded bg-white/5" />
              <div className="space-y-2">
                <div className="h-2.5 w-full animate-pulse rounded bg-white/5" />
                <div className="h-2.5 w-full animate-pulse rounded bg-white/5" />
                <div className="h-2.5 w-full animate-pulse rounded bg-white/5" />
              </div>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className="rounded-[2rem] border border-rose-400/20 bg-rose-500/5 p-6 shadow-glow">
        <div className="flex items-start gap-4">
          <div className="rounded-2xl border border-rose-400/20 bg-rose-500/10 p-3">
            <AlertTriangle className="h-5 w-5 text-rose-200" />
          </div>
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-white">Analysis failed</h2>
            <p className="text-sm leading-6 text-rose-100/90">{error}</p>
          </div>
        </div>
      </section>
    );
  }

  if (!data) {
    return (
      <section className="rounded-[2rem] border border-dashed border-white/12 bg-white/[0.02] p-8 text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-3xl border border-white/10 bg-white/[0.03]">
          <ScanSearch className="h-6 w-6 text-slate-300" />
        </div>
        <h2 className="text-xl font-semibold text-white">Ready to analyze</h2>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-7 text-slate-400">
          Paste article text or drop in a URL above, choose how granular you want the analysis to be, and Bias Checker will return probability-weighted LEFT, CENTER, and RIGHT predictions.
        </p>
      </section>
    );
  }

  const styles = dominantLabel ? LABEL_STYLES[dominantLabel] : LABEL_STYLES.CENTER;

  return (
    <section className="space-y-6">
      <div className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 shadow-glow backdrop-blur">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs uppercase tracking-[0.22em] text-slate-400">
              <FileSearch className="h-3.5 w-3.5" />
              Analysis Summary
            </div>
            <h2 className="text-2xl font-semibold text-white">
              {data.mode === "article" ? "Whole article prediction" : `${data.results.length} segment predictions`}
            </h2>
            <p className="max-w-3xl text-sm leading-7 text-slate-400">
              Source type: <span className="text-slate-200">{data.source_type}</span>. Mode:{" "}
              <span className="text-slate-200">{data.mode}</span>. The interface below keeps the segment-level predictions color coded so the overall leaning is easy to scan.
            </p>
          </div>
          <div className={`inline-flex items-center gap-3 rounded-2xl border bg-white/[0.03] px-4 py-3 ${styles.border}`}>
            <BarChart3 className={`h-5 w-5 ${styles.text}`} />
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Top signal</p>
              <p className={`text-sm font-semibold ${styles.text}`}>{dominantLabel ?? "CENTER"}</p>
            </div>
          </div>
        </div>
      </div>

      {data.mode !== "article" ? (
        <div className="rounded-[2rem] border border-white/10 bg-white/[0.02] p-5">
          <p className="mb-4 text-xs uppercase tracking-[0.2em] text-slate-500">Highlighted segment view</p>
          <div className="flex flex-wrap gap-2">
            {data.results.map((result) => (
              <span
                key={`${result.segment_index}-${result.label}`}
                className={`rounded-2xl px-3 py-2 text-sm leading-6 ${LABEL_STYLES[result.label].badge}`}
                title={result.label}
              >
                {result.text}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4">
        {data.results.map((result) => (
          <SegmentCard key={result.segment_index} result={result} />
        ))}
      </div>
    </section>
  );
}
