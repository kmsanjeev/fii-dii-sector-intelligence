# Continuity Simulation

An accelerated continuity test now simulates:
- 24 hourly cycles;
- ongoing candidate enrichment;
- restart-safe persistence of the resulting candidate state.

The continuity suite proves:
- pending approvals do not inherently block future runs;
- repeated discovery enriches an existing candidate instead of creating uncontrolled duplicates;
- runtime state survives service re-instantiation through SQLite persistence.
