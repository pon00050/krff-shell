# 20 — Cloud Infrastructure Setup

> **Scope:** Cloudflare R2 object storage and Oracle Cloud Free Tier VPS provisioning — setup steps, configuration, and status as of February 2026.
> **Canonical for:** R2 + Oracle Cloud provisioning; cloud infrastructure status.
> **See also:** `04_Technical_Architecture.md` (architecture overview), `22_Phase1_Completion_Record.md` (provisioning status)

Phase 1 cloud infrastructure: Cloudflare R2 object storage + Oracle Cloud Free Tier VPS.
**Status as of February 27, 2026:** Code changes complete. Steps 1–4 complete. Oracle Cloud instance running — VPS setup in progress.

> **Note:** Hetzner was the original VPS choice but the account was deactivated by Hetzner after review. Replaced with Oracle Cloud Free Tier (Always Free — no monthly cost).

---

## Architecture Overview

```
Your laptop
  └── .env with R2 credentials
  └── beneish_screen.py reads company_financials.parquet directly from R2 via DuckDB
  └── No local 01_Data/ files needed for analysis

Oracle Cloud Free Tier VPS ($0/month — Always Free)
  └── Shape: VM.Standard.E2.1.Micro (1 OCPU, 1 GB RAM)
  └── OS: Canonical Ubuntu 22.04 Minimal
  └── Region: ap-chuncheon-1 (Chuncheon, South Korea)
  └── Instance name: kr-forensic-finance
  └── Public IP: 168.107.21.26 (Ephemeral — eip-kr-forensic-finance)
  └── Private IP: 10.0.0.193
  └── VCN: vcn-20260227-2027
  └── Subnet: subnet-20260227-2026 (public)
  └── SSH key: ~/.ssh/ssh-key-2026-02-27.key (laptop)
  └── git clone + uv sync
  └── .env: DART_API_KEY + R2 credentials
  └── Pipeline runs manually via SSH
        01_Data/raw/     — local VPS cache only (wipe after run)
        01_Data/processed/ → written locally, then auto-uploaded to R2

Cloudflare R2 (~$0/month within free tier)
  └── processed/company_financials.parquet
  └── processed/beneish_scores.parquet
```

**Design principle:** R2 is optional. When `R2_ENDPOINT_URL`, `R2_ACCESS_KEY_ID`, and `R2_SECRET_ACCESS_KEY` are all absent from `.env`, every script behaves exactly as before — writes locally, reads locally. No behavioral change for local dev or smoke tests.

---

## What Was Implemented (Code Changes)

All code changes were applied on February 27, 2026.

### `pyproject.toml`
Added three new dependencies:
```toml
"s3fs>=2024.1.0",
"boto3>=1.34.0",
"duckdb>=1.0.0",
```
Run `uv sync` once to install them.

### `.env.example`
Appended R2 credential block:
```bash
# Cloudflare R2 (optional — omit for local-only mode)
R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_r2_access_key_id_here
R2_SECRET_ACCESS_KEY=your_r2_secret_access_key_here
R2_BUCKET=kr-forensic-finance
```

### `02_Pipeline/transform.py`
Two new functions added after `_write_parquet`:

- **`_r2_fs()`** — reads the three R2 env vars; returns an `s3fs.S3FileSystem` if all are present, else `None`. No import happens if credentials are absent.
- **`_upload_to_r2(local_path, r2_key)`** — calls `_r2_fs()`; if not `None`, uploads the file to `{R2_BUCKET}/{r2_key}` and logs the destination. Silent no-op otherwise.

Both `_write_parquet` call sites in `build_company_financials` were updated to capture the returned path and call `_upload_to_r2` immediately after:
```python
out = _write_parquet(df, "company_financials")
_upload_to_r2(out, "processed/company_financials.parquet")
```

### `03_Analysis/beneish_screen.py`
**`_load_data` cell** — replaced the simple `pd.read_parquet` call with a `_load_financials()` inner function:
1. If `R2_ENDPOINT_URL` + `R2_ACCESS_KEY_ID` + `R2_SECRET_ACCESS_KEY` are all set: connects via DuckDB `httpfs`, configures S3 endpoint to point at R2, reads `s3://{bucket}/processed/company_financials.parquet` into a DataFrame.
2. Otherwise: reads from `01_Data/processed/company_financials.parquet` (existing behavior).
3. `mo.stop()` fires only when both paths return nothing.

**`_write_parquet` cell** — after writing `beneish_scores.parquet` locally, checks for R2 credentials and uploads via `s3fs` if present.

### `tests/test_acceptance_criteria.py` (formerly `00_Reference/verify/check_acceptance_criteria.py`)
`load()` helper updated with the same R2/DuckDB primary path:
1. Tries DuckDB → R2 first.
2. On any R2 error: logs a warning and falls back to local.
3. If local also missing: exits with error as before.

### `README.md`
Added "Production Setup (Cloudflare R2 + Hetzner VPS)" section between Quickstart and "Data Not Committed", with a 4-step setup summary and the R2-is-optional note.

### `00_Reference/19_Data_Refresh_Cadence.md` (new)
Reference document covering the cadence for each data source (one-time, annual, quarterly, weekly, daily), practical run schedule, and the refresh manifest design (Phase 2 scope — documented only, not yet implemented).

---

## What Remains: Manual Steps

### Step 1 — Install new dependencies (laptop)

```bash
uv sync
```

Installs `s3fs`, `boto3`, `duckdb`. Takes ~30 seconds.

### Step 2 — Verify local behavior is unchanged

```bash
python 02_Pipeline/pipeline.py --market KOSDAQ --start 2021 --end 2023 --sample 5 --sleep 0.1 --max-minutes 3
python 03_Analysis/beneish_screen.py
```

With no R2 credentials in `.env`, output must be identical to pre-change behavior. Confirm no errors.

---

### Step 3 — Create Cloudflare R2 bucket

**Account:**
1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → create a free account if you don't have one
2. From the left sidebar: **R2 Object Storage** → **Get started** (one-time activation; requires a valid payment method even on free tier)

**Bucket:**
1. R2 dashboard → **Create bucket**
2. Name: `kr-forensic-finance`
3. Location: leave as automatic (or choose a region near South Korea — `APAC`)
4. Click **Create bucket**

**API token:**
1. R2 dashboard → **Manage R2 API Tokens** (top-right of the R2 overview page)
2. Click **Create API Token**
3. Name: `kr-forensic-finance-pipeline`
4. Permissions: **Object Read & Write**
5. Specify bucket: select `kr-forensic-finance` only (don't grant access to all buckets)
6. Click **Create API Token**
7. **Copy and save immediately** — the Secret Access Key is shown only once:
   - `Access Key ID` (starts with something like `abc123...`)
   - `Secret Access Key` (long random string)

**Account ID:**
- Visible in the R2 overview URL: `dash.cloudflare.com/<account_id>/r2/overview`
- Also shown on the right side of the R2 overview page under "Account ID"

**Endpoint URL format:**
```
https://<account_id>.r2.cloudflarestorage.com
```

**Free tier limits (as of 2026):**
- Storage: 10 GB/month free
- Class A operations (writes): 1 million/month free
- Class B operations (reads): 10 million/month free
- Egress: always free (zero egress fees — that's the point)

This project's data volume is well within the free tier.

---

### Step 4 — Add R2 credentials to `.env` (laptop)

Open `.env` and append:
```bash
R2_ENDPOINT_URL=https://<your_account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=<your_access_key_id>
R2_SECRET_ACCESS_KEY=<your_secret_access_key>
R2_BUCKET=kr-forensic-finance
```

---

### Step 5 — Provision Oracle Cloud Free Tier VPS

> **Status: ✅ Instance running as of Feb 27, 2026.**

**Oracle Cloud account:** [cloud.oracle.com](https://cloud.oracle.com)

**Instance details (already provisioned):**
- Name: `kr-forensic-finance`
- Shape: `VM.Standard.E2.1.Micro` (Always Free — 1 OCPU, 1 GB RAM, 46.6 GB boot volume)
- OS: Canonical Ubuntu 22.04 Minimal (build 2026.01.29-0)
- Region: `ap-chuncheon-1` (Chuncheon, South Korea)
- Availability domain: AD-1
- Public IP: `168.107.21.26` (Ephemeral — named `eip-kr-forensic-finance`)
- Private IP: `10.0.0.193`
- VCN: `vcn-20260227-2027`
- Subnet: `subnet-20260227-2026` (public, CIDR 10.0.0.0/24)
- SSH key file (laptop): `~/.ssh/ssh-key-2026-02-27.key`

**Connect via SSH:**
```bash
ssh -i ~/.ssh/ssh-key-2026-02-27.key ubuntu@168.107.21.26
```

**Install dependencies (first login only):**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

**Set up the project:**
```bash
git clone https://github.com/pon00050/kr-forensic-finance.git
cd kr-forensic-finance
uv sync
cp .env.example .env
nano .env   # add DART_API_KEY + all four R2_ variables
```

> **Note:** Oracle Cloud Ubuntu instances use the `ubuntu` user (not `root`). Use `sudo` for privileged commands.

> **Ephemeral IP warning:** The public IP `168.107.21.26` will change if the instance is stopped and restarted. If you need a stable IP, convert to a Reserved Public IP via OCI Console → Networking → IP Management → Reserved Public IPs.

---

### Step 6 — Run the pipeline on the VPS

```bash
ssh -i ~/.ssh/ssh-key-2026-02-27.key ubuntu@168.107.21.26
cd kr-forensic-finance

# Smoke test first
uv run python 02_Pipeline/pipeline.py --market KOSDAQ --start 2021 --end 2023 --sample 5 --sleep 0.1 --max-minutes 3

# Confirm R2 upload lines appear in log output:
# 2026-02-27 ... [INFO] Uploaded to R2: s3://kr-forensic-finance/processed/company_financials.parquet

# Full run (run inside tmux or screen so SSH disconnect doesn't kill it)
tmux new -s pipeline
uv run python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023
# Ctrl+B, D to detach; tmux attach -t pipeline to reattach
```

> **Known issue — PyKRX geo-block:** PyKRX returns 0 KOSDAQ tickers when run from the Oracle Cloud VPS (Chuncheon, ap-chuncheon-1). KRX's API appears to block or return empty responses for non-browser data center IPs. The R2 upload path works correctly — this only affects fresh data pulls. Workaround: run the full pipeline from your laptop (Korean residential IP) and rely on the VPS only for R2-read analysis tasks, or investigate KRX header spoofing (see `00_Reference/19_Pipeline_Improvement_Areas.md`).

**Verify upload in Cloudflare dashboard:**
- R2 → `kr-forensic-finance` bucket → Objects tab
- Confirm `processed/company_financials.parquet` and `processed/beneish_scores.parquet` appear

---

### Step 7 — Verify laptop reads from R2 (no local data needed)

```bash
# On laptop — delete local processed data to confirm R2 path works
rm -rf 01_Data/processed/

# Confirm R2 credentials are in .env, then run analysis
python 03_Analysis/beneish_screen.py
# Should load from R2 and produce 03_Analysis/beneish_scores.csv without error

# Run acceptance criteria check
pytest tests/test_acceptance_criteria.py -v
# All AC1–AC7 should PASS
```

---

## Verification Checklist

| Step | Check | Status |
|---|---|---|
| B1–B6 code changes | Implemented | ✅ Done |
| `uv sync` | Installs s3fs, boto3, duckdb | ✅ Done |
| Smoke test (no R2 creds) | Identical behavior to pre-change confirmed | ✅ Done |
| Acceptance criteria (local) | All AC1–AC7 PASS — confirmed Feb 27 2026 full run | ✅ Done |
| Cloudflare account + R2 bucket | `kr-forensic-finance` bucket created | ✅ Done (Feb 27, 2026) |
| R2 API token | Access Key ID + Secret saved | ✅ Done (Feb 27, 2026) |
| `.env` updated (laptop) | Four R2_ vars populated | ✅ Done (Feb 27, 2026) |
| Oracle Cloud VPS provisioned | SSH access confirmed | ✅ Done (Feb 27, 2026) — instance running at 168.107.21.26 |
| VPS setup | git clone + uv sync + .env populated | ✅ Done (Feb 27, 2026) — git clone + uv sync + .env populated |
| Pipeline on VPS (smoke) | "Uploaded to R2" in log | ⚠️ Partial (Feb 27, 2026) — R2 upload confirmed; PyKRX returned 0 tickers (KRX geo-block — see Step 6 note) |
| Pipeline on VPS (full) | Full KOSDAQ 2019–2023 run completes | ⬜ Pending — blocked by KRX geo-block |
| R2 bucket contents | Both parquet files visible in dashboard | ✅ Done (Feb 27, 2026) — company_financials.parquet confirmed uploaded |
| Laptop R2 read | beneish_screen.py works with no local data | ⬜ Pending (user action) |
| Acceptance criteria (R2) | All AC1–AC7 PASS from R2 | ⬜ Pending (user action) |

---

## Cost Estimate (Monthly)

| Service | Plan | Cost |
|---|---|---|
| Cloudflare R2 | Free tier (10 GB storage, zero egress) | $0 |
| Oracle Cloud Free Tier VPS | Always Free (VM.Standard.E2.1.Micro) | $0 |
| **Total** | | **$0/month** |

**Always Free means always free** — Oracle's Always Free tier does not expire after 12 months unlike AWS/GCP free tiers. The `VM.Standard.E2.1.Micro` shape is permanently free with no time limit.

---

## Phase 2 Scope (Not Yet Implemented)

The following were designed but deliberately deferred to Phase 2:

- **`--data-type` pipeline flag** for per-source incremental refresh (e.g., `--stage dart --data-type cb_bw`)
- **`01_Data/raw/refresh_manifest.json`** — lightweight record of what was last downloaded and when, uploaded to R2 alongside processed files
- **Daily OHLCV refresh** — PyKRX price/volume, needed for real-time timing anomaly signals
- **Weekly CB/BW and officer monitoring** — DART event-driven pulls

Design for all of the above is documented in `00_Reference/19_Data_Refresh_Cadence.md`.

---

## Phase 5 — Continuous Monitoring Infrastructure

The monitoring daemon (described in `08_Continuous_Monitoring_System.md`) runs three legs
continuously:

- **Leg 1** — watchlist management (updated from Phases 2–4 outputs)
- **Leg 2** — market polling via PyKRX every 5 minutes during KST trading hours
- **Leg 3** — DART RSS and news RSS, continuously

This is a long-running process. It cannot run on a laptop that sleeps or goes offline.
Phase 5 is the first milestone that **requires a persistent hosted process**.

### Option A — Oracle Cloud VPS (existing, recommended)

Already provisioned at `168.107.21.26` (ap-chuncheon-1, Chuncheon, South Korea).

**Advantages:**
- $0/month (Always Free — no expiry)
- South Korea region → correct KST timezone handling for market hours and DART timestamps
- Already set up with git clone + uv sync + .env

**Blocker:** The same PyKRX geo-block that prevents full pipeline runs on the VPS also
affects Leg 2. KRX returns 0 tickers from the Oracle Cloud data center IP. **This must be
resolved before the monitoring daemon can run on the VPS.** See the Step 6 note and
`00_Reference/19_Pipeline_Improvement_Areas.md` for the investigation path.

### Option B — Railway

Railway provides a clean worker service type (no web server needed) and good developer
experience for long-running daemons.

**Critical blocker:** PyKRX must be confirmed working from Railway IP ranges before
committing to this option. If KRX geo-blocks Railway's data center IPs (the same reason it
blocks Oracle Cloud), Leg 2 is broken and Railway cannot host the monitoring daemon.

**Pre-commit test:** Deploy a minimal Railway service and run:
```python
from pykrx import stock
print(stock.get_market_ticker_list('20230101', market='KOSDAQ'))
```
If this returns an empty list, Railway has the same geo-block as Oracle Cloud.

**Estimated cost:** ~$5–10/month for a small always-on worker (vs. $0 for the VPS).

### Recommendation

Start with the **Oracle Cloud VPS already provisioned**. Solve the PyKRX geo-block first —
the fix (browser header spoofing or a proxy) applies equally to both options. Evaluate
Railway only after confirming PyKRX returns tickers from a hosted IP, and only if VPS
management becomes a friction point.

### Storage

SQLite is sufficient for the match engine's trigger buffer at this scale. No managed
database is needed for either hosting option.
