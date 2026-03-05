"""kr-forensic-finance CLI — entry point for the `krff` command.

Usage:
  krff run [OPTIONS]     Run the ETL pipeline
  krff analyze           Load and print beneish_scores.parquet
  krff charts            Generate beneish_viz.html from beneish_scores.parquet
  krff version           Print version
"""

from __future__ import annotations

import sys
from importlib.metadata import version as _pkg_version
from pathlib import Path
from typing import Optional

import typer

# Windows: force UTF-8 stdout/stderr so Korean company names don't crash cp1252
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass  # Python < 3.7 fallback

app = typer.Typer(
    name="krff",
    help="Korean forensic-finance pipeline CLI",
    add_completion=False,
)

_VERSION = _pkg_version("kr-forensic-finance")
_DEFAULT_PARQUET = Path(__file__).parent / "01_Data" / "processed" / "beneish_scores.parquet"
_ANALYSIS_DIR = Path(__file__).parent / "03_Analysis"


@app.command()
def run(
    market: str = typer.Option("KOSDAQ", help="Exchange market (KOSDAQ or KOSPI)"),
    start: int = typer.Option(2019, help="Start year"),
    end: int = typer.Option(2023, help="End year"),
    stage: Optional[str] = typer.Option(None, help="Pipeline stage: dart | transform | cb_bw (default: dart + transform)"),
    corp_code: Optional[str] = typer.Option(None, help="Single corp_code to process"),
    force: bool = typer.Option(False, "--force", help="Re-download even if cached"),
    sample: Optional[int] = typer.Option(None, help="Limit to N companies (smoke test)"),
    max_minutes: Optional[float] = typer.Option(None, help="Hard time limit in minutes"),
    sleep: Optional[float] = typer.Option(None, help="Sleep seconds between API calls"),
    wics_date: Optional[str] = typer.Option(None, help="WICS snapshot date (YYYYMMDD)"),
    scoped: bool = typer.Option(False, "--scoped", help="Limit cb_bw stage to top-N flagged"),
    top_n: int = typer.Option(100, help="Top-N for scoped cb_bw stage"),
) -> None:
    """Run the ETL pipeline (DART extraction + transform)."""
    from src.pipeline import run_pipeline

    run_pipeline(
        market=market,
        start=start,
        end=end,
        stage=stage,
        corp_code=corp_code,
        force=force,
        sample=sample,
        max_minutes=max_minutes,
        sleep=sleep,
        wics_date=wics_date,
        scoped=scoped,
        top_n=top_n,
    )


@app.command()
def analyze(
    parquet: Optional[Path] = typer.Option(None, help="Path to beneish_scores.parquet"),
) -> None:
    """Load beneish_scores.parquet and print a summary."""
    from src.analysis import run_beneish_screen

    path = parquet or _DEFAULT_PARQUET
    if not path.exists():
        typer.echo(f"Error: {path} not found. Run 'krff run' then 'python 03_Analysis/beneish_screen.py' first.", err=True)
        raise typer.Exit(code=1)

    df = run_beneish_screen(path)
    typer.echo(df.to_string())
    typer.echo(f"\n{len(df):,} rows · {df['corp_code'].nunique():,} companies · {int(df['flag'].sum()):,} flagged")


@app.command()
def charts(
    parquet: Optional[Path] = typer.Option(None, help="Path to beneish_scores.parquet"),
    output_dir: Optional[Path] = typer.Option(None, help="Directory for beneish_viz.html (default: 03_Analysis/)"),
) -> None:
    """Generate beneish_viz.html from beneish_scores.parquet."""
    from src.analysis import run_beneish_screen
    from src.charts import generate_charts

    path = parquet or _DEFAULT_PARQUET
    if not path.exists():
        typer.echo(f"Error: {path} not found. Run 'krff run' then 'krff analyze' first.", err=True)
        raise typer.Exit(code=1)

    df = run_beneish_screen(path)
    out_dir = output_dir or _ANALYSIS_DIR
    out_path = generate_charts(df, out_dir)
    typer.echo(f"Wrote {out_path} ({out_path.stat().st_size / 1024:.0f} KB)")


@app.command()
def report(
    corp_code: str = typer.Argument(..., help="DART 8-digit corp code, e.g. 01051092"),
    output_dir: Optional[Path] = typer.Option(None, help="Output dir (default: 03_Analysis/reports/)"),
    skip_claude: bool = typer.Option(False, "--skip-claude", help="Skip Claude API synthesis"),
) -> None:
    """Generate a self-contained HTML forensic report for one company."""
    from src.report import generate_report

    out_path = (output_dir or (_ANALYSIS_DIR / "reports")) / f"{corp_code.zfill(8)}_report.html"
    typer.echo(f"Generating report for corp_code={corp_code}...")
    result = generate_report(corp_code=corp_code, output_path=out_path, skip_claude=skip_claude)
    typer.echo(f"Wrote {result} ({result.stat().st_size / 1024:.0f} KB)")


@app.command()
def version() -> None:
    """Print kr-forensic-finance version."""
    typer.echo(f"kr-forensic-finance v{_VERSION}")


if __name__ == "__main__":
    app()
