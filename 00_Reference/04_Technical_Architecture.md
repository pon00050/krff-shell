# Technical Architecture

> **Scope:** Full pipeline diagram, unified dataset schema, Phase 1–4 milestone specs, and tech stack.
> **Canonical for:** Three-layer architecture; milestone definitions; planned Parquet table schemas.
> **See also:** `17_MVP_Requirements.md` (acceptance criteria), `18_Research_Findings.md` (confirmed API patterns), `pipeline-details.md` (run commands)

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│  OpenDART API    KRX data.krx.co.kr    SEIBRO    KFTC egroup   │
└──────────┬──────────────┬──────────────┬────────────┬──────────┘
           │              │              │            │
           ▼              ▼              ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     02_Pipeline/ (ETL)                          │
│  - Extract: API calls, downloads, scheduled pulls               │
│  - Transform: normalize schemas, resolve entity names,          │
│               join on company ID (corp_code / ticker)           │
│  - Load: structured Parquet or SQLite in 01_Data/processed/     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Unified Dataset Schema                        │
│                                                                 │
│  company_financials   (corp_code, year, quarter, ratio_*)       │
│  cb_bw_events         (corp_code, issue_date, terms, exercise_*) │
│  price_volume         (ticker, date, open, high, low, close,    │
│                        volume, short_balance)                   │
│  officer_holdings     (corp_code, person_id, date, shares, pct) │
│  disclosures          (corp_code, filed_at, type, title)        │
│  kftc_network         (group_name, affiliate_corp_code,         │
│                        cross_holdings)                          │
│  corp_ticker_map      (corp_code, ticker, corp_name, market,   │
│                        effective_from, effective_to)            │
│                        [planned: + krx_sector, ksic_code,      │
│                         wics_sector, wics_industry_group,       │
│                         wics_industry — see 11_Industry_        │
│                         Classification.md]                      │
└──────────────────────────────┬──────────────────────────────────┘

> **Phase 1 status:** Only `company_financials` is produced by the current pipeline.
> The remaining six tables (cb_bw_events, price_volume, officer_holdings, disclosures,
> kftc_network, corp_ticker_map) are Phase 2–4 targets and do not exist yet.
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    03_Analysis/ (Screening)                     │
│                                                                 │
│  Milestone 1: Beneish M-Score screen                            │
│  Milestone 2: CB/BW anomaly timeline reconstruction             │
│  Milestone 3: Disclosure timing anomaly detection               │
│  Milestone 4: Officer/shareholder network graph                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Outputs                                 │
│  Ranked anomaly tables (CSV/Excel)                              │
│  Network visualizations                                         │
│  DART filing links for flagged companies                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Company identifier: corp_code (DART) as primary key

DART assigns every company a unique `corp_code` (8-digit). This is the stable join key across all DART data. KRX uses ticker symbols, which change on relisting. The pipeline should maintain a `corp_code ↔ ticker` mapping table with effective date ranges.

### Storage format

- **Raw data** (`01_Data/raw/`): Downloaded as-is — JSON from DART API, CSV from KRX, HTML from SEIBRO where API is unavailable. Never modify raw files.
- **Processed data** (`01_Data/processed/`): Parquet files (columnar, efficient for pandas) or SQLite for cross-table queries. One file/table per logical entity.

### Notebook format

Analysis notebooks are written in Marimo `.py` cell format (not `.ipynb`) and run as plain Python scripts (`python notebook.py`). They are version-controlled as plain Python with clean git diffs.

> **Marimo interactive UI deferred.** The `marimo edit` / `marimo run` interactive web app experience is not set up at this stage. Scripts execute correctly with `python` directly. Re-enable when interactive filtering/deployment is needed.

### Entity resolution challenge

The same person appears across DART filings as:
- 김철수 (Company A, 2021)
- 김 철수 (Company B, 2022)
- KIM CHUL SOO (overseas filing)

Name normalization + birth date matching (where disclosed) + company co-occurrence clustering is required before the officer network graph is meaningful. This is the hardest data quality problem in the pipeline.

---

## Milestone 1: Beneish M-Score Screen

**What it does:** Calculates the probability of earnings manipulation for each KOSDAQ company-year using 8 financial ratios derived from consecutive-year balance sheets and income statements.

**Inputs required from DART:**
- Receivables (매출채권)
- Revenue (매출액)
- COGS (매출원가)
- SG&A (판매비와관리비)
- PPE (유형자산)
- Depreciation (감가상각비)
- Total assets (자산총계)
- Long-term debt (장기차입금)
- Net income (당기순이익)
- Cash from operations (영업활동현금흐름)

**Korean IFRS note:** Korean listed companies adopted K-IFRS (mandatory since 2011). COGS and SG&A are separately disclosed, resolving the data availability issue that affects approximately 19% of Asian companies on this metric.

**M-Score threshold:** Above -1.78 suggests likely manipulation. The original Beneish model correctly identifies ~76% of manipulators out of sample.

**Output:** `03_Analysis/beneish_screen.csv` — all KOSDAQ companies ranked by M-Score, with component ratios and DART filing links.

---

## Milestone 2: CB/BW Anomaly Timeline

**What it does:** For each CB/BW issuance event on DART, reconstructs the full timeline:
1. Issuance date and terms (from DART 주요사항보고서)
2. Exercise price and any subsequent repricings (from SEIBRO)
3. Actual conversion/exercise events (from SEIBRO 권리행사내역)
4. Price and volume behavior in ±60 trading days around issuance and exercise events (from KRX)
5. Officer/major shareholder holding changes in the same window (from DART)

**Anomaly signals:**
- Repricing below market price (리픽싱) shortly before conversion — mechanically increases dilution
- Conversion clustered at or near price peak
- Surge in trading volume 1–5 days before disclosure of conversion
- Decrease in disclosed officer holdings immediately after conversion events (suggests undisclosed beneficial ownership)

**Output:** `03_Analysis/cb_bw_timelines/` — one file per flagged company, with joined timeline data and anomaly flag rationale.

---

## Milestone 3: Disclosure Timing Anomaly

**What it does:** Compares the timestamp of each DART filing (주요사항보고서, 유상증자, 합병 등) against same-day KRX price and volume to flag cases where significant price/volume movement preceded the disclosure.

**Logic:** If a stock moves +5% or more on above-average volume on day T, and a material disclosure is filed after market close on day T (or on day T+1), that timestamp gap is an anomaly signal — it suggests information was trading before it was publicly disclosed.

**Output:** `03_Analysis/timing_anomalies.csv` — ranked by anomaly score (price move magnitude × volume multiple × gap between market close and filing time).

---

## Milestone 4: Officer/Shareholder Network Graph

**What it does:** Constructs a network graph where:
- Nodes = individuals (officers, major shareholders) and companies
- Edges = relationships (person serves as officer at company; person holds >5% of company; company cross-holds shares of another company)

**Why it matters:** The CB/BW manipulation scheme relies on concealing the fact that the "independent" CB subscriber is actually controlled by the same syndicate as the issuing company's officers. If Person A appears as an officer at Company X and also as a related party or officer at the CB subscriber entity Y, that connection is a red flag even if both disclosures individually appear compliant.

**Library:** `networkx` for graph construction and analysis; `pyvis` or `matplotlib` for visualization.

**Output:** `03_Analysis/officer_network/` — graph files and centrality reports highlighting densely connected individuals who appear across multiple flagged companies.

---

## Technology Stack

```python
# Core pipeline
opendartreader    # DART API
dart-fss          # DART financial statement extraction
pykrx             # KRX price/volume data
pandas            # Data manipulation
pyarrow           # Parquet storage

# Analysis
numpy             # Numerical computation
scipy             # Statistical testing
networkx          # Network graph
pyvis             # Interactive network visualization

# Analysis environment
marimo            # Reactive notebook — stored as .py, deployable as web app
uv                # Package management — dependencies inlined per PEP 723
matplotlib        # Charting
plotly            # Interactive charts
```

---

## Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| No intraday order flow | Cannot see sequence of orders within a day | Focus on daily patterns; flag for institutional follow-up |
| SEIBRO not fully API-accessible | Some CB/BW data requires web scraping | Document scraping methodology; add to pipeline incrementally |
| KFTC data covers only groups ≥5 trillion won assets | Misses small/mid KOSDAQ targets of CB manipulation | Use DART officer network data for smaller companies |
| Entity resolution across name variants | Network graph may miss connections | Document limitations; use birth date matching where disclosed |
| Reward payout is years after tip filing | Not a near-term income source | Frame as public infrastructure and portfolio artifact |
| `corp_ticker_map` has no sector data | Beneish false positive rate higher; no peer-group context for CB/BW triage; sector-concentrated manipulation (biotech, entertainment, IT) not filterable | Add KRX 업종분류 (MDCSTAT03901) + DART `induty_code` + WICS sector to `corp_ticker_map` — see `11_Industry_Classification.md` for full schema and implementation notes |
