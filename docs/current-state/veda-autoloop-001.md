# VEDA-AUTOLOOP-001

The persistent controller is [scripts/veda_loop.py](../../../scripts/veda_loop.py).
It reads [LOOP_STATE.json](../../roadmap/veda/LOOP_STATE.json), acquires a
single-instance lock, refuses unrelated tracked changes, invokes the installed
Codex CLI once per bounded activity, records ignored JSONL iteration logs under
`.veda-loop/`, retries transient process failures at most twice, and stops on
explicit state or repository-failure conditions.

## Usage

```powershell
py -3.11 scripts/veda_loop.py --dry-run
py -3.11 scripts/veda_loop.py --max-loops 10
```

Set `enabled` to `false` in `LOOP_STATE.json` for a graceful stop. `Ctrl+C`
also releases the controller lock without rewriting history. The controller
uses safe default execution with `codex exec --json --ephemeral --sandbox
workspace-write --approve-for-me -C <repo> -`. Unrestricted execution
is explicit opt-in via `--unsafe-codex`.

R1 hardens streaming JSONL event capture, heartbeat state, hard and idle
timeouts, partial-completion classification, bounded repair, blocker history,
track switching and zero-progress protection. Runtime logs remain ignored.
