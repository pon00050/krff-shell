"""
extract_seibro.py — SEIBRO CB/BW data extraction layer.

SEIBRO (seibro.or.kr) provides convertible bond (CB) and bond with warrant (BW)
issuance terms and exercise/conversion history.

API vs. scraping strategy:
  - SEIBRO has a partial OpenAPI at https://seibro.or.kr/websquare/service/
  - Endpoint availability changes without notice — this module tries the API first
    and falls back to HTML scraping for endpoints that return errors or empty responses.
  - All HTML scraping uses BeautifulSoup on publicly accessible pages.
  - Rate limiting: 1 request/sec to avoid triggering SEIBRO's IP throttle.

Output: 01_Data/raw/seibro/{corp_code}/ — JSON per fetch type.

Usage:
    python 02_Pipeline/extract_seibro.py --corp-code 00126380
    python 02_Pipeline/extract_seibro.py --corp-codes-file 01_Data/raw/dart/cb_bw_corp_codes.txt
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

RAW_SEIBRO = Path("01_Data/raw/seibro")

# SEIBRO base URLs — subject to change; update if scraping breaks.
SEIBRO_BASE = "https://seibro.or.kr"
SEIBRO_API = f"{SEIBRO_BASE}/websquare/service/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; kr-forensic-research/0.1; "
        "educational/research use; contact: see project README)"
    ),
    "Accept": "application/json, text/html",
    "Referer": SEIBRO_BASE,
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def _get(url: str, params: dict | None = None, timeout: int = 15) -> requests.Response:
    """GET with retry and rate limit."""
    for attempt in range(1, 4):
        try:
            resp = SESSION.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            time.sleep(1.0)  # SEIBRO rate limit
            return resp
        except requests.RequestException as exc:
            if attempt == 3:
                raise
            log.warning("GET attempt %d failed: %s — retrying", attempt, exc)
            time.sleep(2.0)
    raise RuntimeError("Unreachable")


def _post(url: str, data: dict, timeout: int = 15) -> requests.Response:
    """POST with retry and rate limit."""
    for attempt in range(1, 4):
        try:
            resp = SESSION.post(url, data=data, timeout=timeout)
            resp.raise_for_status()
            time.sleep(1.0)
            return resp
        except requests.RequestException as exc:
            if attempt == 3:
                raise
            log.warning("POST attempt %d failed: %s — retrying", attempt, exc)
            time.sleep(2.0)
    raise RuntimeError("Unreachable")


def fetch_cb_issuance_terms(corp_code: str) -> list[dict]:
    """
    Fetch CB (전환사채) issuance conditions and repricing history for corp_code.

    Strategy: POST to SEIBRO OpenAPI bond search endpoint. Falls back to
    HTML scrape of the public CB search page if API returns no data.

    Output: 01_Data/raw/seibro/{corp_code}/cb_issuance_terms.json
    """
    log.info("Fetching CB issuance terms: %s", corp_code)
    results: list[dict] = []

    # Attempt API call
    try:
        api_url = f"{SEIBRO_API}BondService"
        payload = {
            "W2XPOP_CMD": "getCBList",
            "isuCd": corp_code,
            "pageSize": "100",
            "pageNo": "1",
        }
        resp = _post(api_url, payload)
        data = resp.json()
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict) and "list" in data:
            results = data["list"]
    except Exception as exc:
        log.warning("SEIBRO API CB terms failed for %s: %s — trying HTML scrape", corp_code, exc)

    # HTML scrape fallback
    if not results:
        try:
            url = f"{SEIBRO_BASE}/websquare/main.html#CB_issuance"
            params = {"isuCd": corp_code}
            resp = _get(url, params=params)
            soup = BeautifulSoup(resp.text, "html.parser")
            # Parse table rows — SEIBRO renders data in standard HTML tables
            table = soup.find("table", {"id": "grid1"}) or soup.find("table")
            if table:
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                for row in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if cells and len(cells) == len(headers):
                        results.append(dict(zip(headers, cells)))
            log.info("HTML scrape found %d CB records for %s", len(results), corp_code)
        except Exception as exc2:
            log.warning("SEIBRO HTML CB scrape failed for %s: %s", corp_code, exc2)

    out = RAW_SEIBRO / corp_code / "cb_issuance_terms.json"
    _write_json(out, {"corp_code": corp_code, "type": "CB", "records": results})
    return results


def fetch_bw_issuance_terms(corp_code: str) -> list[dict]:
    """
    Fetch BW (신주인수권부사채) warrant terms for corp_code.

    Same API/scrape strategy as CB.

    Output: 01_Data/raw/seibro/{corp_code}/bw_issuance_terms.json
    """
    log.info("Fetching BW issuance terms: %s", corp_code)
    results: list[dict] = []

    try:
        api_url = f"{SEIBRO_API}BondService"
        payload = {
            "W2XPOP_CMD": "getBWList",
            "isuCd": corp_code,
            "pageSize": "100",
            "pageNo": "1",
        }
        resp = _post(api_url, payload)
        data = resp.json()
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict) and "list" in data:
            results = data["list"]
    except Exception as exc:
        log.warning("SEIBRO API BW terms failed for %s: %s — trying HTML scrape", corp_code, exc)

    if not results:
        try:
            url = f"{SEIBRO_BASE}/websquare/main.html#BW_issuance"
            params = {"isuCd": corp_code}
            resp = _get(url, params=params)
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if table:
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                for row in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if cells and len(cells) == len(headers):
                        results.append(dict(zip(headers, cells)))
        except Exception as exc2:
            log.warning("SEIBRO HTML BW scrape failed for %s: %s", corp_code, exc2)

    out = RAW_SEIBRO / corp_code / "bw_issuance_terms.json"
    _write_json(out, {"corp_code": corp_code, "type": "BW", "records": results})
    return results


def fetch_exercise_history(corp_code: str) -> list[dict]:
    """
    Fetch 권리행사내역 (actual CB conversion / BW exercise events) for corp_code.

    These are the timestamps showing when bondholders actually converted or exercised,
    which can be cross-referenced with price peaks to detect coordinated pump-and-dump.

    Output: 01_Data/raw/seibro/{corp_code}/exercise_history.json
    """
    log.info("Fetching exercise history: %s", corp_code)
    results: list[dict] = []

    try:
        api_url = f"{SEIBRO_API}BondExerciseService"
        payload = {
            "W2XPOP_CMD": "getExerciseList",
            "isuCd": corp_code,
            "pageSize": "200",
            "pageNo": "1",
        }
        resp = _post(api_url, payload)
        data = resp.json()
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict) and "list" in data:
            results = data["list"]
    except Exception as exc:
        log.warning("SEIBRO API exercise history failed for %s: %s — trying HTML scrape", corp_code, exc)

    if not results:
        try:
            url = f"{SEIBRO_BASE}/websquare/main.html#CB_exercise"
            params = {"isuCd": corp_code}
            resp = _get(url, params=params)
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if table:
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                for row in table.find_all("tr")[1:]:
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    if cells and len(cells) == len(headers):
                        results.append(dict(zip(headers, cells)))
        except Exception as exc2:
            log.warning("SEIBRO HTML exercise history scrape failed for %s: %s", corp_code, exc2)

    out = RAW_SEIBRO / corp_code / "exercise_history.json"
    _write_json(out, {"corp_code": corp_code, "records": results})
    return results


def run(corp_codes: list[str]) -> None:
    """Fetch all SEIBRO data for the given corp_codes."""
    for i, code in enumerate(corp_codes, 1):
        log.info("[%d/%d] SEIBRO fetch: %s", i, len(corp_codes), code)
        fetch_cb_issuance_terms(code)
        fetch_bw_issuance_terms(code)
        fetch_exercise_history(code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract SEIBRO CB/BW data")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--corp-code", help="Single DART corp_code")
    group.add_argument(
        "--corp-codes-file",
        help="Path to text file with one corp_code per line",
    )
    args = parser.parse_args()

    if args.corp_code:
        codes = [args.corp_code]
    else:
        codes = Path(args.corp_codes_file).read_text(encoding="utf-8").splitlines()
        codes = [c.strip() for c in codes if c.strip()]

    run(codes)
