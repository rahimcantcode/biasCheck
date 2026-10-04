import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Bias Checker",
  description: "See left, center, and right political leaning sentence by sentence.",
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
