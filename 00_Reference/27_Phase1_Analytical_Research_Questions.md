# Phase 1 — Open Analytical Research Questions

**Status:** Open. All questions are pursuable with existing Phase 1 data
(`beneish_scores.parquet`) — no pipeline advancement required.

These questions emerged from visual inspection of `beneish_viz.html`. They are
recorded here as a structured research agenda for anyone who wants to go deeper
into the Phase 1 results before Phase 2 data becomes available.

---

## Q1 — Is SGI the primary driver of Critical flags, or does it just look that way?

**Observation:** Chart 4 in `beneish_viz.html` shows SGI (Sales Growth Index) as
the component with by far the largest average value among flagged companies — visually
dominating the other seven components.

**Why this warrants scrutiny:** SGI is simply a revenue growth ratio. Every growing
company triggers it regardless of accounting quality. Because SGI is one of the inputs
to the flag and carries a relatively high coefficient (+0.892), it will mechanically
appear elevated among flagged companies — this may be partly circular rather than
genuinely diagnostic.

**The real question:** Among the Critical-tier companies specifically, how many have
elevated DSRI and TATA *alongside* elevated SGI? That three-component combination —
revenue growing fast (SGI), receivables outpacing that growth (DSRI), and earnings not
backed by cash (TATA) — is the classic revenue inflation pattern. SGI alone is noise;
SGI + DSRI + TATA together is a signal worth acting on.

**Suggested analysis:**
- For each Critical company-year, identify which components are above their population
  median (not just above 1.0)
- Cluster Critical companies by their dominant component driver(s)
- Separate "SGI-only" flags (likely false positives) from "SGI + DSRI + TATA" flags
  (stronger manipulation signal)
- Check whether the "SGI-only" cluster overlaps heavily with `high_fp_risk = True`
  (biotech/pharma)

---

## Q2 — Which sectors are genuinely elevated versus structurally elevated?

**Observation:** Charts 2 and 5 together show that the flag rate and risk tier
distribution are not uniform across WICS sectors — certain sectors are consistently
and substantially higher than others.

**The distinction that matters:** Some sectors score high for entirely legitimate reasons
(biotech and pharma: elevated SGI and AQI are structurally expected in growth-stage R&D
companies — this is what the `high_fp_risk` flag captures). Other sectors scoring high
may not have an obvious structural explanation, and an elevated flag rate in those sectors
is a stronger investigative signal.

**The real question:** Which sectors have elevated flag rates that *cannot* be explained
by sector-level growth dynamics, IFRS accounting choices, or industry norms? Those are
the sectors where the screen is likely picking up genuine anomalies at higher-than-chance
rates.

**Suggested analysis:**
- Separate sectors into two buckets: those with a known structural false-positive reason
  (biotech, pharma, early-stage tech) and those without
- For the "no obvious structural reason" sectors, examine the component-level breakdown:
  is the elevation driven by TATA and DSRI (accounting manipulation signals) or by SGI
  alone (growth signal)?
- Cross-reference sector flag rates with sector-level revenue growth benchmarks: is a
  sector's elevated SGI consistent with actual industry growth, or does it stand out?

---

## Q3 — Are Critical flags concentrated in a small number of repeat offenders, or broadly distributed?

**Observation:** The dataset covers 2020–2023 (four score periods per company). A company
that is flagged in a single year may have experienced a one-time business event. A company
that is flagged Critical in three or four consecutive years is exhibiting a persistent pattern.

**Why persistence matters:** Persistent multi-year flags are a materially stronger signal
than one-off flags. Earnings manipulation is difficult to sustain indefinitely; a company
maintaining elevated M-Scores over multiple years is either (a) continuously manipulating,
(b) in a sustained business deterioration that creates ongoing manipulation pressure, or
(c) in a sector where the structural false-positive pattern is persistent. All three
warrant different but specific follow-up.

**Suggested analysis:**
- Count Critical flags per `corp_code` across the four score years
- Identify companies with 3 or 4 consecutive Critical flags — this is a much shorter list
  than the full Critical population and represents the highest-priority investigation targets
- For the persistent flaggers, check `fs_type_switched`: a company that flipped between
  CFS and OFS mid-period may be generating artificial flags from the accounting basis change
  rather than genuine manipulation

---

## Q4 — Do the CFS/OFS filers behave differently in the flag distribution?

**Observation:** The `fs_type` column distinguishes consolidated (CFS) from standalone
(OFS) financial statement filers. The `fs_type_switched` column flags companies that
changed basis across years. Approximately 40–60% of KOSDAQ companies file OFS only.

**Why this matters analytically:** Mixing CFS and OFS data across years introduces
mechanical noise into several components — particularly DSRI, GMI, and TATA — because
the scope of the consolidated entity changes. A company that acquires a subsidiary and
switches from OFS to CFS will show dramatic balance sheet changes that have nothing to do
with earnings manipulation.

**Suggested analysis:**
- Compare flag rates and risk tier distributions between pure-CFS, pure-OFS, and
  switched filers
- If `fs_type_switched = True` companies are over-represented in the Critical tier,
  that suggests some Critical flags are accounting-basis artifacts rather than genuine
  signals — and those companies should be de-prioritized in any follow-up investigation

---

*Document created Feb 28, 2026 following visual inspection of beneish_viz.html Phase 1 results.*
*All analyses are pursuable with `01_Data/processed/beneish_scores.parquet` and standard pandas.*
