# Monitoring Prerequisites Research

> **Scope:** Pre-build due diligence for the continuous monitoring system (doc 08). Identifies all relevant parties, catalogs technical assumptions that must be verified, and tests keyword vocabulary for the RSS filter.
> **See also:** `08_Continuous_Monitoring_System.md` (3-way match design), `10_Multi_Agent_Architecture.md` (agent roster), `30_Multi_Agent_Implementation_Guide.md` (Agent SDK adoption)

*Created: March 2, 2026.*

---

## Relevant Parties (Institutions, Not Companies)

### A. Regulatory Bodies (Policy + Enforcement)

| Institution | Korean Name | Role | Relevant Outputs |
|---|---|---|---|
| Financial Services Commission | 금융위원회 (FSC) | Policy body | Press releases, 시행령 amendments, enforcement referrals |
| Financial Supervisory Service | 금융감독원 (FSS) | Enforcement arm, DART operator | Press releases, whistleblower intake, investigation announcements |
| Korea Exchange | 한국거래소 (KRX) | Market operator | 조회공시 demands, 불성실공시법인 designations, KIND system, market surveillance |
| National Police Agency | 경찰청 | Criminal investigation | Cross-referral eligibility for whistleblower reports |
| Anti-Corruption & Civil Rights Commission | 국민권익위원회 | Anti-corruption referrals | Also qualifies for 신고포상금 referral pathway |

### B. Data Infrastructure Operators

| Operator | System | Data Provided | Access Method |
|---|---|---|---|
| FSS | DART (OpenDART API) | Filing data, financial statements, CB/BW issuance disclosures | REST API (key required), company-specific RSS |
| KRX | KRX Data / PyKRX | OHLCV, short selling balances | PyKRX library (geo-block on data center IPs) |
| KSD (Korea Securities Depository) | SEIBRO | CB/BW terms, repricing history, exercise events | OpenAPI for reference data; WebSquare scraping for CB/BW detail |
| KFTC (Fair Trade Commission) | egroup.go.kr | Cross-shareholding network (≥5T KRW groups) | Bulk download |
| WISEfn / WISEindex | WICS | Sector classification | HTTPS endpoint (browser headers required) |

### C. News Sources (Leg 3 Channel B)

| Source | Korean Name | RSS Status | Notes |
|---|---|---|---|
| Yonhap News | 연합뉴스 | Confirmed (economy TV RSS index) | `yonhapnewseconomytv.com/rssIndex.html` |
| Hankyung | 한국경제 | Confirmed | `https://www.hankyung.com/feed` |
| Maeil Business | 매일경제 | Inferred (check `/rss/`) | Referenced in knews-rss GitHub repo |
| E-Daily | 이데일리 | Inferred (check `edaily.co.kr/rss/`) | Sister outlet eToday confirmed at `etoday.co.kr/rss/` |
| FSS Press Releases | 금감원 보도자료 | Confirmed | RSS via FSS website; contact 공보실 (02-3145-5786) |
| FSC Press Releases | 금위 보도자료 | Confirmed | `https://www.fsc.go.kr/ut060101` (RSS service guide) |

**Canonical RSS directory:** [github.com/akngs/knews-rss](https://github.com/akngs/knews-rss) — curated Korean news agency RSS collection.

---

## Technical Facts Requiring Verification

Each item below is stated or assumed in docs 08/10/29 but has not been tested against a live endpoint. Verification status indicates what's needed to confirm.

### 1. DART RSS Endpoint

| Aspect | What docs claim | What we found | Status |
|---|---|---|---|
| Aggregated feed | `dart.fss.or.kr/api/todayRSS.xml` | **Offline** — explicitly documented as non-functional | Blocked |
| Company-specific feed | `companyRSS.xml?crpCd=XXXXXX` | **Functional** — requires known corp_code | Confirmed |
| Implication | Doc 08 assumes aggregated RSS polling | Must use OpenDART API for discovery; company RSS only for known targets | Design change needed |

**Verification method:** Manual browser check (URL + inspect). Already partially verified via web search.

### 2. News RSS Feed URLs

| Source | Claimed URL | Verified? | Method needed |
|---|---|---|---|
| 한국경제 | `hankyung.com/feed` | Yes | — |
| 연합뉴스 | Economy TV RSS index | Yes | — |
| 매일경제 | Unknown | No | Manual browser check (`mk.co.kr/rss/`) |
| 이데일리 | Unknown | No | Manual browser check (`edaily.co.kr/rss/`) |

**Blocking impact:** Medium. At least 2 feeds confirmed; others likely available via knews-rss repo.

### 3. PyKRX Intraday Polling

| Question | What docs assume | Verified? |
|---|---|---|
| Can PyKRX fetch same-day data during market hours? | Yes (Leg 2 design assumes 5-min polling) | No — needs code spike |
| Latency at 5-min intervals for 50–500 tickers? | Acceptable | No — needs code spike |
| Rate limit behavior under sustained polling? | No rate limit hit | No — needs code spike from Korean IP |

**Verification method:** Code spike (small test script during KRX trading hours, from laptop — not VPS).
**Blocking impact:** High. If PyKRX can't do intraday, Leg 2 design needs alternative (KRX WebSocket or OTP scrape).

### 4. DART Filing Type Codes

| Question | What docs claim | Verified? |
|---|---|---|
| Exact `report_tp` values for 5 priority filing types (doc 08) | Listed but not tested | No — needs live API call |
| Do these codes appear in OpenDART `list.json` response? | Assumed | No — needs live API call |

**Verification method:** Live API call (requires DART key).
**Blocking impact:** Medium. Wrong codes = missed filings in Leg 1.

### 5. Claude Haiku Classification Latency

| Question | What docs assume | Verified? |
|---|---|---|
| Round-trip for single A–F classification on ~500-token Korean article | <1 second | No — needs code spike |
| Batch throughput for 50 articles in burst | Manageable | No — needs code spike |

**Verification method:** Code spike (direct API call with `claude-haiku-4-5`).
**Blocking impact:** Low. Haiku is known to be fast; this is a sanity check.

### 6. feedparser Compatibility

| Question | What docs assume | Verified? |
|---|---|---|
| Handles Korean RSS feeds (encoding, date parsing) | Yes | No — needs code spike |
| Parses DART company RSS correctly | Yes | No — needs code spike |
| Handles 한국경제 feed structure | Yes | No — needs code spike |

**Verification method:** Code spike (feedparser on confirmed RSS URLs).
**Blocking impact:** Low. feedparser is mature; Korean encoding is standard UTF-8.

### 7. KST Timezone in DART Timestamps

| Question | What docs assume | Verified? |
|---|---|---|
| DART RSS entry timestamps in KST? | Assumed | No — needs manual browser check |
| ISO 8601 or custom format? | Unknown | No — needs manual browser check |

**Verification method:** Manual browser check (fetch a company RSS feed, inspect `<pubDate>`).
**Blocking impact:** Low. Fixable with timezone conversion regardless.

### 8. Short Selling Data Lag

| Question | What docs claim | Verified? |
|---|---|---|
| Short balance data available T+2 | Doc 08 states this | No — needs PyKRX code spike |
| Data format and fields | Assumed standard | No — needs code spike |

**Verification method:** Code spike (PyKRX short selling function).
**Blocking impact:** Low. T+2 vs T+3 doesn't change monitoring design.

### 9. SEIBRO OpenAPI Capabilities

| Question | What docs assume | Verified? |
|---|---|---|
| API exists at `api.seibro.or.kr` | Yes | **Confirmed** — 7 categories, ~40 data items |
| Serves CB/BW repricing/exercise data | Unknown | **No** — API covers corporate info, stock data, lending; NOT CB/BW detail |
| Registration required | Yes | **Confirmed** — account + API key |

**Implication:** SEIBRO API is useful for reference data but does NOT replace WebSquare scraping for CB/BW event history. Phase 2 scraping requirement stands.

### 10. FSS/FSC 보도자료 Feed Format

| Question | What docs assume | Verified? |
|---|---|---|
| FSS offers RSS for press releases | Unknown | **Confirmed** — RSS button on press release page |
| FSC offers RSS | Unknown | **Confirmed** — `fsc.go.kr/ut060101` (service guide) |
| Structured or unstructured content | Unknown | Likely standard RSS 2.0 — needs manual check |

**Verification method:** Manual browser check (subscribe to feed, inspect entries).
**Blocking impact:** Low. Both confirmed available.

---

## Confirmed vs. Assumed

| Confirmed (from doc 18 + this research) | Assumed (never tested live) |
|---|---|
| OpenDART API works, 10K calls/day limit | DART aggregated RSS feed is available (it's NOT — offline) |
| PyKRX returns 0 tickers from VPS (geo-block) | PyKRX can do intraday polling during market hours |
| WICS endpoint uses `GetIndexComponets` (typo is real) | feedparser handles Korean RSS cleanly |
| DART `fnlttMultiAcnt` has 100-company batch limit | DART filing type codes match doc 08 list |
| CFS availability ~40–60% for KOSDAQ | Short selling data lag is exactly T+2 |
| DART error 020 at ~20K requests/day | Claude Haiku classifies Korean text in <1s |
| SEIBRO has no CB/BW API (scraping required) | DART RSS timestamps are in KST |
| FSS and FSC both offer press release RSS | News RSS feeds all use standard RSS 2.0 |
| 한국경제 RSS at `hankyung.com/feed` | 매일경제 and 이데일리 have functional RSS |
| SEIBRO OpenAPI exists (reference data only) | PyKRX rate limits are acceptable at 5-min intervals |

---

## Keyword Search Testing

Testing which Korean keywords surface the target event types for the Leg 3 monitoring classifier (categories A–F from doc 08).

### Category A — Regulatory Action

| Keyword | What it caught | Precision | Recommend | False positives |
|---|---|---|---|---|
| 금감원 조사 | System overviews, general DART info — not specific cases | Low | Exclude from keyword filter; use FSS press releases directly | Returns descriptions of what FSS *does*, not what FSS *did* |
| 조회공시 요구 | KIND system page, regulatory guidance, academic papers | High | Include | Some compliance guidance docs; filter by DART filing type |
| 불성실공시법인 | Official KIND list, corporate monitoring tools | High | Include | Zero — official designation list is canonical |
| 불공정거래 혐의 | KRX enforcement statistics, FSC press releases, case breakdowns | High | Include | News reports statistics, not per-company status; cross-ref with KRX formal decisions |

### Category B — Insider/Manipulation

| Keyword | What it caught | Precision | Recommend | False positives |
|---|---|---|---|---|
| 내부자거래 | Pre-disclosure system (2024+), reporting obligations, clawback rules | High | Include | Generic guidance docs; filter by date (2024+) and DART filings |
| 시세조종 | Regulatory definitions, KRX statistics (16 cases in 2024), enforcement patterns | Medium | Include (verify with KRX formal data) | News provides statistics, not granular enforcement timelines |
| 주가조작 | Synonym for 시세조종; micro-cap manipulation tactics, punishment frameworks | Medium | Include alongside 시세조종 | High overlap; use KRX formal surveillance for authority |
| 미공개정보 이용 | 60% of unfair trading cases; clear regulatory definition; recent enforcement examples | High | Include | News reports after disclosure; use DART/FSC formal decisions |

### Category C — Accounting Irregularity

| Keyword | What it caught | Precision | Recommend | False positives |
|---|---|---|---|---|
| 감사의견 거절 | Regulatory definition, delisting trigger, academic coverage | High | Include | None if using DART structured 감사의견 field |
| 분식회계 | Case studies, enforcement consequences, 기업사냥꾼 patterns | Medium | Include (combine with M-Score) | Requires narrative analysis; routine related-party transactions may flag |
| 회계부정 | Broad category (self-dealing, misrepresentation, fund diversion) | Low-Medium | Include for monitoring, combine with M-Score | Requires narrative detection across multiple DART documents |
| 한정의견 | Clear regulatory significance; 2 consecutive years = KOSDAQ delisting | High | Include | None if using DART structured field |

### Category D — Officer/Shareholder Activity

| Keyword | What it caught | Precision | Recommend | False positives |
|---|---|---|---|---|
| 대량보유 변동 | 5% threshold framework, KIND official list, bulk download API | High | Include | News may not reflect subsequent changes; use DART bulk reports |
| 임원 매도 | Pre-disclosure system (2024+), clawback rules, exit cases | Medium-High | Include | Routine diversification sales at retirement; needs narrative context |
| 주요주주 변경 | KIND official list, change reporting obligations | High | Include | None if using DART structured data |
| CB 전환 | CB framework, repricing restrictions, regulatory tightening (2024) | High | Include | News on CB market trends (리픽싱) is common; use DART filing date |

### Category E — Material Business Event

| Keyword | What it caught | Precision | Recommend | False positives |
|---|---|---|---|---|
| 신규 계약 | Clinical trial contract processes (MFDS), not commercial contracts | Low | Exclude from general filter; use DART 주요계약 공시 | Returns academic/clinical content, not listed company disclosures |
| 임상시험 승인 | Clear regulatory process (IRB → MFDS → initiation) | High (pharma only) | Include for biotech/pharma sector only | Broad false positives outside pharma; restrict by KSIC code |
| 합병 | Typically captured as 주요경영사항 공시 in DART | High | Include via DART structured disclosure | None if using structured field |
| 유상증자 | Captured as 주요경영사항 or 증자 공시 in DART | High | Include via DART structured disclosure | None if using structured field |

### Keyword Strategy Summary

**High-precision, include in automated filter (15 keywords):**
불성실공시법인, 조회공시 요구, 불공정거래 혐의, 내부자거래, 미공개정보 이용, 감사의견 거절, 한정의견, 대량보유 변동, 주요주주 변경, CB 전환, 임원 매도, 시세조종, 주가조작, 합병, 유상증자

**Context-dependent, combine with structured analysis (3 keywords):**
분식회계, 회계부정, 임상시험 승인

**Exclude from keyword filter, use structured data instead (2 keywords):**
금감원 조사 (use FSS press releases), 신규 계약 (use DART 주요계약 공시)

---

## Verification Priority Matrix

Items ordered by blocking impact on monitoring system build:

| Priority | Item | Blocking Impact | Method | Est. Time |
|---|---|---|---|---|
| 1 | PyKRX intraday polling capability | High | Code spike (laptop, trading hours) | 1 hr |
| 2 | DART aggregated RSS replacement strategy | High (design) | Already resolved: use OpenDART API | 0 hrs |
| 3 | DART filing type codes for priority filings | Medium | Live API call (DART key) | 30 min |
| 4 | News RSS URLs (매일경제, 이데일리) | Medium | Manual browser check | 15 min |
| 5 | feedparser Korean RSS compatibility | Low | Code spike | 30 min |
| 6 | Claude Haiku classification latency | Low | Code spike | 15 min |
| 7 | DART RSS timestamp format | Low | Manual browser check | 10 min |
| 8 | Short selling data lag | Low | Code spike | 15 min |

**Total verification effort:** ~3 hours of focused testing, all achievable in a single session with DART key and laptop (Korean IP for PyKRX).

---

*End of document.*
