export function Footer() {
  return (
    <footer className="border-t border-white/8 bg-black/20">
      <section id="how-it-works" className="mx-auto max-w-7xl space-y-3 px-6 pt-8 text-sm leading-6 text-slate-400 lg:px-8">
        <h2 className="font-medium text-slate-200">How it works</h2>
        <p>Paste English article text or a public article URL. Article mode processes the document; sentence and paragraph modes also inspect individual passages. Quotations, sarcasm, and mixed positions can mislead the model.</p>
        <details id="model-details">
          <summary className="cursor-pointer text-slate-300">About the models and limitations</summary>
          <p className="mt-2">This research build supports the original RoBERTa classifier and an optional PoliticalDEBATE entailment model. The experimental engine checks political relevance and can return a tentative leaning or ask for more context. Neither engine has passed the independent release evaluation. Scores are model outputs, not measured certainty, factuality, or word-level bias.</p>
        </details>
      </section>
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-8 text-sm text-slate-400 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <p>Bias Checker is an experimental tool for political leaning in English U.S. news. It does not check facts.</p>
        <p>Model labels: LEFT, RIGHT, CENTER.</p>
      </div>
    </footer>
  );
}
