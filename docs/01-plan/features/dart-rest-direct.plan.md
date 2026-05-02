# Plan — DART REST Direct Integration

**Status**: Pending (deferred to its own session)
**Origin**: Live HF Space probe on 2026-05-02 confirmed `/api/diag/dart`
returns HTTP 000 after 60 s for every KR ticker. The `OpenDartReader`
library that backs `mcp_server/tools/dart.py` is unusable from the
HF Spaces cluster — it downloads a ~10 MB `corp_code` mapping then
fans out into several follow-up RPCs, and the cluster IP cannot
complete that handshake within any reasonable per-request budget
(45 s timeout still misses).

Until this lands, the Stock Analyzer `Financial Analysis` card on KR
tickers shows the **5 KIS valuation** fields only (PER / PBR / EPS /
BPS / 시가총액). Deep fundamentals (ROE / ROA / Operating Margin /
Net Margin / Debt-to-Equity / Asset Turnover / Revenue & EPS Growth)
remain blank.

---

## Goal

Replace `OpenDartReader.finstate_all()` with a thin direct-REST
client that hits `https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json`
in a single round-trip per ticker, using a pre-baked `corp_code`
lookup table so we never pay the ~10 MB cold-start cost on the cluster.

**Success criteria**: A first cold-cache call to
`/api/stock/factor-interpretation?ticker=005930` on the deployed HF
Space returns ≥ 9 of 20 financial factors (ROE/ROA/Op_Margin/Net_Margin/
Debt_to_Equity/Asset_Turnover/Revenue_Growth/EPS_Growth + the existing
KIS valuation 5) within **5 seconds**.

---

## Approach

### Phase 1 — Static `corp_code` table

`OpenDartReader` is slow because it pulls every KRX issuer's mapping
from `corpCode.xml` on first call. We don't need every issuer — KOSPI
+ KOSDAQ common stock plus a curated list of REITs/ETNs is enough for
the demo.

- Pre-fetch the full `corpCode.xml` (~10 MB) **once on a developer
  workstation** (not the cluster) using
  `OpenDartReader('KEY').list_dart_codes()`.
- Filter to `stock_code IS NOT NULL` (~3,000 rows).
- Serialize to `mcp_server/tools/data/dart_corp_codes.json`
  (~150 KB after pruning to `{stock_code, corp_code, corp_name}`).
- Bundle in the repo so the container never needs to call DART for the
  mapping.

### Phase 2 — Thin REST client

New file `mcp_server/tools/dart_rest.py`:

```python
def get_financials_rest(ticker, year=None):
    corp_code = _STATIC_LOOKUP.get(ticker)
    if not corp_code: return {}
    resp = requests.get(
        "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json",
        params={
            "crtfc_key": KEY, "corp_code": corp_code,
            "bsns_year": year or _last_filed_year(),
            "reprt_code": "11011",  # 사업보고서
            "fs_div": "CFS",         # 연결재무제표
        },
        timeout=10,
    )
    # parse `list[]` → ratios identical to current dart.py
```

- One HTTP call per ticker, predictable 1-3 s response.
- Same ratio-extraction logic as current `dart.py::get_financials`,
  reused unchanged.

### Phase 3 — Wire into `financial_factors._dart_financials`

- Replace the `OpenDartReader` call with `get_financials_rest`.
- Drop the 45 s `ThreadPoolExecutor` timeout — REST call has its own
  10 s `requests` timeout and is fast enough not to need a worker.
- Keep the 24h cache + short failure-sentinel as-is.

### Phase 4 — Verify

- `/api/diag/dart?ticker=005930` returns ≥ 6 ratios in < 5 s.
- `/api/stock/factor-interpretation?ticker=005930` cold call returns
  10+ non-null factors (5 KIS + 6+ DART) in < 6 s.
- 005930 / 373220 / 035720 / 207940 spot-checked for sane numbers
  (ROE ~10–15 %, Op_Margin ~5–25 %, Debt_to_Equity ~0.05–1.0).

---

## Out of scope for this cycle

- KOSDAQ small-cap or KRX special listings (REIT/ETN/A-prefix codes
  like `0001A0`) — DART doesn't carry standard filings for these and
  they will continue to show only the KIS valuation 5.
- Quarterly fundamentals — annual `사업보고서 (11011)` is enough for
  the chart panel; quarterly drift can be a separate enhancement.
- Frontend changes — the existing `Financial Analysis` card already
  renders any field-key the backend returns, so no UI work needed.

---

## Estimated effort

~3 hours, broken down:

| Step | Time |
|---|---|
| Pre-fetch + prune `corp_code` table | 30 min |
| `dart_rest.py` (HTTP client + parser) | 60 min |
| Wire into `financial_factors`, remove OpenDartReader path | 30 min |
| Local tests (6 sample tickers) | 30 min |
| Push, HF rebuild, live verification | 30 min |

---

## Dependencies

- Same `DART_API_KEY` (already set as HF Space Secret).
- No new libraries (`requests` already in `requirements.txt`).
- Existing `_dart_financials` cache + sentinel logic stays.
