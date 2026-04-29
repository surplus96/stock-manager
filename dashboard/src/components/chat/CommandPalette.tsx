"use client";

/**
 * CommandPalette — FR-U08. Minimal ⌘K palette (no external dependency).
 *
 * - Opens on Cmd/Ctrl+K globally.
 * - Filters the 4 quick-start prompts by substring match.
 * - Enter submits the highlighted entry, Esc closes.
 */

import { useEffect, useRef, useState } from "react";
import { Sparkles, ArrowRight } from "lucide-react";

export interface PaletteItem {
  label: string;
  prompt: string;
}

interface CommandPaletteProps {
  items: PaletteItem[];
  open: boolean;
  onClose: () => void;
  onPick: (prompt: string) => void;
}

export default function CommandPalette({ items, open, onClose, onPick }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setQuery("");
      setActive(0);
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [open]);

  if (!open) return null;

  const filtered = items.filter(
    (it) =>
      !query.trim() ||
      it.label.toLowerCase().includes(query.toLowerCase()) ||
      it.prompt.toLowerCase().includes(query.toLowerCase()),
  );

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => Math.min(filtered.length - 1, a + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => Math.max(0, a - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const pick = filtered[active];
      if (pick) {
        onPick(pick.prompt);
        onClose();
      }
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
      className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4"
    >
      <button
        aria-label="Close palette"
        type="button"
        className="absolute inset-0 bg-black/40"
        onClick={onClose}
      />
      <div
        className="relative w-full max-w-xl rounded-xl border bg-white dark:bg-slate-900 shadow-xl overflow-hidden"
        style={{ borderColor: "var(--border)" }}
      >
        <div className="flex items-center gap-2 px-3 py-2 border-b" style={{ borderColor: "var(--border)" }}>
          <Sparkles className="w-4 h-4 text-blue-500" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActive(0);
            }}
            onKeyDown={onKeyDown}
            placeholder="빠른 질문 검색… (↑↓ 선택, Enter 전송, Esc 닫기)"
            aria-label="Command palette query"
            className="flex-1 bg-transparent outline-none text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400"
          />
          <kbd className="text-[10px] font-mono text-slate-400 border rounded px-1 py-0.5" style={{ borderColor: "var(--border)" }}>
            Esc
          </kbd>
        </div>
        <ul role="listbox" className="max-h-80 overflow-y-auto">
          {filtered.length === 0 && (
            <li className="px-3 py-6 text-sm text-slate-400 text-center">일치하는 항목이 없습니다.</li>
          )}
          {filtered.map((it, i) => (
            <li key={it.label} role="option" aria-selected={i === active}>
              <button
                type="button"
                onClick={() => {
                  onPick(it.prompt);
                  onClose();
                }}
                onMouseEnter={() => setActive(i)}
                className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors ${
                  i === active
                    ? "bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-200"
                    : "text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <ArrowRight className="w-3.5 h-3.5 shrink-0 text-slate-400" />
                <div className="flex-1">
                  <div className="font-medium">{it.label}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400 truncate">{it.prompt}</div>
                </div>
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
