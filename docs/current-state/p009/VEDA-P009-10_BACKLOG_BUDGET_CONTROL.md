# Backlog And Budget Control

Backlog state is now computed from pending candidates and contradictions:
- `NORMAL`
- `ELEVATED`
- `HIGH`
- `SATURATED`

When backlog rises:
- discovery-style missions can be deprioritized;
- due schedules may be skipped rather than allowed to flood the Admin queue.

Mission budget enforcement now covers:
- query count
- source count
- provider call count
- runtime ceiling

Budget exhaustion marks a run partial rather than silently continuing.
