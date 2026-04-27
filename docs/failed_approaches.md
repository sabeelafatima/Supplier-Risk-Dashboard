# Failed Approaches: What Didn't Work and Why

## 1. Real-Time AI Narrative on Click

**What I tried first.** Each time a user clicked a supplier in the dashboard, fire a Claude API call to generate the narrative live.

**Why it broke.** Three problems compounded:
- Latency: 3-5 seconds per click is unacceptable in an interactive dashboard.
- Cost: 100 suppliers × multiple clicks per session × multiple users = unbounded API spend.
- Rate limits: a busy review meeting with multiple PMs would hit per-minute limits.

**What I changed.** Pre-compute narratives in a Python script that runs nightly (or on-demand). Store them in `supplier_narratives.csv`. Join into Power BI as a static column.

**Lesson.** Real-time LLM in interactive dashboards is almost always wrong. Pre-compute on a schedule, refresh as data changes. The freshness penalty (up to 24 hours stale) is acceptable for risk monitoring; the latency, cost, and reliability wins are not.

---

## 2. ML-Based Risk Scoring

**What I tried first.** Train a small classifier (logistic regression or gradient boost) on the synthetic supplier features to predict tier.

**Why it broke.** Two reasons. First, with synthetic data, the model just learned the rules I encoded into the data generator. Circular. Second, even if I had real data, a black-box ML model is harder to defend in front of a procurement leader. "Why did this supplier score 47?" gets a useless answer from a tree ensemble.

**What I changed.** Stuck with a transparent weighted formula. The 5-factor weighted score is auditable: any score can be traced to specific input metrics. A real org with real historical data could move to ML later, but the formula version is the right starting point.

**Lesson.** Interpretability beats marginal accuracy for PM tools. If a Director can't argue with your model in plain English, your model loses to whichever simpler tool the Director can argue with.

---

## 3. Single-Dimension Scoring

**What I tried first.** Score each supplier on quality only, with quality being PPAP-status-driven.

**Why it broke.** Suppliers like the deliberately-injected MFG-073 (PPAP approved, 4 quality escapes, 78% OTD) scored as healthy on quality alone. The whole point of the dashboard is to surface multi-dimensional risk, and a single-dimension model defeated that.

**What I changed.** Five-factor weighted model with quality having a 30% weight inside which PPAP and escapes are weighted 60/40. This forces the conflict cases to surface.

**Lesson.** The interesting risks are almost always at the intersection of dimensions. Single-axis scoring misses them by design.

---

## 4. Random Synthetic Data

**What I tried first.** Used `random.uniform()` for every field with no intentional structure.

**Why it broke.** The dashboard had no interesting cases. The "top 5 at-risk" looked random rather than telling a story. An interviewer reviewing the demo would see noise, not insight.

**What I changed.** Hand-crafted edge cases (the conflict-pattern suppliers, the financial distress suppliers, the headline MFG-073). Every intentional case is documented in `synthetic_data_methodology.md` so I can defend it in interviews.

**Lesson.** Test data without intentional structure produces uninteresting demos. The 8 "PPAP-approved-with-escapes" suppliers are the demo; everything else is the realistic background noise that makes those 8 look real.

---

## 5. Including Sensitive Real Data Patterns

**What I tried first.** Used real supplier name patterns I'd seen at Skyworks (without naming them directly).

**Why it broke.** Even pattern-matching real suppliers risks confidentiality. A reviewer who knows the industry could potentially infer real relationships.

**What I changed.** Generated supplier names from a fixed list of generic prefixes ("Pacific", "Atlas", "Volta") and suffixes ("Solutions", "Industries", "Tech"). No pattern matches any real supplier. The README explicitly states all names are synthetic.

**Lesson.** Confidentiality is non-negotiable for portfolio projects from a current employer. The bar for "could this be inferred to be a real company" is high, and the cost of a bad inference is much greater than the benefit of marginally more realistic names.

---

## 6. AI Picking the Weights

**What I tried first.** Asked Claude to suggest weights based on a description of typical NPI priorities.

**Why it broke.** The output was reasonable but variable. Different runs produced different weight assignments. For a model that needs to be defended in interviews and tuned for specific orgs, AI-suggested weights add no value over human judgment.

**What I changed.** Picked weights manually based on industry knowledge, documented the reasoning in `risk_scoring_methodology.md`, and made every weight defensible.

**Lesson.** AI is for synthesis and narrative, not for strategic decisions. Weighting risk factors is a strategic decision. Humans pick weights, AI explains them.
