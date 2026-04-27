"""
Synthetic Supplier Data Generator.

Generates a realistic 100-supplier dataset for the AI-Enhanced Supplier Risk
Dashboard. Designed so that every row is defensible: distributions match
industry patterns and intentional edge cases are documented in the methodology.

Run:
    python scripts/generate_suppliers.py
Outputs:
    data/suppliers_master.csv
"""

import csv
import random
from pathlib import Path

# Seed makes the dataset reproducible. Important for interview defensibility:
# you can re-run and get the exact same suppliers.
random.seed(42)

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = DATA_DIR / "suppliers_master.csv"


# Realistic distribution: APAC dominant for hardware (matches actual industry)
REGION_DISTRIBUTION = [
    ("APAC", 0.50),
    ("Americas", 0.25),
    ("EMEA", 0.15),
    ("Other", 0.10),
]

# Region risk index (lower = higher risk; geopolitical proxy)
REGION_RISK = {
    "APAC": 0.75,
    "Americas": 0.95,
    "EMEA": 0.90,
    "Other": 0.65,
}

CATEGORIES = [
    "PCBA", "Semiconductors", "Memory", "Connectors", "Sensors",
    "Display", "Battery", "Mechanical", "Passives", "Packaging",
]

# Realistic supplier name fragments for synthetic but plausible names
NAME_PREFIXES = [
    "Pacific", "Atlas", "Volta", "Nexus", "Memex", "Sensorium", "EastBay",
    "Precision", "DisplayWorks", "PowerCell", "FormFlex", "LabelPrint",
    "BoxCraft", "Silicon", "Wireless", "Generic", "Photon", "Ferro",
    "Crystal", "Quantum", "Anchor", "Vertex", "Helix", "Onyx", "Tessera",
]
NAME_SUFFIXES = [
    "Solutions", "Industries", "Components", "Tech", "Corp", "Manufacturing",
    "Systems", "Co", "Group", "Ltd", "Inc", "Partners", "Works",
]


def generate_name(idx: int) -> str:
    """Stable supplier name generation."""
    prefix = NAME_PREFIXES[idx % len(NAME_PREFIXES)]
    suffix = NAME_SUFFIXES[(idx * 3) % len(NAME_SUFFIXES)]
    return f"{prefix} {suffix}"


def pick_region() -> str:
    r = random.random()
    cumulative = 0.0
    for region, weight in REGION_DISTRIBUTION:
        cumulative += weight
        if r <= cumulative:
            return region
    return "Other"


def generate_supplier(idx: int) -> dict:
    """Generate a single synthetic supplier row."""
    region = pick_region()
    category = random.choice(CATEGORIES)
    relationship_years = random.choices(
        [1, 2, 3, 5, 7, 10],
        weights=[10, 15, 20, 25, 20, 10],
    )[0]

    # Most suppliers PPAP-approved, some pending or conditional
    ppap_status = random.choices(
        ["Approved", "Conditional", "Pending"],
        weights=[78, 12, 10],
    )[0]

    # On-time delivery: most are healthy, some struggling
    if relationship_years >= 5:
        otd = round(random.gauss(94.0, 4.0), 1)
    else:
        otd = round(random.gauss(88.0, 6.5), 1)
    otd = max(60.0, min(99.9, otd))

    # Quality escapes: most 0-1, some 2-3, rare 4+
    quality_escapes = random.choices(
        [0, 1, 2, 3, 4, 5],
        weights=[55, 25, 10, 5, 3, 2],
    )[0]

    # Capacity confirmation
    capacity_confirmed = random.choices(
        ["Yes", "Conditional", "No", "Pending"],
        weights=[70, 15, 5, 10],
    )[0]
    capacity_utilization = round(random.uniform(45, 92), 1)

    # Lead time varies by category
    base_lead = {
        "Semiconductors": 70, "Memory": 45, "Display": 50, "Battery": 42,
        "PCBA": 28, "Connectors": 25, "Sensors": 30, "Mechanical": 25,
        "Passives": 15, "Packaging": 28,
    }
    avg_lead_time = max(7, int(random.gauss(base_lead[category], 8)))

    # Financial health 1-5 (5 = strongest)
    financial_health = random.choices([1, 2, 3, 4, 5], weights=[3, 7, 25, 40, 25])[0]

    # Single source: ~22% of suppliers
    single_source = random.random() < 0.22

    # Annual spend in USD millions, log-normal-ish distribution
    annual_spend_m = round(random.lognormvariate(1.2, 1.0), 2)
    annual_spend_m = min(annual_spend_m, 50.0)

    return {
        "supplier_id": f"MFG-{idx:03d}",
        "supplier_name": generate_name(idx),
        "region": region,
        "category": category,
        "ppap_status": ppap_status,
        "on_time_delivery_pct": otd,
        "quality_escapes_60d": quality_escapes,
        "capacity_confirmed": capacity_confirmed,
        "capacity_utilization_pct": capacity_utilization,
        "avg_lead_time_days": avg_lead_time,
        "financial_health_score": financial_health,
        "region_risk_index": REGION_RISK[region],
        "single_source": single_source,
        "relationship_years": relationship_years,
        "annual_spend_usd_m": annual_spend_m,
    }


def inject_intentional_conflicts(suppliers: list[dict]) -> None:
    """
    Inject specific edge cases that make the dashboard worth using.

    These are the cases that an interviewer should be able to find when they
    sort by risk score. They are documented in synthetic_data_methodology.md.
    """
    # Pick 8 suppliers and force the "PPAP approved + elevated quality escapes" conflict.
    # This is the headline pattern: a naive PPAP-only filter would mark these as ready,
    # the multi-dimensional risk score correctly flags them.
    conflict_indices = [7, 23, 41, 56, 68, 73, 84, 91]
    for idx in conflict_indices:
        suppliers[idx]["ppap_status"] = "Approved"
        suppliers[idx]["quality_escapes_60d"] = random.choice([3, 4, 5])
        suppliers[idx]["on_time_delivery_pct"] = round(random.uniform(75.0, 84.0), 1)

    # 3 suppliers with financial health 1/5 to test the financial dimension
    financial_distress_indices = [12, 47, 88]
    for idx in financial_distress_indices:
        suppliers[idx]["financial_health_score"] = 1

    # 4 suppliers with capacity_confirmed=No (acute capacity risk)
    capacity_risk_indices = [5, 33, 62, 79]
    for idx in capacity_risk_indices:
        suppliers[idx]["capacity_confirmed"] = "No"
        suppliers[idx]["capacity_utilization_pct"] = round(
            random.uniform(85, 95), 1
        )

    # Make supplier 73 the headline "everything wrong" example - high spend,
    # single source, conflict pattern, capacity stress. This is the supplier
    # that should rank #1 most-at-risk.
    suppliers[73]["supplier_name"] = "EastBay Magnetics"
    suppliers[73]["category"] = "Sensors"
    suppliers[73]["region"] = "APAC"
    suppliers[73]["region_risk_index"] = REGION_RISK["APAC"]
    suppliers[73]["ppap_status"] = "Approved"
    suppliers[73]["quality_escapes_60d"] = 4
    suppliers[73]["on_time_delivery_pct"] = 78.5
    suppliers[73]["single_source"] = True
    suppliers[73]["financial_health_score"] = 3
    suppliers[73]["annual_spend_usd_m"] = 8.4
    suppliers[73]["capacity_utilization_pct"] = 88.0


def main() -> None:
    suppliers = [generate_supplier(i) for i in range(100)]
    inject_intentional_conflicts(suppliers)

    fieldnames = list(suppliers[0].keys())
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(suppliers)

    print(f"Wrote {len(suppliers)} suppliers to {OUTPUT_PATH}")

    # Summary statistics for sanity check
    by_region: dict[str, int] = {}
    by_ppap: dict[str, int] = {}
    for s in suppliers:
        by_region[s["region"]] = by_region.get(s["region"], 0) + 1
        by_ppap[s["ppap_status"]] = by_ppap.get(s["ppap_status"], 0) + 1
    print(f"By region: {by_region}")
    print(f"By PPAP status: {by_ppap}")
    print(
        f"Avg OTD: {sum(s['on_time_delivery_pct'] for s in suppliers)/len(suppliers):.1f}%"
    )


if __name__ == "__main__":
    main()
