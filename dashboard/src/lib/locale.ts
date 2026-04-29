/**
 * Locale-aware formatters for price / percent / compact-number fields.
 *
 * Added as part of the Korean market integration so every KR-specific
 * price can render in ``₩1,234,500`` (no decimals) while US prices stay
 * as ``$123.45``. The goal is one single helper per concern so we never
 * sprinkle ``new Intl.NumberFormat(...)`` calls across page components.
 */

export type Market = "US" | "KR";

export function formatPrice(value: number, market: Market = "US"): string {
  if (!Number.isFinite(value)) return "—";
  if (market === "KR") {
    return new Intl.NumberFormat("ko-KR", {
      style: "currency",
      currency: "KRW",
      maximumFractionDigits: 0,
    }).format(value);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number, market: Market = "US", digits = 0): string {
  if (!Number.isFinite(value)) return "—";
  const locale = market === "KR" ? "ko-KR" : "en-US";
  return new Intl.NumberFormat(locale, { maximumFractionDigits: digits }).format(value);
}

export function formatPercent(value: number, digits = 2): string {
  if (!Number.isFinite(value)) return "—";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

/** Compact notation (1.2K / 3.4M / 1.2B). Useful for volume columns. */
export function formatCompact(value: number, market: Market = "US"): string {
  if (!Number.isFinite(value)) return "—";
  const locale = market === "KR" ? "ko-KR" : "en-US";
  return new Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

/**
 * Format a Korean ticker as ``"한글명 (006400)"`` when the name is known,
 * otherwise just ``"006400"``. Use this anywhere a KR ticker shows up
 * in the dashboard so the surface stays consistent.
 *
 * The frontend never *resolves* a name — it always trusts ``name_kr``
 * from the API. Pass an empty / undefined ``name`` for US tickers and
 * the helper returns the bare ticker, which is what we want.
 */
export function formatKrTickerLabel(
  ticker: string | null | undefined,
  name?: string | null,
): string {
  const t = String(ticker ?? "").trim();
  if (!t) return "";
  const n = name ? String(name).trim() : "";
  return n ? `${n} (${t})` : t;
}

/** Heuristic mirror of the backend's ``detect_market`` so the UI can
 *  pick a locale before any network round-trip.
 *
 *  Korean company names (Hangul) also resolve to KR — the backend's
 *  ``resolve_korean_ticker`` will then turn ``"삼성전자"`` into
 *  ``"005930"`` so the rest of the page can reuse the canonical code. */
export function detectMarketFromTicker(ticker: string): Market {
  const raw = (ticker || "").trim();
  // Hangul check first: ``"삼성전자"`` must be classified as KR even
  // though it isn't a digit string and uppercasing is a no-op for CJK.
  if (/[가-힣]/.test(raw)) return "KR";
  const t = raw.toUpperCase();
  if (t.endsWith(".KS") || t.endsWith(".KQ")) return "KR";
  if (/^\d{6}$/.test(t)) return "KR";
  return "US";
}
