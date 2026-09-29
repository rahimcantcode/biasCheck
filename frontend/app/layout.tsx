import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Bias Checker",
  description: "Explore experimental political-leaning assessments with context and uncertainty.",
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
