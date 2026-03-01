"""
extract_price_volume.py — Phase 2: OHLCV price/volume data via PyKRX.

Loads cb_bw_events.parquet, maps corp_code → ticker, then fetches ±60 trading
days of OHLCV for each CB/BW event window.

NOTE: PyKRX is geo-blocked on VPS/data-center IPs. Run from laptop only.

Output:
  01_Data/processed/price_volume.parquet
  Columns: ticker, date, open, high, low, close, volume

Usage:
  python 02_Pipeline/extract_price_volume.py
  python 02_Pipeline/extract_price_volume.py --sample 5 --sleep 0.3
"""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from pathlib import Path

import pandas as pd

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
RAW = ROOT / "01_Data" / "raw"
PROCESSED = ROOT / "01_Data" / "processed"

WINDOW_DAYS = 60
SLEEP_DEFAULT = 0.3


def fetch_price_volume(
    force: bool = False,
    sample: int | None = None,
    sleep: float = SLEEP_DEFAULT,
    max_minutes: float | None = None,
) -> pd.DataFrame:
    """
    Fetch OHLCV windows around each CB/BW event.
    Writes 01_Data/processed/price_volume.parquet.

    Requires cb_bw_events.parquet and company_list.parquet to exist.
    """
    import time

    out = PROCESSED / "price_volume.parquet"
    if out.exists() and not force:
        log.info("price_volume.parquet exists, loading cached (use --force to refresh)")
        return pd.read_parquet(out)

    cb_path = PROCESSED / "cb_bw_events.parquet"
    if not cb_path.exists():
        raise FileNotFoundError(
            "cb_bw_events.parquet not found. Run extract_cb_bw.py first."
        )
    company_list_path = RAW / "company_list.parquet"
    if not company_list_path.exists():
        raise FileNotFoundError(
            "company_list.parquet not found. Run extract_dart.py --stage company-list."
        )

    events = pd.read_parquet(cb_path)
    companies = pd.read_parquet(company_list_path)

    # Build corp_code → ticker mapping
    ticker_map: dict[str, str] = {}
    for row in companies.itertuples():
        cc = str(row.corp_code).zfill(8)
        ticker = str(getattr(row, "stock_code", "")).zfill(6)
        if ticker and ticker != "000000":
            ticker_map[cc] = ticker

    # Get unique (corp_code, issue_date) pairs
    pairs = events[["corp_code", "issue_date"]].drop_duplicates()
    if sample is not None:
        pairs = pairs.head(sample)

    try:
        from pykrx import stock as krx_stock
    except ImportError:
        raise ImportError("pykrx not installed. Run: uv add pykrx")

    deadline = (
        datetime.datetime.now() + datetime.timedelta(minutes=max_minutes)
        if max_minutes else None
    )

    all_rows: list[dict] = []
    total = len(pairs)

    for i, ev in enumerate(pairs.itertuples(), 1):
        if deadline and datetime.datetime.now() >= deadline:
            log.info("--max-minutes reached at event %d/%d", i, total)
            break

        corp_code = str(ev.corp_code).zfill(8)
        ticker = ticker_map.get(corp_code)
        if not ticker:
            log.debug("No ticker for corp_code=%s, skipping", corp_code)
            continue

        try:
            issue_dt = pd.to_datetime(ev.issue_date)
        except Exception:
            log.warning("Unparseable issue_date=%r for corp_code=%s", ev.issue_date, corp_code)
            continue

        start_dt = (issue_dt - datetime.timedelta(days=WINDOW_DAYS)).strftime("%Y%m%d")
        end_dt   = (issue_dt + datetime.timedelta(days=WINDOW_DAYS)).strftime("%Y%m%d")

        try:
            df_ohlcv = krx_stock.get_market_ohlcv_by_date(start_dt, end_dt, ticker)
            if df_ohlcv.empty:
                continue
            df_ohlcv = df_ohlcv.reset_index()
            df_ohlcv.columns = [c.lower() for c in df_ohlcv.columns]
            df_ohlcv = df_ohlcv.rename(columns={"날짜": "date", "시가": "open", "고가": "high",
                                                  "저가": "low", "종가": "close", "거래량": "volume"})
            # Keep only standard OHLCV columns
            keep = [c for c in ["date", "open", "high", "low", "close", "volume"] if c in df_ohlcv.columns]
            df_ohlcv = df_ohlcv[keep].copy()
            df_ohlcv["ticker"] = ticker
            all_rows.extend(df_ohlcv.to_dict("records"))
            log.debug("Fetched %d rows for ticker=%s", len(df_ohlcv), ticker)
        except Exception as exc:
            log.warning("PyKRX error for ticker=%s: %s", ticker, exc)

        time.sleep(sleep)

    if not all_rows:
        df_out = pd.DataFrame(columns=["ticker", "date", "open", "high", "low", "close", "volume"])
    else:
        df_out = pd.DataFrame(all_rows)
        # Deduplicate
        if "ticker" in df_out.columns and "date" in df_out.columns:
            df_out = df_out.drop_duplicates(subset=["ticker", "date"])

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df_out.to_parquet(out, index=False)
    log.info("Written %d price/volume rows to %s", len(df_out), out)
    return df_out


def main():
    parser = argparse.ArgumentParser(description="Fetch price/volume windows for CB/BW events")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=SLEEP_DEFAULT)
    parser.add_argument("--max-minutes", type=float, default=None)
    args = parser.parse_args()

    fetch_price_volume(
        force=args.force,
        sample=args.sample,
        sleep=args.sleep,
        max_minutes=args.max_minutes,
    )


if __name__ == "__main__":
    main()
