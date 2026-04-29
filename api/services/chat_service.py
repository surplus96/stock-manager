"""Chat orchestration service (mcp-chatbot).

Implements a prompt-based tool-calling loop:

    1. Build system prompt enumerating ``TOOL_SPECS``.
    2. Send transcript to Gemma via ``_call_gemma``.
    3. Parse the model's reply:
        * leading ``{ "tool": ... }`` JSON  → execute tool, append observation,
          loop again (up to ``MAX_HOPS``).
        * anything else                     → final answer, return.

Why prompt-based (not native function calling)?
    The default ``GEMINI_MODEL`` is Gemma 4, which does not support the
    Gemini SDK's ``tools=`` parameter. A JSON contract works on every
    model and is trivial to swap for native function calling later.

Session memory is kept in-process (dict) with a 30 minute TTL so the user
can ask follow-ups ("더 자세히", "다른 종목은?") without losing context.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from api.services import chat_metrics

from api.schemas.chat import ChatResponseData, ToolTrace
from api.services.chat_tools import TOOL_SPECS, execute_tool, summarize_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

MAX_HOPS = 5
SESSION_TTL = timedelta(minutes=30)
MAX_HISTORY_TURNS = 20  # rolling window to cap prompt size

# Resilience knobs for upstream Gemini outages (e.g. preview-model 503s).
LLM_INNER_RETRIES = 3            # extra attempts beyond _call_gemma's own retry
LLM_RETRY_BACKOFF_SEC = 2.0      # base backoff; doubled each attempt
# Comma-separated fallback model list. Tried in order when the primary 5xx's.
# This shadow list mirrors ``mcp_server.tools.llm._LLM_FALLBACK_MODELS_DEFAULT``
# and exists only for callers that import the constant directly. The
# resilient wrapper in ``llm.py`` is the source of truth for the runtime
# chain — kept in sync to avoid surprise.
LLM_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_FALLBACK_MODELS",
        "gemini-2.0-flash,gemini-2.0-flash-lite,gemini-2.5-flash-lite",
    ).split(",")
    if m.strip()
]


# ---------------------------------------------------------------------------
# Session memory (process-local; production would swap to Redis)
# ---------------------------------------------------------------------------

@dataclass
class _Session:
    messages: list[dict[str, str]] = field(default_factory=list)  # role, content
    last_used: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))


_SESSIONS: dict[str, _Session] = {}


def _gc_sessions() -> None:
    cutoff = datetime.now(tz=timezone.utc) - SESSION_TTL
    stale = [sid for sid, s in _SESSIONS.items() if s.last_used < cutoff]
    for sid in stale:
        _SESSIONS.pop(sid, None)


def _get_or_create_session(session_id: str | None) -> tuple[str, _Session]:
    _gc_sessions()
    if session_id and session_id in _SESSIONS:
        sess = _SESSIONS[session_id]
        sess.last_used = datetime.now(tz=timezone.utc)
        return session_id, sess
    new_id = session_id or str(uuid.uuid4())
    sess = _Session()
    _SESSIONS[new_id] = sess
    return new_id, sess


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    lines = [
        "당신은 시니어 금융 애널리스트입니다. 사용자 질문에 답하기 위해 아래 도구들을",
        "필요할 때만 호출할 수 있습니다. 도구 결과를 받으면 자연어로 종합해 답하세요.",
        "",
        "## 도구 목록",
    ]
    for t in TOOL_SPECS:
        arg_strs = []
        for a in t.args:
            req = "" if a.required else "?"
            default = f"={a.default}" if a.default is not None and not a.required else ""
            arg_strs.append(f"{a.name}{req}: {a.type}{default}")
        sig = f"{t.name}({', '.join(arg_strs)})"
        lines.append(f"- **{sig}** — {t.description}")
        for a in t.args:
            if a.description:
                lines.append(f"    - `{a.name}`: {a.description}")
    lines += [
        "",
        "## 도구 호출 형식 (반드시 준수)",
        "도구가 필요하면 응답의 **첫 줄을 JSON 한 줄**로 시작하세요:",
        '`{"tool": "도구이름", "args": {"key": "value"}}`',
        "JSON 외 다른 텍스트는 절대 추가하지 마세요. 도구 결과를 받으면 다음 턴에 또",
        "다른 도구를 호출하거나, 자연어로 최종 답을 작성합니다.",
        "",
        "## 한국 / 미국 주식 구분 규칙 (FR-K 통합)",
        "- **6자리 숫자 코드** (예: `005930`, `373220`) → 한국 상장사. 기본 통화 **₩(KRW)**",
        "- `.KS` / `.KQ` 접미 티커 (예: `005930.KS`) → 한국 상장사",
        "- 영문 대문자 티커 (예: `AAPL`, `NVDA`, `MSFT`) → 미국 상장사. 기본 통화 **$(USD)**",
        "- 한국 테마/종목 질의에는 `propose_themes_kr` / `analyze_theme_kr` / `dart_filings` 우선 사용",
        "- 미국 테마/종목 질의에는 기존 `propose_themes` / `analyze_theme` 사용",
        "- 종목명(한글)을 그대로 도구 인자로 전달해도 백엔드가 6자리 코드로 자동 매핑한다 (예: `ticker=\"삼성전자\"` 정상 동작).",
        "  하지만 가능하면 코드(`005930`) 로 호출해 정확성을 확보할 것.",
        "",
        "## 최종 답변 작성 규칙",
        "- 한국어, 시니어 애널리스트 어조",
        "- 도구 결과의 **수치를 반드시 인용** (예: '종합점수 78.4/100', '60일 SPY 수익률 +4.3%')",
        "- **통화 표기 강제**: 도구 결과의 `market`/`currency` 필드를 확인하고 KR=₩, US=$ 기호 사용",
        "  - 예: 삼성전자 시가총액 `₩400조`, AAPL 시가총액 `$3.2T`",
        "  - 한국 종목과 미국 종목이 섞이면 각 종목별로 해당 통화 사용 (혼용 금지)",
        "  - 종합점수/수익률/팩터 점수 같은 **단위 없는 값은 그대로** (₩ 붙이지 말 것)",
        "- 한국 종목은 한글명과 6자리 코드 병기 (예: '삼성전자(005930)')",
        "- 매수/매도 의견은 근거 + 리스크 함께 제시",
        "- 모르는 영역은 '추가 분석 필요'라고 솔직히 표시",
        "- 최대 5개 도구까지만 호출 가능 (이후는 강제 종료)",
        "",
        "## 권장 패턴",
        "- '미국 테마 추천' → propose_themes → analyze_theme",
        "- '한국 테마 추천' → propose_themes_kr → analyze_theme_kr",
        "- '종목 분석' (KR 또는 US) → stock_comprehensive + news_sentiment",
        "- '한국 종목 공시 확인' → dart_filings",
        "- '시장 상황' → market_condition (미국 SPY 기반)",
        "",
        "## 답변 마무리 (FR-PSP-F: Suggested follow-ups)",
        "최종 자연어 답변 마지막 줄에 **<<SUGGEST>>** 마커와 함께 다음과 같은 ",
        "JSON 배열을 추가하세요. 사용자가 자연스럽게 이어 갈 후속 질문 3~5개:",
        '`<<SUGGEST>>["질문1","질문2","질문3"]`',
        "- 각 항목은 50자 이내, 같은 답변에서 이미 다룬 내용 재질의는 금지",
        "- 마커 줄은 사용자에게 표시되지 않음. 누락해도 답변 자체에는 영향 없음.",
    ]
    return "\n".join(lines)


def build_transcript(history: list[dict[str, str]], new_user_message: str) -> str:
    """Render history + new turn into a single prompt the LLM can read."""
    parts = []
    # Cap history to avoid prompt bloat
    recent = history[-MAX_HISTORY_TURNS * 2 :]
    for m in recent:
        role = m["role"]
        if role == "user":
            parts.append(f"사용자: {m['content']}")
        elif role == "assistant":
            parts.append(f"어시스턴트: {m['content']}")
        elif role == "tool":
            parts.append(f"[도구 결과]\n{m['content']}")
    parts.append(f"사용자: {new_user_message}")
    parts.append("어시스턴트:")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

_SUGGEST_MARKER_RE = re.compile(
    r"<<SUGGEST>>\s*(\[[^\]]*\])\s*$",
    re.MULTILINE,
)


def split_suggested_marker(text: str) -> tuple[str, list[str]]:
    """Strip the trailing ``<<SUGGEST>>[...]`` marker from an LLM answer.

    Returns ``(clean_text, suggested_list)``. If the marker is missing or
    the JSON is malformed the answer text is returned untouched and
    ``suggested_list`` is empty — the chip row simply doesn't render,
    which is the intended FR-PSP-F backward-compat behaviour.
    """
    if not text or "<<SUGGEST>>" not in text:
        return text, []
    m = _SUGGEST_MARKER_RE.search(text)
    if not m:
        return text, []
    raw_json = m.group(1)
    try:
        items = json.loads(raw_json)
    except json.JSONDecodeError:
        return text, []
    if not isinstance(items, list):
        return text, []
    clean = (text[: m.start()] + text[m.end():]).rstrip()
    out: list[str] = []
    for entry in items:
        if isinstance(entry, str):
            s = entry.strip()
            if s:
                out.append(s[:80])  # cap length defensively
        if len(out) >= 8:
            break
    return clean, out


def parse_tool_call(text: str) -> dict[str, Any] | None:
    """Return ``{"tool": str, "args": dict}`` if the reply is a tool call.

    Tolerant: accepts triple-backtick ``json`` fences and leading whitespace.
    Returns ``None`` if no parseable JSON tool call is found — that means
    the reply is the final answer.
    """
    if not text:
        return None
    cleaned = text.strip()
    # Strip markdown code fence if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    # Quick check: must begin with { and contain "tool"
    if not cleaned.startswith("{") or '"tool"' not in cleaned[:200]:
        return None
    # Try to extract first balanced JSON object
    depth = 0
    end = -1
    for i, ch in enumerate(cleaned):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        return None
    blob = cleaned[:end]
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict) or "tool" not in obj:
        return None
    args = obj.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    return {"tool": str(obj["tool"]), "args": args}


# ---------------------------------------------------------------------------
# Resilient LLM call — FR-P05: thin shim over mcp_server.tools.llm so other
# modules (chat_stream_service, tests) can still import these names.
# ---------------------------------------------------------------------------

def _is_transient_upstream_error(exc: BaseException) -> bool:
    from mcp_server.tools.llm import is_transient_upstream_error
    return is_transient_upstream_error(exc)


def _call_llm_resilient(system: str, prompt: str, temperature: float = 0.2) -> str:
    """Chatbot wrapper — pins chat to ``settings.default_chat_model``."""
    from mcp_server.tools.llm import call_llm_resilient
    from core.config import get_settings
    model = get_settings().default_chat_model
    return call_llm_resilient(system, prompt, model=model, temperature=temperature)


def _friendly_llm_error(exc: BaseException) -> str:
    """Convert an upstream LLM failure into a Korean user-facing message."""
    if _is_transient_upstream_error(exc):
        return (
            "LLM 서비스가 일시적으로 응답하지 않습니다 (Google AI Studio 503/타임아웃). "
            "잠시 후 다시 질문해 주세요. 문제가 계속되면 `GEMINI_MODEL` 을 안정 버전 "
            "(예: `gemini-2.5-flash` 또는 `gemini-2.0-flash`) 으로 바꿔 보세요."
        )
    return f"LLM 호출 실패: {exc}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_chat(message: str, session_id: str | None = None) -> ChatResponseData:
    sid, sess = _get_or_create_session(session_id)
    sess.messages.append({"role": "user", "content": message})

    system = build_system_prompt()
    trace: list[ToolTrace] = []
    answer = ""
    hops = 0
    t_request_start = time.monotonic()

    # Inner-loop: tool calls until the LLM returns a final answer
    for _ in range(MAX_HOPS + 1):
        prompt = build_transcript(sess.messages, "")  # message already appended
        try:
            raw = _call_llm_resilient(system, prompt)
        except Exception as e:  # noqa: BLE001
            logger.warning("LLM call failed after retries: %s", e)
            chat_metrics.record_llm_error()
            answer = _friendly_llm_error(e)
            break

        call = parse_tool_call(raw)
        if call is None:
            # Final answer
            answer = raw.strip() or "(빈 응답)"
            break

        if hops >= MAX_HOPS:
            answer = (
                "도구 호출 한도(5회)에 도달해 종합 답변을 생성할 수 없었습니다. "
                "질문을 좁혀서 다시 물어봐 주세요."
            )
            break

        hops += 1
        t_tool = time.monotonic()
        ok, result = execute_tool(call["tool"], call["args"])
        tool_ms = (time.monotonic() - t_tool) * 1000
        chat_metrics.record_tool(ok, tool_ms)
        logger.info(
            "chat.hop session=%s hop=%d tool=%s ok=%s latency_ms=%.0f",
            sid, hops, call["tool"], ok, tool_ms,
        )
        summary = summarize_result(result) if ok else f"ERROR: {result}"
        trace.append(ToolTrace(
            tool=call["tool"],
            args=call["args"],
            result_summary=summary,
            ok=ok,
        ))
        # Feed observation back to the model as a "tool" turn
        observation = json.dumps(
            {"tool": call["tool"], "ok": ok, "result": result},
            ensure_ascii=False,
            default=str,
        )
        # Keep observation manageable
        if len(observation) > 8000:
            observation = observation[:8000] + " …(truncated)"
        sess.messages.append({"role": "tool", "content": observation})

    # FR-PSP-F: split off the trailing <<SUGGEST>>[...] marker before we
    # commit the answer to the session transcript.
    clean_answer, suggested = split_suggested_marker(answer)
    sess.messages.append({"role": "assistant", "content": clean_answer})
    total_ms = (time.monotonic() - t_request_start) * 1000
    chat_metrics.record_request(total_ms, hops)
    return ChatResponseData(
        session_id=sid, answer=clean_answer, trace=trace, hops=hops,
        suggested=suggested,
    )


def get_session_history(session_id: str) -> list[dict[str, str]] | None:
    sess = _SESSIONS.get(session_id)
    return list(sess.messages) if sess else None
