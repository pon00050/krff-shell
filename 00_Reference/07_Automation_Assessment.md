# Automation Assessment: Python + Claude AI — Honest Evaluation

> **Scope:** Automation ceiling analysis, Won benchmark findings (arXiv 2503.17963), Claude reliability by task type, and false positive rates for ML-based fraud detection.
> **Canonical for:** Won benchmark results; automation ceiling; false positive rates; Claude capability limits.
> **See also:** `09_Claude_Cost_Optimization.md` (cost implications), `10_Multi_Agent_Architecture.md` (architecture that follows from these limits)

*Technical facts verified via web research, February 2026.*

---

## The Honest Framing

The user's intuition — that much of this work does not require professional accountant judgment — is **partially correct** for the screening layer and **meaningfully wrong** for the investigation layer. The distinction between these two layers is the most important thing in this document.

The SEC's own Accounting Quality Model (AQM), deployed since 2013, explicitly states:

> *"We have not built a model that can 'detect fraud' per se, but rather hope to provide one more tool that the already sophisticated staff of the SEC can use."*

This is the ceiling. Everything below it can be automated. Everything above it cannot.

---

## What Can Be Automated — Confirmed High Reliability

These tasks involve structured data, deterministic calculations, and no judgment calls:

| Task | Automation Level | Method |
|---|---|---|
| Data extraction from OpenDART API | 95%+ | OpenDartReader + scheduled Python scripts |
| OHLCV and short selling data pull | 95%+ | PyKRX |
| Beneish M-Score calculation | 100% | Pure arithmetic on DART financial statement fields |
| Disclosure timing anomaly flagging | 90%+ | Timestamp delta (DART filing time vs. KRX price movement) |
| CB/BW issuance event detection | 90%+ | DART 주요사항보고서 category filter |
| SEIBRO conversion/exercise event extraction | 80% | Web scraping or API where available |
| Peer-group outlier ranking | 95%+ | Statistical comparison across sector groupings |
| Officer/shareholder network graph construction | 70–80% | networkx on disclosed relationship data; entity resolution is the hard part |
| Report generation (markdown, Excel output) | 95%+ | Templated output from structured screening results |

The Beneish M-Score in particular is entirely automatable: it is 8 ratio calculations using inputs that are directly available from DART XBRL data. No judgment, no interpretation — just arithmetic. The question is whether the output is useful, which depends on the false positive rate (discussed below).

---

## What Claude AI Can Help With — With Important Caveats

### What it can usefully do

**Narrative inconsistency detection:** Claude (200K token standard context, 1M token extended beta) can hold an entire 사업보고서 in context and identify language that contradicts the financial numbers. Example: a company claims strong sales pipeline growth in the MD&A section while accounts receivable balances are deteriorating. This is a genuine LLM capability.

**Entity resolution assistance:** When the same person appears across DART filings as "김철수," "김 철수," and "KIM CHULSOO," Claude can help cluster these as likely the same individual. It cannot guarantee correctness, but it can reduce the manual workload substantially.

**Cross-filing synthesis:** Given a set of DART filings for the same company across multiple years, Claude can summarize changes in disclosure language, flag dropped risk factors, or identify newly inserted boilerplate.

**Pipeline orchestration:** Claude Sonnet 4.6 supports tool use (function calling), enabling agentic workflows where Claude orchestrates Python scripts, queries the DART API, processes results, and generates structured output without human intervention at each step.

### What it cannot reliably do — confirmed by research

**Korean-language open-ended financial analysis:** The Won (₩on) benchmark (arXiv 2503.17963, March 2025), the first comprehensive Korean financial NLP evaluation, found:
- Best models score **0.01–0.04 on open-ended Korean financial questions** (near-zero accuracy)
- Multiple-choice format: 0.51–0.94 (high variance)
- Finance & Accounting category: 0.78 (best model, multiple-choice only)

Open-ended reasoning — "what is unusual about this company's disclosure?" — is what anomaly analysis requires. The benchmark says models fail at this in Korean. **This is the single most important limitation for this project.**

**Hallucination risk in long documents:** The PHANTOM benchmark (NeurIPS 2025) found >15% hallucination rates when LLMs analyze financial statements even in best-case setups. The FinanceBench benchmark (Patronus AI, Stanford, 2023) found 81% failure rates for GPT-4 with standard RAG retrieval; 21% with long context. The best-case Oracle context setup (model handed the exact right passage) still produces 15% wrong answers.

**Implication:** Claude outputs on narrative sections of DART filings should be treated as hypothesis-generation, not conclusions. Every flagged inconsistency needs a human review step before it is acted upon.

---

## The False Positive Problem — The Operational Limiting Factor

This is where the honest critical assessment is most important.

Research on ML-based financial statement fraud detection (Kelley School of Business, 2022 review):
- Newer ML models achieved ~70–82% recall on fraud cases
- But flagged **40%+ of non-fraud firms as suspicious** — a catastrophically high false positive rate for any investigative program
- The Beneish M-Score, by contrast, flags about 17.5% of non-manipulators — lower false positives, but lower recall on fraud
- A combined model (Random Forest + Beneish + Altman) achieves ~83% accuracy in controlled settings (Istanbul market study, Sagepub 2025)

The implication for this project: the screen will produce a list of companies with anomaly flags. A substantial fraction of those companies will have legitimate explanations for their anomalous signals. The screen does not tell you which fraction is which — that requires investigation.

If the screen flags 200 KOSDAQ companies as anomalous, perhaps 20–40 of them have genuine manipulation signals worth investigating. Separating those from the legitimate anomalies is the work that requires human judgment.

---

## Where Professional Judgment Is Actually Required

This is the part the user may underestimate:

**1. Materiality assessment**
Auditing standards explicitly define this as a "matter of professional judgment." Whether a specific anomaly is material — large enough and meaningful enough to indicate intentional manipulation rather than legitimate business change — cannot be reliably automated. The SEC's AQM explicitly cannot do this; neither can Claude.

**2. Undisclosed related-party identification**
DART discloses *known* related parties. The CB/BW manipulation schemes that the FSS prosecuted specifically work by *concealing* the related-party relationships — using investment partnerships (투자조합) to disguise the fact that the CB subscriber is controlled by the same syndicate as the issuer. Detecting those concealed relationships requires external registry searches, cross-referencing business registration records, sometimes foreign entity lookups, and contextual judgment about why a transaction was structured the way it was. An LLM cannot identify what is not in the disclosed data.

**3. Causation vs. correlation in timing anomalies**
Price moved +7% on volume 3x average the day before a material disclosure. Was that insider trading? Or was there a sector-wide event, an analyst note, or a news article the system didn't capture? Distinguishing these cases requires contextual analysis that automation cannot reliably provide.

**4. Legal defensibility**
A tip submitted to the FSC requires a documented evidence package ("구체적인 위반사실 및 증거자료"). An automated screen output — "Beneish M-Score = -1.3, ranked 12th among KOSDAQ companies this quarter" — is not that evidence package. Converting a screening signal into a documentable, legally defensible referral requires a human to verify, contextualize, and document the finding.

---

## Claude's Technical Capabilities — Confirmed

**Context window (claude-sonnet-4-6):**
- Standard: 200K tokens (~150K words) — sufficient for a full annual report in a single request
- Extended beta (1M tokens): available to Tier 4 organizations — sufficient for multiple multi-year filings simultaneously
- Max output: 64K tokens

**Multi-agent orchestration:**
- Officially supported via Anthropic API tool use
- Orchestrator-worker pattern: lead agent decomposes tasks, parallel subagents execute
- Documented Anthropic internal test: multi-agent Claude system outperformed single-agent Claude Opus 4 by 90.2% on research evaluation tasks; parallel tool execution reduced research time by up to 90%
- **Cost caveat:** Multi-agent systems consume approximately 15x more tokens than single-chat interactions — this is a real budget consideration

Source: [Anthropic: How We Built Our Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system)

**Why claude-opus-4-6 is excluded from this architecture (current scope):**

Opus 4.6's genuine advantages over Sonnet 4.6 are long-context retrieval fidelity (76% on MRCR v2 1M 8-needle vs. an unspecified but lower Sonnet figure — context rot is minimal even at 800K–1M tokens) and deeper multi-step expert reasoning. In every other dimension — GUI automation, coding benchmarks, structured extraction — Sonnet 4.6 is within 1–2% of Opus at approximately one-fifth the cost.

Cross-checking those advantages against the tasks this architecture actually assigns to Claude:

| Agent | Task | Does Opus's advantage apply? |
|---|---|---|
| Monitoring | Binary A–F classification | No — pattern matching, not reasoning |
| SEIBRO parsing | Structured HTML extraction | No |
| Entity resolution | Name clustering + confidence score | No |
| Orchestrator | Decompose, delegate, route | No — coordination, not expert reasoning |
| Narrative inconsistency | Flag contradictions: Korean text vs. financial ratios | **Partially** — see note below |

The narrative inconsistency agent is the only task where Opus's capabilities are directionally relevant. However, two constraints keep Sonnet sufficient at current scope:

1. **The Won benchmark applies to all models.** Open-ended Korean financial reasoning scores 0.01–0.04 across the best available models — Opus included. The bottleneck is task type in Korean, not model capacity. Paying for Opus does not escape this ceiling.
2. **Structured output constraint.** The narrative agent outputs `[{source_quote, flag_type, severity}]` — a structured extraction task. This is not the open-ended deep reasoning where the Sonnet–Opus gap is widest.

**Re-evaluate Opus if:** the narrative inconsistency agent is asked to synthesise multi-year 사업보고서 corpora exceeding ~500K tokens in a single context, where Opus's long-context retrieval accuracy becomes the binding constraint rather than the Won benchmark reasoning ceiling. At that scale, the accuracy delta may justify the cost premium. Until then, the `ValueError` guardrail stands.

---

## The Realistic Architecture

```
Layer 1 — Fully automated (Python, no AI):
  OpenDartReader + PyKRX + SEIBRO scraper
  → Beneish M-Score calculation
  → CB/BW event timeline construction
  → Disclosure timing anomaly flagging
  → Peer-group outlier ranking
  → Output: ranked anomaly table (CSV)

Layer 2 — AI-assisted, human-reviewed (Claude API):
  For top N flagged companies:
  → Pull 사업보고서 narrative sections
  → Claude: "Flag language inconsistent with the financial data below"
  → Claude: entity resolution across officer name variants
  → Claude: summarize year-over-year disclosure changes
  → Output: annotated report per company (human must verify)

Layer 3 — Human judgment required:
  → Materiality assessment for each flag
  → Undisclosed related-party investigation (external registries)
  → Causation analysis for timing anomalies
  → Evidence package construction for any regulatory submission
```

This architecture is realistic and buildable. Layers 1 and 2 are the project scope. Layer 3 is where the output goes — to investigators, journalists, or researchers who can provide the judgment.

---

## Automation Ceiling Summary

| Question | Answer |
|---|---|
| Can the screening pipeline be automated? | ~80–90% of it, yes |
| Can Claude analyze Korean-language DART filings? | Partially — structured data well, open-ended narrative analysis unreliably |
| Will there be false positives? | Yes — expect 40%+ of flagged companies to have legitimate explanations |
| Does this replace a professional accountant? | No — it replaces the data collection and initial screening work; judgment on flagged cases still requires a human |
| What is the output? | A triage tool — a ranked list of companies warranting closer human investigation |
| Is that output valuable? | Yes — it is the missing layer between raw DART data and actual investigation |
