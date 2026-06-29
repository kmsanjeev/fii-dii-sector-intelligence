# Module 09 — Alert System
## Phase 9A/9B/9C/9D/9E Complete | 2026-06-30

---

## What Was Built

### Phase 9A — alert_engine.py
File: alerts/alert_engine.py

Evaluates all 6 intelligence CSVs and emits Alert dataclass objects by priority.
Read-only consumer — never modifies intelligence files.

7 alert types (evaluated in priority order):
- P1 REGIME_CHANGE: compares current Market_Regime vs stored previous_regime (no cooldown)
- P2 STRONG_CANDIDATE: bull_run_score >= 65 from bull_run_probability.csv
- P3 SECTOR_ROTATION: rotation_signal == EARLY_ROTATION from sector_rotation_intelligence.csv
- P4 INSTITUTIONAL_DEAL: inst_net_value_cr >= 50 Cr from institutional_deal_signals.csv
- P5 CORPORATE_CONFIDENCE: confidence_score_12m >= 2.0 from corporate_confidence_scores.csv
- P6 PARTICIPANT_DIVERGENCE: abs(FII_DII_Divergence) >= 2.0 sigma from participant_intelligence.csv
- P7 DAILY_DIGEST: handled by daily_digest.py + alert_store cooldown

Alert dataclass:
  alert_type, priority, title, body, symbol, sector, score, data_date, created_at
  .telegram_text() formats for plain-text Telegram delivery

Run result (2026-06-30):
  Previous regime: DISTRIBUTION -> Current: NEUTRAL -> P1 fires
  117 raw alerts: P3=1, P4=20 deals, P5=95 corporate confidence, P6=1 divergence

### Phase 9B — alert_store.py
File: alerts/alert_store.py

Tracks sent alerts in data/intelligence/alert_state.json.
Enforces per-(symbol+type) cooldown windows.
Atomic writes (.tmp -> rename) per G-D-02.

Cooldown by type:
  REGIME_CHANGE=0h (always fire), STRONG_CANDIDATE=72h, SECTOR_ROTATION=48h
  INSTITUTIONAL_DEAL=48h, CORPORATE_CONFIDENCE=48h, PARTICIPANT_DIVERGENCE=48h
  DAILY_DIGEST=24h

filter_eligible(alerts): returns only alerts not within cooldown
mark_sent(alert): stamps the cooldown key with current timestamp
get_previous_regime() / set_current_regime(): persist regime for P1 detection

### Phase 9C — telegram_bot.py (rewritten)
File: alerts/telegram_bot.py

Full Telegram Bot API integration (replaces old stub using requests directly).
Credentials from os.getenv() — NEVER hardcoded.
HTML parse_mode with named icons per priority level ([!!], [**], [>>], etc.)

Functions:
  send_message(text, parse_mode="HTML") -> bool
  send_alerts(alerts: list) -> int (count sent)
  send_raw(text: str) -> bool
  test_connection() -> bool

100ms sleep between batch sends to respect Telegram 30msg/s rate limit.

### Phase 9D — daily_digest.py
File: alerts/daily_digest.py

Builds the 18:30 IST daily intelligence summary in HTML format.
5 sections: Market Regime, Participant Flows, Sector Signals, Watchlist Top 5, Deals.

Sample output (2026-06-30):
  MARKET REGIME: NEUTRAL
  Smart Money Score: -4.7 | FII Conviction: 40%
  FII: +10.9 | DII: -4.5 | PRO: -20.2 | CLIENT: +9.4
  EARLY_ROTATION: MEDIA
  Top EMERGING: ADANIENSOL 62, ADANIENT 57, GMRAIRPORT 56, CRAFTSMAN 54, EMCURE 54
  Top Deals: ADANIENT BUY 4790 Cr [MF], LENSKART BUY 3511 Cr, LODHA BUY 2758 Cr
  Total: 690 chars

### Phase 9E — alert_scheduler.py
File: alerts/alert_scheduler.py

APScheduler BlockingScheduler with Asia/Kolkata timezone.
Jobs:
  - daily_digest: CronTrigger(hour=18, minute=30) -> run_daily_digest()
  - alert_cycle: CronTrigger(day_of_week=mon-fri, hour=16-22, minute=0,30) -> run_alert_cycle()
  
Market hours guard (G-A-04): run_alert_cycle() exits if 09:15-15:30 IST.
Checks TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID at startup (G-SYS-01).

Usage: py -3.11 alerts/alert_scheduler.py

---

## Packages Installed

APScheduler==3.11.3
python-telegram-bot==21.11.1

---

## ADR Created

ADR-021-Alert-System-Architecture.md (docs/decisions/)
- 7 alert types with priority/cooldown table
- Design principles: atomic writes, env-only credentials, no stale data
- Related: ADR-010 (AI-first UX), ADR-016 (Participant), ADR-020 (Corporate)

---

## Test Results

alert_engine.py: 118 alerts on first run (regime=DISTRIBUTION->NEUTRAL + P3/P4/P5/P6)
alert_store.py: cooldown filter works, fresh store passes all eligible
daily_digest.py: 690-char HTML digest with all 5 sections populated
alert_scheduler.py: imports verified, APScheduler init OK

---

## Next Steps

Phase 10 — FastAPI Backend:
  backend/main.py + routers + services/data_loader.py + ws/live_ticker.py
  py -3.11 -m pip install fastapi uvicorn[standard]
