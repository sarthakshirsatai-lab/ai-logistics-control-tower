# AI Logistics Control Tower

A personal learning project — building agentic AI 
systems that simulate operational decision-making 
in logistics, based on experience in end-to-end 
logistics operations.

Built with Claude Code | Python

---

## Agent 1: Last Mile Exception Detector

Monitors simulated B2C last mile shipments across 
Germany, France and Netherlands.

**Couriers:** DHL, PostNL, DPD, SpeedX Logistics 
(fictional budget courier)

**SLA Windows:** 24h urban | 72h standard

**5 exceptions detected:**
- SLA Breach Risk
- Customer Absent
- Courier Underperformance
- Address Error
- Regional Delay Spike

**Decision logic:**
Auto-execute — reroute, notify customer, 
suspend courier

Escalate to human — VIP customer, 
order >€200, regional impact >20 shipments

**Latest simulation run:**
10 shipments | 11 exceptions | 
5 auto-executed | 6 escalated to human

---

## Project Structure

- last_mile_agent.py — Agent 1 Python script
- Workflows/ — Plain English agent instructions
- output/ — Simulation results

---

## Disclaimer

All shipment data is simulated. Courier OTD 
benchmarks based on Parcel Monitor Q2/Q3 2024. 
SpeedX Logistics is fictional.
