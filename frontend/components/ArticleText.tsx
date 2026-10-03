import type { EvidenceSpan } from "../lib/api";
import type { ArticlePart } from "../lib/article";

interface ArticleTextProps {
  parts: ArticlePart[];
  showHighlights: boolean;
  selected: EvidenceSpan | null;
  onSelect: (span: EvidenceSpan | null) => void;
}

const NAMES = { LEFT: "Left", RIGHT: "Right" };
const HIGHLIGHTS = {
  LEFT: "bg-blue-500/20 text-blue-200 decoration-blue-300 decoration-solid",
  RIGHT: "bg-red-500/20 text-red-200 decoration-red-300 decoration-double",
};

// Render plain React text children, never HTML from the article or rationale.
// This stateless view can also be tested independently of network/model output.
export function ArticleText({ parts, showHighlights, selected, onSelect }: ArticleTextProps) {
  return (
    <article aria-label="Analyzed article" className="mx-auto max-w-3xl whitespace-pre-wrap break-words font-serif text-[18px] leading-[1.95] text-slate-200 sm:text-[20px]">
      {parts.map((part, index) => {
        const span = part.evidence;
        if (!span || !showHighlights) return <span key={index}>{part.text}</span>;
        const active = selected === span;
        const description = `Experimental ${NAMES[span.label]}-leaning expression attributed to the author`;
        return (
          <mark
            key={`${span.start}:${span.end}`}
            role="button"
            tabIndex={0}
            aria-label={`${description}: ${part.text}`}
            aria-pressed={active}
            title={`${description}. Select to inspect.`}
            onClick={() => onSelect(active ? null : span)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect(active ? null : span);
              }
              if (event.key === "Escape") onSelect(null);
            }}
            className={`cursor-pointer rounded-xs underline decoration-1 underline-offset-[5px] transition-colors hover:brightness-125 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-300 ${HIGHLIGHTS[span.label]} ${active ? "outline outline-1 outline-offset-2 outline-slate-400" : ""}`}
          >
            {part.text}
          </mark>
        );
      })}
    </article>
  );
}
