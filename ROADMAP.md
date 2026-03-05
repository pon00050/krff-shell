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
| `officer_holdings.parquet` | 6,957 | Officer holding changes |
| `disclosures.parquet` | 734 | DART filing listings |
| `major_holders.parquet` | — | 5%+ ownership threshold filings |
| `bondholder_register.parquet` | — | CB bondholder names from 사채권자명부 |
| `revenue_schedule.parquet` | — | Revenue by customer/segment from 매출명세서 |

## What's Next

1. **SEIBRO repricing data** — `extract_seibro_repricing.py` built; data.go.kr API key applied for; once key arrives, run extractor → re-score CB/BW timelines and officer network
2. **Populate paid-tier tables** — run `extract_major_holders.py`, `extract_bondholder_register.py`, `extract_revenue_schedule.py` at scale for Tier 1 leads

## Open Backlog

| ID | Description | Phase | Effort |
|---|---|---|---|
| PR5 | Historical backfill 2014–2018 | 4 | Medium |
| A1 | Automate recurring data refresh | 2 | Low |
| I1 | Verify PyKRX from hosted IPs | 5 | Low |
