# ENGINES/ACQUISITION — CLAUDE CONTEXT

## PURPOSE
Data downloaders for NSE raw data. These are the entry point of the data pipeline.
All raw data produced here is IMMUTABLE once written (ADR-001).

## ACTIVE ENGINES

| Engine | Purpose | Output |
|--------|---------|--------|
| `nse_equity_acquisition_engine.py` | Download equity bhavcopy | `data/NSE/bhavcopy/equity/YYYY/bhavcopy_YYYYMMDD.csv` |
| `nse_fno_acquisition_engine.py` | Download F&O bhavcopy | `data/NSE/bhavcopy/fno/YYYY/` |
| `nse_corporate_actions_acquisition_engine.py` | Download corporate actions | `data/NSE/corporate_actions/` |

## DATA SOURCE POLICY (ADR-005 — nselib First)
```
1. nselib                  ← ALWAYS try first
2. NSE API (direct)        ← fallback if nselib fails
3. Alternative sources     ← secondary fallback
4. yFinance                ← LAST RESORT only
```
Document the fallback reason in the log when nselib is not used.

## FILE NAMING STANDARDS (ADR-002)
```
Equity bhavcopy:   bhavcopy_YYYYMMDD.csv
F&O bhavcopy:      fno_bhavcopy_YYYYMMDD.csv
```
Filenames are the date index. Never deviate from this format.

## RAW DATA RULES (ADR-001)
- Never overwrite an existing bhavcopy file
- Never modify a downloaded bhavcopy file post-download
- If a file is corrupted: flag it, download fresh, keep original with `.corrupted` suffix
- Downloads are idempotent: skip if file already exists and passes hash check

## BHAVCOPY PATH NOTE
The config (`engines/common/config.py`) writes bhavcopy to `data/NSE/bhavcopy/equity/`.
Historical bhavcopy (1995–2026) currently lives at `data/bhavcopy/equity/` (old path).
When building new acquisition logic, always target `cfg.NSE_EQUITY_BHAVCOPY_DIR`.
Do NOT read from `data/bhavcopy/` in new engines — that directory is legacy.

## RECOVERY PATTERN (required for all acquisition engines)
```python
for date in missing_dates:
    try:
        data = nse_client.download(date)
        save(data, path)
        logger.info(f"Downloaded {date}")
    except Exception as e:
        logger.error(f"Failed {date}: {e}")
        failed_dates.append(date)
        continue   # never break the loop on single failure

# After loop: write failed_dates to a recovery queue CSV
save_recovery_queue(failed_dates, cfg.NSE_DIR / "bhavcopy_recovery_queue.csv")
```

## INTEGRITY VALIDATION (every acquisition engine must support)
After download run:
1. Expected file count vs actual file count
2. Schema check (expected columns present)
3. Record count vs expected range
4. Missing date gap detection vs NSE trading calendar

## FUTURE ACQUISITIONS (Phase 4-6, planned)
- `nse_results_acquisition_engine.py` → `data/NSE/results/`
- `nse_shareholding_acquisition_engine.py` → `data/NSE/shareholding/`
- `nse_announcements_acquisition_engine.py` → `data/NSE/announcements/`
- `nse_concall_acquisition_engine.py` → `data/NSE/corporate/call_recordings/`

These must NOT be built until Company Fundamentals Master Engine is complete.
