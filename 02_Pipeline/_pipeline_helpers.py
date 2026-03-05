"""
_pipeline_helpers.py — Shared utilities for pipeline extractor scripts.

Imported by extract_cb_bw.py, extract_disclosures.py, extract_officer_holdings.py,
and extract_seibro_repricing.py to avoid duplicating boilerplate.
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
