# Hourly Discovery

Hourly runs are intended to stay lightweight.

Current implementation:
- uses the schedule trigger type `HOURLY`;
- executes through the same governed service pipeline as manual runs;
- can be throttled by backlog state and mission budgets;
- advances schedule state without needing the Admin UI.

Hourly discovery is not allowed to bypass Admin review or Approved Core boundaries.
