"""Unit tests for KR market integration (FR-K01/K02/K14)."""
from __future__ import annotations

import pytest

from mcp_server.tools.yf_utils import detect_market
from mcp_server.tools.kr_themes import (
    list_themes,
    lookup_theme_for_ticker,
    propose_tickers_kr,
)


# ---- detect_market (FR-K01) -------------------------------------------------

@pytest.mark.parametrize("ticker,expected", [
    ("005930", "KR"),
    ("005930.KS", "KR"),
    ("247540.KQ", "KR"),
    ("005930.ks", "KR"),          # case-insensitive
    ("  005930 ", "KR"),          # whitespace tolerance
    ("AAPL", "US"),
    ("TSLA", "US"),
    ("BRK.A", "US"),
    ("MSFT.US", "US"),            # dotted non-KR suffix → US default
    ("", "US"),                   # empty → US default
    ("12345", "US"),              # 5 digits — not a valid KR code
    ("1234567", "US"),            # 7 digits — not a valid KR code
])
def test_detect_market(ticker, expected):
    assert detect_market(ticker) == expected


# ---- KR themes (FR-K14) -----------------------------------------------------

def test_list_themes_non_empty():
    themes = list_themes()
    assert len(themes) >= 10
    assert "2차전지" in themes
    assert "AI반도체" in themes


def test_propose_tickers_kr_known():
    tickers = propose_tickers_kr("2차전지")
    assert isinstance(tickers, list)
    assert len(tickers) >= 3
    # Samsung SDI code
    assert "006400" in tickers


def test_propose_tickers_kr_whitespace_tolerant():
    """ 'AI 반도체' (공백 포함) 도 'AI반도체' 로 매칭돼야 한다."""
    assert propose_tickers_kr("AI 반도체") == propose_tickers_kr("AI반도체")


def test_propose_tickers_kr_unknown_returns_empty():
    assert propose_tickers_kr("존재하지-않는-테마") == []


def test_lookup_theme_for_ticker_finds_membership():
    themes = lookup_theme_for_ticker("005930")  # Samsung Electronics
    assert "AI반도체" in themes


def test_lookup_theme_for_ticker_handles_suffix():
    """'.KS' 붙은 티커도 동일하게 매칭돼야 한다."""
    a = lookup_theme_for_ticker("005930")
    b = lookup_theme_for_ticker("005930.KS")
    assert a == b


def test_lookup_theme_for_ticker_bad_input_is_empty():
    assert lookup_theme_for_ticker("AAPL") == []
    assert lookup_theme_for_ticker("") == []


# ---- Korean name → ticker resolver (FR-K01 확장) ----

def test_resolve_korean_ticker_seed_hits():
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    assert resolve_korean_ticker("삼성전자") == "005930"
    assert resolve_korean_ticker("LG에너지솔루션") == "373220"
    assert resolve_korean_ticker("에코프로") == "086520"
    assert resolve_korean_ticker("한미반도체") == "042700"


def test_resolve_korean_ticker_whitespace_tolerant():
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    assert resolve_korean_ticker("  삼성전자 ") == "005930"
    assert resolve_korean_ticker("삼성 전자") == "005930"


def test_resolve_korean_ticker_passthrough_for_codes_and_us():
    """이미 티커 형태면 그대로 반환해야 한다 (멱등)."""
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    assert resolve_korean_ticker("005930") == "005930"
    assert resolve_korean_ticker("005930.KS") == "005930.KS"
    assert resolve_korean_ticker("AAPL") == "AAPL"
    assert resolve_korean_ticker("BRK.A") == "BRK.A"


def test_resolve_korean_ticker_partial_match():
    """'삼성' 같이 prefix 만 맞아도 best-effort 매칭."""
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    # "삼성전자", "삼성바이오로직스", "삼성SDI" 중 하나로 매칭되어야 한다
    result = resolve_korean_ticker("삼성")
    assert result in ("005930", "207940", "006400", "028260")


def test_resolve_korean_ticker_unknown_returns_input():
    from mcp_server.tools.kr_ticker_resolver import resolve_korean_ticker
    # 시드/index 에 없는 임의 한글 → 입력 그대로
    assert resolve_korean_ticker("완전임의의비상장기업XYZ") == "완전임의의비상장기업XYZ"


def test_detect_market_on_korean_name():
    """한글 이름은 KR 로 분류돼야 한다 (resolver 타기 전 단계)."""
    from mcp_server.tools.yf_utils import detect_market
    assert detect_market("삼성전자") == "KR"
    assert detect_market("SK하이닉스") == "KR"
    assert detect_market("에코프로비엠") == "KR"


# ---- KOSPI vs KOSDAQ suffix lookup (kr_market_lookup) ----

def test_kr_market_lookup_seed_kosdaq():
    """Seed dict 에 들어 있는 코드는 ``.KQ`` 로 분류돼야 한다 (network 호출 X)."""
    from mcp_server.tools.kr_market_lookup import market_suffix, is_kosdaq, kr_yfinance_symbol
    assert market_suffix("247540") == "KQ"        # 에코프로BM
    assert market_suffix("086520") == "KQ"        # 에코프로
    assert market_suffix("042700") == "KQ"        # 한미반도체
    assert is_kosdaq("058470") is True             # 리노공업
    assert kr_yfinance_symbol("247540") == "247540.KQ"


def test_kr_market_lookup_invalid_input_defaults_ks():
    """6자리 숫자가 아닌 입력은 .KS 기본 (passthrough 가깝게)."""
    from mcp_server.tools.kr_market_lookup import market_suffix
    assert market_suffix("AAPL") == "KS"
    assert market_suffix("") == "KS"
    assert market_suffix("12345") == "KS"


def test_normalize_ticker_uses_kosdaq_suffix():
    """normalize_ticker_multi_market 이 seed KOSDAQ 코드는 .KQ 를 붙여야 한다."""
    from mcp_server.tools.yf_utils import normalize_ticker_multi_market
    assert normalize_ticker_multi_market("247540", "KR") == "247540.KQ"
    assert normalize_ticker_multi_market("086520", "KR") == "086520.KQ"
    # KOSPI 코드는 .KS
    assert normalize_ticker_multi_market("005930", "KR") == "005930.KS"
    assert normalize_ticker_multi_market("373220", "KR") == "373220.KS"


# ---- Reverse lookup: code → name (FR-K01 expansion) ----

def test_code_to_name_seed():
    from mcp_server.tools.kr_ticker_resolver import code_to_name
    assert code_to_name("005930") == "삼성전자"
    assert code_to_name("373220") == "LG에너지솔루션"
    assert code_to_name("247540") == "에코프로비엠"
    assert code_to_name("042700") == "한미반도체"


def test_code_to_name_strips_suffix():
    """``.KS`` / ``.KQ`` suffixed inputs should still resolve."""
    from mcp_server.tools.kr_ticker_resolver import code_to_name
    assert code_to_name("005930.KS") == "삼성전자"
    assert code_to_name("247540.KQ") == "에코프로비엠"


def test_code_to_name_unknown_returns_none():
    from mcp_server.tools.kr_ticker_resolver import code_to_name
    assert code_to_name("AAPL") is None
    assert code_to_name("999999") is None
    assert code_to_name("") is None


def test_label_kr_ticker_format():
    """``label_kr_ticker`` should produce ``"name (code)"`` for known codes
    and bare code otherwise."""
    from mcp_server.tools.kr_ticker_resolver import label_kr_ticker
    assert label_kr_ticker("005930") == "삼성전자 (005930)"
    assert label_kr_ticker("247540") == "에코프로비엠 (247540)"
    assert label_kr_ticker("999999") == "999999"


def test_resolve_then_code_to_name_roundtrip():
    """한글 → 코드 → 한글 round-trip."""
    from mcp_server.tools.kr_ticker_resolver import code_to_name, resolve_korean_ticker
    for q in ["삼성전자", "SK하이닉스", "에코프로비엠", "한미반도체"]:
        code = resolve_korean_ticker(q)
        assert code.isdigit() and len(code) == 6
        assert code_to_name(code) == q
