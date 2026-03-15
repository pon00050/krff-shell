"""
extract_corp_actions.py — Extract capital reduction (감자결정) events from DART.

Endpoint: https://opendart.fss.or.kr/api/crDecsn.json  (DS005 #2020026)

Share consolidations (주식병합) are reported as 감자결정. This extractor
captures the shares-before and shares-after counts, allowing downstream
consumers to compute cumulative adjustment factors for price/exercise-price
denomination alignment.

Why this exists:
  pykrx adjusted=True retroactively scales historical prices by all
  consolidation factors, but DART exercise prices (cv_prc) remain at the
  original filing denomination. Without adjustment factors, moneyness (S/K)
  is inflated by the consolidation ratio for affected tickers.

Output:
  01_Data/processed/corp_actions.parquet
  Columns: corp_code, rcept_no, effective_date, shares_before, shares_after,
           reduction_ratio, method

Usage:
  python 02_Pipeline/extract_corp_actions.py
  python 02_Pipeline/extract_corp_actions.py --sample 10 --sleep 0.5
"""

from __future__ import annotations

import argparse
import datetime
import logging
import re
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from _pipeline_helpers import (
    DART_STATUS_NOT_FOUND,
    DART_STATUS_OK,
    _dart_api_key,
    _norm_corp_code,
    fetch_with_backoff,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "01_Data" / "processed"

DART_CR_URL = "https://opendart.fss.or.kr/api/crDecsn.json"
SLEEP_DEFAULT = 0.5


def _parse_int(raw) -> int | None:
    """Parse a comma-formatted integer string."""
    if not raw:
        return None
    s = str(raw).strip().replace(",", "")
    if not s or s == "-":
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _parse_date(raw) -> str | None:
    """Parse DART date (YYYYMMDD or '2022년 06월 27일') to ISO YYYY-MM-DD."""
    if not raw:
        return None
    raw = str(raw).strip()
    if raw == "-":
        return None
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", raw)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    dt = pd.to_datetime(raw, errors="coerce")
    return str(dt.date()) if not pd.isna(dt) else None


def _parse_float(raw) -> float | None:
    """Parse a percentage or decimal string."""
    if not raw:
        return None
    s = str(raw).strip().replace(",", "").replace("%", "")
    if not s or s == "-":
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_response(data: dict, corp_code: str) -> list[dict]:
    """Parse a crDecsn.json response into rows."""
    status = str(data.get("status", ""))
    if status == DART_STATUS_NOT_FOUND:
        return []
    if status not in (DART_STATUS_OK, ""):
        log.debug("DART status %s for corp_code=%s", status, corp_code)
        return []

    items = data.get("list", [])
    if not items:
        return []

    rows = []
    for item in items:
        shares_before = _parse_int(item.get("bfcr_tisstk_ostk"))
        shares_after = _parse_int(item.get("atcr_tisstk_ostk"))

        rows.append({
            "corp_code": corp_code,
            "rcept_no": item.get("rcept_no", ""),
            "effective_date": _parse_date(item.get("cr_std")),
            "shares_before": shares_before,
            "shares_after": shares_after,
            "reduction_ratio": _parse_float(item.get("cr_rt_ostk")),
            "method": (item.get("cr_mth") or "").strip(),
        })

    return rows


def fetch_corp_actions(
    force: bool = False,
    sample: int | None = None,
    sleep: float = SLEEP_DEFAULT,
) -> pd.DataFrame:
    """Fetch capital reduction events for all companies in cb_bw_events.parquet.

    Queries only corp_codes that have CB/BW issuances, since those are the
    only ones where denomination mismatch matters.
    """
    out = PROCESSED / "corp_actions.parquet"
    if out.exists() and not force:
        log.info("corp_actions.parquet exists, loading cached (use --force to refresh)")
        return pd.read_parquet(out)

    cb_path = PROCESSED / "cb_bw_events.parquet"
    if not cb_path.exists():
        raise FileNotFoundError(
            "cb_bw_events.parquet not found. Run extract_cb_bw.py first."
        )

    cb = pd.read_parquet(cb_path)
    corp_codes = sorted(cb["corp_code"].astype(str).str.zfill(8).unique())
    if sample is not None:
        corp_codes = corp_codes[:sample]

    log.info("Querying DART crDecsn.json for %d corp_codes...", len(corp_codes))

    api_key = _dart_api_key()
    all_rows: list[dict] = []
    hits = 0

    for i, cc in enumerate(corp_codes, 1):
        if i % 100 == 0 or i == 1:
            log.info("Corp action fetch %d/%d (hits so far: %d)", i, len(corp_codes), hits)

        try:
            data = fetch_with_backoff(
                DART_CR_URL,
                params={
                    "crtfc_key": api_key,
                    "corp_code": cc,
                    "bgn_de": "20150101",
                    "end_de": datetime.date.today().strftime("%Y%m%d"),
                },
            )
            rows = _parse_response(data, cc)
            if rows:
                hits += 1
                all_rows.extend(rows)
        except Exception as exc:
            log.warning("Error for corp_code=%s: %s", cc, exc)

        time.sleep(sleep)

    columns = [
        "corp_code", "rcept_no", "effective_date",
        "shares_before", "shares_after", "reduction_ratio", "method",
    ]
    df = pd.DataFrame(all_rows, columns=columns) if all_rows else pd.DataFrame(columns=columns)

    # Deduplicate by (corp_code, rcept_no)
    before = len(df)
    df = df.drop_duplicates(subset=["corp_code", "rcept_no"])
    if len(df) < before:
        log.info("Dropped %d duplicate rows", before - len(df))

    PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    log.info(
        "Written %d corp action events (%d companies with actions) to %s",
        len(df), hits, out,
    )
    return df


def main():
    parser = argparse.ArgumentParser(description="Extract capital reduction events from DART")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=SLEEP_DEFAULT)
    args = parser.parse_args()

    fetch_corp_actions(force=args.force, sample=args.sample, sleep=args.sleep)


def _configure_stdout() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass


if __name__ == "__main__":
    _configure_stdout()
    main()
