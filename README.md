# Stock Manager

> An AI-powered stock analysis dashboard for the Korean and U.S. markets — chat with a Gemini-backed analyst, generate streaming research reports, rank candidates, and inspect single tickers, all from one browser tab.

**Live demo**: <!-- DEMO_URL --> _(updated after deployment)_
**License**: [MIT](LICENSE) · **Third-party notices**: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)

---

## What it does

A reviewer landing on the dashboard can:

| Page | Purpose |
|---|---|
| **`/` (Home)** | Market overview cards (KOSPI / S&P 500 / sector heat) and quick-jump actions. |
| **`/chat`** | Streaming chat with a Gemini-backed analyst. Tool-augmented: the assistant can pull prices, news, filings, fundamentals, and rankings on demand and render rich blocks (tables, charts, ticker pills, follow-up suggestions) inline. SSE-streamed responses with stop-button support. |
| **`/stock/[ticker]`** | Single-ticker deep dive — price chart, technical indicators (SMA / EMA / RSI / MACD / Bollinger / ADX), fundamentals snapshot, recent news. Works for both U.S. tickers (`AAPL`) and Korean codes (`005930`). |
| **`/ranking`** | Multi-factor ranking across a candidate set — fundamentals, momentum, sentiment composite. Triggers a streaming analysis report when a candidate is opened. |
| **`/theme`** | Theme exploration — propose tickers from a natural-language theme, then run cross-ticker comparisons. |
| **`/portfolio`** | Holdings evaluation — sector allocation, dividend yield, correlation matrix, phase signals (uptrend / hold / unstable / red-flag). |

The same backend tools also expose an MCP (Model Context Protocol) server, so anyone running Claude Desktop or another MCP host can call them directly from their own client.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Next.js 16 dashboard (Turbopack)   │  ← Vercel
│  · App Router pages                  │
│  · SSE chat client + ReadableStream  │
│  · framer-motion + Tailwind tokens   │
└────────────────┬────────────────────┘
                 │ REST + SSE (NEXT_PUBLIC_API_URL)
                 ▼
┌─────────────────────────────────────┐
│  FastAPI backend                    │  ← Hugging Face Spaces (Docker)
│  · /api/chat/stream (SSE)            │
│  · /api/technical/* /finnhub/*       │
│  · /api/ranking/analysis-report      │
│  · slowapi rate-limit + CORS         │
│  · diskcache + circuit breakers      │
└────────────────┬────────────────────┘
                 │
   ┌─────────────┼─────────────┬──────────────┐
   ▼             ▼             ▼              ▼
 Gemini API   yfinance /    DART OPEN API   PyKrx /
 (LLM)        Finnhub /     (KR filings &   FinanceData-
              SEC EDGAR     fundamentals)   Reader (KR)
```

### Tech stack

- **Frontend**: Next.js 16 (App Router, Turbopack), React 19, TypeScript, Tailwind CSS, framer-motion, recharts, react-markdown, lucide-react. Source Serif 4 via `next/font/google`.
- **Backend**: FastAPI, Uvicorn, Pydantic v2, SlowAPI, Tenacity (retry + circuit breaker), Diskcache, APScheduler, Jinja2.
- **LLM**: Google Gemini (`gemini-2.5-flash` default, with a resilient fallback chain through `gemini-2.0-flash` / `gemini-2.0-flash-lite` / `gemini-2.5-flash-lite`). Streaming via the `streamGenerateContent` REST endpoint. UTF-8 forced on responses for Korean output.
- **MCP**: `fastmcp` server exposing 39 tools — the same tool surface the web chat orchestrator uses.
- **Markets**:
  - Korea — `pykrx`, `finance-datareader`, `OpenDartReader`, plus a 3-tier KOSPI/KOSDAQ classifier (seed JSON → live yfinance probe → `.KS` fallback) so 6-digit codes resolve to the right Yahoo suffix automatically.
  - U.S. — `yfinance` (price + fundamentals), optional Finnhub (analyst/insider/earnings) and SEC EDGAR (filings).

### Project layout

```
api/                FastAPI app (server.py) + chat orchestration services
mcp_server/         FastMCP tools + market-data adapters (yfinance, PyKrx, DART)
core/               Cross-cutting config, schemas, resilience helpers
dashboard/          Next.js 16 frontend (App Router under src/app)
docs/               Architecture notes + archived PDCA cycles
tests/              Pytest suite (~70 tests covering tools, KR market, server bootstrap)
Dockerfile          Backend container (Hugging Face Spaces / any Docker host)
```

---

## Running locally

Prereqs: Python 3.11+, Node 20+, a free [Google AI Studio key](https://aistudio.google.com/apikey).

```bash
# 1. Configure environment
cp .env.example .env
# Set GEMINI_API_KEY at minimum. DART/Finnhub keys are optional (graceful fallback).

# 2. Backend — FastAPI on :8000
pip install -r requirements.txt
uvicorn api.server:app --reload

# 3. Frontend — Next.js 16 on :3000
cd dashboard
npm install
npm run dev
```

Visit http://localhost:3000 — the chat at `/chat` is the fastest way to see the whole pipeline in action (try `삼성전자 005930 종합 분석` or `AAPL deep dive`).

### Run the tests

```bash
pytest -q
```

### Optional: use as an MCP server in Claude Desktop or any MCP host

```bash
python -m mcp_server.mcp_app   # stdio MCP transport
```

See `mcp_config.sample.json` for a Claude Desktop config snippet.

---

## Deployment

The repository is wired for a two-platform free-tier deployment:

- **Backend** → Hugging Face Spaces (Docker SDK). The included `Dockerfile` is HF-Spaces compatible (port 7860, `/tmp` writable for `diskcache` / matplotlib). All API keys are set as Space **Secrets**; non-sensitive config (`ALLOWED_ORIGINS`, `CHAT_MODEL`) goes in **Variables**.
- **Frontend** → Vercel. Set the project's **Root Directory** to `dashboard/` and add `NEXT_PUBLIC_API_URL` pointing at the Space URL.

Both tiers are free and require no credit card.

---

## License & attribution

- Code: [MIT License](LICENSE) — © 2025 Taeyoung Choi
- Dependency licenses (per package): [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
- Font: Source Serif 4 — SIL Open Font License 1.1
- Icons: lucide-react — ISC
- External data services: Google Gemini, Yahoo Finance, KRX, DART OPEN API, Finnhub (optional), SEC EDGAR (optional). Used in accordance with each provider's terms for non-commercial research; no scraped content is redistributed.

No third-party copyrighted images, illustrations, or stock media are bundled in this repository. Every chart and report image is generated at runtime from public market data by code in this repo.
