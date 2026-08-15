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
