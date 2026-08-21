from __future__ import annotations

import pandas as pd

from engines.participant import institutional_contract as contract


def _frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.date_range("2026-07-01", periods=30, freq="D")
    flows = pd.DataFrame({"date": dates})
    for participant in contract.FNO_PARTICIPANTS:
        flows[f"{participant}_OI_Net"] = range(30)
        flows[f"{participant}_OI_Delta"] = range(30)
    for participant in contract.CASH_PARTICIPANTS:
        flows[f"{participant}_net_cr"] = range(30)
    intelligence = pd.DataFrame(
        {
            "date": dates,
            "Market_Regime": ["MIXED"] * len(dates),
            "FII_DII_Divergence": [0.0] * len(dates),
            "Smart_Retail_Divergence": [0.0] * len(dates),
            "Smart_Money_Score": [0.0] * len(dates),
            "Cash_Institutional_Score": [0.0] * len(dates),
            "Ensemble_Score": [0.0] * len(dates),
        }
    )
    return flows, intelligence


def test_institutional_contract_reuses_request_scoped_snapshots(monkeypatch) -> None:
    flows, intelligence = _frames()
    calls = {"fno": 0, "cash": 0}
    original_fno = contract._participant_snapshot
    original_cash = contract._cash_snapshot

    def counted_fno(*args, **kwargs):
        calls["fno"] += 1
        return original_fno(*args, **kwargs)

    def counted_cash(*args, **kwargs):
        calls["cash"] += 1
        return original_cash(*args, **kwargs)

    monkeypatch.setattr(contract, "_participant_snapshot", counted_fno)
    monkeypatch.setattr(contract, "_cash_snapshot", counted_cash)

    result = contract.build_institutional_contract(flows, intelligence, {"state": "EOD"})

    assert result["contract_version"] == "institutional-flow-1.1"
    assert calls == {"fno": len(contract.FNO_PARTICIPANTS), "cash": len(contract.CASH_PARTICIPANTS)}


def test_window_snapshot_is_equivalent_to_full_history_for_current_windows() -> None:
    series = pd.Series(range(100), dtype="float64")
    result = contract._window_snapshot(series)

    assert result["5D"]["value"] == 5 * 99 - 10
    assert result["20D"]["value"] == sum(range(80, 100))
    assert result["20D"]["observations"] == 20
    assert result["20D"]["expected_observations"] == 20
    assert result["20D"]["state"] == "COMPLETE"
