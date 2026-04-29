/**
 * Chat SSE event schema — mirror of `api/services/chat_events.py`.
 *
 * The backend emits one JSON object per SSE frame, all tagged with a
 * `type` field so consumers can exhaustively branch on this discriminated
 * union.
 */

import type { ReportBlock } from "./reportBlocks";

export type ChatEvent =
  | { type: "tool_call"; tool: string; args: Record<string, unknown>; hop: number }
  | {
      type: "tool_result";
      tool: string;
      ok: boolean;
      summary: string;
      ms: number;
      hop: number;
      /** Optional structured payload — rich-visual-reports (FR-R-B06). */
      artifact?: ReportBlock[];
    }
  | { type: "token"; text: string }
  | { type: "done"; hops: number; session_id: string; suggested?: string[] }
  | { type: "error"; message: string; retriable: boolean };

export function isChatEvent(value: unknown): value is ChatEvent {
  if (typeof value !== "object" || value === null) return false;
  const t = (value as { type?: unknown }).type;
  return (
    t === "tool_call" ||
    t === "tool_result" ||
    t === "token" ||
    t === "done" ||
    t === "error"
  );
}
