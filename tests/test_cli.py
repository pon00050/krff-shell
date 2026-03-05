"""Smoke tests for the krff Typer CLI."""

import pathlib

import pytest
from typer.testing import CliRunner

from cli import app

runner = CliRunner()

ROOT      = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "01_Data" / "processed"


def test_cli_help():
    """--help exits 0 and lists all 4 subcommands."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("run", "analyze", "charts", "version"):
        assert cmd in result.output, f"Expected '{cmd}' in --help output"


def test_cli_version():
    """version prints the package version string."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "kr-forensic-finance" in result.output
    assert "1.5.0" in result.output


def test_cli_analyze_with_data():
    """analyze exits 0 and prints row/company summary when parquet exists."""
    p = PROCESSED / "beneish_scores.parquet"
    if not p.exists():
        pytest.skip("beneish_scores.parquet not found — run the pipeline first")

    result = runner.invoke(app, ["analyze"])
    assert result.exit_code == 0, f"krff analyze failed:\n{result.output}"
    assert "rows" in result.output
    assert "companies" in result.output
