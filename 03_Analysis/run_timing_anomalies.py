"""
run_timing_anomalies.py — Standalone runner for disclosure timing anomaly detection.

Extracts the scoring logic from timing_anomalies.py (Marimo app) and runs it
as a plain Python script. Produces the same output files without the Marimo UI.

Output:
    03_Analysis/timing_anomalies.csv

Run:
    python 03_Analysis/run_timing_anomalies.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "01_Data" / "processed"
ANALYSIS = ROOT / "03_Analysis"

MATERIAL_KEYWORDS = [
    "주요사항", "전환사채", "신주인수권", "유상증자", "합병", "분할", "양수도",
    "최대주주", "특수관계인", "풍문", "조회공시", "공급계약", "매출액",
]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    required = ["disclosures.parquet", "price_volume.parquet"]
    missing = [f for f in required if not (PROCESSED / f).exists()]
    if missing:
        print(f"ERROR: Missing data files: {', '.join(missing)}", file=sys.stderr)
        print("Run: python 02_Pipeline/pipeline.py and python 02_Pipeline/extract_disclosures.py", file=sys.stderr)
        sys.exit(1)

    df_disc = pd.read_parquet(PROCESSED / "disclosures.parquet")
    df_pv = pd.read_parquet(PROCESSED / "price_volume.parquet")
    df_map = (
        pd.read_parquet(PROCESSED / "corp_ticker_map.parquet")
        if (PROCESSED / "corp_ticker_map.parquet").exists()
        else pd.DataFrame()
    )
    print(f"Loaded {len(df_disc):,} disclosures, {df_pv['ticker'].nunique():,} tickers")
    return df_disc, df_pv, df_map


def prepare_disclosures(df_disc: pd.DataFrame) -> pd.DataFrame:
    df = df_disc.copy()
    df["filed_at"] = pd.to_datetime(df["filed_at"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["filed_at"])
    df["filed_datetime"] = df["filed_at"] + pd.Timedelta(hours=18)
    df["trading_date"] = df["filed_at"]
    df["gap_hours"] = 18.0 - 15.5  # 2.5 hours after market close
    pattern = "|".join(MATERIAL_KEYWORDS)
    df["is_material"] = df["title"].str.contains(pattern, na=False)
    return df


def prepare_price(df_pv: pd.DataFrame) -> pd.DataFrame:
    df = df_pv.copy()
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col and date_col != "date":
        df = df.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["ticker", "date"])
    df["price_change_pct"] = df.groupby("ticker")["close"].pct_change() * 100

    vol_col = next((c for c in df.columns if "volume" in c.lower()), None)
    if vol_col:
        df["vol_30d_avg"] = (
            df.groupby("ticker")[vol_col]
            .transform(lambda x: x.rolling(30, min_periods=5).mean().shift(1))
        )
        df["volume_ratio"] = df[vol_col] / df["vol_30d_avg"].replace(0, float("nan"))
    else:
        df["volume_ratio"] = float("nan")
    return df


def score_disclosures(
    df_disc_clean: pd.DataFrame,
    df_pv_clean: pd.DataFrame,
    df_map: pd.DataFrame,
) -> pd.DataFrame:
    if not df_map.empty and "corp_code" in df_map.columns:
        map_lookup = df_map.drop_duplicates("corp_code").set_index("corp_code")["ticker"].to_dict()
    else:
        map_lookup = {}

    pv_idx = df_pv_clean.set_index(["ticker", "date"])

    results = []
    for _, disc in df_disc_clean.iterrows():
        corp_code = disc["corp_code"]
        ticker = map_lookup.get(corp_code)
        if not ticker:
            continue

        t_date = disc["trading_date"]
        gap_hours = disc["gap_hours"]

        for offset_days, label in [(0, "same_day"), (-1, "prior_day")]:
            check_date = t_date + pd.Timedelta(days=offset_days)
            key = (ticker, check_date)
            if key not in pv_idx.index:
                continue

            row_pv = pv_idx.loc[key]
            price_chg = float(row_pv.get("price_change_pct", np.nan))
            vol_ratio = float(row_pv.get("volume_ratio", np.nan))

            if np.isnan(price_chg) or np.isnan(vol_ratio):
                continue

            anomaly_score = abs(price_chg) * vol_ratio * gap_hours
            flag = abs(price_chg) >= 5.0 and vol_ratio >= 2.0

            if flag or abs(price_chg) >= 3.0:
                results.append({
                    "corp_code": corp_code,
                    "ticker": ticker,
                    "filing_date": str(t_date.date()),
                    "check_date": str(check_date.date()),
                    "timing": label,
                    "disclosure_type": disc.get("type"),
                    "title": disc.get("title"),
                    "price_change_pct": round(price_chg, 2),
                    "volume_ratio": round(vol_ratio, 2),
                    "gap_hours": round(gap_hours, 1),
                    "anomaly_score": round(anomaly_score, 2),
                    "flag": flag,
                    "is_material": disc.get("is_material", False),
                    "dart_link": disc.get("dart_link"),
                })

    df_results = pd.DataFrame(results)
    if not df_results.empty:
        df_results = df_results.sort_values("anomaly_score", ascending=False)
    return df_results


def main() -> None:
    df_disc, df_pv, df_map = load_data()
    df_disc_clean = prepare_disclosures(df_disc)
    df_pv_clean = prepare_price(df_pv)
    print("Scoring disclosure timing anomalies...")
    df_results = score_disclosures(df_disc_clean, df_pv_clean, df_map)
    print(f"Scored {len(df_results):,} disclosure-day pairs")

    out_path = ANALYSIS / "timing_anomalies.csv"
    df_results.to_csv(out_path, index=False, encoding="utf-8-sig")
    flagged = df_results["flag"].sum() if not df_results.empty else 0
    print(f"Exported {len(df_results):,} rows to {out_path}")
    print(f"  Flagged (>=5% price change AND >=2x volume): {flagged:,}")


if __name__ == "__main__":
    main()
