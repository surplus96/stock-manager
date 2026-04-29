import type { Metadata } from "next";
import Script from "next/script";
import { Source_Serif_4 } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

// FR-PSP-T01 — Display serif for h1/h2/AnalysisReport titles. Bound to a
// CSS variable so the rule lives in globals.css (`.font-display`) and
// doesn't pollute every component import.
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Stock Manager",
  description: "AI-Powered Investment Dashboard with 40-Factor Analysis",
};

/**
 * Inline theme-init script — runs before React hydrates so pages render
 * in the correct palette from the very first paint. Without this the
 * user would see a one-frame flash of light mode before ThemeToggle's
 * useEffect swaps the attribute.
 */
const themeInit = `
try {
  var t = localStorage.getItem("chat.theme");
  if (t === "dark") document.documentElement.dataset.theme = "dark";
} catch (_) {}
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // suppressHydrationWarning — the inline theme-init script sets
    // `data-theme="dark"` on <html> before React hydrates, which intentionally
    // differs from the server-rendered output (server has no access to the
    // user's localStorage). React's warning about this mismatch is expected
    // and safe to suppress for this single attribute.
    <html lang="en" className={`h-full antialiased ${sourceSerif.variable}`} suppressHydrationWarning>
      <head>
        <Script id="theme-init" strategy="beforeInteractive">
          {themeInit}
        </Script>
      </head>
      <body className="min-h-full flex bg-[var(--background)] text-[var(--foreground)]">
        <Sidebar />
        <main className="flex-1 md:ml-60 min-h-screen">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 pt-16 md:pt-6">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
