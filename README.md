# AI-Enhanced Supplier Risk Dashboard

> A Power BI dashboard with AI-augmented narrative summaries that scores 100 suppliers across quality, delivery, and external risk signals to enable proactive escalation in hardware NPI programs.

**Status**: v1 prototype, active build
**Author**: Sabeela \[Last Name]
**Stack**: Power BI Desktop, Power BI Copilot (or Q\&A visual), Python (data generation), Anthropic Claude API (narrative layer, optional)

\---

## The Problem This Solves

Supplier risk in hardware NPI is reactive by default. Procurement flags a delay, then PM scrambles for a recovery plan, by then the schedule has already slipped. The data needed to predict the slip usually exists, scattered across:

* Quality systems (incoming inspection, escapes, audit findings)
* ERP / procurement (PO aging, on-time delivery, fill rate)
* Supplier scorecards (PPAP status, capacity confirmation)
* External signals (financial health, geopolitical, news)

This dashboard combines those signals into a single forward-looking risk score per supplier, with AI-generated narrative summaries that explain the score and recommend an action.

The use case I built it for: a Program Manager preparing for a weekly supply review, who wants to walk in knowing which 5 suppliers need attention, why, and what to ask.

## Why AI

The risk score itself is deterministic - a weighted formula across 5 factors. AI is not what computes the score.

AI is used for two things:

1. **Per-supplier narrative summary**: turns the underlying numbers into a 2-3 sentence explanation that a PM can paste into a status report or a recovery plan.
2. **Natural-language Q\&A**: lets a PM ask "show me APAC suppliers with PPAP overdue and OTD under 90%" without writing a DAX measure or filter.

The dashboard works without AI (the score, the visuals, the filters all function on their own). AI adds the narrative layer that translates numbers into stakeholder-ready language.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            SYNTHETIC DATA GENERATION (Python)               │
│  scripts/generate\_suppliers.py                              │
│  - 100 suppliers across 4 regions, 8 categories             │
│  - Realistic distributions for OTD, quality, PPAP           │
│  - Intentional conflict cases (approved but failing)        │
│  - External risk signals (financial, geopolitical)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼  data/suppliers\_master.csv
┌─────────────────────────────────────────────────────────────┐
│                    POWER BI MODEL                           │
│  - suppliers\_master (fact table)                            │
│  - dim\_region, dim\_category, dim\_risk\_tier                  │
│  - DAX measures for risk scoring (5-factor weighted)        │
│  - Calculated columns for tier (Green/Yellow/Red)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   DASHBOARD VIEWS                           │
│  Page 1: Executive Summary (KPIs + risk distribution map)   │
│  Page 2: Supplier Detail (drill-through with narrative)     │
│  Page 3: Risk Trends (time-series view)                     │
│  Page 4: Q\&A (Copilot or Q\&A visual)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         AI NARRATIVE LAYER (Python pre-compute)             │
│  scripts/generate\_narratives.py                             │
│  - Reads supplier risk tier + flagged dimensions            │
│  - Calls Claude API to produce per-supplier summary         │
│  - Falls back to deterministic mock if no API key           │
│  - Outputs: data/supplier\_narratives.csv                    │
│  - Joined into Power BI as a related table                  │
└─────────────────────────────────────────────────────────────┘
```

**Key design choice**: AI narratives are pre-computed in a Python script and joined into Power BI as a static column, not generated on-click. This is intentional. Real-time LLM calls in a dashboard create unpredictable latency, cost spikes, and rate-limit failures. Pre-computation means the dashboard is fast and reliable, narratives refresh on a schedule (daily / weekly) rather than per-interaction.

## The Risk Scoring Model

Each supplier gets a score 0-100 across 5 weighted factors:

|Factor|Weight|Source|
|-|-|-|
|Quality (escapes, PPAP)|30%|quality\_escapes\_60d, ppap\_status|
|Delivery (OTD, lead time)|25%|on\_time\_delivery\_pct, avg\_lead\_time\_days|
|Capacity (confirmation, utilization)|20%|capacity\_confirmed, capacity\_utilization\_pct|
|Financial health|15%|financial\_health\_score (proxy: 1-5 scale)|
|Geopolitical / region|10%|region risk index|

Score → tier mapping:

* 75-100 → GREEN
* 50-74 → YELLOW
* 0-49 → RED

The weights are defensible but not sacred. A real org would tune them per product class and per gate phase. The methodology doc explains the rationale; in interviews you should be able to argue any weight.

See `docs/risk\_scoring\_methodology.md` for the full derivation.

## Project Structure

```
supplier-risk-dashboard/
├── README.md
├── data/
│   ├── suppliers\_master.csv         # 100-supplier dataset
│   └── supplier\_narratives.csv      # AI-generated narratives
├── scripts/
│   ├── generate\_suppliers.py        # Synthetic data generator
│   ├── generate\_narratives.py       # AI narrative pre-compute
│   └── risk\_scoring.py              # Reference implementation in Python
├── powerbi/
│   ├── BUILD\_INSTRUCTIONS.md        # Step-by-step Power BI build
│   ├── dax\_measures.md              # All DAX measures with explanations
│   └── visual\_specs.md              # Page-by-page visual layout
└── docs/
    ├── risk\_scoring\_methodology.md  # Why these weights, how to defend them
    ├── synthetic\_data\_methodology.md
    ├── failed\_approaches.md
    └── narrative\_prompt\_design.md
```

## How to Run This

### Step 1: Generate the synthetic data

```bash
cd supplier-risk-dashboard
pip install -r requirements.txt
python scripts/generate\_suppliers.py
# Outputs: data/suppliers\_master.csv
```

### Step 2: Generate AI narratives (optional)

```bash
export ANTHROPIC\_API\_KEY="your\_key\_here"   # optional; falls back to mock
python scripts/generate\_narratives.py
# Outputs: data/supplier\_narratives.csv
```

### Step 3: Build the Power BI report

Open Power BI Desktop and follow `powerbi/BUILD\_INSTRUCTIONS.md`. Estimated build time: 60-90 minutes if you're comfortable with Power BI.

### Step 4: Publish

Use Power BI's free "Publish to Web" feature for the demo link. Note: this makes the report public, which is fine for synthetic data but never use this with real data.

## Sample View: Executive Summary Page

```
┌──────────────────────────────────────────────────────────────┐
│  SUPPLIER RISK OVERVIEW          Last refreshed: 2025-10-19  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   Total Suppliers: 100    🔴 RED: 12    🟡 YELLOW: 28        │
│   Avg Risk Score: 71              🟢 GREEN: 60               │
│                                                              │
│   ┌─────────── Risk Distribution by Region ──────────────┐   │
│   │ APAC      ████████████████ 40% (16 RED)              │   │
│   │ Americas  ████████ 20% (3 RED)                       │   │
│   │ EMEA      ██████ 15% (1 RED)                         │   │
│   │ Other     ██████████ 25% (8 RED)                     │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                              │
│   TOP 5 AT-RISK SUPPLIERS (click for narrative)             │
│   ┌────────────────────────────────────────────────────────┐ │
│   │ MFG-073 EastBay Magnetics    Score 31 🔴              │ │
│   │ "PPAP approved but 4 quality escapes in 60d.          │ │
│   │  OTD 78%, below threshold for PVT gate suppliers.     │ │
│   │  Recommend on-site quality review this week."         │ │
│   └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## What's in the Synthetic Dataset

100 suppliers with these realistic patterns:

* **Categories**: PCBA, Semiconductors, Memory, Connectors, Sensors, Display, Battery, Mechanical, Passives, Packaging
* **Regions**: APAC (50%), Americas (25%), EMEA (15%), Other (10%) - reflects hardware reality
* **Mix of risk tiers**: \~12% RED, \~28% YELLOW, \~60% GREEN at baseline
* **Intentional conflict cases**: 8 suppliers with approved PPAP but elevated quality escapes (the headline pattern)
* **Long-tail risk**: 3 suppliers with financial health 1/5 to test the financial dimension
* **Single-source flags**: \~22 suppliers marked single\_source=True for capacity risk modeling

See `docs/synthetic\_data\_methodology.md` for the full data design rationale.

## Honest Limitations

* Synthetic data is modeled on industry patterns. Real procurement data has more shape and noise.
* The 5-factor risk model is illustrative. Real orgs tune weights per product class and per gate phase. I picked defensible defaults.
* External risk signals (financial, geopolitical) are simulated as scalar values. A production version would pull from D\&B, Reuters, Bloomberg APIs.
* Power BI Copilot availability varies by tenant license. The dashboard works without it (Q\&A visual is the fallback).
* AI narratives are pre-computed nightly, not real-time. This is a feature, not a limitation, but it means narrative latency to a real-world supplier event is up to 24h.

## What I'd Build Next

1. **Time-series view**: track supplier scores over the last 12 weeks. Trending-down suppliers are often the most actionable signal.
2. **What-if simulator**: "If supplier X went down for 4 weeks, which BOM lines are at risk?" This is the kind of view that makes a director say "send her to my hiring loop."
3. **Recovery plan templates**: per risk tier, generate a starter recovery plan the PM can edit.

These are deferred because the prototype is demonstrating the pattern, not shipping a production tool.

\---

**Built by Sabeela \[Last Name]** | [LinkedIn](https://linkedin.com/in/...) | [Portfolio](https://...)

