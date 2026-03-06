"""
run_cb_bw_timelines.py — Standalone runner for CB/BW timeline analysis.

Delegates scoring to _scoring.score_events() (shared with cb_bw_timelines.py
Marimo app). Handles data loading, price preparation, and result export.

Outputs:
    03_Analysis/cb_bw_summary.csv
    03_Analysis/cb_bw_timelines/<corp_code>_<date>.json  (flagged events only)

Run:
    python 03_Analysis/run_cb_bw_timelines.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from _scoring import score_events

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "01_Data" / "processed"
ANALYSIS = ROOT / "03_Analysis"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = ["cb_bw_events.parquet", "price_volume.parquet", "officer_holdings.parquet"]
    missing = [f for f in required if not (PROCESSED / f).exists()]
    if missing:
        print(f"ERROR: Missing data files: {', '.join(missing)}", file=sys.stderr)
        print("Run: python 02_Pipeline/pipeline.py --market KOSDAQ --start 2020 --end 2025", file=sys.stderr)
        sys.exit(1)

    df_cb = pd.read_parquet(PROCESSED / "cb_bw_events.parquet")
    df_pv = pd.read_parquet(PROCESSED / "price_volume.parquet")
    df_oh = pd.read_parquet(PROCESSED / "officer_holdings.parquet")
    df_map = (
        pd.read_parquet(PROCESSED / "corp_ticker_map.parquet")
        if (PROCESSED / "corp_ticker_map.parquet").exists()
        else pd.DataFrame()
    )
    print(f"Loaded {len(df_cb):,} CB/BW events across {df_cb['corp_code'].nunique():,} companies")
    return df_cb, df_pv, df_oh, df_map


def prepare_price(df_pv: pd.DataFrame) -> pd.DataFrame:
    df = df_pv.copy()
    date_col = next(
        (c for c in df.columns if "date" in c.lower()),
        df.columns[1] if len(df.columns) > 1 else None,
    )
    if date_col and date_col != "date":
        df = df.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values(["ticker", "date"])
    return df


def export_results(df_results: pd.DataFrame) -> None:
    out_dir = ANALYSIS / "cb_bw_timelines"
    out_dir.mkdir(parents=True, exist_ok=True)

    flagged = df_results[df_results["anomaly_score"] > 0]
    for _, row in flagged.iterrows():
        fname = f"{row['corp_code']}_{row['issue_date'].replace('-', '')}.json"
        with open(out_dir / fname, "w", encoding="utf-8") as f:
            json.dump(row.to_dict(), f, ensure_ascii=False, indent=2, default=str)

    summary_path = ANALYSIS / "cb_bw_summary.csv"
    df_results.to_csv(summary_path, index=False, encoding="utf-8-sig")
    print(f"Exported {len(df_results):,} events to {summary_path}")
    print(f"  Flagged (>=1 flag): {len(flagged):,}")
    print(f"  High risk (>=3 flags): {(df_results['anomaly_score'] >= 3).sum():,}")
    print(f"Per-event JSON in {out_dir}/")


def main() -> None:
    df_cb, df_pv, df_oh, df_map = load_data()
    df_pv_clean = prepare_price(df_pv)
    print("Scoring CB/BW events...")
    df_results = score_events(df_cb, df_pv_clean, df_oh, df_map)
    print(f"Scored {len(df_results):,} events")
    export_results(df_results)


if __name__ == "__main__":
    main()
