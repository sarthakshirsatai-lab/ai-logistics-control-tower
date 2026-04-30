import json
from pathlib import Path

LOG_PATH = Path("data/shipment_log.json")

GREEN_THRESHOLD = 0.93
AMBER_THRESHOLD = 0.88

COURIER_ATTRIBUTABLE = {"sla_breach_risk", "courier_underperformance"}
NON_COURIER_ATTRIBUTABLE = {"customer_absent", "address_error"}

# Composite underperformance thresholds
OTD_FLOOR = 0.85
MISS_RATE_CEILING = 0.15
ATTRIB_EXC_RATE_CEILING = 0.20


def load_shipment_log():
    if not LOG_PATH.exists():
        raise FileNotFoundError("data/shipment_log.json not found. Run last_mile_agent.py first.")
    return json.loads(LOG_PATH.read_text(encoding="utf-8"))


def rate_courier(otd_rate):
    if otd_rate >= GREEN_THRESHOLD:
        return "Green", "Continue"
    elif otd_rate >= AMBER_THRESHOLD:
        return "Amber", "Monitor"
    else:
        return "Red", "Suspend"


def build_scorecard(log):
    couriers = {}
    for entry in log:
        c = entry["courier"]
        if c not in couriers:
            couriers[c] = {
                "total_shipments": 0,
                "otd_rates": [],
                "courier_attributable_miss": 0,
                "non_courier_attributable_miss": 0,
                "courier_attributable_exceptions": 0,
                "total_exceptions": 0,
            }
        couriers[c]["total_shipments"] += 1
        couriers[c]["otd_rates"].append(entry["courier_otd_rate"])

        exc_types = set(entry["exceptions"])
        if exc_types & COURIER_ATTRIBUTABLE:
            couriers[c]["courier_attributable_miss"] += 1
        if exc_types & NON_COURIER_ATTRIBUTABLE:
            couriers[c]["non_courier_attributable_miss"] += 1
        couriers[c]["courier_attributable_exceptions"] += len(exc_types & COURIER_ATTRIBUTABLE)
        couriers[c]["total_exceptions"] += len(entry["exceptions"])

    scorecard = []
    for courier, data in couriers.items():
        total = data["total_shipments"]
        avg_otd = sum(data["otd_rates"]) / len(data["otd_rates"])
        rating, recommendation = rate_courier(avg_otd)

        miss_rate = data["courier_attributable_miss"] / total
        attrib_exc_rate = data["courier_attributable_exceptions"] / total
        composite_flag = (
            avg_otd < OTD_FLOOR
            or miss_rate > MISS_RATE_CEILING
            or attrib_exc_rate > ATTRIB_EXC_RATE_CEILING
        )
        if composite_flag:
            recommendation = "Suspend"

        scorecard.append({
            "courier": courier,
            "total_shipments": total,
            "otd_rate": avg_otd,
            "courier_attributable_miss": data["courier_attributable_miss"],
            "non_courier_attributable_miss": data["non_courier_attributable_miss"],
            "attrib_exc_rate": attrib_exc_rate,
            "total_exceptions": data["total_exceptions"],
            "composite_flag": composite_flag,
            "rating": rating,
            "recommendation": recommendation,
        })

    order = {"Red": 0, "Amber": 1, "Green": 2}
    scorecard.sort(key=lambda x: order[x["rating"]])
    return scorecard


RECOMMENDATION_NOTES = {
    "Continue": "Performance is within acceptable OTD range. Maintain current allocation.",
    "Monitor": "OTD rate approaching lower threshold. Review weekly; reduce allocation if trend worsens.",
    "Suspend": "OTD rate significantly below threshold or composite flag triggered. Pause new shipment allocation immediately and initiate review.",
}


def save_output(scorecard, run_dates, total_entries):
    Path("output").mkdir(exist_ok=True)

    date_range = f"{run_dates[0]} to {run_dates[-1]}" if len(run_dates) > 1 else run_dates[0]

    lines = [
        "# Courier Performance Scorecard",
        f"**Date Range:** {date_range}",
        f"**Runs:** {len(run_dates)} | **Total Shipment Entries:** {total_entries}",
        "",
        "## Scorecard",
        "",
        "| Courier | Shipments | OTD Rate | Courier Miss | Non-Courier Miss | Attrib. Exc. Rate | Composite Flag | Rating | Action |",
        "|---------|-----------|----------|--------------|-----------------|-------------------|----------------|--------|--------|",
    ]

    for r in scorecard:
        flag_label = "YES" if r["composite_flag"] else "NO"
        lines.append(
            f"| {r['courier']} "
            f"| {r['total_shipments']} "
            f"| {r['otd_rate']*100:.1f}% "
            f"| {r['courier_attributable_miss']} "
            f"| {r['non_courier_attributable_miss']} "
            f"| {r['attrib_exc_rate']*100:.1f}% "
            f"| {flag_label} "
            f"| {r['rating']} "
            f"| {r['recommendation']} |"
        )

    lines += ["", "---", "", "## Courier Detail & Rationale", ""]

    for r in scorecard:
        total = r["total_shipments"]
        miss_rate = r["courier_attributable_miss"] / total * 100
        flag_reasons = []
        if r["otd_rate"] < OTD_FLOOR:
            flag_reasons.append(f"OTD {r['otd_rate']*100:.1f}% < {OTD_FLOOR*100:.0f}% floor")
        if r["courier_attributable_miss"] / total > MISS_RATE_CEILING:
            flag_reasons.append(f"Courier miss rate {miss_rate:.1f}% > {MISS_RATE_CEILING*100:.0f}% ceiling")
        if r["attrib_exc_rate"] > ATTRIB_EXC_RATE_CEILING:
            flag_reasons.append(f"Attrib. exc. rate {r['attrib_exc_rate']*100:.1f}% > {ATTRIB_EXC_RATE_CEILING*100:.0f}% ceiling")

        lines += [
            f"### {r['courier']} — {r['rating']}",
            f"**Action: {r['recommendation']}**  ",
            f"{RECOMMENDATION_NOTES[r['recommendation']]}",
            "",
            f"- OTD Rate: {r['otd_rate']*100:.1f}% (Green ≥ {GREEN_THRESHOLD*100:.0f}% | Amber ≥ {AMBER_THRESHOLD*100:.0f}% | Red < {AMBER_THRESHOLD*100:.0f}%)",
            f"- Total Shipments: {r['total_shipments']}",
            f"- Courier-Attributable Miss: {r['courier_attributable_miss']} ({miss_rate:.1f}% of shipments)",
            f"- Non-Courier-Attributable Miss: {r['non_courier_attributable_miss']}",
            f"- Courier-Attributable Exception Rate: {r['attrib_exc_rate']*100:.1f}%",
            f"- Total Exceptions Flagged: {r['total_exceptions']}",
            f"- Composite Underperformance Flag: {'YES — ' + ' | '.join(flag_reasons) if r['composite_flag'] else 'NO'}",
            "",
        ]

    lines += [
        "---",
        f"**Rating Bands:** Green ≥ {GREEN_THRESHOLD*100:.0f}% OTD | Amber {AMBER_THRESHOLD*100:.0f}–{GREEN_THRESHOLD*100-1:.0f}% OTD | Red < {AMBER_THRESHOLD*100:.0f}% OTD",
        f"**Composite Flag triggers Suspend when:** OTD < {OTD_FLOOR*100:.0f}% | Courier Miss Rate > {MISS_RATE_CEILING*100:.0f}% | Attrib. Exc. Rate > {ATTRIB_EXC_RATE_CEILING*100:.0f}%",
    ]

    Path("output/courier_performance_output.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def main():
    log = load_shipment_log()
    run_dates = sorted({e["run_date"] for e in log})
    scorecard = build_scorecard(log)

    print(f"\n=== Courier Performance Scorecard ===")
    print(f"Data: {run_dates[0]} to {run_dates[-1]} | {len(run_dates)} run(s) | {len(log)} entries\n")
    print(f"{'Courier':<22} {'Ships':>5} {'OTD':>7} {'Courier Miss':>13} {'Non-Cour Miss':>14} {'Attrib Exc%':>12} {'Flag':>5} {'Rating':<7} Action")
    print("-" * 100)
    for r in scorecard:
        flag = "YES" if r["composite_flag"] else "NO"
        print(
            f"{r['courier']:<22} {r['total_shipments']:>5} "
            f"{r['otd_rate']*100:>6.1f}% {r['courier_attributable_miss']:>13} "
            f"{r['non_courier_attributable_miss']:>14} {r['attrib_exc_rate']*100:>11.1f}% "
            f"{flag:>4}  {r['rating']:<7} {r['recommendation']}"
        )

    save_output(scorecard, run_dates, len(log))
    print("\nOutput saved to output/courier_performance_output.md")


if __name__ == "__main__":
    main()
