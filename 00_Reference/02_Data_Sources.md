# Verified Public Data Sources

> **Scope:** All four data sources (OpenDART, KRX, SEIBRO, KFTC) — endpoints, rate limits, library selection, and access patterns. All confirmed February 2026.
> **Canonical for:** Data source specs; rate limits; library choices; API endpoint URLs.
> **See also:** `18_Research_Findings.md` (empirical findings from API testing), `11_Industry_Classification.md` (sector data specifically)

All sources confirmed via web research, February 2026. All are free and publicly accessible.

---

## 1. OpenDART API

**URL:** https://opendart.fss.or.kr
**English portal:** https://engopendart.fss.or.kr
**Operator:** 금융감독원 (Financial Supervisory Service)

### Access
- Free registration required (individual or institutional tier)
- Issues an API authentication key upon registration
- Rate limit: approximately 1,000 requests/minute; institutional tier has higher quota

### What's Available via API (structured data, JSON/XML)

| Category | Contents |
|---|---|
| Disclosure listings | All filings by company, date, type |
| Company overview (기업개황) | Registration number, listed exchange, `induty_code` (KSIC 3-digit 소분류 code), fiscal year end. Endpoint: `GET /api/company.json?crtfc_key=...&corp_code=...`. Requires one call per company; ~2,700 calls for full KOSPI+KOSDAQ coverage, within the 20,000 req/day quota. See `11_Industry_Classification.md` for batch fetch pattern. |
| Financial statements | Balance sheet, income statement, cash flow — quarterly, annual; XBRL structured |
| CB/BW issuances | 전환사채, 신주인수권부사채 issuance events (주요사항보고서 category) |
| Officer shareholdings | 임원·대주주 주식 소유현황 — per person, per company, per period |
| Major shareholder changes | 최대주주 변동 events |
| Related party transactions | 특수관계인 거래 disclosures |
| Auditor opinions | Going-concern qualifications, opinion changes |
| Capital events | Paid-in capital increases (유상증자), rights issuances, mergers, splits |

### What Is Web-Only (not via API)
Full-text original filings in HTML/PDF. Narrative sections of 사업보고서 must be scraped from the web interface, not pulled via API.

### Python Libraries

```python
# DART API wrapper
pip install opendartreader   # github.com/FinanceData/OpenDartReader

# Financial statement extraction (includes PDF/HTML parsing)
pip install dart-fss         # PyPI: dart-fss
```

---

## 2. KRX Data Marketplace

**URL:** https://data.krx.co.kr
**Operator:** 한국거래소 (Korea Exchange)

### Access
- No registration required for web downloads
- Direct CSV/Excel download from the web interface
- Programmatic access via PyKRX library

### What's Available

| Dataset | Details |
|---|---|
| Daily OHLCV | All KOSPI, KOSDAQ, KONEX listed securities; historical |
| Short selling balance (공매도 잔고) | By security, by institution; T+2 lag |
| Program trading | Breakdown by type |
| Market indices | KOSPI, KOSDAQ composites and sector indices |
| Listed company metadata | Market cap, shares outstanding |
| 업종분류 현황 (MDCSTAT03901) | KRX native sector name per ticker; KOSPI and KOSDAQ separately; daily CSV via OTP endpoint. See `11_Industry_Classification.md` for download code. |
| KIND 상장법인목록 | Ticker + KSIC division-level industry name + 상장일 + 결산월 + 대표자명. **Only free source covering KONEX with sector data.** Excel download from `kind.krx.co.kr`. |

### Python Library

```python
pip install pykrx   # github.com/sharebook-kr/pykrx

# Example usage:
from pykrx import stock
df = stock.get_market_ohlcv_by_date("20200101", "20260225", "005930")
```

**Note:** FinanceDataReader is an alternative that covers KRX plus global exchanges:
```python
pip install finance-datareader   # github.com/FinanceData/FinanceDataReader
```

---

## 3. SEIBRO (증권정보포털)

**URL:** https://seibro.or.kr
**Mobile:** https://m.seibro.or.kr
**Operator:** 한국예탁결제원 (Korea Securities Depository, KSD)
**OpenAPI:** http://api.seibro.or.kr/openapi/service/ (via data.go.kr)

### Access
- No login required for most data
- OpenAPI available for structured access

### What's Available

| Dataset | Details |
|---|---|
| CB issuance details | Issue conditions, conversion prices, repricing history |
| BW issuance details | Warrant terms, exercise prices |
| Stock-related bond rights exercise history | Actual conversion/warrant exercise events — critical for tracking dilution |
| Bond rights exercise schedules | Forward-looking calendar |
| Warrant inquiry (신주인수권 조회) | Per-company outstanding warrants |
| Overseas CB/BW | Cross-border issuance data |

SEIBRO is the key source for **reconstructing the full CB/BW lifecycle**: issuance → repricing → exercise → dilution. This is the data layer needed to document the manipulation pattern (see `03_Project_Rationale.md`).

---

## 4. KFTC Corporate Group Portal (기업집단포털)

**URL:** https://egroup.go.kr
**Operator:** 공정거래위원회 (Korea Fair Trade Commission)
**OpenAPI:** https://www.data.go.kr (search 공정거래위원회)

### Access
- Free, public
- Two confirmed OpenAPI endpoints via data.go.kr:
  - 공정거래위원회_지정된 대규모기업집단 조회 서비스
  - 공정거래위원회_대규모기업집단 소속회사 재무현황 정보 조회 서비스

### What's Available (published on annual cycle)

| Dataset | Published |
|---|---|
| Group shareholding structure (주식소유 현황) | May annually |
| Internal transaction data (내부거래 현황) | November/December annually |
| Debt guarantee status (채무보증 현황) | October annually |
| Governance structure (지배구조 현황) | December annually |
| Affiliate lists with financials | Per designation cycle |
| Shareholding diagrams (지분도) | With annual data |

**Threshold:** Covers business groups with total assets exceeding 5 trillion won (대규모기업집단). Does not cover small/mid KOSDAQ companies, which are the primary target for CB/BW manipulation schemes.

---

## 5. WICS / WISEindex

**URL:** https://www.wiseindex.com
**Operator:** WISEfn (FnGuide subsidiary)

### Access
- Free JSON API — no API key, no login required
- Query by sector code and date

### What's Available

| Dataset | Details |
|---|---|
| WICS sector classification | 10 sectors → 25 industry groups → ~70 industries; all KOSPI + KOSDAQ listed companies |
| Index constituents by sector | All members of each WICS sector index at a given date |

**Key detail:** As of October 2025, WICS supersedes FICS (FnGuide Industry Classification Standard). Do not use FICS endpoints — they are no longer maintained.

**WICS sector codes:** G10 (에너지), G15 (소재), G20 (산업재), G25 (경기관련소비재), G30 (필수소비재), G35 (건강관리), G40 (금융), G45 (IT), G50 (커뮤니케이션서비스), G55 (유틸리티).

See `11_Industry_Classification.md` for the API endpoint pattern and Python fetch code.

**Note:** KONEX companies are not covered by WICS.

---

## 6. KRX KIND (상장법인목록)

**URL:** https://kind.krx.co.kr
**Operator:** 한국거래소

### Access
- Free, no login required
- Excel download from the 상장법인목록 page

### What's Available

| Field | Details |
|---|---|
| 회사명 | Company name |
| 종목코드 | 6-digit ticker |
| 업종 | KSIC 중분류 (division) name — text label, not numeric code |
| 주요제품 | Main products |
| 상장일 | Listing date |
| 결산월 | Fiscal year end month |
| 대표자명 | CEO name |

**Coverage:** KOSPI + KOSDAQ + **KONEX** — the only free source covering all three markets with sector data.

**Note:** The 업종 field is the KSIC division name as text (e.g., "전자부품, 컴퓨터, 영상, 음향 및 통신장비 제조업"), not a numeric code. Join to the KSIC Rev. 11 codebook to get the 2-digit division code.

---

## Important Correction

**PublicDataReader** (github.com/WooilJeong/PublicDataReader) was initially listed as a DART/KRX wrapper — this is incorrect. It covers real estate transactions, building permits, land data, and statistical portals (ECOS, KOSIS). It does **not** support DART or KRX financial market data. Use OpenDartReader and PyKRX instead.

---

## Library Stack Summary

```python
# Install all at once
pip install opendartreader dart-fss pykrx finance-datareader pandas networkx
```

| Library | Purpose |
|---|---|
| `opendartreader` | DART API — disclosures, financials, events |
| `dart-fss` | DART financial statement extraction |
| `pykrx` | KRX OHLCV, short selling data |
| `finance-datareader` | KRX universe + global prices; `fdr.StockListing('KRX')` wraps KRX native sector for KOSPI+KOSDAQ+KONEX |
| `pandas` | Data manipulation and joining |
| `networkx` | Officer/shareholder network graph construction |
