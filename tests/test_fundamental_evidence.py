from datetime import date

import pandas as pd

from backend.services import fundamental_evidence as evidence


def _quarters(count: int = 8) -> pd.DataFrame:
    ends = pd.date_range("2024-06-30", periods=count, freq="QE")
    return pd.DataFrame(
        {
            "symbol": ["TEST"] * count,
            "date_end": ends.strftime("%Y-%m-%d"),
            "filing_date": ends.strftime("%Y-%m-%d"),
            "revenue_cr": list(range(10, 10 + count)),
            "net_profit_cr": ([1, 2, -3, 4, 5, 6, 7, 8] * 2)[:count],
            "eps": ([1, 1, -1, 1, 1, 1, 1, 1] * 2)[:count],
            "standalone_or_consolidated": ["CONSOLIDATED"] * count,
        }
    )


def test_ttm_requires_four_comparable_periods_and_preserves_negative_values():
    frame = _quarters(3)
    result = evidence.compute_complete_ttm(frame, "TEST")
    assert result["status"] == "INSUFFICIENT_PERIODS"
    assert result["values"] == {}

    result = evidence.compute_complete_ttm(_quarters(4), "TEST")
    assert result["status"] == "AVAILABLE"
    assert result["values"]["net_profit_cr"] == 4.0


def test_contract_separates_period_filing_retrieval_and_legacy_roe(monkeypatch):
    frames = {
        "quarterly_results": _quarters(),
        "extended_financials": pd.DataFrame(
            [{"symbol": "TEST", "roce_pct": 12.0, "opm_pct": 8.0, "as_of_date": "2025-12-31"}]
        ),
        "valuation_scores": pd.DataFrame(
            [{"symbol": "TEST", "pe_ratio": 18.0, "roe_pct": 7.0, "as_of_date": "2025-12-31", "valuation_label": "CHEAP_QUALITY"}]
        ),
    }

    monkeypatch.setattr(evidence.data_loader, "get", lambda name: frames.get(name))
    monkeypatch.setattr(evidence, "_load_master", lambda symbol: {"sector_platform": "IT"})
    evidence._local_frame.cache_clear()
    result = evidence.build_fundamental_evidence("TEST", today=date(2026, 1, 1))

    ttm = result["observations"]["revenue_ttm_cr"]
    assert ttm["direct_or_derived"] == "DERIVED_FROM_QUARTERLY_COMPONENTS"
    assert ttm["dates"]["period_end"] != ttm["dates"]["retrieved_at"]
    assert result["observations"]["roe_pct"]["status"] == "UNTRUSTED_SOURCE"
    assert result["observations"]["roe_pct"]["missing_reason"] == "LEGACY_COLUMN_IS_NET_MARGIN_NOT_ROE"
    assert result["observations"]["valuation_label"]["limitations"]


def test_financial_sector_metrics_carry_applicability_limitation(monkeypatch):
    frames = {
        "quarterly_results": _quarters(4),
        "extended_financials": pd.DataFrame(
            [{"symbol": "TEST", "opm_pct": 8.0, "ebitda_cr_latest": 10.0, "as_of_date": "2025-12-31"}]
        ),
        "valuation_scores": pd.DataFrame(),
    }
    monkeypatch.setattr(evidence.data_loader, "get", lambda name: frames.get(name))
    monkeypatch.setattr(evidence, "_load_master", lambda symbol: {"sector_platform": "BANKING"})
    evidence._local_frame.cache_clear()
    result = evidence.build_fundamental_evidence("TEST", today=date(2026, 1, 1))
    assert result["observations"]["opm_pct"]["applicability"] == "LIMITED_FOR_FINANCIAL_SECTOR"
    assert any("financial-sector" in item.lower() for item in result["limitations"])


def test_unparseable_historical_filing_date_is_not_promoted(monkeypatch):
    frame = _quarters(4)
    frame.loc[0, "filing_date"] = "11-Nov-202"
    monkeypatch.setattr(evidence.data_loader, "get", lambda name: frame if name == "quarterly_results" else pd.DataFrame())
    monkeypatch.setattr(evidence, "_load_master", lambda symbol: {})
    monkeypatch.setattr(evidence, "_load_reference", lambda symbol: {})
    evidence._local_frame.cache_clear()
    result = evidence.build_fundamental_evidence("TEST", today=date(2026, 1, 1))
    assert result["dates"]["latest_filing_date"] is not None
    assert evidence._iso("11-Nov-202") is None
