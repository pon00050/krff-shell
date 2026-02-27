# Verification Scripts — Open Questions (OQ-A through OQ-F)

These scripts resolve the 6 open questions from `00_Reference/18_Research_Findings.md`
that require empirical testing rather than web research.

## Status

| Script | API Key Required | Status | Notes |
|---|---|---|---|
| `oq_a_ksic_financial_codes.py` | No | **Ready to run** | Downloads KSIC CSV from GitHub |
| `oq_b_expense_method_prevalence.py` | **Yes — DART** | Blocked | Awaiting DART_API_KEY |
| `oq_c_cfs_ofs_split.py` | **Yes — DART** | Blocked | Awaiting DART_API_KEY |
| `oq_d_rate_limit_window.py` | **Yes — DART** | Blocked | Awaiting DART_API_KEY |
| `oq_e_noncurrent_borrowings_element.py` | **Yes — DART** | Blocked | Awaiting DART_API_KEY |
| `oq_f_bulk_download.py` | No | **Ready to run** | HTTP probe, no auth needed |

## Why DART-dependent scripts are not run yet

A DART API key (`DART_API_KEY`) has not been provisioned for this environment.
Scripts OQ-B, OQ-C, OQ-D, and OQ-E all require it.

**To unblock:** Register at `https://opendart.fss.or.kr/intro/main.do`, obtain a
free API key, and add it to `.env`:

```
DART_API_KEY=your_key_here
```

Then run the scripts in the order below.

## Execution Order (once key is available)

Run quota-free scripts first, then ascending by API call count:

```bash
cd 00_Reference/verify

# No API key needed — run immediately
python oq_a_ksic_financial_codes.py
python oq_f_bulk_download.py

# Requires DART_API_KEY — ordered by call count
python oq_d_rate_limit_window.py      # 10 calls
python oq_e_noncurrent_borrowings_element.py  # 5 calls
python oq_b_expense_method_prevalence.py      # ~50 calls
python oq_c_cfs_ofs_split.py                  # ~200 calls
```

Total DART API calls: ~265 (well within 10,000/day budget).

## Results

Each script writes one file to `results/` (gitignored):

| File | Script |
|---|---|
| `results/oq_a_ksic_section_k.csv` | OQ-A |
| `results/oq_a_juju_reits_codes.csv` | OQ-A |
| `results/oq_b_expense_method.csv` | OQ-B |
| `results/oq_c_cfs_ofs_split.csv` | OQ-C |
| `results/oq_d_rate_limit_observations.txt` | OQ-D |
| `results/oq_e_account_ids.csv` | OQ-E |
| `results/oq_f_bulk_download_findings.txt` | OQ-F |

After running, update `00_Reference/18_Research_Findings.md` to close each open question.
