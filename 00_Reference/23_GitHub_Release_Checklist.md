# 23 — GitHub Pre-Release Checklist

> **Scope:** Pre-release audit results and checklist for publishing the repo publicly. Written February 27, 2026.
> **Canonical for:** .gitignore gaps fixed; pre-release checklist status.
> **See also:** `22_Phase1_Completion_Record.md` (completion sign-off), `ROADMAP.md` (CB4 blocker status)

Checklist for publishing kr-forensic-finance as a public GitHub repository.
Written February 27, 2026. Based on a full pre-release audit.

---

## Audit Results Summary (Feb 27, 2026)

| Category | Status | Notes |
|---|---|---|
| Hardcoded credentials in .py files | ✅ Clean | All use `os.getenv()` — no hardcoding |
| .env file | ✅ Gitignored | Will not be committed |
| .gitignore coverage | ⚠️ 3 gaps found | See Section 1 below |
| README.md | ✅ Ready | Disclaimer, limitations, install instructions all present |
| pyproject.toml | ✅ Clean | No private registries or internal packages |
| 00_Reference/ docs | ✅ Clean | 26 documents (24 at pre-release audit + reference-index.md + pipeline-details.md added during housekeeping), no proprietary or personal data |
| tests/ | ✅ Clean | Uses os.getenv() for credentials, no hardcoding |
| Log files | ⚠️ Not gitignored | pipeline_*.log will be committed unless fixed |
| .claude/settings.local.json | ⚠️ Not gitignored | Local IDE settings should not be committed |
| docs_cache/ | ⚠️ Not gitignored | Should be excluded |

---

## Section 1 — Fix .gitignore Before First Commit

These three patterns were missing from `.gitignore` and have been added:

- [x] Added `*.log` — prevents committing pipeline_batch1.log (20 KB), pipeline_run.log (162 KB), pipeline_full2.log (1.3 MB)
- [x] Added `.claude/settings.local.json` — prevents committing local Claude Code IDE settings (27 KB). Note: `.claude/CLAUDE.md` SHOULD be committed — it is project instructions for Claude Code.
- [x] Added `docs_cache/` — prevents committing the docs cache directory at project root

---

## Section 3 — Technical Verification (All Tests Pass)

Run this sequence on the laptop before publishing. All must pass.

```bash
# 1. Confirm .gitignore additions took effect
git status   # pipeline_*.log, .claude/settings.local.json, docs_cache/ should NOT appear

# 2. Unit + schema tests (no pipeline or data needed)
pytest tests/test_pipeline_invariants.py -v

# 3. Acceptance criteria (requires 01_Data/processed/ to exist locally)
pytest tests/test_acceptance_criteria.py -v
# Expected: AC1–AC7 all PASS

# 4. Beneish screen end-to-end
python 03_Analysis/beneish_screen.py
# Expected: completes, produces beneish_scores.csv
```

- [x] `test_pipeline_invariants.py` — all tests pass
- [x] `test_acceptance_criteria.py` — AC1–AC7 all pass
- [x] `beneish_screen.py` — completes without error

---

## Section 4 — Documentation Review

- [x] README.md disclaimer present: "Outputs are hypotheses for human review — not fraud conclusions"
- [x] README.md GitHub clone URL updated from `YOUR_USERNAME` placeholder to actual username
- [x] `00_Reference/20_Cloud_Infrastructure_Setup.md` — Oracle Cloud replaces Hetzner; Step 6 updated with correct SSH user, uv run python, and geo-block note
- [ ] No TODO/FIXME comments in any source file (confirmed clean in audit)
- [ ] `.env.example` shows placeholders only (confirmed clean in audit)

---

## Section 5 — GitHub Repository Setup

```bash
# Initialize git (if not already done)
cd C:\Users\pon00\Projects\kr-forensic-finance
git init
git add .
git status   # Review carefully — confirm no .env, no logs, no 01_Data/

# First commit
git commit -m "Initial public release: KOSDAQ Beneish M-Score pipeline (Phase 1 complete)"

# Create GitHub repo (via gh CLI or browser)
gh repo create kr-forensic-finance --public --description "Korean capital markets data pipeline: KOSDAQ anomaly detection using public DART + KRX data"

# Push
git remote add origin https://github.com/<username>/kr-forensic-finance.git
git branch -M main
git push -u origin main
```

- [x] `git status` reviewed carefully before first commit — no secrets, no large files
- [x] GitHub repo created as **public** (https://github.com/pon00050/kr-forensic-finance)
- [x] Initial commit pushed
- [ ] README renders correctly on GitHub (check formatting, links, code blocks)
- [x] Update README.md `git clone` URL from placeholder to actual repo URL, push again

---

## Section 6 — Post-Publish

- [ ] Add GitHub repo URL to career-development portfolio notes (`02_Opportunities/한국세무사회전산법인_Company_Research.md` Section 19 publication checklist)
- [ ] Verify `01_Data/` directory does not appear in GitHub file browser (gitignored)
- [ ] Verify `.env` does not appear in GitHub file browser (gitignored)
- [ ] Star / watch the repo to monitor any issue reports

---

## Known Safe-to-Skip Items

These were checked in the audit and require no action:
- All Python files use `os.getenv()` for credentials — no hardcoding anywhere
- `pyproject.toml` has no private registries
- All 26 reference documents contain no personal data, proprietary information, or credentials
- Test files use environment variables, not hardcoded values
