# Known Issues

Documented data gaps, source limitations, and pipeline design decisions that affect output quality. These are not bugs — they are known, understood constraints recorded here so that anyone using the output can interpret results correctly.

---

## KI-001 — WICS sector coverage is ~85%, not 100%

**Affects:** `wics_sector_code`, `wics_sector`, `sector_percentile` columns in `beneish_scores.parquet`
**Scope:** ~240 of 1,566 companies (~15%) have no WICS sector code
**AC2 threshold set to:** ≥80% (reflects actual source ceiling)

### What WICS is

WICS (WISEindex Industry Classification Standard) is a private classification system maintained by WISEfn, a Korean financial data vendor. It is the most granular and widely used sector taxonomy for Korean equities, covering both KOSPI and KOSDAQ. It is used by institutional investors for peer group construction and benchmark composition.

### Why ~15% of companies are unclassified

WISEfn classifies companies based on institutional investor relevance. Smaller KOSDAQ companies with limited institutional following are often not assigned a WICS code. This is a deliberate curation decision by WISEfn — not a data error. No matter how many times the pipeline re-runs or how WICS is queried, those ~240 companies will not appear because WISEfn has not classified them.

### What this means for outputs

Companies without a WICS sector code still receive a Beneish M-Score — they are not dropped from the output. What they are missing is the `sector_percentile` column, which ranks a company against its industry peers within the same year. For the ~15% without a sector code, `sector_percentile` will be null.

The M-Score itself is unaffected.

### Why the AC2 threshold is ≥80% and not ≥95%

AC2 exists to catch a pipeline failure — specifically, the WICS join silently breaking and leaving all companies unclassified. At ~85% coverage, the join is clearly working correctly. The 240 missing companies are a source limitation, not a fixable pipeline issue.

Keeping the threshold at 95% would cause AC2 to permanently fail for a reason outside our control, making it useless as a health signal. Lowering it to ≥80% preserves its diagnostic value: a genuine breakage (e.g. WICS returning empty) would drop coverage to near zero and still trigger the failure. The check remains meaningful.

### Potential remediation (Phase 2)

For the ~240 unclassified companies, a fallback sector assignment could be derived from KSIC codes (already present in the output as `ksic_code`). KSIC Rev.10 maps to a standardised industry hierarchy that could approximate WICS group-level classification. This would require building a KSIC → WICS-equivalent mapping table and is deferred to Phase 2.

---

## KI-004 — `--sample` run overwrites `ksic.parquet` with only N rows (fixed)

**Affects:** `01_Data/raw/sector/ksic.parquet`
**Status:** Fixed in `extract_dart.py` on February 27, 2026
**Triggered by:** Running the pipeline with `--sample N` after a full KSIC fetch had already completed

### What happened

`fetch_ksic()` loads existing entries from `ksic.parquet` into a dict (`existing`) to support resumable runs. When `--sample N` is passed, it limits the company loop to N companies. Each company already in `existing` is appended to `rows` directly without an API call. However, at the end of the function, only `rows` (the N-entry list) was written back to disk — the remaining 1,702 − N entries loaded from `existing` were silently discarded.

Result: a smoke test with `--sample 5` reduced `ksic.parquet` from 1,702 rows to 5 rows, causing the subsequent full transform to show "KSIC join: 16/7,222 rows" instead of the expected ~7,000+.

### Fix applied

At the end of `fetch_ksic()`, when `sample` is set, the newly fetched `rows` are merged back over the full `existing` set before writing, with `new_df` taking precedence for any `corp_code` present in both. When `sample` is not set (full run), the existing behaviour is unchanged.

### How it was discovered

Smoke test (`--sample 5`) was run after the full pipeline completed as part of the cloud infrastructure backward-compatibility check. The transform stage immediately following the smoke test logged "KSIC join: 16/7,222 rows have KSIC code", which was anomalously low and prompted investigation.

### Regression test

`tests/test_pipeline_invariants.py::TestKsicSamplePreservation` guards this fix. See `00_Reference/21_Test_Suite.md` for full test documentation.

---

## KI-002 — `completed_at` and `elapsed_minutes` not written to run_summary.json

**Affects:** `01_Data/raw/run_summary.json`
**Scope:** These fields are always `null` after a full pipeline run

The `run_summary.json` written by `extract_dart.py` at the end of the financials stage initialises `completed_at` and `elapsed_minutes` as `null` but the pipeline orchestrator (`pipeline.py`) does not populate them after the transform stage completes. The counts (`full_data`, `partial_data`, `no_data`, `errors`) are correct and reliable.

Not a blocker — the summary is informational only. Fix deferred to a later cleanup pass.

---

## KI-003 — AC4 financial exclusion check is a soft pass

**Affects:** `tests/test_acceptance_criteria.py` AC4
**Scope:** AC4 checks for KSIC 640–669 / 68200 rows in `beneish_scores.parquet`, but `beneish_scores.parquet` does not carry a `ksic_code` column (it is present in `company_financials.parquet` but dropped in the Beneish output schema)

The exclusion itself is applied correctly during `transform.py` — financial sector companies are removed before `company_financials.parquet` is written. AC4 soft-passes because it cannot find a KSIC column in the scores output to verify against. The underlying exclusion is sound; the verification check needs to be updated to read from `company_financials.parquet` instead. Deferred to a later cleanup pass.
