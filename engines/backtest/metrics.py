"""
Backtest Metrics -- Phase 21
Performance analytics over a list of trade result dicts.
"""

import numpy as np
import pandas as pd


def compute_metrics(trades: list[dict], ret_col: str = "ret_90d") -> dict:
    """
    Aggregate performance metrics from a list of trade result dicts.
    ret_col: which return column to use as the primary metric.
    Silently drops trades where ret_col is None (open / horizon not yet reached).
    """
    rets = pd.to_numeric(
        pd.Series([t.get(ret_col) for t in trades]), errors="coerce"
    ).dropna()

    if len(rets) == 0:
        return _empty()

    n      = len(rets)
    wins   = int((rets > 0).sum())
    losses = int((rets < 0).sum())

    # Sharpe: cross-sectional trade returns, annualised assuming hold_days horizon
    hold_days = 90
    try:
        hold_days = int(ret_col.replace("ret_", "").replace("d", ""))
    except ValueError:
        pass
    daily_rets = rets / max(hold_days, 1)
    sharpe = 0.0
    if len(daily_rets) > 1 and daily_rets.std() > 0:
        sharpe = round(float(daily_rets.mean() / daily_rets.std() * np.sqrt(252)), 2)

    return {
        "trade_count":   n,
        "win_count":     wins,
        "loss_count":    losses,
        "hit_rate":      round(float(wins / n * 100), 1),
        "avg_return":    round(float(rets.mean()), 2),
        "median_return": round(float(rets.median()), 2),
        "best_trade":    round(float(rets.max()), 2),
        "worst_trade":   round(float(rets.min()), 2),
        "std_return":    round(float(rets.std()), 2),
        "sharpe":        sharpe,
    }


def _empty() -> dict:
    return {
        "trade_count": 0, "win_count": 0, "loss_count": 0,
        "hit_rate": 0.0, "avg_return": 0.0, "median_return": 0.0,
        "best_trade": 0.0, "worst_trade": 0.0, "std_return": 0.0, "sharpe": 0.0,
    }
