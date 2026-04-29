# Third-Party Notices

This project depends on the following open-source software. All listed
licenses are permissive and compatible with this project's MIT license.
Full license texts are available in each package's repository.

## Frontend (`dashboard/`)

| Package | License | Source |
|---|---|---|
| Next.js | MIT | https://github.com/vercel/next.js |
| React, React DOM | MIT | https://github.com/facebook/react |
| lucide-react | ISC | https://github.com/lucide-icons/lucide |
| recharts | MIT | https://github.com/recharts/recharts |
| framer-motion | MIT | https://github.com/framer/motion |
| react-markdown | MIT | https://github.com/remarkjs/react-markdown |
| remark-gfm | MIT | https://github.com/remarkjs/remark-gfm |
| clsx | MIT | https://github.com/lukeed/clsx |
| Tailwind CSS | MIT | https://github.com/tailwindlabs/tailwindcss |
| Source Serif 4 (font) | OFL-1.1 | https://fonts.google.com/specimen/Source+Serif+4 |

## Backend (`api/`, `mcp_server/`, `core/`)

| Package | License | Source |
|---|---|---|
| FastAPI | MIT | https://github.com/tiangolo/fastapi |
| Uvicorn | BSD-3-Clause | https://github.com/encode/uvicorn |
| Pydantic | MIT | https://github.com/pydantic/pydantic |
| pandas | BSD-3-Clause | https://github.com/pandas-dev/pandas |
| NumPy | BSD-3-Clause | https://github.com/numpy/numpy |
| yfinance | Apache-2.0 | https://github.com/ranaroussi/yfinance |
| pykrx | MIT | https://github.com/sharebook-kr/pykrx |
| FinanceDataReader | Apache-2.0 | https://github.com/FinanceData/FinanceDataReader |
| requests | Apache-2.0 | https://github.com/psf/requests |
| APScheduler | MIT | https://github.com/agronholm/apscheduler |
| diskcache | Apache-2.0 | https://github.com/grantjenks/python-diskcache |
| jinja2 | BSD-3-Clause | https://github.com/pallets/jinja |
| python-dateutil | Apache-2.0 / BSD-3-Clause | https://github.com/dateutil/dateutil |
| tenacity | Apache-2.0 | https://github.com/jd/tenacity |

## External APIs

This project calls the following external services. API credentials are
held only in server-side environment variables; reviewers do **not** need
to supply their own keys to use the deployed demo.

| Service | Use | Terms |
|---|---|---|
| Google Gemini API | LLM-backed chat & report generation | https://ai.google.dev/terms |
| DART Open API (KR 금융감독원) | Korean issuer filings | https://opendart.fss.or.kr |
| Yahoo Finance (via `yfinance`) | Price/fundamentals (US + KR) | Yahoo ToS — use is for non-commercial research |
| KRX (via `pykrx` / `FinanceDataReader`) | Korean OHLCV | https://data.krx.co.kr |
| Finnhub (optional) | Earnings/insider data | https://finnhub.io/legal |
| SEC EDGAR (optional) | US filings | https://www.sec.gov/os/accessing-edgar-data |

## Assets

- All charts and report images shipped under `obsidian_vault/Images/` and
  `data/charts/` are generated programmatically from public market data
  by this project's own code (no third-party copyrighted artwork).
- No copyrighted icons, illustrations, or stock photography are bundled
  in the repository. Iconography is rendered at runtime from
  `lucide-react` (ISC).
