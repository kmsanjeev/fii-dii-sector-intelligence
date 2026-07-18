# SESSION & MEMORY MANAGEMENT GUIDE
## Capital Flow Intelligence Platform | Added 2026-07-19

Purpose: keep every Claude Code session fast and token-cheap, without ever
losing project state. This works because state lives in two durable places
that survive a cleared or brand-new session:

1. **File-based docs** — `docs/governance/CHANGELOG.md`,
   `docs/governance/MASTER_CHECKLIST.md`, `docs/PROJECT_MASTER_STATE.md`.
2. **Cross-session memory** — `C:\Users\hp\.claude\projects\D--Projects-fii-dii-sector-intelligence\memory\`.

Neither depends on chat scrollback. That's what makes clearing/starting
fresh safe — nothing is "forgotten," it's just not sitting in the token
window anymore.

---

## The three tools, and when each one applies

| Tool | What it does | Use when | Don't use when |
|------|---------------|----------|-----------------|
| **New session** (close this chat, start a new one) | Zero carried-over tokens. Fresh session reads the small status docs + memory to reconstruct context. | Starting a **new phase or unrelated feature** — e.g. finished Portfolio CSV import, now starting a different engine. Also: whenever a session has been open for **most of a working day** regardless of topic. | Mid-task — you'll lose the specific file states/decisions made in the last few turns unless they're already committed or in the CHANGELOG. |
| **`/clear`** | Wipes conversation history, keeps the same terminal/session alive. | Between two **unrelated asks in the same sitting** — e.g. "check the dashboard for X" then, once that's answered and closed, "now build Y" with no dependency on the first answer. | Mid-way through a single multi-step task — clearing loses the working context you need for step 2. |
| **`/compact`** | Summarizes history into a condensed form, keeps working. | You're **still on the same phase/task** but it's spanned many turns/tool calls/file reads and is starting to feel slow. Use it proactively every ~30-40 turns on a long single-phase session, not just when it's already sluggish. | Right before ending the session anyway (just start fresh next time), or immediately after starting (nothing to compact yet). |

### Quick decision rule
- **Same task, getting long** → `/compact`
- **Different task, same sitting** → `/clear`
- **Different phase, or a new day** → new session

---

## Project-side hygiene (already applied, keep enforcing)

- **CHANGELOG.md must stay small.** It was 5,681 lines before 2026-07-19 and
  was being read/flagged nearly every session — a real, avoidable token
  cost. Archived everything before v4.43.0 into
  `docs/governance/CHANGELOG_ARCHIVE.md`. **Rule going forward: whenever
  CHANGELOG.md exceeds ~2000 lines, archive the oldest half into the same
  archive file** (append, don't overwrite) and note the split at the top
  of both files, same pattern as the 2026-07-19 split.
- **MASTER_CHECKLIST.md and PROJECT_MASTER_STATE.md must stay in sync with
  CHANGELOG.md.** They had drifted 4 phases behind because only the
  CHANGELOG step of the mandatory update sequence (`docs/CLAUDE.md`) was
  being followed consistently. All three are resynced as of v4.56
  (2026-07-19) — the phase-gatekeeper agent's end-of-phase ceremony should
  touch all three going forward, not just CHANGELOG.md.
- **Don't re-read CHANGELOG.md in full** to check "what's the latest
  version" — read the first ~50 lines only; the newest entry is always at
  the top.

---

## What never needs to be re-explained in a new session

Because it's already persisted, a fresh session (or one right after
`/clear`) does **not** need you to re-brief:
- Architecture, phase status, known bugs → `MASTER_CHECKLIST.md` /
  `PROJECT_MASTER_STATE.md`
- What changed and why, recent work → top of `CHANGELOG.md`
- Your working preferences (phased dev protocol, raw-data immutability,
  shell-permission stance, GUI dev preferences) → the memory files under
  `C:\Users\hp\.claude\projects\D--Projects-fii-dii-sector-intelligence\memory\`

If a new session seems to be missing context that isn't in one of those
three places, that's a sign something worth persisting was skipped at the
end of the last phase — say so and it'll get added.
