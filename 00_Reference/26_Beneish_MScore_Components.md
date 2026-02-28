# Beneish M-Score: Components Reference

> **What this document is:** A plain-language explanation of the eight variables that make up
> the Beneish M-Score — the analytical backbone of Phase 1 of this project. Written for
> readers who understand financial statements but are not familiar with the model.

---

## Background

The Beneish M-Score is a statistical model that uses eight financial ratios to estimate
the probability that a company has manipulated its reported earnings. It was developed by
Professor Messod D. Beneish of Indiana University's Kelley School of Business and published in:

> **"The Detection of Earnings Manipulation"**
> *Financial Analysts Journal*, Vol. 55, No. 5, pp. 24–36, 1999.
> DOI: https://www.tandfonline.com/doi/abs/10.2469/faj.v55.n5.2296

The model was trained on 74 confirmed earnings manipulators (1982–1992) matched against
2,332 non-manipulators from US public company filings.

---

## The M-Score Formula

The overall score is a weighted sum of the eight components:

```
M-Score = −4.84
        + (0.920 × DSRI)
        + (0.528 × GMI)
        + (0.404 × AQI)
        + (0.892 × SGI)
        + (0.115 × DEPI)
        − (0.172 × SGAI)
        + (4.679 × TATA)
        − (0.327 × LVGI)
```

Six components carry **positive** coefficients — a higher value increases the score and
raises the manipulation probability. Two (**SGAI** and **LVGI**) carry **negative**
coefficients — a higher value actually lowers the score. This is counterintuitive and is
explained in the per-component sections below.

---

## Decision Thresholds

| M-Score | Interpretation |
|---|---|
| > −1.78 | **Likely manipulator** — flag for review (used in this project) |
| −2.22 to −1.78 | Grey zone — possible manipulator |
| < −2.22 | Unlikely manipulator |

The −1.78 cutoff is from the 8-variable model and is the stricter threshold used in practice.
The −2.22 cutoff is from the earlier 5-variable model and is used by GMT Research for Asian
markets when SG&A and COGS are not separately disclosed (approximately 19% of KOSDAQ companies).

These thresholds are decision-rule choices, not hard statistical boundaries. Beneish set them
to balance sensitivity (catching actual manipulators) against specificity (avoiding false positives).

---

## Documented Model Accuracy

| Metric | Value |
|---|---|
| True positive rate (manipulators correctly flagged) | ~76% |
| False positive rate (non-manipulators incorrectly flagged) | ~17.5% |
| Real-world validation (1998–2002 major fraud cases) | 12 of 17 correctly flagged (71%) |
| Out-of-sample return gap (1993–2007) | Flagged companies underperformed by ~9.7% per year |

**Implication for this project:** Roughly 1 in 4 actual manipulators will be missed, and
roughly 1 in 6 clean companies will be incorrectly flagged. The model is a screen, not a
verdict. All flags require human review.

---

## The 8 Components

Each component is computed as a **ratio of year T to year T-1**. A value of 1.0 is neutral
(no change). Values above 1.0 mean the metric worsened or grew year-over-year; values below
1.0 mean it improved or shrank.

---

### 1. DSRI — Days Sales in Receivables Index

**Coefficient:** +0.920

**Formula:**
```
DSRI = (Receivables_t / Sales_t) ÷ (Receivables_{t-1} / Sales_{t-1})
```

**What it measures:** Whether accounts receivable are growing faster than sales. A ratio
above 1.0 means the company is collecting a smaller share of its revenue in cash this year
compared to last year.

**Why it signals manipulation:** Revenue inflation is one of the most common forms of
earnings manipulation. A company recording fictitious or premature revenue will show rising
receivables — it books the sale but the cash never arrives (or arrives much later). If
receivables grow much faster than actual sales, that gap is suspicious.

**Legitimate reasons for elevation:** Genuine expansion into new markets with longer
payment terms; acquisitions bringing in customers with different billing cycles; seasonal
timing effects.

---

### 2. GMI — Gross Margin Index

**Coefficient:** +0.528

**Formula:**
```
GMI = Gross Margin_{t-1} ÷ Gross Margin_t
       where Gross Margin = (Sales − COGS) / Sales
```

Note: GMI is prior year ÷ current year, so a value above 1.0 means **margins deteriorated**.

**What it measures:** Whether gross profitability declined year-over-year. GMI above 1.0
means this year's gross margin is lower than last year's.

**Why it signals manipulation:** Declining margins signal weakening competitive position or
pricing power. When management knows investors are watching margin trends, a deteriorating
margin creates pressure to compensate by inflating revenue or understating cost of goods
sold. The model captures this incentive pressure.

**Legitimate reasons for elevation:** Industry-wide pricing pressure; strategic shift toward
lower-margin products; raw material cost spikes; early-stage companies deliberately investing
margin into growth.

**Data note for Korea:** Companies filing income statements under "nature of expense"
classification (성격별 분류) do not separately disclose COGS, so GMI cannot be calculated.
Approximately 19% of KOSDAQ companies fall into this category. Those rows use 1.0 (neutral).

---

### 3. AQI — Asset Quality Index

**Coefficient:** +0.404

**Formula:**
```
AQI = (1 − (Current Assets_t + PP&E_t) / Total Assets_t) ÷
      (1 − (Current Assets_{t-1} + PP&E_{t-1}) / Total Assets_{t-1})
```

The numerator of each fraction is the share of total assets that is **neither** current
assets nor PP&E — i.e., the "soft" portion: goodwill, intangibles, deferred costs, and other
long-term assets.

**What it measures:** Whether a company is accumulating intangible, difficult-to-value assets
relative to its total asset base.

**Why it signals manipulation:** Assets like goodwill, deferred charges, and capitalized
development costs are harder to value independently and easier to overstate. Rising AQI can
indicate that the company is capitalizing costs that should be expensed (deferring losses into
the future) or booking goodwill aggressively through acquisitions — both of which inflate
current reported earnings.

**Legitimate reasons for elevation:** Acquisitions naturally add goodwill; R&D-intensive
industries (biotech, software) legitimately capitalize development costs under IFRS IAS 38;
capital-light business models structurally carry higher intangible-to-total-asset ratios.

---

### 4. SGI — Sales Growth Index

**Coefficient:** +0.892

**Formula:**
```
SGI = Sales_t / Sales_{t-1}
```

This is simply the revenue growth ratio. SGI of 1.20 means 20% revenue growth.

**What it measures:** Year-over-year revenue growth.

**Why it signals manipulation:** SGI above 1.0 means the company is growing — which is not
inherently suspicious. The model includes it because Beneish found empirically that
manipulators as a group had higher-than-average sales growth relative to peers. The mechanism
is **incentive pressure**: companies growing fast are priced as growth stocks; if growth slows,
share prices fall sharply; that pressure motivates management to sustain the growth narrative
through manipulation.

**Important caveat:** SGI has the **highest false positive risk** of all eight components.
Any legitimately high-growth company will trigger this component. It should never be
evaluated in isolation. The `high_fp_risk` flag in this project specifically targets the
sectors (biotech, pharma) where elevated SGI is structurally expected.

---

### 5. DEPI — Depreciation Index

**Coefficient:** +0.115 *(smallest positive weight)*

**Formula:**
```
DEPI = (Dep_{t-1} / (Dep_{t-1} + PP&E_{t-1})) ÷ (Dep_t / (Dep_t + PP&E_t))
```

Each fraction is the depreciation rate as a share of gross fixed assets. A value above 1.0
means the depreciation rate **slowed** this year compared to last year.

**What it measures:** Whether the company reduced its depreciation charge by extending
estimated asset useful lives or changing its depreciation method.

**Why it signals manipulation:** Slower depreciation directly increases reported pre-tax
income with no operational improvement. Extending asset useful lives is a legitimate
accounting estimate, but when it coincides with other manipulation signals, it suggests
earnings management to hit targets.

**Legitimate reasons for elevation:** Shift in asset mix toward longer-lived assets; new
PP&E added late in the year (less than a full period of depreciation); acquisitions of
assets with genuinely longer remaining useful lives.

**Data note:** DEPI requires depreciation expense (감가상각비) as a separate line item from
the cash flow statement — not available in OpenDartReader's key-accounts batch endpoint;
requires the full-statement endpoint (`fnlttSinglAcntAll`).

---

### 6. SGAI — Sales, General and Administrative Expenses Index

**Coefficient:** −0.172 *(negative — counterintuitive)*

**Formula:**
```
SGAI = (SG&A_t / Sales_t) / (SG&A_{t-1} / Sales_{t-1})
```

**What it measures:** Whether SG&A overhead is growing faster than sales.

**Why the coefficient is negative:** This is empirically determined, not theoretically
derived. Despite SGAI > 1 signaling operational inefficiency — which creates manipulation
incentive — Beneish's data showed that companies that were actually manipulating earnings
more often held SG&A flat or reduced it (while inflating revenue), whereas non-manipulators
showed higher SG&A growth in the same periods. In practice, rising SGAI slightly *lowers*
the M-Score.

**Legitimate reasons for elevation:** Genuine investment in sales or marketing for growth;
post-acquisition integration costs booked in SG&A; new market entry with high customer
acquisition costs.

**Data note:** Same as GMI — requires separate SG&A disclosure; unavailable for
nature-of-expense filers.

---

### 7. LVGI — Leverage Index

**Coefficient:** −0.327 *(negative — counterintuitive)*

**Formula:**
```
LVGI = ((Current Liabilities_t + Long-Term Debt_t) / Total Assets_t) ÷
       ((Current Liabilities_{t-1} + Long-Term Debt_{t-1}) / Total Assets_{t-1})
```

**What it measures:** Whether total debt burden relative to total assets increased or
decreased year-over-year. LVGI > 1 means the company became more leveraged.

**Why the coefficient is negative:** The theoretical prior is that rising leverage increases
covenant-breach risk and therefore creates earnings-manipulation incentive. However,
Beneish's data contradicted this. Companies that were actually manipulating more often
*reduced* leverage — they were boosting reported equity through inflated retained earnings
and share issuance rather than taking on additional debt. Companies taking on more debt do
so through arm's-length transactions with lenders who perform independent due diligence —
a genuine economic activity with external validation. An increase in leverage therefore
correlates *negatively* with manipulation in the original sample.

---

### 8. TATA — Total Accruals to Total Assets

**Coefficient:** +4.679 *(largest weight by a wide margin)*

**Formula (2013 updated version — used in this project):**
```
TATA = (Net Income Before Extraordinary Items_t − Cash From Operations_t) / Total Assets_t
```

**What it measures:** The accrual component of reported earnings — the gap between what a
company reports as net income and what it actually collected in operating cash. Large positive
TATA means reported earnings significantly exceed cash generation; the difference is made up
of accounting accruals (estimates and deferrals).

**Why it signals manipulation — and why it has the largest coefficient:**
Cash earnings are objective and hard to fake. Accrual earnings reflect management's
discretionary accounting judgments: when to recognize revenue, how to estimate bad debt,
whether to capitalize or expense a cost. Accruals are precisely the levers manipulators
pull. TATA is the most direct mechanical signal of active earnings management rather than
incentive pressure, which is why Beneish's regression assigned it the highest weight.

The relationship between high accruals and future stock underperformance was separately
documented by Sloan (1996) in what became known as the "accrual anomaly."

**Legitimate reasons for high TATA:**
- Long-term contracts where revenue is earned before cash is received (construction,
  defense, SaaS with annual billings)
- Legitimate non-cash gains (fair value adjustments, reversal of provisions)
- Rapid working capital investment during growth phases

---

## How the Components Work Together

No single component is sufficient to reach a conclusion. The model is designed to catch
companies where multiple signals align simultaneously:

- **DSRI + TATA elevated together:** Revenue may be recognized but not collected, and
  earnings are dominated by accruals rather than cash — a classic revenue inflation pattern.
- **GMI + SGI elevated together:** Margins are deteriorating even as growth is high —
  the growth may be purchased through unsustainable discounting or channel stuffing.
- **AQI + DEPI elevated together:** Both soft assets and depreciation manipulation point
  toward balance sheet manipulation to sustain reported asset values.
- **Single component elevated in isolation:** Much weaker signal; usually explainable by
  sector norms or legitimate business events.

---

## Documented False Positive Sectors

| Sector / Situation | Elevated Components | Reason |
|---|---|---|
| High-growth technology / platforms | SGI, DSRI, AQI | Rapid growth and intangible asset accumulation are normal |
| Biotech / pharmaceutical (growth stage) | SGI, AQI, DSRI | R&D capitalization, milestone billings, growth dynamics |
| Companies making acquisitions | AQI, LVGI, DSRI | Goodwill, integration costs, acquired receivable pools |
| Construction / long-term contracts | TATA | Revenue before cash collection is standard under % completion |
| Companies facing genuine margin compression | GMI | Industry-wide pricing pressure is not manipulation |
| Financial institutions | All components | Model does not apply; balance sheet structure is incompatible |
| Korean 성격별 분류 filers | GMI, SGAI | COGS and SG&A not separately disclosed; components set to 1.0 |

---

## Known Real-World Cases

**Enron (flagged 1998, collapsed 2001):** Cornell students applying the M-Score to Enron's
1998 financial statements identified it as a probable manipulator while the stock was still
trading at roughly half its eventual peak. Enron's M-Score in 2000 has been estimated at
approximately +3.72 — far above both thresholds. The signals were present in the public
filings; they were not acted upon.

**12 of 17 major US frauds (1998–2002):** An ex-post study found the model correctly flagged
71% of the highest-profile accounting fraud cases from that period. WorldCom and Satyam are
referenced in academic literature as cases where the model's signals were present in advance.

**Investment return signal (1993–2007):** Over a 15-year out-of-sample period, companies
flagged above the manipulation threshold returned approximately 9.7% less per year than
non-flagged companies — confirming the model's ongoing predictive utility beyond its original
training data.

---

## What the Model Does Not Detect

- Revenue **understatement** (companies hiding profits to avoid taxes or regulatory scrutiny)
- Related-party transaction manipulation that does not run through reported accruals
- Tax evasion
- Manipulation structured specifically to stay below the M-Score thresholds on each component
  while still inflating earnings
- Fraud at entities that file no public financial statements

---

## Scope Limitations

The model was developed on US public companies filing under US GAAP (1982–1992). Applied to
Korean KOSDAQ companies filing under K-IFRS, structural differences exist:

- **성격별 분류 filers (~19%):** GMI and SGAI cannot be calculated; those rows use 1.0 (neutral).
- **CFS vs. OFS mixing:** Companies that switch between consolidated and standalone statements
  across years introduce noise into all eight components.
- **No Korean-specific threshold recalibration:** No published study has re-estimated the
  thresholds or coefficients on a Korean sample. The −1.78 threshold is applied as-is.
- **Financial sector exclusion:** KSIC codes 640–669 are excluded from this project's screen.

---

*Sources: Beneish (1999), Financial Analysts Journal; GMT Research Asian Markets Report;
Corporate Finance Institute; Wikipedia (Beneish M-score); Indiana University Kelley School
of Business working materials.*
