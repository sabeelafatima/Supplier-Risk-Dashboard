# Risk Scoring Methodology

This document explains how the supplier risk score is computed, why each factor is weighted as it is, and how an interviewer should expect you to defend the design. If you cannot answer "why this weight?" in 30 seconds for any factor, the methodology is hollow.

## The Five Factors

| Factor | Weight | What It Captures | Why This Weight |
|--------|--------|------------------|-----------------|
| Quality | 30% | PPAP status + quality escapes | Quality issues are the most expensive failure mode in NPI; field returns and recalls dwarf supplier-side savings |
| Delivery | 25% | OTD + lead time | Schedule risk is the second-most expensive failure; a 1-week slip late in NPI costs ramp revenue |
| Capacity | 20% | Confirmation + utilization | Predicts ramp readiness; less acute than quality/delivery in pre-production phases |
| Financial | 15% | Financial health proxy 1-5 | Catastrophic but rare; small weight reflects low-probability-high-impact reality |
| Geopolitical | 10% | Regional risk index | Slow-moving signal; matters for diversification strategy more than weekly review |

These weights total 100%. They are defensible defaults, not sacred. A real org would tune them per product class and per gate phase (DVT, PVT, MP).

## Why Quality Gets the Largest Weight

Three reasons:

1. **Quality issues compound.** A supplier that ships parts with a 2% defect rate creates downstream cost everywhere: rework, returns, warranty, brand damage. Delivery slips are recoverable; quality escapes are often not.
2. **Quality is leading-indicator visible.** Escapes in the last 60 days are a strong predictor of escapes in the next 60 days. This is the most actionable factor for a PM running weekly reviews.
3. **Quality and PPAP can disagree.** PPAP is a point-in-time qualification. Quality escapes are an ongoing measurement. The 60/40 split between PPAP and escapes inside the quality factor reflects this: PPAP is the foundation, escapes are the ground truth.

## Why Delivery Is Second

Delivery slips are recoverable but expensive. A 1-week slip at PVT costs 1 week of ramp revenue plus opportunity cost. The OTD scoring is sigmoid-like (95+ = 100, 80 = 50, 70 = 0) because the difference between 95% and 99% OTD matters less than the difference between 80% and 90%.

Lead time is a small penalty inside the delivery factor because it interacts with risk asymmetrically: a 90-day lead time supplier that's on-time is fine, but a 90-day lead time supplier with capacity issues is catastrophic.

## Why Capacity Is Third

In pre-production phases (DVT, PVT), capacity matters less because volumes are small. In ramp (post-MP), capacity becomes the dominant risk. This is why a real org would tune the weights up to ~30-35% for capacity at MP phase and down to ~10-15% at DVT phase.

The default 20% is the middle weight, appropriate for the typical PVT-phase use case this dashboard targets.

## Why Financial Is Only 15%

Financial distress is catastrophic when it happens (supplier bankruptcy = 6-12 month recovery), but it is rare and slow-moving. The 15% weight reflects:

- High impact, low probability
- Slow signal (financial reports lag actual conditions by months)
- Diversification is the right mitigation, not weekly score-watching

A real org would supplement this with D&B reports, Reuters monitoring, and a watch list of named distressed suppliers, not just rely on the score.

## Why Geopolitical Is Smallest

Geopolitical risk is real but mostly irrelevant week-to-week. The score uses a regional risk index as a proxy, which is admittedly crude. Real-world geopolitical risk requires named-event monitoring (sanctions, trade restrictions, conflicts) which is out of scope for this prototype.

The 10% weight prevents geopolitical from drowning out actionable signals while still penalizing concentration risk.

## Spend Adjustment

After the weighted score, the model applies a small spend-weighted adjustment (up to -5 points for $10M+ suppliers). The intent: a $10M supplier with a score of 60 deserves more attention than a $0.5M supplier with the same score.

This is controversial. Arguments against: spend should be a separate sort dimension, not bake into the risk score. Arguments for: a single risk score that accounts for impact is more actionable than two separate scores.

The compromise here (small adjustment, capped at 5 points) is defensible. In an interview, expect to be asked about this and have your reasoning ready. Either side is valid; what matters is that you've thought about it.

## Single-Source Penalty

A flat -3 points if `single_source = True`. Same reasoning: single-sourced suppliers carry concentration risk that diversified ones don't. The penalty is small because single-sourcing is a strategic decision, not a supplier-quality issue.

## Tier Thresholds

```
75-100 → GREEN
50-74  → YELLOW
0-49   → RED
```

Why these specific cutoffs:

- **75 for GREEN**: a supplier needs to be at "good" or better on most dimensions to clear this. A purely-average supplier (60 on every factor) lands at YELLOW, which is correct.
- **50 for YELLOW boundary**: below 50 means at least one dimension is severely flagged. This is the "executive escalation" threshold.
- **No GREEN for any dimension below 50**: this is enforced by the math. A supplier with one factor at 30 cannot reach 75 overall unless other factors are near 100.

In a real deployment, the thresholds would be tuned based on the actual distribution of your supplier base. If 70% of your suppliers naturally score 80+, the GREEN threshold should move up. The fixed thresholds here are illustrative.

## How to Defend This in an Interview

Anticipated questions and short answers:

**Q: Why weights, not a flat 20% each?**
A: Different factors have different actionability and different cost-of-failure. Weighting reflects which factors a PM should pay attention to first.

**Q: Why is geopolitical only 10%? China supplier concentration is huge.**
A: Geopolitical risk matters for strategy (diversification) more than for weekly review. The 10% weight ensures it shows up in scores without drowning out actionable signals. A real org would supplement with named-event monitoring.

**Q: How would you change this for an automotive customer?**
A: Quality weight goes up (40-50%), threshold for "elevated escapes" drops to 1+, financial weight stays the same. Automotive has zero-defect culture and longer product life, so quality dominates more.

**Q: How would you change this for a consumer electronics ramp?**
A: Capacity weight goes up to 30-35% near MP, financial weight stays, quality stays. Volume risk dominates ramp.

**Q: Could the AI choose these weights?**
A: No. Weights are a strategic decision that reflects org priorities. AI can help validate weights against historical data, but the weights themselves should be human-owned and version-controlled.

## Honest Limitations

1. The scoring is rule-based. Machine learning could outperform on a richer dataset (training on historical supplier outcomes), but that requires real data, real labels, and a real validation pipeline. Out of scope for a portfolio prototype.
2. The scoring is static per snapshot. A "trending worse" supplier (score 70 but degrading 5 points/quarter) is more concerning than a stable 65. Time-series scoring is in the next-iteration list.
3. The scoring treats suppliers as independent. Correlated risks (multiple suppliers affected by the same regional disruption) are not modeled.

These are intentional scope cuts.
