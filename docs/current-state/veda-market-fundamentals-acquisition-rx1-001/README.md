# VEDA-MARKET-FUNDAMENTALS-ACQUISITION-RX1-001

Status: `OPERATIONAL_WITH_CONDITIONS`

This activity repairs the provider-local quarterly fundamental acquisition
path. It does not move Market ownership to VEDA and does not alter prediction,
ML, empirical, Jyotish, RAG, or Corporate Intelligence behavior.

The repaired path now rechecks dynamically derived recent completed filing
windows, uses the official NSE results endpoint with bounded identity-encoded
transport, preserves filing-date and statement-variant provenance, and avoids
rewriting an unchanged normalized result. The live source currently exposes
delayed or re-filed older periods rather than a representative 2026-06-30
quarter; that upstream condition remains explicit.

Owner: `D:\Projects\fii-dii-sector-intelligence`

Canonical command:

```powershell
py -3.11 engines/fundamentals/financial_results_engine.py --windows 2
```

The routine daily refresh remains a separate EOD market pipeline. Quarterly
results acquisition is exposed through the existing manual/backfill operation;
this activity does not create a second scheduler.
