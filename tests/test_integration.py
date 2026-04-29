"""
연동 테스트 - 각 API 연결 상태 확인
Usage: python -m tests.test_integration
"""
import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"


def test_gemini_api():
    """1. Google AI Studio (Gemma 4) 연동"""
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")

    if not api_key:
        print(f"  {SKIP} Gemini API - GEMINI_API_KEY not set")
        return False

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": "Say 'hello' in one word."}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 32},
    }

    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"  {PASS} Gemini API ({model}) - Response: {text[:50]}")
        return True
    except Exception as e:
        print(f"  {FAIL} Gemini API - {e}")
        return False


def test_finnhub_api():
    """2. Finnhub API 연동"""
    key = os.getenv("FINNHUB_API_KEY", "")

    if not key:
        print(f"  {SKIP} Finnhub API - FINNHUB_API_KEY not set")
        return False

    try:
        resp = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={key}",
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        price = data.get("c", 0)
        print(f"  {PASS} Finnhub API - AAPL current: ${price}")
        return True
    except Exception as e:
        print(f"  {FAIL} Finnhub API - {e}")
        return False


def test_alpha_vantage_api():
    """3. Alpha Vantage API 연동"""
    key = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    if not key:
        print(f"  {SKIP} Alpha Vantage API - ALPHA_VANTAGE_API_KEY not set")
        return False

    try:
        resp = requests.get(
            f"https://www.alphavantage.co/query?function=RSI&symbol=AAPL&interval=daily&time_period=14&series_type=close&apikey={key}",
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        if "Technical Analysis: RSI" in data:
            latest = list(data["Technical Analysis: RSI"].values())[0]
            print(f"  {PASS} Alpha Vantage API - AAPL RSI: {latest['RSI']}")
            return True
        elif "Note" in data:
            print(f"  {FAIL} Alpha Vantage API - Rate limit reached")
            return False
        else:
            print(f"  {FAIL} Alpha Vantage API - Unexpected response: {list(data.keys())}")
            return False
    except Exception as e:
        print(f"  {FAIL} Alpha Vantage API - {e}")
        return False


def test_sec_edgar():
    """4. SEC EDGAR 연동"""
    ua = os.getenv("SEC_EDGAR_USER_AGENT", "")

    if not ua:
        print(f"  {SKIP} SEC EDGAR - SEC_EDGAR_USER_AGENT not set")
        return False

    try:
        headers = {"User-Agent": ua}
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index?q=%22AAPL%22&dateRange=custom&startdt=2026-01-01&enddt=2026-04-13&forms=8-K",
            headers=headers, timeout=15
        )
        # SEC EDGAR returns 200 even for simple queries
        if resp.status_code == 200:
            print(f"  {PASS} SEC EDGAR - Connected (UA: {ua[:30]}...)")
            return True
        else:
            print(f"  {FAIL} SEC EDGAR - HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"  {FAIL} SEC EDGAR - {e}")
        return False


def test_google_news_rss():
    """5. Google News RSS 연동"""
    try:
        import feedparser
        feed = feedparser.parse(
            "https://news.google.com/rss/search?q=AAPL+stock&hl=en-US&gl=US&ceid=US:en",
            request_headers={"User-Agent": "PM-MCP/1.0"}
        )
        count = len(feed.entries)
        if count > 0:
            title = feed.entries[0].title[:60]
            print(f"  {PASS} Google News RSS - {count} articles (latest: {title}...)")
            return True
        else:
            print(f"  {FAIL} Google News RSS - No entries returned")
            return False
    except Exception as e:
        print(f"  {FAIL} Google News RSS - {e}")
        return False


def test_yfinance():
    """6. yfinance 연동"""
    try:
        import yfinance as yf
        ticker = yf.Ticker("AAPL")
        info = ticker.fast_info
        price = info.last_price
        print(f"  {PASS} yfinance - AAPL: ${price:.2f}")
        return True
    except Exception as e:
        print(f"  {FAIL} yfinance - {e}")
        return False


if __name__ == "__main__":
    print("=" * 55)
    print("  Stock Manager - Integration Test")
    print("=" * 55)
    print()

    tests = [
        ("Gemini API (Gemma 4)", test_gemini_api),
        ("Finnhub API", test_finnhub_api),
        ("Alpha Vantage API", test_alpha_vantage_api),
        ("SEC EDGAR", test_sec_edgar),
        ("Google News RSS", test_google_news_rss),
        ("yfinance", test_yfinance),
    ]

    results = []
    for name, func in tests:
        print(f"[{name}]")
        results.append(func())
        print()

    print("=" * 55)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"  Result: {passed}/{total} passed")
    print("=" * 55)
