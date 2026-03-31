# 02_Pipeline — Legacy Monolith Copy

> **Canonical source:** `../kr-dart-pipeline` repo (`kr_dart_pipeline/` package)

The scripts in this directory are the **original monolith** from before the ecosystem split
(2026-03-26). The extraction logic has since been extracted into the standalone
`kr-dart-pipeline` package.

## Status

These files are kept here because `krff/pipeline.py` proxies to `02_Pipeline/pipeline.py`
at runtime, and `tests/test_pipeline_invariants.py` uses bare `import transform` imports
that resolve to this directory via `sys.path` manipulation in `tests/conftest.py`.

**Do not edit these files directly.** Changes to ETL logic belong in `kr-dart-pipeline`.
The two codebases can diverge silently — any divergence is a bug.

## Files

| File | Canonical location |
|------|--------------------|
| `extract_*.py` (15 files) | `kr-dart-pipeline/kr_dart_pipeline/extract_*.py` |
| `pipeline.py` | `kr-dart-pipeline/kr_dart_pipeline/pipeline.py` |
| `transform.py` | `kr-dart-pipeline/kr_dart_pipeline/transform.py` |
| `_pipeline_helpers.py` | `kr-dart-pipeline/kr_dart_pipeline/_pipeline_helpers.py` |
| `build_isin_map.py` | `kr-dart-pipeline/kr_dart_pipeline/build_isin_map.py` |
