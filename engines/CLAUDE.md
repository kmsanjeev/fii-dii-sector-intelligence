# ENGINES DIRECTORY — CLAUDE CONTEXT

## DIRECTORY MAP WITH STATUS

```
engines/
├── common/              ← Shared utilities — ALWAYS import from here, never duplicate
├── acquisition/         ← NSE data downloaders (nselib-first)
│   ├── nse_equity_acquisition_engine.py      ✅ active
│   ├── nse_fno_acquisition_engine.py         ✅ active
│   └── nse_corporate_actions_acquisition_engine.py  ✅ active
├── foundation/          ← Index constituent management
│   └── nse_constituents_engine_v1.py         ✅ active (needs auto-download expansion)
├── fundamentals/        ← PHASE 4 — current build focus
│   ├── company_fundamentals_master_engine.py  🔴 IN PROGRESS — #1 priority
│   ├── industry_master_engine.py              🔴 blocked by above
│   ├── classification_engine_v4.py            🟡 active, incomplete
│   ├── security_master_engine_v2.py           ✅ active (v2 is canonical)
│   ├── security_master_engine.py              ❌ LEGACY — do not use or modify
│   ├── company_name_mapping_engine.py         ✅ active
│   ├── screener_classification_engine.py      ✅ validation layer only
│   └── theme_master_engine.py                 ✅ active
├── intelligence/        ← Phase 3 output engines
│   ├── index_intelligence_engine_v2.py        ❌ 80-line stub — do not use
│   └── leadership_persistence_engine_v2.py    ❌ 30-line stub — do not use
├── analytics/
│   └── price_adjustment_engine.py             ✅ active
├── classification/      ← EMPTY placeholder (content lives in fundamentals/)
├── corporate/           ← EMPTY placeholder (Phase 5)
├── management/          ← EMPTY placeholder (Phase 6)
├── orchestration/       ← EMPTY placeholder (future main.py evolution)
│
│   ── ROOT-LEVEL ENGINES (legacy flat placement) ──
├── bhavcopy_import_engine.py                  ✅ Phase 1 foundation
├── equity_master_engine.py                    ✅ Phase 1 foundation (148 lines)
├── cache_manager.py                           ✅ Phase 1 foundation
├── auto_classification_engine_v2.py           🟡 Phase 2 active (758 lines)
├── classification_engine.py                   ❌ LEGACY V1 — do not use
├── index_intelligence_engine.py               ✅ Phase 3 ACTIVE (221 lines)
├── index_intelligence_engine_v1_backup.py     ❌ BACKUP — do not use or modify
├── index_snapshot_engine.py                   ✅ Phase 3 active
├── index_taxonomy_engine.py                   ✅ Phase 3 active
└── sector_leadership_persistence_engine.py    ✅ Phase 3 active (316 lines)
```

## ENGINE TEMPLATE (mandatory structure for all new engines)

```python
"""
<Engine Name>
Phase <N> — <one-line purpose>
"""

from pathlib import Path
from engines.common.logger import get_logger
from engines.common import config as cfg

logger = get_logger(__name__)


class <EngineName>Engine:
    """<One-line description of what this engine produces>"""

    def __init__(self):
        self.output_dir = cfg.<RELEVANT_DIR>
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        logger.info(f"[{self.__class__.__name__}] Starting")
        try:
            self._validate_inputs()
            result = self._process()
            self._save(result)
            logger.info(f"[{self.__class__.__name__}] Complete — {len(result)} records")
            return True
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Failed: {e}")
            raise

    def _validate_inputs(self):
        """Verify all required source files exist before processing."""
        pass

    def _process(self) -> "pd.DataFrame":
        """Core transformation logic."""
        pass

    def _save(self, df: "pd.DataFrame"):
        """Write outputs. CSV always; Parquet if cfg.WRITE_PARQUET."""
        pass


if __name__ == "__main__":
    engine = <EngineName>Engine()
    engine.run()
```

## VALIDATION REQUIREMENTS (every engine must implement)
1. **Schema validation** — verify expected columns exist and have correct dtypes
2. **Completeness validation** — detect and log missing records / null key fields
3. **Integrity validation** — expected record count vs actual
4. **Recovery mechanism** — on failure: log, flag for retry, never silently skip

## IMPORT RULES
- Paths: always `from engines.common import config as cfg` then use `cfg.NSE_DIR` etc.
- Logging: always `from engines.common.logger import get_logger`
- NSE client: always `from engines.common.nse_client import NSEClient`
- Never hardcode paths. Never import from `fetchers/` in new engines.

## LISTING-DATE RULE (ADR-004)
Every engine processing per-symbol data must:
```python
listing_date = equity_master.loc[symbol, "listing_date"]
files = [f for f in bhavcopy_files if f.date >= listing_date]
```
Never process bhavcopy history before a stock's listing date.

## GUARDRAIL COMPLIANCE CHECKLIST (for every new engine before marking complete)
```
[ ] Schema validation on all writes (validate_schema())
[ ] Atomic writes — write to .tmp then shutil.move()
[ ] Empty DataFrame guard — check df.empty before write
[ ] EQ series filter — df = df[df["series"] == "EQ"]
[ ] Listing-date-aware file filtering
[ ] Market hours guard — no heavy batch during 09:15–15:30 IST
[ ] Retry with exponential backoff on all API calls
[ ] Recovery queue — failed items → NSE/recovery_queue.csv
[ ] No hardcoded paths — all via cfg.* constants
[ ] Score range enforcement (clip if applicable)
[ ] NaN propagation prevention — no fillna(0) on financial data
[ ] Environment variable guard at module startup
[ ] Log rotate — RotatingFileHandler(maxBytes=5MB, backupCount=5)
[ ] Stale data detection — flag if source data > 5 trading days old
```
Full guardrail specs: `docs/governance/GUARDRAILS.md`

## PERFORMANCE RULES
- Default concurrency: `cfg.MIN_CONCURRENCY` to `cfg.MAX_CONCURRENCY` (3–6 workers)
- Rate limit API calls: `cfg.API_DELAY` = 1.0s between requests
- Retry: `cfg.MAX_RETRIES` = 3, delay `cfg.RETRY_DELAY` = 3s
- Heavy rebuilds: after market hours or weekends only
