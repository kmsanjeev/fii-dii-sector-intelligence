# STORAGE DIRECTORY — CLAUDE CONTEXT

## PURPOSE
Persistence managers for institutional data. These wrap file I/O with
validation, schema enforcement, and atomic write guarantees.

## ACTIVE FILES
| File | Purpose |
|------|---------|
| `fii_dii_history_manager.py` | Read/write FII-DII cash flow history |
| `institutional_history_manager.py` | Read/write full institutional positioning history |

## STORAGE DESIGN PRINCIPLES
These managers implement the interface between intelligence engines and the data layer.
They enforce:
1. Schema validation on every write
2. Atomic writes (write to temp file, rename — never partial writes)
3. Duplicate date detection (do not append if date already exists)
4. Sorted output (always sort by date ascending before saving)

## ATOMIC WRITE PATTERN (required for all storage managers)
```python
import tempfile, shutil
from pathlib import Path

def safe_write(df: pd.DataFrame, target: Path):
    """Write atomically to prevent partial files on crash."""
    tmp = target.with_suffix(".tmp")
    df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(target))
```
Never write directly to the final path — always use a `.tmp` intermediary.

## SCHEMA ENFORCEMENT
```python
REQUIRED_COLUMNS = ["date", "fii_buy", "fii_sell", "fii_net", "dii_buy", "dii_sell", "dii_net"]

def validate_before_write(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Schema violation: missing columns {missing}")
```

## DUPLICATE DETECTION
```python
def append_new_rows(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    existing_dates = set(existing["date"])
    fresh = new[~new["date"].isin(existing_dates)]
    if fresh.empty:
        logger.info("No new dates to append")
        return existing
    return pd.concat([existing, fresh]).sort_values("date").reset_index(drop=True)
```

## DATA LOCATIONS
```python
# FII/DII cash flow
data/historical/fii_dii/fii_dii_history.csv

# Full institutional positioning (OI, Volume, Derivatives)
data/historical/institutional/institutional_positioning_history.csv
```

## FUTURE STORAGE MANAGERS (Phase 4+)
```
company_fundamentals_store.py      ← company_fundamentals_master.csv
results_history_store.py           ← financial results time series
shareholding_history_store.py      ← quarterly shareholding changes
sector_intelligence_store.py       ← sector heatmaps and scores
stock_history_store.py             ← per-symbol OHLCV with metadata
```
