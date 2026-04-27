# DAX Measures Reference

Full set of DAX measures used in the dashboard. Each one includes the formula and a one-sentence rationale you should be able to explain in an interview.

## Tier Counts

```DAX
Total Suppliers = COUNTROWS(suppliers_master)
```
Why: simple count of rows. Used in the top-left KPI card.

```DAX
Red Suppliers =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[tier] = "RED"
)
```

```DAX
Yellow Suppliers =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[tier] = "YELLOW"
)
```

```DAX
Green Suppliers =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[tier] = "GREEN"
)
```

## Score Aggregates

```DAX
Avg Risk Score = AVERAGE(suppliers_master[overall_score])
```

```DAX
Avg Score by Region =
AVERAGEX(
    VALUES(suppliers_master[region]),
    CALCULATE(AVERAGE(suppliers_master[overall_score]))
)
```

## Spend at Risk

This is the measure a Director-level reviewer will care about. Total dollar exposure of RED-tier suppliers.

```DAX
Spend at Risk USD M =
CALCULATE(
    SUM(suppliers_master[annual_spend_usd_m]),
    suppliers_master[tier] = "RED"
)
```

```DAX
Spend at Conditional USD M =
CALCULATE(
    SUM(suppliers_master[annual_spend_usd_m]),
    suppliers_master[tier] = "YELLOW"
)
```

```DAX
% Spend at Risk =
DIVIDE(
    [Spend at Risk USD M],
    SUM(suppliers_master[annual_spend_usd_m]),
    0
)
```

## Conflict Detection

The headline measure: how many suppliers are PPAP-approved but have elevated quality escapes? This is the multi-dimensional pattern that single-factor checks miss.

```DAX
PPAP Approved With Escapes =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[ppap_status] = "Approved",
    suppliers_master[quality_escapes_60d] >= 3
)
```

In the dashboard, surface this number on Page 1. A Director seeing "8 suppliers PPAP-approved but failing quality" will instantly understand the value of the multi-dimensional model.

## Single Source Risk

```DAX
Single Source Suppliers =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[single_source] = TRUE()
)
```

```DAX
Single Source At Risk =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[single_source] = TRUE(),
    suppliers_master[tier] IN { "RED", "YELLOW" }
)
```

## Region Drill

```DAX
APAC Suppliers At Risk =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[region] = "APAC",
    suppliers_master[tier] = "RED"
)
```

Generalize this pattern across regions for the regional risk distribution chart.

## Capacity Stress

```DAX
Capacity Not Confirmed =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[capacity_confirmed] IN { "No", "Pending" }
)
```

```DAX
High Utilization Suppliers =
CALCULATE(
    COUNTROWS(suppliers_master),
    suppliers_master[capacity_utilization_pct] >= 90
)
```

## Tier Color (for conditional formatting)

If you want to use the tier as a color directly:

```DAX
Tier Color =
SWITCH(
    SELECTEDVALUE(suppliers_master[tier]),
    "RED", "#dc2626",
    "YELLOW", "#eab308",
    "GREEN", "#16a34a",
    "#6b7280"
)
```

Use this in conditional formatting → Format by → Field value → pick this measure.

## Derived Risk Score (Power BI native)

If you want to recompute the score in Power BI rather than relying on the Python pre-compute, here is the equivalent:

```DAX
PBI Overall Score =
VAR Quality =
    SWITCH(
        suppliers_master[ppap_status],
        "Approved", 60,
        "Conditional", 36,
        "Pending", 18,
        0
    )
    + 0.4 * SWITCH(
        TRUE(),
        suppliers_master[quality_escapes_60d] = 0, 100,
        suppliers_master[quality_escapes_60d] = 1, 80,
        suppliers_master[quality_escapes_60d] = 2, 60,
        suppliers_master[quality_escapes_60d] = 3, 35,
        suppliers_master[quality_escapes_60d] = 4, 15,
        5
    )
VAR Delivery =
    SWITCH(
        TRUE(),
        suppliers_master[on_time_delivery_pct] >= 95, 100,
        suppliers_master[on_time_delivery_pct] >= 80,
            50 + (suppliers_master[on_time_delivery_pct] - 80) / 15 * 50,
        MAX(0, (suppliers_master[on_time_delivery_pct] - 70) / 10 * 50)
    )
RETURN
    Quality * 0.30 + Delivery * 0.25 + 50  -- abbreviated
```

The full PBI version is verbose. The Python pre-compute is the recommended path. Keep the PBI version as a reference for an interviewer who asks "could you do this all in Power BI?"

## How to Defend These in an Interview

Pick any measure above. Be ready to answer:

1. **What does this measure tell a PM?**
2. **How would you tune it for a different product class?**
3. **What's the failure mode if the underlying data is wrong?**

For example, `PPAP Approved With Escapes`:
1. Identifies suppliers passing the formal qualification gate but failing in real production. The exact case naive scorecards miss.
2. The threshold of `>= 3 escapes` is tunable. For automotive (zero-defect culture) it might be `>= 1`. For consumer electronics it's `>= 3-5`.
3. Failure mode: if the quality system has lag (escapes not yet logged), this measure under-reports. Mitigation is a freshness check on the quality data feed.
