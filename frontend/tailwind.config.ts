import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#070b14",
        foreground: "#f5f7fb",
        panel: "#0d1321",
        panelAlt: "#101827",
        border: "rgba(148, 163, 184, 0.16)",
        left: "#5aa2ff",
        center: "#9aa4b2",
        right: "#f06b6b",
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(148, 163, 184, 0.12), 0 24px 60px rgba(15, 23, 42, 0.45)",
      },
      backgroundImage: {
        "hero-radial":
          "radial-gradient(circle at top right, rgba(91, 120, 255, 0.20), transparent 24%), radial-gradient(circle at top left, rgba(74, 222, 128, 0.08), transparent 28%)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "\"Segoe UI\"",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
