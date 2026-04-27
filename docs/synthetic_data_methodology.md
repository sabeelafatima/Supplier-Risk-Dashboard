# Synthetic Data Methodology

This document explains how the 100-supplier dataset was constructed, what real-world distributions it mimics, and what edge cases were intentionally injected.

## Design Goals

1. **Believable scale**: 100 suppliers is the right size for a mid-volume hardware product (a true semiconductor fab might track 500+, a small startup might track 30, 100 is the comfortable middle).
2. **Realistic distributions**: OTD, quality escapes, lead times all follow real-world shape.
3. **Intentional edge cases**: documented patterns that the dashboard should surface and that an interviewer can verify.
4. **Reproducible**: the script uses a fixed seed (42), so re-running produces the exact same dataset.

## Distribution Choices

### Region (50% APAC, 25% Americas, 15% EMEA, 10% Other)

Why this split: matches actual hardware-supplier reality for consumer/IoT products. APAC concentration reflects PCB/PCBA, semiconductor, and many component categories being dominated by Asian suppliers. A real fab might be 70%+ APAC; 50% is the conservative middle.

### Category (10 categories, even distribution)

Why this split: lets the dashboard demonstrate filtering by category without any category being too sparse. Real BOMs have power-law distribution (lots of passives, few semis), but for a dashboard demo even distribution gives more interesting filter behavior.

### PPAP Status (78% Approved, 12% Conditional, 10% Pending)

Why this split: at PVT/MP phase of an NPI, most strategic suppliers should be PPAP-approved. The 12% conditional reflects new suppliers in qualification, the 10% pending reflects late-add or low-priority suppliers.

### OTD (Gaussian centered at 91-94%, clipped at 60-99.9%)

Why this distribution: OTD is bounded above (you can't ship more than 100% on time) and skews right. The Gaussian-with-clipping is a reasonable approximation for a portfolio of suppliers. Real OTD data often has a fat tail of struggling suppliers; the synthetic version has 5-8% in the 75-85% range, which feels right.

### Quality Escapes (heavy weight on 0-1, rare 4+)

Why this distribution: in a healthy supplier base, most suppliers have zero escapes in any given 60-day window. The right tail (3+ escapes) is where the action is. The intentional injection of conflict-pattern suppliers ensures the dashboard demonstrates the multi-dimensional risk insight.

### Financial Health (weighted 1-5 with 3-4 dominant)

Why this distribution: most suppliers in a working portfolio are financially OK (3-4). A small portion are in distress (1-2). The 1/5 financial-distress cases are intentionally injected.

### Lead Time (category-specific Gaussian)

Why this distribution: semiconductor and memory have notoriously long lead times (60-80 days), passives are commodity and short (2-3 weeks). The category-specific base + noise produces realistic shape.

### Annual Spend (log-normal, capped at $50M)

Why this distribution: spend is heavily right-skewed in real supplier data. Most suppliers are <$1M/year, a few are $5-30M. Log-normal captures this.

## Intentional Edge Cases

These are the cases that make the dashboard worth using. An interviewer should be able to find each one by sorting or filtering the data.

### 1. PPAP Approved + Quality Escapes (the headline conflict)

**Suppliers affected**: indices 7, 23, 41, 56, 68, 73, 84, 91 (8 suppliers)

**Pattern**: PPAP status forced to "Approved", quality escapes forced to 3-5, OTD reduced to 75-84%.

**Why this matters**: this is the case a single-factor filter (just PPAP, just quality) would miss. The multi-dimensional risk score correctly flags these. In an interview, sort by score ascending and these should appear in the top 15 RED/YELLOW.

### 2. Financial Distress (3 suppliers)

**Suppliers affected**: indices 12, 47, 88

**Pattern**: financial_health_score forced to 1.

**Why this matters**: tests the financial dimension. Even a supplier with good quality and OTD will tier down with severe financial distress.

### 3. Acute Capacity Risk (4 suppliers)

**Suppliers affected**: indices 5, 33, 62, 79

**Pattern**: capacity_confirmed = "No", utilization 85-95%.

**Why this matters**: tests the capacity dimension as a primary driver. A supplier that's quality-good and delivery-good but capacity-stressed should still flag.

### 4. The Headline Supplier (MFG-073 "EastBay Magnetics")

**Pattern**: forced into the conflict bucket with high spend ($8.4M), single source, sensors category. Designed to be the supplier you point to in interviews.

**Why this matters**: gives you a concrete example to walk through. "Here's a supplier in our top 10 at-risk; let me show you why the model flagged it..."

## What This Dataset Does NOT Capture

1. **Time-series data**: every metric is a point-in-time snapshot. Real risk-monitoring would track 12 weeks of history.
2. **Cross-supplier correlation**: regional disruptions affect multiple suppliers simultaneously. Not modeled.
3. **Product-specific impact**: a supplier's score should depend on which BOM lines they support. Modeled implicitly via spend, not explicitly.
4. **Supplier scorecards from real systems**: real PPAP packages contain Cpk values, FAIs, dimensional data. This dataset stops at the status flag.

These are intentional scope cuts. The prototype demonstrates the pattern, not a production model.

## Reproducibility

Random seed: `42` (set in `generate_suppliers.py`). Re-running the script produces an identical dataset. This is important for interview defensibility: every claim about the data can be re-verified.

If you want a different dataset (different seed, different size, different distributions), edit the script. Don't claim "the model generates a realistic dataset" without being able to point to the script.
