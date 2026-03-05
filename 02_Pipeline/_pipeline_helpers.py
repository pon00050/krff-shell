"""
_pipeline_helpers.py — Shared utilities for pipeline extractor scripts.

Imported by extract_cb_bw.py, extract_disclosures.py, extract_officer_holdings.py,
extract_seibro_repricing.py, extract_bondholder_register.py, and
extract_revenue_schedule.py to avoid duplicating boilerplate.
"""

from __future__ import annotations

import os


def _dart_api_key() -> str:
    """Retrieve and validate DART_API_KEY from environment."""
    key = os.getenv("DART_API_KEY", "")
    if not key or key == "your_opendart_api_key_here":
        raise EnvironmentError("DART_API_KEY not set.")
    return key


def _norm_corp_code(code) -> str:
    """Normalise a corp_code to an 8-character zero-padded string."""
    return str(code).zfill(8)


# Browser-like headers for DART HTML viewer requests
DART_HTML_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://dart.fss.or.kr/",
}


def _parse_krw(raw, unit_multiplier: int = 1) -> int | None:
    """Parse a KRW integer from raw table cell value. Handles comma formatting,
    parenthetical negatives, and unit multiplier (e.g. 1000 for 천원 tables)."""
    if not raw or not str(raw).strip():
        return None
    s = str(raw).strip().replace(",", "").replace("%", "")
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1]
    try:
        val = int(float(s))
        return -val * unit_multiplier if negative else val * unit_multiplier
    except (ValueError, TypeError):
        return None


def _detect_unit_multiplier(html: str) -> int:
    """Return 1000 if the first 2000 chars of html mention 천원, else 1."""
    snippet = html[:2000]
    if "천원" in snippet or "(단위: 천원)" in snippet:
        return 1000
    return 1
