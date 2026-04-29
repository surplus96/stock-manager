---
template: plan
version: 1.2
feature: backend-quality-upgrade
date: 2026-04-15
author: Stock Manager Team
project: Stock Manager (adoring-swartz)
status: Draft
---

# backend-quality-upgrade Planning Document

> **Summary**: Stock Manager 백엔드(FastAPI + MCP Tools)의 보안, 안정성, 유지보수성, 성능을 전반적으로 업그레이드하여 프로덕션 준비도를 85 → 95+로 끌어올린다.
>
> **Project**: Stock Manager
> **Version**: 1.0 → 1.1
> **Author**: Stock Manager Team
> **Date**: 2026-04-15
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

구현된 Stock Manager 서비스의 백엔드 품질을 체계적으로 끌어올린다. code-analyzer 점검 결과 도출된 **24개 이슈 (High 6, Medium 10, Low 8)** 를 우선순위별로 해소하여 다음을 달성한다.

- 보안 취약점 제거 (CORS, API Key 노출, Rate limit 부재)
- 안정성 강화 (LLM timeout, retry 정책, 예외 처리 표준화)
- 유지보수성 향상 (단일 파일 → 라우터 분리, Pydantic 모델, Service Layer)
- 성능 최적화 (LLM 보고서 구간 병렬화, N+1 제거)

### 1.2 Background

code-analyzer 점검 결과(backend) 주요 Critical 이슈:
- `api/server.py:29-35` CORS `allow_origins=["*"]` + `allow_credentials=True` 조합
- `mcp_server/tools/llm.py:19` Gemini API Key가 URL 쿼리스트링으로 노출
- `mcp_server/tools/resilience.py:35` Gemini timeout=30s (사용자 의도 300s)
- `api/server.py` 921 라인에 23개 엔드포인트 단일 파일, bare except 8+, 매직 넘버 다수

### 1.3 Related Documents

- 기획서: `docs/기획서_투자대시보드.md`
- 관련 병렬 Feature: `frontend-quality-upgrade`
- Skills: `Skills.md`

---

## 2. Scope

### 2.1 In Scope

- [ ] 보안: CORS 허용 도메인 명시, Gemini API Key 헤더 전환, Rate Limit(slowapi) 적용
- [ ] 안정성: LLM timeout 300s, retry/backoff 데코레이터 적용, Circuit Breaker 임계치 재조정
- [ ] 구조: `api/server.py` → `api/routers/*.py` 분리 (portfolio, theme, analysis, news, llm)
- [ ] 타입: Pydantic 요청/응답 모델 도입, OpenAPI 스키마 자동 생성
- [ ] 예외: 공통 에러 핸들러, bare except 제거, 구조적 로깅(structlog) 적용
- [ ] 성능: LLM 종합 보고서의 섹션별 `asyncio.gather` 병렬화, 섹터 Fallback N+1 제거
- [ ] 구성: 하드코딩된 `PM_MCP_ROOT` → 환경변수/설정 파일
- [ ] 테스트: 핵심 엔드포인트 pytest 커버리지 70%+, Contract test 추가

### 2.2 Out of Scope

- 프론트엔드 리팩토링 (별도 feature: `frontend-quality-upgrade`)
- 신규 기능 추가 (개선 업데이트에 한정)
- DB 도입 / 인증 시스템 신규 구축 (추후 로드맵)

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-B01 | CORS `allow_origins`를 허용 도메인 리스트로 제한 | High | Pending |
| FR-B02 | Gemini API Key를 `x-goog-api-key` 헤더로 전송 | High | Pending |
| FR-B03 | LLM 호출 timeout을 300s로 수정하고 retry_with_backoff 적용 | High | Pending |
| FR-B04 | FastAPI Rate Limit (slowapi) - 분당 60회/IP 기본 | High | Pending |
| FR-B05 | `PM_MCP_ROOT` 하드코딩 제거 → 환경변수 기반 설정 | High | Pending |
| FR-B06 | 전역 예외 핸들러 + bare except 8곳 이상 제거 | High | Pending |
| FR-B07 | `api/server.py` → 5개 APIRouter 모듈로 분리 | Medium | Pending |
| FR-B08 | 모든 엔드포인트에 Pydantic request/response 모델 부착 | Medium | Pending |
| FR-B09 | LLM 종합 보고서 섹션 병렬 생성 (`asyncio.gather`) | Medium | Pending |
| FR-B10 | 섹터 Fallback N+1 제거(배치 fetch) | Medium | Pending |
| FR-B11 | 매직 넘버 → `constants.py` 상수화 | Medium | Pending |
| FR-B12 | structlog 기반 구조적 로깅 통일 | Medium | Pending |
| FR-B13 | Circuit Breaker 임계치 재튜닝 (failure_threshold 3→5, reset 60s) | Medium | Pending |
| FR-B14 | `GEMMA_MODEL` / `GEMINI_MODEL` 네이밍 정리 | Medium | Pending |
| FR-B15 | Service Layer 분리 (routers → services → tools) | Medium | Pending |
| FR-B16 | 응답 스키마 버전 필드 추가 (API versioning 준비) | Medium | Pending |
| FR-B17 | `.env.example` 정비 (누락 변수 전량 반영) | Low | Pending |
| FR-B18 | README의 백엔드 실행 가이드 업데이트 | Low | Pending |
| FR-B19 | 헬스체크 `/health` 엔드포인트 Detail 모드 | Low | Pending |
| FR-B20 | 중복 util 함수 통합 | Low | Pending |
| FR-B21 | Dead code 제거 (주석/미사용 import) | Low | Pending |
| FR-B22 | OpenAPI 태그/설명 보강 | Low | Pending |
| FR-B23 | 타임존 일관성(UTC) 검증 | Low | Pending |
| FR-B24 | pytest 커버리지 70%+ 달성 | Low | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|-------------------|
| Security | CORS 허용 도메인 명시, Secrets 헤더 전송, Rate Limit 적용 | 수동 점검 + OWASP ZAP |
| Reliability | LLM 호출 성공률 ≥ 98% (300s timeout 기준) | Prometheus/로그 |
| Performance | 종합 보고서 생성 응답 p95 < 12s (기존 20s+) | 응답시간 로깅 |
| Maintainability | 파일당 LoC ≤ 400, 순환복잡도 ≤ 10 | radon, flake8 |
| Observability | 모든 에러에 request_id + context 포함 | 로그 포맷 점검 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] High 우선순위 6개 이슈 100% 해소
- [ ] Medium 이슈 80%+ 해소
- [ ] `api/server.py` 단일 파일 해체 완료
- [ ] Pydantic 모델 도입된 엔드포인트 100%
- [ ] pytest 통과 + 커버리지 70%+
- [ ] code-analyzer 재점검 match rate ≥ 90%

### 4.2 Quality Criteria

- [ ] `ruff`/`flake8` 에러 0
- [ ] `mypy` 주요 경로 통과
- [ ] 보안 스캔 (bandit) High 0건
- [ ] 주요 엔드포인트 응답 p95 기존 대비 동등 이상

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Router 분리 중 회귀 버그 | High | Medium | 단계별 PR + contract test 선작성 |
| LLM timeout 증가에 따른 FE 체감 지연 | Medium | Medium | FE에서 streaming/스켈레톤 병행(FE feature) |
| Rate limit이 개발 편의성 저하 | Low | Medium | dev 환경은 완화된 정책 |
| Pydantic 도입 시 기존 응답 포맷 변경 | High | Low | 스키마 스냅샷 테스트, v1 유지 후 v2 병행 |

---

## 6. Architecture Considerations

### 6.1 Project Level Selection

| Level | Characteristics | Recommended For | Selected |
|-------|-----------------|-----------------|:--------:|
| Starter | 단순 | 정적 사이트 | ☐ |
| **Dynamic** | Feature 모듈 + Service Layer | Web + Backend | ☑ |
| Enterprise | 레이어 엄격 분리 | 대규모 시스템 | ☐ |

### 6.2 Key Architectural Decisions

| Decision | Options | Selected | Rationale |
|----------|---------|----------|-----------|
| Router 구조 | 단일 / APIRouter 분리 | **APIRouter 분리** | 921라인 단일 파일 유지보수 한계 |
| 스키마 관리 | dict / Pydantic / attrs | **Pydantic v2** | FastAPI 친화 + OpenAPI 자동 |
| 예외 처리 | try/except 분산 / 전역 핸들러 | **전역 핸들러** | bare except 제거 + 일관성 |
| 로깅 | print / logging / structlog | **structlog** | 구조적 JSON 로그 |
| Rate Limit | 없음 / slowapi / nginx | **slowapi** | 앱 레벨 세밀 제어 |
| 병렬화 | 순차 / asyncio.gather | **asyncio.gather** | LLM 섹션 독립성 높음 |

### 6.3 Clean Architecture Approach

```
api/
  main.py              (app 팩토리)
  routers/
    portfolio.py
    theme.py
    analysis.py
    news.py
    llm.py
  schemas/             (Pydantic)
  services/            (비즈니스 로직)
  deps.py              (DI)
mcp_server/tools/      (도메인 도구, 변경 최소)
core/
  config.py            (env)
  logging.py           (structlog)
  errors.py            (exc handler)
```

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `CLAUDE.md` 존재 (bio-simulagent 루트)
- [ ] `docs/01-plan/conventions.md` 미존재
- [ ] `CONVENTIONS.md` 미존재
- [ ] `ruff.toml` / `.flake8` 점검 필요
- [x] `pyproject.toml` 존재

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| Naming (router/service) | missing | `*_router.py` / `*_service.py` | High |
| 폴더 구조 | 부분 존재 | routers/schemas/services | High |
| Import order | missing | isort/ruff 규칙 | Medium |
| Env vars | 일부 존재 | `.env.example` 전량 | High |
| Error handling | 분산 | `core/errors.py` 중앙화 | High |

### 7.3 Environment Variables Needed

| Variable | Purpose | Scope | To Be Created |
|----------|---------|-------|:-------------:|
| `PM_MCP_ROOT` | MCP 루트 경로 | Server | ☑ |
| `GEMINI_API_KEY` | LLM Key | Server | 기존 |
| `GEMINI_MODEL` | 모델명 정규화 | Server | ☑ |
| `LLM_TIMEOUT_SEC` | LLM 타임아웃 | Server | ☑ |
| `RATE_LIMIT_PER_MIN` | Rate limit | Server | ☑ |
| `ALLOWED_ORIGINS` | CORS 허용 origin | Server | ☑ |

---

## 8. Next Steps

1. [ ] `/pdca design backend-quality-upgrade` 로 Design 문서 작성
2. [ ] 병렬 Feature `frontend-quality-upgrade` 와 일정 동기화
3. [ ] Phase 1(1주) Critical 6개부터 PR 분할 착수

### 8.1 Roadmap Phases

| Phase | 기간 | 포함 이슈 |
|-------|------|-----------|
| Phase 1 | 1주 | FR-B01~B06 (Critical 6) |
| Phase 2 | 2주 | FR-B07~B16 (구조/성능) |
| Phase 3 | 2-3주 | FR-B17~B24 (품질/문서/테스트) |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-04-15 | code-analyzer 24개 이슈 기반 초안 | Stock Manager Team |
