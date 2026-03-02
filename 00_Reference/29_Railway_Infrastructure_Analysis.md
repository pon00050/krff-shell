# Railway + Infrastructure Options Analysis

> **Scope:** Deep analysis of Railway, Oracle Cloud VPS, and Mac Mini M4 as hosting
>   options for the Phase 5 continuous monitoring daemon.
> **Canonical for:** Infrastructure options analysis; Phase 5 hosting decision.
> **See also:** `20_Cloud_Infrastructure_Setup.md` (current infra), `08_Continuous_Monitoring_System.md`
> **Supersedes:** The Railway vs. Oracle brief in `20_Cloud_Infrastructure_Setup.md` Phase 5 section
>   (that section remains as a pointer to this doc).

*Created: March 2, 2026.*

---

## Section 1 — The Pivotal Prerequisite Test

**Run this test before committing to any hosted platform for Phase 5.**

Both Railway and Oracle Cloud VPS share the same PyKRX geo-block problem. KRX
(`data.krx.co.kr`) blocks requests from data center IP ranges — this is the confirmed
root cause of PyKRX returning 0 tickers from Oracle Cloud ap-chuncheon-1. Any hosted
platform (Railway, AWS, GCP, Azure, Oracle Cloud) is likely affected identically.

Leg 2 of the monitoring daemon (intraday price/volume polling during KST trading hours)
requires PyKRX. If PyKRX is blocked, Leg 2 cannot run on the hosted platform and must
be moved elsewhere.

**Pre-commit test — run on the target platform before signing up:**

```python
from pykrx import stock
tickers = stock.get_market_ticker_list('20230101', market='KOSDAQ')
print(f"Ticker count: {len(tickers)}")
# Expected: ~1,700
# If 0 is returned → KRX geo-block confirmed; Leg 2 cannot run here
```

For Railway specifically: deploy a minimal service (one Python file, one `requirements.txt`
with `pykrx`) and run this test before any Phase 5 infrastructure investment.

**See:** `00_Reference/19_Pipeline_Improvement_Areas.md` item I1 for tracking status.

---

## Section 2 — The Three-Environment Split

Regardless of which hosted platform is chosen, the correct Phase 5 architecture
separates concerns by IP requirement:

```
Laptop / Mac Mini (Korean residential IP)
  └── PyKRX extraction (price_volume.parquet, Leg 2 intraday polling)
  └── Full pipeline runs (Phases 1–2 pattern — batch extraction + transform)
  └── Upload processed parquets to Cloudflare R2

Always-on hosted process (Railway OR Oracle VPS)
  └── Leg 3: DART RSS + news classification (no PyKRX needed)
  └── Match engine (reads from Postgres/SQLite; reads parquets from R2)
  └── Alert dispatch (email/Slack)
  └── DART-only batch cron (financials refresh — no PyKRX needed)

Cloudflare R2 (neutral ground — no geo-block concern)
  └── All processed parquets (company_financials, beneish_scores, cb_bw_events, etc.)
  └── All environments read from here — single source of truth for processed data
```

This split means the hosted platform only needs to handle Legs 1 and 3 (DART + news).
PyKRX (Leg 2) always runs from a Korean IP regardless of platform choice.

---

## Section 3 — Option A: Oracle Cloud VPS (current)

**Status:** Already provisioned (ap-chuncheon-1, ARM64 Ubuntu).

See `00_Reference/20_Cloud_Infrastructure_Setup.md` for full provisioning steps,
`00_Reference/24_VPS_Setup_Procedure.md` for the step-by-step rebuild procedure.

**Summary:**
- Cost: $0/month (Always Free tier — 4 OCPU, 24 GB RAM, 200 GB storage)
- Already provisioned and configured — no new work required
- PyKRX geo-block confirmed: returns 0 tickers (Leg 2 cannot run here)
- Legs 1 + 3 and the match engine work fine
- Management: SSH + systemd (medium ops overhead)
- No managed Postgres — SQLite or manual Postgres install required
- No preview environments

**Verdict:** Best choice when no budget is available and Leg 2 is acceptable to run
from a separate Korean IP machine (laptop or Mac Mini).

---

## Section 4 — Option B: Railway

Railway is a managed Platform-as-a-Service with multi-service private networking,
native managed Postgres, and GitHub-triggered auto-deploy.

**Key differentiators over Oracle VPS:**

- **Multi-service private networking:** Each component (daemon, match engine, API) runs
  as a separate Railway service. They share a private network — no public exposure
  required for inter-service calls.
- **Preview environments:** Each pull request gets an isolated clone of the entire
  service stack. This is uniquely valuable for testing monitoring rule calibration
  changes (e.g., adjusting CB/BW alert thresholds) without touching production.
- **Managed Postgres:** First-class managed database — no setup, automatic backups,
  connection pooling. Replaces the manual SQLite approach on Oracle VPS.
- **Zero-ops deploys:** `git push` triggers automatic rebuild and deploy for all
  services. No SSH required for routine maintenance or dependency updates.

**Cost:** ~$5–10/month (Hobby plan, scales with actual resource usage).

**Geo-block status:** UNKNOWN — must run the Section 1 test before committing.
Railway uses AWS/GCP backend IPs. KRX is known to geo-block data center IPs.
If the test returns 0, Leg 2 must be moved to a Korean IP source (same split
architecture as Oracle VPS).

**Deployment sketch (3 services + 1 database):**

```
Service: leg3-monitor
  → Leg 3 daemon (DART RSS polling + news classification via Claude Haiku)
  → Runs continuously; wakes every 15 min for RSS check
  → Environment vars: DART_API_KEY, ANTHROPIC_API_KEY, DATABASE_URL

Service: match-engine
  → 3-way match buffer evaluation (DART event + price spike + news signal)
  → Cron: every 15 min during KST trading hours
  → Reads price_volume.parquet from R2 (written by laptop/Mac Mini)
  → Writes match_events to Postgres
  → Environment vars: R2_* credentials, DATABASE_URL

Service: api (Phase 5+)
  → FastAPI serving /scores, /alerts, /company/{ticker}
  → Read-only query layer over Postgres + R2
  → Environment vars: DATABASE_URL, R2_* credentials

Database: Railway Postgres
  → Tables: watchlist, leg3_triggers, match_events, alert_log, company_metadata
  → Accessed by all three services via private network DATABASE_URL

Service: leg2-monitor (BLOCKED)
  → PyKRX intraday polling
  → Status: blocked pending geo-block investigation (Section 1 test)
  → If blocked: remove this service; route Leg 2 to laptop/Mac Mini cron
```

**`railway.toml` sketch:**
```toml
[build]
builder = "NIXPACKS"

[[services]]
name = "leg3-monitor"
source = "02_Pipeline/monitor_leg3.py"
startCommand = "python 02_Pipeline/monitor_leg3.py"

[[services]]
name = "match-engine"
source = "02_Pipeline/match_engine.py"
startCommand = "python 02_Pipeline/match_engine.py"
cron = "*/15 1-7 * * 1-5"  # Every 15 min, 10:00–16:30 KST (UTC+9)
```

**Verdict:** Best choice when a clean ops experience, managed Postgres, and preview
environments are valued, AND when budget of ~$10/month is acceptable. Must verify
PyKRX geo-block status before committing Leg 2 here.

---

## Section 5 — Option C: Mac Mini M4

### What it is

Apple Mac Mini M4 (2024) — a compact desktop that can run as an always-on server at
a Korean residential or business address.

### Why it matters for this project specifically

A Mac Mini at a Korean residence is a physical device with a **Korean residential IP**.
This permanently solves the PyKRX geo-block — KRX does not block residential IPs, only
data center IPs. No VPN proxy, no header spoofing, no workarounds. It can run all three
legs of the monitoring daemon AND the full pipeline extraction.

**Critical caveat:** The Mac Mini must be physically located at a Korean address with a
Korean residential or business internet connection. If no Korean address is currently
available, this option is future-viable — mark it for when a Korean address is
established.

### Hardware specs (M4, 2024)

| Spec | Value |
|---|---|
| CPU | Apple M4 (10-core: 4 performance + 6 efficiency) |
| RAM | 16 GB unified memory (base); 24–64 GB on M4 Pro |
| Storage | 256 GB SSD (base) — upgrade to 512 GB or 1 TB for data work |
| Connectivity | 3× Thunderbolt 4, HDMI 2.1, Gigabit Ethernet, Wi-Fi 6E, Bluetooth 5.3 |
| Size | 5 × 5 × 2 inches |
| Price | $599 base; ~$479–499 on sale (observed Mar 2026) |
| M4 Pro | $1,399 (24 GB, 512 GB) — unnecessary for this use case |

### Power consumption

| State | Watts |
|---|---|
| Idle | 3–4 W (Jeff Geerling measurement on M4 Mac Mini) |
| Peak (HPL benchmark) | 42 W |
| Python daemon workload (estimated) | ~5–8 W |
| Annual electricity at idle (5W × 8,760 hr × $0.10/kWh) | ~$4.40/year |

**Effectively zero ongoing operating cost.**

### Python / uv compatibility

- macOS on M4 (ARM64): Python 3.11+ runs natively; all project dependencies confirmed
- `uv` installs cleanly on macOS; `uv sync` works without modification
- pykrx, opendartreader, pandas, duckdb, s3fs — all have ARM64 wheels available
- No cross-compilation required

### Always-on daemon setup (macOS)

- **SSH access:** System Settings → Sharing → Remote Login (one toggle)
- **Auto-restart on power failure:** System Settings → Energy → "Start up automatically after power failure"
- **Daemon management:** `launchd` (macOS equivalent of systemd)
  - Create a `.plist` file in `~/Library/LaunchAgents/`; load with `launchctl`
  - More GUI-friendly than systemd; logs via `Console.app` or `log stream`
- **Prevent sleep:** `sudo pmset -a sleep 0 disksleep 0`
- **Remote management:** SSH for terminal; Screen Sharing for GUI (no monitor needed post-setup)

### Setup path (when Korean address is available)

```bash
# On Mac Mini — one-time setup

# 1. Enable SSH
#    System Settings → Sharing → Remote Login → ON

# 2. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone and install project
git clone https://github.com/pon00050/kr-forensic-finance.git
cd kr-forensic-finance
uv sync

# 4. Configure environment
cp .env.example .env
nano .env  # Add DART_API_KEY, R2_* credentials, ANTHROPIC_API_KEY

# 5. Prevent sleep
sudo pmset -a sleep 0 disksleep 0

# 6. Verify PyKRX works (the critical test)
python -c "
from pykrx import stock
tickers = stock.get_market_ticker_list('20230101', market='KOSDAQ')
print(f'Ticker count: {len(tickers)}')
# Expected: ~1,700 (not 0)
"

# 7. Set up launchd daemon for the monitoring process
#    Create ~/Library/LaunchAgents/com.kr-forensic.monitor.plist
#    Load with: launchctl load ~/Library/LaunchAgents/com.kr-forensic.monitor.plist
```

### Comparison table

| Criterion | Mac Mini M4 | Railway | Oracle VPS |
|---|---|---|---|
| PyKRX geo-block | **SOLVED** (residential IP) | Unknown (test required) | Confirmed blocked |
| Full pipeline (all 3 legs) | **YES** | NO (Leg 2 blocked if geo-blocked) | NO (Leg 2 blocked) |
| Cost | $599 one-time + ~$4/yr electricity | ~$10/month (~$120/yr) | $0/month |
| Upfront cost | $599 | $0 | $0 |
| Break-even vs. Railway | ~5 months | — | — |
| Setup complexity | Low (macOS GUI + launchd) | Very low (git push) | Medium (SSH + systemd) |
| Managed Postgres | No (SQLite or manual install) | **Yes (first-class)** | No |
| Preview environments | No | **Yes** | No |
| Ops overhead | Low | Very low | Medium |
| Physical Korean location required | **YES** | No | No |
| Reliability | Consumer hardware (add UPS) | Managed | Managed |

### Risks

- **macOS auto-updates:** Security updates can trigger unscheduled reboots. Configure
  update timing or defer with `sudo softwareupdate --ignore <update-name>`.
- **SSD failure:** 3–5 year lifespan under 24/7 load. Add Time Machine backup to an
  external USB drive. Processed parquets are in R2 (safe); only daemon state (SQLite
  alert log) needs local backup.
- **Power outage:** Add a small UPS ($30–60) for clean shutdown and auto-restart.
- **No hot-swap redundancy:** If the Mac Mini fails, monitoring is offline until
  repaired. For a research tool (not production trading), this is acceptable.

### Verdict

When a Korean address is available, the Mac Mini M4 is the strategically superior
option for Phase 5. It permanently solves the geo-block, runs all three legs without
compromise, and costs less than 5 months of Railway usage over a 2-year horizon.

**Until a Korean address is established:** the Railway vs. Oracle VPS comparison
applies (Section 3 vs. Section 4). Mac Mini is marked "viable when Korean address
is established."

---

## Section 6 — Decision Guide

```
Do you have a Korean residential/business address where you can
leave a Mac Mini running 24/7?
  │
  ├── YES → Mac Mini M4 ($599 one-time)
  │         Solves geo-block permanently. Runs full pipeline. ~$4/yr electricity.
  │         Buy a UPS ($30–60). Set up launchd. Done.
  │         → See Section 5 setup path above.
  │
  └── NO → Is PyKRX geo-blocked from Railway IPs?
            (Run the Section 1 test on a Railway service first)
            │
            ├── YES (0 tickers returned) → Oracle Cloud VPS (already provisioned, $0)
            │   Leg 2 polling must run from another Korean IP (laptop cron, future Mac Mini)
            │   Legs 1 + 3 and match engine work fine on VPS.
            │   → See 20_Cloud_Infrastructure_Setup.md + 24_VPS_Setup_Procedure.md
            │
            └── NO (tickers returned) → Railway (~$10/month)
                Cleaner ops, managed Postgres, preview environments.
                Leg 2 works from Railway IPs.
                → See Section 4 deployment sketch above.
```

---

## Appendix — Related Documents

| Document | Relevance |
|---|---|
| `20_Cloud_Infrastructure_Setup.md` | Oracle VPS + R2 provisioning detail; current infra state |
| `24_VPS_Setup_Procedure.md` | Step-by-step VPS rebuild; known issues list |
| `08_Continuous_Monitoring_System.md` | Three-leg monitoring architecture (DART + news + price) |
| `19_Pipeline_Improvement_Areas.md` | Item I1: geo-block verification tracking |
