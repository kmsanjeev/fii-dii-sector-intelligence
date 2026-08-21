"""Governed provenance and period semantics for provider-local fundamentals.

This module is intentionally additive.  It does not replace the legacy
fundamental fields consumed by existing screens; it describes their evidence
quality and makes unsafe interpretations visible to stock and cross-layer
consumers.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.services import data_loader

CONTRACT_VERSION = "fundamental-evidence-1.0"
_MASTER_PATH = Path("data/NSE/equity_master/company_fundamentals_master.csv")
_REFERENCE_PATH = Path("data/reference/company_fundamentals_master.csv")

EXPECTED_FIELDS = (
    "revenue_ttm_cr",
    "profit_ttm_cr",
    "eps_ttm",
    "yoy_revenue_pct",
    "yoy_profit_pct",
    "opm_pct",
    "roce_pct",
    "book_value_per_share",
    "sales_growth_cagr_pct",
    "pe_ratio",
    "pb_ratio",
    "roe_pct",
)
_EXT_FIELDS = {
    "opm_pct", "roce_pct", "book_value_per_share", "total_equity_cr",
    "capital_employed_cr", "ebitda_cr_latest", "ebit_cr_latest",
    "sales_growth_cagr_pct", "sales_growth_years",
}
_VALUATION_FIELDS = {
    "pe_ratio", "pb_ratio", "roe_pct", "pe_score", "roe_score",
    "growth_score", "valuation_score", "valuation_label", "as_of_date",
}
_FINANCIAL_SECTOR_WORDS = (
    "BANK", "NBFC", "FINANC", "INSURANCE", "LIFE", "HOUSING FINANCE",
    "MICROFINANCE", "BROKING", "ASSET MANAGEMENT",
)


def _value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _number(value: Any) -> float | None:
    value = _value(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) and number not in (float("inf"), float("-inf")) else None


def _iso(value: Any) -> str | None:
    parsed = pd.to_datetime(_value(value), errors="coerce")
    if pd.isna(parsed) or parsed.year < 2000 or parsed.year > 2100:
        return None
    return parsed.date().isoformat()


def _retrieved_at(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
    except OSError:
        return None


@lru_cache(maxsize=16)
def _local_frame(name: str, path_text: str) -> pd.DataFrame:
    """Use the shared loader when warm, with a bounded provider-local fallback."""
    frame = data_loader.get(name)
    if frame is not None:
        return frame
    path = Path(path_text)
    try:
        return pd.read_csv(path, low_memory=False)
    except (OSError, ValueError):
        return pd.DataFrame()


def _freshness(period_end: str | None, frequency: str, today: date) -> dict[str, Any]:
    if not period_end:
        return {"state": "UNKNOWN", "basis": "PERIOD_END", "lag_days": None}
    lag = (today - date.fromisoformat(period_end)).days
    if lag < 0:
        return {"state": "QUALITY_WARNING", "basis": "PERIOD_END", "lag_days": lag}
    limits = {"QUARTERLY": 150, "TTM": 210, "ANNUAL": 450, "MASTER": 90}
    limit = limits.get(frequency, 210)
    state = "CURRENT" if lag <= limit else "STALE"
    if lag > limit * 2:
        state = "VERY_STALE"
    return {"state": state, "basis": "PERIOD_END", "lag_days": lag}


def _period(*, frequency: str, end: str | None, start: str | None = None,
            label: str | None = None, components: int | None = None) -> dict[str, Any]:
    return {
        "frequency": frequency,
        "period_start": start,
        "period_end": end,
        "label": label,
        "component_periods": components,
    }


def _observation(
    value: Any,
    *,
    field: str,
    source: str,
    dataset: str,
    authority: str,
    directness: str,
    period: dict[str, Any],
    filing_date: str | None = None,
    retrieved_at: str | None = None,
    status: str = "AVAILABLE",
    missing_reason: str | None = None,
    limitations: list[str] | None = None,
    today: date,
    applicable: str = "APPLICABLE",
) -> dict[str, Any]:
    value = _value(value)
    if value is None and status == "AVAILABLE":
        status = "NOT_AVAILABLE"
        missing_reason = missing_reason or "VALUE_MISSING"
    end = period.get("period_end")
    return {
        "field": field,
        "value": value,
        "unit": "PERCENT" if field.endswith("_pct") else "CRORE" if field.endswith("_cr") else None,
        "status": status,
        "missing_reason": missing_reason,
        "source": source,
        "source_dataset": dataset,
        "source_authority": authority,
        "direct_or_derived": directness,
        "period": period,
        "dates": {
            "period_end": end,
            "filing_date": filing_date,
            "retrieved_at": retrieved_at,
        },
        "freshness": _freshness(end, period.get("frequency", "UNKNOWN"), today),
        "applicability": applicable,
        "limitations": limitations or [],
    }


def _select_quarter_rows(frame: pd.DataFrame | None, symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty or "symbol" not in frame.columns:
        return pd.DataFrame()
    out = frame[frame["symbol"].astype(str).str.upper().str.strip() == symbol].copy()
    if out.empty:
        return out
    out["_period_end"] = pd.to_datetime(out.get("date_end"), errors="coerce")
    out = out.dropna(subset=["_period_end"])
    if out.empty:
        return out
    # Prefer consolidated filings when the same period has both variants.
    if "standalone_or_consolidated" in out.columns:
        out["_consolidated"] = out["standalone_or_consolidated"].astype(str).str.upper().str.contains("CONSOL")
    else:
        out["_consolidated"] = False
    return (
        out.sort_values(["_period_end", "_consolidated"])
        .drop_duplicates("_period_end", keep="last")
        .sort_values("_period_end")
        .reset_index(drop=True)
    )


def compute_complete_ttm(frame: pd.DataFrame | None, symbol: str) -> dict[str, Any]:
    """Return complete four-period TTM values; never annualize partial data."""
    rows = _select_quarter_rows(frame, symbol.upper())
    if len(rows) < 4:
        return {"status": "INSUFFICIENT_PERIODS", "component_periods": len(rows), "values": {}}
    rows = rows.tail(4)
    values: dict[str, float | None] = {}
    for field in ("revenue_cr", "net_profit_cr", "eps"):
        numeric = pd.to_numeric(rows.get(field), errors="coerce")
        values[field] = round(float(numeric.sum()), 6) if len(numeric) == 4 and numeric.notna().all() else None
    return {
        "status": "AVAILABLE" if any(value is not None for value in values.values()) else "INVALID_VALUE",
        "component_periods": 4,
        "period_end": rows["_period_end"].max().date().isoformat(),
        "period_start": rows["_period_end"].min().date().isoformat(),
        "values": values,
        "periods": [item.date().isoformat() for item in rows["_period_end"]],
    }


def _growth(frame: pd.DataFrame | None, symbol: str) -> dict[str, Any]:
    rows = _select_quarter_rows(frame, symbol.upper())
    if len(rows) < 8:
        return {"status": "INSUFFICIENT_PERIODS", "values": {}}
    latest, previous = rows.tail(4), rows.iloc[-8:-4]
    result: dict[str, float | None] = {}
    for field, output in (("revenue_cr", "yoy_revenue_pct"), ("net_profit_cr", "yoy_profit_pct")):
        current = pd.to_numeric(latest.get(field), errors="coerce")
        prior = pd.to_numeric(previous.get(field), errors="coerce")
        total_current = float(current.sum()) if current.notna().all() else None
        total_prior = float(prior.sum()) if prior.notna().all() else None
        result[output] = round((total_current / total_prior - 1) * 100, 4) if total_current is not None and total_prior not in (None, 0) else None
    return {"status": "AVAILABLE", "values": result}


def _load_master(symbol: str) -> dict[str, Any]:
    try:
        frame = pd.read_csv(_MASTER_PATH, dtype=str)
        row = frame[frame.get("symbol", pd.Series(dtype=str)).astype(str).str.upper() == symbol]
        if row.empty:
            return {}
        return {key: _value(value) for key, value in row.iloc[0].to_dict().items()}
    except (OSError, ValueError, KeyError):
        return {}


def _load_reference(symbol: str) -> dict[str, Any]:
    try:
        frame = pd.read_csv(_REFERENCE_PATH, dtype=str)
        row = frame[frame.get("SYMBOL", pd.Series(dtype=str)).astype(str).str.upper() == symbol]
        return {key: _value(value) for key, value in row.iloc[0].to_dict().items()} if not row.empty else {}
    except (OSError, ValueError, KeyError):
        return {}


def _financial_sector(sector: str | None) -> bool:
    value = str(sector or "").upper()
    return any(word in value for word in _FINANCIAL_SECTOR_WORDS)


def build_fundamental_evidence(
    symbol: str,
    *,
    fundamentals: dict[str, Any] | None = None,
    sector: str | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    """Build the additive field-level fundamental evidence contract."""
    symbol = str(symbol).upper().strip()
    today = today or datetime.now(tz=timezone.utc).date()
    fundamentals = fundamentals or {}
    master = _load_master(symbol)
    reference = _load_reference(symbol)
    sector = sector or _value(master.get("sector_platform"))
    financial = _financial_sector(sector)
    quarterly = _local_frame("quarterly_results", str(data_loader.SOURCES["quarterly_results"]))
    extended = _local_frame("extended_financials", str(data_loader.SOURCES["extended_financials"]))
    valuation = _local_frame("valuation_scores", str(data_loader.SOURCES["valuation_scores"]))
    ttm = compute_complete_ttm(quarterly, symbol)
    growth = _growth(quarterly, symbol)
    observations: dict[str, dict[str, Any]] = {}
    qr_path = data_loader.SOURCES["quarterly_results"]
    ext_path = data_loader.SOURCES["extended_financials"]
    val_path = data_loader.SOURCES["valuation_scores"]
    qr_rows = _select_quarter_rows(quarterly, symbol)
    latest_q = qr_rows.iloc[-1] if not qr_rows.empty else None
    latest_period_end = latest_q["_period_end"].date().isoformat() if latest_q is not None else None
    latest_filing = _iso(latest_q.get("filing_date")) if latest_q is not None else None
    ttm_period = _period(frequency="TTM", end=ttm.get("period_end"), start=ttm.get("period_start"), components=ttm.get("component_periods"))
    for field, raw in (("revenue_ttm_cr", ttm.get("values", {}).get("revenue_cr")), ("profit_ttm_cr", ttm.get("values", {}).get("net_profit_cr")), ("eps_ttm", ttm.get("values", {}).get("eps"))):
        observations[field] = _observation(raw, field=field, source="NSE XBRL quarterly results", dataset="quarterly_results.csv", authority="PRIMARY_PROVIDER_SOURCE", directness="DERIVED_FROM_QUARTERLY_COMPONENTS", period=ttm_period, filing_date=latest_filing, retrieved_at=_retrieved_at(qr_path), status="AVAILABLE" if raw is not None else ttm.get("status", "NOT_AVAILABLE"), missing_reason=None if raw is not None else "TTM_REQUIRES_FOUR_VALID_COMPARABLE_PERIODS", today=today)
    for field in ("yoy_revenue_pct", "yoy_profit_pct"):
        raw = growth.get("values", {}).get(field)
        observations[field] = _observation(raw, field=field, source="NSE XBRL quarterly results", dataset="quarterly_results.csv", authority="PRIMARY_PROVIDER_SOURCE", directness="DERIVED_FROM_QUARTERLY_COMPONENTS", period=ttm_period, filing_date=latest_filing, retrieved_at=_retrieved_at(qr_path), status="AVAILABLE" if raw is not None else growth.get("status", "NOT_AVAILABLE"), missing_reason=None if raw is not None else "YOY_REQUIRES_EIGHT_VALID_COMPARABLE_PERIODS", today=today)
    ext_row = None
    if extended is not None and not extended.empty and "symbol" in extended.columns:
        rows = extended[extended["symbol"].astype(str).str.upper().str.strip() == symbol]
        if not rows.empty:
            ext_row = rows.iloc[0]
    ext_end = _iso(ext_row.get("as_of_date")) if ext_row is not None else None
    ext_limitations = ["Extended financials are provider-local aggregates over fetched XBRL components; raw filing lineage is not retained in this output."]
    if financial:
        ext_limitations.append("Operating-margin, revenue, EBITDA and capital-employed comparisons are not directly comparable across financial-sector business models.")
    for field in _EXT_FIELDS:
        raw = _value(ext_row.get(field)) if ext_row is not None else _value(fundamentals.get(field))
        status = "AVAILABLE" if raw is not None else "NOT_AVAILABLE"
        observations[field] = _observation(raw, field=field, source="NSE XBRL extended financials", dataset="extended_financials.csv", authority="PRIMARY_PROVIDER_SOURCE", directness="DERIVED_PROVIDER_LOCAL", period=_period(frequency="ANNUAL_OR_LATEST_AGGREGATE", end=ext_end, label="provider aggregate"), retrieved_at=_retrieved_at(ext_path), status=status, missing_reason=None if raw is not None else "FIELD_NOT_PRESENT", limitations=ext_limitations, today=today, applicable="LIMITED_FOR_FINANCIAL_SECTOR" if financial and field in {"opm_pct", "capital_employed_cr", "ebitda_cr_latest", "ebit_cr_latest"} else "APPLICABLE")
    val_row = None
    if valuation is not None and not valuation.empty and "symbol" in valuation.columns:
        rows = valuation[valuation["symbol"].astype(str).str.upper().str.strip() == symbol]
        if not rows.empty:
            val_row = rows.iloc[0]
    val_end = _iso(val_row.get("as_of_date")) if val_row is not None else None
    for field in _VALUATION_FIELDS:
        if field == "roe_pct":
            observations[field] = _observation(None, field=field, source="Legacy valuation output", dataset="valuation_scores.csv", authority="LEGACY_PROVIDER_OUTPUT", directness="UNTRUSTED_SEMANTICS", period=_period(frequency="UNKNOWN", end=val_end), retrieved_at=_retrieved_at(val_path), status="UNTRUSTED_SOURCE", missing_reason="LEGACY_COLUMN_IS_NET_MARGIN_NOT_ROE", limitations=["The legacy valuation engine populated roe_pct with net margin; it is not promoted as ROE."], today=today)
            continue
        raw = _value(val_row.get(field)) if val_row is not None else _value(fundamentals.get(field))
        observations[field] = _observation(raw, field=field, source="Legacy provider valuation output", dataset="valuation_scores.csv", authority="LEGACY_PROVIDER_OUTPUT", directness="DERIVED_LEGACY_OUTPUT", period=_period(frequency="UNKNOWN", end=val_end), retrieved_at=_retrieved_at(val_path), status="AVAILABLE" if raw is not None else "NOT_AVAILABLE", missing_reason=None if raw is not None else "FIELD_NOT_PRESENT", limitations=["PE/PB are ratios only; valuation_label and composite scores are not a governed fair-value conclusion."], today=today)
    source_conflicts: list[dict[str, Any]] = []
    valuation_pe = _number(val_row.get("pe_ratio")) if val_row is not None else None
    reference_pe = _number(reference.get("PE_RATIO"))
    if valuation_pe is not None and reference_pe is not None and abs(valuation_pe - reference_pe) > 0.01:
        source_conflicts.append({"field": "pe_ratio", "sources": ["valuation_scores.csv", "reference/company_fundamentals_master.csv"], "values": {"valuation_scores": valuation_pe, "reference": reference_pe}, "resolution": "REFERENCE_SOURCE_NOT_AUTHORITATIVE", "state": "CONFLICT_EXPOSED"})
    usable = sum(item["status"] == "AVAILABLE" for item in observations.values())
    source_dates = [item["dates"]["period_end"] for item in observations.values() if item["dates"]["period_end"]]
    freshness_rank = {"QUALITY_WARNING": 5, "VERY_STALE": 4, "STALE": 3, "UNKNOWN": 2, "CURRENT": 1}
    freshness_states = [item["freshness"]["state"] for item in observations.values() if item["status"] == "AVAILABLE"]
    freshness_state = max(freshness_states, key=lambda item: freshness_rank.get(item, 2)) if freshness_states else "UNKNOWN"
    return {
        "contract_version": CONTRACT_VERSION,
        "symbol": symbol,
        "identity_source": "NSE_EQUITY_MASTER+FUNDAMENTALS_MASTER" if master else "NSE_EQUITY_MASTER",
        "sector": sector,
        "observations": observations,
        "coverage": {"expected_fields": len(EXPECTED_FIELDS), "observed_fields": len(observations), "usable_fields": usable, "coverage_pct": round(usable / len(observations) * 100, 2) if observations else 0.0, "quality": "HIGH" if usable >= 8 else "MEDIUM" if usable >= 4 else "LIMITED" if usable else "INSUFFICIENT"},
        "freshness": {"state": freshness_state, "basis": "FREQUENCY_AWARE_PERIOD_END", "component_states": freshness_states},
        "dates": {"latest_period_end": max(source_dates) if source_dates else None, "latest_quarter_end": latest_period_end, "latest_filing_date": latest_filing, "retrieved_at": max((item["dates"]["retrieved_at"] for item in observations.values() if item["dates"]["retrieved_at"]), default=None)},
        "frequency": {"reporting": "QUARTERLY", "derived": ["TTM", "YOY"], "freshness_basis": "PERIOD_END_NOT_RETRIEVAL_DATE"},
        "source_conflicts": source_conflicts,
        "limitations": ["Fundamental observations are descriptive evidence, not a recommendation, target price, fair-value conclusion, or prediction.", "Source date, reporting period, filing date and local retrieval time remain separate.", "Missing, invalid, negative and not-applicable values are not converted to zero."] + (["Financial-sector metrics require sector-specific interpretation; industrial OPM/EBITDA/capital-employed comparisons are limited."] if financial else []),
        "legacy_fields": {key: _value(value) for key, value in fundamentals.items() if key in _VALUATION_FIELDS or key.startswith("_")},
    }
