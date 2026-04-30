import json
import random
from datetime import datetime, timedelta
from pathlib import Path

BASE_DATE = datetime(2026, 4, 28, 14, 0, 0)


def _compute_now():
    log_path = Path("data/shipment_log.json")
    if not log_path.exists():
        return BASE_DATE
    try:
        log = json.loads(log_path.read_text(encoding="utf-8"))
        run_dates = {e["run_date"] for e in log}
        return BASE_DATE + timedelta(days=len(run_dates))
    except Exception:
        return BASE_DATE


NOW = _compute_now()

COURIERS = {
    "DHL": (0.95, 0.98),
    "PostNL": (0.93, 0.97),
    "DPD": (0.88, 0.93),
    "Zipovva Exxpress": (0.65, 0.75),
}

SHIPMENT_TEMPLATES = [
    {"shipment_id": "EU-DE-001", "country": "Germany",     "postcode": "10115", "sla_tier": "Tier2", "address_complete": True,  "is_vip": False, "order_value_eur": 85,  "regional_delay": False},
    {"shipment_id": "EU-DE-002", "country": "Germany",     "postcode": "20095", "sla_tier": "Tier1", "address_complete": True,  "is_vip": False, "order_value_eur": 45,  "regional_delay": False},
    {"shipment_id": "EU-DE-003", "country": "Germany",     "postcode": "80331", "sla_tier": "Tier1", "address_complete": False, "is_vip": True,  "order_value_eur": 240, "regional_delay": False},
    {"shipment_id": "EU-FR-004", "country": "France",      "postcode": "75001", "sla_tier": "Tier2", "address_complete": True,  "is_vip": False, "order_value_eur": 60,  "regional_delay": True},
    {"shipment_id": "EU-FR-005", "country": "France",      "postcode": "69001", "sla_tier": "Tier1", "address_complete": True,  "is_vip": False, "order_value_eur": 35,  "regional_delay": False},
    {"shipment_id": "EU-FR-006", "country": "France",      "postcode": "13001", "sla_tier": "Tier1", "address_complete": True,  "is_vip": False, "order_value_eur": 110, "regional_delay": False},
    {"shipment_id": "EU-NL-007", "country": "Netherlands", "postcode": "1017",  "sla_tier": "Tier2", "address_complete": True,  "is_vip": True,  "order_value_eur": 310, "regional_delay": False},
    {"shipment_id": "EU-NL-008", "country": "Netherlands", "postcode": "3011",  "sla_tier": "Tier1", "address_complete": True,  "is_vip": False, "order_value_eur": 55,  "regional_delay": False},
    {"shipment_id": "EU-NL-009", "country": "Netherlands", "postcode": "2511",  "sla_tier": "Tier1", "address_complete": False, "is_vip": False, "order_value_eur": 220, "regional_delay": False},
    {"shipment_id": "EU-DE-010", "country": "Germany",     "postcode": "50667", "sla_tier": "Tier1", "address_complete": True,  "is_vip": False, "order_value_eur": 70,  "regional_delay": False},
]

SLA_HOURS = {"Tier1": 72, "Tier2": 24}


def build_shipments():
    order_creation = NOW.replace(hour=9, minute=0, second=0, microsecond=0)
    courier_list = list(COURIERS.keys())
    assignments = courier_list * 2          # guarantee 2 per courier (8 shipments)
    assignments += random.choices(courier_list, k=2)  # distribute remaining 2 randomly
    random.shuffle(assignments)

    shipments = []
    for tmpl, courier in zip(SHIPMENT_TEMPLATES, assignments):
        otd_min, otd_max = COURIERS[courier]
        otd_rate = round(random.uniform(otd_min, otd_max), 2)
        roll = random.random()
        if roll > otd_rate:
            status, attempt_count = "failed_attempt", 1
        else:
            status, attempt_count = random.choice(["out_for_delivery", "delivered"]), 0
        s = dict(tmpl)
        s["courier"] = courier
        s["courier_otd_rate"] = otd_rate
        s["status"] = status
        s["attempt_count"] = attempt_count
        s["sla_deadline"] = order_creation + timedelta(hours=SLA_HOURS[tmpl["sla_tier"]])
        shipments.append(s)
    return shipments


SHIPMENTS = build_shipments()

ACTIONS = {
    "address_error": "Trigger address correction workflow; contact customer",
    "customer_absent": "Reroute to nearest parcel locker",
    "courier_underperformance": "Flag courier; pause new shipment allocation",
    "sla_breach_risk": "Send proactive SLA delay notification to customer",
    "regional_delay_spike": "Monitor zone; pre-notify affected customers",
}

SEVERITY = {
    "address_error": "Medium",
    "courier_underperformance": "High",
    "sla_breach_risk": "High",
    "regional_delay_spike": "Medium",
}


def check_address_error(s):
    if not s["address_complete"]:
        return {"exception_type": "address_error", "severity": "Medium"}
    return None


def check_customer_absent(s):
    if s["status"] == "failed_attempt" and s["attempt_count"] >= 1:
        severity = "Medium" if s["attempt_count"] >= 2 else "Low"
        return {"exception_type": "customer_absent", "severity": severity}
    return None


def check_courier_underperformance(s):
    if s["courier_otd_rate"] < 0.85:
        return {"exception_type": "courier_underperformance", "severity": "High"}
    return None


def check_sla_breach_risk(s):
    if s["status"] != "delivered":
        hours_left = (s["sla_deadline"] - NOW).total_seconds() / 3600
        if hours_left < 2:
            return {"exception_type": "sla_breach_risk", "severity": "High"}
    return None


def check_regional_delay(s):
    if s["regional_delay"]:
        return {"exception_type": "regional_delay_spike", "severity": "Medium"}
    return None


def detect_exceptions(shipments):
    results = []
    checkers = [
        check_address_error,
        check_customer_absent,
        check_courier_underperformance,
        check_sla_breach_risk,
        check_regional_delay,
    ]
    for s in shipments:
        for checker in checkers:
            exc = checker(s)
            if exc:
                exc["shipment_id"] = s["shipment_id"]
                exc["shipment"] = s
                results.append(exc)
    return results


def apply_decision_rules(exc):
    s = exc["shipment"]
    action = ACTIONS[exc["exception_type"]]
    escalate = False
    reason = None

    if s["is_vip"]:
        escalate = True
        reason = "VIP Customer"
    elif s["order_value_eur"] > 200:
        escalate = True
        reason = f"High-value order (€{s['order_value_eur']})"
    elif exc["exception_type"] == "regional_delay_spike":
        escalate = True
        reason = "Regional delay may affect >20 shipments"

    exc["recommended_action"] = action
    exc["disposition"] = "escalate_human" if escalate else "auto_execute"
    exc["escalation_reason"] = reason
    exc["timestamp"] = NOW.strftime("%Y-%m-%d %H:%M:%S")
    return exc


def format_alert(exc):
    s = exc["shipment"]
    hours_left = (s["sla_deadline"] - NOW).total_seconds() / 3600
    disp_label = "ESCALATE TO HUMAN" if exc["disposition"] == "escalate_human" else "AUTO-EXECUTE"
    exc_label_map = {
        "address_error": "Address Error",
        "customer_absent": "Customer Absent",
        "courier_underperformance": "Courier Underperformance",
        "sla_breach_risk": "SLA Breach Risk",
        "regional_delay_spike": "Regional Delay Spike",
    }
    exc_label = exc_label_map.get(exc["exception_type"], exc["exception_type"].replace("_", " ").title())

    lines = [
        f"[ALERT] {exc['shipment_id']} | {exc_label} | {exc['severity'].upper()}",
        f"Courier: {s['courier']} | Country: {s['country']} | Postcode: {s['postcode']}",
        f"SLA Deadline: {s['sla_deadline'].strftime('%Y-%m-%d %H:%M')} UTC | Hours Left: {hours_left:.1f}h | Status: {s['status']}",
    ]
    if exc["exception_type"] == "courier_underperformance":
        lines.append(f"Courier OTD Rate: {s['courier_otd_rate']*100:.0f}% | Threshold: 85%")
    lines += [
        f"Action: {exc['recommended_action']}",
        f"Disposition: {disp_label}",
    ]
    if exc["escalation_reason"]:
        lines.append(f"Escalation Reason: {exc['escalation_reason']}")
    lines.append(f"Timestamp: {exc['timestamp']}")
    return "\n".join(lines)


def save_output(alerts, shipments):
    Path("output").mkdir(exist_ok=True)
    auto = sum(1 for a in alerts if a["disposition"] == "auto_execute")
    escalated = len(alerts) - auto

    lines = [
        "# Last Mile Europe — Control Tower Output",
        f"**Run:** {NOW.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        "",
        "## Summary",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total Shipments | {len(shipments)} |",
        f"| Exceptions Detected | {len(alerts)} |",
        f"| Auto-Executed | {auto} |",
        f"| Escalated to Human | {escalated} |",
        "",
        "## Alerts",
        "",
    ]

    for alert in alerts:
        lines.append("```")
        lines.append(format_alert(alert))
        lines.append("```")
        lines.append("")

    lines += [
        "---",
        "**Escalation Path:** Dispatcher → Supervisor → Regional Manager",
        "Each level has 30 minutes to respond before auto-escalating.",
    ]

    Path("output/last_mile_control_tower_output.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def append_to_log(shipments, exceptions):
    Path("data").mkdir(exist_ok=True)
    log_path = Path("data/shipment_log.json")
    log = json.loads(log_path.read_text(encoding="utf-8")) if log_path.exists() else []

    exc_map = {}
    for e in exceptions:
        exc_map.setdefault(e["shipment_id"], []).append(e["exception_type"])

    for s in shipments:
        entry = {k: v for k, v in s.items() if k != "sla_deadline"}
        entry["sla_deadline"] = s["sla_deadline"].isoformat()
        entry["run_date"] = NOW.strftime("%Y-%m-%d")
        entry["exceptions"] = exc_map.get(s["shipment_id"], [])
        log.append(entry)

    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    exceptions = detect_exceptions(SHIPMENTS)
    alerts = [apply_decision_rules(e) for e in exceptions]

    print(f"\n=== Last Mile Control Tower | {NOW.strftime('%Y-%m-%d %H:%M')} UTC ===")
    print(f"Shipments: {len(SHIPMENTS)} | Exceptions: {len(alerts)}\n")
    for alert in alerts:
        print(format_alert(alert))
        print()

    save_output(alerts, SHIPMENTS)
    append_to_log(SHIPMENTS, exceptions)
    print("Output saved to output/last_mile_control_tower_output.md")
    print(f"Log updated: data/shipment_log.json ({NOW.strftime('%Y-%m-%d')})")


if __name__ == "__main__":
    main()
