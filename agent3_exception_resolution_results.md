# Agent 3 — Exception Resolution Simulation
**Run Date:** 2026-05-04  |  **Seed:** 20260504

## Summary

| Total | AUTO-EXECUTE | ESCALATE | Avg Composite Score |
|:-----:|:------------:|:--------:|:-------------------:|
| 10 | 5 | 5 | 7.17 |

---

## Shipment Decisions

```
SHIPMENT: SHP-1001 | PostNL | Germany
EXCEPTION: customer_absent | URGENCY: MEDIUM
HOURS LEFT: 34h | ORDER: €96.92
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
Express Re-ship             0     3   9      3.30
─────────────────────────────────────────────────
DECISION: AUTO-EXECUTE
  → Action: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1002 | Zipovva Exxpress | Netherlands
EXCEPTION: failed_attempt | URGENCY: MEDIUM
HOURS LEFT: 18h | ORDER: €130.80
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
PUDO Point Reroute ✓        7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
Express Re-ship             0     3   9      3.30
─────────────────────────────────────────────────
DECISION: AUTO-EXECUTE
  → Action: PUDO Point Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1003 | DPD | Netherlands
EXCEPTION: address_error | URGENCY: MEDIUM
HOURS LEFT: 48h | ORDER: €68.26
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
PUDO Point Reroute ✓        7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
─────────────────────────────────────────────────
DECISION: ESCALATE TO DISPATCH CONTROLLER
  → Recommended: PUDO Point Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1004 | DHL | France
EXCEPTION: failed_attempt | URGENCY: MEDIUM
HOURS LEFT: 35h | ORDER: €127.69
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
─────────────────────────────────────────────────
DECISION: AUTO-EXECUTE
  → Action: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1005 | DPD | Germany
EXCEPTION: address_error | URGENCY: MEDIUM
HOURS LEFT: 33h | ORDER: €208.93
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
Express Re-ship             0     3   9      3.30
Proactive Compensation      0     1   8      2.35
─────────────────────────────────────────────────
DECISION: ESCALATE TO DISPATCH CONTROLLER
  → Recommended: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1006 | PostNL | France
EXCEPTION: address_error | URGENCY: HIGH
HOURS LEFT: 7h | ORDER: €207.30
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Standard Re-attempt ✓       1     8   4      4.20
Proactive Compensation      0     1   8      2.35
─────────────────────────────────────────────────
DECISION: ESCALATE TO DISPATCH CONTROLLER
  → Recommended: Standard Re-attempt | Cost: €2.50
```

```
SHIPMENT: SHP-1007 | DPD | France
EXCEPTION: failed_attempt | URGENCY: MEDIUM
HOURS LEFT: 34h | ORDER: €89.51
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     7    10   5      7.55
Standard Re-attempt         3     8   4      5.00
─────────────────────────────────────────────────
DECISION: AUTO-EXECUTE
  → Action: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1008 | PostNL | Germany
EXCEPTION: failed_attempt | URGENCY: LOW
HOURS LEFT: 64h | ORDER: €104.26
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     8    10   5      7.95
Standard Re-attempt         6     8   4      6.20
Express Re-ship             0     3   9      3.30
─────────────────────────────────────────────────
DECISION: AUTO-EXECUTE
  → Action: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1009 | PostNL | France
EXCEPTION: customer_absent | URGENCY: HIGH
HOURS LEFT: 7h | ORDER: €60.12
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     4    10   5      6.35
Standard Re-attempt         1     8   4      4.20
─────────────────────────────────────────────────
DECISION: ESCALATE TO DISPATCH CONTROLLER
  → Recommended: Parcel Locker Reroute | Cost: €1.50
```

```
SHIPMENT: SHP-1010 | Zipovva Exxpress | Netherlands
EXCEPTION: customer_absent | URGENCY: LOW
HOURS LEFT: 64h | ORDER: €218.13
─────────────────────────────────────────────────
OPTION                    SLA  COST  CX COMPOSITE
Parcel Locker Reroute ✓     8    10   5      7.95
Standard Re-attempt         6     8   4      6.20
Express Re-ship             0     3   9      3.30
Proactive Compensation      0     1   8      2.35
─────────────────────────────────────────────────
DECISION: ESCALATE TO DISPATCH CONTROLLER
  → Recommended: Parcel Locker Reroute | Cost: €1.50
```

---

> Simulation only. All data fictional.  
> Couriers: DHL, PostNL, DPD, Zipovva Exxpress (fictional).  
> Built with Claude Code.