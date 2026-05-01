"use client";

/**
 * ModelSelector — FR-U03.
 *
 * Lightweight dropdown that lets the user pick which Gemini model the chat
 * backend should use for the next turn. The choice is persisted to
 * localStorage and mirrored to a React context so the chat page can
 * forward it to the backend as a ``?model=`` query param.
 *
 * The model list is hard-coded for now (Plan P2/P3 upgrades it to a
 * `/api/chat/models` endpoint that enumerates server-available models).
 */

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { Cpu, ChevronDown } from "lucide-react";

// FR-PSP-M02 — ``tone`` decorates the segmented buttons with a small
// dot in family-specific colours (Preview = violet, Flash = teal,
// Lite = slate). Helps users recognise the family at a glance without
// reading the label.
//
// Lineup verified against the live /v1beta/models/{name} endpoint on
// 2026-05-01 — ``gemini-3.1-flash-lite-preview`` now returns 200 on
// this API tier and was promoted to the default. 2.5-flash drops one
// slot and stays as the highest-quality non-preview alternative.
const MODELS = [
  { value: "gemini-3.1-flash-lite-preview", short: "3.1", label: "Flash Lite 3.1 (권장, preview)", tone: "preview" },
  { value: "gemini-2.5-flash", short: "2.5", label: "Flash 2.5 (안정)", tone: "flash" },
  { value: "gemini-2.0-flash", short: "2.0", label: "Flash 2.0 (저비용)", tone: "flash" },
] as const;

const TONE_DOT: Record<"preview" | "flash" | "lite", string> = {
  preview: "var(--accent)",        // violet — preview family
  flash:   "var(--chart-pos)",     // teal — main Flash family
  lite:    "var(--chart-neutral)", // slate — Lite variants
};

// FR-PSP-M01 — top 3 stay in the segmented control, the rest fall into a
// "More" overflow popover so the visible UI stays compact.
const MORE_MODELS = [
  { value: "gemini-2.5-flash-lite", label: "Flash 2.5 Lite" },
  { value: "gemini-2.0-flash-lite", label: "Flash 2.0 Lite" },
];

const ALL_MODEL_VALUES = new Set<string>([
  ...MODELS.map((m) => m.value),
  ...MORE_MODELS.map((m) => m.value),
]);

const STORAGE_KEY = "chat.model";
const DEFAULT_MODEL = MODELS[0].value;

interface ChatModelContextValue {
  model: string;
  setModel: (m: string) => void;
}

const ChatModelContext = createContext<ChatModelContextValue>({
  model: DEFAULT_MODEL,
  setModel: () => {},
});

export function ChatModelProvider({ children }: { children: ReactNode }) {
  // Annotate as plain string so the segmented control can swap to any
  // value (top-3 + overflow) without TS narrowing fighting the literal
  // ``as const`` MODELS array.
  const [model, setModelState] = useState<string>(DEFAULT_MODEL);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null;
    if (saved && ALL_MODEL_VALUES.has(saved)) {
      setModelState(saved);
    }
  }, []);

  function setModel(m: string) {
    setModelState(m);
    try {
      localStorage.setItem(STORAGE_KEY, m);
    } catch {
      /* ignore */
    }
  }

  return (
    <ChatModelContext.Provider value={{ model, setModel }}>{children}</ChatModelContext.Provider>
  );
}

export function useChatModel(): ChatModelContextValue {
  return useContext(ChatModelContext);
}

/**
 * ModelSelector — FR-PSP-M01..03 segmented control variant.
 *
 * Top 3 models are exposed as a segmented (radiogroup) row; the remaining
 * fallbacks live in an overflow popover. ``1`` / ``2`` / ``3`` keyboard
 * shortcuts swap the segmented value when no input/textarea owns focus.
 */
export default function ModelSelector() {
  const { model, setModel } = useChatModel();
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement | null>(null);

  // FR-PSP-M03 — global digit hotkeys, ignored while typing.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement | null;
      const tag = (t?.tagName || "").toUpperCase();
      if (tag === "INPUT" || tag === "TEXTAREA" || t?.isContentEditable) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const idx = ["1", "2", "3"].indexOf(e.key);
      if (idx >= 0 && MODELS[idx]) {
        setModel(MODELS[idx].value);
      } else if (e.key === "Escape" && moreOpen) {
        setMoreOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setModel, moreOpen]);

  // Click-outside to close More popover.
  useEffect(() => {
    if (!moreOpen) return;
    function onDown(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setMoreOpen(false);
      }
    }
    window.addEventListener("mousedown", onDown);
    return () => window.removeEventListener("mousedown", onDown);
  }, [moreOpen]);

  const overflowLabel =
    MORE_MODELS.find((m) => m.value === model)?.label.split(" ")[0] ?? "More";

  return (
    <div className="inline-flex items-center gap-1.5 text-xs">
      <Cpu className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
      <span className="sr-only">Model selector</span>
      <div
        role="radiogroup"
        aria-label="Chat model"
        className="inline-flex border rounded-md overflow-hidden bg-white dark:bg-slate-900"
        style={{ borderColor: "var(--border)" }}
      >
        {MODELS.map((m, idx) => {
          const selected = model === m.value;
          return (
            <button
              key={m.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => setModel(m.value)}
              title={`${m.label} (단축키: ${idx + 1})`}
              className={`px-2 py-1 transition-colors border-r last:border-r-0 inline-flex items-center gap-1 ${
                selected
                  ? "bg-[var(--accent)] text-white"
                  : "text-slate-600 dark:text-slate-300 hover:bg-[var(--accent-soft)]"
              }`}
              style={{ borderColor: "var(--border)" }}
            >
              <span
                aria-hidden="true"
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: TONE_DOT[m.tone] }}
              />
              {m.short}
            </button>
          );
        })}
        {/* FR-PSP-M01 — overflow popover for less-common fallbacks */}
        <div ref={moreRef} className="relative">
          <button
            type="button"
            aria-haspopup="menu"
            aria-expanded={moreOpen}
            onClick={() => setMoreOpen((v) => !v)}
            className={`px-2 py-1 inline-flex items-center gap-0.5 transition-colors ${
              MORE_MODELS.some((m) => m.value === model)
                ? "bg-[var(--accent)] text-white"
                : "text-slate-600 dark:text-slate-300 hover:bg-[var(--accent-soft)]"
            }`}
          >
            <span>{overflowLabel}</span>
            <ChevronDown className="w-3 h-3" />
          </button>
          {moreOpen && (
            <div
              role="menu"
              className="absolute right-0 top-full mt-1 z-20 min-w-[180px] rounded-md border bg-white dark:bg-slate-900 shadow-lg"
              style={{ borderColor: "var(--border)" }}
            >
              {MORE_MODELS.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  role="menuitemradio"
                  aria-checked={model === m.value}
                  onClick={() => {
                    setModel(m.value);
                    setMoreOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 text-xs transition-colors ${
                    model === m.value
                      ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "text-slate-700 dark:text-slate-200 hover:bg-[var(--accent-soft)]"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
