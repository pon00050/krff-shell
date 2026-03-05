# Roadmap

## Milestones

| # | Milestone | Status | Script |
|---|---|---|---|
| 1 | Beneish M-Score screen | Complete | `beneish_screen.py` |
| 2 | CB/BW timelines | Implemented, runnable | `cb_bw_timelines.py` |
| 3 | Timing anomalies | Implemented, runnable | `timing_anomalies.py` |
| 4 | Officer network graph | Implemented, runnable | `officer_network.py` |

## Phase 2 Data (extracted)

| Table | Description |
|---|---|
| `cb_bw_events.parquet` | CB/BW issuance events from DART DS005 |
| `price_volume.parquet` | OHLCV ±60 day windows around events |
| `corp_ticker_map.parquet` | corp_code ↔ ticker mapping |
| `officer_holdings.parquet` | Officer holding changes |
| `disclosures.parquet` | DART filing listings |
| `major_holders.parquet` | 5%+ ownership threshold filings |
| `bondholder_register.parquet` | CB bondholder names from 사채권자명부 |
| `revenue_schedule.parquet` | Revenue by customer/segment from 매출명세서 |

## What's Next

1. **SEIBRO repricing data** — extractor built; data.go.kr API key applied for; once key arrives, run extractor → re-score CB/BW timelines and officer network
2. **Populate paid-tier tables** — run paid-tier extractors at scale for flagged companies
3. **Statistical analysis layer** — 10 ISL-grade scripts written; S1–S5 complete (session 24); findings in `FINDINGS.md`

## Statistical Analysis — Completed (Session 24)

| ID | Description | Outcome |
|---|---|---|
| S1 | Fix `cluster_peers.py` z-score contamination (KI-020) | **50 cluster-relative flags** (was 0); KI-020 resolved |
| S2 | Investigate 김형석 and 박정우 | Confirmed 4 and 2 flagged companies respectively; no Tier 1 lead overlap; 박정우 confirmed as 전무이사 at 우리기술 with CB acquisition; see `FINDINGS.md` §5a |
| S3 | Redesign FDR null distribution | timing_anomalies.csv pre-filtered (all extreme events); clean null requires full disclosures.parquet join — new blocker documented |
| S4 | PC3 as alternative manipulation screen | 531 top-decile company-years; 6 of 18 Tier 1 lead company-years in top decile; `pca_pc3_scores.csv` output added |
| S5 | Depreciation extractor for Tier 1 leads | `extract_depreciation_schedule.py` written; Category 20 schema test added; ready to run |

## Statistical Analysis — Remaining Action Items

### Blocked (external dependencies)

| ID | Description | Blocked by |
|---|---|---|
| S6 | Run `extract_seibro_repricing.py` → re-run `permutation_repricing_peak.py` + `survival_repricing.py` | SEIBRO API key activation |
| S7 | Expand `labels.csv` to ≥10 rows → unlock `bootstrap_threshold.py`, `lasso_beneish.py`, `rf_feature_importance.py` | Labeling decision |

### New action items (from session 24 findings)

| ID | Description | Effort | Blocked by |
|---|---|---|---|
| S8 | Run `extract_depreciation_schedule.py` for 5 Tier 1 leads; update `FINDINGS.md` §4 with results | 1–2 hours | DART API (already active) |
| S9 | Join `pca_pc3_scores.csv` (PC3 top decile) against `cb_bw_summary.csv`; identify double-flagged secondary targets | 2 hours | Nothing |
| S10 | Extend `fdr_timing_anomalies.py` to build null from full `disclosures.parquet` + `price_volume.parquet` join | 1 day | Nothing |

## Open Backlog

| ID | Description | Phase | Effort |
|---|---|---|---|
| PR5 | Historical backfill 2014–2018 | 4 | Medium |
| A1 | Automate recurring data refresh | 2 | Low |
| I1 | Verify PyKRX from hosted IPs | 5 | Low |
