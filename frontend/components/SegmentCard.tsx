import { SegmentResult } from "@/lib/api";
import { LABEL_STYLES } from "@/lib/constants";
import { ProbabilityBars } from "@/components/ProbabilityBars";

interface SegmentCardProps {
  result: SegmentResult;
}

export function SegmentCard({ result }: SegmentCardProps) {
  const styles = LABEL_STYLES[result.label];

  return (
    <article
      className={`relative overflow-hidden rounded-3xl border bg-white/[0.03] p-5 shadow-glow backdrop-blur ${styles.border}`}
    >
      <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${styles.glow} opacity-80`} />

      <div className="relative space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${styles.badge}`}>
              {result.label}
            </span>
            <span className="text-xs uppercase tracking-[0.16em] text-slate-500">
              Segment {result.segment_index + 1}
            </span>
          </div>
        </div>

        <p className="relative text-sm leading-7 text-slate-100 sm:text-[15px]">{result.text}</p>

        <ProbabilityBars probabilities={result.probabilities} />
      </div>
    </article>
  );
}
