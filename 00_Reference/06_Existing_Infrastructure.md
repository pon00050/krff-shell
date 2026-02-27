# Existing Infrastructure: What Already Exists, What Doesn't

> **Scope:** Survey of existing Korean financial data tools, APIs, and open-source projects — gap analysis showing what this project adds.
> **Canonical for:** Tool landscape; gap justification.
> **See also:** `02_Data_Sources.md` (sources this project uses), `04_Technical_Architecture.md` (what this project builds)

*Research conducted February 2026. The goal is to complement and extend, not duplicate.*

---

## What Exists — Data Tools

These are the foundational libraries. They are real, maintained, and form the data access layer:

| Library | Purpose | Status |
|---|---|---|
| [OpenDartReader](https://github.com/FinanceData/OpenDartReader) | DART API — disclosures, financials, events | Actively maintained |
| [dart-fss](https://pypi.org/project/dart-fss/) | DART financial statement extraction | Available on PyPI |
| [PyKRX](https://github.com/sharebook-kr/pykrx) | KRX OHLCV, investor flow, short selling | Actively maintained; MCP server also available |
| [FinanceDataReader](https://github.com/FinanceData/FinanceDataReader) | KRX + global price data | Actively maintained |

These exist. Building a data access pipeline using these tools is not novel — it is the starting point.

---

## What Exists — Academic Research

### AI-Based Misstatement Detection, Korean Firms (MDPI Sustainability, 2025)

"Enhancing Corporate Transparency: AI-Based Detection of Financial Misstatements in Korean Firms Using NearMiss Sampling and Explainable Models" (Vol. 17, No. 19, Article 8933).

Analyzed all publicly listed non-financial Korean firms on KSE and KOSDAQ, 2009–2023. Contribution: NearMiss undersampling + SHAP/PFI explainability outperforms standard ML approaches on recall/F1 in imbalanced fraud datasets.

**Gap this leaves:** The paper is a methodology contribution — it does not produce a public, maintained, updated screening database. Its output is a journal article, not a running pipeline.

### Litigation Risk and Fraud Reduction (ScienceDirect, 2024)

Found significant fraud reduction among KOSPI firms with assets > KRW 2 trillion subject to securities class action law — but **no comparable reduction for smaller KOSDAQ firms below the threshold**. This is the population where CB/BW manipulation is most concentrated.

**Gap this leaves:** Small/mid KOSDAQ companies — the primary targets for the most systematic manipulation scheme — are the least studied and least protected.

### Beneish M-Score on Korean Markets

No dedicated peer-reviewed Korean-specific Beneish M-Score study was found in open English databases. The Korean academic databases (DBpia, RISS) likely contain Korean-language studies, but there is no published English-language systematic M-Score application to KOSDAQ/KOSPI companies.

---

## What Exists — Investigative Journalism

### Newstapa / KCIJ (한국탐사저널리즘센터)

- ICIJ member; participated in Panama Papers and Pandora Papers
- Has data journalism capabilities (published data journalism textbook)
- Covers chaebol governance issues episodically

**Gap this leaves:** Newstapa produces individual investigative stories. It does not maintain a public, searchable database of KOSDAQ manipulation cases or systematic screening outputs. Coverage is episodic, not systematic.

There is no Korean equivalent of:
- ProPublica's systematic financial data portals
- Hindenburg-style formatted public research reports targeting specific listed companies with documented evidence chains

---

## What Exists — Short Seller Research

**International short sellers** (Hindenburg, Muddy Waters, Citron): No major published reports targeting KOSPI/KOSDAQ-listed companies found. The 16-month short selling ban (Nov 2023–Mar 2025) made Korean markets impractical targets.

**Domestic Korean short seller research firms:** None identified. No Korean equivalent of an activist short-seller firm exists.

---

## What Exists — Activist Investors

**KCGI (Korea Corporate Governance Improvement Fund):** Korea's first-generation activist fund (est. July 2018). Campaigns target board independence and shareholder returns — not accounting fraud. Uses ownership stakes and proxy battles, not public disclosure as a weapon.

---

## What Exists — Regulatory Data Outputs

**DART:** Comprehensive mandatory filing database; programmatic access via OpenDartReader. ✓

**KRX Data Marketplace:** Market data, short selling statistics. ✓

**FSC/FSS Enforcement Database:** Individual enforcement actions via press releases only. **No structured, searchable aggregate enforcement database comparable to SEC's EDGAR enforcement releases.** ✗

---

## Summary: The Gap Map

| Layer | What Exists | What Is Missing |
|---|---|---|
| Data access | OpenDartReader, PyKRX, FinanceDataReader | — |
| Anomaly signal layer | Academic papers (not public pipelines) | Reproducible, maintained anomaly screen on DART + KRX + SEIBRO data |
| CB/BW abuse detection | FSS enforcement press releases | Systematic public dataset of CB issuance → exercise → price impact timelines |
| Investigative journalism database | Newstapa episodic coverage | Systematic KOSDAQ manipulation case database |
| Short-seller research | None for Korean markets | Domestic or international research targeting KOSDAQ |
| Enforcement database | FSC press releases | Structured, searchable FSC/FSS enforcement history |
| Minority shareholder litigation tool | 0.01% derivative suit threshold (July 2025) | Accounting research that provides the evidentiary basis to use that threshold |

---

## What This Project Adds

The project does not duplicate what exists. It builds the missing layer:

1. A **reproducible, documented, public pipeline** joining DART + KRX + SEIBRO data (nothing like this exists publicly)
2. A **systematic Beneish M-Score screen** updated quarterly across all KOSDAQ companies (first public English-documented version)
3. A **CB/BW anomaly timeline dataset** reconstructing the full issuance → exercise → price impact chain (no public version exists)
4. **Documentation in English** — accessible to international researchers, journalists, and investors who cannot read Korean-language academic databases

The addressable audience for this output includes Newstapa, KCIJ, international short sellers considering Korea post-ban-reinstatement, academic researchers, and minority shareholder litigants under the new 0.01% threshold.
