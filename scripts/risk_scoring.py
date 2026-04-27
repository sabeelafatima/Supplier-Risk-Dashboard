"""
Risk Scoring Reference Implementation.

This is the Python version of the risk scoring model. The same logic is
implemented as DAX measures in Power BI (see powerbi/dax_measures.md).
This Python version exists to:

1. Validate the model against synthetic data before building in Power BI
2. Provide a callable function for the AI narrative generator
3. Serve as the source of truth for documentation and tests

Run:
    python scripts/risk_scoring.py
"""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# Weights are tunable. These defaults are defensible for a generic hardware
# NPI program at PVT/MP gate phases. A real org would tune per product class.
WEIGHTS = {
    "quality": 0.30,
    "delivery": 0.25,
    "capacity": 0.20,
    "financial": 0.15,
    "geopolitical": 0.10,
}

# Score thresholds for tier assignment
TIER_THRESHOLDS = {
    "GREEN": 75,
    "YELLOW": 50,
    # below 50 = RED
}


def score_quality(supplier: dict) -> float:
    """
    Score 0-100 for quality dimension.

    Weights PPAP status (60%) and quality escapes (40%).
    A supplier with PPAP approved but high escapes scores lower than naive
    PPAP-only check would suggest. This is the multi-dimensional insight.
    """
    ppap_score = {"Approved": 100, "Conditional": 60, "Pending": 30}.get(
        supplier["ppap_status"], 0
    )

    # Escapes: 0 → 100, 1 → 80, 2 → 60, 3 → 35, 4 → 15, 5+ → 5
    escapes = int(supplier["quality_escapes_60d"])
    escape_curve = [100, 80, 60, 35, 15, 5]
    escape_score = escape_curve[min(escapes, len(escape_curve) - 1)]

    return ppap_score * 0.6 + escape_score * 0.4


def score_delivery(supplier: dict) -> float:
    """Score 0-100 for delivery dimension. Mostly OTD with lead-time penalty."""
    otd = float(supplier["on_time_delivery_pct"])
    # Linear scale: OTD 95+ → 100, 80 → 50, 70 → 0
    if otd >= 95:
        otd_score = 100.0
    elif otd >= 80:
        otd_score = 50.0 + (otd - 80) / 15 * 50
    else:
        otd_score = max(0.0, (otd - 70) / 10 * 50)

    # Lead time penalty: long-lead suppliers (90+ days) get a haircut
    lead_time = int(supplier["avg_lead_time_days"])
    lead_penalty = 0
    if lead_time >= 90:
        lead_penalty = 15
    elif lead_time >= 60:
        lead_penalty = 8
    elif lead_time >= 45:
        lead_penalty = 3

    return max(0.0, otd_score - lead_penalty)


def score_capacity(supplier: dict) -> float:
    """Score 0-100 for capacity dimension."""
    confirmation = supplier["capacity_confirmed"]
    confirmation_score = {
        "Yes": 100, "Conditional": 65, "Pending": 40, "No": 10
    }.get(confirmation, 0)

    # Utilization: high utilization = less headroom = more risk
    util = float(supplier["capacity_utilization_pct"])
    if util < 70:
        util_score = 100.0
    elif util < 85:
        util_score = 80.0
    elif util < 95:
        util_score = 50.0
    else:
        util_score = 20.0

    return confirmation_score * 0.65 + util_score * 0.35


def score_financial(supplier: dict) -> float:
    """Financial health 1-5 maps directly to 0-100."""
    fh = int(supplier["financial_health_score"])
    return {1: 10, 2: 35, 3: 60, 4: 80, 5: 100}[fh]


def score_geopolitical(supplier: dict) -> float:
    """Region risk index already 0-1 scale; convert to 0-100."""
    return float(supplier["region_risk_index"]) * 100


def overall_score(supplier: dict) -> dict:
    """Compute weighted overall risk score and per-dimension breakdown."""
    dimensions = {
        "quality": score_quality(supplier),
        "delivery": score_delivery(supplier),
        "capacity": score_capacity(supplier),
        "financial": score_financial(supplier),
        "geopolitical": score_geopolitical(supplier),
    }

    weighted = sum(dimensions[k] * WEIGHTS[k] for k in dimensions)

    # Spend-weighted bump: high-spend suppliers get an attention bump
    # (a $10M supplier with score 60 deserves more focus than a $0.5M one)
    annual_spend = float(supplier["annual_spend_usd_m"])
    if annual_spend >= 5.0:
        # Reduce score (raise risk visibility) by up to 5 points based on spend
        weighted = weighted - min(5, annual_spend / 2)

    # Single source penalty
    if str(supplier.get("single_source")).lower() == "true":
        weighted -= 3

    score = max(0.0, min(100.0, weighted))

    if score >= TIER_THRESHOLDS["GREEN"]:
        tier = "GREEN"
    elif score >= TIER_THRESHOLDS["YELLOW"]:
        tier = "YELLOW"
    else:
        tier = "RED"

    return {
        "overall_score": round(score, 1),
        "tier": tier,
        "dimensions": {k: round(v, 1) for k, v in dimensions.items()},
        "flagged_dimensions": [
            k for k, v in dimensions.items() if v < 50
        ],
    }


def score_all_suppliers(input_path: Path = None, output_path: Path = None) -> list[dict]:
    """Score every supplier in the master file. Optionally write enriched CSV."""
    if input_path is None:
        input_path = DATA_DIR / "suppliers_master.csv"
    if output_path is None:
        output_path = DATA_DIR / "suppliers_scored.csv"

    with input_path.open(encoding="utf-8") as f:
        suppliers = list(csv.DictReader(f))

    enriched = []
    for s in suppliers:
        score = overall_score(s)
        enriched_row = {
            **s,
            "overall_score": score["overall_score"],
            "tier": score["tier"],
            "score_quality": score["dimensions"]["quality"],
            "score_delivery": score["dimensions"]["delivery"],
            "score_capacity": score["dimensions"]["capacity"],
            "score_financial": score["dimensions"]["financial"],
            "score_geopolitical": score["dimensions"]["geopolitical"],
            "flagged_dimensions": "|".join(score["flagged_dimensions"]),
        }
        enriched.append(enriched_row)

    if output_path:
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(enriched[0].keys()))
            writer.writeheader()
            writer.writerows(enriched)

    return enriched


def print_summary(suppliers: list[dict]) -> None:
    """Quick summary of score distribution for sanity-check."""
    tiers = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for s in suppliers:
        tiers[s["tier"]] += 1

    print(f"Total suppliers scored: {len(suppliers)}")
    print(f"Tier distribution:")
    for tier, count in tiers.items():
        print(f"  {tier}: {count} ({count/len(suppliers):.0%})")

    avg_score = sum(s["overall_score"] for s in suppliers) / len(suppliers)
    print(f"Average overall score: {avg_score:.1f}")

    # Top 5 at-risk
    at_risk = sorted(suppliers, key=lambda s: s["overall_score"])[:5]
    print(f"\nTop 5 at-risk suppliers:")
    for s in at_risk:
        print(
            f"  {s['supplier_id']} {s['supplier_name']:<28} "
            f"Score {s['overall_score']:>5} {s['tier']:<7} "
            f"flags: {s['flagged_dimensions']}"
        )


if __name__ == "__main__":
    suppliers = score_all_suppliers()
    print_summary(suppliers)
