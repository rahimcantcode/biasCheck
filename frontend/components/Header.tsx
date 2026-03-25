import { Info, Orbit } from "lucide-react";

export function Header() {
  return (
    <header className="relative z-20 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-glow backdrop-blur">
          <Orbit className="h-5 w-5 text-blue-200" />
        </div>
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">
            Bias Checker
          </p>
          <p className="text-xs text-slate-500">RoBERTa political bias analysis</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 transition hover:border-white/20 hover:bg-white/10">
          <Info className="h-4 w-4" />
          How it works
        </button>
        <button className="hidden rounded-full border border-blue-400/30 bg-blue-500/10 px-4 py-2 text-sm text-blue-100 transition hover:bg-blue-500/15 sm:inline-flex">
          About Model
        </button>
      </div>
    </header>
  );
}
