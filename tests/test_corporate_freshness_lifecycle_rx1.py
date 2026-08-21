from __future__ import annotations

import pandas as pd
import requests

from backend.services import corporate_intelligence as corporate
from engines.corporate.corporate_event_calendar_engine import (
    CorporateEventCalendarEngine,
)


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class _Session:
    def __init__(self, payload):
        self.payload = payload
        self.calls: list[dict] = []

    def get(self, endpoint, *, params, timeout):
        self.calls.append({"endpoint": endpoint, "params": params, "timeout": timeout})
        return _Response(self.payload)


def test_event_calendar_fetch_adds_retrieval_metadata_without_nselib() -> None:
    session = _Session(
        [
            {
                "symbol": "RELIANCE",
                "company": "Reliance",
                "date": "25-Aug-2026",
                "purpose": "Board Meeting",
                "bm_desc": "Meeting rescheduled to 25-Aug-2026",
            }
        ]
    )
    engine = CorporateEventCalendarEngine()
    engine.sector_map = {"RELIANCE": "OIL & GAS"}

    rows = engine._fetch_chunk(session, "04-08-2026", "21-08-2026")

    assert len(rows) == 1
    assert rows[0]["symbol"] == "RELIANCE"
    assert rows[0]["retrieved_at"]
    assert rows[0]["purpose_type"] == "BOARD_MEETING"
    assert session.calls[0]["endpoint"].endswith("/api/event-calendar")
    assert session.calls[0]["params"]["index"] == "equities"


def test_event_calendar_source_failure_is_explicit(monkeypatch) -> None:
    class _FailingSession:
        def get(self, endpoint, *, params, timeout):
            raise requests.RequestException("simulated source outage")

    monkeypatch.setattr(
        "engines.corporate.corporate_event_calendar_engine.cfg.MAX_RETRIES", 1
    )
    engine = CorporateEventCalendarEngine()

    rows = engine._fetch_chunk(_FailingSession(), "04-08-2026", "21-08-2026")

    assert rows == []
    assert engine._source_errors
    assert "simulated source outage" in engine._source_errors[0]


def test_lifecycle_states_require_explicit_source_language() -> None:
    base = pd.Series(
        {
            "symbol": "RELIANCE",
            "date": "2026-08-20",
            "announcement_type": "ACQUISITION",
            "desc_raw": "Acquisition announced; completion subject to approval.",
            "title_snippet": "Acquisition disclosure",
            "seq_id": "ANN-1",
            "retrieved_at": "2026-08-21T10:00:00+00:00",
        }
    )
    announced = corporate._announcement_event(base, None)
    assert announced["status"] == "ANNOUNCED"
    assert announced["completion_date"] is None
    assert announced["lifecycle"]["lineage_method"] == "UNKNOWN"
    assert announced["provenance"]["retrieved_at"]

    completed = base.copy()
    completed["desc_raw"] = "Acquisition completed and commissioned."
    completed_event = corporate._announcement_event(completed, None)
    assert completed_event["status"] == "COMPLETED"
    assert completed_event["lifecycle"]["state_method"] == "EXPLICIT_SOURCE_LANGUAGE"


def test_result_event_keeps_fundamental_freshness_separate(monkeypatch) -> None:
    results = pd.DataFrame(
        [
            {
                "symbol": "RELIANCE",
                "date_end": "2026-06-30",
                "filing_date": "2026-07-20",
            }
        ]
    )
    monkeypatch.setattr(
        corporate.data_loader,
        "freshness_metadata",
        lambda: {
            "datasets": {
                "quarterly_results": {
                    "freshness": "DELAYED",
                    "dataset_build_at": "2026-08-21T08:15:00+00:00",
                }
            }
        },
    )

    linkage = corporate._result_linkage("RELIANCE", results)

    assert linkage["state"] == "FUNDAMENTAL_EVIDENCE_AVAILABLE"
    assert linkage["latest_announcement_date"] == "2026-07-20"
    assert linkage["fundamental_evidence_freshness"] == "DELAYED"
    assert linkage["metrics_inlined"] is False


def test_legacy_date_is_not_treated_as_year_0202(tmp_path) -> None:
    metadata = corporate.data_loader._build_metadata(
        "quarterly_results",
        tmp_path / "results.csv",
        pd.DataFrame(
            {
                "filing_date": ["10-Nov-202", "2026-07-20"],
                "date_end": ["2026-06-30", "2026-06-30"],
            }
        ),
        now=pd.Timestamp("2026-08-21"),
    )

    assert metadata["date_column"] == "filing_date"
    assert metadata["as_of"] == "2026-07-20"
    assert metadata["null_date_rows"] == 1
