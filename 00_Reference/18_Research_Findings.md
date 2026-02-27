# Research Findings — MVP Requirements Verification

> **Scope:** Verified technical findings from API testing, empirical KOSDAQ runs, and web research (February 2026).
> **Canonical for:** Confirmed API patterns; DART XBRL field mappings; WICS endpoint behavior; industry classification join logic.
> **Read before:** Modifying any pipeline code or adding new data source integrations.
> **See also:** `02_Data_Sources.md` (source specs), `04_Technical_Architecture.md` (architecture context)

*Documented February 2026. Based on three rounds of web searches against official DART documentation, OpenDartReader source code, Korean regulatory sources, and academic literature. Unanswered questions are flagged at the bottom.*

---

## Section A — User Value and Phasing

### A1: Is standalone Beneish M-Score (Phase 1) useful without price/volume data?

**Finding: Useful as a first-pass ranking signal, but not actionable on its own.**

- At the -1.78 threshold, approximately **8.25% of all listed companies flag positive** at any given time. On a 1,600-company KOSDAQ universe that is ~130 companies — too large a shortlist for direct investigation.
- The model correctly identifies ~76% of actual manipulators prior to public discovery (Beneish 1999; reconfirmed Kelley School 2022), but has a ~17.5% false positive rate among non-manipulators who exceed the threshold.
- Muddy Waters and Hindenburg do not use quantitative screens as their entry point — their published reports lead with accounting evidence, but that is the *output* of already-completed investigation. Their entry point is behavioral/market signals.
- **Phase 1 is worth building** as a ranked shortlist that a journalist or analyst can filter by sector and trend. It is not independently actionable but dramatically narrows the field for Phase 2.

### A2: Is 10-sector WICS granularity sufficient, or is industry group level (25 groups) better?

**Finding: Industry group level (25 groups) is optimal for KOSDAQ.**

- GMT Research (closest structural comparable to this project) uses GICS industry-level peer grouping (~65 industries) and scores every ratio as a percentile within the peer group. They explicitly warn that cross-sector absolute thresholds produce false signals.
- 10-sector level is too coarse: lumping all biotech and all IT into single sectors inflates false positives.
- **WICS industry group (25 groups) is the right default.** However, 8 groups have fewer than 10 KOSDAQ companies and require fallback to sector level (see B6 below for full list).
- For the rarest groups (G4010 은행: 1 KOSDAQ company; G5520 가스: 0), skip peer scoring entirely.

### A3: Should financial companies be excluded?

**Finding: Yes — universal exclusion is correct. No modified Beneish exists for financial firms.**

- The original Beneish (1999) paper explicitly excluded financial institutions because DSRI, GMI, SGAI, and AQI have no meaningful equivalent in bank/insurance balance sheets.
- No published modified approach for Korean financial companies was found in any source.
- **Correct KSIC exclusion:** Section K — Financial and Insurance Activities. KSIC Rev.10 codes **640–669** cover banking, insurance, and auxiliary financial services.
- *Note: whether this range also captures financial holding companies and REITs is unanswered — see Open Questions.*

### A4: KOSDAQ first, or KOSPI 200?

**Finding: KOSDAQ is correct. Supported by academic research and regulatory enforcement data.**

- Two peer-reviewed studies confirm KOSDAQ has structurally higher earnings manipulation than KOSPI:
  - Yoon (2005, JBFA): KOSDAQ firms manipulate earnings more aggressively in both directions, even controlling for operating cash flows.
  - 2017 Korea Science study: KOSDAQ has lower accrual quality and less persistent earnings than KOSPI under K-IFRS.
- FSS enforcement data: KOSDAQ accounts for approximately 70–75% of detected unfair trading cases; ~3:1 ratio vs. KOSPI. *(Source: secondary Korean news reporting on FSS press releases — verify against FSS 자본시장조사 연보 for precise numbers.)*
- The CB/BW 3자배정 manipulation scheme is structurally a KOSDAQ phenomenon: small float, narrative-driven valuation, weak governance. The FSC's 2021 and 2024 CB reform rules were explicitly targeting KOSDAQ small-caps.
- KOSPI 200 has better data quality but much lower base rate of the target phenomena. Starting there would produce cleaner data on schemes that are rarely present.

---

## Section B — Technical Verification

### B1: OpenDART API rate limits

**Finding: Officially undocumented time window. Treat 20,000/day as the working limit.**

- Error code 020 fires at approximately "20,000+ requests" per the official guide. Quote: *"요청 제한을 초과하였습니다. 일반적으로는 20,000건 이상의 요청에 대하여 이 에러 메시지가 발생되나, 요청 제한이 다르게 설정된 경우에는 이에 준하여 발생됩니다."*
- **The time window (per day, per session, per key) is not stated anywhere in the official documentation.** The terms of service defers to "a separate page" that returned 404.
- Community convention assumes calendar-day reset at 00:00 KST, consistent with other FSS public APIs.
- The "10,000/day" figure in the existing project notes is unverified; the official ceiling is 20,000 before error fires. Design conservatively for 10,000 meaningful data calls.
- Per-minute burst limit: not documented anywhere.

### B2: fnlttMultiAcnt batch endpoint — critical finding

**Finding: Batch access works BUT does NOT return depreciation or CFO. Cannot be used as sole source for Beneish.**

Confirmed from OpenDartReader source code (`dart_finstate.py`):

```python
url += 'fnlttMultiAcnt.json' if ',' in corp_code else 'fnlttSinglAcnt.json'
```

- Passing comma-separated 8-digit corp_codes to `dart.finstate()` triggers the batch endpoint.
- Returns a single DataFrame with all companies; `corp_code` column identifies rows.
- **Maximum 100 companies per call** (DART API enforced via error 021). **OpenDartReader does NOT enforce this limit** — passing 150 companies silently returns an empty DataFrame with a `print()` to stdout. Chunking must be implemented manually.
- **The batch endpoint covers only Balance Sheet + Income Statement (주요계정과목).**
  - ✅ Returns: 매출채권, 매출액, 매출원가, 판매비와관리비, 유형자산, 자산총계, 장기차입금, 당기순이익
  - ❌ Missing: **감가상각비** (depreciation — notes item, not main I/S line) and **영업활동현금흐름** (CFO — Cash Flow Statement entirely excluded)
- **Consequence: `fnlttMultiAcnt` cannot be the sole data source for Beneish M-Score.** The DEPI and TATA ratios require fields this endpoint does not return.

**Recommended approach — use DART bulk download for the initial Phase 1 pull:**
- URL: `https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do`
- Tab-delimited TXT files (cp949 encoding), all listed companies, all 5 statement types (BS, IS, CIS, CF, SCE)
- Contains a `sj_div` column: `BS`=Balance Sheet, `IS`=Income Statement, `CF`=Cash Flow, etc.
- Download once per year, parse locally — avoids API rate limits entirely for the historical pull.
- For ongoing updates: use `dart.finstate_all(corp_code, year, fs_div='CFS')` (falls back to OFS automatically as of v0.0.8).

### B3: CFS vs OFS filing rate for KOSDAQ

**Finding: Estimated 40–60% file OFS only — unverified, no authoritative statistic found.**

- Under K-IFRS 1110 (IFRS 10), the consolidation trigger is **control-based**, not a fixed 50% threshold. De facto control can exist with lower ownership.
- KOSDAQ-listed companies cannot claim the CFS exemption (condition: equity not publicly traded; listed companies fail this condition).
- A 2013 KCI academic study found KOSDAQ companies' subsidiary count grew 3.11x after K-IFRS adoption — suggesting pre-IFRS, the *majority* had no subsidiaries. The current ratio is unverified.
- **Confirmed practical issue:** `dart.finstate_all(fs_div='CFS')` silently returns empty DataFrame for OFS-only companies. Fixed in OpenDartReader v0.0.8 with automatic OFS fallback. But mixing CFS years and OFS years for the *same company* in the same 5-year window creates ratio noise — track `fs_type` per company-year and flag year-to-year switches.

### B4: Beneish M-Score threshold for K-IFRS

**Finding: No Korean-specific recalibration exists. -1.78 is used as-is in practitioner tools. Biotech is the highest false positive risk.**

- Extensive search found no published paper recalibrating Beneish for K-IFRS or Korean markets. Korean academic fraud literature is dominated by the **modified Jones model** (재량적 발생액), not Beneish directly.
- Two thresholds in use: **-1.78** (8-variable, higher sensitivity, 17.5% false positive rate) and **-2.22** (5-variable). GMT Research uses -2.22 for Asian screens.
- **K-IFRS-specific issue — expense presentation method:**
  - Companies using the **"function of expense" method** (기능별 분류) disclose COGS and SG&A separately → GMI and SGAI are computable.
  - Companies using the **"nature of expense" method** (성격별 분류) disclose raw inputs (wages, materials, depreciation) without a COGS line → GMI and SGAI **cannot be computed**.
  - GMT Research found 19% of Asian companies had to be excluded from Beneish screening because of missing COGS/SGA disclosure.
  - When GMI and SGAI are unavailable: set them to 1.0 (neutral) and note the limitation in methodology documentation; alternatively drop to the 6-variable model.
- **Biotech/pharmaceutical (바이오/제약) is the highest false positive sector:**
  - Pre-revenue biotech companies have chronically elevated SGI (legitimate revenue growth), AQI (capitalized R&D under IAS 38), and DSRI (milestone payment receivables).
  - These structural characteristics are indistinguishable from manipulation signals on the Beneish screen.
  - Biotech companies have *real* governance problems on KOSDAQ, but Beneish will not distinguish biotech manipulation from biotech growth-stage economics.
  - **Practical mitigation:** flag biotech company scores with a `high_fp_risk` indicator; require Phase 2 corroboration before treating any biotech flag as actionable.

### B5: SEIBRO OpenAPI for CB/BW data

**Finding: API is live but provides only aggregate statistics. Granular repricing/exercise history requires web scraping.**

- SEIBRO has two delivery channels: SEIBRO Open Platform (`openplatform.seibro.or.kr`) and data.go.kr public API (`api.seibro.or.kr/openapi/service/`).
- The `채권정보서비스` endpoint `BondSvc/getRgtXrcInfo` returns **annual aggregate exercise counts and amounts** — not individual issuance-level data.
- **Not available via API:** individual CB issuance terms, repricing (리픽싱) history, individual exercise records by date, CB holder identity.
- **The practical pattern:** DART is the primary source for CB issuance terms and repricing notices (these are structured disclosures via DS005 endpoints — see C1 below). SEIBRO web scraping remains necessary only for granular exercise history (cumulative conversion amounts, remaining unconverted balance).
- SEIBRO's web interface (`seibro.or.kr`) uses WebSquare JavaScript rendering — headless browser (Playwright/Selenium) required for scraping. Plain HTTP requests will not work.

### B6: WICS API — confirmed live, critical corrections to existing docs

**Finding: WICS API is live. CRITICAL: use `https://`, not `http://`. Browser headers required.**

**Existing project notes say `Use http:// not https://` — this is now wrong.** HTTP connections are actively reset by the server. Use HTTPS.

Confirmed working pattern:
```python
import requests

WICS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.wiseindex.com/",
    "Accept": "application/json",
    "X-Requested-With": "XMLHttpRequest",
}

def get_wics_constituents(sec_cd: str, dt: str = "20241230") -> list[dict]:
    """sec_cd: 'G45' (sector) or 'G4510' (industry group)"""
    url = f"https://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt={dt}&sec_cd={sec_cd}"
    resp = requests.get(url, headers=WICS_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()["list"]
```

**Live test results (dt=20241230, confirmed trading day):**
- G45 IT: 686 total companies ✅
- G35 건강관리: 338 total companies ✅
- G20 산업재: 392 total companies ✅

**No market field in WICS response.** Both KOSPI and KOSDAQ companies appear together. Cross-reference against KIND (`kind.krx.co.kr`) or PyKRX to separate markets.

**Industry group codes work** — 4-digit codes (G4510, G3510, etc.) return industry-group-level constituents.

**KOSDAQ peer group sizes by WICS industry group (as of 2024-12-30):**

| Industry Group | Code | KOSDAQ Count | Peer group adequate? |
|---|---|---|---|
| 에너지 | G1010 | 21 | ✅ |
| 소재 | G1510 | 86 | ✅ |
| 자본재 | G2010 | 177 | ✅ |
| 상업서비스 | G2020 | 20 | ✅ |
| 운송 | G2030 | 14 | ✅ |
| 자동차 | G2510 | 73 | ✅ |
| 내구소비재 | G2520 | 87 | ✅ |
| 의류/의복 | G2530 | 9 | ⚠️ borderline — fall back to G25 sector |
| 소매유통 | G2550 | 16 | ✅ |
| 여가/서비스 | G2560 | 18 | ✅ |
| 식품/음료 | G3010 | 5 | ❌ fall back to G30 sector |
| 가정용품 | G3020 | 36 | ✅ |
| 식품유통/약국 | G3030 | 5 | ❌ fall back to G30 sector |
| 제약/바이오/생명 | G3510 | 92 | ✅ |
| 의료기기/서비스 | G3520 | 185 | ✅ |
| 은행 | G4010 | 1 | ❌ skip peer scoring |
| 다각화금융 | G4020 | 4 | ❌ fall back to G40 sector |
| 보험 | G4030 | 77 (excl. SPACs) | ✅ |
| 소프트웨어 | G4510 | 147 | ✅ |
| 하드웨어 | G4520 | 196 | ✅ |
| 반도체 | G4530 | 138 | ✅ |
| 통신서비스 | G5010 | 2 | ❌ fall back to G50 sector |
| 미디어/엔터 | G5020 | 102 | ✅ |
| 전기 | G5510 | 2 | ❌ fall back to G55 sector |
| 가스 | G5520 | 0 | ❌ empty — no peer group possible |

**Rule:** Use industry group if KOSDAQ peer count ≥ 10; fall back to sector if < 10.

### B7: DART `induty_code` and KSIC versioning

**Finding: DART almost certainly still uses Rev.10. Rev.11 crosswalk exists but no machine-readable file yet.**

- KSIC Rev.11 became statutory July 1, 2024 (통계청 고시 제2024-2호).
- No FSS announcement of DART migrating `induty_code` to Rev.11 was found.
- Samsung Electronics still returns `induty_code="264"` consistent with KSIC Rev.10 code C264.
- Statistics Korea published a **Rev.10 → Rev.11 crosswalk table** with the announcement — available at mods.go.kr (고시 제2024-2호). No third-party machine-readable CSV (comparable to `KSIC_10.csv.gz`) has been confirmed yet.
- **Action:** Continue joining `induty_code` to `KSIC_10.csv.gz`. Add a `dtype=str` guard. Check a company registered after July 2024 to empirically verify revision version.

---

## Section C — Code Bugs Confirmed

### C1: `fetch_cb_bw_events()` — two bugs confirmed

**Bug 1:** Loop iterates `("C001", "C002")` but never passes `report_type` to `dart.list()` — makes two identical calls, produces duplicates.

**Bug 2:** `C001`/`C002` are wrong category codes entirely. They belong to `kind='C'` (발행공시 — securities registration). CB/BW *issuance decision* reports are `kind='B'`, `kind_detail='B001'` (주요사항보고서).

**Correct approach — two-stage fetch:**

1. `dart.list(corp_code, kind='B', kind_detail='B001', final=False)` → gets filing index with dates and receipt numbers; filter by `report_nm` containing "전환사채|신주인수권부사채".
2. Direct `requests.get()` to DS005 structured endpoints for issuance terms:
   - CB: `https://opendart.fss.or.kr/api/cvbdIsDecsn.json` (params: crtfc_key, corp_code, bgn_de, end_de)
   - BW: `https://opendart.fss.or.kr/api/bdwtIsDecsn.json` (same params)
   - Returns: conversion price (`cvtr_prc`), face value (`bd_fta`), maturity date (`bd_mtd`), board date (`bddd`), shares to be issued (`cvtr_stk_cnt`)
   - Status `"013"` = no CB/BW history for this company — normal, not an error.
   - **OpenDartReader does NOT wrap DS005 endpoints** — must call via `requests` directly.

Use `final=False` to capture amendment filings (정정보고서) — important for tracking repricing events.

### C2: `lt_debt` fallback to `비유동부채` — confirmed wrong

**`비유동부채`** = all non-current liabilities (includes deferred tax, pension, lease liabilities, bonds). Using it as `lt_debt` dramatically inflates LVGI.

**Correct DART taxonomy element:** `dart_LongTermBorrowingsGross` (account_nm: `장기차입금`)

**Note:** `ifrs-full:NoncurrentPortionOfLongtermBorrowings` (currently in `BENEISH_ACCOUNTS` in `extract_dart.py` line 48) **does not exist** in the IFRS taxonomy. It will never match anything in DART XBRL responses.

**Corrected fallback chain for `lt_debt`:**
1. `dart_LongTermBorrowingsGross` — confirmed in DART API responses
2. `dart_NoncurrentBorrowings` — plausible DART element; unverified element name
3. `ifrs_Borrowings` — total borrowings (over-broad; last resort only)
4. ❌ Remove `비유동부채` / `ifrs_NoncurrentLiabilities` entirely

### C3: `OpenDartReader.corp_codes` market filtering — confirmed always fails

**`stock_market` column does not exist in `corp_codes`.** The DataFrame has exactly 5 columns: `corp_code`, `corp_name`, `corp_eng_name`, `stock_code`, `modify_date`. The `if "stock_market" in df.columns` check always evaluates False, and the pipeline silently processes all ~2,700 listed companies (KOSPI + KOSDAQ + KONEX) instead of KOSDAQ only.

**Correct fix — PyKRX-based market filter:**

```python
from pykrx import stock
import pandas as pd

def fetch_company_list(market: str = "KOSDAQ", dart=None) -> list[dict]:
    # Step 1: Get exchange-specific tickers from KRX (authoritative)
    # Use a recent confirmed trading day
    kosdaq_tickers = set(
        str(t).zfill(6)
        for t in stock.get_market_ticker_list("20241230", market=market)
    )
    # Step 2: Filter corp_codes by matching stock_code to KRX tickers
    df = dart.corp_codes
    df["stock_code"] = df["stock_code"].fillna("").str.strip().str.zfill(6)
    df_market = df[df["stock_code"].isin(kosdaq_tickers)].copy()
    return df_market.to_dict(orient="records")
```

`corp_cls` values (from DART `company.json` endpoint): Y=KOSPI, K=KOSDAQ, N=KONEX, E=Other. Available one company at a time via `dart.company(corp_code)` — not in bulk.

---

## Open Questions — Resolved (Feb 2026)

*All six open questions verified empirically by running `00_Reference/verify/oq_*.py` scripts against the live DART API and KSIC reference data. Results stored in `00_Reference/verify/results/`.*

### OQ-A — CLOSED: KSIC Section K scope confirmed; 리츠 not separately listed

**Finding: Codes 640–669 are complete for financial sector exclusion. 지주회사 IS captured (code 64992). 리츠 is NOT a separate KSIC category under Rev.10.**

- Downloaded `KSIC_10.csv.gz` (2,000 rows). Section K yields exactly 55 rows spanning 641–662.
- `지주회사` appears as code **64992** (`그 외 기타 금융업` → `지주회사`) — inside the 640–669 range, so holding companies are already excluded.
- The string `리츠` does not appear anywhere in KSIC Rev.10. Korean REITs (부동산투자회사) are listed under code **68200** (부동산 임대 및 공급업, Section L — Real Estate Activities) — **outside** Section K and therefore NOT excluded by the 640–669 filter.
- **Action:** Add KSIC code 68200 (or the broader 682xx range) to the financial exclusion list. REITs structurally fail Beneish for the same reasons as banks: the AQI, GMI, and SGAI ratios are meaningless for a pass-through real estate vehicle.
- Result file: `results/oq_a_ksic_section_k.csv`

### OQ-B — CLOSED: 87.8% function method, 12.2% nature method

**Finding: Expense method prevalence verified on 50-company KOSDAQ random sample (2023 사업보고서 CFS).**

| Status | Count | % |
|---|---|---|
| Function method (기능별) | 36 | 87.8% of valid |
| Nature method (성격별) | 5 | 12.2% of valid |
| No CFS filing (status 013) | 9 | 18.0% of sample |

- **Important discovery:** `sj_div` takes value `'CIS'` (not `'IS'`) for companies that present a combined Statement of Comprehensive Income without a separate Income Statement. The `매출원가` check must cover both `sj_div IN ('IS', 'CIS')` — the original script only checked `'IS'` and would have miscounted all `CIS`-only companies as "nature method." Fixed before running.
- GMT Research estimated 19% nature-method exclusion for Asian companies. Empirical KOSDAQ rate is lower (~12%), but 18% of the sample had no CFS filing at all, which is a distinct population effect (see OQ-C).
- **Pipeline implication:** Set missing GMI/SGAI to 1.0 (neutral) for the ~12% nature-method companies; flag them with `expense_method=nature` in output. Do not drop them entirely.
- Result file: `results/oq_b_expense_method.csv`

### OQ-C — CLOSED: 77% CFS, 23% no-filing (not OFS-only)

**Finding: 77% of KOSDAQ companies returned non-empty CFS for 2022. The "40–60% OFS-only" estimate was wrong. The 23% "no_filing" group includes SPACs and newly listed companies, not pure OFS-only filers.**

| fs_type | Count | % |
|---|---|---|
| CFS (returned data) | 154 | 77.0% |
| No filing (status 013) | 46 | 23.0% |

- The 200-company sample was drawn from 2022-12-30 KOSDAQ tickers. Companies returning status `013` include: SPACs (기업인수목적), companies listed after the 2022 fiscal year-end, and genuinely OFS-only companies.
- **Critical note:** `finstate_all` with `fs_div='CFS'` does NOT automatically fall back to OFS in OpenDartReader v0.2.3 — it returns empty (status 013) for OFS-only filers. The v0.0.8 auto-fallback mentioned in B3 above may have been removed. **Always check explicitly:** if CFS returns empty, retry with `fs_div='OFS'` and record `fs_type` in the output row.
- The `fs_div` column is absent from `finstate_all` responses in v0.2.3 — the script recorded `CFS_assumed` because the column was missing. Cannot distinguish CFS from OFS-fallback in returned data without retrying with explicit `'OFS'`.
- **Pipeline implication:** Two-pass strategy required: attempt CFS, fall back to OFS, record which was used per company-year.
- Result file: `results/oq_c_cfs_ofs_split.csv`

### OQ-D — PARTIALLY RESOLVED: No burst throttling; window still undocumented

**Finding: No throttling observed in 10 rapid-fire calls. Window type remains undocumented. Calendar-day reset assumption stands.**

- 10 consecutive calls to `dart.company("00126380")` with no sleep: all returned `ok`, latency 0.7–1.3s per call (network round-trip, not server-side throttling).
- DART FAQ page (`opendart.fss.or.kr/intro/main.do`) returned HTTP 200 but no rate-limit language in parseable HTML — page requires JavaScript rendering for the actual content.
- **Conservative operating assumption unchanged:** 10,000 calls/day, calendar-day reset at 00:00 KST. The 20,000 ceiling figure from official docs is the hard limit; operating at half provides a safety buffer.
- Full window test (observing behavior across a reset boundary) was not run — requires a 24h monitoring period. Not necessary for initial pipeline build.
- Result file: `results/oq_d_rate_limit_observations.txt`

### OQ-E — CLOSED: `dart_NoncurrentBorrowings` does NOT exist

**Finding: Confirmed across 2 companies (3 returned errors/no data). `dart_NoncurrentBorrowings` never appears. `dart_LongTermBorrowingsGross` is the correct primary element.**

Unique borrowing-related `account_id` values observed:
- `dart_LongTermBorrowingsGross` ✅ — confirmed in Celltrion Healthcare BS
- `dart_BondsIssued` ✅ — corporate bonds; a separate line from borrowings
- `ifrs-full_ShorttermBorrowings` ✅ — short-term debt (not relevant to LVGI lt_debt)
- `ifrs-full_CurrentPortionOfLongtermBorrowings` ✅ — current portion of long-term debt
- `dart_NoncurrentBorrowings` ❌ — not found in any company
- `dart_LongTermDebt` ❌ — not found
- `ifrs_Borrowings` / `ifrs-full_Borrowings` ❌ — not found

**Revised lt_debt fallback chain for LVGI:**
1. `dart_LongTermBorrowingsGross` — primary; confirmed in DART XBRL
2. `dart_BondsIssued` — if long-term borrowings absent but bonds present (uncommon; add to numerator)
3. ❌ Remove `dart_NoncurrentBorrowings` — element does not exist
4. ❌ Remove `ifrs-full:NoncurrentPortionOfLongtermBorrowings` — does not exist (already flagged in C2)
5. ❌ Remove `비유동부채` / `ifrs_NoncurrentLiabilities` — far too broad (already flagged in C2)

- Result file: `results/oq_e_account_ids.csv`

### OQ-F — CLOSED: Bulk download requires web login; not freely accessible

**Finding: The DART bulk download page returns HTML with a login form. Direct unauthenticated download is not possible.**

- `GET https://opendart.fss.or.kr/disclosureinfo/fnltt/dwld/main.do` → HTTP 200, 31 KB HTML, login wall detected.
- Two download links found (`재무정보 다운로드`, `재무정보일괄다운로드`) but both point back to the same page (`action=main.do`) via POST form with empty hidden fields `bsn_yr`, `docu_cd`, `role_cd`.
- Candidate direct download URL `downloadFnltt.do?fnlttYear=2022&fnlttQe=11` → HTTP 200 but returned 4.7 KB HTML (error/login page), not a file.
- **Confirmed:** DART bulk download requires an authenticated session (FSS member account, not the API key). It is a web UI feature, not an open data endpoint.
- **Pipeline consequence:** The DART bulk download cannot be used as an unauthenticated alternative to the per-company API. The recommended approach for the historical pull is:
  - Use `dart.finstate_all(corp_code, year, fs_div='CFS')` per company, with explicit OFS fallback.
  - Batch with 0.3–0.5s sleep between calls; ~1,700 KOSDAQ companies × 5 years × 0.5s = ~70 min per full pull, well within daily quota.
- Result file: `results/oq_f_bulk_download_findings.txt`

---

## Pipeline E2E Test Findings (Feb 26, 2026)

*First end-to-end run of the Phase 1 pipeline. Sample: ~50 KOSDAQ companies, 2019–2023.*

### E2E-1: CRITICAL BUG — Financial sector exclusion missed 89 of 126 companies (FIXED)

**Root cause:** `_is_financial()` in `transform.py` used `int(s)` for range check. DART `induty_code` is variable-length (3, 4, or 5 digits). `int("66199") = 66199` is not in `range(640, 670)`, so 5-digit codes were silently passed through.

**Impact (KOSDAQ full universe):** Only 37 of 126 financial sector companies were excluded. 89 companies from insurance (66199), holding companies (64992), and other 5-digit codes passed through to the Beneish screen.

**Fix applied:** Changed `int(s)` to `int(s[:3])` — uses first 3 digits only (the KSIC section code). `int("66199"[:3]) = 661` → correctly in range(640, 670).

**Verification:** Run transform with full KSIC data — log should show "Excluding ~126 rows" not 37.

### E2E-2: WICS API date limitation — hardcoded date would stale out (FIXED)

**Finding:** WICS API confirmed to return empty JSON for historical dates (20231229, 20241231 both return `CNT: 0`). Only recent dates work (20260226, 20250131 confirmed live).

**Fix applied:** Replaced `WICS_SNAPSHOT_DATE = "20260226"` constant with `_find_wics_snapshot_date()` function that probes backwards from today (up to 10 days) to find a valid date. Called once at module load.

**Implication for analysis:** WICS sector assignments are a recent snapshot, not historical. For Phase 1, this is acceptable — most KOSDAQ companies do not change industry group.

### E2E-3: Account ID corrections (confirmed empirically, already applied)

Two account ID mismatches found and fixed in `transform.py`:

| Field | Wrong ID | Correct ID | Impact |
|---|---|---|---|
| SGA | `dart_SellingGeneralAdministrativeExpenses` | `dart_TotalSellingGeneralAdministrativeExpenses` | ~10% SGA null rate on wrong ID |
| Receivables | `ifrs-full_TradeAndOtherCurrentReceivables` as first priority | `dart_ShortTermTradeReceivable` first | 27x DSRI spike on 파크시스템스 — was "기타수취채권" not 매출채권 |

Additional: `"유형자산상각비"` added to Korean fallback list for depreciation — some non-standard filers use this instead of `"감가상각비"`.

### E2E-4: Depreciation null rate ~57.5% — structural, not a bug (DOCUMENTED)

**Finding:** Companies that report the cash flow statement with only a subtotal for operating activities (without individual adjustments) have null depreciation. This is a reporting choice, not a missing data error.

**Fix applied in `beneish_screen.py`:** DEPI is imputed to 1.0 (neutral — depreciation rate unchanged) when depreciation is null. This preserves the M-Score for ~42.5% of companies that would otherwise have a null M-Score.

**Result:** 100% M-Score coverage on test sample.

**Note:** GMT Research found 19% exclusion rate for Asian companies for similar reasons. Our imputation approach produces more coverage but adds noise — acceptable for Phase 1 screening.

### E2E-5: Test mode missing — full 1702-company run triggered accidentally (FIXED)

**Cause:** Running `extract_dart.py --corp-code 00264945` without `--stage financials` triggered the full pipeline including all-company KSIC fetch (~1,700 calls, 8.5 min). No sample mode existed.

**Fix applied:** Added `--sample N` flag to `extract_dart.py`, `pipeline.py`, `fetch_all_financials()`, and `fetch_ksic()`. Limits universe to first N companies.

**Usage:** `python 02_Pipeline/pipeline.py --sample 50 --start 2022 --end 2023` — completes in ~4 min.

### E2E Run Time Benchmarks (confirmed)

| Stage | Scope | Observed time |
|---|---|---|
| company-list | 1,702 KOSDAQ | ~10 sec |
| financials | 50 companies × 5 years | ~4 min |
| financials | 1,702 companies × 1 year | ~28 min (estimated) |
| financials | 1,702 companies × 5 years | ~2.4 hrs (split over 2 days) |
| sector/WICS | 25 groups | ~30 sec |
| sector/KSIC | 1,702 companies | ~8.5 min |
| transform | all files | ~3 sec |

---

## Summary of Critical Pipeline Changes Required

Based on all research findings, the following changes to existing skeleton code are required before any production run:

| File | Line(s) | Issue | Fix |
|---|---|---|---|
| `extract_dart.py` | 48 | `ifrs-full:NoncurrentPortionOfLongtermBorrowings` does not exist in DART XBRL | Replace with `dart_LongTermBorrowingsGross` |
| `extract_dart.py` | 69–91 | `fetch_company_list()` always takes fallback path; returns all markets | Rewrite using PyKRX `get_market_ticker_list()` + corp_codes join |
| `extract_dart.py` | 130–158 | `fetch_cb_bw_events()` loop bug; wrong kind_detail codes | Rewrite using `dart.list(kind='B', kind_detail='B001')` + DS005 direct calls |
| `extract_dart.py` | 111–127 | `fetch_financial_statements()` using `dart.finstate()` which misses depreciation and CFO | Switch to `dart.finstate_all()` per company, or use DART bulk download |
| `transform.py` | 60–92 | `ACCOUNT_MAP['lt_debt']` includes `비유동부채` as fallback | Remove `비유동부채`; use `dart_LongTermBorrowingsGross` as primary, `dart_BondsIssued` as secondary; `dart_NoncurrentBorrowings` does not exist (OQ-E confirmed) |
| `extract_krx.py` | WICS fetch | `http://` URLs will be refused | Change all WICS URLs to `https://`; add browser headers |
| All files | Rate limiting | Current 0.1s sleep between calls may still hit rate limits at scale | Use DART bulk download for historical pull; per-company API only for incremental updates |
