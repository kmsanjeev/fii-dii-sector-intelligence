# ENGINES/COMMON — CLAUDE CONTEXT

## PURPOSE
Shared infrastructure for all engines. Never duplicate what exists here.
All engines in this project MUST import from `engines.common` — never re-implement.

## MODULE REFERENCE CARD

| Module | Import | Purpose |
|--------|--------|---------|
| `config.py` | `from engines.common import config as cfg` | All path constants (DATA_DIR, NSE_DIR, etc.) |
| `logger.py` | `from engines.common.logger import get_logger` | Structured file logger |
| `constants.py` | `from engines.common.constants import <NAME>` | Domain constants |
| `filesystem.py` | `from engines.common.filesystem import <fn>` | Path utilities |
| `holiday_engine.py` | `from engines.common.holiday_engine import HolidayEngine` | NSE trading calendar |
| `nse_client.py` | `from engines.common.nse_client import NSEClient` | nselib wrapper |
| `progress.py` | `from engines.common.progress import ProgressReporter` | Progress tracking |
| `recovery.py` | `from engines.common.recovery import RecoveryManager` | Error recovery |
| `registry.py` | `from engines.common.registry import EngineRegistry` | Engine inventory |
| `validators.py` | `from engines.common.validators import validate_schema` | Data validation |

## KEY CONFIG CONSTANTS (use these, never hardcode paths)

```python
from engines.common import config as cfg

cfg.PROJECT_ROOT                 # repo root
cfg.DATA_DIR                     # data/
cfg.NSE_DIR                      # data/NSE/
cfg.BSE_DIR                      # data/BSE/ (future)
cfg.CACHE_DIR                    # data/cache/
cfg.REFERENCE_DIR                # data/reference/
cfg.INTELLIGENCE_DIR             # data/intelligence/

cfg.BHAVCOPY_DIR                 # data/NSE/bhavcopy/
cfg.NSE_EQUITY_BHAVCOPY_DIR      # data/NSE/bhavcopy/equity/
cfg.NSE_FNO_BHAVCOPY_DIR         # data/NSE/bhavcopy/fno/

cfg.INDICES_DIR                  # data/NSE/indices/
cfg.EQUITY_MASTER_DIR            # data/NSE/equity_master/
cfg.CORPORATE_ACTIONS_DIR        # data/NSE/corporate_actions/
cfg.RESULTS_DIR                  # data/NSE/results/
cfg.SHAREHOLDING_DIR             # data/NSE/shareholding/

cfg.STOCK_HISTORY_CACHE          # data/cache/stock_history/
cfg.NSE_HOLIDAY_FILE             # data/reference/nse_holidays.csv
cfg.LOG_DIR                      # logs/

# Runtime settings
cfg.NSE_EQUITY_START_YEAR        # 1995
cfg.NSE_FNO_START_YEAR           # 2000
cfg.MIN_CONCURRENCY              # 3
cfg.MAX_CONCURRENCY              # 6
cfg.WRITE_CSV                    # True
cfg.WRITE_PARQUET                # True
cfg.API_TIMEOUT                  # 30
cfg.API_DELAY                    # 1.0
cfg.MAX_RETRIES                  # 3
cfg.RETRY_DELAY                  # 3
```

## LOGGER USAGE
```python
from engines.common.logger import get_logger
logger = get_logger(__name__)

# Use these levels:
logger.info("Started processing 2123 symbols")
logger.warning("Symbol ADANIPORTS: no industry match, using fallback")
logger.error("Failed to download bhavcopy for 2026-06-28: timeout")
```
Logger writes to `logs/<module_name>.log` automatically.

## HOLIDAY ENGINE USAGE
```python
from engines.common.holiday_engine import HolidayEngine
holidays = HolidayEngine()
trading_days = holidays.get_trading_days(start="2024-01-01", end="2024-12-31")
is_trading = holidays.is_trading_day("2024-01-15")
```

## VALIDATORS USAGE
```python
from engines.common.validators import validate_schema
# Raises ValueError if schema doesn't match
validate_schema(df, required_columns=["symbol", "isin", "listing_date"])
```

## ADDING TO COMMON
Only add to `engines/common/` if the utility is needed by 3+ engines.
Single-engine utilities stay in that engine's file.
Never add business logic to common — only infrastructure.
