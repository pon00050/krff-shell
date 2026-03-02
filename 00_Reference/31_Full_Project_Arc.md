# Full Project Arc — Phase 1 Through Phase 5

> **Scope:** End-to-end narrative of the project from foundation through continuous monitoring.
> **Canonical for:** Project vision, phase sequencing, infrastructure decisions, agent architecture summary.
> **See also:** `04_Technical_Architecture.md` (schema/milestone specs), `08_Continuous_Monitoring_System.md` (3-way match detail), `10_Multi_Agent_Architecture.md` (agent roster), `29_Railway_Infrastructure_Analysis.md` (hosting options), `30_Multi_Agent_Implementation_Guide.md` (Agent SDK adoption)

*Created: March 2, 2026.*

---

## Phase 1 — The Foundation (Complete)

A working batch pipeline that pulls financial statements from DART for every KOSDAQ company (2019–2023), calculates the 8-variable Beneish M-Score, and outputs a ranked anomaly list. 7,042 company-year rows, 5,357 scored. This is the first quantitative screen — it tells you which companies' numbers look like they've been manipulated, based on the same model that flagged Enron before it collapsed.

The output is a static snapshot: here are 1,470 companies ranked by how much their financials deviate from normal patterns. It doesn't tell you *why* or *what happened* — just that something looks off.

---

## Phase 2 — CB/BW Timeline Reconstruction (Scaffold built, 5 gaps remain)

This is where the project transitions from "generic earnings manipulation screen" to "Korean capital markets specific." CB/BW (convertible bonds / bonds with warrants) are the primary vehicle for the manipulation scheme unique to KOSDAQ small-caps:

1. Company issues CB at above-market conversion price
2. Stock price drops (sometimes engineered)
3. Conversion price gets "refixed" (리픽싱) downward
4. Insiders or connected parties exercise at the depressed price
5. Stock price recovers (sometimes engineered)
6. Insiders sell at market, pocketing the spread

Phase 2 reconstructs this timeline per company by joining three data sources: DART (issuance terms), SEIBRO (repricing and exercise history — the hardest data source, requires Playwright scraping of a WebSquare UI), and KRX (price/volume in ±60 trading days around each event). The output is a per-company timeline file that shows whether the CB/BW lifecycle followed the manipulation playbook.

The scaffold exists (`extract_cb_bw.py`, `extract_price_volume.py`, `extract_officer_holdings.py`, `pipeline.py --stage cb_bw`). What's missing: actually running it with a DART key, the SEIBRO scraper, `corp_ticker_map.parquet` to bridge DART corp_codes to KRX tickers, and the scoping filter (top-100 M-Score companies union all companies with at least one CB/BW event).

---

## Phase 3 — Disclosure Timing Anomalies

Pure arithmetic, no AI. For every material DART filing, compare the filing timestamp against same-day KRX price and volume. If a stock moves +5% on 3x average volume *before* the disclosure hits DART, information was trading before it was public. The anomaly score is `price_move × volume_multiple × timestamp_gap_hours`.

This is the second independent signal. A company that scores high on both Beneish (Phase 1) *and* timing anomaly (Phase 3) is a much stronger hypothesis than either alone.

---

## Phase 4 — Officer/Shareholder Network Graph

The hidden connection layer. The CB/BW scheme works because the "independent" bond subscriber is actually controlled by the same people as the issuing company. Phase 4 builds a `networkx` graph: nodes are individuals and companies, edges are officer roles, 5%+ shareholdings, and KFTC cross-holdings.

The hardest problem here is entity resolution — 김철수, 김 철수, and KIM CHUL SOO are the same person across three filings. Claude Haiku handles clustering (structured extraction, within its reliable range). The output highlights densely connected individuals who appear across multiple flagged companies.

---

## Phase 5 — Continuous Monitoring (The System Goes Live)

Everything before Phase 5 is batch: run the pipeline, get a snapshot, review it. Phase 5 makes it a living system using the **3-way match** model (borrowed from accounts payable):

- **Leg 1** (batch, already done): Quantitative flag from Phases 1–4. A company is on the watchlist because its numbers are anomalous.
- **Leg 2** (live): PyKRX polls price/volume every 5 minutes during KRX trading hours for watchlist companies. A ±5% intraday move or 3x volume spike fires a trigger.
- **Leg 3** (live): DART RSS feed + Korean financial news RSS, continuously classified by Claude Haiku (single letter A–F, no explanation). A regulatory action, insider trading allegation, or officer holding change fires a trigger.

The **match engine** runs every 15 minutes. When multiple legs fire on the same company within a 5-trading-day window, confidence escalates. All three legs = highest confidence, alert fires immediately. Leg 1 + Leg 2 (market anomaly, no news) = elevated signal, alert fires. Leg 1 only = stays on watchlist, reviewed at next batch cycle.

Equally important: the system detects **legitimate explanations**. A biotech with a high M-Score and a price surge *after* a genuine clinical trial approval gets flagged for clearance review, not escalation. This keeps the human review queue clean.

**Infrastructure:** This is where the PyKRX geo-block becomes the decisive constraint. KRX returns zero data from data center IPs — Leg 2 requires a Korean residential IP. Three options analyzed:

| Option | Solves | Doesn't Solve |
|---|---|---|
| Oracle VPS (free, already provisioned) | Legs 1+3 (DART + news), $0/month | Leg 2 (PyKRX geo-blocked) |
| Railway (~$10/month) | Clean ops, managed Postgres, git-push deploys | Leg 2 (same geo-block) |
| Mac Mini M4 in Korea (~$4/year electricity) | All three legs from one machine | Needs a physical Korean address |

The likely end state: Mac Mini handles everything that needs a Korean IP (Leg 2 + full pipeline extraction). Railway is optional for ops polish (public API, managed Postgres) if/when a public-facing endpoint is needed.

---

## The Agent Layer — Claude Agent SDK on Top

The 12-agent roster wraps around the Python scripts without changing their logic:

| Agent | Model | Mode | What It Does |
|---|---|---|---|
| Orchestrator | Sonnet | Always-on | Schedules, routes, aggregates |
| Monitoring | Haiku | Always-on | DART RSS + news classification |
| DART/KRX/SEIBRO/KFTC Ingestion | Python only | On-demand | Data pulls, no AI |
| Beneish/CB-BW/Timing/Network | Python only | Scheduled | Screening arithmetic, no AI |
| Narrative Inconsistency | Sonnet | On-demand | Reads 사업보고서 vs. financial ratios, flags contradictions (Batch API) |
| Entity Resolution | Haiku | Nightly batch | Name variant clustering |

Python scripts stay deterministic and idempotent — runnable standalone for testing. Agents add orchestration: the monitoring agent detects a new CB/BW issuance on DART RSS, escalates to the orchestrator, which triggers the CB/BW timeline agent for that company, which pulls from DART + SEIBRO + KRX and outputs a timeline file. The human sees a pre-assembled alert with source citations.

---

## The Output — What the Human Actually Sees

```
═══════════════════════════════════════════════
3-WAY MATCH ALERT — 2026-03-15 14:23 KST
═══════════════════════════════════════════════
Company:     에이텍 (045300)
Watchlist since: 2026-02-26 | Composite score: 94

LEG 1 — Quantitative flag:
  M-Score: -1.18 | CB/BW: YES | Price-disclosure delta: +8.3%

LEG 2 — Market trigger:
  Intraday move: +6.2% | Volume ratio: 4.1x 30-day average

LEG 3 — News/DART trigger:
  Source: 금융감독원 보도자료
  Classification: A (Regulatory action)
  Headline: "금감원, 코스닥 5개사 불공정거래 혐의 조회공시 요구"

MATCH WINDOW: Legs 2 and 3 within 2 trading days
ACTION: Layer 2 analysis queued. Human review required.
═══════════════════════════════════════════════
```

The human doesn't monitor. The human *responds* to pre-corroborated, pre-cited signals and makes the judgment call: is this worth pursuing further, or does the evidence explain itself?

---

## What This Is Not

It's not a fraud detector. It's not a trading signal. It produces **hypotheses for human review** — ranked, corroborated, and cited. The three-layer architecture (Python automation → AI-assisted review → human judgment) is the design constraint. Layer 3 is always a person.

---

## The Public Access Model

The natural end state is a public-facing website where the anomaly outputs — M-Scores, CB/BW timelines, timing anomaly rankings, network graphs — are open for anyone to browse. The infrastructure is public; the methodology is transparent. Anyone can see what the system flagged and why.

The value proposition splits into two tiers:

**Open tier (free, self-serve):** Browse the ranked anomaly tables. See which companies flagged, on which signals, with what confidence. Review the methodology. Follow up on leads independently — the data, the DART filing links, and the component breakdowns are all there.

**Services tier (on request, as-needed):** Customized data pulls, deeper investigation into specific companies or sectors, bespoke analysis combining signals in ways the standard pipeline doesn't cover. This is where domain expertise (accounting background, bilingual Korean/English, understanding of K-IFRS and DART filing conventions) becomes the differentiator — not the software, which is open source, but the judgment layer on top of it.

The operator's involvement in the services tier is interest-driven, not obligation-driven. The system runs autonomously. Leads surface continuously. Most go unactioned — the public can pick them up. When a request comes in, or when something is genuinely interesting, the operator engages. The infrastructure doesn't depend on constant human attention; it rewards it when it arrives.
