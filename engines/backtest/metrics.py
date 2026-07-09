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

    # Sortino: penalise downside deviation only (Phase R1)
    downside = daily_rets[daily_rets < 0]
    sortino = 0.0
    if len(downside) > 1 and downside.std() > 0:
        sortino = round(float(daily_rets.mean() / downside.std() * np.sqrt(252)), 2)

    # Profit factor: gross wins / gross losses (Phase R1)
    gross_win  = float(rets[rets > 0].sum())
    gross_loss = float(-rets[rets < 0].sum())
    profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else 0.0

    avg_win  = round(float(rets[rets > 0].mean()), 2) if wins   else 0.0
    avg_loss = round(float(rets[rets < 0].mean()), 2) if losses else 0.0

    # Max drawdown of the sequential trade equity curve (returns are %,
    # trades assumed in the order given — backtest emits them entry-date sorted)
    equity = (1.0 + rets / 100.0).cumprod()
    max_drawdown = round(float((equity / equity.cummax() - 1.0).min() * 100), 2)

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
        "sortino":       sortino,
        "profit_factor": profit_factor,
        "avg_win":       avg_win,
        "avg_loss":      avg_loss,
        "max_drawdown":  max_drawdown,
    }


def _empty() -> dict:
    return {
        "trade_count": 0, "win_count": 0, "loss_count": 0,
        "hit_rate": 0.0, "avg_return": 0.0, "median_return": 0.0,
        "best_trade": 0.0, "worst_trade": 0.0, "std_return": 0.0, "sharpe": 0.0,
        "sortino": 0.0, "profit_factor": 0.0, "avg_win": 0.0, "avg_loss": 0.0,
        "max_drawdown": 0.0,
    }
