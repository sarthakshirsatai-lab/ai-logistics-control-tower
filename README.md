# AI Logistics Control Tower

A personal learning project — building agentic AI 
systems that simulate operational decision-making 
in logistics, based on 8.5 years of experience in 
end-to-end logistics operations.

Built with Claude Code | Python

---

## Agent 1 — Last Mile Exception Detector

Monitors simulated B2C last mile shipments across 
Germany, France and Netherlands. Detects exceptions 
in real-time and classifies them by type and severity.

**Couriers:** DHL, PostNL, DPD, SpeedX Logistics (fictional)

**Exception types detected:**
- Failed Attempt
- Customer Absent
- Address Error
- Regional Delay
- Courier Underperformance

**Latest simulation run:**

![Agent 1 Simulation Results](agent1_simulation_results_3.png)

10 shipments | 11 exceptions detected | 
5 auto-executed | 6 escalated to human

---

## Agent 2 — Courier Performance Monitor

Analyses 30 days of shipment data across 300 shipments. 
Scores each courier on OTD rate, courier-attributable 
failures and exception rate. Outputs a RAG rating with 
recommended action per courier.

**Couriers:** DHL, PostNL, DPD, Zipovva Exxpress (fictional)

**Rating bands:** 🟢 Green ≥ 93% OTD | 🟡 Amber 88–92% | 🔴 Red < 88%

**Actions:** Continue / Monitor / Suspend

**Latest simulation run:**

![Agent 2 Scorecard](agent2_courier_performance.png)

300 shipments | 30 days | 4 couriers evaluated | 1 suspended

---

## Agent 3 — Exception Resolution Agent

Given a shipment exception, evaluates all available 
remediation options and recommends the optimal action 
using a weighted composite score across three dimensions:
SLA Recovery (40%), Cost (35%), Customer Experience (25%).

**Couriers:** DHL, PostNL, DPD, Zipovva Exxpress (fictional)

**Exception types:** Failed Attempt | Customer Absent | Address Error

**Options evaluated:**
- Parcel Locker Reroute
- PUDO Point Reroute
- Standard Re-attempt
- Express Re-ship
- Proactive Compensation

**Output:** Scored decision table + AUTO-EXECUTE or 
ESCALATE TO DISPATCH CONTROLLER

**Latest simulation run:**

![Agent 3 Exception Resolution](agent3_exception_resolution.png)

10 shipments | 5 auto-executed | 5 escalated | 
Avg composite score: 7.17 / 10

---

## Coming Soon

- Agent 4 — Customer Communication Agent
- Agent 5 — Orchestrator

---

## Case Study

Full design decisions, scoring logic and simulation 
results for all agents:

[AI Logistics Control Tower — Case Study](AI_Logistics_Control_Tower_Case_Study_05052026.docx)

---

## Project Structure
