/**
 * Markdown — thin react-markdown wrapper with GFM enabled (FR-F09).
 *
 * Applies heading / list / code styling that matches the existing design tokens.
 * Use this instead of hand-rolled regex parsers anywhere markdown content is
 * rendered from LLM outputs.
 *
 * Note: react-markdown and remark-gfm are declared in package.json — install
 * with `npm install` before building. The tsconfig excludes are updated in
 * tsconfig.json to prevent type errors when the module is not yet installed.
 */
"use client";

import type { ReactNode } from "react";

// Dynamic import guard — avoids hard TS errors when module is not installed yet.
// Once `npm install` is run, react-markdown and remark-gfm are available.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _ReactMarkdown: any = null;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let _remarkGfm: any = null;
try {
  // These are loaded at runtime; if unavailable the plain fallback renders.
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  _ReactMarkdown = (require("react-markdown") as { default: unknown }).default;
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  _remarkGfm = (require("remark-gfm") as { default: unknown }).default;
} catch {
  // deps not installed yet — plain fallback will be used
}

/** Fallback: simple paragraph split used before react-markdown is installed. */
function PlainMarkdown({ children }: { children: string }): ReactNode {
  return (
    <div className="space-y-2 text-sm text-slate-900 dark:text-slate-50 leading-relaxed">
      {children.split("\n").map((line, i) => {
        const t = line.trim();
        if (!t) return <div key={i} className="h-1" />;
        if (t.startsWith("## "))
          return <h3 key={i} className="text-base font-semibold text-slate-950 dark:text-white mt-4 mb-1">{t.slice(3)}</h3>;
        if (t.startsWith("### "))
          return <h4 key={i} className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-3 mb-1">{t.slice(4)}</h4>;
        if (t.startsWith("- ") || t.startsWith("* "))
          return <p key={i} className="pl-4 text-slate-900 dark:text-slate-50 before:content-['•'] before:mr-2 before:text-slate-500 dark:before:text-slate-400">{t.slice(2)}</p>;
        return <p key={i} className="text-slate-900 dark:text-slate-50">{t}</p>;
      })}
    </div>
  );
}

/**
 * Recharts-style component map — only used when react-markdown is installed.
 *
 * Color rationale: the previous palette (text-slate-600 on paragraphs) was
 * visibly washed out, especially inside dark bubbles. We now run paragraph
 * text at slate-900 in light mode and slate-50 in dark mode — near-pure
 * white on dark for strong contrast — and headings use the absolute
 * slate-950 / slate-50 endpoints so the hierarchy still reads.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const mdComponents: Record<string, (props: any) => ReactNode> = {
  h1: ({ children }: { children: ReactNode }) => (
    <h1 className="font-display text-2xl font-bold text-slate-950 dark:text-slate-50 mt-5 mb-2">{children}</h1>
  ),
  h2: ({ children }: { children: ReactNode }) => (
    <h2 className="font-display text-lg font-semibold text-slate-950 dark:text-slate-50 mt-4 mb-1">{children}</h2>
  ),
  h3: ({ children }: { children: ReactNode }) => (
    <h3 className="font-display text-base font-semibold text-slate-900 dark:text-slate-100 mt-3 mb-1">{children}</h3>
  ),
  p: ({ children }: { children: ReactNode }) => (
    /* FR-PSP-T03 — line-height 1.65 for prose readability */
    <p className="text-sm text-slate-900 dark:text-slate-50" style={{ lineHeight: 1.65 }}>{children}</p>
  ),
  ul: ({ children }: { children: ReactNode }) => (
    <ul className="list-none space-y-1 my-1">{children}</ul>
  ),
  ol: ({ children }: { children: ReactNode }) => (
    <ol className="list-decimal list-inside space-y-1 my-1 text-sm text-slate-900 dark:text-slate-50">{children}</ol>
  ),
  li: ({ children }: { children: ReactNode }) => (
    <li className="pl-4 text-sm text-slate-900 dark:text-slate-50 before:content-['•'] before:mr-2 before:text-slate-500 dark:before:text-slate-400">
      {children}
    </li>
  ),
  strong: ({ children }: { children: ReactNode }) => (
    <strong className="font-semibold text-slate-950 dark:text-white">{children}</strong>
  ),
  em: ({ children }: { children: ReactNode }) => (
    <em className="italic text-slate-900 dark:text-slate-100">{children}</em>
  ),
  code: ({ children, className }: { children: ReactNode; className?: string }) => {
    const isBlock = className?.startsWith("language-");
    if (isBlock) {
      return (
        <pre className="my-2 overflow-x-auto rounded-lg bg-slate-100 dark:bg-slate-800 p-3 text-xs font-mono text-slate-900 dark:text-slate-100">
          <code>{children}</code>
        </pre>
      );
    }
    return (
      <code className="rounded bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-900 dark:text-slate-100">
        {children}
      </code>
    );
  },
  blockquote: ({ children }: { children: ReactNode }) => (
    <blockquote className="my-2 border-l-4 border-blue-300 dark:border-blue-500 pl-4 text-sm text-slate-700 dark:text-slate-200 italic">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-3 border-slate-200 dark:border-slate-700" />,
  a: ({ href, children }: { href?: string; children: ReactNode }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-600 dark:text-blue-300 underline hover:text-blue-800 dark:hover:text-blue-200"
    >
      {children}
    </a>
  ),
};

interface MarkdownProps {
  children: string;
  className?: string;
}

export function Markdown({ children, className }: MarkdownProps) {
  const wrapperClass = className ?? "space-y-2 text-sm text-slate-700 leading-relaxed";

  if (!_ReactMarkdown) {
    return <PlainMarkdown>{children}</PlainMarkdown>;
  }

  const RM = _ReactMarkdown;
  const plugins = _remarkGfm ? [_remarkGfm] : [];

  return (
    <div className={wrapperClass}>
      <RM remarkPlugins={plugins} components={mdComponents}>
        {children}
      </RM>
    </div>
  );
}
