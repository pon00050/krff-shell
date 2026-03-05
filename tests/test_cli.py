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


def test_cli_report_in_help():
    """'report' appears in krff --help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "report" in result.output


def test_cli_report_missing_corp_code():
    """krff report with no argument exits non-zero."""
    result = runner.invoke(app, ["report"])
    assert result.exit_code != 0


def test_cli_report_smoke(tmp_path, monkeypatch):
    """With monkeypatched generate_report and --skip-claude, prints 'Wrote' and exits 0."""
    import src.report as rpt

    def fake_generate_report(corp_code, output_path=None, skip_claude=False):
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("<html><body>test report</body></html>", encoding="utf-8")
            return output_path
        fallback = tmp_path / f"{corp_code}_report.html"
        fallback.write_text("<html><body>test report</body></html>", encoding="utf-8")
        return fallback

    monkeypatch.setattr(rpt, "generate_report", fake_generate_report)
    result = runner.invoke(
        app, ["report", "01051092", "--skip-claude", "--output-dir", str(tmp_path)]
    )
    assert result.exit_code == 0, f"Expected exit 0:\n{result.output}\n{result.exception}"
    assert "Wrote" in result.output
