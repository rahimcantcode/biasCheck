import { cn } from "@/lib/cn";
import { MODES } from "@/lib/constants";
import { Mode } from "@/lib/api";

interface ModeTabsProps {
  value: Mode;
  onChange: (mode: Mode) => void;
}

export function ModeTabs({ value, onChange }: ModeTabsProps) {
  return (
    <div className="inline-flex w-full rounded-2xl border border-white/10 bg-black/20 p-1.5 sm:w-auto">
      {MODES.map((mode) => {
        const active = value === mode.value;
        return (
          <button
            key={mode.value}
            type="button"
            onClick={() => onChange(mode.value)}
            className={cn(
              "flex-1 rounded-xl px-4 py-2.5 text-sm font-medium transition sm:flex-none",
              active
                ? "bg-white text-slate-950 shadow-sm"
                : "text-slate-300 hover:bg-white/5 hover:text-white"
            )}
          >
            {mode.label}
          </button>
        );
      })}
    </div>
  );
}
