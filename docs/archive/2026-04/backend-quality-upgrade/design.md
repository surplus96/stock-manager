---
template: design
version: 1.2
feature: backend-quality-upgrade
date: 2026-04-15
author: Stock Manager Team
project: Stock Manager (adoring-swartz)
status: Draft
---

# backend-quality-upgrade Design Document

> **Summary**: FastAPI 백엔드를 라우터/스키마/서비스 레이어로 재편하고, 보안·안정성·관측성을 표준화한다.
>
> **Project**: Stock Manager
> **Version**: 1.0 → 1.1
> **Author**: Stock Manager Team
> **Date**: 2026-04-15
> **Status**: Draft
> **Planning Doc**: [backend-quality-upgrade.plan.md](../../01-plan/features/backend-quality-upgrade.plan.md)

---

## 1. Overview

### 1.1 Design Goals

- 단일 `api/server.py` 921 LoC를 도메인별 APIRouter로 분해
- 모든 경계(입·출력, 에러, 설정, 시크릿)를 타입/정책으로 명시화
- LLM/외부 호출의 안정성 계층(Timeout·Retry·Circuit) 재정렬
- 관측성(structlog + request_id) 일관화, pytest 70%+ 커버리지

### 1.2 Design Principles

- **Boundary first**: Router는 IO, Service는 로직, Tools는 도메인 어댑터
- **Fail-fast config**: 환경변수는 앱 기동 시 pydantic-settings 로 검증
- **Secrets never in URL/logs**: 헤더 전송 + 로그 마스킹
- **Backward compatibility**: 응답 스키마는 v1 유지 후 v2 병행
- **Observable by default**: 모든 요청에 request_id, 모든 에러에 context

---

## 2. Architecture

### 2.1 Component Diagram

```
[Client Dashboard]
       │  HTTPS
       ▼
[FastAPI App Factory (api/main.py)]
  ├── Middleware: CORS / RequestID / RateLimit / ErrorHandler
  ├── Routers (api/routers/*)
  │     portfolio · theme · analysis · news · llm · health
  ├── Services (api/services/*)
  └── Schemas (api/schemas/*)
             │
             ▼
     [mcp_server/tools/*]  (도메인 어댑터, 최소 수정)
             │
             ▼
   [External: Gemini API / Data Sources]
```

### 2.2 Data Flow

```
Request
  → CORS check
  → RequestID middleware (uuid4 → contextvars)
  → RateLimit (slowapi, key=IP)
  → Router (pydantic validate)
  → Service (orchestration)
  → Tool (domain call, resilience wrapper)
  → Response (pydantic serialize)
  → ErrorHandler(on raise) → structured JSON error
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| routers/* | services/*, schemas/* | IO 바인딩 |
| services/* | mcp_server/tools/*, core/* | 비즈니스 로직 |
| core/config | pydantic-settings | env 검증 |
| core/logging | structlog | 구조적 로깅 |
| core/errors | FastAPI ExceptionHandler | 공통 에러 |
| core/resilience | httpx, tenacity | timeout/retry |

---

## 3. Data Model

### 3.1 Core Schemas (Pydantic v2)

```python
# api/schemas/common.py
from pydantic import BaseModel, Field
from datetime import datetime

class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict | None = None

class Envelope[T](BaseModel):
    data: T
    generated_at: datetime
    version: str = "v1"
```

```python
# api/schemas/analysis.py
class AnalysisRequest(BaseModel):
    tickers: list[str] = Field(min_length=1, max_length=50)
    include_llm_report: bool = True
    timeframe: Literal["1M", "3M", "6M", "1Y"] = "3M"

class AnalysisReport(BaseModel):
    summary: str
    sections: dict[str, str]     # executive/risk/valuation/...
    metrics: dict[str, float]
    citations: list[str]
```

### 3.2 Config Schema

```python
# core/config.py
class Settings(BaseSettings):
    pm_mcp_root: Path
    gemini_api_key: SecretStr
    gemini_model: str = "gemini-3.1-flash-lite-preview"
    llm_timeout_sec: int = 300
    rate_limit_per_min: int = 60
    allowed_origins: list[str]
    log_level: str = "INFO"
    environment: Literal["dev", "staging", "prod"] = "dev"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

---

## 4. API Specification

### 4.1 Endpoint Reorganization

| Router | Path Prefix | Endpoints (예) |
|--------|-------------|----------------|
| portfolio | `/api/portfolio` | GET list, POST save, GET `/{id}` |
| theme | `/api/theme` | GET list, POST analyze |
| analysis | `/api/analysis` | POST comprehensive, GET `/{id}` |
| news | `/api/news` | GET search, GET sentiment |
| llm | `/api/llm` | POST report (stream optional) |
| health | `/health` | GET `/`, GET `/detail` |

### 4.2 LLM Report Endpoint (개선)

`POST /api/llm/report`

**Request**
```json
{ "tickers": ["AAPL","MSFT"], "sections": ["executive","risk","valuation","outlook"] }
```

**Server flow**
```python
async def build_report(req):
    tasks = {s: asyncio.create_task(gen_section(s, req)) for s in req.sections}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    return assemble(results)
```

**Response (200)**
```json
{
  "data": { "summary": "...", "sections": {...}, "metrics": {...} },
  "generated_at": "2026-04-15T00:00:00Z",
  "version": "v1"
}
```

### 4.3 Error Response (통일)

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "LLM call exceeded 300s",
    "request_id": "c0ffee...",
    "details": { "section": "valuation" }
  }
}
```

---

## 5. Resilience & Security Design

### 5.1 Timeout / Retry / Circuit

| Layer | Policy |
|-------|--------|
| Gemini LLM | timeout=300s, retry 2회 (exponential 2s→8s), circuit 5회 실패/60s reset |
| Market data | timeout=15s, retry 3회 |
| News API | timeout=10s, retry 2회 |

```python
# core/resilience.py
class Timeout:
    GEMINI = 300   # ← 30에서 수정
    MARKET = 15
    NEWS = 10
```

### 5.2 Secret Handling

```python
# Before (❌ URL 쿼리 노출)
url = f"{BASE}/models/{model}:generateContent?key={KEY}"

# After (✅ 헤더)
headers = {"x-goog-api-key": settings.gemini_api_key.get_secret_value()}
```

### 5.3 CORS

```python
allow_origins = settings.allowed_origins   # env 로 주입
allow_credentials = True if dev else False  # 운영은 credentials=False
```

### 5.4 Rate Limit (slowapi)

```python
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_min}/minute"])
```

---

## 6. Error Handling

### 6.1 Error Codes

| Code | HTTP | Cause |
|------|------|-------|
| `VALIDATION_ERROR` | 400 | Pydantic validation |
| `AUTH_REQUIRED` | 401 | (추후) |
| `NOT_FOUND` | 404 | 리소스 없음 |
| `RATE_LIMITED` | 429 | slowapi 한도 |
| `LLM_TIMEOUT` | 504 | Gemini 타임아웃 |
| `UPSTREAM_ERROR` | 502 | 외부 API 오류 |
| `INTERNAL_ERROR` | 500 | 처리되지 않은 예외 |

### 6.2 Global Handler

```python
@app.exception_handler(Exception)
async def unhandled(request, exc):
    rid = request.state.request_id
    log.exception("unhandled", request_id=rid)
    return JSONResponse(500, ApiError(code="INTERNAL_ERROR", message="...", request_id=rid).model_dump())
```

---

## 7. Security Considerations

- [x] Pydantic 입력 검증 (XSS/Injection 1차 방어)
- [x] API Key 헤더 전송 + 로그 마스킹
- [x] CORS 허용 도메인 명시
- [x] Rate Limit 기본 60/min, 분석 엔드포인트 10/min
- [x] HTTPS 전제 (리버스 프록시 레이어)
- [x] Request body size limit (1MB)
- [x] 의존성 보안 스캔 (pip-audit, bandit)

---

## 8. Test Plan

### 8.1 Scope

| Type | Target | Tool |
|------|--------|------|
| Unit | services/*, core/resilience | pytest |
| Contract | routers/* (schema 고정) | pytest + jsonschema |
| Integration | LLM mock, E2E /api/llm/report | pytest-asyncio + respx |
| Security | CORS / secret leak | pytest + bandit |

### 8.2 Key Cases

- [ ] LLM 300s 내 정상 응답 / 초과 시 `LLM_TIMEOUT`
- [ ] CORS disallowed origin 거부
- [ ] Rate limit 초과 시 429
- [ ] Gemini 호출 URL에 key 미포함 확인
- [ ] 하드코딩 PM_MCP_ROOT 제거 검증 (env 없으면 기동 실패)
- [ ] 종합 보고서 병렬화 시간 측정 (순차 대비 40%+ 단축)

---

## 9. Clean Architecture

### 9.1 Layers (Python)

| Layer | Responsibility | Location |
|-------|---------------|----------|
| Presentation (IO) | APIRouter, 요청/응답 바인딩 | `api/routers/` |
| Application | Use case orchestration | `api/services/` |
| Domain | 엔티티, 상수, 도메인 규칙 | `api/domain/`, `api/schemas/` |
| Infrastructure | Gemini/MCP tools, HTTP, cache | `mcp_server/tools/`, `core/` |

### 9.2 Dependency Rules

```
routers ──► services ──► domain ◄── infrastructure
                │                       ▲
                └──────── infrastructure┘

금지: tools → routers / services → routers
```

### 9.3 File Import Rules

| From | Allowed | Disallowed |
|------|---------|------------|
| routers | services, schemas | tools 직접 호출 |
| services | tools, core, domain | routers, FastAPI 객체 |
| core | stdlib, settings | 도메인 코드 |
| tools | core(resilience/logging) | routers, services |

### 9.4 Feature Layer Assignment

| Component | Layer | Location |
|-----------|-------|----------|
| `portfolio_router` | Presentation | `api/routers/portfolio.py` |
| `AnalysisService` | Application | `api/services/analysis.py` |
| `AnalysisReport` | Domain | `api/schemas/analysis.py` |
| `gemini_client` | Infrastructure | `mcp_server/tools/llm.py` |

---

## 10. Coding Convention Reference

### 10.1 Naming

| Target | Rule | Example |
|--------|------|---------|
| module | snake_case | `analysis_service.py` |
| class | PascalCase | `AnalysisService` |
| func/var | snake_case | `build_report()` |
| constant | UPPER_SNAKE | `LLM_TIMEOUT_SEC` |
| router file | `<domain>.py` | `portfolio.py` |

### 10.2 Import Order (ruff isort)

```python
# 1. stdlib
import asyncio
from datetime import datetime
# 2. third-party
from fastapi import APIRouter, Depends
# 3. first-party
from api.schemas.analysis import AnalysisRequest
from api.services.analysis import AnalysisService
# 4. relative
from .deps import get_service
```

### 10.3 Env Vars

| Prefix | Purpose | Example |
|--------|---------|---------|
| (plain) | app 설정 | `LLM_TIMEOUT_SEC` |
| `GEMINI_` | LLM 관련 | `GEMINI_API_KEY`, `GEMINI_MODEL` |
| `ALLOWED_` | 보안 허용목록 | `ALLOWED_ORIGINS` |

### 10.4 Applied

| Item | Convention |
|------|-----------|
| Router naming | `<domain>_router` (변수), `<domain>.py` (파일) |
| 에러 처리 | `raise AppError(code=...)` → 전역 핸들러 |
| 로깅 | `log.info("event", key=value)` structlog |
| 병렬화 | `asyncio.gather(..., return_exceptions=True)` |

---

## 11. Implementation Guide

### 11.1 File Structure

```
api/
├── main.py                 # app factory + middleware wiring
├── deps.py
├── routers/
│   ├── portfolio.py
│   ├── theme.py
│   ├── analysis.py
│   ├── news.py
│   ├── llm.py
│   └── health.py
├── services/
│   ├── portfolio.py
│   ├── analysis.py
│   └── llm.py
├── schemas/
│   ├── common.py
│   ├── portfolio.py
│   ├── analysis.py
│   └── llm.py
core/
├── config.py
├── logging.py
├── errors.py
├── resilience.py
└── middleware.py
mcp_server/tools/
├── llm.py                  # 헤더 전송 + retry 적용
└── resilience.py           # Timeout.GEMINI=300
tests/
├── unit/
├── contract/
└── integration/
```

### 11.2 Implementation Order

1. [ ] `core/config.py` (Settings) + `.env.example` 정비 — FR-B05, FR-B17
2. [ ] `core/logging.py`, `core/errors.py`, RequestID 미들웨어 — FR-B06, FR-B12
3. [ ] `mcp_server/tools/resilience.py` Timeout.GEMINI=300 + `llm.py` 헤더 전환 — FR-B01~B03
4. [ ] `api/main.py` app factory + CORS/RateLimit/CORS 미들웨어 — FR-B01, FR-B04
5. [ ] Router 분리 (portfolio → theme → analysis → news → llm → health) — FR-B07
6. [ ] Pydantic schemas 전량 부착 — FR-B08
7. [ ] Service layer 이동 + 섹터 N+1 제거 — FR-B10, FR-B15
8. [ ] LLM 섹션 병렬화(`asyncio.gather`) — FR-B09
9. [ ] 매직넘버 상수화, Circuit 재튜닝, 모델명 정리 — FR-B11, FR-B13, FR-B14
10. [ ] 테스트(unit/contract/integration) 70%+, OpenAPI 태그 보강 — FR-B22, FR-B24
11. [ ] README / `.env.example` / `/health/detail` 마무리 — FR-B18, FR-B19

### 11.3 Parallel Sync with Frontend

| Sync Point | What | When |
|------------|------|------|
| API schema freeze | `openapi.json` 발행 | Phase 1 종료 시 |
| Error code set | `ApiError` 스키마 공유 | Phase 1 |
| Rate limit 정책 | FE 재시도 전략 합의 | Phase 2 시작 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-15 | Plan FR-B01~B24 기반 초안 | Stock Manager Team |
