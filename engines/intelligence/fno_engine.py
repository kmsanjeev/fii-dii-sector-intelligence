"""F&O intelligence stage backed by the governed F&O projection."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services.governed_fno_intelligence import (
    FNO_DIR,
    build_governed_fno_intelligence,
)
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)
FNO_OUTPUT = cfg.INTELLIGENCE_DIR / "fno_intelligence.csv"
CTX_OUTPUT = cfg.INTELLIGENCE_DIR / "market_context.json"


def _write_atomic(path: Path, payload: str, suffix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".tmp{suffix}")
    temporary.write_text(payload, encoding="utf-8")
    shutil.move(str(temporary), str(path))


def run() -> dict:
    result = build_governed_fno_intelligence(fno_dir=FNO_DIR)
    if result.get("status") != "AVAILABLE":
        return {"status": "ERROR", "error": "No F&O CSV files found"}

    records = result.get("futures", [])
    if records:
        import pandas as pd

        _write_atomic(FNO_OUTPUT, pd.DataFrame(records).to_csv(index=False), ".csv")
        logger.info("[FNO] Saved %d governed futures records", len(records))

    stock_pcr = result.get("pcr", {}).get("stock_options_oi", {})
    legacy_pcr = stock_pcr.get("pcr_oi") if isinstance(stock_pcr, dict) else None
    context = {
        # Compatibility fields retain their historical names but carry explicit
        # semantics so consumers cannot mistake stock-option PCR for market PCR.
        "trade_date": result.get("as_of_date", ""),
        "pcr": legacy_pcr,
        "pcr_signal": "UNINTERPRETED",
        "calls_oi": stock_pcr.get("call_oi") if isinstance(stock_pcr, dict) else None,
        "puts_oi": stock_pcr.get("put_oi") if isinstance(stock_pcr, dict) else None,
        "pcr_semantics": "AGGREGATE_STOCK_OPTION_OI_PCR_ALL_ACTIVE_EXPIRIES",
        "fno_contract_version": result.get("contract_version"),
        "data_status": result.get("data_status", {}),
        "index_options_pcr": result.get("pcr", {}).get("index_options_oi", {}),
        "limitations": result.get("limitations", []),
    }
    _write_atomic(CTX_OUTPUT, json.dumps(context, indent=2), ".json")
    logger.info("[FNO] Context saved: stock-option PCR=%s (descriptive only)", legacy_pcr)
    return {
        "status": "DONE",
        "symbols": len(records),
        "pcr": legacy_pcr,
        "trade_date": result.get("as_of_date", ""),
        "contract_version": result.get("contract_version"),
    }


if __name__ == "__main__":
    outcome = run()
    print(f"Status:  {outcome['status']}")
    print(f"Symbols: {outcome.get('symbols', 0)}")
    print(f"PCR:     {outcome.get('pcr')}")
    print(f"Date:    {outcome.get('trade_date', '')}")
    if outcome.get("error"):
        print(f"Error:   {outcome['error']}")
