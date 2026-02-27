# 24 — VPS Setup Procedure (Oracle Cloud Free Tier)

> **Scope:** Step-by-step procedure to set up the kr-forensic-finance pipeline on a fresh Oracle Cloud Ubuntu 22.04 instance.
> **Canonical for:** VPS rebuild procedure; known issues on VPS (PyKRX geo-block, uv run python requirement).
> **See also:** `20_Cloud_Infrastructure_Setup.md` for instance details, architecture, and provisioning steps.

## When to use this

- First-time VPS setup (done Feb 27, 2026)
- Rebuilding after instance termination or IP change
- Setting up on a second Oracle Free Tier instance

## Prerequisites

- Oracle Cloud instance running Ubuntu 22.04 Minimal (see `20_Cloud_Infrastructure_Setup.md` for provisioning steps)
- SSH key at `~/.ssh/ssh-key-2026-02-27.key` on your laptop
- GitHub repo at https://github.com/pon00050/kr-forensic-finance (public)
- `.env` values ready: `DART_API_KEY` + four `R2_*` variables

---

## Step 1 — Connect

From Git Bash on laptop:

```bash
ssh -i ~/.ssh/ssh-key-2026-02-27.key ubuntu@168.107.21.26
```

> **Note:** Oracle Cloud Ubuntu instances use the `ubuntu` user — not `root`. Use `sudo` for privileged commands.

---

## Step 2 — Update OS and install dependencies

```bash
sudo apt update && sudo apt upgrade -y
# When prompted about kernel upgrade list, press q
# Then reboot if needed:
# sudo reboot
# Reconnect after ~30 seconds

sudo apt install -y git nano
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

---

## Step 3 — Clone and install Python dependencies

```bash
git clone https://github.com/pon00050/kr-forensic-finance.git
cd kr-forensic-finance
uv sync
```

`uv sync` installs all dependencies including `setuptools<82` (required for pykrx — see Known Issues).

---

## Step 4 — Configure .env

```bash
cp .env.example .env
nano .env
# Fill in: DART_API_KEY, R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET
# Save: Ctrl+X → Y → Enter
```

---

## Step 5 — Smoke test

```bash
uv run python 02_Pipeline/pipeline.py --market KOSDAQ --start 2021 --end 2023 --sample 5 --sleep 0.1 --max-minutes 3
```

### Expected output

```
[INFO] Uploaded to R2: s3://kr-forensic-finance/processed/company_financials.parquet  ← confirms R2 works
[WARNING] PyKRX returned 0 KOSDAQ tickers  ← expected on VPS (KRX geo-block; see Known Issues)
```

---

## Known Issues on VPS

1. **PyKRX returns 0 tickers:** KRX API blocks data center IPs. Run the full pipeline from your laptop (Korean residential IP). R2 upload still works — the VPS is useful for analysis tasks that read from R2.

2. **`python` command not found:** Always use `uv run python` inside the project directory. Bare `python` or `python3` will not find the virtualenv.

3. **`setuptools<82` required:** pykrx depends on `pkg_resources`, which was removed in setuptools 82 (Feb 2026). The pin is in `pyproject.toml` so `uv sync` handles this automatically.

---

## Full Pipeline Run (from laptop — not VPS)

Due to the KRX geo-block, run the full data pull from your laptop:

```bash
python 02_Pipeline/pipeline.py --market KOSDAQ --start 2019 --end 2023
```

Data uploads to R2 automatically after each transform stage. The VPS can then run analysis scripts that read from R2.
