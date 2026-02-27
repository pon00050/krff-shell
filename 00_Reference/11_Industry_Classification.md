# Industry Classification for Korean Listed Companies

> **Scope:** KSIC Rev. 10 join logic, WICS taxonomy and API patterns, pre-implementation decisions, verified fallback rules.
> **Canonical for:** Industry classification methodology; WICS endpoint behavior; KSIC code source.
> **See also:** `02_Data_Sources.md` (source specs), `18_Research_Findings.md` (empirical findings)

Reference for adding sector/industry data to the pipeline. No code changes are implemented here — this document describes what to build and why.

**Research verification (Feb 2026):** Pre-implementation open questions resolved. Decision gate outcomes:
| Gate | Answer | Impact |
|---|---|---|
| WICS `GetIndexComponets` alive? | Likely YES — stable since 2019, no reported breakage; no live 2025-2026 confirmation (unofficial API) | Keep WICS branch as designed |
| pykrx has 업종분류 function? | NO | Keep custom OTP code in `extract_krx.py` |
| FDR `StockListing` has sector for all 3 markets? | YES — column `"Sector"`, ~8% null rate, known intermittent reliability | FDR is a valid simpler alternative; OTP remains primary |
| FinanceData/KSIC has clean structured file? | YES — `KSIC_10.csv.gz`, `pd.read_csv(url, dtype=str)` works; no Rev. 11 file | Step 4 = one-liner; use Rev. 10 file |
| DART `induty_code` is Rev. 9? | NO — it is **Rev. 10** (KSIC 10th revision, 2017) | Use `KSIC_10.csv.gz`; Rev. 9 warning removed |
| KRX unified taxonomy published? | NOT CONFIRMED — two-call MDCSTAT03901 pattern still required | No architecture change |
| KIND requires browser automation? | NO — plain `requests.post()` works | Simpler scraping implementation |

---

## Section 1 — Five Classification Systems

### 1. KRX Native 업종분류

Operated by 한국거래소. Legacy system with separate sector trees for KOSPI (~22 sectors) and KOSDAQ (~34 sectors). The two trees are not directly comparable — KOSPI and KOSDAQ sector names overlap but cover different scopes (e.g., both have "전기전자" but with different constituent sets). KRX issued an RFP in 2023 to unify the two trees into a single taxonomy; unified classification was being rolled out through 2024–2025.

Available free via two endpoints:
- `data.krx.co.kr` MDCSTAT03901 OTP — daily CSV, ticker + KRX sector name
- `kind.krx.co.kr` 상장법인목록 — full listing including KONEX

Use for: quick sector filter, KOSPI/KOSDAQ coverage. Do not use for cross-market comparisons until the unified taxonomy is confirmed stable.

### 2. GICS (Global Industry Classification Standard)

Proprietary system jointly owned by S&P and MSCI. 11 sectors → 25 industry groups → 74 industries → 163 sub-industries. KRX adopted GICS as the underlying taxonomy for KOSPI 200 sector indices starting in 2018. Paid license required for programmatic use. **Not a viable free data source.** Reference only for understanding how KRX sector indices are constructed.

### 3. KSIC Rev. 11 (한국표준산업분류 제11차 개정)

Statutory classification published by Statistics Korea (통계청). Effective July 2024. 5-level hierarchy:
- 대분류 (Section): 21 codes (A–U), single letter
- 중분류 (Division): 77 codes, 2-digit
- 소분류 (Group): 234 codes, 3-digit
- 세분류 (Class): 501 codes, 4-digit
- 세세분류 (Sub-class): 1,205 codes, 5-digit

DART stores `induty_code` at the 소분류 (3-digit Group) level. KSIC is public domain — full codebook available from the Statistics Korea portal and the FinanceData/KSIC GitHub repository.

Use for: statutory compliance framing, joining to DART company data, cross-referencing SEIBRO and KFTC data.

### 4. WICS (WISEfn Industry Classification Standard)

Published by WISEfn (a FnGuide subsidiary). GICS-like structure adapted for Korean market realities:
- 10 sectors (대분류)
- 25 industry groups (중분류)
- ~70 industries (소분류)

Free JSON API with no authentication required. As of October 2025, WICS supersedes FICS (FnGuide Industry Classification Standard) — FICS endpoints are retired. Do not use FICS.

WICS sector codes:
| Code | Sector |
|---|---|
| G10 | 에너지 |
| G15 | 소재 |
| G20 | 산업재 |
| G25 | 경기관련소비재 |
| G30 | 필수소비재 |
| G35 | 건강관리 |
| G40 | 금융 |
| G45 | IT |
| G50 | 커뮤니케이션서비스 |
| G55 | 유틸리티 |

Coverage: all KOSPI + KOSDAQ companies. No KONEX.

**Reliability note:** `GetIndexComponets` (the typo is intentional — this is the actual deployed endpoint name) is an undocumented internal API discovered via browser DevTools. FnGuide can change or block it without notice. It has been stable since at least 2019 with no schema changes reported, but no live confirmation from 2025–2026 exists in public sources. Add `Referer: https://www.wiseindex.com/` header. Use `time.sleep(1)` between sector calls.

### 5. FICS (FnGuide Industry Classification Standard)

Retired as of late 2025. Superseded by WICS. Do not use FICS endpoints — they are no longer maintained.

---

## Section 2 — Ranked Free Data Sources

Sources ranked by coverage, reliability, and ease of programmatic access.

| Rank | Source | Publisher | Endpoint / Path | Fields | Coverage | Format | Update | Auth |
|---|---|---|---|---|---|---|---|---|
| 1 | KRX 업종분류 현황 | 한국거래소 | `data.krx.co.kr` MDCSTAT03901 OTP | ticker, KRX sector name | KOSPI, KOSDAQ | CSV | Daily | None |
| 2 | KRX KIND 상장법인목록 | 한국거래소 | `kind.krx.co.kr` | ticker, KSIC division name, 상장일, 결산월 | KOSPI + KOSDAQ + **KONEX** | Excel | Daily | None |
| 3 | DART 기업개황 API | 금융감독원 | `GET /api/company.json?corp_code=` | `induty_code` (KSIC 3-digit), exchange, fiscal year end | All DART corps | JSON per call | Per filing | API key |
| 4 | WICS WISEindex API | WISEfn | `wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt=YYYYMMDD&sec_cd=G{xx}` | ticker, WICS sector, industry group, industry | KOSPI + KOSDAQ | JSON | Daily | None |
| 5 | FinanceDataReader | FinanceData | `fdr.StockListing('KRX')` | ticker, name, `Sector` (KRX native sector name, ~8% null rate) | KOSPI + KOSDAQ + KONEX | DataFrame | On call | None |
| 6 | data.go.kr FSC listing | 금융위원회 | data.go.kr FSC endpoint | ticker, ISIN | KOSPI + KOSDAQ | JSON/CSV | Periodic | API key |

**Source 6 note:** FSC listing at data.go.kr provides ISIN↔ticker join only — no industry codes. Use it for ISIN resolution, not sector data.

### Python Code Snippets

**KRX 업종분류 현황 via MDCSTAT03901 OTP:**

```python
import requests
import pandas as pd
from io import StringIO

def fetch_krx_sector(market: str = "STK", trd_dd: str = "") -> pd.DataFrame:
    """
    Fetch KRX sector classification.
    market: 'STK' for KOSPI, 'KSQ' for KOSDAQ
    trd_dd: trading date as 'YYYYMMDD'; leave blank for latest
    Notes:
    - Use http:// not https:// — the OTP flow requires the non-TLS endpoint
    - Referer must point to the sector statistics page or the request will be rejected
    - Response encoding is EUC-KR
    - KOSDAQ calls may need 'segTpCd': 'ALL' to return the full list
    """
    # Step 1: Get OTP token
    otp_url = "http://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd"
    params = {
        "locale": "ko_KR",
        "mktId": market,
        "trdDd": trd_dd,
        "money": "1",
        "csvxls_isNo": "true",   # true = CSV; false = XLS
        "name": "fileDown",
        "url": "dbms/MDC/STAT/standard/MDCSTAT03901",
    }
    if market == "KSQ":
        params["segTpCd"] = "ALL"
    headers = {
        "Referer": "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020506",
        "User-Agent": "Mozilla/5.0",
    }
    otp_resp = requests.post(otp_url, data=params, headers=headers)
    otp_token = otp_resp.text

    # Step 2: Download CSV
    download_url = "http://data.krx.co.kr/comm/fileDn/download_csv/download.cmd"
    csv_resp = requests.post(
        download_url,
        data={"code": otp_token},
        headers=headers,
    )
    csv_resp.encoding = "euc-kr"
    df = pd.read_csv(StringIO(csv_resp.text))
    df["market"] = "KOSPI" if market == "STK" else "KOSDAQ"
    return df
```

**DART batch call for induty_code:**

```python
import opendartreader as odr
import time

def fetch_dart_industry_codes(api_key: str, corp_codes: list[str]) -> dict[str, str]:
    """
    Fetch KSIC industry codes from DART 기업개황.
    Returns {corp_code: induty_code}.
    Rate limit: 20,000 calls/day. ~2,700 KOSDAQ+KOSPI companies fits within quota.
    """
    dart = odr.OpenDartReader(api_key)
    result = {}
    for corp_code in corp_codes:
        try:
            info = dart.company(corp_code)
            if info is not None and "induty_code" in info:
                result[corp_code] = info["induty_code"]
        except Exception:
            pass
        time.sleep(0.05)  # ~20 calls/sec, safely within rate limit
    return result
```

**WICS 10-sector loop:**

```python
import requests
import pandas as pd

WICS_SECTOR_CODES = ["G10", "G15", "G20", "G25", "G30", "G35", "G40", "G45", "G50", "G55"]

def fetch_wics_sectors(date: str) -> pd.DataFrame:
    """
    Fetch WICS sector classification for all constituents.
    date: 'YYYYMMDD' string
    Returns DataFrame with CMP_CD (ticker), CMP_KOR (name), SEC_NM_KOR (sector), IDX_NM_KOR (index name).
    """
    frames = []
    for sec_cd in WICS_SECTOR_CODES:
        url = (
            f"https://www.wiseindex.com/Index/GetIndexComponets"
            f"?ceil_yn=0&dt={date}&sec_cd={sec_cd}"
        )
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if "list" in data:
                df = pd.DataFrame(data["list"])
                df["wics_sector_code"] = sec_cd
                frames.append(df)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
```

---

## Section 3 — Recommended Best Path (4 Steps)

To build a complete master sector table for all KOSPI + KOSDAQ + KONEX companies:

**Step 1 — Base universe with KRX sector**

Two approaches; choose based on reliability requirements:

*Primary (more reliable):*
- KOSPI + KOSDAQ: KRX 업종분류 현황 MDCSTAT03901 (`fetch_krx_sector("STK")` and `fetch_krx_sector("KSQ")`)
- KONEX: KIND 상장법인목록 — accessible via plain `requests.post()` without browser automation (no Selenium needed); direct POST to `http://kind.krx.co.kr/corpgeneral/corpList.do` with `method=download&searchType=13`; response is HTML-encoded `.xls`, parse with `pd.read_html(BytesIO(r.content))[0]`

*Simpler alternative (single call, covers all 3 markets):*
- `fdr.StockListing('KRX')` returns KOSPI + KOSDAQ + KONEX in one call; sector column is named exactly `"Sector"`; ~8% null rate (ETFs, SPACs, preferred shares typically missing); known intermittent reliability issues (HTTP 401) that track library updates — verify before depending on it in production

- Result: ticker + KRX native sector for all listed companies

**Step 2 — KSIC codes from DART**
- Start from `corpCode.xml` (bulk download from DART — all 50,000+ corp_codes with stock_code)
- Filter to listed companies (stock_code is non-empty)
- Batch call `GET /api/company.json?corp_code=` for each → extract `induty_code`
- ~2,700 calls for full KOSPI+KOSDAQ+KONEX coverage; within 20,000/day quota
- Result: corp_code → KSIC 3-digit code

**Step 3 — WICS sector from WISEindex**
- Loop all 10 WICS sector codes with today's date
- Extract CMP_CD (ticker) + sector + industry group + industry
- Result: ticker → WICS 3-level classification
- Note: KONEX companies are not in WICS — use N/A for those

**Step 4 — KSIC codebook for human-readable labels**
- `github.com/FinanceData/KSIC` contains two files: `KSIC_09.csv.gz` (Rev. 9, pre-2017) and `KSIC_10.csv.gz` (Rev. 10, effective July 2017). **No Rev. 11 file exists in the repo** (Rev. 11 became statutory July 2024 but has not been added). Load with:
  ```python
  df = pd.read_csv("https://github.com/FinanceData/KSIC/raw/master/KSIC_10.csv.gz", dtype=str)
  ```
  `dtype=str` is required to preserve leading zeros in classification codes.
- **Version confirmed: DART `induty_code` follows KSIC Rev. 10.** Samsung Electronics (`corp_code=00126380`) returns `induty_code="264"` which is a valid 3-digit 소분류 under Rev. 10 (C26: 전자부품, 컴퓨터, 영상, 음향 및 통신장비 제조업). Join on the 3-digit 소분류 column in `KSIC_10.csv.gz`. There is no evidence that DART has updated to Rev. 11 as of early 2026.
- Result: KSIC code → section/division/group names in Korean

---

## Section 4 — Master Table Schema

Target schema for the enriched `corp_ticker_map` table:

| Column | Source | Type | Example |
|---|---|---|---|
| `ticker` | KRX | str | `005930` |
| `isin` | data.go.kr | str | `KR7005930003` |
| `corp_code` | DART corpCode.xml | str | `00126380` |
| `company_name` | KRX | str | `삼성전자` |
| `market` | KRX | str | `KOSPI` |
| `krx_sector` | KRX 업종분류 | str | `전기전자` |
| `ksic_code` | DART API | str | `261` |
| `ksic_name` | KSIC codebook | str | `전자부품, 컴퓨터, 영상, 음향 및 통신장비 제조업` |
| `wics_sector_code` | WISEindex | str | `G45` |
| `wics_sector` | WISEindex | str | `IT` |
| `wics_industry_group` | WISEindex | str | `반도체와반도체장비` |
| `wics_industry` | WISEindex | str | `반도체및관련장비` |
| `effective_from` | KRX | date | `2020-01-02` |
| `effective_to` | KRX | date | `null` (current) |

**Storage:** Parquet at `01_Data/processed/corp_ticker_map.parquet` — replaces current 6-column table.

---

## Section 5 — Pipeline Integration Notes

These are documentation of required changes — not yet implemented. A follow-on task will implement the code.

### `02_Pipeline/extract_dart.py`
Add `fetch_company_overview(corp_code: str) -> dict` calling `GET /api/company.json`:
- Extract: `corp_name`, `stock_code`, `corp_cls` (KOSPI/KOSDAQ/KONEX), `induty_code`, `est_dt`, `acc_mt`
- Bulk-callable: loop over `corp_codes` from `corpCode.xml`, ~2,700 calls for listed companies only, well within 20,000/day quota
- Store raw responses to `01_Data/raw/dart_company_overview/` as JSON files (one per corp_code)
- **KSIC version confirmed:** `induty_code` reflects KSIC Rev. 10 (10th revision, effective July 2017). Join to `KSIC_10.csv.gz` from `github.com/FinanceData/KSIC` on the 3-digit 소분류 column. No Rev. 11 update from DART detected as of early 2026.

### `02_Pipeline/extract_krx.py`
Add two functions:
- `fetch_sector_classification(market: str) -> pd.DataFrame`: uses the KRX OTP MDCSTAT03901 mechanism shown above; call once for KOSPI, once for KOSDAQ; store to `01_Data/raw/krx_sector_{market}_{date}.csv`
- `fetch_wics_sectors(date: str) -> pd.DataFrame`: loops 10 WICS sector codes as shown above; store to `01_Data/raw/wics_sectors_{date}.parquet`

### `02_Pipeline/transform.py`
In `build_corp_ticker_map()`:
- Join KRX sector CSV on ticker
- Join DART overview data on corp_code → add `induty_code` + KSIC codebook label
- Join WICS data on ticker → add sector/industry group/industry columns
- Handle KONEX companies (no WICS data) with null fill
- Update output schema to 14-column table (see Section 4 above)

### `03_Analysis/beneish_screen.py`
- Add `krx_sector` and `wics_sector` columns to output CSV
- Add sector filter widget to Marimo UI (multiselect on KRX sector values)
- Enable peer-group M-Score percentile calculation within sector

### `03_Analysis/timing_anomalies.py`
- Add sector column to anomaly output
- Enable sector-based filtering in the analysis UI
- CB/BW-concentrated sectors (바이오, 엔터테인먼트, IT, 제약) — use as a prioritization signal

---

## Section 6 — Identifier Notes

### Primary join key by system

| System | Identifier | Format | Notes |
|---|---|---|---|
| DART | `corp_code` | 8-digit str (`00126380`) | Stable across relistings — preferred internal key |
| DART | `stock_code` | 6-digit str (`005930`) | = KRX ticker; present only for listed companies |
| KRX | ticker | 6-digit str (`005930`) | Changes on relisting — always use effective date ranges |
| WICS | `CMP_CD` | 6-digit str | = KRX ticker |
| SEIBRO | 종목코드 | 6-digit str | = KRX ticker |
| data.go.kr | ISIN | 12-char str (`KR7005930003`) | — |

### ISIN to ticker conversion
ISIN format for Korean equities: `KR` + `7` + `{6-digit ticker}` + `{1 check digit}`.
Extract characters at index 3–8 (0-indexed) from the 12-character ISIN to get ticker:
```python
ticker = isin[3:9]  # e.g., "KR7005930003" → "005930"
```
This is a fast local operation — no API call needed.

### Cross-system join path
```
DART corp_code → DART stock_code = KRX ticker = WICS CMP_CD = SEIBRO 종목코드
                                  ↓
                          ISIN chars[3:9] = KRX ticker
```
Always join external systems (KRX, WICS, SEIBRO) via `ticker` (6-digit). The `corp_ticker_map` table with effective date ranges is the canonical bridge between `corp_code` and `ticker`.
