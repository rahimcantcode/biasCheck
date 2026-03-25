"use client";

import { FormEvent, useState } from "react";
import { Globe, LoaderCircle, RotateCcw, Sparkles, TextSearch } from "lucide-react";

import { ModeTabs } from "@/components/ModeTabs";
import { Mode } from "@/lib/api";
import { DEMO_ARTICLE, QUICK_ACTIONS } from "@/lib/constants";

interface BiasInputCardProps {
  mode: Mode;
  input: string;
  loading: boolean;
  onModeChange: (mode: Mode) => void;
  onInputChange: (value: string) => void;
  onSubmit: () => Promise<void>;
  onClear: () => void;
}

export function BiasInputCard({
  mode,
  input,
  loading,
  onModeChange,
  onInputChange,
  onSubmit,
  onClear,
}: BiasInputCardProps) {
  const [focused, setFocused] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onSubmit();
  }

  function handleQuickAction(action: string) {
    if (action === "Paste a news article") {
      onInputChange(DEMO_ARTICLE);
      return;
    }

    if (action === "Try article mode") {
      onModeChange("article");
      return;
    }

    if (action === "Analyze by sentence") {
      onModeChange("sentence");
      return;
    }

    if (action === "Analyze by paragraph") {
      onModeChange("paragraph");
    }
  }

  return (
    <div
      className={`relative overflow-hidden rounded-[2rem] border bg-black/30 p-5 shadow-glow backdrop-blur transition sm:p-6 ${
        focused ? "border-blue-400/30" : "border-white/10"
      }`}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      <form className="relative space-y-5" onSubmit={handleSubmit}>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/15 bg-blue-500/8 px-3 py-1 text-xs uppercase tracking-[0.22em] text-blue-100/90">
              <Sparkles className="h-3.5 w-3.5" />
              Live analysis workspace
            </div>
            <p className="text-sm text-slate-400">
              Paste a full article or a URL. The backend will extract article text automatically for valid links.
            </p>
          </div>

          <ModeTabs value={mode} onChange={onModeChange} />
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
          <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-3">
            <label className="mb-3 flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500">
              <TextSearch className="h-4 w-4" />
              Article text or URL
            </label>
            <textarea
              value={input}
              onChange={(event) => onInputChange(event.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="Paste article text here, or enter a full URL like https://example.com/story"
              className="min-h-[220px] w-full resize-none rounded-[1.2rem] border border-white/8 bg-slate-950/70 px-4 py-4 text-sm leading-7 text-slate-100 outline-none placeholder:text-slate-500"
            />
          </div>

          <div className="flex flex-col justify-between rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
            <div className="space-y-4">
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <div className="mb-2 flex items-center gap-2 text-sm font-medium text-white">
                  <Globe className="h-4 w-4 text-slate-300" />
                  Input guidance
                </div>
                <p className="text-sm leading-6 text-slate-400">
                  Use article mode for one overall label, sentence mode to inspect line-by-line framing, or paragraph mode for more stable section-level reads.
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current mode</p>
                <p className="mt-2 text-lg font-semibold text-white">
                  {mode.charAt(0).toUpperCase() + mode.slice(1)} analysis
                </p>
              </div>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                {loading ? "Analyzing..." : "Analyze"}
              </button>
              <button
                type="button"
                onClick={onClear}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm font-medium text-slate-200 transition hover:bg-white/[0.06]"
              >
                <RotateCcw className="h-4 w-4" />
                Clear
              </button>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => handleQuickAction(action)}
              className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06] hover:text-white"
            >
              {action}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
