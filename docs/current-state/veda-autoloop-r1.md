# VEDA-AUTOLOOP-R1

R1 hardens the persistent controller without changing Jyotisha capability
status. Safe Codex execution is now the default; unrestricted bypass requires
`--unsafe-codex`. The controller records streamed event heartbeats, separates
hard and idle timeout categories, detects completion despite timeout, preserves
recovery context, switches away from repeated blocked empirical/prospective
tracks, and records loop-health metrics in `LOOP_STATE.json`.

Operational dry run:

```powershell
py -3.11 scripts/veda_loop.py --dry-run
```

Recommended bounded run: `--max-loops 3` with explicit hard/idle timeouts.
Do not launch an unattended long run until a safe-mode live validation is
reviewed.

## Acceptance

Status: `IMPLEMENTED / FROZEN` with `PASS_WITH_CONDITION`.

Focused controller and affected regression checks passed. Bounded safe-mode
live probes launched Codex, streamed events, maintained heartbeats, enforced
hard timeouts, and recorded partial completion honestly. PowerShell
shell-snapshot and skills-traversal warnings are external runtime conditions
recorded by the controller; no permission bypass was enabled. No Jyotisha,
empirical, prospective, prediction, or RAG content was created.
