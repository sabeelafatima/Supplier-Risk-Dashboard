# AI-Enhanced Supplier Risk Dashboard

> An interactive dashboard that scores 100 simulated suppliers across quality, delivery, and external risk signals to enable proactive escalation in hardware NPI programs.

**Status**: v1 prototype, active build  
**Author**: Sabeela Fatima  
**Stack**: HTML, JavaScript, React 18, Claude AI (narrative layer)

---

## The Problem This Solves

Supplier risk in hardware NPI is reactive by default. Procurement flags a delay, then PM scrambles for a recovery plan — by then the schedule has already slipped. The data needed to predict the slip usually exists, scattered across:

- Quality systems (incoming inspection, DPPM, audit findings)
- ERP / procurement (PO aging, on-time delivery)
- Supplier scorecards (capacity confirmation, lead time)
- External signals (financial health, geopolitical, regional exposure)

This dashboard combines those signals into a single forward-looking risk score per supplier, with AI-generated narrative summaries that explain the score and recommend an action.

The use case I built it for: a Program Manager preparing for a weekly supply review, who wants to walk in knowing which 5 suppliers need attention, why, and what to ask.

## Why AI

The risk score itself is deterministic — a weighted formula across 3 dimensions. AI is not what computes the score.

AI is used for one thing:

1. **Per-supplier narrative summary**: turns the underlying numbers into a 2–3 sentence explanation that a PM can paste into a status report or a recovery plan — covering risk assessment, key drivers, and recommended action.

The dashboard works without AI (the score, the visuals, the filters all function on their own). AI adds the narrative layer that translates numbers into stakeholder-ready language.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         SYNTHETIC DATA GENERATION (JavaScript)              │
│  - 100 suppliers across 8 regions, 12 commodity categories  │
│  - Realistic distributions for OTD, DPPM, external risk     │
│  - Intentional conflict cases (approved but failing)        │
│  - NPI program exposure flags per supplier                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼  in-memory supplier objects
┌─────────────────────────────────────────────────────────────┐
│                   RISK SCORING MODEL                        │
│  - 3-factor weighted composite (Quality, Delivery, External)│
│  - Weights user-adjustable in real time via sliders         │
│  - Tier assignment: Critical / High / Medium / Low          │
│  - Scores repaint live when weights change                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   DASHBOARD VIEWS                           │
│  View 1: Risk Leaderboard (sortable, filterable table)      │
│  View 2: Supplier Detail (drill-through with narrative)     │
│  View 3: Escalation Queue (Open → In Review → Resolved)     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              AI NARRATIVE LAYER (rule-based)                │
│  - Reads supplier risk tier + flagged dimensions            │
│  - Detects primary risk drivers (quality, delivery, ext.)   │
│  - Produces per-supplier 3-sentence narrative on click      │
│  - Assessment → Key Drivers → Recommended Action            │
└─────────────────────────────────────────────────────────────┘
```

**Key design choice**: AI narratives are generated on-click using a rule-based engine rather than a live LLM call. This keeps the dashboard fast, offline-capable, and free of API latency. The narrative logic detects which dimensions are failing and maps them to action templates — the same pattern a PM would follow manually.

## The Risk Scoring Model

Each supplier gets a composite risk score 0–100 across 3 weighted dimensions:

| Dimension | Default Weight | Source Fields |
|-----------|---------------|---------------|
| Quality Risk | 35% | quality score (inverse), DPPM |
| Delivery Risk | 35% | delivery score (inverse), OTD% |
| External Risk | 30% | external signal score, region, lead time |

Score → tier mapping:

- **65–100** → CRITICAL
- **49–64** → HIGH
- **31–48** → MEDIUM
- **0–30** → LOW

The weights default to 35 / 35 / 30 but are fully adjustable via the ⚙ Weights panel. Scores and tiers repaint live.

## Project Structure

```
Supplier-Risk-Dashboard/
├── README.md
└── index.html                  # Full self-contained dashboard
                                # Includes:
                                #   - Synthetic data generator
                                #   - Risk scoring model
                                #   - React UI (Risk Leaderboard,
                                #     Escalation Queue, Detail Panel)
                                #   - AI narrative engine
                                #   - Configurable weight sliders
```

## How to Run This

No build step required. Just open the file:

```bash
git clone https://github.com/sabeelafatima/Supplier-Risk-Dashboard.git
cd Supplier-Risk-Dashboard
open index.html
```

Or drag `index.html` into any browser. No server, no dependencies, no API key needed.

## What's in the Synthetic Dataset

100 suppliers with these realistic patterns:

- **Commodities**: PCB Assembly, ICs & Semiconductors, Memory, Connectors, Sensors, Display Modules, Power Supplies, Enclosures, Cables & Harnesses, Thermal Solutions, Passive Components, Mechanical Fasteners
- **Regions**: East Asia (40%), Southeast Asia, South Asia, Eastern Europe, Western Europe, North America, Mexico, Middle East
- **Risk mix**: ~14% Critical, ~22% High, ~40% Medium, ~24% Low at default weights
- **NPI exposure**: ~30% of suppliers tagged to active NPI programs (ARIA-X1, BOLT-NX, CORSAIR, DELTA-3, ECHO-7)
- **Escalation cases**: High and Critical suppliers have a 60% chance of open escalation
- **Spend range**: $0.2M–$12M per supplier; lead times 6–18 weeks

## Honest Limitations

- Synthetic data is modeled on industry patterns. Real procurement data has more shape and noise.
- The 3-dimension risk model is illustrative. Real orgs tune weights per product class and per gate phase.
- External risk signals are simulated as scalar values. A production version would pull from D&B, Reuters, or Bloomberg APIs.
- No time-series data in v1. Trend arrows are simulated from a 6-month quality history.

## What I'd Build Next

1. **Time-series scoring**: track supplier scores over 12+ weeks. Trending-down suppliers are the most actionable signal.
2. **BOM impact view**: "If supplier X goes down, which NPI BOM lines are at risk?"
3. **Recovery plan templates**: per risk tier, generate a starter recovery plan the PM can edit.
4. **Real data connectors**: replace synthetic data with live pulls from ERP, QMS, and D&B.

---

**Built by Sabeela Fatima** | [GitHub](https://github.com/sabeelafatima) · [LinkedIn](https://linkedin.com/in/sabeela-fatima)
