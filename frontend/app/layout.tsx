import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Bias Checker",
  description: "Analyze political bias in articles with a fine-tuned RoBERTa model.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-background font-sans text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
