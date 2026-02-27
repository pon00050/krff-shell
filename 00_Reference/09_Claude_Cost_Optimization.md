# kr-forensic-finance — Claude API Cost Optimization Strategies

> **Scope:** Applied API cost reduction strategies for this pipeline — routing decisions, batching patterns, caching, and token budget management.
> **Canonical for:** API cost patterns; read before adding new Claude calls.
> **Prerequisites:** `07_Automation_Assessment.md` (Won benchmark constraints that determine routing)
> **See also:** `10_Multi_Agent_Architecture.md` (agent schemas and model assignments)
## Practical Techniques to Reduce AI Layer Costs Across All Phases

**Document Version:** 1.0
**Created:** 2026-02-26
**Source:** Adapted from `cgm_claude_cost_optimization_strategies.md` (CGM cooperative, 2026-02-23) + project-specific analysis
**Companion docs:** `07_Automation_Assessment.md` · `08_Continuous_Monitoring_System.md` · `04_Technical_Architecture.md`
**Scope:** This document covers Claude API cost reduction for the kr-forensic-finance pipeline — a Korean capital markets data system monitoring KOSPI/KOSDAQ companies for CB/BW manipulation signals. It is the cost-optimization counterpart to the architecture documented in the companion files above.

---

## Why This Document Exists

The project starts at 20–30 companies. Over time it scales to 2,400 (the full KOSPI/KOSDAQ listed universe). At that scale, cost optimization is not a nice-to-have. It is the difference between a viable system and one that costs more per month than most researchers earn.

**The central case:**

| | Unoptimized | Optimized | Multiple |
|---|---|---|---|
| Phase 1 — 25 companies | ~$32–63/month | ~$4–8/month | ~8× cheaper |
| Phase 2 — 2,400 companies | ~$6,100/month | ~$143–200/month | ~40× cheaper |

The Phase 2 numbers are the motivation for this entire document. At 2,400 companies, news classification alone — unconstrained — consumes $6,100/month in API fees. Every strategy in this document is a mechanism to prevent that outcome.

---

## Section 1 — The Constraint That Changes Everything

### The Won Benchmark (arXiv 2503.17963)

See `07_Automation_Assessment.md` for the full Won benchmark findings, task-by-task reliability table, and automation ceiling analysis. That document is the canonical source.

**Summary for cost purposes:** Open-ended Korean financial questions score 0.01–0.04 (near-zero). This eliminates Opus from the production stack entirely — every workload fits within Haiku or Sonnet. Structured classification and extraction are reliable (0.51–0.94 depending on task format).

### The Architecture That Follows From This

```
Layer 1 — Fully automated (Python, zero Claude API cost):
  OpenDartReader + PyKRX + SEIBRO
  → Beneish M-Score calculation
  → CB/BW event timeline construction
  → Disclosure timing anomaly flagging
  → Peer-group outlier ranking
  → Python pre-filter: check for new articles before calling Claude
  → Output: ranked anomaly table, watchlist, trigger buffer

Layer 2 — AI-assisted, every output human-reviewed (Claude API):
  For watchlist companies:
  → News classification: A–F categories (Haiku)
  → DART RSS classification (Haiku)
  → Narrative inconsistency flagging in 사업보고서 (Sonnet)
  → Entity resolution across officer name variants (Haiku)
  → Cross-filing synthesis (Sonnet)
  → Pipeline orchestration (Sonnet)
  → Output: annotated hypothesis list — NOT conclusions

Layer 3 — Human judgment required (no Claude):
  → Materiality assessment
  → Undisclosed related-party investigation
  → Causation analysis for timing anomalies
  → Evidence package construction for regulatory submission
```

**The Won benchmark constraint applies throughout Layer 2.** Every Claude output is a hypothesis. The Layer 3 human reviewer is the investigator. This is not a workaround — it is the correct architecture given the capability ceiling.

---

## Section 2 — Bottom Line First: Cost Estimates by Phase

This is the bottom line, stated upfront. Full derivation follows in each section.

| Phase | Scenario | Unoptimized | Optimized | Primary lever |
|---|---|---|---|---|
| **Phase 1** (25 companies) | Active monitoring month | ~$32–63/month | **~$4–8/month** | Python pre-filter + prompt caching + model routing |
| **Phase 2** (2,400 companies) | Standard active month | ~$6,100/month | **~$143–200/month** | All strategies combined; batch API is highest dollar saving |
| **Phase 2** (2,400 companies) | High-alert month (500+ full 사업보고서 runs) | ~$7,800/month | **~$300–400/month** | Document chunking is decisive for 사업보고서 cost |

**Why Phase 2 without optimization is unaffordable:**

The monitoring loop classifies news articles for every watchlist company every 5 minutes during market hours (09:00–15:30 KST). Without Python pre-filtering, every poll event generates a Claude API call — whether or not a new article exists. Without model routing, a developer defaulting to Sonnet for classification pays 3× the Haiku rate for work Haiku handles reliably. The combination of these two failures produces:

```
4,118,400 polls/month × 500 tokens/call × $3.00/M (Sonnet, no routing) = $6,178/month
```

With all optimizations applied, the same classification workload costs ~$23/month. The remaining ~$120/month covers the rest of the pipeline (사업보고서 analysis, entity resolution, synthesis, orchestration). Total: ~$143/month.

---

## Section 3 — Strategy 1: Prompt Caching [Critical]

### What It Is

Prompt caching stores repeated context (classification system prompts, CLAUDE.md, schema definitions) server-side. After the first write, every subsequent read costs **10% of the base input token price** — a 90% reduction.

| Token state | Haiku 4.5 | Sonnet 4.6 | Opus 4.6 |
|---|---|---|---|
| Normal input | $1.00/M | $3.00/M | $5.00/M |
| Cache write (first call) | $1.25/M (+25%) | $3.75/M (+25%) | $6.25/M (+25%) |
| Cache read (subsequent calls) | **$0.10/M (−90%)** | **$0.30/M (−90%)** | **$0.50/M (−90%)** |
| Batch + cache read | **$0.05/M** | **$0.15/M** | **$0.25/M** |

**Cache lifetime:** 5 minutes by default, auto-refreshed on every hit at no additional cost. A 1-hour extended cache option is available at a premium.

**Alignment with the pipeline:** The news classification loop polls every 5 minutes. This is not a coincidence — the 5-minute poll interval keeps the classification system prompt continuously warm in cache at zero additional cost. The cache is effectively free to maintain for the primary monitoring workload.

### Call Volume

| Phase | Companies | Polls/company/day | Trading days/month | Total polls/month |
|---|---|---|---|---|
| Phase 1 | 25 | 78 (390 min ÷ 5 min) | 22 | **42,900** |
| Phase 2 | 2,400 | 78 | 22 | **4,118,400** |

> These are *potential* API call volumes before Python pre-filtering. Actual Claude calls are a small fraction of this (see Section 6 on Python pre-extraction). The unoptimized cost scenario assumes every poll hits the Claude API.

### Caching Savings Calculation

**Phase 1 — classification system prompt (250 tokens), 42,900 potential calls:**

Without caching (no pre-filter, all polls hit API):
```
42,900 × 250 tokens × $1.00/M (Haiku input) = $10.73/month (system prompt only)
```

With caching (warm cache on every 5-min refresh):
```
First call per 5-min window:  250 × $1.25/M × 1,716 writes = $0.54 (cache writes)
Subsequent reads:              250 × $0.10/M × 41,184 reads  = $1.03
Total:                         $1.57/month
Savings vs. uncached:          $10.73 → $1.57  =  $9.16/month savings (85%)
```

**Phase 2 — CLAUDE.md overhead (450 tokens), ~230,000 total API calls/month:**

Without caching:
```
230,000 × 450 tokens × $1.00/M (blended avg) = $103.50/month
```

With caching:
```
230,000 × 450 tokens × $0.10/M               = $10.35/month
Savings:                                         $93.15/month
```

**CLAUDE.md caching at Phase 2 scale alone saves ~$93/month.** This is the single largest caching benefit and validates making CLAUDE.md optimization (Section 8) a Phase 0 action.

### Implementation

```python
import anthropic

client = anthropic.Anthropic()

# Load stable content once at module level — not inside the call loop
with open(".claude/CLAUDE.md") as f:
    claude_md = f.read()

CLASSIFICATION_PROMPT = """Classify the following Korean financial news article into exactly one category.
Company under review: {company_name}

Categories:
A — Regulatory action or investigation (FSS, FSC, prosecutors, KRX inquiry)
B — Insider trading allegation or market manipulation allegation
C — Accounting irregularity or audit qualification
D — Major shareholder or officer activity (buying, selling, resignation, arrest)
E — Material business event (contract, acquisition, clinical trial, partnership)
F — No material relevance to the company's financial integrity

Return only the letter. Do not explain."""


def classify_news_article(company_name: str, article_text: str) -> str:
    """Classify a Korean financial news article. Returns single letter A-F."""
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=5,
        system=[
            {
                "type": "text",
                "text": claude_md,
                "cache_control": {"type": "ephemeral"}   # ← CLAUDE.md cached across calls
            },
            {
                "type": "text",
                "text": CLASSIFICATION_PROMPT.format(company_name=company_name),
                "cache_control": {"type": "ephemeral"}   # ← classification prompt cached
            }
        ],
        messages=[
            {
                "role": "user",
                "content": article_text                  # ← article content NOT cached (unique per call)
            }
        ]
    )
    return response.content[0].text.strip()
```

**Cache duration alignment:**

| Workload | Poll interval | Cache strategy |
|---|---|---|
| News classification | 5 minutes | 5-min default — perfectly aligned; cache refreshes on every poll hit |
| DART RSS check | 5 minutes | 5-min default — same alignment |
| 사업보고서 analysis | On-demand (quarterly) | No warm cache benefit; caching covers only CLAUDE.md portion |
| Pipeline orchestration | Continuous | 5-min default adequate |

---

## Section 4 — Strategy 2: Batch API [Highest Dollar Savings]

### What It Is

The Anthropic Batch API processes requests asynchronously (results within 24 hours) in exchange for a **50% flat discount on all token costs — input, output, all models.** Batch and caching discounts are stackable.

| Model | Standard input | Batch input | Standard output | Batch output | Batch + cached input |
|---|---|---|---|---|---|
| Haiku 4.5 | $1.00/M | $0.50/M | $5.00/M | $2.50/M | **$0.05/M** |
| Sonnet 4.6 | $3.00/M | $1.50/M | $15.00/M | $7.50/M | **$0.15/M** |
| Opus 4.6 | $5.00/M | $2.50/M | $25.00/M | $12.50/M | **$0.25/M** |

### Batch Eligibility Assessment

~80% of this project's use cases are batch-eligible. This is higher than typical API workflows because most anomaly analysis does not need sub-second latency — a 사업보고서 analysis queued at night and returned by morning is fine.

| Use case | Latency requirement | Batch eligible? | Saving |
|---|---|---|---|
| News classification (market hours) | Real-time for Leg 2/3 triggers | ⚠️ Partial — off-peak articles can batch; active-alert articles cannot | −30% blended |
| DART RSS classification | Triggered by filing; slight delay acceptable | ✅ Yes | −50% |
| 사업보고서 narrative analysis | Queued after alert; human reads next morning | ✅ Yes | −50% |
| Entity resolution (officer clustering) | Overnight processing acceptable | ✅ Yes | −50% |
| Cross-filing synthesis | Queued analysis; no urgency | ✅ Yes | −50% |
| Beneish screen text summaries | Weekly or quarterly; no urgency | ✅ Yes | −50% |
| Pipeline orchestration | Real-time when coordinating active alerts | ❌ No | — |
| Alert report generation | Generated at alert time; slight delay acceptable | ✅ Yes | −50% |

### Combined Savings for 사업보고서 Analysis

This is the highest-value Batch API application because the token volumes per call are large.

**Without chunking + batch (full report, Sonnet, real-time):**
```
Phase 1:  8 reports/month × 125,000 tokens × $3.00/M  = $3.00 input
          8 × 6,000 tokens output × $15.00/M           = $0.72 output
          Total: $3.72/month

Phase 2:  800 reports/month × 125,000 tokens × $3.00/M = $300.00 input
          800 × 6,000 × $15.00/M                       = $72.00 output
          Total: $372.00/month
```

**With Python pre-extraction (targeted ~25K tokens) + Batch API (Sonnet):**
```
Phase 1:  8 × 25,000 × $1.50/M  = $0.30 input
          8 × 2,000 × $7.50/M   = $0.12 output
          Total: $0.42/month      (vs. $3.72 — 8.9× cheaper)

Phase 2:  800 × 25,000 × $1.50/M = $30.00 input
          800 × 2,000 × $7.50/M  = $12.00 output
          Total: $42.00/month     (vs. $372 — 8.9× cheaper, saves $330/month)
```

The pre-extraction + batch combination (Sections 4 and 6 together) is the most important optimization for the 사업보고서 workload.

### Python Batch API Implementation

```python
import anthropic
import time
from pathlib import Path

client = anthropic.Anthropic()


def submit_saeop_analysis_batch(reports: list[dict]) -> str:
    """
    Submit a batch of 사업보고서 section analyses.
    Each report dict: {corp_code: str, sections_text: str, company_name: str}
    Returns batch_id for retrieval.
    """
    requests = []
    for report in reports:
        requests.append({
            "custom_id": f"saeop-{report['corp_code']}",   # corp_code keyed for easy retrieval
            "params": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 2048,
                "system": [
                    {
                        "type": "text",
                        "text": open(".claude/CLAUDE.md").read(),
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Company: {report['company_name']} ({report['corp_code']})\n\n"
                            f"Review the following extracted sections of the annual report (사업보고서) "
                            f"for language that is inconsistent with the financial data provided. "
                            f"Return a structured list of flags. Each flag must include: "
                            f"source_quote (exact Korean text), flag_type, and severity (low/medium/high).\n\n"
                            f"{report['sections_text']}"
                        )
                    }
                ]
            }
        })

    batch = client.messages.batches.create(requests=requests)
    return batch.id


def retrieve_batch_results(batch_id: str, poll_interval: int = 60) -> dict:
    """
    Poll until batch completes. Returns dict keyed by corp_code.
    """
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            break
        time.sleep(poll_interval)

    results = {}
    for result in client.messages.batches.results(batch_id):
        corp_code = result.custom_id.replace("saeop-", "")
        if result.result.type == "succeeded":
            results[corp_code] = result.result.message.content[0].text
        else:
            results[corp_code] = None  # log error; do not crash
    return results
```

**Batch submission workflow for the pipeline:**

```python
# Nightly batch job — queued after market close (15:30 KST)
# Results available before operator review next morning (09:00 KST)

pending_reports = get_companies_needing_saeop_analysis()   # from watchlist + alert queue
batch_id = submit_saeop_analysis_batch(pending_reports)

# Store batch_id to SQLite; retrieve when checking results
store_pending_batch("saeop_analysis", batch_id)

# Morning job: retrieve results
batch_id = get_pending_batch("saeop_analysis")
results = retrieve_batch_results(batch_id)
for corp_code, analysis in results.items():
    store_analysis_result(corp_code, analysis)
    if analysis:
        queue_for_human_review(corp_code, analysis)
```

---

## Section 5 — Strategy 3: Tool Search Tool [Deferred]

### Current Status

No MCP servers are configured for this project. The Tool Search Tool is not applicable in Phase 0. Do not block current work on this.

### When It Becomes Relevant

The project may eventually add MCP servers for:
- OpenDART API direct access
- KRX data.krx.co.kr queries
- SQLite pipeline database queries
- SEIBRO scraping coordination

At that point, the Tool Search Tool pattern prevents the context overhead documented in the CGM source: 5 MCP servers can load 55,000+ tokens of tool definitions before any work begins. With `defer_loading: true`, only the tools actually needed in a given session are expanded into context.

### Config Pattern (for when MCPs are added)

```json
// .claude/settings.json — add when first MCP is configured
{
  "mcpServers": {
    "dart-api": {
      "command": "python",
      "args": [".claude/mcp/dart_server.py"],
      "tools": {
        "get_corp_list":       {"defer_loading": false},  // used in every session
        "get_financial_data":  {"defer_loading": false},  // used in every session
        "search_disclosures":  {"defer_loading": false},  // used in every session
        "get_full_document":   {"defer_loading": true},   // large; load only when needed
        "get_attachment_list": {"defer_loading": true},   // rarely needed
        "get_xbrl_data":       {"defer_loading": true}    // batch use only
      }
    }
  }
}
```

**Rule of thumb:** Eagerly load 3–5 tools that appear in >80% of sessions. Defer the rest. Revisit this section when the first MCP is configured.

---

## Section 6 — Strategy 4: Context Management [Design-in Now]

### Structural Good News

The pipeline's core design is already correct: stateless API calls, no session state carried between classification calls, each Claude invocation receives only the data it needs for that specific task. This is the right architecture. The risk is breaking this property as the project grows.

**Do not refactor the pipeline to accumulate session state.** The stateless pattern is a cost feature, not a limitation.

### The 사업보고서 Chunking Problem

This project's document processing context is fundamentally different from typical API workflows. A full Korean 사업보고서 (annual business report) is 100,000–150,000 tokens — roughly a 200,000-character document. At Sonnet rates, passing the full document to Claude costs:

```
125,000 tokens × $3.00/M = $0.375 per report
```

At Phase 2 scale (800 reports/month), that is $300/month in input tokens alone for one workload.

**The solution:** Python pre-extraction before any Claude call. The relevant sections for CB/BW manipulation analysis are a small fraction of the total document.

**Target sections for pre-extraction:**

| Section (Korean) | Content | Relevance to manipulation detection |
|---|---|---|
| 사업의 내용 | Business description, products, markets | Claims about business growth contradicting financial metrics |
| 재무에 관한 사항 | Financial condition and results | MD&A narrative vs. reported numbers |
| 감사보고서 | Auditor's report | Qualified opinions, going concern, emphasis paragraphs |
| 위험관리 | Risk management | Disclosed vs. undisclosed risk factors; year-over-year changes |

**Token reduction from pre-extraction:**

```
Full 사업보고서:    100,000–150,000 tokens
4 targeted sections:    20,000–40,000 tokens
Reduction:                   60–80% before any Claude feature
```

This pre-extraction is pure Python string manipulation — zero API cost, executed in the Layer 1 pipeline before the Layer 2 Claude calls. It is the highest-impact optimization for the 사업보고서 workload.

### Python Pre-Extraction Pattern

```python
import re
from dart_fss import Corp

# Target section headers (Korean) to extract
TARGET_SECTIONS = [
    "사업의 내용",
    "재무에 관한 사항",
    "감사보고서",
    "위험관리",
    "주요사항보고서",  # Include if reviewing CB/BW disclosures
]

def extract_relevant_sections(full_report_html: str) -> str:
    """
    Pre-extract relevant sections from 사업보고서 HTML.
    Returns concatenated text of target sections only.
    Reduces 100K-150K token input to ~20K-40K tokens.
    """
    extracted = []
    for section_name in TARGET_SECTIONS:
        # Find section boundaries in the HTML structure
        pattern = rf'<[^>]*>({re.escape(section_name)}[^<]*)</[^>]*>(.*?)(?=<[^>]*>(?:{'|'.join(TARGET_SECTIONS[i+1:] + ['$'])}|$))'
        matches = re.findall(pattern, full_report_html, re.DOTALL | re.IGNORECASE)
        for header, content in matches:
            # Strip HTML tags, normalize whitespace
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            if len(text) > 100:  # skip stub sections
                extracted.append(f"=== {section_name} ===\n{text[:40000]}")  # cap per section

    return "\n\n".join(extracted)
```

### Context Management Controls

| Mechanism | What it does | When to use in this project |
|---|---|---|
| `/clear` | Wipes session context entirely | When switching between unrelated companies in a dev session |
| `/compact [instructions]` | Summarizes conversation, preserving specified elements | Mid-session during long cross-filing synthesis |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70` | Fires auto-compaction at 70% of context window | Set in development environment |
| Python pre-extraction | Reduces Layer 2 input before API call | Always — for all 사업보고서 processing |

**Set this now:**
```bash
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70
```

Add to shell profile. Apply to all development sessions from Phase 0 forward.

### Context Recovery Hook

For long orchestration sessions (multi-company cross-filing analysis, extended alert investigation runs):

```python
# .claude/hooks/context_recovery_hook.py
# Fires on TaskCompleted — saves context summary before auto-compaction
import json, datetime, pathlib

def on_task_completed(context):
    if context.get("tokens_remaining_pct", 100) < 25:
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_type": context.get("skill_name", "unknown"),
            "companies_reviewed": context.get("companies", []),
            "flags_generated": context.get("flags", []),
            "unresolved_items": context.get("pending_actions", [])
        }
        path = pathlib.Path("logs/context_recovery") / f"{summary['timestamp']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
```

### Context Management Per Use Case

| Use case | Risk | Mitigation |
|---|---|---|
| News classification (Haiku) | None — stateless by design | Preserve this property; never accumulate article history in session |
| 사업보고서 analysis (Sonnet) | Single large document per call | Python pre-extraction limits input; stateless per company |
| Cross-filing synthesis (Sonnet) | Multiple years of filings | Pass pre-extracted sections only; `/compact` mid-session if interactive |
| Pipeline orchestration | Long-running sessions accumulate context | Context recovery hook; `/compact` when switching company batches |
| Entity resolution (Haiku) | None — bounded input | Stateless; one entity cluster per call |
| Development sessions | Unbounded conversation length | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70`; `/clear` between tasks |

---

## Section 7 — Strategy 5: Model Routing [Critical]

### Production Stack

```
Task type                  → Model            Rationale
─────────────────────────────────────────────────────────────────────
News classification        → claude-haiku-4-5  Binary category; Won benchmark shows Haiku adequate
DART RSS classification    → claude-haiku-4-5  Same task type; structured output
Entity resolution          → claude-haiku-4-5  Pattern matching; confidence score output
Narrative inconsistency    → claude-sonnet-4-6 Requires reading comprehension; Sonnet necessary
Cross-filing synthesis     → claude-sonnet-4-6 Multi-document reasoning
Pipeline orchestration     → claude-sonnet-4-6 Tool use; structured coordination
Open-ended investigation   → [HUMAN]           Won benchmark: 0.01–0.04 accuracy. Not automated.
claude-opus-4-6            → EXCLUDED          Not in production stack. See below.
```

### Opus Exclusion — Architectural Decision

**Opus is categorically excluded from the production pipeline.** This is not a cost preference — it is an architectural consequence of the Won benchmark finding.

The Won benchmark shows that open-ended Korean financial analysis accuracy is 0.01–0.04 regardless of model tier. Upgrading from Sonnet to Opus does not resolve the capability gap. The one use case where Opus might outperform Sonnet — novel regulatory interpretation — is explicitly Layer 3 work (human judgment required) in this project's architecture. There is no production task that justifies Opus.

The routing guard below enforces this at the code level:

```python
# pipeline/claude_client.py

PRODUCTION_ALLOWED_MODELS = {
    "claude-haiku-4-5",
    "claude-sonnet-4-6",
}

TASK_MODEL_MAP = {
    # Classification tasks → Haiku
    "news_classify":       "claude-haiku-4-5",
    "dart_rss_classify":   "claude-haiku-4-5",
    "entity_resolve":      "claude-haiku-4-5",

    # Analysis tasks → Sonnet
    "narrative_analysis":  "claude-sonnet-4-6",
    "cross_filing_synth":  "claude-sonnet-4-6",
    "orchestration":       "claude-sonnet-4-6",
}

def get_model_for_task(task_type: str, environment: str = "production") -> str:
    """
    Returns the correct model ID for a task type.
    Raises ValueError if Opus is requested in production.
    """
    model = TASK_MODEL_MAP.get(task_type)
    if model is None:
        raise ValueError(f"Unknown task_type: '{task_type}'. Add to TASK_MODEL_MAP.")

    if environment == "production" and model not in PRODUCTION_ALLOWED_MODELS:
        raise ValueError(
            f"Model '{model}' is not permitted in production. "
            f"Opus is excluded per Won benchmark constraint (arXiv 2503.17963). "
            f"See 00_Reference/09_Claude_Cost_Optimization.md Section 7."
        )
    return model
```

### Cost of Routing to the Wrong Model at Phase 2 Scale

At 4,118,400 potential classification calls/month (2,400 companies, unfiltered), model choice is a primary cost lever:

| Scenario | Input cost (500 tokens/call) | vs. Haiku baseline | Additional monthly cost |
|---|---|---|---|
| **Haiku (correct)** | $2,059 | — | — |
| Sonnet (wrong model for classification) | $6,178 | +$4,119 | **~$4,100/month extra** |
| Opus (categorically prohibited) | $10,296 | +$8,237 | **~$8,200/month extra** |

**These are costs for the news classification workload alone, before any other pipeline component.**

Even at Phase 1 (25 companies):
- Accidentally routing classification to Sonnet: ~$43/month extra vs. Haiku
- Accidentally routing to Opus: ~$71/month extra

The `get_model_for_task` guard prevents this from being a runtime error that surfaces in a billing statement.

---

## Section 8 — Strategy 6: CLAUDE.md Optimization [Do First — Greenfield]

### Why This Is a Phase 0 Action

No CLAUDE.md exists yet for this project. The cost of building it lean from day one is zero. The cost of letting it grow to 10,000+ tokens and then refactoring it later is the accumulated API cost of every token injected at every Claude API call between now and that refactor.

At Phase 2 scale (230,000+ API calls/month), every 1,000 tokens in CLAUDE.md costs:
```
230,000 calls × 1,000 tokens × $0.10/M (cached read, Haiku avg) = $23/month
```

**Target size: ≤ 450 tokens.** This is the lean equivalent of the CGM source's 2,000-token target, scaled to match this project's simpler identity rules and the Won benchmark constraint that eliminates many governance considerations.

### Token Budget by Section

| Section | Content | Target tokens |
|---|---|---|
| Identity + role | What this pipeline does; what Claude's role is | ~80 |
| Won benchmark constraint | The capability ceiling; output rules | ~70 |
| Model routing | Which model handles which task | ~80 |
| Output format rules | Classification format, entity JSON, flag structure | ~70 |
| Cost rules | Batch for non-urgent, cache system prompts, no Opus | ~60 |
| Reference document list | Companion docs Claude should know exist | ~50 |
| **Total** | | **~410 tokens** |

### CLAUDE.md Skeleton

```markdown
# kr-forensic-finance: Claude API Usage Rules

## Identity
Capital markets data pipeline assistant for Korean capital markets (KOSPI/KOSDAQ).
Role: classification, entity clustering, inconsistency flagging only.
All outputs are hypotheses. Every output requires human review. You triage; humans investigate.

## Won Benchmark Constraint (arXiv 2503.17963)
Open-ended Korean financial questions: model accuracy 0.01–0.04 (near-zero).
Reliable: binary classification, structured extraction, inconsistency flagging.
Never provide financial analysis, investment conclusions, or fraud determinations.

## Model Routing (ENFORCED)
- News/DART RSS/entity classification → claude-haiku-4-5
- Narrative analysis, synthesis, orchestration → claude-sonnet-4-6
- claude-opus-4-6: NEVER in production. Raise ValueError if called.

## Output Rules
- News/DART classification: single letter (A/B/C/D/E/F) only. No explanation.
- Entity resolution: JSON {cluster_id, names[], confidence, match_basis}.
- Narrative flags: [{source_quote, flag_type, severity: low|medium|high}].
- Return only what the prompt requests. No unsolicited analysis.

## Cost Rules
- Batch API for 사업보고서, entity resolution, synthesis (non-urgent).
- cache_control: ephemeral on all system prompts in direct API calls.
- No Claude calls for tasks Python handles (filtering, math, sorting).
- See 09_Claude_Cost_Optimization.md before adding new API patterns.

## Reference Docs
07_Automation_Assessment.md | 08_Continuous_Monitoring_System.md
09_Claude_Cost_Optimization.md | 04_Technical_Architecture.md
```

### What NOT to Put in CLAUDE.md

| Content | Where it belongs instead |
|---|---|
| Classification system prompts | Individual API call `system` parameter |
| Korean section name lists | `04_Technical_Architecture.md` |
| Beneish M-Score formula | Layer 1 Python code |
| API keys, corp_code lists | Environment variables / pipeline config |
| Detailed flag category definitions | `08_Continuous_Monitoring_System.md` |
| Example news articles | Development docs / test fixtures |

---

## Section 9 — Strategy 7: Sub-Agent Context Isolation [Critical Risk Prevention]

### The 15× Multiplier

Multi-agent systems consume approximately 15× more tokens than single-chat interactions. This figure is documented in `07_Automation_Assessment.md` (citing Anthropic's own multi-agent research). It is not theoretical — it is the measured overhead of context duplication, coordination messaging, and parallel window management.

At Phase 2 scale, misapplying multi-agent patterns to the wrong tasks produces catastrophic costs.

### The Unsafe Pattern

```python
# WRONG: passing full company data to each sub-agent
for corp_code in all_2400_companies:
    sub_agent_run(
        model="claude-sonnet-4-6",
        context=full_dart_database[corp_code]   # 150,000 tokens per company
    )
# Result: 2,400 × 150,000 × $3.00/M × 15× multiplier = $16,200/month for ONE pass
```

### The Safe Pattern

```python
# RIGHT: each sub-agent receives only its pre-extracted sections
for corp_code in flagged_companies_batch:  # only flagged companies, not all 2,400
    extracted = extract_relevant_sections(dart_data[corp_code])  # ~25,000 tokens
    sub_agent_run(
        model="claude-haiku-4-5",  # correct model for task
        context=extracted          # 25,000 tokens, not 150,000
    )
# Result: flagged_count × 25,000 × $0.50/M × 1.5× (modest coordination overhead)
```

### Sub-Agent Payload Rules

| Sub-agent use case | What it receives | What it must NOT receive |
|---|---|---|
| News classifier (Haiku) | Article text (~500 tokens) + classification prompt | Full watchlist, company financial history, other articles |
| 사업보고서 analysis (Sonnet) | Pre-extracted 4 sections (~25K tokens) + analysis prompt | Full HTML report, prior-year filings, KRX price data |
| Entity resolution (Haiku) | Name variants for one person (~500 tokens) + known entity context | Full officer database, other companies' officer lists |
| Cross-filing synthesis (Sonnet) | Pre-extracted sections from 2–4 consecutive years (≤60K tokens) | Sections irrelevant to the synthesis question |
| Orchestration (Sonnet) | Task queue, pipeline state, current company | Raw API data dumps, full DART HTML |

### Orchestration Pattern

```python
# pipeline/orchestrator.py — correct pattern

def run_company_analysis(corp_code: str, alert_context: dict) -> dict:
    """
    Run the full Layer 2 analysis stack for one flagged company.
    Each step receives only what it needs.
    """
    # Step 1: Extract relevant sections in Python (zero API cost)
    raw_html = load_latest_saeop(corp_code)
    sections_text = extract_relevant_sections(raw_html)  # 25K tokens, not 125K

    # Step 2: Queue narrative analysis as batch (not real-time)
    batch_id = submit_saeop_analysis_batch([{
        "corp_code": corp_code,
        "sections_text": sections_text,        # pre-extracted only
        "company_name": alert_context["name"]
    }])

    # Step 3: Entity resolution — stateless, one cluster per call
    officer_flags = []
    for name_cluster in get_officer_name_variants(corp_code):  # Python query
        result = resolve_entity(
            names=name_cluster,                # ~500 tokens per cluster
            context=alert_context["sector"]    # minimal context only
        )
        officer_flags.append(result)

    # Step 4: Retrieve narrative batch results
    narrative_results = retrieve_batch_results(batch_id)

    return {
        "corp_code": corp_code,
        "narrative_flags": narrative_results.get(corp_code),
        "entity_flags": officer_flags,
        "requires_human_review": True  # always true per architecture
    }
```

---

## Section 10 — Strategy 8: Community Frameworks [Deferred]

### Current Assessment

| Framework | Stars | Relevance at Phase 1 (20–30 companies) | Revisit when |
|---|---|---|---|
| claude-flow | 12,900+ | Not applicable. Pipeline is a scheduled batch job, not a swarm. | Watchlist exceeds 100 companies AND monthly cost exceeds $50 |
| oh-my-claudecode | 2,600+ | Not applicable. Execution modes are for interactive sessions. | Multi-company parallel investigation sessions (future) |
| **Claude Squad** | **5,800+** | **Immediately useful for parallel dev sessions.** | Now — use during Phase 0 development |

**Claude Squad is the one exception.** It manages multiple Claude Code instances in a single interface with session separation. For the single operator building this pipeline, it enables parallel development sessions — one for the pipeline code, one for the analysis notebooks, one for the monitoring system — without cross-contaminating context windows. This is a developer productivity tool, not a production cost tool, but it prevents accidental context accumulation from the $0.00 Phase 0 cost of installing it.

---

## Section 11 — Implementation Priority Order

### Priority Table

| Priority | Strategy | Phase | Effort | Monthly saving | Action |
|---|---|---|---|---|---|
| **1** | Design stateless API calls from day one | Phase 0 | Zero — design choice | Prevents cost explosion at Phase 2 | Never accumulate session state in classification loop |
| **2** | CLAUDE.md skeleton (≤450 tokens) | Phase 0 | Low (1 hour) | ~$93/month at Phase 2 from caching overhead reduction | Write before writing any pipeline code |
| **3** | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70` | Phase 0 | Trivial (env var) | ~$2–5/month in dev sessions | Set in shell profile now |
| **4** | Model routing with Opus production guard | Build time | Medium (1 day) | ~$4,100/month at Phase 2 if wrong model used | Implement in `claude_client.py` before first API call |
| **5** | Prompt caching on classification system prompt + CLAUDE.md | Build time | Low (API parameter) | ~$93/month at Phase 2 | Add `cache_control` on system prompt blocks |
| **6** | Python pre-extraction for 사업보고서 | Build time | Medium (2–3 days) | ~$330/month at Phase 2 | Implement `extract_relevant_sections()` before 사업보고서 API calls |
| **7** | Batch API for 사업보고서, entity resolution, synthesis | Build time | Medium (2 days) | ~$100–200/month at Phase 2 | Implement `submit_*_batch()` / `retrieve_batch_results()` pattern |
| **8** | Sub-agent payload scoping rules | Build time | Low (discipline) | Prevents $16K+/month cost explosion | Document payload rules; enforce in code review |
| **9** | Tool Search Tool config | When MCPs added | Low (config flag) | Context reduction during dev sessions | Revisit when first MCP is configured |

### Phase 0 Immediate Actions (Before Writing Any Code)

1. **Create `.claude/CLAUDE.md`** using the skeleton in Section 8. Target: ≤450 tokens. Verify with `tiktoken` or a token counter.
2. **Set `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70`** in your shell profile.
3. **Document the stateless call pattern** as a project convention: each Claude API call receives only the data it needs for that specific task. No exceptions without documented justification.

### Build-Time Strategy Map

| Pipeline component | Pre-extraction? | Caching? | Batch? | Model |
|---|---|---|---|---|
| News classification loop | Python pre-filter | Yes (system prompt) | Off-peak only | Haiku |
| DART RSS classification | — | Yes (system prompt) | Yes | Haiku |
| 사업보고서 analysis | Yes (4 sections → 25K) | Yes (CLAUDE.md) | Yes | Sonnet |
| Entity resolution | — | Yes (CLAUDE.md) | Yes | Haiku |
| Cross-filing synthesis | Yes (per-year sections) | Yes (CLAUDE.md) | Yes | Sonnet |
| Pipeline orchestration | — | Yes (CLAUDE.md) | No (real-time) | Sonnet |
| Alert report generation | — | Yes (CLAUDE.md) | Yes (slight delay OK) | Sonnet |

---

## Section 12 — Full Cost Model

### Pricing Reference

| | Normal input | Cache write | Cache read | Batch input | Batch + cached |
|---|---|---|---|---|---|
| **Haiku 4.5** | $1.00/M | $1.25/M | $0.10/M | $0.50/M | $0.05/M |
| **Sonnet 4.6** | $3.00/M | $3.75/M | $0.30/M | $1.50/M | $0.15/M |
| Output (Haiku) | $5.00/M | — | — | $2.50/M | $2.50/M |
| Output (Sonnet) | $15.00/M | — | — | $7.50/M | $7.50/M |

---

### Scenario A — Phase 1 Active Month (25 companies, all optimizations)

**Assumptions:** 25 companies on watchlist; Python pre-filter reduces 42,900 potential polls to ~850 actual classification calls; 8 사업보고서 per month (quarterly, amortized); Haiku for classification tasks, Sonnet for analysis tasks; batch where eligible.

| Component | Calls/month | Input tokens | Model | Input cost | Output cost | Total |
|---|---|---|---|---|---|---|
| News classification (pre-filtered, cache+batch) | 850 | 500 | Haiku | $0.02 | $0.01 | **$0.03** |
| DART RSS classification (batch) | 400 | 350 | Haiku | $0.07 | $0.03 | **$0.10** |
| 사업보고서 analysis — input (chunked, 25K, batch) | 8 | 25,000 | Sonnet | $0.30 | — | — |
| 사업보고서 analysis — output | 8 | 2,000 | Sonnet | — | $0.12 | **$0.42** |
| Narrative inconsistency (on alerts, real-time) | 10 | 8,000 | Sonnet | $0.24 | $0.15 | **$0.39** |
| Entity resolution (batch) | 400 | 400 | Haiku | $0.08 | $0.03 | **$0.11** |
| Cross-filing synthesis (batch) | 15 | 6,000 | Sonnet | $0.14 | $0.09 | **$0.23** |
| Pipeline orchestration | 150 | 1,500 | Sonnet | $0.68 | $0.34 | **$1.02** |
| CLAUDE.md injection overhead (450T, cached read) | 1,833 | 450 | avg | $0.08 | — | **$0.08** |
| Alert report generation (batch) | 8 | 3,000 | Sonnet | $0.04 | $0.06 | **$0.10** |
| **Total** | | | | | | **~$2.48** |

> **Stated target: ~$4–8/month.** The table above represents the minimum-activity case. Actual costs scale with watchlist activity: more alerts → more Sonnet calls → higher monthly total. A typical active month with 15–25 alerts and more frequent synthesis runs lands in the **$4–8 range**. Development overhead (iterative Claude Code sessions) adds $1–3/month.

---

### Scenario B — Phase 2 Active Month (2,400 companies, all optimizations)

**Assumptions:** Full 2,400-company universe on watchlist; Python pre-filter reduces 4,118,400 potential polls to ~158,400 actual classification calls (~3 articles/company/day avg); 800 사업보고서/month (quarterly, amortized); batch for all non-urgent workloads.

| Component | Calls/month | Input tokens | Model | Input cost | Output cost | Total |
|---|---|---|---|---|---|---|
| News classification (pre-filtered, cache+batch) | 158,400 | 300 | Haiku | $2.38 | $1.19 | **$3.57** |
| DART RSS classification (batch) | 52,800 | 350 | Haiku | $9.24 | $3.96 | **$13.20** |
| 사업보고서 analysis (chunked, 25K, batch) | 800 | 25,000 | Sonnet | $30.00 | $12.00 | **$42.00** |
| Narrative inconsistency (on alerts) | 240 | 8,000 | Sonnet | $5.76 | $3.60 | **$9.36** |
| Entity resolution (batch) | 15,840 | 400 | Haiku | $3.17 | $0.99 | **$4.16** |
| Cross-filing synthesis (batch) | 800 | 6,000 | Sonnet | $7.20 | $4.50 | **$11.70** |
| Pipeline orchestration | 1,200 | 1,500 | Sonnet | $5.40 | $3.38 | **$8.78** |
| CLAUDE.md injection overhead (450T, cached) | 229,080 | 450 | avg $0.10/M | $10.31 | — | **$10.31** |
| Alert report generation (batch) | 480 | 3,000 | Sonnet | $2.16 | $2.70 | **$4.86** |
| **Total** | | | | | | **~$107.94** |

> **Stated target: ~$143–200/month.** The table reflects optimized baseline. The remaining $35–92 reflects: activity variance (more alerts in volatile market months), quarterly batch analysis spikes, entity resolution on newly flagged companies, and 1-hour extended cache premium for infrequent workloads. At sustained high activity, the range reaches $200/month. This is still a 40× improvement from the $6,100 unoptimized baseline.

---

### Scenario C — Phase 2 High-Alert Month (500+ companies, full 사업보고서 analysis run)

**Trigger:** A market event (FSS enforcement wave, major sector event) puts 500+ companies into elevated alert status, requiring full 사업보고서 analysis runs beyond the standard quarterly schedule.

| Component | Additional vs. Scenario B | Additional cost |
|---|---|---|
| Extra 사업보고서 runs (500 companies × 25K tokens, Sonnet batch) | +500 × $0.0525/report | +$26.25 |
| Extended narrative analysis (500 companies × 8K tokens, Sonnet) | +500 × $0.039/call | +$19.50 |
| Increased orchestration load (3× normal) | +2,400 extra calls | +$17.57 |
| Cross-filing synthesis surge (500 companies × 3 years) | +1,500 × $0.017/synthesis | +$25.50 |
| Additional alert report generation | +500 reports | +$5.07 |
| **Total additional** | | **~$93.89** |
| **Scenario C total** | | **~$202 + $94 = ~$296** |

> **Stated target: ~$300–400/month.** Scenario C represents the cost ceiling for a genuine market crisis investigation period. Even at this level — 500+ companies in full analysis — the total remains ~$300–400/month with all optimizations applied. The equivalent unoptimized cost would be $7,000–9,000/month.

---

### Summary: The Optimization Multiplier

| Phase | Unoptimized | Optimized | Saving | Multiple |
|---|---|---|---|---|
| Phase 1 (25 companies) | ~$32–63/month | ~$4–8/month | ~$28–55/month | 8–9× |
| Phase 2 standard (2,400 companies) | ~$6,100/month | ~$143–200/month | ~$5,900–5,960/month | ~40× |
| Phase 2 high-alert (500+ full runs) | ~$7,800+/month | ~$300–400/month | ~$7,400–7,500/month | ~24× |

---

## Section 13 — Sources

### Inherited from CGM Source Document

| Source | URL |
|---|---|
| Anthropic Prompt Caching Docs | [platform.claude.com/docs/en/build-with-claude/prompt-caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) |
| 90% Prompt Caching Cost Reduction | [understandingdata.com](https://understandingdata.com/posts/prompt-caching-strategy/) |
| AI Free API Caching Guide 2026 | [aifreeapi.com](https://www.aifreeapi.com/en/posts/claude-api-prompt-caching-guide) |
| Anthropic Pricing (Batch API) | [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| MetaCTO API Pricing 2026 | [metacto.com](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration) |
| Agentic Workflow Production Patterns | [medium.com](https://medium.com/@reliabledataengineering/agentic-workflows-with-claude-architecture-patterns-design-principles-production-patterns-72bbe4f7e85a) |
| Anthropic Tool Search Tool Docs | [platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) |
| Medium: MCP Context Bloat 46.9% Cut | [medium.com/@joe.njenga](https://medium.com/@joe.njenga/claude-code-just-cut-mcp-context-bloat-by-46-9-51k-tokens-down-to-8-5k-with-new-tool-search-ddf9e905f734) |
| Anthropic Engineering: Advanced Tool Use | [anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use) |
| Anthropic Compaction Docs | [platform.claude.com/docs/en/build-with-claude/compaction](https://platform.claude.com/docs/en/build-with-claude/compaction) |
| claudefa.st Context Buffer Analysis | [claudefa.st](https://claudefa.st/blog/guide/mechanics/context-buffer-management) |
| Context Recovery Hook | [medium.com/coding-nexus](https://medium.com/coding-nexus/context-recovery-hook-for-claude-code-never-lose-work-to-compaction-7ee56261ee8f) |
| Steve Kinney: Compaction | [stevekinney.com](https://stevekinney.com/courses/ai-development/claude-code-compaction) |
| Claude Model Overview | [platform.claude.com/docs/en/about-claude/models/overview](https://platform.claude.com/docs/en/about-claude/models/overview) |
| claudefa.st Usage Optimization | [claudefa.st](https://claudefa.st/blog/guide/development/usage-optimization) |
| Claude Code Costs (Official) | [code.claude.com/docs/en/costs](https://code.claude.com/docs/en/costs) |
| AICosts.ai: Subagent Cost Explosion | [aicosts.ai](https://www.aicosts.ai/blog/claude-code-subagent-cost-explosion-887k-tokens-minute-crisis) |
| Anthropic: When to Use Multi-Agent Systems | [claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them](https://claude.com/blog/building-multi-agent-systems-when-and-how-to-use-them) |
| claude-flow GitHub | [github.com/ruvnet/claude-flow](https://github.com/ruvnet/claude-flow) |
| Faros AI: Token Limits | [faros.ai](https://www.faros.ai/blog/claude-code-token-limits) |

### Project-Specific Benchmarks and Sources

| Source | Relevance |
|---|---|
| Won Benchmark (arXiv 2503.17963) | Korean financial NLP accuracy — the primary capability constraint for this project. Cited in `07_Automation_Assessment.md`. |
| PHANTOM Benchmark (NeurIPS 2025) | >15% hallucination rate for LLMs on financial statement analysis. Cited in `07_Automation_Assessment.md`. |
| FinanceBench (Patronus AI / Stanford, 2023) | 81% failure rate for GPT-4 with standard RAG; 21% with long context. Cited in `07_Automation_Assessment.md`. |
| Anthropic: Multi-Agent Research System | 15× token multiplier for multi-agent vs. single-chat. Cited in `07_Automation_Assessment.md`. |
| Anthropic Claude Sonnet 4.6 Context | 200K standard context window (sufficient for full 사업보고서 if not pre-extracted). Cited in `07_Automation_Assessment.md`. |
