import pandas as pd

from backend.routers import participant
from engines.participant.institutional_contract import build_institutional_contract


def _frames():
    dates = pd.date_range("2026-08-17", periods=5, freq="D")
    flows = pd.DataFrame({
        "date": dates,
        "FII_OI_Net": [100, 110, 108, 125, 140],
        "DII_OI_Net": [20, 19, 18, 17, 16],
        "PRO_OI_Net": [5, 6, 7, 8, 9],
        "CLIENT_OI_Net": [40, 39, 38, 37, 36],
        "FII_Volume_Net": [10, 11, 12, 13, 14],
        "DII_Volume_Net": [2, 2, 2, 2, 2],
        "PRO_Volume_Net": [1, 1, 1, 1, 1],
        "CLIENT_Volume_Net": [3, 3, 3, 3, 3],
        "FPI_net_cr": [None, None, 10, 20, None],
        "MF_net_cr": [1, 2, 3, 4, 5],
    })
    intelligence = pd.DataFrame({
        "date": dates,
        "Market_Regime": ["NEUTRAL"] * 5,
        "Smart_Money_Score": [1, 2, 3, 4, 5],
        "Cash_Institutional_Score": [None, None, None, 10, 12],
        "Ensemble_Score": [1, 2, 3, 4, 5],
        "FII_DII_Divergence": [1, 2, 3, 4, 5],
        "Smart_Retail_Divergence": [0, 1, 0, 1, 0],
    })
    return flows, intelligence


def test_contract_exposes_windows_and_preserves_missing_cash():
    flows, intelligence = _frames()
    result = build_institutional_contract(flows, intelligence, {"state": "EOD"})
    assert result["windows"] == ["1D", "3D", "5D", "10D", "20D"]
    assert result["participants"]["FII"]["windows"]["3D"]["state"] == "COMPLETE"
    assert result["cash_participants"]["FPI"]["windows"]["5D"]["state"] == "PARTIAL"
    assert result["cash_participants"]["FPI"]["windows"]["5D"]["value"] is not None
    assert result["instrument_scope"]["options"] == "NOT_SUPPORTED_BY_CURRENT_PARTICIPANT_CONTRACT"
    assert result["evidence_quality"]["type"] == "EVIDENCE_QUALITY_NOT_PREDICTION_CONFIDENCE"


def test_contract_marks_cash_vs_derivatives_unsupported():
    flows, intelligence = _frames()
    result = build_institutional_contract(flows, intelligence, {"state": "EOD"})
    assert result["derived_signals"]["divergence"]["cash_vs_derivatives"]["state"] == "NOT_SUPPORTED"


def test_legacy_latest_response_keeps_existing_contract(monkeypatch):
    flows, intelligence = _frames()
    monkeypatch.setattr(participant.data_loader, "get", lambda key: {
        "participant_intel": intelligence,
        "participant_flows": flows,
    }.get(key))
    monkeypatch.setattr(participant.data_loader, "freshness_for", lambda *args: {"state": "EOD"})
    result = participant.get_participant_latest()
    assert result["date"].startswith("2026-08-21")
    assert "FII_flow_score" in result
    assert result["institutional_contract"]["contract_version"] == "institutional-flow-1.1"


def test_derivatives_contract_separates_level_change_and_source_granularity():
    flows, intelligence = _frames()
    result = build_institutional_contract(flows, intelligence, {"state": "EOD"})
    participant = result["participants"]["FII"]
    assert participant["position_level"]["semantic"] == "aggregate_futures_net_open_interest"
    assert participant["position_change"]["semantic"] == "day_over_day_change_in_aggregate_futures_net_open_interest"
    assert participant["positive_persistence_20d"] is not None
    assert participant["negative_persistence_20d"] is not None
    assert result["derivatives"]["instrument_capabilities"]["index_futures"] == "SOURCE_AVAILABLE_NOT_PERSISTED"
    assert result["derivatives"]["instrument_capabilities"]["long_short_ratio"] == "NOT_SUPPORTED"


def test_derivatives_divergence_is_like_for_like_and_date_alignment_is_explicit():
    flows, intelligence = _frames()
    result = build_institutional_contract(flows, intelligence, {"state": "EOD"})
    divergence = result["derived_signals"]["divergence"]["participant_derivatives"]
    assert divergence["basis"] == "same_participant_aggregate_futures_oi_change_window"
    assert divergence["pairs"]["fii_vs_pro"]["state"] == "AVAILABLE"
    alignment = result["derivatives"]["date_alignment"]
    assert alignment["state"] == "ALIGNED"
    assert alignment["comparison_allowed"] is False
