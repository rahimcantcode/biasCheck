"use client";

import { ArrowRight, Paperclip } from "lucide-react";

import { AiHeroBackground } from "@/components/AiHeroBackground";
import { BiasInputCard } from "@/components/BiasInputCard";
import { Mode, PredictResponse } from "@/lib/api";

interface HeroSectionProps {
  input: string;
  mode: Mode;
  loading: boolean;
  results: PredictResponse | null;
  onInputChange: (value: string) => void;
  onModeChange: (mode: Mode) => void;
  onSubmit: () => Promise<void>;
  onClear: () => void;
}

export function HeroSection({
  input,
  mode,
  loading,
  results,
  onInputChange,
  onModeChange,
  onSubmit,
  onClear,
}: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden border-b border-white/8 bg-hero-radial">
      <AiHeroBackground />

      <div className="pointer-events-none absolute right-0 top-0 z-10 h-72 w-72 rounded-full bg-blue-500/12 blur-3xl" />
      <div className="pointer-events-none absolute right-24 top-16 z-10 h-40 w-40 rounded-full bg-indigo-400/10 blur-3xl" />
      <div className="pointer-events-none absolute right-20 top-28 z-10 h-1.5 w-72 rotate-[28deg] rounded-full bg-gradient-to-r from-blue-400/0 via-blue-300/70 to-cyan-200/10 blur-sm" />
      <div className="pointer-events-none absolute right-10 top-10 z-10 h-1.5 w-56 rotate-[35deg] rounded-full bg-gradient-to-r from-indigo-300/0 via-indigo-300/60 to-transparent blur-sm" />

      <div className="relative z-20 mx-auto flex min-h-[calc(100vh-88px)] w-full max-w-7xl items-center px-6 pb-20 pt-10 lg:px-8">
        <div className="w-full space-y-10">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-300">
              <Paperclip className="h-3.5 w-3.5 text-blue-200" />
              Article, sentence, and paragraph political bias analysis
            </div>
            <h1 className="mx-auto max-w-4xl text-balance text-4xl font-semibold tracking-tight text-white sm:text-6xl">
              See how your article leans
            </h1>
            <p className="mx-auto mt-5 max-w-3xl text-balance text-base leading-8 text-slate-300 sm:text-lg">
              Paste article text or a URL, choose a mode, and get color-coded political bias predictions powered by a fine-tuned RoBERTa classifier.
            </p>
          </div>

          <div className="mx-auto max-w-6xl">
            <BiasInputCard
              mode={mode}
              input={input}
              loading={loading}
              onModeChange={onModeChange}
              onInputChange={onInputChange}
              onSubmit={onSubmit}
              onClear={onClear}
            />
          </div>

          <div className="mx-auto flex max-w-5xl flex-col items-center justify-center gap-4 rounded-[1.75rem] border border-white/8 bg-white/[0.02] px-5 py-4 text-center text-sm text-slate-400 sm:flex-row sm:text-left">
            <div className="flex items-center gap-2 text-slate-200">
              <ArrowRight className="h-4 w-4 text-blue-200" />
              {results
                ? `Latest run returned ${results.results.length} ${results.mode === "article" ? "prediction" : "segments"} in ${results.mode} mode.`
                : "Local MVP flow: input, classify, and inspect segment-level probabilities in one place."}
            </div>
            <div className="hidden h-4 w-px bg-white/10 sm:block" />
            <p>Bias Checker loads your exported local model from `bias_model/` through FastAPI.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
