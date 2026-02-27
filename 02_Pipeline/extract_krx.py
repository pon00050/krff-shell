"""
extract_krx.py — KRX data extraction layer.

Fetches daily OHLCV and short selling data from KRX via PyKRX.
All output is written to 01_Data/raw/krx/ as CSV.
Scripts are idempotent — re-running overwrites with identical data.

PyKRX does not require an API key. It scrapes the KRX data portal,
so network failures are expected — each fetch retries up to 3 times.

Usage:
    python 02_Pipeline/extract_krx.py --market KOSDAQ --start 2020-01-01 --end 2025-12-31
    python 02_Pipeline/extract_krx.py --ticker 005930  # single ticker
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

import pandas as pd
from pykrx import stock as krx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

RAW_KRX = Path("01_Data/raw/krx")


def _retry(fn, *args, retries: int = 3, delay: float = 2.0, **kwargs) -> pd.DataFrame:
    """Call fn(*args, **kwargs) with up to `retries` retries on exception."""
    for attempt in range(1, retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            if attempt == retries:
                raise
            log.warning("Attempt %d/%d failed: %s — retrying in %.1fs", attempt, retries, exc, delay)
            time.sleep(delay)
    raise RuntimeError("Unreachable")


def fetch_listed_companies(market: str = "KOSDAQ") -> pd.DataFrame:
    """
    Return DataFrame of all companies listed on market with columns:
    ticker, corp_name, sector, listing_date.

    market: 'KOSDAQ' | 'KOSPI' | 'KONEX'
    """
    log.info("Fetching listed companies for market: %s", market)
    tickers = krx.get_market_ticker_list(market=market)
    rows = []
    for ticker in tickers:
        try:
            name = krx.get_market_ticker_name(ticker)
            rows.append({"ticker": ticker, "corp_name": name, "market": market})
            time.sleep(0.05)
        except Exception as exc:
            log.warning("Ticker name fetch failed %s: %s", ticker, exc)

    df = pd.DataFrame(rows)
    out = RAW_KRX / f"listed_{market.lower()}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log.info("Saved %d tickers to %s", len(df), out)
    return df


def fetch_ohlcv(
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch daily OHLCV for ticker from start_date to end_date.

    start_date / end_date: 'YYYYMMDD'

    Output: 01_Data/raw/krx/ohlcv/{ticker}.csv
    """
    log.debug("Fetching OHLCV %s %s→%s", ticker, start_date, end_date)
    df = _retry(
        krx.get_market_ohlcv_by_date,
        start_date,
        end_date,
        ticker,
    )
    if df is None or df.empty:
        log.warning("No OHLCV data for %s", ticker)
        return pd.DataFrame()

    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    df.insert(0, "ticker", ticker)

    out = RAW_KRX / "ohlcv" / f"{ticker}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return df


def fetch_short_balance(
    ticker: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Fetch daily short selling balance for ticker.

    Output: 01_Data/raw/krx/short/{ticker}.csv
    """
    log.debug("Fetching short balance %s %s→%s", ticker, start_date, end_date)
    try:
        df = _retry(
            krx.get_shorting_balance_by_date,
            start_date,
            end_date,
            ticker,
        )
    except Exception as exc:
        log.warning("Short balance fetch failed %s: %s", ticker, exc)
        return pd.DataFrame()

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]
    df.insert(0, "ticker", ticker)

    out = RAW_KRX / "short" / f"{ticker}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return df


def build_corp_ticker_map(
    dart_corp_list: list[dict],
    krx_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build corp_code ↔ ticker mapping table with effective date ranges.

    Joins DART company list (has corp_code + stock_code = ticker) with KRX list
    (has ticker + corp_name). Deduplication handles relistings: same corp_code
    can have multiple tickers over time — captured via effective_from / effective_to.

    Output: 01_Data/raw/krx/corp_ticker_map.csv
    """
    log.info("Building corp_code ↔ ticker map")

    dart_df = pd.DataFrame(dart_corp_list)
    # OpenDartReader uses 'stock_code' for the KRX ticker
    if "stock_code" not in dart_df.columns:
        raise ValueError("dart_corp_list missing 'stock_code' column")

    dart_df = dart_df.rename(columns={"stock_code": "ticker"})
    dart_df = dart_df[dart_df["ticker"].notna() & (dart_df["ticker"] != "")]

    # Merge on ticker to get KRX name (optional enrichment)
    merged = dart_df.merge(
        krx_df[["ticker", "corp_name", "market"]].rename(columns={"corp_name": "krx_name"}),
        on="ticker",
        how="left",
    )

    # Effective date range: OpenDartReader provides modify_date (last update to corp_code record).
    # Use it as effective_from; effective_to = None means currently active.
    if "modify_date" in merged.columns:
        merged = merged.rename(columns={"modify_date": "effective_from"})
    else:
        merged["effective_from"] = None
    merged["effective_to"] = None  # extend as relisting data becomes available

    result = merged[["corp_code", "ticker", "corp_name", "market", "effective_from", "effective_to"]].copy()
    result = result.drop_duplicates(subset=["corp_code", "ticker"])

    out = RAW_KRX / "corp_ticker_map.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False, encoding="utf-8-sig")
    log.info("Corp-ticker map: %d rows", len(result))
    return result


def run(
    market: str,
    start_date: str,
    end_date: str,
    ticker: str | None = None,
    dart_corp_list: list[dict] | None = None,
) -> None:
    """
    Main KRX extraction run.

    If ticker is given, fetches only that ticker.
    Otherwise fetches all tickers in market.
    dart_corp_list is used to build the corp_ticker map; if None, map is skipped.
    """
    # Normalise dates to YYYYMMDD (accept YYYY-MM-DD too)
    start_date = start_date.replace("-", "")
    end_date = end_date.replace("-", "")

    if ticker:
        tickers = [ticker]
    else:
        krx_df = fetch_listed_companies(market)
        tickers = krx_df["ticker"].tolist()

        if dart_corp_list:
            build_corp_ticker_map(dart_corp_list, krx_df)

    total = len(tickers)
    for i, tkr in enumerate(tickers, 1):
        log.info("[%d/%d] %s OHLCV + short", i, total, tkr)
        fetch_ohlcv(tkr, start_date, end_date)
        time.sleep(0.3)
        fetch_short_balance(tkr, start_date, end_date)
        time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract KRX OHLCV + short selling data")
    parser.add_argument("--market", default="KOSDAQ", choices=["KOSDAQ", "KOSPI", "KONEX"])
    parser.add_argument("--start", default="20200101", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="20251231", help="End date YYYYMMDD")
    parser.add_argument("--ticker", help="Single KRX ticker (6-digit)")
    args = parser.parse_args()
    run(args.market, args.start, args.end, args.ticker)
