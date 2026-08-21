from __future__ import annotations

import pandas as pd

from engines.fundamentals import financial_results_engine as module


def _row(symbol: str, period_end: str, *, filing_date: str, statement: str = "Consolidated", source: str = "nselib_xbrl") -> dict:
    return {
        "symbol": symbol,
        "date_start": period_end[:4] + "-04-01",
        "date_end": period_end,
        "quarter_label": "Quarterly",
        "window_label": "Q4FY26",
        "filing_date": filing_date,
        "revenue_cr": -10.0,
        "net_profit_cr": None,
        "eps": -1.5,
        "rounding": "Crores",
        "standalone_or_consolidated": statement,
        "source": source,
    }


def test_recent_windows_are_dynamic_and_newest_first():
    windows = module._recent_filing_windows(2)
    assert len(windows) == 2
    assert windows[0][2] != "Q3FY25"
    assert windows[0][1] >= windows[1][1]


def test_filing_date_parser_does_not_truncate_year():
    assert module._parse_filing_date("29-Mar-2025 14:58") == "2025-03-29"
    assert module._parse_filing_date("2026-08-06 14:07:24") == "2026-08-06"
    assert module._parse_filing_date("18-Jul-202") == ""


def test_normalizer_preserves_negative_and_normalizes_filing_date():
    engine = module.FinancialResultsEngine(use_yfinance=False)
    result = engine._normalize_xbrl_row({
        "symbol": "TEST",
        "date_start": "2026-04-01",
        "date_end": "2026-06-30",
        "quarter_label": "Quarterly",
        "window_label": "Q1FY27",
        "filing_date": "06-Aug-2026 14:07",
        "revenue_raw": "-10000000",
        "profit_raw": "-2500000",
        "eps": "-1.25",
        "rounding": "Crores",
        "nature": "Consolidated",
    })
    assert result["filing_date"] == "2026-08-06"
    assert result["revenue_cr"] == -1.0
    assert result["net_profit_cr"] == -0.25


def test_dedupe_retains_statement_variants_and_restatement_versions():
    rows = [
        _row("TEST", "2026-06-30", filing_date="2026-08-01", statement="Standalone"),
        _row("TEST", "2026-06-30", filing_date="2026-08-01", statement="Consolidated"),
        _row("TEST", "2026-06-30", filing_date="2026-08-12", statement="Consolidated"),
        _row("TEST", "2026-06-30", filing_date="2026-08-12", statement="Consolidated"),
    ]
    result = module.FinancialResultsEngine._deduplicate(pd.DataFrame(rows))
    assert len(result) == 3
    assert set(result["standalone_or_consolidated"]) == {"Standalone", "Consolidated"}
    assert set(result["filing_date"]) == {"2026-08-01", "2026-08-12"}


def test_source_master_fetch_uses_identity_encoding_and_official_endpoint(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"symbol": "TEST", "xbrl": "https://example.invalid/test.xml"}]

    class Session:
        def __init__(self):
            self.calls = []

        def get(self, url, **kwargs):
            self.calls.append((url, kwargs))
            return Response()

    session = Session()
    monkeypatch.setattr(module, "create_session", lambda origin: session)
    engine = module.FinancialResultsEngine(use_yfinance=False)
    frame, headers, _ = engine._fetch_master("01-04-2026", "31-07-2026")
    assert frame.iloc[0]["symbol"] == "TEST"
    assert session.calls[0][0].startswith(module.RESULTS_API)
    assert session.calls[0][1]["headers"]["Accept-Encoding"] == "identity"
    assert headers["Accept-Encoding"] == "identity"


def test_existing_window_does_not_suppress_new_symbol(monkeypatch):
    existing = pd.DataFrame([_row("OLD", "2026-06-30", filing_date="2026-08-01")])
    saved = []
    observed_skip_labels = []
    engine = module.FinancialResultsEngine(use_yfinance=False)
    engine._load_existing = lambda: existing
    engine._fetch_bulk_nselib = lambda skip_labels: (
        observed_skip_labels.append(skip_labels) or
        [_row("NEW", "2026-06-30", filing_date="2026-08-02")]
    )
    engine._save = lambda frame: saved.append(frame)

    assert engine.run() is True
    assert observed_skip_labels == [set()]
    assert set(saved[0]["symbol"]) == {"OLD", "NEW"}


def test_unchanged_normalized_result_is_not_rewritten():
    existing = pd.DataFrame([_row("TEST", "2026-06-30", filing_date="2026-08-01")])
    saved = []
    engine = module.FinancialResultsEngine(use_yfinance=False)
    engine._load_existing = lambda: existing
    engine._fetch_bulk_nselib = lambda skip_labels: [
        _row("TEST", "2026-06-30", filing_date="2026-08-01")
    ]
    engine._save = lambda frame: saved.append(frame)

    assert engine.run() is True
    assert saved == []
