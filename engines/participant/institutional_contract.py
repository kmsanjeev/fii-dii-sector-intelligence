"""Deterministic institutional-flow contract built from existing participant files.

This module is deliberately a read/derive layer.  It does not fetch data, score
predictions, or create a second participant engine.  The raw F&O and cash
histories remain the source of truth; missing values stay missing and every
window carries an explicit completeness state.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

WINDOWS = (1, 3, 5, 10, 20)
FNO_PARTICIPANTS = ("FII", "DII", "PRO", "CLIENT")
CASH_PARTICIPANTS = ("FPI", "MF", "INSURANCE", "RETAIL")


def _number(value: Any, decimals: int = 2) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return round(number, decimals)


def _latest_row(df: pd.DataFrame | None) -> pd.Series | None:
    if df is None or df.empty or "date" not in df.columns:
        return None
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"]).sort_values("date")
    return work.iloc[-1] if not work.empty else None


def _window_snapshot(series: pd.Series, windows: tuple[int, ...] = WINDOWS) -> dict[str, dict[str, Any]]:
    """Return rolling sums and completeness without converting missing to zero."""
    values = pd.to_numeric(series, errors="coerce").reset_index(drop=True)
    available = values.notna().astype(int)
    result: dict[str, dict[str, Any]] = {}
    for window in windows:
        sums = values.rolling(window, min_periods=1).sum()
        observed = available.rolling(window, min_periods=1).sum()
        expected = pd.Series(
            [min(window, index + 1) for index in range(len(values))],
            dtype="int64",
        )
        current_sum = sums.iloc[-1] if len(sums) else np.nan
        current_observed = int(observed.iloc[-1]) if len(observed) else 0
        current_expected = int(expected.iloc[-1]) if len(expected) else 0
        if current_observed == 0:
            state = "UNAVAILABLE"
        elif current_observed < current_expected:
            state = "PARTIAL"
        else:
            state = "COMPLETE"
        result[f"{window}D"] = {
            "value": _number(current_sum),
            "observations": current_observed,
            "expected_observations": current_expected,
            "coverage": round(current_observed / current_expected, 3) if current_expected else 0.0,
            "state": state,
        }
    return result


def _sign(value: Any) -> int | None:
    number = _number(value, 6)
    if number is None:
        return None
    return 1 if number > 0 else -1 if number < 0 else 0


def _participant_snapshot(flows: pd.DataFrame, participant: str) -> dict[str, Any]:
    row = _latest_row(flows)
    result: dict[str, Any] = {
        "oi_net": _number(row.get(f"{participant}_OI_Net")) if row is not None else None,
        "volume_net": _number(row.get(f"{participant}_Volume_Net")) if row is not None else None,
        "flow_score": _number(row.get(f"{participant}_flow_score")) if row is not None else None,
        "oi_delta_1d": _number(row.get(f"{participant}_OI_Delta")) if row is not None else None,
        "windows": {},
        "persistence_20d": None,
        "acceleration_5d": None,
        "reversal_5d": None,
    }
    if flows.empty:
        return result
    delta_col = f"{participant}_OI_Delta"
    if delta_col in flows.columns:
        delta = pd.to_numeric(flows[delta_col], errors="coerce")
    else:
        # Keep the contract usable with the raw history alone.
        delta = pd.to_numeric(flows.get(f"{participant}_OI_Net", pd.Series(dtype=float)), errors="coerce").diff()
    result["windows"] = _window_snapshot(delta)
    usable = delta.dropna()
    if not usable.empty:
        result["persistence_20d"] = _number((usable.tail(20) > 0).mean() * 100, 1)
    five = result["windows"].get("5D", {})
    current = five.get("value")
    if len(delta.dropna()) >= 2:
        prior_values = delta.iloc[:-1]
        prior = _window_snapshot(prior_values).get("5D", {}).get("value")
        if current is not None and prior is not None:
            result["acceleration_5d"] = _number(current - prior)
            current_sign = _sign(current)
            prior_sign = _sign(prior)
            result["reversal_5d"] = bool(current_sign and prior_sign and current_sign != prior_sign)
    return result


def _cash_snapshot(flows: pd.DataFrame, participant: str) -> dict[str, Any]:
    net_col = f"{participant}_net_cr"
    series = pd.to_numeric(flows.get(net_col, pd.Series(dtype=float)), errors="coerce")
    row = _latest_row(flows)
    return {
        "net_cr": _number(row.get(net_col), 2) if row is not None else None,
        "windows": _window_snapshot(series),
        "source_date": (
            str(pd.to_datetime(flows.loc[series.notna(), "date"], errors="coerce").max().date())
            if "date" in flows.columns and series.notna().any()
            else None
        ),
    }


def _quality(flows: pd.DataFrame, intelligence: pd.DataFrame, status: dict[str, Any]) -> dict[str, Any]:
    flow_date = _latest_row(flows)
    intel_date = _latest_row(intelligence)
    cash_dates = []
    for participant in CASH_PARTICIPANTS:
        col = f"{participant}_net_cr"
        if col in flows.columns:
            dates = pd.to_datetime(flows.loc[pd.to_numeric(flows[col], errors="coerce").notna(), "date"], errors="coerce")
            if not dates.dropna().empty:
                cash_dates.append(dates.max())
    source_dates = {
        "fno": str(flow_date["date"].date()) if flow_date is not None else None,
        "cash": str(max(cash_dates).date()) if cash_dates else None,
        "intelligence": str(intel_date["date"].date()) if intel_date is not None else None,
    }
    partial_windows = 0
    unavailable_windows = 0
    for participant in FNO_PARTICIPANTS:
        for window in _participant_snapshot(flows, participant)["windows"].values():
            partial_windows += window["state"] == "PARTIAL"
            unavailable_windows += window["state"] == "UNAVAILABLE"
    for participant in CASH_PARTICIPANTS:
        for window in _cash_snapshot(flows, participant)["windows"].values():
            partial_windows += window["state"] == "PARTIAL"
            unavailable_windows += window["state"] == "UNAVAILABLE"
    if flow_date is None or intel_date is None:
        quality = "UNAVAILABLE"
    elif unavailable_windows:
        quality = "LIMITED"
    elif partial_windows:
        quality = "CONDITIONAL"
    else:
        quality = "HIGH"
    return {
        "state": quality,
        "type": "EVIDENCE_QUALITY_NOT_PREDICTION_CONFIDENCE",
        "source_dates": source_dates,
        "partial_windows": partial_windows,
        "unavailable_windows": unavailable_windows,
        "limitations": [
            "F&O and cash series have different coverage starts and may have different as-of dates.",
            "Options and cash-vs-derivatives comparability are not asserted by this contract.",
            f"Provider freshness: {status.get('state', 'UNKNOWN')}",
        ],
    }


def build_institutional_contract(
    flows: pd.DataFrame | None,
    intelligence: pd.DataFrame | None,
    data_status: dict[str, Any],
) -> dict[str, Any]:
    """Build the additive public institutional-flow contract."""
    flows = flows.copy() if flows is not None else pd.DataFrame()
    intelligence = intelligence.copy() if intelligence is not None else pd.DataFrame()
    for frame in (flows, intelligence):
        if "date" in frame.columns:
            frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
            frame.dropna(subset=["date"], inplace=True)
            frame.sort_values("date", inplace=True)
    latest_intel = _latest_row(intelligence)
    latest_flow = _latest_row(flows)
    fno = {participant: _participant_snapshot(flows, participant) for participant in FNO_PARTICIPANTS}
    cash = {participant: _cash_snapshot(flows, participant) for participant in CASH_PARTICIPANTS}
    divergence = {
        "fii_dii": _number(latest_intel.get("FII_DII_Divergence"), 3) if latest_intel is not None else None,
        "smart_retail": _number(latest_intel.get("Smart_Retail_Divergence"), 3) if latest_intel is not None else None,
        "cash_vs_derivatives": {
            "state": "NOT_SUPPORTED",
            "reason": "Cash values are rupee-crore net turnover while F&O values are participant futures/OI units; no governed normalization is present.",
        },
    }
    return {
        "contract_version": "institutional-flow-1.0",
        "as_of": str(latest_flow["date"].date()) if latest_flow is not None else None,
        "participants": fno,
        "cash_participants": cash,
        "derived_signals": {
            "market_regime": str(latest_intel.get("Market_Regime")) if latest_intel is not None else None,
            "smart_money_score": _number(latest_intel.get("Smart_Money_Score")) if latest_intel is not None else None,
            "cash_institutional_score": _number(latest_intel.get("Cash_Institutional_Score")) if latest_intel is not None else None,
            "ensemble_score": _number(latest_intel.get("Ensemble_Score")) if latest_intel is not None else None,
            "divergence": divergence,
        },
        "instrument_scope": {
            "futures_participant_oi_and_volume": "SUPPORTED",
            "fii_futures_statistics": "SUPPORTED_WHEN_PRESENT",
            "options": "NOT_SUPPORTED_BY_CURRENT_PARTICIPANT_CONTRACT",
            "cash_vs_derivatives": "NOT_SUPPORTED",
        },
        "windows": [f"{window}D" for window in WINDOWS],
        "evidence_quality": _quality(flows, intelligence, data_status),
        "data_status": data_status,
    }
