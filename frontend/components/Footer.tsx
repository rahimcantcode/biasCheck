export function Footer() {
  return (
    <footer className="border-t border-white/8 bg-black/20">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-8 text-sm text-slate-400 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <p>Bias Checker is a local MVP for political bias analysis across full articles, sentences, and paragraphs.</p>
        <p>Model labels: LEFT, RIGHT, CENTER.</p>
      </div>
    </footer>
  );
}
