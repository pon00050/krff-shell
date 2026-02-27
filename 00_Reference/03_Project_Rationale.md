# Project Rationale: Infrastructure First

> **Scope:** Why this project exists — the CB/BW 3자배정 manipulation scheme, why public data is sufficient to surface it, and the infrastructure-first framing.
> **Canonical for:** CB/BW manipulation scheme explanation; public data sufficiency argument.
> **See also:** `01_Policy_Context.md` (regulatory trigger), `07_Automation_Assessment.md` (automation limits)

## The Core Insight

The data exists. The manipulation patterns are documented. The regulatory incentive structure is being strengthened. What does **not** exist publicly is a maintained, reproducible pipeline that joins these sources into a single queryable dataset.

This project builds that missing infrastructure layer — not a single investigation, but the foundation that makes systematic investigation possible.

---

## What Gap This Fills

### What investigators have but researchers lack
- Actual trading account data (who bought what, through which broker, in what sequence)
- Phone and communications records
- Bank account flows beyond financial statement disclosure

### What researchers can build that investigators don't prioritize
- Systematic screening across all 2,400+ listed companies simultaneously
- Reproducible, documented methodology that can be audited and extended
- Cross-source joins (DART financials + SEIBRO CB events + KRX price/volume + KFTC networks) that no single institution maintains as a unified dataset
- Public transparency — outputs publishable as open data

The institutions have depth on specific targets. Independent infrastructure can provide breadth across the whole market — a triage layer that tells them where to look.

---

## Why "Infrastructure First" Is the Right Scope

### One person + AI tools cannot investigate everything

The Epstein forensic finance project spent 70+ sessions analyzing 1.48 million documents for a single subject. The Korean listed market has 2,400+ companies. Full investigation of each is not feasible.

What is feasible: building a screen that reduces the universe from 2,400 companies to a ranked list of, say, 20–50 that exhibit multiple simultaneous anomaly signals. That prioritized list has genuine value for any downstream investigator.

### The scope that is completable

A focused pipeline targeting three signal types:

| Signal | Data required | Methodology |
|---|---|---|
| Earnings manipulation probability | DART financial statements (5 years) | Beneish M-Score |
| CB/BW dilution pattern | DART issuances + SEIBRO exercise history + KRX price/volume | Timeline reconstruction |
| Disclosure timing anomaly | DART filing timestamps + KRX intraday/daily price movements | Timestamp delta analysis |

Each of these is independently buildable. They compound in value when layered together — a company that scores high on all three is a much stronger signal than one that triggers only one.

### Portfolio value is independent of any investigation outcome

A documented, public Korean capital markets data pipeline is a legitimate portfolio artifact regardless of whether it surfaces anything actionable. It demonstrates:
- Korean financial data literacy (DART, KRX, SEIBRO, KFTC ecosystems)
- ETL and data pipeline architecture
- Domain knowledge (accounting methodology applied to an actual market)
- Bilingual technical capacity (Korean regulatory data + English documentation)

This is directly relevant to the Fintech/Payments Infrastructure career cluster and the Compliance/Audit Tech track (see Career Options Evaluation document).

---

## Who Can Build On This

| Audience | How they use it |
|---|---|
| Investigative journalists (한겨레, 경향, JTBC 탐사팀) | Prioritized target list from anomaly rankings; methodology they can cite |
| Academic researchers | Clean, reproducible dataset for market microstructure or accounting studies |
| Short-sellers | Public data screen as starting point for deeper proprietary research |
| FSC/FSS analysts | Triage intelligence — where to deploy their non-public investigative tools |
| Other developers | Building block for more sophisticated models |

The goal is to be the infrastructure layer. Others bring the investigative depth.

---

## Connection to the CB/BW Manipulation Pattern

The 3자배정 CB/BW scheme is the best-documented and most systematic form of KOSDAQ manipulation. Its full footprint is visible in public data:

1. **DART**: CB issuance notice (주요사항보고서) with 3자배정 terms and exercise price
2. **DART**: Subsequent officer/major shareholder holding changes (concealed beneficial ownership)
3. **DART**: False 신사업 announcements (optimistic disclosures preceding price run-up)
4. **SEIBRO**: Actual conversion/exercise event — timing relative to price peak
5. **KRX**: Price and volume data showing the pump-and-dump pattern
6. **DART**: Post-exit holding disclosures (if any) showing insider exit

Each of these data points exists publicly. None of them have been systematically joined into a unified, screened dataset available to the public. This pipeline does that.

---

## Regulatory Context

The FSC/FSS 2023 investigation into samo CB abuse resulted in 33 prosecutions across 14 cases, with approximately 840 billion won in illicit gains. Private CB issuance grew from 4.6 trillion won (2013–2015) to 23.2 trillion won in the three years preceding the crackdown.

The February 25, 2026 포상금 reform removes the reward cap and extends cross-agency eligibility. The structural environment for this work is improving, not static.
