# FSCMA Regulatory Analysis: Capital Markets Research and Data

> **Scope:** Capital Markets and Financial Investment Business Act (자본시장법) — disclosure obligations, distribution constraints on derived data, and compliance considerations.
> **Canonical for:** FSCMA legal provisions relevant to this project; distribution constraint analysis.
> **See also:** `16_CPA_Act_Regulatory_Analysis.md` (audit act), `05_Regulatory_Environment.md` (broader context)

*Research conducted February 2026 via Perplexity. This document records objective facts and confirmed legal provisions. Items marked as requiring attorney confirmation are not settled by public sources alone.*

---

## Section 1 — The Three-Tier Regulatory Hierarchy

Korea's Financial Investment Services and Capital Markets Act (자본시장과 금융투자업에 관한 법률, FSCMA) establishes a three-tier structure for investment-related advice. The tier that applies depends on whether the service is personalized:

| Tier | Category | Korean term | Regulatory pathway | Key characteristic |
|---|---|---|---|---|
| 1 (Lightest) | Quasi-investment advisory | 유사투자자문업 | Report (신고) filed with FSC | Non-personalized, one-way channel only |
| 2 (Medium) | Investment advisory | 투자자문업 | Registration (등록) with FSC | Personalized; may be two-way |
| 3 (Heaviest) | Dealing/brokerage/underwriting | 투자매매·투자중개업 | Authorization (인가) from FSC | Execution of transactions |

The pipeline's activities fall within Tiers 1 and 2 only. Tier 3 (dealing) is categorically inapplicable — the pipeline does not execute trades or manage portfolios.

---

## Section 2 — Key Provisions

### Article 6(6) — Investment Advisory Business (투자자문업)

Defined as providing advice on the value of financial investment instruments or related judgments (class, item, acquisition, disposition, quantity, price, timing, etc.), conducted "continuously or repeatedly for the purpose of earning a profit."

The definition is broad and could encompass anomaly scores that directly implicate judgments about listed securities. However, **personalization** determines whether Tier 1 or Tier 2 applies. The Korean Supreme Court has confirmed: the distinction between 투자자문업 and 유사투자자문업 turns on whether **actual one-on-one counseling or personalized advisory service** is provided to individual investors. Non-personalized, one-directional research outputs fall outside 투자자문업 even if they contain strong views on specific companies.

Registration requirements for 투자자문업:
- Legal form: 주식회사 (stock company)
- Minimum equity capital: KRW 100 million (standard unit) or KRW 250 million (expanded unit, per April 2024 FSS guidance)
- At least one full-time investment advisory personnel (투자권유자문인력)
- Qualified executives; conflict-of-interest prevention system

Note: 투자자문업 requires **registration** (등록), not authorization (인가). Registration is the lighter pathway.

### Article 7(3) — Publication Exemption

"A business shall not be deemed an investment advisory business when it provides advice through a periodical, publication, correspondence, broadcast or **any other medium** that is issued or transmitted to an **unspecified number of people**, and which is available to an unspecified number of people for purchase or receipt from time to time."

Key elements:
- "Any other medium" — language broad enough to cover digital platforms, websites, and data feeds
- "Unspecified number of people" (불특정 다수) — advice must not be personalized to individual clients
- "Available for purchase or receipt from time to time" — subscription models are included if the service is available to any willing subscriber

**Gray area:** If a subscription is restricted to a small number of named institutional clients with bespoke interaction, it may fall outside this exemption. If the subscription is open to any qualifying buyer, the exemption likely applies. The exact boundary for institutional-only subscriptions has not been tested in published Korean case law.

### Article 101(1) — Quasi-Investment Advisory Business (유사투자자문업)

Amended February 13, 2024, effective March 31, 2025. Formal pathway for non-personalized investment advice: an entity providing non-individualized advice (개별성 없는 조언) on financial investment instruments through periodicals, publications, correspondence, broadcasts, etc., for a fee, must **file a report (신고)** with the FSC.

Properties of 유사투자자문업:
- Report-only system (신고) — not registration or authorization
- Reports valid for 5 years; require pre-filing education
- Restricted to **one-way channels** (단방향 채널) as of August 2024

**Korea-specific context:** The 유사투자자문업 framework has no equivalent in the US or Japan. It was created specifically to address the gap between unregulated "stock tip" services and fully registered investment advisors.

### August 2024 Reform — The One-Way / Two-Way Bright Line

The FSC implemented a reform effective August 14, 2024 tightening the boundary between Tier 1 and Tier 2. The reform was driven by widespread fraud by quasi-investment advisory operators using YouTube, Telegram, and open chat rooms (FSS inspected 351 entities and detected 54 cases of suspected illegal activity).

**After August 2024:**
- **유사투자자문업 (Tier 1)**: One-way channels only — text messages, ARS, publication sales, broadcasts, non-interactive data feeds
- **투자자문업 (Tier 2)**: Required for two-way channels — SNS open chat, 1:1 consultation, interactive Q&A

The one-way vs. two-way distinction is now the operative bright line in Korean securities regulation.

The FSS issued an April 2024 batch registration guidance for quasi-investment advisors wishing to convert to full 투자자문업 registration, with a May 13, 2024 deadline. This pathway remains available.

### Article 335-3 — Credit Rating Business (신용평가업)

Requires FSC **authorization** (인가), minimum equity capital of KRW 5 billion, ownership restrictions on conglomerates. Defined as evaluating the creditworthiness of issuers or specific financial instruments.

Accounting anomaly scores are **categorically different** from credit ratings. Anomaly scores assess accounting quality, disclosure patterns, and governance risk — not debt repayment probability. The credit rating regime (KR, NICE, KIS) operates under an entirely separate framework and does not overlap with the investment advisory regime.

### Professional Investor Status (전문투자자) — Article 9(5)

Defined as entities with risk-absorbing ability based on expertise and asset scale: the State, Bank of Korea, financial institutions, listed corporations, and others per Presidential Decree. Following a 2019 reform, individual investor thresholds were lowered, expanding the estimated professional investor pool from 1,950 to approximately 370,000–390,000.

**Critical finding:** No explicit "professional investor only" exemption from investment advisory registration exists in FSCMA Article 7 or elsewhere in the statute. Selling research exclusively to professional investors does **not**, by itself, eliminate the need for registration or reporting. This is a significant difference from Hong Kong, where professional investor status affects licensing thresholds. Professional investor classification affects investor protection obligations applied, not the fundamental question of whether the activity is regulated.

---

## Section 3 — Classification by Revenue Activity

| Revenue Activity | FSCMA Classification | Registration/Filing Required | Safest Operating Structure |
|---|---|---|---|
| **Automated screening pipeline** (quantitative scores and flags across ~2,700 companies) | Pure data output → likely exempt under Art. 7(3); if sold with analytical framing → 유사투자자문업 at minimum | If exempt: none. If 유사투자자문업: report (신고) only | Publish as data feed; include KCGS-style disclaimer disclaiming investment advice |
| **Research reports** (written analysis of specific companies, non-personalized) | **유사투자자문업** (if one-way, non-personalized, open subscription) | Report (신고) only | Non-personalized reports to open subscriber base → 유사투자자문업 filing |
| **Research reports** (bespoke, tailored to specific client's portfolio context) | **투자자문업** | Registration (등록); min. KRW 100M–250M equity capital; ≥1 qualified advisory personnel | Separate 투자자문업-registered entity or subsidiary |
| **Data licensing** (machine-readable scores to institutional clients, no advisory language) | Likely **exempt** — analogous to Bloomberg Data License, MSCI, S&P data services in Korea | None, if structured as pure data without advisory language | Incorporate as tech/data company (not financial services); follow Bloomberg/MSCI precedent |
| **Consulting** (time-billed advisory for M&A due diligence, compliance, litigation) | **투자자문업** (personalized advice on specific securities to specific clients) | Registration (등록) | Register as 투자자문업 entity or conduct through a separately registered advisory subsidiary |

---

## Section 4 — How Existing Korean Entities Handle This

### Independent Research Firms (독립리서치, IRP)

As of February 2026, Korean IRPs operate under the 유사투자자문업 framework — they have filed a report (신고) with the FSC but hold no formal financial investment business registration.

Named Korean IRPs:
- **리서치알음** (Research Ahlum) — founded 2016, first Korean IRP; as of 2025, the **first and only** IRP to obtain full 투자자문업 registration with the FSS
- **밸류파인더** (ValueFinder) — headed by Lee Chung-heon (이충헌), inaugural president of the Korea Independent Research Association
- **퀀트케이** (QuantK), **FS리서치** (FS Research), **CTT리서치** (CTT Research)
- **지엘리서치** (GL Research), **아리스** (Aris) — founding members of KIRA

**Regulatory characterization:** KB Think's financial dictionary describes the situation as: "Even though analysts, private bankers, and fund manager veterans establish corporations and publish reports on par with securities firm research centers, under the current system they receive the same treatment as 'stock tip chatrooms' (주식 리딩방)." — This reflects the FSS's active dissatisfaction with the current classification and its intent to change it.

**Korea Independent Research Association (한국독립리서치협회, KIRA):** Officially launched January 2, 2026. First privately-led professional association of IRPs in Korea. Stated focus: discovering and publicizing undervalued small- and mid-cap KOSPI/KOSDAQ companies. Inaugural president: Lee Chung-heon of ValueFinder.

### FSS Reform in Progress (as of February 2026)

The FSS included in its 2023 work plan a commitment to "pursue the introduction of an independent research company system" (독립리서치 회사 제도 도입). Options under discussion:
- Creating a new financial investment business authorization unit (금융투자업 인가 단위) specifically for IRPs
- Placing IRPs within existing categories such as brokerage or advisory

**Status as of February 2026: not yet enacted.** IRPs continue to operate under 유사투자자문업.

The FSC's December 2025 KOSDAQ activation measures ordered five comprehensive securities firms to double their KOSDAQ research staff (from avg. 4.6 to 9.2 analysts). This targets existing securities firms, not IRPs — but it explicitly acknowledges the KOSDAQ coverage vacuum that IRPs and a data pipeline both address.

### KCGS (한국ESG기준원) — Scoring Entity Precedent

KCGS is organized as a 사단법인 (incorporated association under the Korean Civil Code). It rates approximately 1,024 listed companies on ESG criteria and is **not** registered as a financial investment business entity under FSCMA.

KCGS's legal disclaimer: "The data and analysis provided by KCGS are solely for informational purposes intended to help improve corporate management practices and assist investment decisions. They do not represent the opinions on whether to buy, sell, or hold shares of a particular stock."

This disclaimer is the template for operating a scoring/rating entity outside FSCMA's investment advisory registration.

### Sustinvest (서스틴베스트) — Registered ESG Advisor Precedent

Founded 2006. Evaluates 1,000+ Korean companies on ESG performance and provides institutional investors with research-driven consultancy. Explicitly self-describes as a "투자자문사" (investment advisory company) — registered as 투자자문업. Partners with Sustainalytics and Trucost.

This confirms: an ESG/governance data and rating provider **can** register as 투자자문업 in Korea. Sustinvest appears to have voluntarily chosen the higher registration tier because it provides bespoke advisory services (proxy advisory, investment stewardship consulting) alongside its rating products — crossing the personalization boundary.

### Bloomberg Korea, MSCI, S&P

These operate their data services in Korea **without** apparent 투자자문업 registration. Bloomberg Data License, MSCI ESG ratings, and S&P data appear to be treated as general information/data provision rather than investment advice. The critical structural choice: outputs are framed as information, not advice, and no personalized advisory interaction is offered.

---

## Section 5 — Cross-Border Considerations

### Cross-Border Registration Pathway (역외투자자문업)

FSCMA Article 18(2)(1), amended January 21, 2025 (effective July 22, 2025): A foreign investment advisory entity (외국 투자자문업자) **can** conduct investment advisory business targeting Korean residents from overseas without establishing a Korean branch or office. However, it must **register** with the FSC as a cross-border investment advisory business.

Cross-border registration application requirements:
1. Articles of incorporation (or equivalent)
2. Certificate of business establishment from home country
3. Group organization chart
4. Executive resumes and career certificates
5. Three years of audited financial statements
6. Proof of qualifications equivalent to Korean investment advisory personnel
7. Proof that major shareholders meet requirements
8. Designation of a Korean contact person

**Live precedent:** PGIM Quantitative Solutions LLC holds cross-border discretionary investment management and investment advisory licenses under the Korea FSCMA, registered with the FSC. Its materials are "intended solely for Qualified Professional Investors as defined under the FSCMA." This confirms the pathway is operational and used by institutional asset managers.

### No Passporting or Reciprocity

No evidence exists of an FSC/FSS reciprocity or passporting arrangement with any foreign regulator, including Hong Kong's SFC. A foreign entity with an HK SFC Type 4 license does not get automatic access to operate in Korea — separate Korean registration is required.

### Data-Only Pathway for Foreign Entities

If the foreign entity provides **only** structured data (machine-readable scores, flags, datasets) **without** advisory language or investment recommendations, it may operate outside the FSCMA framework entirely — analogous to Bloomberg Data License, MSCI, and S&P. The framing of outputs as information vs. advice is the determinative structural choice.

---

## Section 6 — Recent Regulatory Developments (2023–2026)

| Date | Development | Relevance |
|---|---|---|
| 2023 | FSS work plan commits to 독립리서치 회사 제도 도입 | Signals intent to formalize IRP status; not yet enacted |
| February 2024 | FSCMA amended to restrict 유사투자자문업 to one-way channels | August 14, 2024 effective date; establishes the one-way/two-way bright line |
| April 2024 | FSS issues batch registration guidance for 유사투자자문업 → 투자자문업 conversion | KRW 100M–250M capital requirements documented |
| October 2025 | FSC strengthens penalty surcharges for unfair trading; introduces non-monetary sanctions (account freezes, transaction restrictions up to 5 years) | Increases enforcement stakes; increases value of pipeline outputs |
| December 2025 | FSC orders five comprehensive securities firms to double KOSDAQ research staff | Acknowledges coverage vacuum; does not address IRPs directly |
| January 2, 2026 | Korea Independent Research Association (KIRA) officially launched | Industry-level organization of IRPs; concerted push for formal regulatory recognition |
| January 21, 2025 (effective July 22, 2025) | FSCMA Article 18 amended; removes physical presence requirement for cross-border investment advisory entities | Cross-border registration pathway now fully operational without Korean office |
| February 9, 2026 | FSS releases 2026 regulatory roadmap: AI-based monitoring for abnormal trading detection | FSS is building internal surveillance capacity overlapping with pipeline functionality; validates market need |

**No MiFID II-style independent research reform:** Despite the EU's Directive (EU) 2024/2811 relaxing research unbundling requirements, Korea has not enacted any analogous policy creating a market for paid independent research. Korea's approach to the KOSDAQ coverage gap has been to mandate that existing securities firms expand coverage, not to create incentives for new independent entrants.

---

## Section 7 — Open Questions Requiring Attorney Confirmation

The following questions cannot be resolved through publicly available sources. Korean securities law counsel (김앤장, 세종, 태평양, 광장, or equivalent) should review these before any commercial activity begins:

1. **Article 7(3) "unspecified number of people" (불특정 다수) boundary for institutional-only subscriptions.** Does a research service available only to qualified institutional subscribers (not open to the general public) still satisfy this requirement? If subscription is open to any institution willing to pay, the exemption likely applies. If the subscriber list is closed and curated, it may not. Not tested in published Korean case law specific to institutional research products.

2. **Data licensing vs. advisory boundary.** At what point does a machine-readable dataset of anomaly scores transition from exempt "data" to regulated "advice"? The inclusion of natural-language labels (e.g., "high accounting anomaly risk") alongside quantitative scores may shift the classification. Specific data schema and output language should be reviewed.

3. **Simultaneous 유사투자자문업 and 투자자문업 operation.** Can a single entity operate both tiers simultaneously, or must they be separated into distinct legal entities? The April 2024 FSS guidance addressed conversion from one to the other, but not simultaneous operation.

4. **Cross-border registration for a startup-scale entity.** The 역외투자자문업 registration pathway is documented and used by large institutional asset managers (PGIM). Whether the FSC processes such registration from a small independent research firm, and what the practical timeline and review process are, has not been publicly documented for startup-scale applicants.

5. **Forthcoming IRP regulatory framework.** The FSS's stated intent to create a dedicated authorization unit for IRPs could materially change the landscape — either more favorable (purpose-built license) or more burdensome (new compliance obligations). Timing and specifics unknown. An attorney with FSS relationships may have current intelligence.

6. **Nonprofit legal form and FSCMA interaction.** KCGS operates as a 사단법인 and KCIJ operates as a nonprofit media organization. Whether a nonprofit legal structure (사단법인 or 재단법인) provides additional FSCMA exemptions or reduces compliance obligations has not been publicly analyzed.

7. **Whistleblower submission structuring.** Whether structuring whistleblower submissions based on pipeline outputs triggers any FSCMA obligations (e.g., "facilitating" securities transactions) requires specific legal analysis under the whistleblower statute and FSCMA together.

8. **August 2024 reform enforcement in practice.** Enforcement patterns regarding the one-way vs. two-way borderline are not yet publicly documented. Practical guidance on enforcement priorities requires an attorney with FSS relationships.

---

*This document will be updated as organizational decisions are made and as Korean IRP regulatory reform progresses. No commitments are implied by its contents.*
