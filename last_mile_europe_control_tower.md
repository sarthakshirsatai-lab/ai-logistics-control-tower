# Last Mile Europe — Control Tower Agent Workflow

## Purpose
This workflow instructs the AI agent to monitor 
last mile delivery operations across European 
markets and detect, decide, and escalate 
exceptions autonomously.

## End User
Primary: Operations Manager at a D2C brand or 
3PL operator managing European last mile 
delivery across Germany, France, Netherlands.

User needs: Exception visibility, recommended 
actions, and escalation paths — all actionable 
in under 30 seconds per alert.

## Context
- Geography: Germany, France, Netherlands
- Operation: B2C last mile delivery
- Couriers: DHL, DPD, PostNL, Evri
- SLA Tier 1: 48-72 hours (standard)
- SLA Tier 2: less than 24 hours (urban express)
- First attempt failure rate: 25% industry norm

## Data Inputs the Agent Monitors
1. GPS and telematics feed per shipment
2. Order scan events (at hub, out for delivery, 
   failed attempt, delivered)
3. Customer SLA deadline per shipment
4. Courier on-time delivery rate (last 30 days)
5. Regional delay signals (weather, strikes, 
   public holidays)

## Exception Types to Detect
1. Address error — incomplete or incorrect 
   customer address
2. Customer absent — missed time slot or 
   no one home
3. Courier underperformance — courier on-time 
   rate drops below 85%
4. SLA breach risk — shipment within 2 hours 
   of SLA deadline and not delivered
5. Regional delay spike — abnormal delay 
   concentration in a specific postcode or zone

## Decision Rules

### Auto-execute (no human needed):
- Reroute shipment to nearest parcel locker 
  if customer absent on first attempt
- Send proactive customer notification when 
  SLA breach risk is detected
- Flag courier as underperforming and stop 
  allocating new shipments to them
- Log all exceptions with timestamp, 
  shipment ID, and action taken

### Escalate to human when:
- Cost of corrective action exceeds 50 euros
- Exception type is novel with no matching rule
- Customer is flagged as VIP or high value order
- Regional delay affects more than 20 shipments 
  simultaneously

## Output Format
For each exception detected, the agent produces 
a 30-second actionable alert:
- Shipment ID
- Exception type
- Severity (Low / Medium / High)
- Recommended action
- Auto-executed or escalated to human
- Timestamp

## Escalation Path
Dispatcher → Supervisor → Regional Manager
Each level has 30 minutes to respond before 
auto-escalating to the next level.
