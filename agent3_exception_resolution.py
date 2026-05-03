from dataclasses import dataclass
import random
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# ── Seed: reproducible per calendar day ───────────────────────────────────────
seed = int(datetime.now().strftime("%Y%m%d"))
rng = random.Random(seed)


# ── Input dataclass ────────────────────────────────────────────────────────────
@dataclass
class Shipment:
    shipment_id: str
    courier: str
    country: str
    exception_type: str
    hours_left: int
    order_value_eur: float
    parcel_locker_available: bool
    pudo_available: bool
    express_available: bool


# ── Lookup tables (scoring only — no inline arithmetic) ────────────────────────
SLA_SCORE = {
    "parcel_locker":      {"LOW": 8, "MEDIUM": 7, "HIGH": 4},
    "pudo":               {"LOW": 8, "MEDIUM": 7, "HIGH": 4},
    "standard_reattempt": {"LOW": 6, "MEDIUM": 3, "HIGH": 1},
    "express_reship":     {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
    "compensation":       {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
}

COST_SCORE = {
    "parcel_locker":      10,
    "pudo":               10,
    "standard_reattempt":  8,
    "express_reship":      3,
    "compensation":        1,
}

CX_SCORE = {
    "express_reship":      9,
    "compensation":        8,
    "parcel_locker":       5,
    "pudo":                5,
    "standard_reattempt":  4,
}

OPTION_COST = {
    "parcel_locker":      1.50,
    "pudo":               1.50,
    "standard_reattempt": 2.50,
    "express_reship":    20.00,
    # "compensation": dynamic — equals order_value_eur
}

OPTION_LABEL = {
    "parcel_locker":      "Parcel Locker Reroute",
    "pudo":               "PUDO Point Reroute",
    "standard_reattempt": "Standard Re-attempt",
    "express_reship":     "Express Re-ship",
    "compensation":       "Proactive Compensation",
}


# ── Shipment generator — minimum-rules-compliant ──────────────────────────────
def generate_shipments() -> list:
    couriers   = ["DHL", "PostNL", "DPD", "Zipovva Exxpress"]
    countries  = ["Germany", "France", "Netherlands"]
    exceptions = ["failed_attempt", "customer_absent", "address_error"]

    # Urgency pool: exactly 2 HIGH, 2 LOW, 6 MEDIUM
    hours_pool = (
        [rng.randint(4, 11)  for _ in range(2)]   # HIGH  (< 12)
        + [rng.randint(49, 96) for _ in range(2)] # LOW   (> 48)
        + [rng.randint(12, 48) for _ in range(6)] # MEDIUM (12–48)
    )
    rng.shuffle(hours_pool)

    # Exception pool: 1 guaranteed address_error, 9 random
    exc_pool = ["address_error"] + [rng.choice(exceptions) for _ in range(9)]
    rng.shuffle(exc_pool)

    # Courier pool: all 4 couriers guaranteed, 6 extra random
    courier_pool = couriers[:] + [rng.choice(couriers) for _ in range(6)]
    rng.shuffle(courier_pool)

    # Country pool: all 3 countries guaranteed, 7 extra random
    country_pool = countries[:] + [rng.choice(countries) for _ in range(7)]
    rng.shuffle(country_pool)

    shipments = []
    for i in range(10):
        order_value = round(rng.uniform(25.0, 250.0), 2)
        shipments.append(Shipment(
            shipment_id=f"SHP-{1001 + i}",
            courier=courier_pool[i],
            country=country_pool[i],
            exception_type=exc_pool[i],
            hours_left=hours_pool[i],
            order_value_eur=order_value,
            parcel_locker_available=rng.choice([True, False]),
            pudo_available=rng.choice([True, False]),
            express_available=rng.choice([True, False]),
        ))

    # Guarantee at least 1 order_value > €150
    if not any(s.order_value_eur > 150 for s in shipments):
        idx = rng.randint(0, 9)
        s = shipments[idx]
        shipments[idx] = Shipment(
            shipment_id=s.shipment_id,
            courier=s.courier,
            country=s.country,
            exception_type=s.exception_type,
            hours_left=s.hours_left,
            order_value_eur=round(rng.uniform(151.0, 250.0), 2),
            parcel_locker_available=s.parcel_locker_available,
            pudo_available=s.pudo_available,
            express_available=s.express_available,
        )

    return shipments


# ── Urgency classifier ─────────────────────────────────────────────────────────
def classify_urgency(hours_left: int) -> str:
    if hours_left < 12:
        return "HIGH"
    if hours_left <= 48:
        return "MEDIUM"
    return "LOW"


# ── Available options ──────────────────────────────────────────────────────────
def get_available_options(s: Shipment) -> list:
    options = ["standard_reattempt"]

    if s.parcel_locker_available:
        options.append("parcel_locker")

    if s.pudo_available and not s.parcel_locker_available:
        options.append("pudo")

    if s.express_available:
        options.append("express_reship")

    # Compensation: high-value order OR no premium option exists
    only_standard = len(options) == 1
    if s.order_value_eur > 150 or only_standard:
        options.append("compensation")

    return options


# ── Composite scorer ───────────────────────────────────────────────────────────
def score_option(option: str, urgency: str, order_value_eur: float) -> dict:
    sla        = SLA_SCORE[option][urgency]
    cost_score = COST_SCORE[option]
    cx         = CX_SCORE[option]
    composite  = round(sla * 0.40 + cost_score * 0.35 + cx * 0.25, 2)
    cost_amount = OPTION_COST.get(option, order_value_eur)  # compensation = order value
    return {
        "option":      option,
        "label":       OPTION_LABEL[option],
        "sla":         sla,
        "cost_score":  cost_score,
        "cx":          cx,
        "composite":   composite,
        "cost_amount": cost_amount,
    }


# ── Recommendation selector ────────────────────────────────────────────────────
def select_recommendation(scored: list) -> dict:
    ranked = sorted(scored, key=lambda x: x["composite"], reverse=True)
    top = ranked[0]
    # Tiebreaker: parcel_locker always beats pudo on equal score
    if len(ranked) >= 2 and top["composite"] == ranked[1]["composite"]:
        if {top["option"], ranked[1]["option"]} == {"parcel_locker", "pudo"}:
            top = next(o for o in ranked if o["option"] == "parcel_locker")
    return top


# ── Action router ──────────────────────────────────────────────────────────────
def determine_action(s: Shipment, recommended: dict) -> str:
    if (
        recommended["cost_amount"] > 3.00
        or s.order_value_eur > 150
        or s.hours_left <= 12
        or s.exception_type == "address_error"
    ):
        return "ESCALATE TO DISPATCH CONTROLLER"
    return "AUTO-EXECUTE"


# ── Block formatter ────────────────────────────────────────────────────────────
DIVIDER = "─" * 49


def format_block(s: Shipment, urgency: str, scored: list,
                 recommended: dict, action: str) -> str:
    lines = [
        f"SHIPMENT: {s.shipment_id} | {s.courier} | {s.country}",
        f"EXCEPTION: {s.exception_type} | URGENCY: {urgency}",
        f"HOURS LEFT: {s.hours_left}h | ORDER: €{s.order_value_eur:.2f}",
        DIVIDER,
        f"{'OPTION':<25} {'SLA':>3} {'COST':>5} {'CX':>3} {'COMPOSITE':>9}",
    ]

    # Recommended first, then descending composite
    display = sorted(
        scored,
        key=lambda x: (x["option"] != recommended["option"], -x["composite"])
    )
    for opt in display:
        marker     = " ✓" if opt["option"] == recommended["option"] else "  "
        label_col  = f"{opt['label']}{marker}"
        lines.append(
            f"{label_col:<25} {opt['sla']:>3} {opt['cost_score']:>5}"
            f" {opt['cx']:>3} {opt['composite']:>9.2f}"
        )

    sub_label = "Action" if action == "AUTO-EXECUTE" else "Recommended"
    lines += [
        DIVIDER,
        f"DECISION: {action}",
        f"  → {sub_label}: {recommended['label']} | Cost: €{recommended['cost_amount']:.2f}",
    ]
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    run_date  = datetime.now().strftime("%Y-%m-%d")
    shipments = generate_shipments()
    results   = []

    for s in shipments:
        urgency     = classify_urgency(s.hours_left)
        options     = get_available_options(s)
        scored      = [score_option(opt, urgency, s.order_value_eur) for opt in options]
        recommended = select_recommendation(scored)
        action      = determine_action(s, recommended)
        block       = format_block(s, urgency, scored, recommended, action)
        results.append({
            "shipment":    s,
            "urgency":     urgency,
            "scored":      scored,
            "recommended": recommended,
            "action":      action,
            "block":       block,
        })

    # Summary stats
    total          = len(results)
    auto_count     = sum(1 for r in results if r["action"] == "AUTO-EXECUTE")
    escalate_count = total - auto_count
    avg_composite  = round(
        sum(r["recommended"]["composite"] for r in results) / total, 2
    )

    # ── Console output ─────────────────────────────────────────────────────────
    banner = f"AGENT 3 — EXCEPTION RESOLUTION  |  Run: {run_date}  |  Seed: {seed}"
    print()
    print(banner)
    print("=" * len(banner))
    print(
        f"SUMMARY  Total: {total}  |  AUTO-EXECUTE: {auto_count}"
        f"  |  ESCALATE: {escalate_count}  |  Avg Score: {avg_composite}"
    )
    print("=" * len(banner))
    for r in results:
        print()
        print(r["block"])

    # ── Markdown output ────────────────────────────────────────────────────────
    md = []
    md.append("# Agent 3 — Exception Resolution Simulation")
    md.append(f"**Run Date:** {run_date}  |  **Seed:** {seed}")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append("| Total | AUTO-EXECUTE | ESCALATE | Avg Composite Score |")
    md.append("|:-----:|:------------:|:--------:|:-------------------:|")
    md.append(f"| {total} | {auto_count} | {escalate_count} | {avg_composite} |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Shipment Decisions")
    md.append("")
    for r in results:
        md.append("```")
        md.append(r["block"])
        md.append("```")
        md.append("")
    md.append("---")
    md.append("")
    md.append(
        "> Simulation only. All data fictional.  \n"
        "> Couriers: DHL, PostNL, DPD, Zipovva Exxpress (fictional).  \n"
        "> Built with Claude Code."
    )

    out_path = Path(__file__).parent / "output" / "agent3_exception_resolution_results.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\nResults saved → {out_path}")


if __name__ == "__main__":
    main()
