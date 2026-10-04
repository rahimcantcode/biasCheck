export function Footer() {
  return (
    <footer className="border-t border-white/8 bg-black/20">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-6 py-8 text-sm text-slate-400 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <p>Sentence-level model predictions, not a fact check.</p>
        <p>Model by Volf &amp; Šimko · <a href="https://creativecommons.org/licenses/by-nc/4.0/" className="underline">CC BY-NC 4.0</a></p>
      </div>
    </footer>
  );
}
