export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const MODES = [
  { value: "article", label: "Article" },
  { value: "sentence", label: "Sentence" },
  { value: "paragraph", label: "Paragraph" },
] as const;

export const QUICK_ACTIONS = [
  "Paste a news article",
  "Try article mode",
  "Analyze by sentence",
  "Analyze by paragraph",
] as const;

export const DEMO_ARTICLE = `The administration announced a wide-reaching economic plan today, arguing that the proposal would protect working families while reducing long-term deficits. Supporters described the measure as overdue and pragmatic, while critics said the messaging downplayed the burden on small businesses and overstated the likely impact on inflation. Analysts noted that the speech used contrasting language depending on the audience, framing the package as both fiscally restrained and historically ambitious.`;

export const LABEL_STYLES = {
  LEFT: {
    badge: "bg-blue-500/12 text-blue-200 ring-1 ring-inset ring-blue-400/30",
    border: "border-blue-400/25",
    glow: "from-blue-500/18 to-transparent",
    text: "text-blue-200",
    bar: "bg-blue-400",
  },
  CENTER: {
    badge: "bg-slate-400/10 text-slate-200 ring-1 ring-inset ring-slate-400/25",
    border: "border-slate-400/20",
    glow: "from-slate-300/14 to-transparent",
    text: "text-slate-200",
    bar: "bg-slate-300",
  },
  RIGHT: {
    badge: "bg-rose-500/12 text-rose-200 ring-1 ring-inset ring-rose-400/30",
    border: "border-rose-400/25",
    glow: "from-rose-500/18 to-transparent",
    text: "text-rose-200",
    bar: "bg-rose-400",
  },
} as const;
