"""Bounded real-provider validation for VEDA-MARKET-INTRADAY...-RX1.

The runner writes only sanitized metadata to the ignored intraday state file.
It never stores provider payloads, credentials or parquet samples in Git.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.intraday_foundation import (
    DhanIntradayProvider,
    InstrumentIdentity,
    IntradaySourceError,
    aggregate_candles,
    build_status,
)
from engines.providers.dhan_auth import DhanAuthError, DhanAuthManager


IST = ZoneInfo("Asia/Kolkata")


def _probe(name: str, operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = operation()
        result: dict[str, Any] = {"state": "PASS", "type": type(value).__name__}
        if isinstance(value, list):
            result["rows"] = len(value)
            if value:
                result["first_timestamp"] = value[0].get("bar_start")
                result["last_timestamp"] = value[-1].get("bar_start")
                result["quality_flag_rows"] = sum(bool(row.get("quality_flags")) for row in value)
        return {"name": name, **result}
    except IntradaySourceError as exc:
        return {"name": name, "state": "BLOCKED", "code": str(exc)}
    except Exception as exc:  # diagnostic classification only; no raw provider body
        return {"name": name, "state": "FAIL", "code": type(exc).__name__}


def main() -> int:
    manager = DhanAuthManager()
    now = datetime.now(IST).isoformat()
    state: dict[str, Any] = {
        "provider": "dhan",
        "validated_at": now,
        "authenticated": False,
        "runtime_health": "UNKNOWN",
        "data_plan": "UNKNOWN",
        "validated_capabilities": [],
        "capability_results": {},
        "market_session": "WEEKEND_OR_CLOSED_VALIDATION_WINDOW",
        "orders_called": False,
        "fallback_used": "NONE",
    }
    try:
        manager = DhanAuthManager.from_environment()
        token = manager.ensure_valid_token()
        profile = manager.profile()
        state.update(
            {
                "authenticated": True,
                "token_expires_at": token.expires_at.isoformat(),
                "data_plan": profile["data_plan"].upper(),
                "active_segment": profile["active_segment"],
                "data_validity": profile["data_validity"],
            }
        )
    except DhanAuthError as exc:
        state.update({"auth_error": exc.code, "runtime_health": "AUTH_FAILED"})
        manager.write_validation_state(state)
        print(json.dumps(state, indent=2, sort_keys=True))
        return 2

    provider = DhanIntradayProvider(auth_manager=manager)
    equity = InstrumentIdentity("2885", "NSE", "NSE_EQ", "EQUITY", "RELIANCE", provider_instrument_type="EQUITY")
    future = InstrumentIdentity(
        "58072", "NSE", "NSE_FNO", "FUTURE", "NIFTY-AUG2026-FUT",
        provider_instrument_type="FUTIDX", underlying="NIFTY", expiry="2026-08-25",
    )
    index = InstrumentIdentity("13", "NSE", "IDX_I", "INDEX", "NIFTY", provider_instrument_type="INDEX")

    probes = [
        _probe("historical_equity_1m_recent", lambda: provider.historical_candles(equity, 1, "2026-08-20", "2026-08-21")),
        _probe("historical_equity_5m_recent", lambda: provider.historical_candles(equity, 5, "2026-08-20", "2026-08-21")),
        _probe("historical_equity_15m_recent", lambda: provider.historical_candles(equity, 15, "2026-08-20", "2026-08-21")),
        _probe("historical_equity_1m_older", lambda: provider.historical_candles(equity, 1, "2026-07-31", "2026-08-01")),
        _probe("historical_futures_1m_oi", lambda: provider.historical_candles(future, 1, "2026-08-20", "2026-08-21", oi=True)),
        _probe("market_quote_batch", lambda: provider.quote([equity, index])),
        _probe("option_chain_nifty", lambda: provider.option_chain(index, "2026-08-25")),
    ]
    state["probes"] = probes
    passed = {item["name"] for item in probes if item["state"] == "PASS"}
    state["validated_capabilities"] = sorted(
        {"INTRADAY_HISTORY" if name.startswith("historical_equity") else "FUTURES_OI" if "futures" in name else "LIVE_QUOTE" if "quote" in name else "OPTION_CHAIN" for name in passed}
    )
    state["runtime_health"] = "HEALTHY" if passed else "ENTITLEMENT_BLOCKED" if state["data_plan"] != "ACTIVE" else "SOURCE_FAILED"
    state["aggregation"] = {"one_minute_to_five_minute": "NOT_RUN" if not passed else "VALIDATE_WITH_REAL_ROWS", "oi_summed": False}
    state["live_stream"] = "LIVE_SESSION_VALIDATION_PENDING" if state["data_plan"] != "ACTIVE" else "NOT_RUN"
    state["status_contract"] = build_status(provider)
    manager.write_validation_state(state)
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if state["runtime_health"] in {"HEALTHY", "ENTITLEMENT_BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
