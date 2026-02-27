# Policy Context: 신고포상금 제도개편 (February 25, 2026)

> **Scope:** The FSC/FSS whistleblower reward reform of February 25, 2026 — the regulatory event that initiated this project.
> **Canonical for:** 신고포상금 reform details; regulatory trigger context.
> **See also:** `03_Project_Rationale.md` (why this project, `05_Regulatory_Environment.md` (broader FSC/FSS context)

## The Triggering Event

On February 25, 2026, the Financial Services Commission (금융위원회) and Financial Supervisory Service (금융감독원) announced a sweeping reform of the whistleblower reward system for stock price manipulation (주가조작) and accounting fraud (회계부정) under the Capital Markets Act (자본시장법) and External Audit Act (외부감사법).

**Legislative vehicle:** Amendments to 자본시장법 시행령, 외부감사법 시행령, 불공정거래 포상규정, and 회계부정 포상규정.

**Public comment period:** February 26 – April 7, 2026 (40 days)

**Target implementation:** Q2 2026

---

## Three Core Changes

### 1. Reward cap abolished entirely

| Category | Previous cap | New cap |
|---|---|---|
| Unfair trading (불공정거래) | 3 billion won | None |
| Accounting fraud (회계부정) | 1 billion won | None |

### 2. Reward calculated as up to 30% of recovered illicit gains

Previous system: complex scoring matrix based on company asset size, trade volume, violation count, sanction level, and illicit gain size — difficult to predict and frequently disconnected from the actual scale of harm.

New system: **up to 30% of confirmed illicit gains recovered or fines imposed**, multiplied by the reporter's contribution level. Simple, proportional, and predictable.

Minimum guarantees regardless of scale:
- Unfair trading: 5 million won (if gains are small); 5 million won or less (if no fine imposed)
- Accounting fraud: 3 million won

Reference: US SEC pays up to 30% of sanctions exceeding $1 million USD to whistleblowers — the Korean reform explicitly benchmarks against this.

### 3. Cross-agency eligibility

Previously: rewards only paid if the original report was filed with 금융위원회, 금융감독원, 한국거래소, or 한국공인회계사회.

Now: reports filed with 경찰청, 국민권익위원회, or other administrative agencies that are then referred or shared with FSC/FSS **also qualify** for the reward.

---

## Whistleblower Eligibility: Insider-Only?

### The law does not explicitly restrict eligibility to insiders.

The FSC communications emphasize insiders because "unfair trading and accounting violations are organized, intelligent crimes where insiders' information plays a decisive role" — but this is the rationale for removing the cap, not a statutory boundary.

Eligibility is determined by:
- Completeness and specificity of the report (신고내용의 충실성 및 구체성)
- Evidentiary quality (구체적인 위반사실 및 증거자료 동시 제출 required)
- Contribution level to the ultimate enforcement outcome

An external analyst submitting a well-documented, evidence-backed report based on public data analysis can theoretically qualify.

### What this means for independent researchers

The practical obstacle is evidentiary, not eligibility-based:

| Scenario | Assessment |
|---|---|
| Submitting a generic tip based on a price anomaly | Very low probability — no investigative added value |
| Submitting a systematic analysis with documented methodology | Credible; institutions treat this as triage intelligence |
| Producing the kind of work short-sellers (Hindenburg, Citron) publish before filing with regulators | This is the model that has won SEC awards for non-insiders |

The gap between "anomaly flagged" and "부당이득 확정·환수" (when the reward is actually paid) can span 2–5 years of investigation. This is not a near-term income vehicle. It is a long-horizon public good contribution with an optionality on future reward.

---

## Why This Project Exists

The policy reform signals that the Korean government is investing in financial misconduct detection infrastructure. The data infrastructure for independent forensic analysis exists (see `02_Data_Sources.md`). What does not exist is a maintained, reproducible, public pipeline joining these sources into a usable dataset.

This project builds that missing layer.

---

## Sources

- FSC Press Release, February 25, 2026: 자본시장법·외부감사법 시행령 및 하위규정 입법예고
- 헤럴드경제: https://biz.heraldcorp.com/article/10682306
- 아주경제: https://www.ajunews.com/view/20260225152617719
- 한국경제: https://www.hankyung.com/article/2026022543196
- 금융위원회 불공정거래신고: https://www.fsc.go.kr/pa030101
