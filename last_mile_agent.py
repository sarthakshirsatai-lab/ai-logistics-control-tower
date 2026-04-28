from datetime import datetime, timedelta
from pathlib import Path

NOW = datetime(2026, 4, 28, 13, 0, 0)

SHIPMENTS = [
    {
        "shipment_id": "EU-DE-001",
        "courier": "DHL",
        "country": "Germany",
        "postcode": "10115",
        "sla_tier": "Tier2",
        "sla_deadline": NOW + timedelta(hours=1.5),
        "status": "out_for_delivery",
        "attempt_count": 0,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 85,
        "courier_otd_rate": 0.96,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-DE-002",
        "courier": "DPD",
        "country": "Germany",
        "postcode": "20095",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=8),
        "status": "failed_attempt",
        "attempt_count": 1,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 45,
        "courier_otd_rate": 0.90,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-DE-003",
        "courier": "DHL",
        "country": "Germany",
        "postcode": "80331",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=20),
        "status": "in_transit",
        "attempt_count": 0,
        "address_complete": False,
        "is_vip": True,
        "order_value_eur": 240,
        "courier_otd_rate": 0.97,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-FR-004",
        "courier": "DPD",
        "country": "France",
        "postcode": "75001",
        "sla_tier": "Tier2",
        "sla_deadline": NOW + timedelta(hours=1.8),
        "status": "out_for_delivery",
        "attempt_count": 0,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 60,
        "courier_otd_rate": 0.89,
        "regional_delay": True,
    },
    {
        "shipment_id": "EU-FR-005",
        "courier": "SpeedX Logistics",
        "country": "France",
        "postcode": "69001",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=30),
        "status": "in_transit",
        "attempt_count": 0,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 35,
        "courier_otd_rate": 0.70,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-FR-006",
        "courier": "SpeedX Logistics",
        "country": "France",
        "postcode": "13001",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=48),
        "status": "delivered",
        "attempt_count": 1,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 110,
        "courier_otd_rate": 0.72,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-NL-007",
        "courier": "PostNL",
        "country": "Netherlands",
        "postcode": "1017",
        "sla_tier": "Tier2",
        "sla_deadline": NOW + timedelta(hours=5),
        "status": "failed_attempt",
        "attempt_count": 2,
        "address_complete": True,
        "is_vip": True,
        "order_value_eur": 310,
        "courier_otd_rate": 0.95,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-NL-008",
        "courier": "DHL",
        "country": "Netherlands",
        "postcode": "3011",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=12),
        "status": "in_transit",
        "attempt_count": 0,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 55,
        "courier_otd_rate": 0.95,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-NL-009",
        "courier": "SpeedX Logistics",
        "country": "Netherlands",
        "postcode": "2511",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=1.2),
        "status": "in_transit",
        "attempt_count": 0,
        "address_complete": False,
        "is_vip": False,
        "order_value_eur": 220,
        "courier_otd_rate": 0.68,
        "regional_delay": False,
    },
    {
        "shipment_id": "EU-DE-010",
        "courier": "DPD",
        "country": "Germany",
        "postcode": "50667",
        "sla_tier": "Tier1",
        "sla_deadline": NOW + timedelta(hours=36),
        "status": "in_transit",
        "attempt_count": 0,
        "address_complete": True,
        "is_vip": False,
        "order_value_eur": 70,
        "courier_otd_rate": 0.91,
        "regional_delay": False,
    },
]

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
    if s["courier_otd_rate"] < 0.88:
        return {"exception_type": "courier_underperformance", "severity": "High"}
    return None


def check_sla_breach_risk(s):
    if s["status"] != "delivered":
        hours_left = (s["sla_deadline"] - NOW).total_seconds() / 3600
        if hours_left <= 2:
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
        f"SLA Deadline: {s['sla_deadline'].strftime('%H:%M')} UTC | Hours Left: {hours_left:.1f}h | Status: {s['status']}",
    ]
    if exc["exception_type"] == "courier_underperformance":
        lines.append(f"Courier OTD Rate: {s['courier_otd_rate']*100:.0f}% | Threshold: 88%")
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


def main():
    exceptions = detect_exceptions(SHIPMENTS)
    alerts = [apply_decision_rules(e) for e in exceptions]

    print(f"\n=== Last Mile Control Tower | {NOW.strftime('%Y-%m-%d %H:%M')} UTC ===")
    print(f"Shipments: {len(SHIPMENTS)} | Exceptions: {len(alerts)}\n")
    for alert in alerts:
        print(format_alert(alert))
        print()

    save_output(alerts, SHIPMENTS)
    print("Output saved to output/last_mile_control_tower_output.md")


if __name__ == "__main__":
    main()
