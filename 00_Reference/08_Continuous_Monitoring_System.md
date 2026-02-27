# Continuous Monitoring System: Real-Time News Integration and 3-Way Match Validation

> **Scope:** DART RSS + news monitoring design, 3-way match validation (DART + news + price), real-time trigger architecture.
> **Canonical for:** Monitoring system design; 3-way match logic.
> **Prerequisites:** `04_Technical_Architecture.md`, `10_Multi_Agent_Architecture.md`
> **See also:** `09_Claude_Cost_Optimization.md` (cost implications of always-on monitoring)

*Drafted February 2026. Extends the architecture in 04_Technical_Architecture.md and 07_Automation_Assessment.md.*

---

## The Problem This Solves

The Layer 1 pipeline runs on a schedule — overnight batch, quarterly financial data. It produces a ranked anomaly list. But a ranked list is a static snapshot: it tells you which companies looked anomalous as of the last data pull. It does not tell you whether anything is happening *right now* on those companies.

The monitoring system described here runs continuously alongside the batch pipeline. Its purpose is not to generate new anomaly signals — the pipeline does that. Its purpose is to watch the companies already flagged and detect when real-world events either corroborate the pipeline's suspicion or explain it away.

The framing is borrowed from accounts payable: **a 3-way match**. In AP, you do not release payment on an invoice alone. You require three independent documents — the purchase order, the goods receipt, and the invoice — to confirm the same underlying transaction from three different sources before the obligation is recognized.

Applied here:

| AP 3-Way Match | Capital Markets 3-Way Match |
|---|---|
| Purchase Order | Layer 1 quantitative flag (M-Score, CB/BW, price delta) |
| Goods Receipt | Market behavior confirmation (price/volume action post-flag) |
| Invoice | News or disclosure corroboration (external record of the same event) |

The analogy holds directionally but should not be read as a hard gate. In AP, payment is blocked until all three documents arrive. Here, the absence of a Leg 3 news or disclosure event does not invalidate a finding — many companies with genuine anomalies will never appear in financial press, and DART filings only surface what companies are required to disclose. Silence is not clearance.

The more accurate framing: each leg that fires increases the confidence level of the signal. A Leg 1 + Leg 2 combination — quantitative anomaly confirmed by live market behavior — is already a meaningful signal that warrants human review, regardless of whether news exists. Leg 3, when it appears, upgrades that signal significantly. When all three align, confidence is at its highest. The monitoring system tracks all three and weights accordingly; it does not wait for all three before acting.

---

## Architecture Overview

```
                    ┌─────────────────────────────────┐
                    │     WATCHLIST (Layer 1 output)   │
                    │  Companies with composite score  │
                    │  above threshold — updated nightly│
                    └────────────────┬────────────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
    │   LEG 1 (batch)  │  │  LEG 2 (live)    │  │  LEG 3 (live)    │
    │                  │  │                  │  │                  │
    │  Quantitative    │  │  Market behavior │  │  News + DART     │
    │  pipeline flag   │  │  monitoring      │  │  disclosure      │
    │  (already done)  │  │  via PyKRX       │  │  monitoring      │
    └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
             │                     │                      │
             └─────────────────────┼──────────────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────────┐
                    │       MATCH ENGINE               │
                    │  How many legs have fired on     │
                    │  this company within the window? │
                    └────────────────┬────────────────┘
                                     │
          ┌──────────────────────────┼──────────────────────────┐
          │                          │                          │
          ▼                          ▼                          ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  ALL THREE LEGS  │      │  LEG 1 + LEG 2   │      │  LEG 1 ONLY      │
│                  │      │  (no news)        │      │                  │
│  Highest         │      │                  │      │  Batch pipeline  │
│  confidence      │      │  Market behavior │      │  flag only. No   │
│                  │      │  confirms quant  │      │  live corrobor-  │
│  → Alert fires   │      │  signal. Absence │      │  ation yet.      │
│  → Layer 2       │      │  of news does    │      │                  │
│    analysis      │      │  not clear it.   │      │  → Stays on      │
│    queued        │      │                  │      │    watchlist.    │
│  immediately     │      │  → Alert fires   │      │  → Reviewed at   │
│                  │      │  → Layer 2       │      │    next batch    │
│                  │      │    queued        │      │    cycle.        │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## Leg 2: Market Behavior Monitoring

**What it watches:** Price and volume for every company on the watchlist, in near-real-time during KRX trading hours (09:00–15:30 KST).

**Data source:** PyKRX — same library as the batch pipeline. Intraday polling is feasible; rate limits are generous for a watchlist of <500 companies.

**What constitutes a Leg 2 trigger:**

| Signal | Threshold (starting point, calibrate over time) |
|---|---|
| Intraday price move | ±5% from prior close within a single session |
| Volume spike | 3x the 30-day average daily volume |
| Short selling surge | Short volume > 20% of total daily volume (unusual for KOSDAQ) |
| Consecutive day pattern | 3+ consecutive sessions of above-average volume without disclosed catalyst |

**Implementation:**

```python
# Pseudocode — polling loop during market hours
import pykrx.stock as krx
from datetime import datetime
import time

WATCHLIST = load_watchlist()  # tickers from Layer 1 output above threshold
POLL_INTERVAL = 300           # seconds — every 5 minutes during market hours

while market_is_open():
    for ticker in WATCHLIST:
        current = krx.get_market_ohlcv_by_date(today, today, ticker)
        baseline = load_30day_average(ticker)

        volume_ratio = current['거래량'] / baseline['avg_volume']
        price_change = (current['종가'] - current['시가']) / current['시가']

        if abs(price_change) >= 0.05 or volume_ratio >= 3.0:
            log_leg2_trigger(ticker, price_change, volume_ratio, timestamp=now())

    time.sleep(POLL_INTERVAL)
```

A Leg 2 trigger alone is not an alert. It goes into the match buffer and waits for Leg 3.

---

## Leg 3: News and Disclosure Monitoring

This is the most complex leg. It watches three independent channels:

### Channel A — DART Real-Time RSS

DART publishes a real-time RSS feed of new filings. Every 주요사항보고서, 임시주주총회 공고, 주식등의대량보유상황보고서, and 임원·주요주주특정증권등소유상황보고서 filed for a watchlist company triggers a Leg 3 event immediately.

This is the highest-value channel. The specific disclosures that matter most for CB/BW scheme detection:

| Filing Type | Why It Matters |
|---|---|
| 주요사항보고서 (신주인수권부사채) | New BW issuance — matches against existing CB/BW flag |
| 주식등의대량보유상황보고서 | 5%+ holder change — who is accumulating before what? |
| 임원·주요주주 소유상황보고서 | Officer/major shareholder holding change — are insiders selling? |
| 조회공시 요구 | KRX formally asked the company to explain unusual trading — confirms market anomaly |
| 불성실공시법인 지정 | FSS designated the company as a habitual late or inaccurate filer |

```python
import feedparser

DART_RSS = "https://dart.fss.or.kr/api/rss.xml"  # verify current endpoint

def poll_dart_rss(watchlist_tickers):
    feed = feedparser.parse(DART_RSS)
    for entry in feed.entries:
        corp_code = extract_corp_code(entry)
        if corp_code in watchlist_tickers:
            filing_type = extract_filing_type(entry)
            log_leg3_dart_trigger(corp_code, filing_type, entry.link, timestamp=now())
```

### Channel B — Korean Financial News RSS / API

Major Korean financial news outlets publish RSS feeds. The monitoring system subscribes to all of them and filters for mentions of watchlist company names or tickers.

Priority sources:

| Source | Coverage | Feed Type |
|---|---|---|
| 연합뉴스 (Yonhap) | Wire service — regulatory actions, FSS/FSC announcements | RSS available |
| 한국경제 (Hankyung) | Deep corporate coverage, often first on 공시 analysis | RSS available |
| 매일경제 (MK) | Capital markets reporting | RSS available |
| 이데일리 | KOSDAQ-focused, strong on small-cap corporate events | RSS available |
| 금융감독원 보도자료 | FSS press releases — enforcement, penalties, warnings | RSS / direct scrape |
| 금융위원회 보도자료 | FSC policy announcements | RSS / direct scrape |

**Important calibration note:** Korean financial news frequently covers companies without any negative implication — earnings beats, new contracts, partnerships. A news mention alone is not a Leg 3 trigger. The content must be categorized first.

This is where Claude earns its place in the monitoring loop.

### Channel B Processing — Claude as News Classifier

When a news article mentions a watchlist company, it is passed to Claude with a narrow classification prompt:

```
Classify the following Korean financial news article into exactly one category.
Company under review: [company name / ticker]

Categories:
A — Regulatory action or investigation (FSS, FSC, prosecutors, KRX inquiry)
B — Insider trading allegation or market manipulation allegation
C — Accounting irregularity or audit qualification
D — Major shareholder or officer activity (buying, selling, resignation, arrest)
E — Material business event (contract, acquisition, clinical trial, partnership)
F — No material relevance to the company's financial integrity

Return only the letter. Do not explain.

Article:
[full text]
```

Only categories A, B, C, and D constitute Leg 3 triggers. Category E is logged but does not trigger the match engine — it goes to the "legitimate explanation" buffer, which is equally important (see below). Category F is discarded.

This is a classification task, not open-ended analysis. It is within Claude's demonstrated reliable capability range even for Korean-language text.

---

## The Match Engine

The match engine runs continuously and checks the trigger buffer every 15 minutes.

**Match logic:**

```
For each company on the watchlist:

  Leg 1 is always present (prerequisite for watchlist membership).
  The engine evaluates what else has fired within the past [N] trading days.

  IF Leg 2 fired AND Leg 3 fired (all three legs active):
    → HIGHEST CONFIDENCE
    → Fire alert immediately
    → Queue for Layer 2 Claude analysis
    → Log with all three source citations

  ELSE IF Leg 2 fired, no Leg 3 (market anomaly, no news):
    → ELEVATED SIGNAL — absence of news does not clear the flag
    → Fire alert
    → Queue for Layer 2 Claude analysis
    → Log with note: "No corroborating news detected as of [timestamp].
      Many companies with genuine anomalies do not appear in press."

  ELSE IF Leg 3 fired, no Leg 2 (news/disclosure, no market anomaly):
    → MODERATE SIGNAL — news event is notable but market hasn't moved yet
    → Log, increment counter
    → If Leg 2 fires within [N] days of the Leg 3 event:
       → Upgrade to ELEVATED SIGNAL, fire alert
    → If [N] days elapse without Leg 2: hold in watchlist, review at batch cycle

  ELSE (Leg 1 only, nothing new):
    → No action. Company remains on watchlist.
    → Reviewed at next batch cycle for score changes.
```

**The time window [N]:** Calibration parameter. Starting point: 5 trading days. Adjust based on observed false match rates over time.

---

## The Equally Important Function: Legitimate Explanation Detection

The monitoring system does not only look for confirmation. It also looks for explanations that *clear* a flagged company.

If a watchlist company generates a Category E news event — major contract win, regulatory approval, legitimate acquisition — that event is logged as a potential explanation for the Leg 1 anomaly signals. A company with a high Beneish M-Score and a price surge *after* a genuine clinical trial approval is not a fraud signal. It's a biotech stock doing what biotech stocks do.

This clearance function is as operationally important as the alert function. It prevents the human review queue from filling with resolved cases.

```
Clearance logic:
  IF Leg 3 Category E event fires on a company
  AND the event's timing aligns with the Leg 1 anomaly window
  THEN:
    → Flag company as "pending clearance review"
    → Queue short Claude summary: "Does this event plausibly explain
      the price movement and disclosure timing anomaly flagged on [date]?"
    → Human confirms clearance or keeps company on watchlist
```

---

## Alert Output Format

When a 3-way match fires, the alert goes to a designated output — email, Slack webhook, local log file, or all three. The alert is structured, not narrative:

```
═══════════════════════════════════════════════
3-WAY MATCH ALERT — 2026-03-15 14:23 KST
═══════════════════════════════════════════════
Company:     에이텍 (045300)
Watchlist since: 2026-02-26 | Composite score: 94

LEG 1 — Quantitative flag (2026-02-26):
  M-Score: -1.18 | CB/BW: YES | Price-disclosure delta: +8.3%

LEG 2 — Market trigger (2026-03-14):
  Intraday move: +6.2% | Volume ratio: 4.1x 30-day average
  Short volume: 24% of daily total

LEG 3 — News/DART trigger (2026-03-15):
  Source: 금융감독원 보도자료
  Classification: A (Regulatory action)
  Headline: "금감원, 코스닥 5개사 불공정거래 혐의 조회공시 요구"
  DART link: [auto-populated]

MATCH WINDOW: Legs 2 and 3 within 2 trading days
ACTION: Layer 2 analysis queued. Human review required.
═══════════════════════════════════════════════
```

---

## What This Does to the Human Workload

Without the monitoring system, the human operator checks the batch pipeline output periodically and manually searches for news on flagged companies. That's unsustainable as the watchlist grows.

With the monitoring system:

| Task | Without Monitoring | With Monitoring |
|---|---|---|
| News surveillance on 50+ companies | Manual, daily, time-intensive | Automated, continuous |
| Connecting market event to pipeline flag | Manual correlation | Match engine handles it |
| Identifying when a flag is explained away | Ad hoc | Clearance detection automated |
| Response time to a regulatory action | Hours to days | Minutes (alert fires on DART RSS) |
| Human attention required | Ongoing, unfocused | Triggered, focused, pre-contextualized |

The human operator is not monitoring. The human operator is responding to confirmed, pre-corroborated signals — with the source citations already assembled — and making the judgment call on what to do next.

That is the 3-way match function: the infrastructure holds the invoice until the PO and the GR arrive. You only see it when all three are in hand.

---

## Implementation Notes

**Dependencies beyond the existing stack:**
- `feedparser` — RSS parsing (pip install feedparser)
- `schedule` or `APScheduler` — continuous polling loop management
- A lightweight persistent store for the trigger buffer — SQLite is sufficient at this scale
- Anthropic API access — already required for Layer 2; same key, same budget line

**Operational risk — scraper fragility:**
News RSS feeds are generally stable but not guaranteed. Korean news sites occasionally restructure their feeds. Build the news polling with graceful failure: if a feed goes dark, the system logs the failure and continues; it does not crash the monitoring loop.

**KST timezone handling:**
The monitoring system operates on KST (UTC+9). The batch pipeline, news timestamps, DART filing timestamps, and KRX data all need to be normalized to the same timezone before the match engine compares windows. This is a common source of off-by-one-day errors in multi-source systems — handle it explicitly, not implicitly.

**Starting watchlist size:**
Begin with the top 20–30 companies by composite score. A watchlist of 200+ companies is technically feasible but generates more noise than signal until the classification thresholds are calibrated. Grow the watchlist as the clearance and match logic is validated against observed outcomes.
