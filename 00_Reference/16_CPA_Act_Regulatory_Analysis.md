# CPA Act and Entity Structure Analysis

> **Scope:** External Audit Act (외부감사법) requirements and officer data handling considerations.
> **Canonical for:** External audit requirements; officer data compliance considerations.
> **See also:** `15_FSCMA_Regulatory_Analysis.md` (capital markets act), `05_Regulatory_Environment.md` (broader context)

*Research conducted February 2026 via Perplexity. This document records objective facts and confirmed legal provisions. Items marked as requiring attorney confirmation are not settled by public sources alone.*

---

## Section 1 — Core Finding: CPA Act Does Not Restrict This Business

The Korean Certified Public Accountants Act (공인회계사법) does **not** restrict accounting anomaly research, data publishing, or the activities of this pipeline.

The CPA Act reserves a specific enumerated set of functions to licensed CPAs. Calculating a Beneish M-Score, publishing written analysis stating that a company's financial ratios show patterns consistent with earnings manipulation, producing anomaly scores across listed companies, and licensing machine-readable data are **all outside** the CPA Act's reserved functions. These activities can be performed by anyone — CPA or not.

---

## Section 2 — Statutory Scope of CPA-Reserved Functions

### Article 2 (직무범위) — The Complete Enumeration

CPA Act Article 2 defines the scope of CPA functions as:

> "A certified public accountant performs the following duties **upon commission from another person** (타인의 위촉에 의하여):
> 1. Accounting-related audit (감사), appraisal (감정), certification (증명), calculation (계산), arrangement (정리), drafting (입안), or accounting related to incorporation of a corporation
> 2. Tax agency (세무대리)
> 3. Work incidental to items 1 and 2"

Three structural features of this provision:

- **"Upon commission from another person"** — The duties are triggered when a CPA is commissioned by a client to perform them. Self-initiated research published to the market is not "commissioned" work in this sense.
- **Item 1 is a closed list** — Audit, appraisal, certification, calculation, arrangement, drafting, and incorporation accounting. Financial research, anomaly detection, and data analytics do not appear.
- **Item 3 ("incidental work")** — Tethered to items 1 and 2. Advisory work that does not arise from or accompany an audit, attestation, or tax engagement is not "incidental" to those functions.

### What Is NOT Reserved to CPAs

The following activities are outside Article 2 and not reserved to licensed CPAs:

- Calculating financial ratios (including Beneish M-Score) from publicly available financial statements
- Publishing written analysis stating a company's financial patterns are "consistent with earnings manipulation"
- Producing quantitative anomaly scores across listed companies
- Selling structured financial data or research reports to institutional clients
- Providing due diligence consulting that does not involve audit, attestation, or tax representation
- Economic analysis, financial research, and data publishing generally

### Article 50 — Restriction on Non-CPAs

Article 50 states that a person who is not a registered CPA or registered accounting firm shall not perform the **duties of Article 2**. Violation carries criminal penalties under Article 54: up to 3 years imprisonment or KRW 30 million fine.

The Constitutional Court upheld Article 50/54 as constitutional in a 2008 decision, specifically addressing "회계에 관한 감사" (audit relating to accounting) as the core reserved function. The Court did not address financial research or data analytics.

### Article 54(2) — The Title/Holding-Out Restriction

A separate penalty (up to 1 year imprisonment or KRW 10 million fine) applies to any non-CPA who:
1. Uses the designation "공인회계사," "회계법인," or similar titles
2. Publishes financial documents falsely claiming CPA audit or certification

This is a **naming and title restriction only**, not a scope-of-work restriction. A non-CPA entity can perform financial analysis freely — it cannot call itself a CPA or claim its work constitutes CPA-level audit or certification.

### September 2025 Amendment Bill (Pending)

Rep. Yoo Dong-su (유동수) introduced a CPA Act amendment bill in September 2025 that would clarify Article 2's scope by explicitly defining the reserved functions as "review, verification, examination, confirmation — regardless of name — performed in a position **independent from the commissioning party**" (i.e., attestation work). The bill would also add a more explicit restriction to Article 50.

Significance: the bill confirms legislative intent that the CPA Act's reserved functions center on **attestation/certification in an independent capacity** — not on general financial analysis or research. If enacted, it would make the favorable boundary even more explicit. Status as of February 2026: not yet enacted.

---

## Section 3 — Employment of Licensed CPAs by Non-Accounting-Firm Entities

### General Rule: Permitted

Korean CPAs routinely work as employees of general corporations (주식회사), financial institutions, and government agencies. The CPA Act distinguishes:
- **개업 공인회계사** — Practicing/independent CPA operating their own office or within a registered accounting firm
- **소속 공인회계사** — Employed/affiliated CPA working at a non-accounting-firm employer

A CPA employed by a general corporation remains a KICPA member and subject to CPD requirements and ethical standards but is not performing "commissioned" Article 2 duties.

### Independence Rules Do Not Apply Outside Audit Context

CPA Act Article 21 independence restrictions apply specifically to the audit/attestation context. They are designed to protect audit independence, not to restrict what a CPA can produce when employed in a non-audit capacity.

A CPA employed by a research firm can publish accounting research reports using their professional credentials, provided they do not represent the work as constituting a CPA audit or certification. KICPA ethics Part C (비개업 공인회계사 — non-practicing CPAs) addresses obligations of CPAs outside public practice but does not prohibit financial research or analysis work.

### 실무수습 (Practical Training) Constraint — The Key Operational Limitation

Under CPA Act Article 7(1) and Enforcement Decree Article 12, a person who has passed the CPA examination must complete practical training before they can register as a CPA and perform CPA duties.

**Designated training institutions and required periods:**

| Institution | Period |
|---|---|
| Accounting firm (회계법인) | 2 years |
| KICPA (한국공인회계사회) | 2 years |
| Financial Supervisory Service (금융감독원) — accounting/audit/listed company finance departments only | 2 years |
| Audit group (감사반), central government agencies, government-invested institutions, financial companies | 3 years |
| External audit-subject companies (외부감사대상회사) — accounting departments only | 3 years |
| Listed companies (KRX-listed) — financial statement preparation departments only | 3 years |
| Other institutions designated by FSC upon KICPA recommendation | Varies |

**Can a startup anomaly research firm qualify as a 실무수습 institution?**

Almost certainly not at founding. Qualification under the "other institutions" category requires FSC designation upon KICPA recommendation. More practically, the named categories (accounting firms, listed companies, government bodies, financial institutions) all require institutional scale. A startup will not qualify as an "외부감사대상회사" (external audit-subject company) without meeting two of four thresholds: assets ≥ KRW 12 billion, liabilities ≥ KRW 7 billion, revenue ≥ KRW 10 billion, or employees ≥ 100.

**Practical hiring consequence:** The correct hiring pool is **post-실무수습 registered CPAs** — those who have already completed practical training (typically at a Big 4 or mid-tier firm) and are fully registered. 수습공인회계사 (trainee CPAs who have passed the exam but not yet completed training) would not be able to count employment at this firm toward their training requirement unless the firm obtains FSC/KICPA designation.

---

## Section 4 — US Accounting Credentials and Korean Recognition

### No US-Korea CPA Reciprocity

No reciprocity agreement exists between KICPA and any US state CPA licensing body (NASBA/AICPA). The US has Mutual Recognition Agreements with Australia, Canada, Mexico, New Zealand, and Hong Kong — but not Korea. Holding US accounting degrees without a Korean CPA license confers **no recognized professional status** under Korean law for CPA Act purposes.

Since the pipeline's activities fall entirely outside the CPA Act's scope, this is not a material operational constraint.

### Foreign CPA Registration (외국공인회계사) — Article 40-2 through 40-9

CPA Act Chapter 5-2, added June 2011, establishes a separate registration regime for foreign CPAs. Under Article 40-3, a registered 외국공인회계사 may perform:
1. Advisory on the accounting law and accounting standards of the country of original qualification
2. Advisory on internationally recognized international accounting standards (IFRS)

Permitted practice modes (Article 40-9): Opening a foreign accounting office, being employed by a foreign CPA/firm, or being employed by a registered Korean accounting firm.

Registration requirements: proof of valid home-country CPA license; proof of no disqualifying conditions; disciplinary history verification; additional documentation per Presidential Decree. Administered by KICPA on behalf of FSC.

**Scope is narrow:** This regime does not permit performing Korean audits, Korean tax representation, or any other Article 2 duties under Korean law. It is limited to US GAAP, US accounting law, and IFRS advisory.

**Potential utility:** If the operator holds a valid US CPA license (not just degrees), registering as a 외국공인회계사 would permit advising on US GAAP and IFRS — potentially useful for cross-border M&A due diligence work involving US accounting standards.

---

## Section 5 — Business Entity Formation

### Dual US/Korean Citizen: No Restriction on Entity Registration

No restriction prevents a dual US/Korean citizen from registering any type of Korean business entity. Korean business registration (사업자등록) at the National Tax Service does not require disclosure of dual citizenship.

**Military service — threshold personal status issue:** Under the Nationality Act Article 12, a male born with dual citizenship who did not renounce Korean nationality before age 18 is subject to Korean military service obligations. Males aged 25–37 with unfulfilled military obligations face restrictions on overseas travel and potentially on business activities in Korea. This is a personal status question that must be resolved before any Korea-based business operation — it is independent of the business structure itself. [Requires individual legal counsel to assess.]

### Korean Entity Options

| Form | Korean term | Key features |
|---|---|---|
| Stock company | 주식회사 | Required if registering as 투자자문업 under FSCMA; most versatile for future regulatory pathways |
| Limited company | 유한회사 | Simpler governance; suitable if FSCMA advisory registration not planned initially |
| LLC | 유한책임회사 | Available since 2012 Commercial Code revision; pass-through flexibility |
| Incorporated association | 사단법인 | Nonprofit form; used by KCGS; grants-eligible but commercial activity limited |

No Korean entity form is specifically designed for professional services firms with mixed CPA/non-CPA staff performing non-audit work. Since the pipeline's activities fall outside the CPA Act's scope, any standard corporate form works. **주식회사 is most versatile** because it satisfies future FSCMA registration requirements (if pursued) and imposes no CPA Act constraints.

### US Entity Operating in Korea — PE Risk

A US LLC or corporation can operate in Korea through several structures:

- **Branch office (지점)**: Requires Korean court registration. A branch is a permanent establishment (PE) by definition under the US-Korea tax treaty Article 9.
- **Liaison office (연락사무소)**: Permitted for preparatory/auxiliary activities only. Cannot engage in revenue-generating activities.
- **Foreign direct investment company**: A Korean-incorporated entity funded by foreign investment. Minimum KRW 100 million investment threshold.
- **No Korean entity**: Operating a US LLC with Korean-based employees, Korean clients, and Korean-source consulting income without any Korean registered entity creates significant permanent establishment risk. A fixed place of business (office, employees) in Korea would almost certainly constitute a PE under the US-Korea tax treaty, subjecting the US entity to Korean corporate income tax on attributable profits.

---

## Section 6 — Precedents: How Analogous Entities Operate

### Korean Independent Research Firms (IRPs)

The known IRPs (리서치알음, 밸류파인더, 퀀트케이, FS리서치, 지엘리서치, 아리스) are staffed primarily by former sell-side analysts and fund managers — not CPAs. No publicly available evidence indicates any Korean IRP employs licensed CPAs specifically for CPA-related functions. The CPA Act has not been a practical constraint on the IRP industry because IRP activities fall entirely outside the CPA Act's scope.

### KCGS (한국ESG기준원)

KCGS, organized as a 사단법인, publishes governance and ESG ratings for approximately 1,024 listed companies. Its governance assessments involve evaluating accounting quality, board oversight, and audit committee effectiveness — overlapping with accounting analysis. KCGS operates without CPA licensing or accounting firm registration. Its work is framed as governance/ESG assessment, placing it outside both the CPA Act and FSCMA's investment advisory regime.

### GMT Research (Hong Kong)

Gillem Tulloch is a financial analyst since 1994, not a licensed accountant (CPA, CA, or equivalent). GMT is regulated by Hong Kong's SFC under a Type 4 license (capital markets license, not accounting license). Hong Kong has a Professional Accountants Ordinance (PAO) that reserves statutory audit to registered CPAs and restricts use of the "CPA" title — but does not reserve accounting research or financial analysis. GMT's entire business operates without any accounting license. The Korean parallel analysis confirms the same result under the Korean CPA Act.

### FRA Korea — Direct Korean Precedent

Forensic Risk Alliance operates in Korea as **한국에프엘아이(유)** — a 유한회사 (limited company). FRA Korea provides compliance, investigation, and data analytics services — described as a "multinational forensic consulting company." It is registered as a general professional services company under the Korean industrial classification "전문, 과학 및 기술 서비스업" (Professional, Scientific, and Technical Services). FRA Korea does not appear to be registered as a 회계법인 under the CPA Act.

This is a direct structural precedent: a financial analysis and forensic consulting firm operating in Korea as a general 유한회사 under the professional services industrial classification, performing financial analysis work without accounting firm registration.

---

## Section 7 — CPA Act and FSCMA: Two Independent Regimes

| Dimension | CPA Act (공인회계사법) | FSCMA (자본시장법) |
|---|---|---|
| Administering body | FSC (via KICPA) | FSC (via FSS) |
| Regulated activity | Audit, attestation, tax agency | Investment advisory, dealing, brokerage |
| Registration level | CPA personal registration (Article 7) | Business entity registration (Article 18) |
| Relevant to this pipeline? | No — activities outside scope | Yes — research reports, data licensing, consulting |

**No dual-licensing situation exists.** Producing accounting anomaly research for commercial sale triggers FSCMA considerations (유사투자자문업 or 투자자문업) but does not trigger CPA Act requirements, because the research is not audit, attestation, or tax representation.

Registering as 유사투자자문업 or 투자자문업 under FSCMA creates no presumption about CPA Act applicability. Sustinvest, which registered as 투자자문업, is not registered as a 회계법인. The Big 4 accounting firms hold both CPA Act registration and separate FSCMA licenses for their advisory businesses — these are independent registrations.

No FSC/FSS/KICPA joint guidance has been identified addressing the intersection of the two Acts for accounting research activities that do not constitute audit. The K-ICFR committee explicitly declined to answer a related February 2025 question, referring the questioner to FSC or KICPA.

---

## Section 8 — Summary Table by Staff Category

| Activity | Operator (US accounting degrees, no Korean CPA) | Registered Korean CPA (post-실무수습) | 수습공인회계사 (trainee, pre-registration) |
|---|---|---|---|
| Calculate M-Scores from DART data | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| Publish anomaly research reports | ✅ Permitted — cannot use "공인회계사" title | ✅ Permitted — may use CPA credential | ⚠️ Cannot use "공인회계사" title until registration complete |
| Sign off as CPA-quality work | ❌ Cannot represent as CPA audit/certification | ✅ Can represent as CPA-credentialed analysis (not audit) | ❌ Not yet registered |
| Perform audit or attestation | ❌ Criminal penalty | ✅ Only through registered accounting firm | ❌ Still in training |
| M&A due diligence consulting (non-attestation) | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| Advise on US GAAP/IFRS | ✅ If registered as 외국공인회계사; otherwise general advisory only | ✅ | ⚠️ Training status limitations |
| Tax representation (세무대리) | ❌ Requires CPA or 세무사 license | ✅ | ❌ Not registered |
| 실무수습 at this firm | N/A | Completed | ❌ Unlikely — startup does not qualify as designated training institution |
| Serve as FSCMA 투자권유자문인력 | Not directly — separate qualification required | ✅ If separately qualified | ❌ Not yet registered |

---

## Section 9 — Open Questions Requiring Legal Counsel

1. **Article 2 "incidental work" boundary.** Could a regulator or court argue that accounting anomaly analysis — even when not commissioned as an audit — is "incidental to" audit work and therefore CPA-reserved? The September 2025 amendment bill suggests the legislature does not intend this reading, but the bill has not been enacted.

2. **실무수습 eligibility as "other institution."** Enforcement Decree Article 12(1)(4) allows the FSC to designate additional training institutions upon KICPA recommendation. Could a financial research company seek KICPA recommendation and FSC designation as a training site? What criteria does the FSC apply? This would enable direct hiring of trainee CPAs.

3. **CPA credential use in research reports.** Can a CPA employed by a general research corporation include "공인회계사" after their name on published research reports? Article 54(2) penalizes non-CPAs for using the title; it does not explicitly address CPAs using their title in non-audit contexts at non-accounting firms. KICPA ethics guidelines may address this.

4. **Military service interaction with Korea-based business operation.** If the operator is a male dual US/Korean citizen with unfulfilled military service obligations, what specific restrictions apply to business registration, physical presence in Korea, and employment? This is a threshold personal status question prior to any Korea-based operations.

5. **Foreign CPA registration scope and utility.** If the operator holds a valid US CPA license, would registering as a 외국공인회계사 expand capabilities (e.g., IFRS/US GAAP advisory in M&A due diligence work), and does registration create additional regulatory obligations or restrictions?

6. **PE risk threshold for US LLC structure.** At what point does a Korean-based operator, Korean employees, and Korean-source consulting income trigger permanent establishment status under the US-Korea tax treaty Article 9? At what point is it more efficient to establish a Korean entity than to manage PE compliance?

7. **September 2025 CPA Act amendment bill status.** Has the Yoo Dong-su amendment bill advanced through committee or been enacted? If enacted, it would provide explicit statutory confirmation that non-attestation accounting research is outside the CPA Act's scope.

8. **IRP regulatory framework and CPA staffing.** If the FSS creates a formal IRP license under FSCMA, would it require at least one licensed CPA on staff for firms publishing accounting-focused research?

---

*This document will be updated as organizational decisions are made and as the September 2025 CPA Act amendment bill status changes. No commitments are implied by its contents.*
