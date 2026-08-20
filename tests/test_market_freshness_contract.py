from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend.routers import market, participant
from backend.services import data_loader


def test_dataset_metadata_marks_delayed_eod_data_explicitly(tmp_path: Path) -> None:
    source = tmp_path / "participant.csv"
    source.write_text("date,value\n2026-08-19,1\n", encoding="utf-8")
    metadata = data_loader._build_metadata(
        "participant_intel",
        source,
        pd.DataFrame({"date": ["2026-08-19"], "value": [1]}),
        now=pd.Timestamp("2026-08-21"),
    )

    assert metadata["as_of"] == "2026-08-19"
    assert metadata["freshness"] == "DELAYED"
    assert metadata["source"] == "FII-DII provider-local dataset: participant.csv"


def test_future_dated_data_is_quality_warning_not_current(tmp_path: Path) -> None:
    source = tmp_path / "future.csv"
    source.write_text("as_of_date,value\n2026-08-31,1\n", encoding="utf-8")
    metadata = data_loader._build_metadata(
        "future",
        source,
        pd.DataFrame({"as_of_date": ["2026-08-31"], "value": [1]}),
        now=pd.Timestamp("2026-08-21"),
    )

    assert metadata["freshness"] == "QUALITY_WARNING"
    assert any("future" in item for item in metadata["limitations"])


def test_scheduled_future_dates_are_not_misclassified_as_quality_warnings(
    tmp_path: Path,
) -> None:
    source = tmp_path / "events.csv"
    source.write_text("event_date,value\n2026-08-31,1\n", encoding="utf-8")

    metadata = data_loader._build_metadata(
        "event_calendar",
        source,
        pd.DataFrame({"event_date": ["2026-08-31"], "value": [1]}),
        now=pd.Timestamp("2026-08-21"),
    )

    assert metadata["freshness"] in {"EOD", "DELAYED", "STALE"}
    assert metadata["as_of"] is None
    assert any("Scheduled event dates" in item for item in metadata["limitations"])


def test_freshness_for_keeps_optional_unavailable_explicit(monkeypatch) -> None:
    monkeypatch.setattr(
        data_loader,
        "_dataset_metadata",
        {
            "required": {
                "dataset": "required",
                "source": "required.csv",
                "as_of": "2026-08-20",
                "freshness": "EOD",
                "last_successful_update": "2026-08-20T18:00:00+00:00",
                "limitations": [],
            },
            "optional": {
                "dataset": "optional",
                "source": "optional.csv",
                "as_of": None,
                "freshness": "UNAVAILABLE",
                "last_successful_update": None,
                "limitations": [
                    "Dataset is unavailable or empty; no current evidence is claimed."
                ],
            },
        },
    )

    status = data_loader.freshness_for(("required",), ("optional",))

    assert status["state"] == "EOD"
    assert status["as_of"] == "2026-08-20"
    assert "optional.csv" in status["source"]
    assert any("optional datasets" in item for item in status["limitations"])


def test_formal_market_surfaces_do_not_convert_missing_numbers_to_zero(
    monkeypatch,
) -> None:
    intelligence = pd.DataFrame(
        {
            "date": ["2026-08-20"],
            "Market_Regime": ["UNKNOWN"],
            "Smart_Money_Score": [None],
            "FII_conviction": [None],
        }
    )
    flows = pd.DataFrame(
        {
            "date": ["2026-08-20"],
            "FII_flow_score": [None],
            "DII_flow_score": [None],
            "PRO_flow_score": [None],
            "CLIENT_flow_score": [None],
        }
    )
    frames = {"participant_intel": intelligence, "participant_flows": flows}
    monkeypatch.setattr(data_loader, "get", lambda key: frames.get(key))
    monkeypatch.setattr(data_loader, "freshness_for", lambda *args: {"state": "EOD"})

    market_result = market.get_market_regime()
    participant_result = participant.get_participant_latest()

    assert market_result["smart_money_score"] is None
    assert market_result["fii_conviction_pct"] is None
    assert market_result["flow_scores"] == {
        "FII": None,
        "DII": None,
        "PRO": None,
        "CLIENT": None,
    }
    assert participant_result["FII_flow_score"] is None
    assert participant_result["DII_flow_score"] is None
