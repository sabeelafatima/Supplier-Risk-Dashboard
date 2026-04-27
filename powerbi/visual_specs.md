# Visual Specs: Page-by-Page Layout

This is the design spec for each page of the dashboard. Use it as a reference while building, and link to it from the README so reviewers can see your design thinking.

## Color Palette

Consistent across all pages:

- RED tier: `#dc2626`
- YELLOW tier: `#eab308`
- GREEN tier: `#16a34a`
- Neutral / borders: `#6b7280`
- Background: `#ffffff` or `#fafafa`
- Text primary: `#111827`
- Text secondary: `#6b7280`

## Typography

- Page titles: Segoe UI Semibold, 20pt
- Section headers: Segoe UI Semibold, 14pt
- Body / table: Segoe UI Regular, 11pt
- Card numbers: Segoe UI Bold, 32pt

---

## Page 1: Executive Summary

**Goal**: A PM walking into a weekly supply review can answer "what's the state of our supplier base?" in 30 seconds.

### Layout grid (1280 × 720)

```
┌─ Page Header ────────────────────────────────────────┐
│  SUPPLIER RISK OVERVIEW         Last refresh: [date] │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│  │ TOTAL  │ │ ✗ RED  │ │ ⚠ YEL │ │ ✓ GREEN │         │
│  │  100   │ │   2    │ │  33   │ │   65    │         │
│  └────────┘ └────────┘ └────────┘ └────────┘         │
│                                                      │
│  ┌─ Spend at Risk ─┐  ┌─ Key Insight Card ──┐        │
│  │  $X.XM at risk  │  │ 8 suppliers PPAP-   │        │
│  │  Y% of total    │  │ approved + escapes  │        │
│  └─────────────────┘  └─────────────────────┘        │
│                                                      │
│  ┌──── Risk Distribution by Region ─────────────┐    │
│  │                                              │    │
│  │  [Stacked Bar: region × tier]                │    │
│  │                                              │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──── Top 10 At-Risk Suppliers ────────────────┐    │
│  │                                              │    │
│  │  [Table sorted by score asc]                 │    │
│  │  Right-click → Drillthrough → Page 2         │    │
│  │                                              │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Filters (top right or side panel)
- Region (multi-select)
- Category (multi-select)
- Tier (multi-select)

### Specific tips

- The "8 suppliers PPAP-approved + escapes" card is the headline insight. Make it visually prominent.
- The Top 10 table should have minimal columns: name, region, score, tier, narrative (truncated). Drillthrough fills in the rest.

---

## Page 2: Supplier Detail (Drillthrough)

**Goal**: Everything a PM needs about one supplier on one screen.

### Layout grid

```
┌─ Page Header ────────────────────────────────────────┐
│  [Supplier Name]                  [Tier badge]       │
│  [supplier_id] | [region] | [category]               │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──── 5-Dimension Score Breakdown ──────────────┐   │
│  │                                               │   │
│  │  [Bar chart: 5 dimensions, score 0-100]       │   │
│  │  Bars colored by score (gradient red→green)   │   │
│  │                                               │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ Underlying Metrics ──────────────────────────┐   │
│  │  PPAP:        [value]   OTD:    [value]%      │   │
│  │  Escapes:     [value]   Lead:   [value]d      │   │
│  │  Capacity:    [value]   Util:   [value]%      │   │
│  │  Financial:   [value]/5 Single source: [Y/N]  │   │
│  │  Spend:       $[value]M Years partner: [val]  │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ AI Narrative ────────────────────────────────┐   │
│  │  [narrative text]                             │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ Recommended Action ──────────────────────────┐   │
│  │  [recommended_action]                         │   │
│  │  Confidence: [HIGH/MEDIUM/LOW]                │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Specific tips

- The drillthrough configuration uses `supplier_id` as the field
- Add a "Back to overview" button at the top (Power BI provides this if you set up drillthrough correctly)
- Make sure narrative wraps (don't truncate it; it's the deliverable)

---

## Page 3: Q&A / Copilot

**Goal**: Demonstrate AI-augmented exploration. This is the "wow" page for AI-Augmented PM hiring loops.

### If using Power BI Copilot

```
┌─ Page Header ────────────────────────────────────────┐
│  ASK COPILOT                                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ Suggested Questions ─────────────────────────┐   │
│  │  "Show APAC suppliers with quality escapes >2"│   │
│  │  "Which suppliers have PPAP approved but      │   │
│  │   OTD below 85%?"                             │   │
│  │  "Total annual spend at-risk"                 │   │
│  │  "Top 5 single-source suppliers in YELLOW"    │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌─ Copilot Visual ──────────────────────────────┐   │
│  │  [Interactive Copilot chat interface]         │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### If using Q&A visual (free tier)

Same layout, but use the standard Q&A visual instead of Copilot. Configure suggested questions in the Q&A setup pane.

### Specific tips

- The suggested questions matter. Pick ones that show the dashboard's depth, not generic questions.
- Demo the "PPAP approved but OTD below 85%" question first; this is the conflict-pattern question that showcases the multi-dimensional insight.

---

## Optional Page 4: About / Methodology

**Goal**: Defensibility documentation embedded in the report itself.

A simple text-heavy page with:

- The 5-factor scoring model
- Weights and rationale
- Tier thresholds
- Honest limitations
- Link to the GitHub repo

This page exists because a thoughtful reviewer (the kind you actually want to work for) will want to know the methodology before trusting the dashboard. Embedding the docs in the report shortcuts that.

---

## What "Polished" Looks Like

The difference between a portfolio dashboard that gets clicks and one that doesn't comes down to four things:

1. **Consistent color palette**: tier colors used the same way everywhere.
2. **Generous whitespace**: don't pack visuals shoulder-to-shoulder.
3. **Real-feeling labels**: "Spend at Risk USD M" not "Sum of annual_spend_usd_m".
4. **One clear "wow" moment per page**: Page 1 is the conflict-pattern card, Page 2 is the 5-dimension bar, Page 3 is the Q&A demo.

Spend the last 20% of build time on polish. It's where the multiplier on perceived quality comes from.
