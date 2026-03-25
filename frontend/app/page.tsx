"use client";

import { useEffect, useRef, useState } from "react";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { HeroSection } from "@/components/HeroSection";
import { ResultsPanel } from "@/components/ResultsPanel";
import { analyzeInput, Mode, PredictResponse } from "@/lib/api";

export default function HomePage() {
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<Mode>("article");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<PredictResponse | null>(null);
  const resultsRef = useRef<HTMLElement | null>(null);

  async function handleAnalyze() {
    if (!input.trim()) {
      setError("Please paste article text or enter a valid URL.");
      setResults(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await analyzeInput(input, mode);
      setResults(response);
    } catch (analysisError) {
      setResults(null);
      setError(
        analysisError instanceof Error
          ? analysisError.message
          : "Analysis failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleClear() {
    setInput("");
    setResults(null);
    setError(null);
  }

  useEffect(() => {
    if ((results || error) && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [results, error]);

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(61,82,160,0.16),transparent_28%),linear-gradient(180deg,#070b14_0%,#06070d_100%)]">
      <Header />
      <HeroSection
        input={input}
        mode={mode}
        loading={loading}
        results={results}
        onInputChange={setInput}
        onModeChange={setMode}
        onSubmit={handleAnalyze}
        onClear={handleClear}
      />
      <section ref={resultsRef} className="mx-auto max-w-7xl px-6 py-20 lg:px-8">
        <ResultsPanel data={results} loading={loading} error={error} />
      </section>
      <Footer />
    </main>
  );
}
