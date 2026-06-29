# ADR-021 — Alert System Architecture
Status: Accepted
Date: 2026-06-30

## Context

The Capital Flow Intelligence Platform generates 16 intelligence CSVs daily covering
market regime, sector rotation, institutional deals, corporate confidence, and bull run
probability. Currently there is no mechanism to proactively deliver these signals to the user.

The user needs to be notified when:
- Market regime changes (highest priority — affects all downstream scores)
- A stock enters STRONG_CANDIDATE or EMERGING territory for the first time
- A sector flips to EARLY_ROTATION
- A significant institutional deal appears (>50 Cr net in 30D)
- A company's corporate confidence score crosses +2.0
- FII/CLIENT divergence reaches extreme levels

Without an alert layer, intelligence value decays as the user must manually check CSVs.

## Decision

Build a Telegram-based alert system (Phase 9) with:

1. **alert_engine.py** — evaluates all intelligence CSVs against 7 alert types, emits
   alert objects with priority, symbol, message, and data source metadata

2. **alert_store.py** — persists sent alerts to data/intelligence/alert_state.json,
   enforces per-(symbol+type) cooldown windows, prevents duplicate delivery

3. **telegram_bot.py** — formats alert objects into Telegram messages and delivers them
   via python-telegram-bot v21; also handles /status, /watchlist, /regime slash commands

4. **daily_digest.py** — builds a structured 18:30 IST daily summary combining all
   intelligence layers into one Telegram message

5. **alert_scheduler.py** — APScheduler CronJob: digest at 18:30 IST, alert checks
   every 30 minutes post-market (16:00-22:00 IST), no checks during market hours

## Alert Priority Order

| Priority | Type | Cooldown |
|----------|------|---------|
| P1 | REGIME_CHANGE | None (always fire) |
| P2 | STRONG_CANDIDATE | 72h per symbol |
| P3 | SECTOR_ROTATION | 48h per sector |
| P4 | INSTITUTIONAL_DEAL | 48h per symbol |
| P5 | CORPORATE_CONFIDENCE | 48h per symbol |
| P6 | PARTICIPANT_DIVERGENCE | 48h |
| P7 | DAILY_DIGEST | 24h |

## Consequences

**Positive:**
- User receives proactive signal delivery without polling CSVs
- Priority ordering prevents lower-priority signals from flooding during regime changes
- Cooldown windows prevent alert fatigue
- ADR-010 (AI-first UX) satisfied: push intelligence to user before they ask

**Negative:**
- Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment
- Scheduler adds background process requirement (APScheduler)
- Alert state file must be backed up or re-derivable if lost

## Implementation Notes

- TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID: always from os.getenv() — never hardcoded
- Alert state: data/intelligence/alert_state.json — atomic writes only (.tmp -> rename)
- All intelligence CSVs are read-only in the alert layer
- Market hours guard (G-A-04): no alert evaluation during 09:15-15:30 IST
- Windows cp1252: never use Unicode chars in print() statements

## Related ADRs

- ADR-010 — AI-First User Experience (push signals, not pull)
- ADR-016 — Participant Intelligence Framework (regime source)
- ADR-020 — Corporate Intelligence Layer (confidence score source)
