# SHEETS DIRECTORY — CLAUDE CONTEXT

## PURPOSE
Google Sheets integration layer. Writes intelligence outputs to shared spreadsheets
for human review and monitoring dashboards.

## ACTIVE FILES
| File | Purpose |
|------|---------|
| `google_sheet_updater.py` | Core Google Sheets API writer |
| `signal_sheet_updater.py` | Write signal outputs to designated sheet |
| `__init__.py` | Package init |

## GOOGLE SHEETS CONFIG (from root config.py)
```python
import json, os
GOOGLE_CREDS = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
SHEET_NAME   = "NSE_FII_DII_Sector_Intelligence"
TIMEZONE     = "Asia/Kolkata"
```
Credentials come from `GOOGLE_CREDENTIALS` env variable (JSON string).
NEVER commit Google credentials to git.

## USAGE PATTERN
```python
# Always import from config, not hardcoded
from config import GOOGLE_CREDS, SHEET_NAME
```

## SHEET UPDATE RULES
- Only update after market close (after 15:45 IST) to avoid mid-session noise
- Always write timestamp + data_date in the sheet header row
- Never clear existing sheet data before writing — use range-specific updates
- Handle API quota errors gracefully: retry with exponential backoff
- Log every sheet update to `logs/sheets.log`

## TIMEZONE RULE
All timestamps written to sheets must be IST (Asia/Kolkata).
```python
from datetime import datetime
import pytz
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist)
```

## PLANNED SHEET TABS (future)
```
Daily FII/DII Summary
Sector Heatmap (Weekly)
Sector Heatmap (BiWeekly)
Sector Heatmap (Monthly)
Theme Heatmap
Leadership Persistence
Institutional Trend
Bull Run Candidates  ← Phase 8
Stock Rankings       ← Phase 8
```

## RELATIONSHIP TO ALERTS
Sheets = persistent dashboard (humans check periodically).
Alerts (Telegram) = push notifications (time-sensitive signals).
Both consume the same intelligence data; neither generates it.
