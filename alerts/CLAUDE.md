# ALERTS DIRECTORY — CLAUDE CONTEXT

## PURPOSE
Delivery layer for intelligence signals via Telegram and (future) other channels.
This is a consumer of intelligence — it never generates signals itself.

## ACTIVE FILES
| File | Purpose |
|------|---------|
| `telegram_bot.py` | Telegram alert delivery |
| `__init__.py` | Package init |

## TELEGRAM BOT CONFIG (from root config.py)
```python
import os
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
```
Both values come from environment variables — NEVER hardcode credentials in source.

## ALERT DESIGN PRINCIPLES (ADR-010 + ADR-011)
- Alerts must be concise — one clear signal per message
- Include: what changed, direction, strength, timestamp
- Never send duplicate alerts for the same signal on the same day
- Never alert during market hours on stale data (check data_date vs today)
- Log every alert sent to `logs/alerts.log` with timestamp

## ALERT CATEGORIES (planned)
```
MARKET REGIME CHANGE    → FII/DII regime shifts (accumulation ↔ distribution)
SECTOR LEADERSHIP       → New sector entering top 3 leadership
SECTOR EXIT             → Sector dropping out of top 3
THEME EMERGENCE         → Theme showing accelerating momentum
INSTITUTIONAL ALERT     → Unusual institutional positioning change
BULL RUN SIGNAL         → Stock entering high bull_run_probability zone (Phase 8)
```

## RATE LIMITING
Telegram has a 30 messages/second limit per bot.
For batch alerts (sector heatmap, daily report): use message queuing with 100ms delay.
```python
import time
for alert in alerts:
    send_telegram(alert)
    time.sleep(0.1)
```

## FUTURE CHANNELS (planned, do not build yet)
- Email alerts (Phase 9)
- Push notifications via mobile app (Phase 9+)
- Dashboard real-time alerts (Phase 9+)

## GOOGLE SHEETS INTEGRATION
Separate from alerts — see `sheets/` directory.
Alert = push notification. Sheet = persistent dashboard.
