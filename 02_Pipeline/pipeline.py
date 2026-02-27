"""
pipeline.py — Phase 1 ETL orchestrator.

Calls extract_dart → transform in dependency order.
All steps are idempotent: re-running is safe and skips existing files.

Phase 1 stages:
    dart       Build KOSDAQ universe + fetch annual financial statements (2019–2023)
    transform  Raw Parquet → company_financials.parquet

Phase 2/3 stages (KRX, SEIBRO, KFTC) are not implemented yet.
Run `--stage dart` and `--stage transform` independently to control quota usage.

Usage:
    # Full Phase 1 run
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023

    # DART extraction only (financials + sector)
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023 --stage dart

    # Transform only (after extraction is complete)
    python 02_Pipeline/pipeline.py --start 2019 --end 2023 --stage transform

    # Single company test
    python 02_Pipeline/pipeline.py --stage dart --corp-code 00126380 --start 2019 --end 2023

    # Sample mode (first 50 companies — ~4 min, good for development)
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2022 --end 2023 --sample 50
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))],
)
log = logging.getLogger(__name__)

# Ensure 02_Pipeline/ is importable regardless of working directory
_PIPELINE_DIR = Path(__file__).parent
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))


def run_stage_dart(
    market: str,
    start: int,
    end: int,
    stage: str | None,
    corp_code: str | None,
    force: bool,
    sample: int | None = None,
    max_minutes: float | None = None,
    sleep: float | None = None,
) -> None:
    """
    Run DART extraction stages.

    `stage` here refers to sub-stages within extract_dart:
      'company-list' | 'financials' | 'sector' | None (all three)

    sample: if set, limit the company universe to the first N companies.
    max_minutes: hard wall-clock deadline for the financials fetch loop.
    sleep: override all sleep constants (test mode).
    """
    import extract_dart as ed

    if sleep is not None:
        ed._apply_sleep_override(sleep)

    if corp_code:
        # Single-company test mode
        log.info("Single-company mode: %s", corp_code)
        dart = ed._dart()
        companies = ed.fetch_company_list(market=market, force=force)
        comp_row = companies[companies["corp_code"] == corp_code]
        if comp_row.empty:
            log.error("corp_code %s not in %s universe", corp_code, market)
            return
        corp_name = comp_row.iloc[0]["corp_name"]
        years = list(range(start, end + 1))
        results = ed.fetch_financials_for_company(
            corp_code, corp_name, years, dart, force=force
        )
        log.info("Results for %s: %s", corp_code, results)
        return

    if stage in (None, "company-list"):
        ed.fetch_company_list(market=market, force=force)

    if stage in (None, "financials"):
        companies = ed.fetch_company_list(market=market, force=False)
        summary = ed.fetch_all_financials(
            companies, start_year=start, end_year=end,
            force=force, sample=sample, max_minutes=max_minutes,
        )
        # Write run summary
        import json
        out = Path("01_Data/raw/run_summary.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        log.info(
            "Run summary: %d full, %d partial, %d no-data, %d errors",
            len(summary.get("full_data", [])),
            len(summary.get("partial_data", [])),
            len(summary.get("no_data", [])),
            len(summary.get("errors", [])),
        )

    if stage in (None, "sector"):
        companies = ed.fetch_company_list(market=market, force=False)
        ed.fetch_wics(force=force)
        ed.fetch_ksic(companies, force=force, sample=sample)


def run_stage_transform(start: int, end: int, sample: int | None = None) -> None:
    """Run transform.py to build company_financials.parquet."""
    import transform as tr
    log.info("=== Stage: transform (%d–%d) ===", start, end)
    tr.run(start_year=start, end_year=end, sample=sample)


def run(
    market: str = "KOSDAQ",
    start: int = 2019,
    end: int = 2023,
    stage: str | None = None,
    corp_code: str | None = None,
    force: bool = False,
    sample: int | None = None,
    max_minutes: float | None = None,
    sleep: float | None = None,
) -> None:
    """
    Run the Phase 1 pipeline.

    stage: 'dart' | 'transform' | None (both in sequence)
    """
    log.info(
        "=== Pipeline: market=%s, years=%d–%d, stage=%s ===",
        market, start, end, stage or "all",
    )

    if stage == "dart":
        log.info("=== Stage: dart ===")
        run_stage_dart(
            market, start, end, stage=None, corp_code=corp_code,
            force=force, sample=sample, max_minutes=max_minutes, sleep=sleep,
        )
        return

    if stage == "transform":
        run_stage_transform(start, end, sample=sample)
        return

    # Full Phase 1 pipeline: dart → transform
    log.info("=== Stage: dart ===")
    run_stage_dart(
        market, start, end, stage=None, corp_code=corp_code,
        force=force, sample=sample, max_minutes=max_minutes, sleep=sleep,
    )

    log.info("=== Stage: transform ===")
    run_stage_transform(start, end, sample=sample)

    log.info("=== Phase 1 pipeline complete ===")
    log.info(
        "Next: python 03_Analysis/beneish_screen.py"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the kr-forensic-finance Phase 1 ETL pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Full Phase 1 run:
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023

  DART extraction only (leaves transform for later):
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023 --stage dart

  Transform only (after extraction is complete):
    python 02_Pipeline/pipeline.py --start 2019 --end 2023 --stage transform

  Re-fetch everything from scratch:
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023 --force

  Single company test (NAVER):
    python 02_Pipeline/pipeline.py --stage dart --corp-code 00126380 --start 2022 --end 2023

  Sample mode — first 50 companies, 2 years (~4 min):
    python 02_Pipeline/pipeline.py --market KOSDAQ --start 2022 --end 2023 --sample 50
        """,
    )
    parser.add_argument(
        "--market",
        default="KOSDAQ",
        choices=["KOSDAQ", "KOSPI", "KONEX"],
        help="Market to process (default: KOSDAQ)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=2019,
        help="First fiscal year, inclusive (default: 2019)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=2023,
        help="Last fiscal year, inclusive (default: 2023)",
    )
    parser.add_argument(
        "--stage",
        choices=["dart", "transform"],
        help="Run a single stage only (default: run both)",
    )
    parser.add_argument(
        "--corp-code",
        dest="corp_code",
        help="Run DART extraction for a single company (8-digit DART code)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch all data even if output files already exist",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        metavar="N",
        help="Limit universe to first N companies (for development/testing). "
             "~4 min for N=50, 5 years. Use before running the full universe.",
    )
    parser.add_argument(
        "--max-minutes",
        type=float,
        default=None,
        metavar="M",
        dest="max_minutes",
        help="Hard wall-clock deadline for the financials fetch loop (default: no limit). "
             "Use --max-minutes 3 for a guaranteed-short test run.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Override inter-request sleep (default: 0.5s/0.3s/1.0s per stage). "
             "Use --sleep 0.1 for test runs with --sample.",
    )

    args = parser.parse_args()
    run(
        market=args.market,
        start=args.start,
        end=args.end,
        stage=args.stage,
        corp_code=args.corp_code,
        force=args.force,
        sample=args.sample,
        max_minutes=args.max_minutes,
        sleep=args.sleep,
    )
