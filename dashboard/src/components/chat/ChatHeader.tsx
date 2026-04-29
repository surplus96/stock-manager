"use client";

/** Chat header — FR-U03. Model selector + session badge + new-chat + theme. */

import { Plus, Sparkles } from "lucide-react";
import ModelSelector from "./ModelSelector";
import ThemeToggle from "./ThemeToggle";

interface ChatHeaderProps {
  sessionId: string | null;
  onNewChat: () => void;
  onOpenCommand: () => void;
}

export default function ChatHeader({ sessionId, onNewChat, onOpenCommand }: ChatHeaderProps) {
  return (
    <header className="flex items-center justify-between gap-3 mb-4 flex-wrap">
      <div className="flex items-center gap-2">
        <Sparkles className="w-6 h-6 text-blue-500" aria-hidden="true" />
        <h1 className="text-xl md:text-2xl font-bold text-slate-800 dark:text-slate-100">
          AI Chatbot
        </h1>
      </div>
      <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
        <ModelSelector />
        <button
          type="button"
          onClick={onOpenCommand}
          aria-label="Open command palette (⌘K)"
          title="⌘K / Ctrl+K"
          className="hidden sm:inline-flex items-center gap-1 rounded-md border bg-white dark:bg-slate-900 px-2 py-1 text-xs text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-800"
          style={{ borderColor: "var(--border)" }}
        >
          <kbd className="font-mono text-[10px]">⌘K</kbd>
          <span>Actions</span>
        </button>
        <button
          type="button"
          onClick={onNewChat}
          aria-label="New chat"
          title="New chat"
          className="inline-flex items-center gap-1 rounded-md border bg-white dark:bg-slate-900 px-2 py-1 text-xs text-slate-600 hover:bg-slate-50 dark:hover:bg-slate-800"
          style={{ borderColor: "var(--border)" }}
        >
          <Plus className="w-3.5 h-3.5" />
          New
        </button>
        <ThemeToggle />
        <span
          className="hidden md:inline font-mono tabular text-[11px] text-slate-400 dark:text-slate-500"
          title="Session ID"
        >
          {sessionId ? sessionId.slice(0, 8) : "new"}
        </span>
      </div>
    </header>
  );
}
