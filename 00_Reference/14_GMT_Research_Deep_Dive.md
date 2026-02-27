# GMT Research: Business Model Reference

> **Scope:** GMT Research methodology (Asian market forensic accounting), peer grouping approach, Beneish adaptations, and business model observations.
> **Canonical for:** GMT Research methodology reference; Asian Beneish adaptation precedents.
> **See also:** `07_Automation_Assessment.md` (automation limits), `18_Research_Findings.md` (KOSDAQ-specific findings)

*Research conducted February 2026 via Perplexity deep dive. This document records objective facts and grounded observations. Revenue estimates are from Perplexity's research and are clearly marked as speculative where applicable.*

---

## Section 1 — Organizational History

### Forensic Asia Limited (March 2010 – December 2013)

GMT Research's predecessor entity. Founded March 2010 by Gillem Tulloch. Operated for approximately 3 years and 10 months before being dissolved and replaced by GMT.

Key structural fact: Forensic Asia was **not an independent standalone company**. It was affiliated with Asianomics, the macroeconomic research firm founded by Dr. Jim Walker. Philip Tulk (former employee) described it as "an independent research house (affiliated with Asianomics) based in Hong Kong."

Grew to 50+ paying institutional clients and 6 full-time employees plus guest analysts before Tulloch wound it down to form GMT.

During the Forensic Asia period, Tulloch simultaneously served as Portfolio Manager — Equities at Bowen Capital Management Ltd (managing The Zipangu Fund and The Stewart Asia Fund, a subsidiary of W.P. Stewart & Co., formerly NYSE: WPL). This dual role — running accounting research while managing money — was unbundled at GMT, which holds only a Type 4 (advisory) license.

Lisa Mangkornkarn (later identified as Tulloch's wife) helped establish Forensic Asia and subsequently joined GMT Research.

### GMT Research Limited (December 2013 – present)

GMT Research is a **new legal entity**, not a rebrand of Forensic Asia. Incorporated in Hong Kong with Registration Number 2025754, registered January 14, 2014. Appeared on the SFC's licensed persons additions list in October 2014.

The separation from Asianomics appears deliberate: Asianomics (Dr. Jim Walker) is listed on Smartkarma as a research provider; GMT Research is not. The two entities appear to have separated cleanly.

**Methodological foundations (from November 2011 "Creative Accounting" presentation under Forensic Asia):**

Red flags identified and carried forward into GMT's framework:
- Cash-based businesses (agriculture) and capital-intensive businesses (infrastructure, property)
- Deteriorating inventories and receivables
- Large "other" assets and liabilities
- Related party transactions
- Persistently high capex and free cash outflows
- High income statement tax relative to cash flow tax
- Growth through acquisitions and use of shell companies
- Super-normal profitability

Quantitative benchmark from the same presentation: 9.4% of Asian companies showed deteriorating inventory and receivable days over three years, versus 4.3% in the US and 4.9% in Western Europe (China exceeded 10%).

---

## Section 2 — Product Architecture

### A&G Screen (Accounting & Governance Screen)

Web-based application accessible to subscribers behind a login wall. Produces **percentile scoring** for each financial ratio relative to **industry peer groups** — it does not apply absolute thresholds but rather compares companies against global sector peers.

Designed to detect "traits in line with past frauds" and enable cross-market search for companies with specific financial characteristics.

GMT implemented copy-paste prevention and security measures after a 2015 incident in which the AirAsia report was stolen from a subscriber.

### Standard Ratios (Publicly Named)

| Ratio / Model | Category |
|---|---|
| Accounting Risk Assessment | Composite |
| Accounts Receivable >90th Percentile | Balance Sheet |
| Accruals Manipulation | Earnings Quality |
| Acquisition Accounting | M&A |
| Acquisitions and Disposals | M&A |
| Affiliate Investment/Equity (%) | Related Party |
| Altman Z-Score | Solvency |
| Asset Turnover: Assets/Sales (%) | Efficiency |
| Assets/Equity (x) | Leverage |
| Auditing Expenses/Sales (bp) | Governance |
| Beneish M-Score | Earnings Manipulation |
| Capex/Sales (%) | Cash Flow |
| Capitalised Interest/Pre-Tax Profit (%) | Cash Flow |
| Cash Conversion Cycle (Days) | Working Capital |
| Cash Extraction Fraud | Proprietary |
| Cash Flow Tax/Income Statement Tax (%) | Tax Manipulation |
| Cash From Operations/Net Profit (x) | Cash Flow Quality |
| Cash Interest Expenses/CFO (%) | Debt Servicing |
| Cash Return less Policy Rate (ppt) | Cash Quality |
| Cash/Sales (%) | Balance Sheet |

*Total list is 20+ named ratios; full list is behind paywall.*

### Proprietary Models

**Fake Cash Flow Fraud Model** — Discrete 0–4 score. Targets companies faking sales and profits while hiding the evidence as fabricated balance sheet assets (receivables, prepayments, deposits, or cash). Triggered at scores of 3 or 4. Originally designed for Chinese frauds. Successfully identified Wirecard (Germany), Folli Follie (Greece), and Satyam (India) — demonstrating cross-GAAP applicability. Approximately 8% of companies globally trigger this model simultaneously with the Excess Capital Raising model.

**Excess Capital Raising Model** — Triggered when net cash inflows over a three-year period are in the highest quintile relative to global industry peers. Targets window-dressing, seasonal distortion, or faking profits hidden in cash-like assets.

**Cost Capitalisation Model** — Triggered when amortisation charges lag costs capitalised, producing a profit uplift exceeding 15% of pre-tax profit, in a sector known to capitalise costs. Approximately 2% of companies globally trigger the full model (red flag); additional 5% show uplift but not in listed sectors (yellow flag).

### Client Interaction Products

GMT offers three product lines to distinct client types:
1. **Institutional investor subscriptions** — A&G Screen access + research reports
2. **Free newsletter** — Lead generation; gives "a flavour of the research topics we have been working on"
3. **Crisis management for companies targeted by short-sellers** — Explicitly offered as a service

The crisis management offering creates a structural conflict of interest: GMT simultaneously screens companies for anomalies and advises companies defending against short-seller attacks. No public documentation exists on how GMT manages this separation. The most plausible reading is that GMT provides factual accounting clarification to companies it believes were unfairly targeted, rather than assisting companies concealing genuine issues.

---

## Section 3 — Regulatory and Corporate Structure

### SFC License

**Type 4 only** (Advising on Securities). SFC ID: BDR130. This was confirmed by the October 2014 SFC additions list.

Implications under Hong Kong's Securities and Futures Ordinance:
- **Can**: publish research reports with investment recommendations; advise on merits of buying/selling securities; provide screening tools constituting investment advice; sell research to professional investors
- **Cannot**: deal in securities (Type 1); manage client portfolios (Type 9); hold client assets
- **Must**: maintain minimum 2 Responsible Officers; HKD 100,000 minimum paid-up capital; submit audited financial statements annually to SFC (not publicly disclosed); submit financial resources returns semi-annually

### Incorporation

Hong Kong only. Registration Number 2025754. No evidence of registrations in US, Singapore, UK, or other jurisdictions found.

SFC requires a dedicated physical office in Hong Kong.

### Regulatory Actions

No SFC enforcement actions or disciplinary proceedings found against GMT Research.

One known complaint: AirAsia X filed with Malaysia's Securities Commission in July 2015 under Section 177 of Malaysia's Capital Markets and Services Act 2007 (prohibition on false/misleading information). No public evidence of enforcement resulting from this complaint.

Evergrande rejected GMT's December 2023 report as "without basis" but did not pursue legal action.

---

## Section 4 — Client Base and Distribution

### Named Client

**RBC Global Asset Management (Asian Equity team)**: Documents GMT Accounting Screens as an "external quantitative screening tool" used alongside MSCI and Sustainalytics. RBC specifically utilizes GMT's Fake Cash Flow model, Beneish M-Score, Altman Z-Score, and flags for working capital manipulation, debt management anomalies, and auditor fee anomalies. This is documented in a published RBC white paper (2020).

Beyond RBC, no other specific institutional clients have been publicly named. This is standard practice in independent research.

### General Client Profile

Tulloch stated in 2017: "most of GMT's clients are institutional shareholders and some are 'long-only' hedge funds."

Precedent from Forensic Asia: 50+ paying institutional clients at the time of wind-down.

### Client Acquisition Channels

- Free newsletter (documented lead generation)
- Media coverage of named reports (AirAsia report: BBC, Reuters, Bloomberg coverage; Evergrande: Bloomberg, Business Times)
- Conference presentations
- Video content on GMT website
- Referrals (standard in the independent research industry)

### Distribution Platform

No confirmed distribution through Bloomberg Terminal, FactSet, Capital IQ, or Smartkarma. GMT's distribution appears to be primarily through its own proprietary website (login-protected).

### Pricing

Not publicly disclosed. Subscribers inquire by email. From the AirAsia incident, Tulloch described the subscription as a "substantial amount of money." Malaysian media reported that research of this type can range from "the low four figures to the mid five figures, in US dollars" annually.

*Revenue estimate (Perplexity, speculative):* Given Forensic Asia's 50+ client precedent, pricing in the above range, and 4-person team overhead, Perplexity estimates annual revenue of approximately $300,000–$4,000,000. This is not confirmed.

---

## Section 5 — Methodology and Cross-Market Calibration

### Accounting Standards Coverage

GMT's A&G Screen covers companies reporting under IFRS, US GAAP, Chinese Accounting Standards (CAS), and various local GAAPs across Asia. The Fake Cash Flow model was designed for CAS but was successfully applied to European IFRS (Wirecard), Greek GAAP/IFRS (Folli Follie), and Indian GAAP (Satyam).

**Relevance to Korea:** K-IFRS (Korean IFRS) is substantially converged with full IFRS. RBC's documentation notes this about CAS convergence, and the same logic applies to K-IFRS. GMT's models are applicable to Korean financial statements without fundamental methodology changes.

### Language

GMT does not publicly disclose how it handles non-English financial statements. Team profile suggests reliance on English-language filings (which most listed Asian companies publish). No Korean-language capability is evident in the team.

Team composition (as of February 2026):
- Gillem Tulloch — founder; 30+ years in Asia; Nomura Securities Singapore/Korea July 2000 – April 2002 (Joint Regional Head of Telecommunications)
- Lisa Mangkornkarn — Tulloch's wife; Chulalongkorn MBA; joined from Forensic Asia
- Mark Webb — 21+ years in Asia; prior HSBC research in Hong Kong and Singapore
- Nigel Stevenson — joined August 2016; prior London-based

### Cross-Market Calibration Approach

The A&G Screen uses percentile scoring relative to industry peer groups, which adjusts for cross-market differences in accounting norms. The 2016 "Global Evaluation" report (covering all of ASEAN and Hong Kong) explicitly compared corporate health metrics across all Asian markets: "the vast majority of companies with problematic accounting are Chinese" while "95% of all companies were engaged in related party transactions across pretty much every market."

### Published Methodology References

| Year | Document | Key Content |
|---|---|---|
| November 2011 | "Creative Accounting" (Forensic Asia presentation) | Most detailed public methodology document; red flag taxonomy; Asia vs. US/Europe comparisons |
| May 2017 | "FAKING CASH FLOWS: And How to Spot It" | Explains the Fake Cash Flow model |
| October 2016 | "GLOBAL EVALUATION: All Roads Lead to China" | Global evaluation framework; related party transaction screening of every ASEAN and HK company |
| Ongoing | GMT website / Accounting Ratios section | Summary-level descriptions of each model (detailed content behind paywall) |
| 2020 | RBC "Managing Accounting Risk in Asia as Stock Pickers" | Most detailed third-party account of GMT screens in institutional practice |

---

## Section 6 — Competitive Landscape

| Competitor | Model | Coverage | Key Difference vs. GMT |
|---|---|---|---|
| Transparently.AI | AI-powered, 150-factor MRA scoring | 85,000+ companies globally | Fully automated; GMT is human-analyst driven |
| Iceberg Research | Activist short-seller | Singapore-focused, company-specific | More confrontational; takes short positions |
| Smartkarma Forensic Vertical | Platform hosting multiple independent analysts | Asia-wide via 300+ providers | Marketplace model vs. GMT's single-firm model |
| FTI Consulting | Consulting firm, litigation/fraud | Global, Seoul office | Enterprise consulting; not subscription research |
| MSCI ESG / Sustainalytics | ESG data providers | Global | Governance-focused, not accounting anomaly detection |
| Traditional sell-side | Broker research | Market-wide | Conflicted; GMT was founded to counter sell-side bias |

**GMT's stated positioning:** Does not take short positions (Type 4 prohibits dealing). Explicitly distinguishes itself from activist short-sellers: "these costs cannot be borne by traditional subscription or commission-based business models." RBC uses GMT alongside MSCI and Sustainalytics as complementary, not competing, tools.

### Track Record

**China Evergrande (vindicated):** GMT published "China Evergrande: Are its auditors asleep?" in January 2017, estimating asset value overstated by ~RMB 15 billion. In March 2024, China's CSRC confirmed Hengda (Evergrande's onshore subsidiary) had overstated a total of 91.9 billion yuan (~$12.7 billion) in profit — validating GMT's analysis by approximately 7 years. The fraud was ultimately sized at $78 billion.

**AirAsia (market impact):** June 2015 report alleged 39% profit inflation through related-party transactions. Caused a 25–30% share price decline within one week. AirAsia's CEO called the report "garbage"; virtually all sell-side analysts maintained buy recommendations.

**Use in regulatory coverage:** GMT's Evergrande research was cited by Bloomberg in the context of China's CSRC investigation into PwC. Nigel Stevenson was directly quoted. No evidence of GMT research being formally submitted as litigation evidence.

---

## Section 7 — Korea-Specific Gap

### GMT's Korea Coverage

**No Korean companies appear in GMT's publicly visible Library listing.** The Library includes companies from China, Japan, India, Malaysia, Hong Kong, Singapore, Australia, and US-listed Asian companies — but no Korean-listed stocks.

The A&G Screen likely includes Korean companies within its pan-Asian universe (the screen covers companies across Asia), but no Korea-specific product, report, or research note has been publicly identified.

### Tulloch's Korea Views (2013)

In a May 2013 Reuters interview, Tulloch expressed bearish views on Korea's corporate sector: "it's not the case in Korean... balance sheets are insolvent or [have] solvency issues... experiencing free cash outflows so you can't have a sustained investment upcycle." He contrasted Korea unfavorably with Southeast Asian markets.

Tulloch's Korea experience: Nomura Securities (July 2000 – April 2002), based in Singapore and Korea as Joint Regional Head of Telecommunications. He described Nomura as "a great lesson in how not to run a research department" — suggesting his experience shaped his commitment to independent research.

### Why the Korea Gap Likely Persists

- A 4-person team cannot cover all of Asia in depth; Korea requires Korean-language competency not evident on GMT's team
- KOSDAQ's extreme coverage vacuum (62% of firms with zero analyst coverage in 2025, per FSS data) makes Korea simultaneously the most underserved and most resource-intensive market to enter
- The Korea IR Council, independent research companies, and KRX's AI analysis reports are beginning to fill general coverage gaps, but none focus on accounting anomaly detection

---

## Section 8 — Business Economics

### Scale

GMT's Library (February 2026) shows approximately 20 company-specific entries covering 2023–2025 — roughly 7–10 new company reports per year. The team compensates for this limited output through:
- Thematic reports covering multiple companies simultaneously (the ASEAN related-party study covered every company in the region)
- The A&G Screen, which automates quantitative screening across thousands of companies
- The factoring study scrutinized nearly 400 Asian companies

Tulloch stated that single company deep dives take approximately 3 months (based on the AirAsia example).

### Financial Data

**No public financial data exists for GMT Research Limited.** As a private Hong Kong company with a Type 4 license, it submits audited financials to the SFC annually, but these are not publicly disclosed.

### Capital Structure

No evidence of external capital raises, outside investors, or outside funding. Given the Type 4 minimum capital requirement of only HKD 100,000 and the low-overhead subscription research model, GMT appears to be self-funded.

### Growth Pattern

The team has remained at 4 named analysts since at least 2018 (when Bloomberg profiled the firm). Nigel Stevenson joined in August 2016 and the team composition has not changed since. This suggests GMT operates as a stable, lifestyle-compatible business rather than a growth-oriented firm. No evidence of planned expansion was found.

---

## Section 9 — Structural Comparison

| Dimension | GMT Research | Korean Pipeline |
|---|---|---|
| Team | 4 analysts (stable since ~2016) | Junior Korean CPAs + AI multiplier |
| Coverage | Pan-Asia, ~7–10 deep dives/year | Korea only, ~2,700 companies systematically |
| Methodology | Human-driven, proprietary models + judgment | Automated pipeline (Beneish M-Score, CB/BW timelines, disclosure timing, network mapping) |
| Data source | Financial statements (multi-country, multi-GAAP) | OpenDART, KRX, SEIBRO, KFTC (Korea-specific, K-IFRS) |
| Language | English-language focus | Bilingual Korean/English |
| Regulatory status | HK SFC Type 4 | TBD (Korean Capital Markets Act considerations) |
| Client base | Institutional investors (long-only, hedge funds) | Multiple options under evaluation |
| Revenue model | Subscription (est. $10K–$50K/client/year — speculative) | Multiple options under evaluation |
| Short positions | None (Type 4 prohibits dealing) | Pipeline does not take positions |
| Open source | Proprietary, closed | Open-source public infrastructure |
| KOSDAQ coverage | None identified | Full universe |
| Output | Anomaly reports + screening tool | Anomaly hypotheses for human review |

**Core differentiation from GMT:** Systematic automation across all ~2,700 listed companies using exclusively public data, bilingual Korean/English capability, and Korea-specific depth. GMT validates that institutional demand exists for accounting anomaly research in Asia; the Korean pipeline addresses a coverage vacuum GMT has chosen not to fill.

---

*This document will be updated as organizational decisions are made. No commitments are implied by its contents.*
