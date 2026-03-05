"""
build_isin_map.py — Build bond_isin_map.parquet: corp_code → CB/BW bond ISINs.

SEIBRO StockSvc endpoints require a 12-character bond ISIN (bondIsin parameter).
DART DS005 does not return ISINs in the CB/BW event response, so this script
builds the lookup table from DART CB/BW filing documents.

Strategy:
  1. Read cb_bw_events.parquet for the set of corp_codes with known CB/BW events
  2. For each corp_code, search DART for CB/BW major disclosures (kind="B")
  3. For each filing, fetch the document HTML and extract ISINs via regex
  4. Deduplicate and save to bond_isin_map.parquet

ISIN format: Korean bond ISINs are 12 chars — "KR" + 10 alphanumeric (e.g. KR62797117B7).
CB/BW ISINs typically start with "KR6".

Output:
  01_Data/processed/bond_isin_map.parquet
    Columns: corp_code (str, 8-char), bond_isin (str, 12-char)

Usage:
  python 02_Pipeline/build_isin_map.py
  python 02_Pipeline/build_isin_map.py --sample 20 --sleep 0.5
  python 02_Pipeline/build_isin_map.py --corp-codes 01051092,01207761
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
import time
from pathlib import Path

import opendartreader as odr
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "01_Data" / "processed"
RAW_DIR = ROOT / "01_Data" / "raw" / "dart" / "isin_map"

# Korean bond ISIN: "KR" + 10 uppercase alphanumeric chars
ISIN_RE = re.compile(r"\bKR[0-9A-Z]{10}\b")

# DART date range to search for CB/BW filings
DART_START = "20190101"
DART_END = "20241231"

# CB/BW-related keywords in DART report names
CB_KEYWORDS = ["전환사채", "신주인수권부사채", "교환사채"]

DART_HTML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://dart.fss.or.kr/",
}


def _dart_api_key() -> str:
    import os
    key = os.getenv("DART_API_KEY", "")
    if not key or key == "your_opendart_api_key_here":
        raise EnvironmentError("DART_API_KEY not set. Add to .env.")
    return key


def _get_cb_filings(dart, corp_code: str) -> list[tuple[str, str]]:
    """
    Return list of (rcept_no, rcept_dt) for CB/BW filings.
    kind="B" = 주요사항보고서 (material disclosures, includes CB/BW issuance).
    """
    try:
        df = dart.list(corp_code, start=DART_START, end=DART_END, kind="B")
    except Exception as exc:
        log.debug("dart.list failed for %s: %s", corp_code, exc)
        return []
    if df is None or len(df) == 0:
        return []
    mask = df["report_nm"].str.contains("|".join(CB_KEYWORDS), na=False)
    relevant = df[mask]
    return [
        (str(row["rcept_no"]).strip(), str(row["rcept_dt"]).strip())
        for _, row in relevant.iterrows()
        if str(row.get("rcept_no", "")).strip()
    ]


def _extract_isins_from_filing(
    dart, rcept_no: str, cache_dir: Path, sleep: float
) -> set[str]:
    """
    Fetch sub-documents for rcept_no and search HTML for ISIN patterns.

    Returns set of ISIN strings found (may be empty).
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        sub_df = dart.sub_docs(rcept_no)
    except Exception as exc:
        log.debug("dart.sub_docs failed for %s: %s", rcept_no, exc)
        return set()

    if sub_df is None or len(sub_df) == 0:
        return set()

    # Try URL column (may be "url" or last column)
    if "url" in sub_df.columns:
        urls = sub_df["url"].dropna().tolist()
    else:
        urls = sub_df.iloc[:, -1].dropna().tolist()

    found_isins: set[str] = set()
    for url in urls[:5]:  # cap at 5 sub-docs per filing
        url = str(url)
        if not url.startswith("http"):
            continue
        cache_path = cache_dir / f"{rcept_no}_{abs(hash(url)) % 100000}.html"
        if cache_path.exists():
            html = cache_path.read_text(encoding="utf-8", errors="ignore")
        else:
            try:
                resp = requests.get(url, headers=DART_HTML_HEADERS, timeout=30)
                if resp.status_code != 200:
                    time.sleep(sleep)
                    continue
                html = resp.text
                cache_path.write_text(html, encoding="utf-8")
                time.sleep(sleep)
            except Exception as exc:
                log.debug("HTML fetch failed for %s: %s", url, exc)
                time.sleep(sleep)
                continue

        isins = ISIN_RE.findall(html)
        # Prefer CB/BW ISINs (KR6 prefix is common for Korean convertible bonds)
        cb_isins = [i for i in isins if i.startswith("KR6")]
        if cb_isins:
            found_isins.update(cb_isins)
        elif isins:
            # Accept any KR ISIN if no KR6 found — filter out equity ISINs later
            found_isins.update(isins)

        if found_isins:
            break  # found ISINs in this sub-doc; no need to check remaining

    return found_isins


def fetch_isins_for_corp(
    dart, corp_code: str, sleep: float
) -> list[str]:
    """
    Return list of unique bond ISINs for corp_code found in DART filings.
    """
    filings = _get_cb_filings(dart, corp_code)
    if not filings:
        log.debug("No CB/BW filings for %s", corp_code)
        return []

    cache_dir = RAW_DIR / corp_code
    all_isins: set[str] = set()
    for rcept_no, rcept_dt in filings[:10]:  # cap at 10 filings per company
        isins = _extract_isins_from_filing(dart, rcept_no, cache_dir, sleep)
        all_isins.update(isins)
        if isins:
            log.debug("  %s (%s): found %s", rcept_no, rcept_dt, isins)

    return sorted(all_isins)


def build_isin_map(
    corp_codes: list[str],
    sleep: float = 0.5,
    append: bool = False,
) -> pd.DataFrame:
    """
    Build bond_isin_map.parquet for the given corp_codes.

    append=True: extend existing parquet instead of overwriting.
    """
    api_key = _dart_api_key()
    dart = odr.OpenDartReader(api_key)

    rows: list[dict] = []
    for i, corp_code in enumerate(corp_codes, 1):
        cc = str(corp_code).zfill(8)
        log.info("[%d/%d] ISIN lookup: %s", i, len(corp_codes), cc)
        isins = fetch_isins_for_corp(dart, cc, sleep)
        if isins:
            log.info("  Found %d ISINs: %s", len(isins), isins)
            for isin in isins:
                rows.append({"corp_code": cc, "bond_isin": isin})
        else:
            log.info("  No ISINs found in DART filings")

    new_df = pd.DataFrame(rows, columns=["corp_code", "bond_isin"])

    out_path = PROCESSED / "bond_isin_map.parquet"
    if append and out_path.exists():
        existing = pd.read_parquet(out_path)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["corp_code", "bond_isin"])
        combined.to_parquet(out_path, index=False)
        log.info(
            "Updated bond_isin_map.parquet: %d rows (was %d, added %d)",
            len(combined), len(existing), len(new_df),
        )
        return combined
    else:
        new_df.to_parquet(out_path, index=False)
        log.info(
            "Saved bond_isin_map.parquet: %d rows (%d corp_codes with ISINs)",
            len(new_df), new_df["corp_code"].nunique() if not new_df.empty else 0,
        )
        return new_df


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build bond_isin_map.parquet: corp_code → CB/BW bond ISINs via DART"
    )
    parser.add_argument(
        "--sample", type=int, default=None,
        help="Limit to first N corp_codes from cb_bw_events.parquet",
    )
    parser.add_argument(
        "--corp-codes", type=str, default=None,
        help="Comma-separated corp_codes to process (e.g. 01051092,01207761)",
    )
    parser.add_argument(
        "--sleep", type=float, default=0.5,
        help="Seconds between DART HTML fetches (default: 0.5)",
    )
    parser.add_argument(
        "--append", action="store_true",
        help="Append to existing bond_isin_map.parquet instead of overwriting",
    )
    args = parser.parse_args()

    if args.corp_codes:
        corp_codes = [c.strip().zfill(8) for c in args.corp_codes.split(",") if c.strip()]
        log.info("Processing %d specified corp_codes", len(corp_codes))
    else:
        cb_path = PROCESSED / "cb_bw_events.parquet"
        if not cb_path.exists():
            log.error("cb_bw_events.parquet not found. Run extract_cb_bw.py first.")
            sys.exit(1)
        df = pd.read_parquet(cb_path)
        corp_codes = df["corp_code"].astype(str).str.zfill(8).unique().tolist()
        log.info("Loaded %d unique corp_codes from cb_bw_events.parquet", len(corp_codes))

    if args.sample is not None:
        corp_codes = corp_codes[: args.sample]
        log.info("--sample %d: processing %d corp_codes", args.sample, len(corp_codes))

    build_isin_map(corp_codes, sleep=args.sleep, append=args.append)


if __name__ == "__main__":
    main()
