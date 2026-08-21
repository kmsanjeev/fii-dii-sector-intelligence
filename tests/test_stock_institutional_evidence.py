from __future__ import annotations

import pandas as pd

from backend.services import stock_institutional_evidence as evidence


def _identity() -> dict:
    return {
        "symbol": "ALPHA",
        "company": "Alpha Limited",
        "isin": "INE000000000",
        "identity_state": "IDENTIFIED",
        "identity_source": "fixture",
    }


def test_contract_separates_disclosed_deals_from_daily_fii_dii_flow(monkeypatch) -> None:
    frames = {
        "block_deals": pd.DataFrame(
            [
                {
                    "date": "2026-08-20",
                    "symbol": "ALPHA",
                    "company": "Alpha Limited",
                    "deal_type": "BLOCK",
                    "client_name": "Unknown Client",
                    "participant": "RETAIL",
                    "direction": "BUY",
                    "qty": 100000,
                    "price": 100.0,
                    "value_cr": 1.0,
                    "seq_id": 1,
                },
                {
                    "date": "2026-08-19",
                    "symbol": "ALPHA",
                    "company": "Alpha Limited",
                    "deal_type": "BULK",
                    "client_name": "Example Mutual Fund",
                    "participant": "MF",
                    "direction": "SELL",
                    "qty": 200000,
                    "price": 90.0,
                    "value_cr": 1.8,
                    "seq_id": 2,
                },
            ]
        ),
        "shareholding": pd.DataFrame(
            [
                {"symbol": "ALPHA", "quarter_end_date": "30-JUN-2026", "submission_date": "15-JUL-2026", "window_label": "Q1FY27", "promoter_pct": 40, "fii_pct": 12, "dii_pct": 8, "public_pct": 40, "source": "nse_xbrl"},
                {"symbol": "ALPHA", "quarter_end_date": "31-MAR-2026", "submission_date": "15-APR-2026", "window_label": "Q4FY26", "promoter_pct": 41, "fii_pct": 11, "dii_pct": 8.5, "public_pct": 39.5, "source": "nse_xbrl"},
            ]
        ),
        "deal_signals": pd.DataFrame(),
        "holding_trends": pd.DataFrame(),
        "participant_flows": pd.DataFrame(),
    }
    monkeypatch.setattr(evidence.data_loader, "get", lambda key: frames.get(key))

    result = evidence.build_stock_institutional_evidence("ALPHA", identity=_identity())

    assert result["scope"] == "DEAL_ACTIVITY_CONTEXT"
    assert result["evidence_taxonomy"]["direct_transactions"] == "DIRECT_DISCLOSED_TRANSACTION_ACTIVITY"
    assert result["evidence_taxonomy"]["unsupported_daily_stock_flow"] == "NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE"
    assert result["data_status"]["direct_daily_stock_flow_decision"] == "NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE"
    assert len(result["bulk_deals"]) == 1
    assert len(result["block_deals"]) == 1
    assert result["participant_classes"]["unknown_remains_unknown"] is True
    assert result["participant_classes"]["counts"]["UNKNOWN"] == 1
    assert result["ownership"]["change"]["fii_pct"] == 1.0
    assert result["ownership"]["latest"]["submission_date"] == "2026-07-15"
    assert result["direct_transactions"]["records"][0]["date_fields"]["disclosure_date"] is None
    assert result["contract_version"] == "stock-institutional-evidence-1.1"
    assert result["direct_transactions"]["records"][0]["source_record_id"]
    assert result["direct_transactions"]["records"][0]["participant"]["participant_raw_name"] == "Unknown Client"
    assert result["direct_transactions"]["records"][0]["participant"]["classification_method"] == "UNKNOWN"
    assert result["identity"]["security_resolution"]["state"] == "EXACT_IDENTITY"
    assert result["frequency"]["ownership"] == "QUARTERLY"
    assert result["data_status"]["freshness_for_frequency"]["ownership"]["frequency"] == "QUARTERLY"
    assert result["provenance"]["direct_record_lineage"]
    assert result["coverage"]["both"] is True


def test_unknown_symbol_requires_identity_review(monkeypatch) -> None:
    frames = {key: pd.DataFrame() for key in ("block_deals", "shareholding", "holding_trends", "deal_signals", "participant_flows")}
    monkeypatch.setattr(evidence.data_loader, "get", lambda key: frames.get(key))

    result = evidence.build_stock_institutional_evidence("UNKNOWN", identity={"symbol": "UNKNOWN", "identity_state": "UNKNOWN_SYMBOL"})

    assert result["scope"] == "IDENTITY_REVIEW_REQUIRED"
    assert result["identity"]["identity_status"] == "REVIEW_REQUIRED"
    assert result["data_status"]["direct_sector_flow_decision"] == "NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE"


def test_market_context_is_not_attributed_to_stock(monkeypatch) -> None:
    frames = {key: pd.DataFrame() for key in ("block_deals", "shareholding", "holding_trends", "deal_signals")}
    frames["participant_flows"] = pd.DataFrame([{"date": "2026-08-20", "FII_flow_score": 4.0, "DII_flow_score": 2.0}])
    monkeypatch.setattr(evidence.data_loader, "get", lambda key: frames.get(key))

    result = evidence.build_stock_institutional_evidence("ALPHA", identity=_identity())

    assert result["scope"] == "MARKET_LEVEL_CONTEXT_ONLY"
    assert result["market_level_context"]["as_of"] == "2026-08-20"
    assert result["signals"]["daily_fii_dii_flow"] == "NOT_AVAILABLE"


def test_duplicate_deals_are_deduplicated_with_stable_source_ids(monkeypatch) -> None:
    duplicate = {
        "date": "2026-08-20",
        "symbol": "ALPHA",
        "company": "Alpha Limited",
        "deal_type": "BLOCK",
        "client_name": "Unknown Client",
        "participant": "RETAIL",
        "direction": "BUY",
        "qty": 100000,
        "price": 100.0,
        "value_cr": 1.0,
        "seq_id": 1,
    }
    frames = {
        "block_deals": pd.DataFrame([duplicate, duplicate]),
        "shareholding": pd.DataFrame(),
        "holding_trends": pd.DataFrame(),
        "deal_signals": pd.DataFrame(),
        "participant_flows": pd.DataFrame(),
    }
    monkeypatch.setattr(evidence.data_loader, "get", lambda key: frames.get(key))

    result = evidence.build_stock_institutional_evidence("ALPHA", identity=_identity())

    assert result["facts"]["deal_activity"]["duplicate_count_removed"] == 1
    assert len(result["direct_transactions"]["records"]) == 1
    assert result["direct_transactions"]["records"][0]["record_id"] == result["direct_transactions"]["records"][0]["source_record_id"]


def test_frequency_freshness_is_cadence_aware() -> None:
    reference = pd.Timestamp("2026-08-21").date()

    assert evidence._freshness_for_frequency("2026-08-20", "DAILY", reference_date=reference)["state"] == "CURRENT_FOR_FREQUENCY"
    assert evidence._freshness_for_frequency("2026-06-30", "QUARTERLY", reference_date=reference)["state"] == "CURRENT_FOR_FREQUENCY"
    assert evidence._freshness_for_frequency("2025-01-01", "QUARTERLY", reference_date=reference)["state"] == "STALE_FOR_FREQUENCY"
    assert evidence._freshness_for_frequency(None, "IRREGULAR", reference_date=reference)["state"] == "UNKNOWN_FREQUENCY"
