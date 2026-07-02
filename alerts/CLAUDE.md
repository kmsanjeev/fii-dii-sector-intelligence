# ALERTS DIRECTORY — CLAUDE CONTEXT

## PURPOSE
Delivery layer for intelligence signals via Telegram.
This is a consumer of intelligence — it never generates signals itself.
Phase 9 of the Capital Flow Intelligence Platform.

## STATUS: PHASE 9 — IN PROGRESS

Build order:
  9A: alert_engine.py (signal evaluation, 7 alert types)
  9B: alert_store.py (cooldown, dedup, JSON state)
  9C: telegram_bot.py (send + format, enhance existing stub)
  9D: daily_digest.py (18:30 IST market summary)
  9E: alert_scheduler.py (APScheduler: digest + periodic checks)

## ACTIVE FILES

| File | Purpose | Status |
|------|---------|--------|
| telegram_bot.py | Telegram alert delivery (stub) | EXISTS — needs full implementation in 9C |
| __init__.py | Package init | EXISTS |

## PHASE 9 TARGET FILES

| File | Purpose |
|------|---------|
| alert_engine.py | Evaluate intelligence CSVs, emit alerts by priority |
| alert_store.py | Track sent alerts, enforce cooldown, dedup by symbol+type |
| telegram_bot.py | Format + send Telegram messages, /commands |
| daily_digest.py | Build 18:30 IST daily summary from all intelligence layers |
| alert_scheduler.py | APScheduler: digest at 18:30, checks every 30 min post-market |

## TELEGRAM BOT CONFIG (from environment — NEVER hardcode)

```python
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
```

## 7 ALERT TYPES (priority order)

| Priority | Type | Trigger | Cooldown |
|----------|------|---------|---------|
| P1 | REGIME_CHANGE | Market_Regime flips (e.g. NEUTRAL->DISTRIBUTION) | None |
| P2 | STRONG_CANDIDATE | bull_run_score >= 65 (first time) | 72h |
| P3 | SECTOR_ROTATION | Sector rotation_signal flips to EARLY_ROTATION | 48h |
| P4 | INSTITUTIONAL_DEAL | inst_net_value_cr > 50 Cr in 30D | 48h |
| P5 | CORPORATE_CONFIDENCE | confidence_score_12m crosses +2.0 | 48h |
| P6 | PARTICIPANT_DIVERGENCE | FII vs CLIENT divergence > 2 sigma | 48h |
| P7 | DAILY_DIGEST | 18:30 IST scheduled summary | 24h |
| P8 | ANNOUNCEMENT_MOMENTUM | Confluence/order-win momentum on pre-discovery stocks | 48h |
| P9 | TRADE_CONVICTION | trade_conviction_scores.csv action in {STRONG_BUY, EXIT_AVOID} | 72h |
| P10 | OI_SIGNAL_FLIP | F&O oi_signal LONG/SHORT_BUILDUP with >=15% day OI change (top 10) | 48h |

## ALERT DESIGN PRINCIPLES (ADR-010 + ADR-011)

- One clear signal per message
- Include: what changed, direction, strength, timestamp, data freshness
- Never send duplicate alerts for the same signal within cooldown window
- Never alert on stale data (check data_date vs today, max 2 trading days lag)
- Log every alert sent to logs/alerts.log with timestamp and message_id

## RATE LIMITING

Telegram limit: 30 messages/second per bot.
Batch alerts: use 100ms delay between sends.
```python
import time
for alert in alerts:
    send_telegram(alert)
    time.sleep(0.1)
```

## INTELLIGENCE INPUTS (read-only CSVs — never modify)

| File | Used By | Signal |
|------|---------|--------|
| participant_intelligence.csv | alert_engine | Regime change (P1) |
| bull_run_watchlist.csv | alert_engine | Strong candidates (P2) |
| sector_rotation_intelligence.csv | alert_engine | Sector rotation (P3) |
| institutional_deal_signals.csv | alert_engine | Institutional deals (P4) |
| corporate_confidence_scores.csv | alert_engine | Corporate confidence (P5) |
| participant_flow_scores.csv | alert_engine | Participant divergence (P6) |
| company_announcements.csv | alert_engine | Announcement momentum (P8) |
| trade_conviction_scores.csv | alert_engine | Trade conviction (P9) |
| fno_intelligence.csv | alert_engine | OI signal flip (P10) |

## PACKAGES REQUIRED

py -3.11 -m pip install "python-telegram-bot==21.*" "APScheduler==3.*"

## GUARDRAILS

- G-SYS-01: Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID at module startup
- G-D-03: Never send alert from empty DataFrame
- G-I-04: Never fillna(0) on financial fields before alert evaluation
- Alert store must use atomic writes (write .tmp, then rename)
- Cooldown state file: data/intelligence/alert_state.json
