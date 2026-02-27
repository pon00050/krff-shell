# Bug Log

Documented bugs found during development. Each entry covers the symptom, the investigation path, the root cause, and the fix. Written so future developers (and future AI assistants) don't spend hours re-diagnosing the same problems.

---

## [Feb 2026] OpenDartReader `finstate_all()` silently produces `no_filing` for every company on Windows

**Severity:** Critical — pipeline produces zero financial data without any error
**Affected file:** `02_Pipeline/extract_dart.py`
**Status:** Fixed

### Symptom

The full pipeline ran to completion (exit code 0, ~3 hours, all 1,702 companies processed) but the output was nearly empty. `run_summary.json` reported:

```
full_data: 0, partial_data: 40, no_data: 1662, errors: 0
```

`01_Data/processed/company_financials.parquet` contained only 80 company-year rows instead of the expected ~8,000+. Every company-year parquet file in `01_Data/raw/financials/` that was written during the run had `_fs_type = "no_filing"` with only 3 columns (a sentinel row). No API error messages appeared anywhere in the log.

### Investigation

**Step 1 — Rule out rate limits.** The DART API daily limit is ~10,000–20,000 calls. The pipeline needs ~17,000 calls for 1,702 companies × 5 years × 2 attempts. A rate limit was the first hypothesis. Checked the log for DART error code "020" (rate limit) — found none. Checked for any non-log-formatted lines that would indicate the `print(jo)` statement inside `finstate_all` firing on error responses — found none.

**Step 2 — Check if the API actually has data.** Ran manual `dart.finstate_all()` calls for several companies (including 인화정공 `00482426` and 프로이천 `01359736`) after the pipeline completed. All returned 100–200+ rows for every year 2019–2023. The DART API had the data all along.

**Step 3 — Analyze the file timestamps.** The 80 "data" parquet files all had timestamps from a previous smoke test run (22:50 on Feb 26), not from the full pipeline run (00:37–03:02 on Feb 27). Every file written during the full run was a `no_filing` sentinel. This meant the pipeline was making API calls and immediately getting empty results — or not making them at all.

**Step 4 — Count how many API calls were actually made.** The `finstate_all()` method in OpenDartReader has a `print()` statement that fires after `find_corp_code()` succeeds but *before* the HTTP request:

```python
# From OpenDartReader source (dart.py line 129):
print(f"reprt_code='{reprt_code}', fs_div='{fs_div}' ({reprt_code_dict[reprt_code]}, {fs_div_dict[fs_div]})'")
return dart_finstate.finstate_all(self.api_key, corp_code, bsns_year, ...)
```

Searched `pipeline_full.log` for `reprt_code` — found **zero matches**. This proved that `finstate_all()` was never reaching the `print()` statement, meaning it was raising an exception before the API call was ever made.

**Step 5 — Reproduce the exact pipeline code path.** Wrote a minimal replication with `DEBUG`-level logging to surface exceptions:

```python
logging.basicConfig(level=logging.DEBUG, ...)
try:
    df = dart.finstate_all('01359736', 2021, fs_div='CFS')
except Exception as e:
    log.error('Exception: %s', e, exc_info=True)
```

Output:
```
UnicodeEncodeError: 'charmap' codec can't encode characters in position 34-38:
character maps to <undefined>
  File "OpenDartReader/dart.py", line 129, in finstate_all
    print(f"reprt_code='{reprt_code}', fs_div='{fs_div}' (사업보고서, 연결제무제표)'")
```

### Root cause

`finstate_all()` calls `print()` with Korean text (`연결제무제표`, `사업보고서`) before making the HTTP request. On Windows, the default `sys.stdout` encoding is `cp1252`, which cannot encode Korean characters. This raises `UnicodeEncodeError`.

In `extract_dart.py`, every `finstate_all()` call is wrapped in:

```python
try:
    df = dart.finstate_all(corp_code, year, fs_div="CFS")
    ...
except Exception as exc:
    log.debug("CFS failed %s %d: %s", corp_code, year, exc)
    df = None
```

`UnicodeEncodeError` is a subclass of `Exception`, so it was caught silently. The `log.debug()` call (not visible at INFO level) recorded the error, and the code proceeded to write a `no_filing` sentinel. The HTTP request was never made. This happened for every single company-year on every pipeline run.

### Why the smoke test appeared to work

The 40 companies that showed data (`_fs_type = "CFS"`) all had files written at 22:50 on Feb 26 — before the Unicode bug was discovered. Those files came from earlier test runs where `sys.stdout` may have been in a different state, or the test was run interactively (where Windows may use a UTF-8 console). The "passing" smoke test result was actually a false positive from cached data.

### Fix

In `extract_dart.py`, added `sys.stdout` redirect to UTF-8 at module load time, *before* any `finstate_all()` call can be made. Updated the logging handler to use `sys.stdout` directly so both `logging` and `print()` share the same stream:

```python
# Windows Unicode fix: OpenDartReader's finstate_all() has a print() that emits Korean
# text (e.g. "연결제무제표") BEFORE making the API call. On Windows the default
# sys.stdout is cp1252, so that print() raises UnicodeEncodeError, which the pipeline's
# except Exception silently catches, writing no_filing for every company-year.
# Redirecting sys.stdout to utf-8 before the first finstate_all call fixes this.
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)
```

After applying this fix, `reprt_code='11011', fs_div='CFS' (사업보고서, 연결제무제표)'` print statements appeared in the log for every API call, confirming the HTTP requests were being made. Data started flowing immediately.

### Detection checklist for future runs

If the pipeline produces mostly `no_filing` results, check:
1. Search `pipeline_run.log` for `reprt_code` — if zero matches, the `finstate_all()` print is crashing before the API call.
2. Run `python -c "import sys; from dotenv import load_dotenv; load_dotenv(); import os, OpenDartReader; dart = OpenDartReader(os.getenv('DART_API_KEY')); print(dart.finstate_all('00482426', 2022))"` — if it crashes with `UnicodeEncodeError`, the `sys.stdout` fix has been lost.
3. Check `sys.stdout.encoding` at the start of a pipeline run — should be `utf-8`, not `cp1252`.

---

## [Feb 2026] `transform.py` crashes with duplicate column on WICS join

**Severity:** High — transform stage crashes, no output written
**Affected file:** `02_Pipeline/transform.py`
**Status:** Fixed

### Symptom

Running the transform stage after a successful DART extraction crashed with a pandas error about duplicate columns when writing to parquet. The error occurred during the WICS sector enrichment join.

### Root cause

`01_Data/raw/sector/wics.parquet` contains two different "sector" columns at different granularity levels:

- `wics_sector_code` — the 3-character sector code (e.g., `G35` for Healthcare), written by `extract_dart.py`
- `wics_group_code` — the 5-character industry group code (e.g., `G3510` for Pharma/Bio)

When `transform.py` joined this file to the company financials and then renamed `wics_group_code` → `wics_sector_code`, it created a duplicate `wics_sector_code` column (the original sector-level one was still present). Pandas `to_parquet()` rejects DataFrames with duplicate column names.

### Fix

In the WICS join within `transform.py`, select only the specific columns needed from `wics.parquet` before joining — `wics_group_code` and `wics_group_name` — and drop the rest. Then rename to `wics_sector_code` / `wics_sector` after the join. This avoids bringing in the pre-existing `wics_sector_code` column from the raw file.

```python
wics = wics[['ticker', 'wics_group_code', 'wics_group_name']].rename(columns={
    'wics_group_code': 'wics_sector_code',
    'wics_group_name': 'wics_sector',
})
```

---

## [Feb 2026] Windows Korean company names crash default logging handler

**Severity:** High — pipeline crashes immediately on startup with Korean company names
**Affected files:** `02_Pipeline/pipeline.py`, `02_Pipeline/extract_dart.py`, `02_Pipeline/transform.py`
**Status:** Fixed

### Symptom

On Windows, running the pipeline with the default `logging.StreamHandler()` (no encoding specified) caused immediate crashes when the first Korean company name was logged. The error was:

```
UnicodeEncodeError: 'charmap' codec can't encode characters
```

This affects every `log.info("[1/1702] GRT ...")` type statement and all subsequent Korean text in log output.

### Root cause

Windows uses `cp1252` as the default console encoding. The standard `logging.StreamHandler()` inherits this encoding from `sys.stdout`. Korean characters (Hangul) are not representable in `cp1252`.

### Fix

All three pipeline files replace the default `StreamHandler` with one that writes directly to stdout's underlying file descriptor in UTF-8:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(stream=open(sys.stdout.fileno(), mode='w', encoding='utf-8', closefd=False))],
)
```

Note: after the OpenDartReader `print()` fix was applied (see first bug above), `extract_dart.py` now assigns `sys.stdout` to UTF-8 first, then passes `sys.stdout` to the handler. The effect is the same.

---

## Template for future entries

```
## [Month Year] Short descriptive title

**Severity:** Critical / High / Medium / Low
**Affected file(s):** path/to/file.py
**Status:** Fixed / Open / Deferred

### Symptom
What you observed. Be specific — include log output, row counts, error messages.

### Investigation
The steps taken to narrow down the cause. Include dead ends.

### Root cause
The actual reason, with code references.

### Fix
What was changed, with before/after code snippets if helpful.
```
