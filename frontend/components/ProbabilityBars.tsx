import { PredictionProbabilities } from "@/lib/api";
import { LABEL_STYLES } from "@/lib/constants";

interface ProbabilityBarsProps {
  probabilities: PredictionProbabilities;
}

const DISPLAY_ORDER = ["LEFT", "CENTER", "RIGHT"] as const;

export function ProbabilityBars({ probabilities }: ProbabilityBarsProps) {
  return (
    <div className="space-y-3">
      {DISPLAY_ORDER.map((label) => {
        const percent = Math.round(probabilities[label] * 100);

        return (
          <div key={label} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.16em] text-slate-400">
              <span>{label}</span>
              <span className={LABEL_STYLES[label].text}>{percent}%</span>
            </div>
            <div className="h-2.5 overflow-hidden rounded-full bg-white/8">
              <div
                className={`h-full rounded-full ${LABEL_STYLES[label].bar}`}
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
