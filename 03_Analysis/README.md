# 03_Analysis — Legacy Monolith Copy

> **Canonical source:** `../kr-anomaly-scoring` repo (`kr_anomaly_scoring/` package)

The scripts in this directory are the **original monolith** from before the ecosystem split
(2026-03-26). The scoring logic has since been extracted into the standalone
`kr-anomaly-scoring` package.

## Status

These files are kept here because `03_Analysis/run_*.py` entry points are used by
`krff refresh` and documented in pipeline run commands.

**Do not edit these files directly.** Changes to scoring logic belong in `kr-anomaly-scoring`.
The two codebases can diverge silently — any divergence is a bug.

## Files

| File | Canonical location |
|------|--------------------|
| `_scoring.py` | `kr-anomaly-scoring/kr_anomaly_scoring/_scoring.py` |
| `beneish_screen.py` | `kr-anomaly-scoring/kr_anomaly_scoring/beneish_screen.py` |
| `beneish_viz.py` | `kr-anomaly-scoring/kr_anomaly_scoring/beneish_viz.py` |
| `cb_bw_timelines.py` | `kr-anomaly-scoring/kr_anomaly_scoring/cb_bw_timelines.py` |
| `officer_network.py` | `kr-anomaly-scoring/kr_anomaly_scoring/officer_network.py` |
| `timing_anomalies.py` | `kr-anomaly-scoring/kr_anomaly_scoring/timing_anomalies.py` |
| `run_*.py` (3 files) | `kr-anomaly-scoring/kr_anomaly_scoring/run_*.py` |
| `phase1_research_questions.py` | `kr-anomaly-scoring/` (research script) |
