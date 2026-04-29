"use client";

/**
 * AI Chatbot — 2-pane analyst workbench (mcp-chatbot-ux, FR-U01/U02/U03/U08).
 *
 * Layout
 *   [Header: model selector, ⌘K, New chat, theme toggle]
 *   [Conversation (60%)]  │  [ArtifactPanel (40%, md+)]
 *   [Composer]                │
 *
 * Mobile (<md) collapses to a single column; artifacts are appended to
 * the conversation stream as a compact strip instead of a side panel.
 *
 * Streaming semantics are inherited from `openChatStream` (FR-S05/S06):
 *   - tool_call  → push placeholder tool chip + artifact slot
 *   - tool_result → fill the chip and artifact with summary/ms
 *   - token       → append to the current assistant draft
 *   - done        → finalize session id and draft
 *   - error       → red bubble (retriable hints from backend)
 *
 * Pre-first-event failures fall back to POST /api/chat (which itself has
 * 1-retry on 503, see `fetchPOST` / FR-P11).
 */

import { useEffect, useId, useRef, useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Send,
  Sparkles,
  Square,
  Wrench,
} from "lucide-react";

import { ApiError, api } from "@/lib/api";
import type { ChatToolTrace } from "@/lib/api.types";
import { Markdown } from "@/components/ui/Markdown";
import { openChatStream, type StreamHandle } from "@/lib/sseClient";
import type { ChatEvent } from "@/lib/chatEvents";
import type { ReportBlock } from "@/lib/reportBlocks";
import { BlockRenderer } from "@/components/report/BlockRenderer";
import SuggestedBlock from "@/components/report/blocks/SuggestedBlock";

import ChatHeader from "@/components/chat/ChatHeader";
import CommandPalette from "@/components/chat/CommandPalette";
import { ChatModelProvider } from "@/components/chat/ModelSelector";

type Role = "user" | "assistant" | "system";

interface Msg {
  id: string;
  role: Role;
  content: string;
  trace?: ChatToolTrace[];
  /** rich-visual-reports: structured block payloads from tool_result events.
   *  Rendered inline beneath the assistant bubble (no side panel). */
  artifacts?: { tool: string; block: ReportBlock }[];
  /** FR-PSP-F — Perplexity-style follow-up chips arriving on the
   *  ``done`` event. Rendered under the assistant bubble. */
  suggested?: string[];
  hops?: number;
  error?: boolean;
  streaming?: boolean;
}

const QUICK_STARTS = [
  // US examples
  { label: "AI 반도체 (US)", prompt: "미국 AI 반도체 테마에서 매수 시그널 강한 종목 3개 추천하고 근거를 $ 단위로 설명해줘." },
  { label: "AAPL 매수 의견?", prompt: "AAPL 현재 시점 매수 의견과 근거, 리스크를 $ 단위 수치로 정리해줘." },
  // KR examples — exercise FR-K14/K15 paths
  { label: "한국 2차전지 추천", prompt: "한국 시장에서 2차전지 테마 상위 종목 3개를 ₩ 단위로 랭킹 이유와 함께 알려줘." },
  { label: "삼성전자(005930) 분석", prompt: "삼성전자(005930) 종합 분석과 매수 의견을 ₩ 단위로 정리해줘." },
  { label: "삼성 최근 공시", prompt: "삼성전자(005930) 의 최근 30일 DART 공시 목록을 알려줘." },
  { label: "오늘 시장 국면?", prompt: "지금 미국 시장 국면과 최근 강세 섹터를 알려줘." },
];

function uid() {
  return Math.random().toString(36).slice(2);
}

export default function ChatPage() {
  return (
    <ChatModelProvider>
      <ChatWorkbench />
    </ChatModelProvider>
  );
}

function ChatWorkbench() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<StreamHandle | null>(null);
  const eventArrivedRef = useRef(false);
  const liveRegionId = useId();

  // Auto-scroll to bottom on new content.
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, busy]);

  // Cancel in-flight stream on unmount.
  useEffect(() => {
    return () => {
      streamRef.current?.cancel();
    };
  }, []);

  // ⌘K / Ctrl+K → open palette.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  function newChat() {
    streamRef.current?.cancel();
    streamRef.current = null;
    setMessages([]);
    setSessionId(null);
    setBusy(false);
    setInput("");
  }

  function beginAssistantDraft(): string {
    const id = uid();
    setMessages((prev) => [
      ...prev,
      { id, role: "assistant", content: "", trace: [], hops: 0, streaming: true },
    ]);
    return id;
  }

  function updateAssistant(id: string, updater: (m: Msg) => Msg) {
    setMessages((prev) => prev.map((m) => (m.id === id ? updater(m) : m)));
  }

  async function fallbackPost(text: string, draftId: string) {
    try {
      const res = await api.chat(text, sessionId);
      setSessionId(res.session_id);
      updateAssistant(draftId, (m) => ({
        ...m,
        content: res.answer,
        trace: res.trace,
        hops: res.hops,
        streaming: false,
      }));
    } catch (e: unknown) {
      const msg =
        e instanceof ApiError
          ? `API 오류 (${e.code}): ${e.message}`
          : e instanceof Error
            ? e.message
            : "알 수 없는 오류가 발생했습니다.";
      updateAssistant(draftId, (m) => ({ ...m, content: msg, streaming: false, error: true }));
    } finally {
      setBusy(false);
      streamRef.current = null;
    }
  }

  function sendText(text: string) {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setInput("");
    setMessages((prev) => [...prev, { id: uid(), role: "user", content: trimmed }]);
    setBusy(true);
    const draftId = beginAssistantDraft();
    eventArrivedRef.current = false;

    streamRef.current = openChatStream(
      { message: trimmed, sessionId },
      {
        onEvent: (ev: ChatEvent) => {
          eventArrivedRef.current = true;
          if (ev.type === "tool_call") {
            updateAssistant(draftId, (m) => ({
              ...m,
              trace: [
                ...(m.trace ?? []),
                { tool: ev.tool, args: ev.args, result_summary: "실행 중…", ok: true },
              ],
              hops: ev.hop,
            }));
          } else if (ev.type === "tool_result") {
            updateAssistant(draftId, (m) => {
              const trace = [...(m.trace ?? [])];
              for (let i = trace.length - 1; i >= 0; i--) {
                if (trace[i].tool === ev.tool && trace[i].result_summary === "실행 중…") {
                  trace[i] = {
                    tool: ev.tool,
                    args: trace[i].args,
                    result_summary: `${ev.summary} · ${ev.ms}ms`,
                    ok: ev.ok,
                  };
                  break;
                }
              }
              // Attach structured artifacts inline — rendered right under
              // the assistant message body (no side panel; user previously
              // asked for single-column conversation).
              const artifacts = ev.artifact && ev.ok
                ? [
                    ...(m.artifacts ?? []),
                    ...ev.artifact.map((block) => ({ tool: ev.tool, block })),
                  ]
                : m.artifacts;
              return { ...m, trace, artifacts };
            });
          } else if (ev.type === "token") {
            updateAssistant(draftId, (m) => ({ ...m, content: m.content + ev.text }));
          } else if (ev.type === "done") {
            setSessionId(ev.session_id);
            updateAssistant(draftId, (m) => ({
              ...m,
              hops: ev.hops,
              streaming: false,
              suggested: ev.suggested ?? [],
              // Strip the trailing <<SUGGEST>>[...] marker from the visible
              // text in case it survived streaming (backend only strips on
              // the final session-history append).
              content: m.content.replace(/\s*<<SUGGEST>>\s*\[[^\]]*\]\s*$/m, "").trimEnd(),
            }));
          } else if (ev.type === "error") {
            updateAssistant(draftId, (m) => ({
              ...m,
              content: m.content || ev.message,
              streaming: false,
              error: true,
            }));
          }
        },
        onError: (err) => {
          if (!eventArrivedRef.current) {
            void fallbackPost(trimmed, draftId);
            return;
          }
          updateAssistant(draftId, (m) => ({
            ...m,
            content: m.content || err.message,
            streaming: false,
            error: true,
          }));
        },
        onClose: () => {
          updateAssistant(draftId, (m) => (m.streaming ? { ...m, streaming: false } : m));
          setBusy(false);
          streamRef.current = null;
        },
      },
    );
  }

  function stopStream() {
    streamRef.current?.cancel();
    streamRef.current = null;
    setBusy(false);
    setMessages((prev) =>
      prev.map((m) =>
        m.streaming ? { ...m, streaming: false, content: m.content || "(응답 중단됨)" } : m,
      ),
    );
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    sendText(input);
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendText(input);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)] max-w-4xl mx-auto">
      <ChatHeader
        sessionId={sessionId}
        onNewChat={newChat}
        onOpenCommand={() => setPaletteOpen(true)}
      />

      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        items={QUICK_STARTS}
        onPick={(p) => sendText(p)}
      />

      {/* Single-column conversation. Artifact side panel was removed per
          user request — all tool results live in the inline trace panel. */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div
          ref={listRef}
          role="log"
          aria-live="polite"
          aria-relevant="additions"
          aria-labelledby={liveRegionId}
          className="flex-1 overflow-y-auto rounded-xl border bg-white dark:bg-slate-900 p-4 space-y-3"
          style={{ borderColor: "var(--border)" }}
        >
          <span id={liveRegionId} className="sr-only">
            Chat messages
          </span>
          {messages.length === 0 && <EmptyState onPick={(p) => sendText(p)} />}
          {messages.map((m) => (
            <MessageBubble key={m.id} msg={m} onSuggestedPick={(q) => sendText(q)} />
          ))}
        </div>

        <form onSubmit={onSubmit} className="mt-3 flex gap-2 items-end">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            rows={2}
            placeholder="질문을 입력하세요. Shift+Enter 로 줄바꿈, ⌘K 로 빠른 명령."
            aria-label="질문 입력"
            disabled={busy}
            className="flex-1 resize-none rounded-lg border bg-white dark:bg-slate-900 px-3 py-2 text-sm text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-slate-50 dark:disabled:bg-slate-800"
            style={{ borderColor: "var(--border)" }}
          />
          {busy ? (
            <button
              type="button"
              onClick={stopStream}
              aria-label="응답 중단"
              className="inline-flex items-center justify-center gap-1 rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white shadow hover:bg-slate-800 transition-colors"
            >
              <Square className="w-4 h-4" />
              중단
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              aria-label="메시지 전송"
              className="inline-flex items-center justify-center gap-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 transition-colors"
            >
              <Send className="w-4 h-4" />
              전송
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (prompt: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <Sparkles className="w-10 h-10 text-blue-400 mb-3" />
      <p className="text-slate-700 dark:text-slate-200 font-medium">무엇이든 물어보세요</p>
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
        예: 테마 추천, 종목 분석, 매수 시그널, 시장 국면 · ⌘K 로 더 빠르게
      </p>
      <div className="mt-5 flex flex-wrap gap-2 justify-center max-w-2xl">
        {QUICK_STARTS.map((q) => (
          <button
            key={q.label}
            type="button"
            onClick={() => onPick(q.prompt)}
            className="rounded-full border bg-slate-50 dark:bg-slate-800 px-3 py-1.5 text-xs text-slate-700 dark:text-slate-200 hover:bg-blue-50 dark:hover:bg-blue-950 hover:border-blue-300 transition-colors"
            style={{ borderColor: "var(--border)" }}
          >
            {q.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function MessageBubble({ msg, onSuggestedPick }: { msg: Msg; onSuggestedPick?: (q: string) => void }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-blue-600 text-white px-4 py-2.5 text-sm whitespace-pre-wrap">
          {msg.content}
        </div>
      </div>
    );
  }
  const empty = !msg.content && !msg.error;
  return (
    <div className="flex justify-start">
      <div
        className={`max-w-[85%] rounded-2xl rounded-bl-sm px-4 py-3 text-sm ${
          msg.error
            ? "bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-900 text-red-800 dark:text-red-100"
            : "bg-slate-50 dark:bg-slate-800 border text-slate-900 dark:text-slate-50"
        }`}
        style={!msg.error ? { borderColor: "var(--border)" } : undefined}
      >
        {msg.error ? (
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{msg.content}</span>
          </div>
        ) : empty ? (
          <TypingDots />
        ) : (
          <div className="relative">
            <Markdown>{msg.content}</Markdown>
            {msg.streaming && <BlinkingCaret />}
          </div>
        )}
        {msg.artifacts && msg.artifacts.length > 0 && (
          <div className="mt-3 space-y-3">
            {msg.artifacts.map((a, i) => (
              <BlockRenderer key={`${a.tool}-${i}`} block={a.block} />
            ))}
          </div>
        )}
        {msg.trace && msg.trace.length > 0 && <ToolTracePanel trace={msg.trace} hops={msg.hops ?? 0} />}
        {/* FR-PSP-F — Perplexity-style follow-up chips. Click submits the
            text as the next user turn via sendText. */}
        {msg.suggested && msg.suggested.length > 0 && !msg.error && (
          <SuggestedBlock items={msg.suggested} onPick={onSuggestedPick} />
        )}
      </div>
    </div>
  );
}

function ToolTracePanel({ trace, hops }: { trace: ChatToolTrace[]; hops: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3 border-t pt-2" style={{ borderColor: "var(--border)" }}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100"
      >
        {open ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        <Wrench className="w-3 h-3" />
        도구 호출 {hops}회 ({trace.length}건)
      </button>
      {open && (
        <ul className="mt-2 space-y-1.5 text-xs tabular">
          {trace.map((t, i) => (
            <li
              key={i}
              className="rounded-md bg-white dark:bg-slate-900 border px-2 py-1.5"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-semibold text-slate-700 dark:text-slate-200">{t.tool}</span>
                <span className={t.ok ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}>
                  {t.result_summary === "실행 중…" ? "running…" : t.ok ? "ok" : "error"}
                </span>
              </div>
              {Object.keys(t.args).length > 0 && (
                <div className="text-slate-500 dark:text-slate-400 font-mono break-all mt-0.5">
                  args: {JSON.stringify(t.args)}
                </div>
              )}
              <div className="text-slate-600 dark:text-slate-300 mt-0.5">→ {t.result_summary}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TypingDots() {
  return (
    <span className="inline-flex gap-1 items-center text-slate-500 dark:text-slate-400">
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "0ms" }} />
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "120ms" }} />
      <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: "240ms" }} />
      <span className="ml-2 text-xs">분석 중…</span>
    </span>
  );
}

function BlinkingCaret() {
  return (
    <span
      aria-hidden="true"
      className="inline-block w-[0.5ch] h-[1em] bg-slate-500 ml-0.5 align-[-0.15em] animate-pulse"
    />
  );
}
