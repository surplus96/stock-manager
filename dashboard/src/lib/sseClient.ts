/**
 * Lightweight Server-Sent Events client for `/api/chat/stream`
 * (mcp-chatbot-streaming, FR-S05).
 *
 * Why fetch + ReadableStream instead of the built-in `EventSource`?
 *   - We need `AbortController` support for clean cancellation.
 *   - We want to attach non-GET headers later (Authorization, CSRF, …).
 *   - Frame parsing is trivially small.
 *
 * Frame format: every event is a single line `data: <json>\n\n`. Comments
 * (lines starting with `:`) and unknown event-name fields are ignored —
 * this matches the SSE spec closely enough for our single-channel use.
 */

import { type ChatEvent, isChatEvent } from "./chatEvents";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface StreamHandlers {
  onEvent: (event: ChatEvent) => void;
  onError?: (err: Error) => void;
  onClose?: () => void;
}

export interface StreamOptions {
  message: string;
  sessionId: string | null;
}

export interface StreamHandle {
  /** Abort the underlying fetch. Safe to call after completion (no-op). */
  cancel: () => void;
}

export function openChatStream(opts: StreamOptions, handlers: StreamHandlers): StreamHandle {
  const ctrl = new AbortController();
  const url = new URL(`${API_BASE}/api/chat/stream`);
  url.searchParams.set("message", opts.message);
  if (opts.sessionId) url.searchParams.set("session_id", opts.sessionId);

  const run = async () => {
    let res: Response;
    try {
      res = await fetch(url.toString(), {
        signal: ctrl.signal,
        headers: { Accept: "text/event-stream" },
      });
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        handlers.onError?.(e as Error);
      }
      handlers.onClose?.();
      return;
    }
    if (!res.ok || !res.body) {
      handlers.onError?.(new Error(`HTTP ${res.status}`));
      handlers.onClose?.();
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Frames are separated by a blank line (\n\n).
        let idx: number;
        while ((idx = buffer.indexOf("\n\n")) >= 0) {
          const frame = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          const dataLine = frame
            .split("\n")
            .find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          try {
            const parsed = JSON.parse(dataLine.slice(6)) as unknown;
            if (isChatEvent(parsed)) {
              handlers.onEvent(parsed);
            }
          } catch {
            // Skip malformed frame; streaming continues.
          }
        }
      }
    } catch (e) {
      if ((e as Error).name !== "AbortError") {
        handlers.onError?.(e as Error);
      }
    } finally {
      handlers.onClose?.();
    }
  };

  void run();

  return { cancel: () => ctrl.abort() };
}
