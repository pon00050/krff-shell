# Roadmap

## Milestones

| # | Milestone | Status | Script |
|---|---|---|---|
| 1 | Beneish M-Score screen | Complete | `beneish_screen.py` |
| 2 | CB/BW timelines | Implemented, runnable | `cb_bw_timelines.py` |
| 3 | Timing anomalies | Implemented, runnable | `timing_anomalies.py` |
| 4 | Officer network graph | Implemented, runnable | `officer_network.py` |

## Phase 2 Data (extracted)

| Table | Rows | Description |
|---|---|---|
| `cb_bw_events.parquet` | 3,672 | CB/BW issuance events from DART DS005 |
| `price_volume.parquet` | 245,354 | OHLCV ±60 day windows around events |
| `corp_ticker_map.parquet` | 1,702 | corp_code ↔ ticker mapping |
| `officer_holdings.parquet` | 6,958 | Officer holding changes |
| `disclosures.parquet` | — | DART filing listings (run `extract_disclosures.py`) |

## What's Next

1. **Run all four analysis milestones** — all are implemented and data exists (including `disclosures.parquet` via `extract_disclosures.py`)
2. **SEIBRO repricing data** — enriches CB/BW timelines (not a blocker for initial analysis):
   - Call 1577-6600 for official API
   - Playwright scraper if no API exists

## Open Backlog

| ID | Description | Phase | Effort |
|---|---|---|---|
| PR5 | Historical backfill 2014–2018 | 4 | Medium |
| A1 | Automate recurring data refresh | 2 | Low |
| I1 | Verify PyKRX from hosted IPs | 5 | Low |
