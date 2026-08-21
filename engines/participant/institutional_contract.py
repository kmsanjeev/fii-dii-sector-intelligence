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
    # Only the largest requested window can affect the current snapshot.  The
    # previous implementation rebuilt rolling arrays across the full history
    # for every participant and cash series, even though no older row could
    # change the returned values.
    history = max(windows, default=0)
    values = pd.to_numeric(series, errors="coerce").tail(history).reset_index(drop=True)
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


def _participant_snapshot(
    flows: pd.DataFrame,
    participant: str,
    latest_row: pd.Series | None = None,
) -> dict[str, Any]:
    row = latest_row if latest_row is not None else _latest_row(flows)
    result: dict[str, Any] = {
        "oi_net": _number(row.get(f"{participant}_OI_Net")) if row is not None else None,
        "volume_net": _number(row.get(f"{participant}_Volume_Net")) if row is not None else None,
        "flow_score": _number(row.get(f"{participant}_flow_score")) if row is not None else None,
        "oi_delta_1d": _number(row.get(f"{participant}_OI_Delta")) if row is not None else None,
        "windows": {},
        "persistence_20d": None,
        "positive_persistence_20d": None,
        "negative_persistence_20d": None,
        "delta_direction_20d": "UNAVAILABLE",
        "acceleration_5d": None,
        "reversal_5d": None,
        "position_level": {
            "field": f"{participant}_OI_Net",
            "value": _number(row.get(f"{participant}_OI_Net")) if row is not None else None,
            "unit": "contracts",
            "semantic": "aggregate_futures_net_open_interest",
        },
        "position_change": {
            "field": f"{participant}_OI_Delta",
            "value": _number(row.get(f"{participant}_OI_Delta")) if row is not None else None,
            "unit": "contracts",
            "semantic": "day_over_day_change_in_aggregate_futures_net_open_interest",
        },
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
        recent = usable.tail(20)
        result["positive_persistence_20d"] = _number((recent > 0).mean() * 100, 1)
        result["negative_persistence_20d"] = _number((recent < 0).mean() * 100, 1)
        result["persistence_20d"] = result["positive_persistence_20d"]
        positive = int((recent > 0).sum())
        negative = int((recent < 0).sum())
        if positive > negative:
            result["delta_direction_20d"] = "POSITIVE"
        elif negative > positive:
            result["delta_direction_20d"] = "NEGATIVE"
        else:
            result["delta_direction_20d"] = "MIXED"
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


def _cash_snapshot(
    flows: pd.DataFrame,
    participant: str,
    latest_row: pd.Series | None = None,
) -> dict[str, Any]:
    net_col = f"{participant}_net_cr"
    series = pd.to_numeric(flows.get(net_col, pd.Series(dtype=float)), errors="coerce")
    row = latest_row if latest_row is not None else _latest_row(flows)
    return {
        "net_cr": _number(row.get(net_col), 2) if row is not None else None,
        "windows": _window_snapshot(series),
        "source_date": (
            str(pd.to_datetime(flows.loc[series.notna(), "date"], errors="coerce").max().date())
            if "date" in flows.columns and series.notna().any()
            else None
        ),
    }


def _latest_source_date(flows: pd.DataFrame, columns: tuple[str, ...]) -> str | None:
    if flows.empty or "date" not in flows.columns:
        return None
    available = [column for column in columns if column in flows.columns]
    if not available:
        return None
    mask = flows[available].apply(pd.to_numeric, errors="coerce").notna().any(axis=1)
    dates = pd.to_datetime(flows.loc[mask, "date"], errors="coerce").dropna()
    return str(dates.max().date()) if not dates.empty else None


def _date_alignment(flows: pd.DataFrame) -> dict[str, Any]:
    """Describe F&O/cash date alignment without silently joining unlike sessions."""
    fno_date = _latest_source_date(
        flows,
        tuple(f"{p}_OI_Net" for p in FNO_PARTICIPANTS),
    )
    cash_date = _latest_source_date(
        flows,
        tuple(f"{p}_net_cr" for p in CASH_PARTICIPANTS),
    )
    if not fno_date or not cash_date:
        return {
            "state": "UNAVAILABLE",
            "fno_as_of": fno_date,
            "cash_as_of": cash_date,
            "calendar_lag_days": None,
            "comparison_allowed": False,
            "reason": "One or both source families have no usable as-of date.",
        }
    lag = (pd.Timestamp(fno_date) - pd.Timestamp(cash_date)).days
    if lag == 0:
        state = "ALIGNED"
        reason = "F&O and cash source dates are equal; units remain non-comparable without normalization."
    elif lag > 0:
        state = "CASH_LAGGING"
        reason = "Cash is older than F&O; no same-session cash-versus-derivatives comparison is emitted."
    else:
        state = "FNO_LAGGING"
        reason = "F&O is older than cash; no same-session cash-versus-derivatives comparison is emitted."
    return {
        "state": state,
        "fno_as_of": fno_date,
        "cash_as_of": cash_date,
        "calendar_lag_days": lag,
        "comparison_allowed": False,
        "reason": reason,
    }


def _derivatives_divergence(
    flows: pd.DataFrame,
    window: str = "5D",
    snapshots: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compare participants on the same aggregate futures OI-change basis."""
    snapshots = snapshots or {p: _participant_snapshot(flows, p) for p in FNO_PARTICIPANTS}
    pairs = (("FII", "DII"), ("FII", "PRO"), ("FII", "CLIENT"), ("PRO", "CLIENT"))
    result: dict[str, Any] = {
        "basis": "same_participant_aggregate_futures_oi_change_window",
        "window": window,
        "unit": "contracts",
        "source_date": _latest_source_date(flows, tuple(f"{p}_OI_Net" for p in FNO_PARTICIPANTS)),
        "pairs": {},
    }
    for left, right in pairs:
        left_window = snapshots[left]["windows"].get(window, {})
        right_window = snapshots[right]["windows"].get(window, {})
        left_value = left_window.get("value")
        right_value = right_window.get("value")
        key = f"{left.lower()}_vs_{right.lower()}"
        if left_value is None or right_value is None:
            result["pairs"][key] = {
                "state": "UNAVAILABLE",
                "value": None,
                "left": left,
                "right": right,
                "reason": "Both participant windows are required for like-for-like comparison.",
            }
            continue
        difference = _number(left_value - right_value)
        result["pairs"][key] = {
            "state": "AVAILABLE",
            "value": difference,
            "left": left,
            "right": right,
            "left_window_value": left_value,
            "right_window_value": right_value,
            "left_window_state": left_window.get("state"),
            "right_window_state": right_window.get("state"),
            "interpretation": "positive means left participant has the higher aggregate net OI change over the window; this is not a price forecast.",
        }
    return result


def _derivatives_metadata(flows: pd.DataFrame) -> dict[str, Any]:
    """Expose source granularity and the deliberate options boundary."""
    return {
        "source_family": "NSE_NSELIB_DERIVATIVES",
        "source_functions": [
            "participant_wise_open_interest",
            "participant_wise_trading_volume",
            "fii_derivatives_statistics",
        ],
        "source_granularity": "PARTICIPANT_AGGREGATE_BY_INSTRUMENT_BUCKET",
        "persisted_contract_scope": "AGGREGATE_FUTURES_PARTICIPANT_OI_AND_VOLUME",
        "participants": list(FNO_PARTICIPANTS),
        "instrument_capabilities": {
            "futures_aggregate": "SUPPORTED",
            "index_futures": "SOURCE_AVAILABLE_NOT_PERSISTED",
            "stock_futures": "SOURCE_AVAILABLE_NOT_PERSISTED",
            "index_options": "SOURCE_AVAILABLE_NOT_PERSISTED",
            "stock_options": "SOURCE_AVAILABLE_NOT_PERSISTED",
            "gross_long_short_breakdown": "SOURCE_AVAILABLE_NOT_PERSISTED",
            "long_short_ratio": "NOT_SUPPORTED",
        },
        "position_level": {
            "field": "{PARTICIPANT}_OI_Net",
            "unit": "contracts",
            "formula": "future_index_long + future_stock_long - future_index_short - future_stock_short",
            "meaning": "aggregate futures net open interest; not a gross long/short ledger",
        },
        "position_change": {
            "field": "{PARTICIPANT}_OI_Delta",
            "unit": "contracts",
            "formula": "current aggregate futures net OI minus prior stored observation",
            "windows": [f"{window}D" for window in WINDOWS],
        },
        "fii_statistics_boundary": {
            "field": "FII_Derivatives_Net",
            "meaning": "daily FII futures buy-contracts minus sell-contracts from the separate FII statistics source",
            "not_equivalent_to": "participant OI level or participant OI change",
        },
        "date_alignment": _date_alignment(flows),
        "options_decision": {
            "state": "NOT_SUPPORTED",
            "reason": "The source exposes option buckets, but the persisted history and governed contract do not retain participant-wise option fields.",
        },
    }


def _quality(
    flows: pd.DataFrame,
    intelligence: pd.DataFrame,
    status: dict[str, Any],
    fno_snapshots: dict[str, dict[str, Any]] | None = None,
    cash_snapshots: dict[str, dict[str, Any]] | None = None,
    latest_flow: pd.Series | None = None,
    latest_intelligence: pd.Series | None = None,
) -> dict[str, Any]:
    flow_date = latest_flow if latest_flow is not None else _latest_row(flows)
    intel_date = latest_intelligence if latest_intelligence is not None else _latest_row(intelligence)
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
    fno_snapshots = fno_snapshots or {
        participant: _participant_snapshot(flows, participant)
        for participant in FNO_PARTICIPANTS
    }
    cash_snapshots = cash_snapshots or {
        participant: _cash_snapshot(flows, participant)
        for participant in CASH_PARTICIPANTS
    }
    for participant in FNO_PARTICIPANTS:
        for window in fno_snapshots[participant]["windows"].values():
            partial_windows += window["state"] == "PARTIAL"
            unavailable_windows += window["state"] == "UNAVAILABLE"
    for participant in CASH_PARTICIPANTS:
        for window in cash_snapshots[participant]["windows"].values():
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
    fno = {
        participant: _participant_snapshot(flows, participant, latest_flow)
        for participant in FNO_PARTICIPANTS
    }
    cash = {
        participant: _cash_snapshot(flows, participant, latest_flow)
        for participant in CASH_PARTICIPANTS
    }
    divergence = {
        "fii_dii": _number(latest_intel.get("FII_DII_Divergence"), 3) if latest_intel is not None else None,
        "smart_retail": _number(latest_intel.get("Smart_Retail_Divergence"), 3) if latest_intel is not None else None,
        "cash_vs_derivatives": {
            "state": "NOT_SUPPORTED",
            "reason": "Cash values are rupee-crore net turnover while F&O values are participant futures/OI units; no governed normalization is present.",
        },
    }
    return {
        "contract_version": "institutional-flow-1.1",
        "compatibility": {
            "change_type": "ADDITIVE_MINOR",
            "backward_compatible_with": "institutional-flow-1.0",
            "legacy_endpoint_preserved": True,
        },
        "as_of": str(latest_flow["date"].date()) if latest_flow is not None else None,
        "participants": fno,
        "cash_participants": cash,
        "derived_signals": {
            "market_regime": str(latest_intel.get("Market_Regime")) if latest_intel is not None else None,
            "smart_money_score": _number(latest_intel.get("Smart_Money_Score")) if latest_intel is not None else None,
            "cash_institutional_score": _number(latest_intel.get("Cash_Institutional_Score")) if latest_intel is not None else None,
            "ensemble_score": _number(latest_intel.get("Ensemble_Score")) if latest_intel is not None else None,
            "divergence": {
                **divergence,
                "participant_derivatives": _derivatives_divergence(flows, snapshots=fno),
            },
        },
        "derivatives": _derivatives_metadata(flows),
        "instrument_scope": {
            "futures_participant_oi_and_volume": "SUPPORTED",
            "fii_futures_statistics": "SUPPORTED_WHEN_PRESENT",
            "options": "NOT_SUPPORTED_BY_CURRENT_PARTICIPANT_CONTRACT",
            "cash_vs_derivatives": "NOT_SUPPORTED",
        },
        "windows": [f"{window}D" for window in WINDOWS],
        "evidence_quality": _quality(
            flows,
            intelligence,
            data_status,
            fno_snapshots=fno,
            cash_snapshots=cash,
            latest_flow=latest_flow,
            latest_intelligence=latest_intel,
        ),
        "data_status": data_status,
    }
