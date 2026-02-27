# Multi-Agent Architecture

> **Scope:** Orchestrator-worker agent design, agent roster with model assignments, batch vs. real-time routing, trust boundaries.
> **Canonical for:** Agent schemas; model assignments per agent; always-on vs. on-demand classification.
> **Prerequisites:** `07_Automation_Assessment.md` (reliability constraints), `09_Claude_Cost_Optimization.md` (cost constraints)
> **See also:** `08_Continuous_Monitoring_System.md` (monitoring layer detail)

*Research conducted February 2026. Covers the full functional agent design for the data pipeline.*

---

## Design Philosophy

The pipeline uses a **functional agent model** — one agent per operational domain, not one agent per company. Each agent owns a well-defined function end-to-end and is responsible for it persistently or on demand depending on the nature of that function.

Two layers coexist and reinforce each other:

**Python scripts** — idempotent, deterministic, refinable. Data ingestion and arithmetic (Beneish M-Score, CB/BW timeline construction, timing anomaly calculation) stay as Python. They produce consistent outputs regardless of how many times they run. This is the foundation.

**Agents** — automation and coordination on top of Python. Agents invoke Python scripts as tools, route outputs between functions, apply Claude where reasoning is required, and make the pipeline self-driving. Promoting a Python script to an agent-callable tool does not change the script's logic — it adds orchestration around it.

This is not an either/or choice. The two layers build on each other.

---

## Always-On vs. On-Demand

| Mode | Agent | Rationale |
|---|---|---|
| **Always-on** | Monitoring agent | DART RSS and news arrive continuously; classification must happen within minutes of filing |
| **Always-on** | Orchestrator | Coordinates scheduled runs, responds to monitoring agent events, routes outputs |
| **Scheduled / on-demand** | All others | Triggered by orchestrator on schedule or event; no need to run continuously |

---

## Full Agent Roster

### 1. Orchestrator Agent

**Model:** `claude-sonnet-4-6`
**Mode:** Always-on
**Responsibility:** The central coordinator. Receives events from the monitoring agent, schedules and triggers all other agents, routes outputs between pipeline stages, and assembles the final per-company report. Does not perform analysis — it decomposes, delegates, and aggregates.

**Triggers other agents when:**
- Monitoring agent surfaces a new material DART filing → triggers DART ingestion → triggers relevant screening agents
- Scheduled weekly run → triggers full Layer 1 pipeline → triggers Layer 2 on top-N results
- New CB/BW issuance detected → triggers CB/BW timeline agent for that company

**Tools available:** Task (subagent invocation), Python script runner (calls Layer 1 scripts), file read/write for routing outputs

---

### 2. Monitoring Agent

**Model:** `claude-haiku-4-5`
**Mode:** Always-on
**Responsibility:** Watches DART RSS feeds and Korean financial news continuously. Classifies each item using the single-letter schema (A–F). Escalates material filings to the orchestrator. This is the real-time entry point for the entire pipeline.

**Classification output:** Single letter only — A/B/C/D/E/F. No explanation.

**Escalation logic (Python, not Claude):**
- If classification = material filing type → notify orchestrator
- If classification = routine/irrelevant → log and discard
- Volume spike on a monitored ticker → notify orchestrator regardless of classification

**Tools available:** DART RSS fetch, news API fetch, classification call to Haiku

**Why Haiku:** High-frequency task — dozens to hundreds of items per day. Classification is structured extraction, not reasoning. Haiku at $0.50/$2.50 per MTok vs. Sonnet at $3.00/$15.00 per MTok.

---

### 3. DART Ingestion Agent

**Model:** None (Python script, agent-callable)
**Mode:** On-demand
**Responsibility:** Pulls financial statements, CB/BW issuance notices, officer holding changes, and disclosure filings from OpenDART via OpenDartReader. Writes raw JSON to `01_Data/raw/dart/`. Idempotent — re-running for the same corp_code and period overwrites with identical data.

**Promoted to agent-callable tool:** The orchestrator invokes this as a tool when a new company enters the screening queue or when a scheduled refresh runs. The Python script itself does not change — only the invocation mechanism does.

**Key constraint:** Raw files in `01_Data/raw/` are never modified by downstream agents. If a downstream agent needs different data, it requests a new pull, not an edit.

---

### 4. KRX Ingestion Agent

**Model:** None (Python script, agent-callable)
**Mode:** On-demand / scheduled daily
**Responsibility:** Pulls OHLCV price/volume data, short selling balances, and investor flow from KRX via PyKRX. Maintains the `corp_code ↔ ticker` mapping table with effective date ranges (tickers change on relisting; corp_code does not).

**Schedule:** Daily after market close (15:30 KST) for active monitored companies. Weekly full refresh for the broader KOSDAQ universe.

---

### 5. SEIBRO Scraping Agent

**Model:** `claude-haiku-4-5` (for parsing only; scraping is Python)
**Mode:** On-demand
**Responsibility:** Scrapes CB/BW issuance terms, repricing (리픽싱) history, and conversion/exercise records from SEIBRO. SEIBRO has no official API — this is the most fragile data source in the pipeline.

**Architecture:** Python handles HTTP requests and HTML parsing. Haiku is optionally invoked only when the page structure is ambiguous or changes — to extract structured fields from irregular HTML rather than maintain brittle CSS selectors.

**Output:** Structured records written to `01_Data/raw/seibro/` — same immutability contract as DART raw data.

---

### 6. KFTC Ingestion Agent

**Model:** None (Python script, agent-callable)
**Mode:** Scheduled (KFTC publishes annual updates)
**Responsibility:** Downloads and parses 재벌 cross-shareholding and internal transaction data from KFTC's bulk download. Coverage limited to corporate groups with ≥5 trillion KRW assets — smaller KOSDAQ targets not covered here (use DART officer network data instead).

---

### 7. Beneish Screening Agent

**Model:** None (pure Python arithmetic, agent-callable)
**Mode:** Scheduled quarterly (after quarterly filings close)
**Responsibility:** Calculates 8-component Beneish M-Score for every KOSDAQ company-year from processed DART financial statement data. Outputs ranked anomaly table to `03_Analysis/beneish_screen.csv`.

**No Claude involved.** M-Score is arithmetic on XBRL fields. Claude is not needed and must not be used for this — see CLAUDE.md cost rules.

**Output:** `corp_code, year, m_score, [8 component ratios], dart_link` — ranked descending by M-Score.

---

### 8. CB/BW Timeline Agent

**Model:** None (Python, agent-callable) + `claude-haiku-4-5` for anomaly annotation
**Mode:** On-demand (triggered by monitoring agent on new CB/BW issuance detection, or by orchestrator on scheduled run)
**Responsibility:** For each CB/BW issuance event, reconstructs the full timeline:
1. Issuance date and terms (DART)
2. Exercise price and repricing history (SEIBRO)
3. Actual conversion/exercise events (SEIBRO)
4. Price/volume in ±60 trading days (KRX)
5. Officer holding changes in the same window (DART)

Python constructs the joined timeline. Haiku optionally annotates anomaly signals (repricing below market, conversion at price peak, volume spike before disclosure) in structured output.

**Output:** `03_Analysis/cb_bw_timelines/{corp_code}_{issue_date}.json`

---

### 9. Disclosure Timing Agent

**Model:** None (Python arithmetic, agent-callable)
**Mode:** Scheduled daily (after market close)
**Responsibility:** Compares DART filing timestamps against same-day KRX price/volume. Flags cases where significant price/volume movement (≥5%, above-average volume) preceded the disclosure.

**Anomaly score:** `price_move_magnitude × volume_multiple × timestamp_gap_hours`

**No Claude involved.** Pure arithmetic comparison — a task Python handles natively.

**Output:** `03_Analysis/timing_anomalies.csv` — ranked by anomaly score, updated daily.

---

### 10. Network Graph Agent

**Model:** None (Python/networkx, agent-callable)
**Mode:** Scheduled weekly
**Responsibility:** Constructs and updates the officer/shareholder network graph. Nodes = individuals and companies. Edges = officer roles, >5% shareholdings, cross-holdings.

Uses `networkx` for graph construction and centrality analysis. `pyvis` for visualization output. Highlights densely connected individuals appearing across multiple flagged companies.

**Output:** `03_Analysis/officer_network/` — graph files and centrality reports.

---

### 11. Narrative Inconsistency Agent

**Model:** `claude-sonnet-4-6`
**Mode:** On-demand (triggered by orchestrator after Layer 1 screening completes, for top-N companies)
**Responsibility:** For each flagged company, reads 사업보고서 narrative sections alongside that company's Layer 1 financial ratios. Flags language inconsistent with the underlying data.

**Input:** DART narrative text + Beneish component ratios + CB/BW anomaly flags
**Output:** `[{source_quote, flag_type, severity: low|medium|high}]`

**Why Sonnet:** This is the one task that genuinely requires reasoning — detecting contradiction between qualitative disclosure language and quantitative financial data in Korean. Haiku's reasoning depth is insufficient here.

**Batch API:** Non-urgent. Runs after Layer 1 completes. Use Batch API for 50% cost discount.

---

### 12. Entity Resolution Agent

**Model:** `claude-haiku-4-5`
**Mode:** On-demand (triggered when new officer/shareholder filings are ingested)
**Responsibility:** Clusters name variants of the same individual across DART filings. Resolves 김철수 / 김 철수 / KIM CHUL SOO into a single cluster with confidence score.

**Resolution strategy:**
1. Korean name normalization (spacing variants)
2. Birth date matching where disclosed
3. Company co-occurrence clustering
4. Romanization matching for overseas filings

**Output:** `{cluster_id, names[], confidence: high|medium|low, match_basis}`

**Batch API:** High-volume, non-urgent. Runs nightly on newly ingested filings.

---

## How Python Scripts and Agents Interact

Python scripts are invoked by agents as tools — the script logic does not change, only the invocation mechanism:

```
Orchestrator agent
  → calls DART ingestion tool (Python script)
      → writes 01_Data/raw/dart/{corp_code}.json
  → calls Beneish screening tool (Python script)
      → reads 01_Data/processed/company_financials.parquet
      → writes 03_Analysis/beneish_screen.csv
  → calls Narrative inconsistency tool (Sonnet API call)
      → reads beneish_screen.csv top-N
      → writes 03_Analysis/layer2_flags/{corp_code}_report.json
```

The Python scripts can also be run standalone, without any agent involvement, for development, testing, or manual re-runs. This is the idempotency guarantee — running a script directly produces the same result as running it via an agent.

---

## Pipeline Flow Diagram

```
                    ┌──────────────────────┐
                    │   Monitoring Agent   │ ← always-on
                    │   (Haiku 4.5)        │   DART RSS + news
                    └──────────┬───────────┘
                               │ event / escalation
                               ▼
                    ┌──────────────────────┐
                    │   Orchestrator Agent │ ← always-on
                    │   (Sonnet 4.6)       │   schedules + routes
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
  Data Ingestion          Layer 1 Screening     Layer 2 Analysis
  (Python scripts)        (Python scripts)      (Claude API)
  ─────────────           ────────────────      ─────────────
  DART agent              Beneish agent         Narrative agent
  KRX agent               CB/BW timeline agent  (Sonnet, Batch)
  SEIBRO agent            Timing anomaly agent
  KFTC agent              Network graph agent   Entity resolution agent
                                                (Haiku, Batch)
          │                    │                    │
          └────────────────────┴────────────────────┘
                               │
                               ▼
                    03_Analysis/ outputs
                    → Human review (Layer 3)
```

---

## Batch API vs. Real-Time: By Agent

| Agent | API Mode | Reason |
|---|---|---|
| Monitoring agent | Real-time | Time-sensitive — must classify within minutes |
| Narrative agent | Batch API | Non-urgent; 50% cost discount; runs after Layer 1 |
| Entity resolution agent | Batch API | High volume, nightly cadence |
| SEIBRO parsing (Haiku) | Real-time | Low volume, on-demand |
| All Python agents | N/A | No Claude API calls |

---

## Cost Structure

```
Haiku 4.5:   $0.25/$1.25 per MTok (Batch) — monitoring, entity resolution
Sonnet 4.6:  $1.50/$7.50 per MTok (Batch) — narrative inconsistency
```

With `cache_control: ephemeral` on all system prompts (required by CLAUDE.md), repeated invocations of the same agent against different companies share cached system prompt tokens — ~90% reduction on input token costs for the shared context.

---

## Trust Boundaries

Each agent's tool access is scoped to its function only:

| Agent | Allowed Tools | Denied |
|---|---|---|
| Monitoring | RSS fetch, news fetch, Haiku classify | Write, Bash, subagent spawn |
| SEIBRO | HTTP fetch, HTML parse, Haiku extract | Write to processed/, Bash |
| Narrative | Read processed data, Sonnet call | Web fetch, Bash, Write raw/ |
| Entity resolution | Read raw DART filings, Haiku call | Bash, Write, subagent spawn |
| Orchestrator | All agent invocations, Read/Write processed/ | Bash on production systems |

External data (DART filing text, news body, SEIBRO HTML) enters agent context only in the user turn — never as cached system context. Schema validation on all structured outputs: any response not matching the defined JSON schema is rejected before reaching the orchestrator.

---

## Reference

- [How we built our multi-agent research system — Anthropic Engineering](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Tool use — Anthropic API docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Message Batches API — Anthropic API docs](https://docs.anthropic.com/en/docs/build-with-claude/message-batches)
- `00_Reference/09_Claude_Cost_Optimization.md` — cost patterns and caching rules
- `00_Reference/07_Automation_Assessment.md` — automation ceiling, false positive rates
