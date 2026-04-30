# Courier Performance Scorecard
**Date Range:** 2026-04-28 to 2026-05-27
**Runs:** 30 | **Total Shipment Entries:** 300

## Scorecard

| Courier | Shipments | OTD Rate | Courier Miss | Non-Courier Miss | Attrib. Exc. Rate | Composite Flag | Rating | Action |
|---------|-----------|----------|--------------|-----------------|-------------------|----------------|--------|--------|
| Zipovva Exxpress | 80 | 69.8% | 80 | 32 | 100.0% | YES | Red | Suspend |
| DPD | 77 | 90.4% | 0 | 26 | 0.0% | NO | Amber | Monitor |
| PostNL | 73 | 95.0% | 0 | 19 | 0.0% | NO | Green | Continue |
| DHL | 70 | 96.5% | 0 | 15 | 0.0% | NO | Green | Continue |

---

## Courier Detail & Rationale

### Zipovva Exxpress — Red
**Action: Suspend**  
OTD rate significantly below threshold or composite flag triggered. Pause new shipment allocation immediately and initiate review.

- OTD Rate: 69.8% (Green ≥ 93% | Amber ≥ 88% | Red < 88%)
- Total Shipments: 80
- Courier-Attributable Miss: 80 (100.0% of shipments)
- Non-Courier-Attributable Miss: 32
- Courier-Attributable Exception Rate: 100.0%
- Total Exceptions Flagged: 122
- Composite Underperformance Flag: YES — OTD 69.8% < 85% floor | Courier miss rate 100.0% > 15% ceiling | Attrib. exc. rate 100.0% > 20% ceiling

### DPD — Amber
**Action: Monitor**  
OTD rate approaching lower threshold. Review weekly; reduce allocation if trend worsens.

- OTD Rate: 90.4% (Green ≥ 93% | Amber ≥ 88% | Red < 88%)
- Total Shipments: 77
- Courier-Attributable Miss: 0 (0.0% of shipments)
- Non-Courier-Attributable Miss: 26
- Courier-Attributable Exception Rate: 0.0%
- Total Exceptions Flagged: 37
- Composite Underperformance Flag: NO

### PostNL — Green
**Action: Continue**  
Performance is within acceptable OTD range. Maintain current allocation.

- OTD Rate: 95.0% (Green ≥ 93% | Amber ≥ 88% | Red < 88%)
- Total Shipments: 73
- Courier-Attributable Miss: 0 (0.0% of shipments)
- Non-Courier-Attributable Miss: 19
- Courier-Attributable Exception Rate: 0.0%
- Total Exceptions Flagged: 29
- Composite Underperformance Flag: NO

### DHL — Green
**Action: Continue**  
Performance is within acceptable OTD range. Maintain current allocation.

- OTD Rate: 96.5% (Green ≥ 93% | Amber ≥ 88% | Red < 88%)
- Total Shipments: 70
- Courier-Attributable Miss: 0 (0.0% of shipments)
- Non-Courier-Attributable Miss: 15
- Courier-Attributable Exception Rate: 0.0%
- Total Exceptions Flagged: 23
- Composite Underperformance Flag: NO

---
**Rating Bands:** Green ≥ 93% OTD | Amber 88–92% OTD | Red < 88% OTD
**Composite Flag triggers Suspend when:** OTD < 85% | Courier Miss Rate > 15% | Attrib. Exc. Rate > 20%