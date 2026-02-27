"""
test_pipeline_invariants.py — Guard tests for pipeline correctness invariants.

Three categories per the rationale in KNOWN_ISSUES.md and the project's
testing philosophy (see 00_Reference/Parallels_Between_Programming_and_Accounting.md):

  1. KSIC sample-preservation  — a --sample run must not destroy existing data
  2. Schema contracts           — company_financials columns, dtypes, no financial sector rows
  3. Beneish formula spot-check — known input → expected M-Score to 2 decimal places

These tests guard the three places where silent failure is most plausible.
They do not aim for comprehensive coverage — the acceptance criteria suite
(test_acceptance_criteria.py) covers downstream correctness.

Run:
    pytest tests/test_pipeline_invariants.py -v
"""

import pathlib
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

ROOT      = pathlib.Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "01_Data" / "processed"
RAW       = ROOT / "01_Data" / "raw"

# ─── Category 1: KSIC sample-preservation ────────────────────────────────────

class TestKsicSamplePreservation:
    """
    A --sample N run of fetch_ksic() must preserve all entries that already
    exist in ksic.parquet and not discard companies outside the sample window.

    Regression guard for the bug discovered Feb 27, 2026:
    sample run overwrote full ksic.parquet with only N rows.
    See KNOWN_ISSUES.md KI-004.
    """

    def _make_companies(self, corp_codes: list[str]) -> pd.DataFrame:
        return pd.DataFrame({"corp_code": corp_codes, "stock_code": corp_codes})

    def test_sample_run_preserves_existing_entries(self, tmp_path, monkeypatch):
        """
        Given: ksic.parquet already has 10 entries (the "full universe").
        When:  fetch_ksic() is called with sample=3 (first 3 companies only).
        Then:  the written parquet still contains all 10 entries.
        """
        import importlib, sys as _sys

        # Point RAW_SECTOR at tmp_path so we don't touch real data
        existing_codes = [f"CODE{i:04d}" for i in range(10)]
        existing_df = pd.DataFrame({
            "corp_code":   existing_codes,
            "induty_code": ["264"] * 10,
        })
        (tmp_path / "sector").mkdir()
        existing_df.to_parquet(tmp_path / "sector" / "ksic.parquet", index=False)

        # Patch RAW_SECTOR inside extract_dart before importing
        import extract_dart as ed
        monkeypatch.setattr(ed, "RAW_SECTOR", tmp_path / "sector")

        # Stub dart.company() to return a minimal object
        class _FakeInfo:
            induty_code = "264"
        class _FakeDart:
            def company(self, corp_code):
                return _FakeInfo()
        monkeypatch.setattr(ed, "_dart", lambda: _FakeDart())

        # Run with sample=3 — only first 3 of 10 companies
        all_companies = self._make_companies(existing_codes)
        ed.fetch_ksic(all_companies, force=False, sample=3)

        result = pd.read_parquet(tmp_path / "sector" / "ksic.parquet")
        assert len(result) == 10, (
            f"fetch_ksic with sample=3 wrote {len(result)} rows; "
            f"expected 10 (all pre-existing entries preserved)"
        )
        assert set(result["corp_code"]) == set(existing_codes), (
            "fetch_ksic with sample=3 dropped some pre-existing corp_codes"
        )

    def test_full_run_writes_all_companies(self, tmp_path, monkeypatch):
        """A full run (no sample) with no pre-existing file writes all companies."""
        import extract_dart as ed
        monkeypatch.setattr(ed, "RAW_SECTOR", tmp_path / "sector")
        (tmp_path / "sector").mkdir()

        class _FakeInfo:
            induty_code = "264"
        class _FakeDart:
            def company(self, corp_code):
                return _FakeInfo()
        monkeypatch.setattr(ed, "_dart", lambda: _FakeDart())
        monkeypatch.setattr(ed, "_sleep_ksic", 0)

        companies = self._make_companies([f"C{i:04d}" for i in range(5)])
        result = ed.fetch_ksic(companies, force=False, sample=None)
        assert len(result) == 5


# ─── Category 2: Schema contracts ────────────────────────────────────────────

class TestSchemaContracts:
    """
    company_financials.parquet must have the expected columns, numeric types,
    and no financial-sector rows. Guards against accidental schema drift that
    would silently break downstream Beneish calculations.
    """

    @pytest.fixture(scope="class")
    def financials(self):
        p = PROCESSED / "company_financials.parquet"
        if not p.exists():
            pytest.skip("company_financials.parquet not found — run the pipeline first")
        return pd.read_parquet(p)

    REQUIRED_COLUMNS = [
        "corp_code", "ticker", "company_name", "market", "year",
        "fs_type", "expense_method",
        "receivables", "revenue", "cogs", "sga", "ppe",
        "depreciation", "total_assets", "lt_debt", "net_income", "cfo",
        "wics_sector_code", "ksic_code",
    ]

    NUMERIC_COLUMNS = [
        "receivables", "revenue", "cogs", "sga", "ppe",
        "depreciation", "total_assets", "lt_debt", "net_income", "cfo",
    ]

    def test_required_columns_present(self, financials):
        missing = [c for c in self.REQUIRED_COLUMNS if c not in financials.columns]
        assert not missing, f"Missing columns in company_financials: {missing}"

    def test_extraction_date_format(self, financials):
        """extraction_date must be ISO 8601 (YYYY-MM-DD) when present.

        Skipped on the existing Phase 1 parquet (produced before PR2).
        Will be enforced after the next pipeline re-run.
        """
        if "extraction_date" not in financials.columns:
            pytest.skip("extraction_date not present — re-run pipeline to add it")
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        sample = financials["extraction_date"].dropna().head(20)
        bad = [v for v in sample if not pattern.match(str(v))]
        assert not bad, f"extraction_date values not ISO 8601: {bad}"

    def test_numeric_columns_are_float(self, financials):
        wrong_type = [
            c for c in self.NUMERIC_COLUMNS
            if c in financials.columns and not pd.api.types.is_float_dtype(financials[c])
        ]
        assert not wrong_type, (
            f"Expected float64 columns but got wrong dtype: {wrong_type}"
        )

    def test_year_is_integer(self, financials):
        assert pd.api.types.is_integer_dtype(financials["year"]), (
            f"year column should be integer, got {financials['year'].dtype}"
        )

    def test_no_financial_sector_rows(self, financials):
        """KSIC 640–669 and 68200 must be excluded (transform.py financial exclusion)."""
        if "ksic_code" not in financials.columns:
            pytest.skip("ksic_code column not present")

        def is_financial(code) -> bool:
            if pd.isna(code):
                return False
            s = str(code).strip()
            if s == "68200":
                return True
            try:
                return 640 <= int(s[:3]) <= 669
            except (ValueError, TypeError):
                return False

        flagged = financials["ksic_code"].apply(is_financial).sum()
        assert flagged == 0, (
            f"{flagged} financial-sector rows (KSIC 640–669 / 68200) survived transform"
        )

    def test_no_empty_corp_code(self, financials):
        null_count = financials["corp_code"].isna().sum()
        assert null_count == 0, f"{null_count} rows have null corp_code"

    def test_market_column_values(self, financials):
        """All rows should be KOSDAQ (Phase 1 scope)."""
        if "market" not in financials.columns:
            pytest.skip("market column not present")
        unexpected = financials[~financials["market"].str.upper().str.contains("KOSDAQ", na=False)]
        assert len(unexpected) == 0, (
            f"{len(unexpected)} rows have unexpected market value: "
            f"{unexpected['market'].unique().tolist()}"
        )

    def test_fs_type_values_and_distribution(self, financials):
        """fs_type must be one of three allowed values; must not be 100% no_filing (KI-003 regression guard).

        The KI-003 Unicode bug caused every company-year to silently write no_filing
        because OpenDartReader's finstate_all() printed Korean text before making the
        API call, raising UnicodeEncodeError on Windows cp1252, caught by except Exception.
        A >50% no_filing rate is the failure signature — this threshold catches a
        partial regression without being too tight on legitimate missing data.
        """
        allowed = {"CFS", "OFS", "no_filing"}
        actual = set(financials["fs_type"].dropna().unique())
        assert actual.issubset(allowed), f"Unexpected fs_type values: {actual - allowed}"

        no_filing_pct = (financials["fs_type"] == "no_filing").mean()
        assert no_filing_pct < 0.50, (
            f"Over 50% of rows are no_filing ({no_filing_pct:.1%}). "
            "Check Unicode fix in extract_dart.py (KI-003)."
        )


# ─── Category 3: Beneish formula spot-check ──────────────────────────────────

class TestBeneishFormula:
    """
    Known input → expected M-Score to 2 decimal places.

    Constructs a synthetic two-year dataset for one fictitious company and
    asserts the computed M-Score matches hand-calculated expectations.

    This documents the formula implementation as executable specification and
    guards against accidental coefficient or sign changes during refactors.

    Reference: Beneish (1999) 8-variable model.
    Coefficients: −4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI
                  + 0.115·DEPI − 0.172·SGAI + 4.679·TATA − 0.327·LVGI
    """

    def _make_two_year_df(self) -> pd.DataFrame:
        """
        Construct a minimal two-year (T-1=2019, T=2020) financial DataFrame
        with exact values chosen so that every Beneish ratio is deterministic
        and hand-calculable.

        Values (all in KRW millions, arbitrary but round):
          revenue:       T-1=1000, T=1200   → SGI = 1.20
          receivables:   T-1=100,  T=130    → DSRI = (130/1200) / (100/1000) = 1.0833
          cogs:          T-1=600,  T=700    → gross margin T-1=0.40, T=0.4167
                                              GMI = 0.40/0.4167 = 0.9600
          ppe:           T-1=400,  T=420
          depreciation:  T-1=50,   T=55
                                              DEPI = (50/(400+50)) / (55/(420+55))
                                                   = 0.11111 / 0.11579 = 0.9596
          total_assets:  T-1=1500, T=1700
          soft_assets:   T-1=1100, T=1280   → AQI = (1280/1700)/(1100/1500) = 1.0256
          sga:           T-1=80,   T=110    → SGAI = (110/1200)/(80/1000) = 1.1458
          lt_debt:       T-1=200,  T=260    → LVGI = (260/1700)/(200/1500) = 1.1471
          net_income:    T=100
          cfo:           T=80
                                              TATA = (100-80)/1700 = 0.01176
        """
        return pd.DataFrame([
            {
                "corp_code": "TEST001", "ticker": "000001", "company_name": "Test Co",
                "market": "KOSDAQ", "year": 2019,
                "fs_type": "CFS", "expense_method": "function",
                "receivables": 100, "revenue": 1000, "cogs": 600, "sga": 80,
                "ppe": 400, "depreciation": 50, "total_assets": 1500,
                "lt_debt": 200, "net_income": None, "cfo": None,
                "wics_sector_code": "G4510", "wics_sector": "Retail",
                "ksic_code": "521", "krx_sector": None,
            },
            {
                "corp_code": "TEST001", "ticker": "000001", "company_name": "Test Co",
                "market": "KOSDAQ", "year": 2020,
                "fs_type": "CFS", "expense_method": "function",
                "receivables": 130, "revenue": 1200, "cogs": 700, "sga": 110,
                "ppe": 420, "depreciation": 55, "total_assets": 1700,
                "lt_debt": 260, "net_income": 100, "cfo": 80,
                "wics_sector_code": "G4510", "wics_sector": "Retail",
                "ksic_code": "521", "krx_sector": None,
            },
        ])

    def _run_beneish(self, df_fin: pd.DataFrame) -> pd.DataFrame:
        """Run the Beneish computation cell logic directly."""
        df = df_fin.copy()
        numeric_cols = [
            "receivables", "revenue", "cogs", "sga", "ppe", "depreciation",
            "total_assets", "lt_debt", "net_income", "cfo",
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.sort_values(["corp_code", "year"]).reset_index(drop=True)
        lag_cols = [
            "receivables", "revenue", "cogs", "sga", "ppe",
            "depreciation", "total_assets", "lt_debt", "fs_type", "expense_method",
        ]
        for col in lag_cols:
            df[f"{col}_l"] = df.groupby("corp_code")[col].shift(1)

        rev   = df["revenue"].replace(0, np.nan)
        rev_l = df["revenue_l"].replace(0, np.nan)
        ta    = df["total_assets"].replace(0, np.nan)
        ta_l  = df["total_assets_l"].replace(0, np.nan)

        df["gross_profit"]   = df["revenue"]   - df["cogs"]
        df["gross_profit_l"] = df["revenue_l"] - df["cogs_l"]
        df["gross_margin"]   = df["gross_profit"]   / rev
        df["gross_margin_l"] = df["gross_profit_l"] / rev_l
        df["soft_assets"]    = df["total_assets"]   - df["ppe"]
        df["soft_assets_l"]  = df["total_assets_l"] - df["ppe_l"]

        df["dsri"] = (df["receivables"] / rev)   / (df["receivables_l"] / rev_l)
        gmi_raw    = df["gross_margin_l"] / df["gross_margin"].replace(0, np.nan)
        df["gmi"]  = np.where(df["expense_method"] == "nature", 1.0, gmi_raw)
        df["aqi"]  = (df["soft_assets"] / ta)    / (df["soft_assets_l"] / ta_l)
        df["sgi"]  = df["revenue"] / rev_l
        ppe_depr   = (df["ppe"]   + df["depreciation"]).replace(0, np.nan)
        ppe_depr_l = (df["ppe_l"] + df["depreciation_l"]).replace(0, np.nan)
        df["depi"] = (df["depreciation_l"] / ppe_depr_l) / (df["depreciation"] / ppe_depr)
        sgai_raw   = (df["sga"] / rev) / (df["sga_l"] / rev_l)
        df["sgai"] = np.where(df["expense_method"] == "nature", 1.0, sgai_raw)
        df["lvgi"] = (df["lt_debt"] / ta) / (df["lt_debt_l"] / ta_l)
        df["tata"] = (df["net_income"] - df["cfo"]) / ta

        core   = ["dsri", "aqi", "sgi", "depi", "tata"]
        df["_null_core"] = df[core].isna().sum(axis=1)

        df["m_score"] = np.where(
            df["_null_core"] > 2,
            np.nan,
            (
                -4.84
                + 0.920 * df["dsri"].fillna(1.0)
                + 0.528 * df["gmi"]
                + 0.404 * df["aqi"].fillna(1.0)
                + 0.892 * df["sgi"].fillna(1.0)
                + 0.115 * df["depi"].fillna(1.0)
                - 0.172 * df["sgai"]
                + 4.679 * df["tata"].fillna(0.0)
                - 0.327 * df["lvgi"].fillna(1.0)
            ),
        )
        df.loc[df["revenue_l"].isna(), "m_score"] = np.nan
        return df

    def test_m_score_known_input(self):
        """M-Score for hand-crafted synthetic data matches manual calculation."""
        df = self._make_two_year_df()
        result = self._run_beneish(df)
        row_t = result[result["year"] == 2020].iloc[0]

        # Hand-calculated ratios (see docstring above)
        assert abs(row_t["dsri"] - 1.0833) < 0.001, f"DSRI={row_t['dsri']:.4f}"
        assert abs(row_t["gmi"]  - 0.9600) < 0.001, f"GMI={row_t['gmi']:.4f}"
        assert abs(row_t["aqi"]  - 1.0267) < 0.001, f"AQI={row_t['aqi']:.4f}"
        assert abs(row_t["sgi"]  - 1.2000) < 0.001, f"SGI={row_t['sgi']:.4f}"
        assert abs(row_t["depi"] - 0.9596) < 0.001, f"DEPI={row_t['depi']:.4f}"
        assert abs(row_t["sgai"] - 1.1458) < 0.001, f"SGAI={row_t['sgai']:.4f}"
        assert abs(row_t["lvgi"] - 1.1471) < 0.001, f"LVGI={row_t['lvgi']:.4f}"
        assert abs(row_t["tata"] - 0.01176) < 0.0001, f"TATA={row_t['tata']:.5f}"

        # M-Score = -4.84 + 0.920*1.0833 + 0.528*0.9600 + 0.404*1.0267
        #           + 0.892*1.2000 + 0.115*0.9596 - 0.172*1.1458
        #           + 4.679*0.01176 - 0.327*1.1471
        # = -4.84 + 0.9967 + 0.5069 + 0.4148 + 1.0704 + 0.1104
        #   - 0.1971 + 0.0550 - 0.3751
        # = -2.2580
        expected_m_score = -2.26
        assert abs(row_t["m_score"] - expected_m_score) < 0.02, (
            f"M-Score={row_t['m_score']:.4f}, expected ~{expected_m_score}"
        )

    def test_nature_method_sets_gmi_sgai_to_one(self):
        """Nature-of-expense companies must have GMI=1.0 and SGAI=1.0."""
        df = self._make_two_year_df()
        df["expense_method"] = "nature"
        result = self._run_beneish(df)
        row_t = result[result["year"] == 2020].iloc[0]
        assert row_t["gmi"]  == 1.0, f"nature method: GMI={row_t['gmi']}"
        assert row_t["sgai"] == 1.0, f"nature method: SGAI={row_t['sgai']}"

    def test_first_year_has_no_m_score(self):
        """Year T-1 (no lag data available) must have null m_score."""
        df = self._make_two_year_df()
        result = self._run_beneish(df)
        row_t_minus_1 = result[result["year"] == 2019].iloc[0]
        assert pd.isna(row_t_minus_1["m_score"]), (
            f"First year should have null m_score, got {row_t_minus_1['m_score']}"
        )


# ─── Category 4: Beneish output schema ───────────────────────────────────────

REQUIRED_BENEISH_COLUMNS = [
    "corp_code", "ticker", "company_name", "market", "year", "extraction_date",
    "fs_type", "fs_type_switched", "expense_method",
    "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "lvgi", "tata",
    "m_score", "flag", "high_fp_risk", "risk_tier",
    "wics_sector_code", "wics_sector", "sector_percentile", "dart_link",
]


class TestBeneishOutputSchema:
    """
    beneish_scores.parquet must contain all required output columns.

    The aggregate M-Score alone is insufficient for downstream consumers:
    - Credit analysts need individual components to understand why a company is flagged.
    - Researchers testing sector patterns (elevated TATA in biotech, etc.) need
      component-level data.
    - fs_type and fs_type_switched are required for academic disclosure of CFS/OFS provenance.
    """

    @pytest.fixture(scope="class")
    def beneish_scores(self):
        p = PROCESSED / "beneish_scores.parquet"
        if not p.exists():
            pytest.skip("beneish_scores.parquet not found — run beneish_screen.py first")
        return pd.read_parquet(p)

    def test_beneish_required_columns_present(self, beneish_scores):
        """All required Beneish output columns must be present by name."""
        missing = [c for c in REQUIRED_BENEISH_COLUMNS if c not in beneish_scores.columns]
        assert not missing, f"Missing columns in beneish_scores.parquet: {missing}"

    def test_extraction_date_format(self, beneish_scores):
        """extraction_date must be ISO 8601 (YYYY-MM-DD) with no nulls."""
        import re
        assert "extraction_date" in beneish_scores.columns, "extraction_date column missing"
        assert beneish_scores["extraction_date"].notna().all(), "extraction_date has null values"
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        bad = [v for v in beneish_scores["extraction_date"].unique() if not pattern.match(str(v))]
        assert not bad, f"extraction_date values not ISO 8601: {bad}"

    def test_risk_tier_values(self, beneish_scores):
        """risk_tier must contain only the four allowed values."""
        valid = {"Critical", "High", "Medium", "Low"}
        assert "risk_tier" in beneish_scores.columns, "risk_tier column missing"
        actual = set(beneish_scores["risk_tier"].dropna().unique())
        unexpected = actual - valid
        assert not unexpected, f"Unexpected risk_tier values: {unexpected}"

    def test_risk_tier_logic(self, beneish_scores):
        """risk_tier must follow the documented tier logic."""
        df = beneish_scores[beneish_scores["m_score"].notna()].copy()
        # Low: flag=False
        low = df[df["risk_tier"] == "Low"]
        assert (low["flag"] == False).all(), "Low tier rows must have flag=False"  # noqa: E712
        # Medium: flag=True and high_fp_risk=True
        medium = df[df["risk_tier"] == "Medium"]
        assert (medium["flag"] == True).all(), "Medium tier rows must have flag=True"  # noqa: E712
        assert (medium["high_fp_risk"] == True).all(), "Medium tier rows must have high_fp_risk=True"  # noqa: E712
        # Critical: flag=True, high_fp_risk=False, m_score > -1.0
        critical = df[df["risk_tier"] == "Critical"]
        assert (critical["flag"] == True).all(), "Critical tier rows must have flag=True"  # noqa: E712
        assert (critical["high_fp_risk"] == False).all(), "Critical tier rows must have high_fp_risk=False"  # noqa: E712
        assert (critical["m_score"] > -1.0).all(), "Critical tier rows must have m_score > -1.0"
        # High: flag=True, high_fp_risk=False, m_score <= -1.0
        high = df[df["risk_tier"] == "High"]
        assert (high["flag"] == True).all(), "High tier rows must have flag=True"  # noqa: E712
        assert (high["high_fp_risk"] == False).all(), "High tier rows must have high_fp_risk=False"  # noqa: E712
        assert (high["m_score"] <= -1.0).all(), "High tier rows must have m_score <= -1.0"


# ─── Category 5: Reference artifact completeness ─────────────────────────────


class TestReferenceArtifacts:
    """
    Published reference artifacts in 00_Reference/ must exist and be complete.
    Guards against the crosswalk CSV being accidentally deleted or truncated.
    """

    def test_xbrl_crosswalk_exists_and_complete(self):
        """dart_xbrl_crosswalk.csv must exist in 00_Reference/ and cover all 10 financial variables."""
        crosswalk_path = ROOT / "00_Reference" / "dart_xbrl_crosswalk.csv"
        assert crosswalk_path.exists(), "dart_xbrl_crosswalk.csv not found in 00_Reference/"

        df = pd.read_csv(crosswalk_path)
        required_cols = ["variable_name", "element_id_primary", "statement_type", "formula_role"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        assert not missing_cols, f"Missing columns in crosswalk: {missing_cols}"

        expected_variables = {
            "receivables", "revenue", "cogs", "sga", "ppe",
            "depreciation", "total_assets", "lt_debt", "net_income", "cfo",
        }
        actual_variables = set(df["variable_name"].tolist())
        missing_vars = expected_variables - actual_variables
        assert not missing_vars, f"Crosswalk missing entries for variables: {missing_vars}"
