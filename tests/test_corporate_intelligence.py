from __future__ import annotations

import pandas as pd

from backend.services import corporate_intelligence as corporate


def _frames() -> dict[str, pd.DataFrame]:
    return {
        "announcements": pd.DataFrame(
            [
                {
                    "symbol": "RELIANCE",
                    "date": "2026-08-20",
                    "announcement_type": "ORDER_WIN",
                    "signal_score": 70,
                    "desc_raw": "Company disclosed a new customer order.",
                    "title_snippet": "Order disclosure",
                    "seq_id": "ANN-1",
                    "pdf_url": "https://example.test/ann-1.pdf",
                },
                {
                    "symbol": "RELIANCE",
                    "date": "2026-08-19",
                    "announcement_type": "ORDER_WIN",
                    "signal_score": 80,
                    "desc_raw": "Memorandum of Understanding signed with a partner.",
                    "title_snippet": "MOU disclosure",
                    "seq_id": "ANN-2",
                    "pdf_url": None,
                },
                {
                    "symbol": "RELIANCE",
                    "date": "2026-08-18",
                    "announcement_type": "UNKNOWN_SOURCE_TYPE",
                    "signal_score": 10,
                    "desc_raw": "Unclassified exchange disclosure.",
                    "title_snippet": "Other disclosure",
                    "seq_id": "ANN-3",
                    "pdf_url": None,
                },
            ]
        ),
        "event_calendar": pd.DataFrame(
            [
                {
                    "event_date": "2026-08-25",
                    "symbol": "RELIANCE",
                    "company": "Reliance",
                    "purpose_raw": "Board meeting",
                    "purpose_type": "BOARD_MEETING",
                    "bm_desc": "Future meeting",
                    "sector": "OIL & GAS",
                }
            ]
        ),
        "corp_actions": pd.DataFrame(
            [
                {
                    "ex_date": "2026-08-22",
                    "rec_date": "2026-08-23",
                    "symbol": "RELIANCE",
                    "company": "Reliance",
                    "sector": "OIL & GAS",
                    "subject": "Dividend",
                    "action_type": "DIVIDEND",
                    "dividend_rs": 5.0,
                    "bonus_ratio": None,
                    "split_new_fv": None,
                }
            ]
        ),
        "quarterly_results": pd.DataFrame(
            [
                {
                    "symbol": "RELIANCE",
                    "date_end": "2026-06-30",
                    "filing_date": "2026-07-20",
                    "revenue": 123456,
                }
            ]
        ),
    }


def test_corporate_contract_preserves_event_semantics_and_provenance(monkeypatch) -> None:
    frames = _frames()
    monkeypatch.setattr(corporate.data_loader, "get", lambda key: frames.get(key))
    monkeypatch.setattr(
        corporate.data_loader,
        "freshness_for",
        lambda *args: {
            "state": "EOD",
            "as_of": "2026-08-20",
            "source": ["fixture"],
            "last_successful_update": "2026-08-20T18:00:00+05:30",
            "limitations": [],
        },
    )
    monkeypatch.setattr(
        corporate,
        "_identity",
        lambda symbol: {"symbol": symbol, "identity_state": "IDENTIFIED", "isin": "INE002A01018"},
    )

    result = corporate.build_corporate_intelligence("RELIANCE", days=30, limit=20)
    events = result["recent_events"]
    categories = {event["category"] for event in events}

    assert result["contract_version"] == "corporate-intelligence-1.0"
    assert categories >= {"ORDER_CONTRACT", "MOU_LOI", "BOARD_MEETING", "DIVIDEND", "UNKNOWN"}
    assert all(event["event_id"].startswith("CORP-") for event in events)
    assert all(event["provenance"]["source_id"] for event in events)
    assert all(event["materiality_context"]["predictive"] is False for event in events)

    mou = next(event for event in events if event["category"] == "MOU_LOI")
    assert mou["status"] == "ANNOUNCED"
    assert mou["completion_date"] is None
    assert "ORDER_CONTRACT" not in {mou["category"]}

    scheduled = next(event for event in events if event["category"] == "BOARD_MEETING")
    assert scheduled["status"] == "SCHEDULED"
    assert scheduled["announcement_date"] is None
    assert scheduled["effective_date"] == "2026-08-25"
    assert result["results_context"]["contract"] == "fundamental-evidence-1.0"
    assert result["results_context"]["metrics_inlined"] is False
    assert "123456" not in str(result)
    assert corporate._date("2026-08-12") == "2026-08-12"


def test_corporate_identity_review_blocks_fuzzy_substitution(monkeypatch) -> None:
    frames = _frames()
    monkeypatch.setattr(corporate.data_loader, "get", lambda key: frames.get(key))
    monkeypatch.setattr(corporate.data_loader, "freshness_for", lambda *args: {"state": "EOD"})
    monkeypatch.setattr(corporate, "_identity", lambda symbol: {"symbol": symbol, "identity_state": "UNKNOWN"})

    result = corporate.build_corporate_intelligence("NOT_A_CANONICAL_SECURITY")

    assert result["data_status"]["state"] == "IDENTITY_REVIEW_REQUIRED"
    assert result["recent_events"] == []
    assert result["evidence_quality"] == "INSUFFICIENT"


def test_corporate_coverage_snapshot_is_deterministic(monkeypatch) -> None:
    frames = _frames()
    monkeypatch.setattr(corporate.data_loader, "get", lambda key: frames.get(key))
    monkeypatch.setattr(corporate.data_loader, "freshness_for", lambda *args: {"state": "EOD"})
    corporate._SUMMARY_CACHE.clear()

    first = corporate.corporate_coverage_snapshot()
    second = corporate.corporate_coverage_snapshot()

    assert first == second
    assert first["master_symbols"] == 1
    assert first["events_total"] == 5
