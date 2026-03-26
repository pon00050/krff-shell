"""krff/ — Core package for krff-shell.

Public API:
    krff.models       — Pydantic models (CompanySummary, PipelineStatus, DataQuality)
    krff.data_access  — Data loading (load_parquet, load_csv, load_company_name)
    krff.report       — get_company_summary, get_report_html, generate_report
    krff.status       — get_status, format_status
    krff.quality      — get_quality, format_quality
    krff.constants    — BENEISH_THRESHOLD, flag names, scoring thresholds
"""
