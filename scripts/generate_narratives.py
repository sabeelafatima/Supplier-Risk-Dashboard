"""
AI Narrative Generator for Supplier Risk Dashboard.

Pre-computes a 2-3 sentence narrative summary per supplier, joined into
Power BI as a static column. Pre-computation is a deliberate design choice:
real-time LLM calls in a dashboard create unpredictable latency, cost
spikes, and rate-limit failures. Refreshing nightly is the right tradeoff.

Run:
    python scripts/generate_narratives.py
Outputs:
    data/supplier_narratives.csv

Falls back to a deterministic mock narrative if no API key is set, so the
dashboard demo always works for portfolio review.
"""

import csv
import json
import os
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # type: ignore

from risk_scoring import score_all_suppliers

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_PATH = DATA_DIR / "supplier_narratives.csv"


SYSTEM_PROMPT = """You are a Supply Chain Risk Analyst.

You receive structured data on a single supplier including risk scores per
dimension (quality, delivery, capacity, financial, geopolitical), the overall
tier (GREEN / YELLOW / RED), and the underlying metrics.

Your job is to generate a 2-3 sentence narrative summary that:

1. States the overall risk picture in plain language.
2. Names the specific dimensions driving the risk (cite the actual metric).
3. Recommends a concrete next action sized to the tier.

Rules:
- Do NOT invent metrics not in the input.
- Do NOT change the tier. The tier is fixed.
- Use specific numbers where they support the recommendation.
- For GREEN suppliers, be brief (1-2 sentences). No filler.
- For RED suppliers, lead with the action.

Output a single JSON object:
{
  "narrative": "2-3 sentence summary",
  "recommended_action": "one short sentence",
  "confidence": "HIGH | MEDIUM | LOW"
}

Return only the JSON. No preamble, no markdown fencing."""


def build_user_message(supplier: dict) -> str:
    return f"""Supplier: {supplier['supplier_name']} ({supplier['supplier_id']})
Category: {supplier['category']}
Region: {supplier['region']}
Tier: {supplier['tier']} (overall score {supplier['overall_score']})

Dimension scores (0-100):
- Quality: {supplier['score_quality']}
- Delivery: {supplier['score_delivery']}
- Capacity: {supplier['score_capacity']}
- Financial: {supplier['score_financial']}
- Geopolitical: {supplier['score_geopolitical']}

Underlying metrics:
- PPAP status: {supplier['ppap_status']}
- On-time delivery: {supplier['on_time_delivery_pct']}%
- Quality escapes (60d): {supplier['quality_escapes_60d']}
- Capacity confirmed: {supplier['capacity_confirmed']}
- Capacity utilization: {supplier['capacity_utilization_pct']}%
- Avg lead time: {supplier['avg_lead_time_days']} days
- Financial health: {supplier['financial_health_score']}/5
- Single source: {supplier['single_source']}
- Annual spend: ${supplier['annual_spend_usd_m']}M

Flagged dimensions: {supplier['flagged_dimensions'] or 'none'}"""


def generate_narrative_with_claude(
    supplier: dict, client, model: str = "claude-opus-4-7"
) -> dict:
    """Call Claude API for one supplier."""
    response = client.messages.create(
        model=model,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(supplier)}],
    )
    text = response.content[0].text.strip()

    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _mock_narrative(supplier)


def _mock_narrative(supplier: dict) -> dict:
    """
    Deterministic fallback narrative.

    Generates useful summaries directly from the score data without an LLM.
    This is what shows up in the dashboard when no API key is configured.
    """
    tier = supplier["tier"]
    flagged = supplier["flagged_dimensions"].split("|") if supplier["flagged_dimensions"] else []

    if tier == "RED":
        flag_str = ", ".join(flagged) if flagged else "multiple dimensions"
        narrative = (
            f"{supplier['supplier_name']} is at HIGH risk (score "
            f"{supplier['overall_score']}). Driven by weakness in {flag_str}, "
            f"with OTD at {supplier['on_time_delivery_pct']}% and "
            f"{supplier['quality_escapes_60d']} quality escapes in last 60 days."
        )
        action = "Escalate to weekly supply review; on-site visit recommended within 2 weeks."
        confidence = "HIGH"
    elif tier == "YELLOW":
        if flagged:
            flag_str = ", ".join(flagged)
            narrative = (
                f"{supplier['supplier_name']} is in CONDITIONAL status (score "
                f"{supplier['overall_score']}). Concerns in {flag_str}; "
                f"OTD {supplier['on_time_delivery_pct']}%, "
                f"{supplier['quality_escapes_60d']} escapes in 60d. "
                "Worth attention but not immediate escalation."
            )
        else:
            narrative = (
                f"{supplier['supplier_name']} is in CONDITIONAL status (score "
                f"{supplier['overall_score']}). No single dimension at red, "
                f"but several are below threshold. "
                f"OTD {supplier['on_time_delivery_pct']}%, "
                f"{supplier['quality_escapes_60d']} escapes in 60d."
            )
        action = "Monitor in monthly supply review; follow up if any dimension worsens."
        confidence = "MEDIUM"
    else:  # GREEN
        narrative = (
            f"{supplier['supplier_name']} is healthy (score "
            f"{supplier['overall_score']}). No flagged dimensions."
        )
        action = "Standard quarterly review."
        confidence = "HIGH"

    # Special case: PPAP-approved-with-quality-escapes conflict
    if (
        supplier["ppap_status"] == "Approved"
        and int(supplier["quality_escapes_60d"]) >= 3
    ):
        narrative += (
            f" NOTE: PPAP approved but {supplier['quality_escapes_60d']} "
            "quality escapes in 60 days; multi-dimensional risk that single-"
            "factor checks would miss."
        )
        action = (
            "Pull-in quality review with supplier; "
            "verify corrective action plan before next gate."
        )

    return {
        "narrative": narrative,
        "recommended_action": action,
        "confidence": confidence,
    }


def main() -> None:
    suppliers = score_all_suppliers()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_llm = api_key is not None and Anthropic is not None
    client = Anthropic(api_key=api_key) if use_llm else None

    if use_llm:
        print(f"Generating narratives via Claude API for {len(suppliers)} suppliers...")
    else:
        print(
            f"No ANTHROPIC_API_KEY set. Using deterministic mock narratives "
            f"for {len(suppliers)} suppliers."
        )

    rows = []
    for i, s in enumerate(suppliers):
        if use_llm:
            try:
                narrative = generate_narrative_with_claude(s, client)
            except Exception as e:
                print(f"  Fallback for {s['supplier_id']}: {e}")
                narrative = _mock_narrative(s)
        else:
            narrative = _mock_narrative(s)

        rows.append({
            "supplier_id": s["supplier_id"],
            "narrative": narrative["narrative"],
            "recommended_action": narrative["recommended_action"],
            "confidence": narrative["confidence"],
        })

        if (i + 1) % 25 == 0:
            print(f"  ...processed {i + 1}/{len(suppliers)}")

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["supplier_id", "narrative", "recommended_action", "confidence"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} narratives to {OUTPUT_PATH}")
    print("\nSample narratives (top 3 at-risk):")
    by_score = sorted(suppliers, key=lambda s: s["overall_score"])[:3]
    by_score_ids = {s["supplier_id"] for s in by_score}
    for row in rows:
        if row["supplier_id"] in by_score_ids:
            print(f"\n  {row['supplier_id']}")
            print(f"  Narrative: {row['narrative']}")
            print(f"  Action:    {row['recommended_action']}")


if __name__ == "__main__":
    main()
