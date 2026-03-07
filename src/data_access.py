"""src/data_access.py — Reusable data loading functions.

Extracted from src/report.py so that future FastAPI endpoints, CLI commands,
and analysis scripts can load data without depending on the report module.

Usage:
    from src.data_access import load_parquet, load_csv, load_company_name
    df = load_parquet("beneish_scores.parquet", corp_code="01051092")
    df_all = load_parquet("beneish_scores.parquet")  # all rows
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src._paths import PROJECT_ROOT, PROCESSED_DIR

log = logging.getLogger(__name__)

# ─── Path constants ────────────────────────────────────────────────────────────
ANALYSIS_DIR = PROJECT_ROOT / "03_Analysis"
CB_BW_CSV = ANALYSIS_DIR / "cb_bw_summary.csv"
TIMING_CSV = ANALYSIS_DIR / "timing_anomalies.csv"
NETWORK_CSV = ANALYSIS_DIR / "officer_network" / "centrality_report.csv"


def load_parquet(
    name: str,
    corp_code: str | None = None,
    sort_by: str | None = None,
    processed_dir: Path | None = None,
) -> pd.DataFrame:
    """Load a parquet table from processed dir, optionally filtered to one corp_code."""
    proc = processed_dir or PROCESSED_DIR
    p = proc / name
    if not p.exists():
        return pd.DataFrame()
    try:
        df = pd.read_parquet(p)
        if corp_code is not None:
            if "corp_code" not in df.columns:
                return pd.DataFrame()
            mask = df["corp_code"].astype(str).str.zfill(8) == corp_code
            df = df[mask]
        if sort_by and sort_by in df.columns:
            df = df.sort_values(sort_by)
        return df.reset_index(drop=True)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as exc:
        log.warning("Error loading %s for %s: %s", name, corp_code, exc)
        return pd.DataFrame()


def load_csv(path: Path, corp_code: str | None = None) -> pd.DataFrame:
    """Load a CSV analysis output, optionally filtered to one corp_code."""
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
        if corp_code is not None:
            if "corp_code" not in df.columns:
                return pd.DataFrame()
            mask = df["corp_code"].astype(str).str.zfill(8) == corp_code
            df = df[mask]
        return df.reset_index(drop=True)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as exc:
        log.warning("Error loading %s for %s: %s", path.name, corp_code, exc)
        return pd.DataFrame()


def load_company_name(
    corp_code: str,
    beneish_df: pd.DataFrame | None = None,
    processed_dir: Path | None = None,
) -> str:
    """Extract company name from pre-loaded beneish data or corp_ticker_map."""
    if beneish_df is not None and not beneish_df.empty and "company_name" in beneish_df.columns:
        val = beneish_df["company_name"].iloc[0]
        if pd.notna(val) and str(val).strip():
            return str(val).strip()
    proc = processed_dir or PROCESSED_DIR
    p2 = proc / "corp_ticker_map.parquet"
    if p2.exists():
        try:
            df2 = pd.read_parquet(p2)
            mask2 = df2["corp_code"].astype(str).str.zfill(8) == corp_code
            rows2 = df2[mask2]
            if not rows2.empty:
                for col in ("company_name", "corp_name", "name"):
                    if col in rows2.columns:
                        val = rows2[col].iloc[0]
                        if pd.notna(val) and str(val).strip():
                            return str(val).strip()
        except FileNotFoundError:
            pass
        except Exception as exc:
            log.warning("Error loading company name from corp_ticker_map for %s: %s", corp_code, exc)
    return corp_code


def load_officer_network(
    corp_code: str,
    network_csv: Path | None = None,
) -> pd.DataFrame:
    """Load officer network CSV with token-match filtering on 'companies' column."""
    csv_path = network_csv or NETWORK_CSV
    if not csv_path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        if "companies" not in df.columns:
            return pd.DataFrame()
        mask = df["companies"].apply(
            lambda val: corp_code in [c.strip() for c in str(val).split(",")]
            if pd.notna(val) else False
        )
        return df[mask].reset_index(drop=True)
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as exc:
        log.warning("Error loading officer_network for %s: %s", corp_code, exc)
        return pd.DataFrame()


__all__ = [
    "load_parquet",
    "load_csv",
    "load_company_name",
    "load_officer_network",
    "ANALYSIS_DIR",
    "CB_BW_CSV",
    "TIMING_CSV",
    "NETWORK_CSV",
]
