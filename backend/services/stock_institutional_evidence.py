"""Authoritative stock-level institutional evidence contract.

This module is deliberately narrower than a flow engine.  It exposes the
evidence that the repository actually has:

* NSE-disclosed bulk/block deal rows, with source-date semantics preserved;
* quarterly shareholding snapshots and independently computed changes; and
* the existing rolling deal summary only as a derived, heuristic signal.

It does not turn a client-name classifier into a direct FII/DII tape and it
does not infer stock-level activity from market-wide participant data.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from backend.services import data_loader

CONTRACT_VERSION = "stock-institutional-evidence-1.1"
DIRECT_DAILY_FLOW_DECISION = "NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE"
DIRECT_SECTOR_FLOW_DECISION = "NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE"
MAX_TRANSACTION_ROWS = 50
DEAL_SOURCE_ID = "NSE_DISCLOSED_BULK_BLOCK_DEAL_LOCAL_EXTRACT"
OWNERSHIP_SOURCE_ID = "NSE_SHAREHOLDING_LOCAL_EXTRACT"
EVIDENCE_TAXONOMY = {
    "direct_transactions": "DIRECT_DISCLOSED_TRANSACTION_ACTIVITY",
    "ownership": "QUARTERLY_OWNERSHIP_SNAPSHOT",
    "ownership_change": "DERIVED_OWNERSHIP_CONFIRMATION",
    "derived_signal": "DERIVED_HEURISTIC_DEAL_SUMMARY",
    "market_context": "MARKET_LEVEL_CONTEXT_ONLY",
    "unsupported_daily_stock_flow": DIRECT_DAILY_FLOW_DECISION,
    "unsupported_sector_flow": DIRECT_SECTOR_FLOW_DECISION,
}

_SOURCE_PRIORITY = {"nse_xbrl": 0, "screener": 1, "master_only": 2}
_KNOWN_DERIVED_CLASSES = {"FII", "MF", "INSURANCE", "PROMOTER"}


def _value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _number(value: Any, digits: int = 4) -> float | None:
    value = _value(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, digits) if pd.notna(number) else None


def _iso_date(value: Any) -> str | None:
    value = _value(value)
    if value in (None, "", "nan", "NaT"):
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.date().isoformat()
    text = str(value).strip()
    parsed = pd.to_datetime(
        text,
        errors="coerce",
        dayfirst=not re.fullmatch(r"\d{4}-\d{2}-\d{2}", text),
    )
    if pd.isna(parsed):
        return None
    return parsed.date().isoformat()


def _normalize_name(value: Any) -> str | None:
    value = _value(value)
    if value in (None, ""):
        return None
    normalized = re.sub(r"[^A-Z0-9]+", " ", str(value).upper()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized or None


def _stable_record_id(source_id: str, fields: dict[str, Any]) -> str:
    payload = json.dumps(fields, sort_keys=True, default=str, separators=(",", ":"))
    digest = hashlib.sha256(f"{source_id}|{payload}".encode()).hexdigest()[:24]
    return f"{source_id.lower()}-{digest}"


def _freshness_for_frequency(
    latest_date: str | None,
    frequency: str,
    *,
    reference_date: date | None = None,
) -> dict[str, Any]:
    """Classify freshness against the cadence, not a universal EOD rule."""
    parsed = pd.to_datetime(latest_date, errors="coerce") if latest_date else pd.NaT
    if pd.isna(parsed):
        return {"state": "UNKNOWN_FREQUENCY", "frequency": frequency, "latest_date": latest_date, "lag_days": None}
    today = reference_date or datetime.now(timezone.utc).date()
    lag_days = (today - parsed.date()).days
    if lag_days < 0:
        state = "QUALITY_WARNING"
    elif frequency == "DAILY":
        state = "CURRENT_FOR_FREQUENCY" if lag_days <= 3 else "DELAYED_FOR_FREQUENCY" if lag_days <= 10 else "STALE_FOR_FREQUENCY"
    elif frequency == "QUARTERLY":
        state = "CURRENT_FOR_FREQUENCY" if lag_days <= 120 else "DELAYED_FOR_FREQUENCY" if lag_days <= 240 else "STALE_FOR_FREQUENCY"
    elif frequency == "EVENT_DRIVEN":
        state = "CURRENT_FOR_FREQUENCY" if lag_days <= 30 else "DELAYED_FOR_FREQUENCY" if lag_days <= 90 else "STALE_FOR_FREQUENCY"
    else:
        state = "UNKNOWN_FREQUENCY"
    return {"state": state, "frequency": frequency, "latest_date": latest_date, "lag_days": lag_days}


def _latest_frame_date(frame: pd.DataFrame, column: str) -> str | None:
    if frame.empty or column not in frame.columns:
        return None
    values = frame[column].astype(str).str.strip()
    parsed = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    iso_mask = values.str.fullmatch(r"\d{4}-\d{2}-\d{2}")
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(values.loc[iso_mask], errors="coerce", format="%Y-%m-%d")
    if (~iso_mask).any():
        parsed.loc[~iso_mask] = pd.to_datetime(values.loc[~iso_mask], errors="coerce", format="mixed", dayfirst=True)
    parsed = parsed.dropna()
    return parsed.max().date().isoformat() if not parsed.empty else None


def _security_resolution(identity: dict[str, Any], source_companies: set[str] | None = None) -> dict[str, Any]:
    symbol = str(identity.get("symbol") or "").upper().strip()
    isin = str(identity.get("isin") or "").upper().strip() or None
    isin_valid = bool(isin and re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin))
    identified = identity.get("identity_state") == "IDENTIFIED" and bool(symbol)
    if identified and isin_valid:
        state = "EXACT_IDENTITY"
    elif identified:
        state = "HIGH_CONFIDENCE_MAPPED"
    else:
        state = "REVIEW_REQUIRED"
    canonical_company = _normalize_name(identity.get("company"))
    company_names = {name for name in (source_companies or set()) if name}
    if not company_names:
        company_state = "NOT_AVAILABLE"
    elif canonical_company and all(_normalize_name(name) == canonical_company for name in company_names):
        company_state = "EXACT_IDENTITY"
    else:
        company_state = "REVIEW_REQUIRED"
    return {
        "state": state,
        "authority": identity.get("identity_source") or "NSE_EQUITY_MASTER",
        "canonical_symbol": symbol or None,
        "canonical_isin": isin,
        "isin_resolution": "MATCHED" if isin_valid else "NOT_AVAILABLE_OR_INVALID",
        "symbol_resolution": "EXACT_SYMBOL" if identified else "REVIEW_REQUIRED",
        "company_name_resolution": company_state,
        "source_exchange": "NSE",
        "limitations": (["ISIN is unavailable or failed format validation."] if identified and not isin_valid else [])
        + (["Source company name differs from the canonical identity; review required."] if company_state == "REVIEW_REQUIRED" else []),
    }


def _frame_symbol(frame: pd.DataFrame | None, symbol: str) -> pd.DataFrame:
    if frame is None or frame.empty or "symbol" not in frame.columns:
        return pd.DataFrame()
    return frame[frame["symbol"].astype(str).str.upper() == symbol.upper()].copy()


def _json_record(row: pd.Series, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: _value(row.get(field)) for field in fields}


def _identity_status(identity: dict[str, Any]) -> str:
    if identity.get("identity_state") != "IDENTIFIED":
        return "REVIEW_REQUIRED"
    if not identity.get("isin"):
        return "IDENTIFIED_SYMBOL_ISIN_NOT_AVAILABLE"
    return "IDENTIFIED_EXACT_SYMBOL_AND_ISIN"


def _classify_participant(raw_label: Any, raw_name: Any) -> dict[str, Any]:
    """Preserve the engine label without treating its fallback as reported.

    The upstream engine uses keyword heuristics over client names and falls
    back to ``RETAIL``.  That fallback is not an exchange participant field,
    so it is intentionally exposed as UNKNOWN here.
    """
    label = str(_value(raw_label) or "").upper().strip()
    raw_name = _value(raw_name)
    normalized_name = _normalize_name(raw_name)
    if label in _KNOWN_DERIVED_CLASSES:
        return {
            "raw_label": label,
            "participant_raw_name": raw_name,
            "participant_normalized_name": normalized_name,
            "normalized_class": label,
            "classification_method": "HEURISTIC",
            "classification_status": "DERIVED_HEURISTIC",
            "classification_source": "block_bulk_deal_engine._classify_client",
            "classification_confidence": "CONDITIONAL",
            "authority": "PRACTITIONER_OR_PLATFORM_HEURISTIC",
            "confidence": "CONDITIONAL",
        }
    return {
        "raw_label": label or None,
        "participant_raw_name": raw_name,
        "participant_normalized_name": normalized_name,
        "normalized_class": "UNKNOWN",
        "classification_method": "UNKNOWN",
        "classification_status": "UNKNOWN",
        "classification_source": "NOT_REPORTED_IN_CURRENT_SOURCE",
        "classification_confidence": "LOW",
        "authority": "NOT_REPORTED_IN_CURRENT_SOURCE",
        "confidence": "LOW",
    }


def _deal_record(row: pd.Series, security_resolution: dict[str, Any]) -> dict[str, Any]:
    participant = _classify_participant(row.get("participant"), row.get("client_name"))
    source_date = _iso_date(row.get("date"))
    record_fields = {
        "date": source_date,
        "symbol": str(_value(row.get("symbol")) or "").upper(),
        "deal_type": str(_value(row.get("deal_type")) or "").upper(),
        "client_name": _value(row.get("client_name")),
        "direction": _value(row.get("direction")),
        "qty": _number(row.get("qty"), 2),
        "price": _number(row.get("price"), 4),
        "value_cr": _number(row.get("value_cr"), 4),
    }
    record_id = _stable_record_id(DEAL_SOURCE_ID, record_fields)
    return {
        "source_id": DEAL_SOURCE_ID,
        "source_record_id": record_id,
        "record_id": record_id,
        "symbol": str(_value(row.get("symbol")) or "").upper(),
        "company": _value(row.get("company")),
        "deal_type": str(_value(row.get("deal_type")) or "").upper(),
        "client_name": _value(row.get("client_name")),
        "participant": participant,
        "security_identity": {
            "symbol": security_resolution.get("canonical_symbol"),
            "isin": security_resolution.get("canonical_isin"),
            "resolution_state": security_resolution.get("state"),
        },
        "direction": _value(row.get("direction")),
        "quantity": _number(row.get("qty"), 2),
        "price": _number(row.get("price"), 4),
        "value_cr": _number(row.get("value_cr"), 4),
        "source_date": source_date,
        "date_fields": {
            "transaction_date": None,
            "disclosure_date": None,
            "reporting_period": None,
            "filing_date": None,
            "effective_date": None,
            "acquisition_date": None,
            "exchange_publication_date": None,
            "reporting_period_end": None,
            "retrieved_at": None,
            "derived_as_of": None,
            "source_date": source_date,
            "source_date_semantics": "NSE_DAILY_DEAL_REPORT_DATE; transaction-versus-disclosure distinction is not separately present in this local extract",
        },
        "date_semantics": "DATE_SEMANTICS_LIMITED",
        "seq_id": _number(row.get("seq_id"), 0),
    }


def _deal_evidence(deals: pd.DataFrame, security_resolution: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if deals.empty:
        return {
            "state": "NOT_AVAILABLE",
            "record_count": 0,
            "latest_source_date": None,
            "source": "NSE_BULK_BLOCK_DEAL_REPORT_LOCAL_EXTRACT",
        }, []
    deals = deals.copy()
    before_dedupe = len(deals)
    dedupe_fields = ["date", "symbol", "deal_type", "client_name", "direction", "qty", "price", "value_cr"]
    available_dedupe_fields = [field for field in dedupe_fields if field in deals.columns]
    deals = deals.drop_duplicates(subset=available_dedupe_fields, keep="first")
    deals["_date"] = deals.get("date").map(_iso_date).pipe(pd.to_datetime, errors="coerce")
    deals = deals.sort_values(["_date", "seq_id"], ascending=[False, False], na_position="last")
    all_records = [_deal_record(row, security_resolution) for _, row in deals.iterrows()]
    records = all_records[:MAX_TRANSACTION_ROWS]
    latest_source_date = _iso_date(deals["_date"].max())
    return {
        "state": "AVAILABLE",
        "record_count": len(deals),
        "returned_record_count": len(records),
        "latest_source_date": latest_source_date,
        "source": "NSE_BULK_BLOCK_DEAL_REPORT_LOCAL_EXTRACT",
        "truncated": len(deals) > len(records),
        "duplicate_count_removed": before_dedupe - len(deals),
        "deduplication": "DETERMINISTIC_SOURCE_FIELDS",
        "source_record_ids": [record["source_record_id"] for record in all_records],
        "frequency": "DAILY",
        "freshness_for_frequency": _freshness_for_frequency(latest_source_date, "DAILY"),
        "reproducibility_state": "LOCAL_ARCHIVE_DEPENDENT",
        "limitations": [
            "A disclosed bulk/block deal is direct deal activity, not a complete daily FII/DII stock-flow tape.",
            "Participant classes in this local extract are derived from client-name heuristics unless the source reports the class explicitly.",
        ],
    }, records


def _ownership_row(row: pd.Series) -> dict[str, Any]:
    source_record_id = _stable_record_id(
        OWNERSHIP_SOURCE_ID,
        {
            "symbol": _value(row.get("symbol")),
            "quarter_end_date": _iso_date(row.get("quarter_end_date")),
            "submission_date": _iso_date(row.get("submission_date")),
            "source": _value(row.get("source")),
        },
    )
    return {
        "source_id": OWNERSHIP_SOURCE_ID,
        "source_record_id": source_record_id,
        "quarter_end_date": _iso_date(row.get("quarter_end_date")),
        "submission_date": _iso_date(row.get("submission_date")),
        "reporting_period": _value(row.get("window_label", row.get("period"))),
        "promoter_pct": _number(row.get("promoter_pct"), 4),
        "fii_pct": _number(row.get("fii_pct"), 4),
        "dii_pct": _number(row.get("dii_pct"), 4),
        "public_pct": _number(row.get("public_pct"), 4),
        "source": _value(row.get("source")),
        "retrieved_at": None,
    }


def _ownership_evidence(symbol: str) -> dict[str, Any]:
    frame = _frame_symbol(data_loader.get("shareholding"), symbol)
    if frame.empty:
        frame = _frame_symbol(data_loader.get("holding_trends"), symbol)
    if frame.empty:
        return {
            "state": "NOT_AVAILABLE",
            "frequency": "QUARTERLY",
            "latest": None,
            "prior": None,
            "change": {},
            "limitations": ["No stock-specific quarterly ownership snapshot is available."],
            "lineage_state": "NOT_AVAILABLE",
        }

    frame = frame.copy()
    if "window_label" not in frame.columns and "period" in frame.columns:
        frame["window_label"] = frame["period"]
    frame["_quarter"] = frame.get("quarter_end_date").map(_iso_date).pipe(pd.to_datetime, errors="coerce")
    frame["_source_rank"] = frame.get("source", pd.Series(index=frame.index, dtype=str)).map(_SOURCE_PRIORITY).fillna(9)
    frame = frame.sort_values(["_quarter", "_source_rank"], ascending=[False, True], na_position="last")
    usable: list[pd.Series] = []
    seen: set[str] = set()
    for _, row in frame.iterrows():
        key = _iso_date(row.get("quarter_end_date")) or ""
        if not key or key in seen:
            continue
        seen.add(key)
        usable.append(row)
        if len(usable) == 2:
            break
    if not usable:
        return {
            "state": "QUALITY_WARNING",
            "frequency": "QUARTERLY",
            "latest": None,
            "prior": None,
            "change": {},
            "limitations": ["Ownership rows exist but no valid quarter-end date could be parsed."],
        }
    latest = _ownership_row(usable[0])
    prior = _ownership_row(usable[1]) if len(usable) > 1 else None
    change: dict[str, float | None] = {}
    if prior:
        for field in ("promoter_pct", "fii_pct", "dii_pct", "public_pct"):
            current, previous = latest.get(field), prior.get(field)
            change[field] = round(current - previous, 4) if current is not None and previous is not None else None
    latest_quarter = latest.get("quarter_end_date")
    source_taxonomy = {row.get("source") for row in (latest, prior) if row and row.get("source")}
    comparability = "COMPARABLE" if prior and len(source_taxonomy) <= 1 else "NOT_COMPARABLE"
    return {
        "state": "AVAILABLE",
        "frequency": "QUARTERLY",
        "latest": latest,
        "prior": prior,
        "change": change,
        "comparability": {
            "state": comparability,
            "metrics": ["promoter_pct", "fii_pct", "dii_pct", "public_pct"],
            "source_taxonomy": sorted(source_taxonomy),
        },
        "period": {"latest": latest.get("reporting_period"), "prior": prior.get("reporting_period") if prior else None},
        "lineage": {
            "state": "REPRODUCIBLE_FROM_LOCAL_SNAPSHOT",
            "source_record_ids": [row["source_record_id"] for row in (latest, prior) if row],
        },
        "freshness_for_frequency": _freshness_for_frequency(latest_quarter, "QUARTERLY"),
        "limitations": [
            "Quarterly ownership change is an ownership snapshot comparison, not a daily transaction flow.",
            "Submission date and quarter-end date are preserved separately.",
        ],
    }


def _derived_signal(symbol: str, raw_deals: pd.DataFrame) -> dict[str, Any] | None:
    row = _frame_symbol(data_loader.get("deal_signals"), symbol)
    if row.empty:
        return None
    item = row.iloc[0]
    as_of_date = _iso_date(item.get("as_of_date"))
    window_days = int(_number(item.get("window_days"), 0) or 0)
    source_ids: list[str] = []
    if as_of_date and window_days:
        cutoff = pd.Timestamp(as_of_date) - pd.Timedelta(days=window_days)
        for _, deal in raw_deals.copy().iterrows():
            deal_date = pd.to_datetime(_iso_date(deal.get("date")), errors="coerce")
            if pd.notna(deal_date) and cutoff <= deal_date <= pd.Timestamp(as_of_date):
                source_ids.append(_deal_record(deal, {}).get("source_record_id"))
    return {
        "source_id": "INSTITUTIONAL_DEAL_SIGNALS_DERIVED",
        "state": "AVAILABLE",
        "type": "DERIVED_HEURISTIC_30D_DEAL_SUMMARY",
        "total_deals": _number(item.get("total_deals"), 0),
        "heuristically_classified_deals": _number(item.get("inst_deals"), 0),
        "heuristic_fii_net_value_cr": _number(item.get("fii_net_value_cr")),
        "heuristic_mf_net_value_cr": _number(item.get("mf_net_value_cr")),
        "heuristic_promoter_net_value_cr": _number(item.get("promoter_net_value_cr")),
        "dominant_participant": _value(item.get("dominant_participant")),
        "deal_signal": _value(item.get("deal_signal")),
        "last_deal_date": _iso_date(item.get("last_deal_date")),
        "as_of_date": as_of_date,
        "window_days": window_days,
        "source_record_ids": sorted(set(source_ids)),
        "source_record_count": len(set(source_ids)),
        "lineage_state": "PARTIALLY_REPRODUCIBLE",
        "lineage": "institutional_deal_signals.csv derived from block_bulk_deals.csv using client-name keyword heuristics; source record IDs are deterministic",
        "interpretation": "Derived summary only; not direct FII/DII attribution.",
    }


def _market_context() -> dict[str, Any]:
    frame = data_loader.get("participant_flows")
    if frame is None or frame.empty:
        return {"state": "NOT_AVAILABLE", "scope": "MARKET_LEVEL_CONTEXT_ONLY"}
    row = frame.sort_values("date").iloc[-1] if "date" in frame.columns else frame.iloc[-1]
    return {
        "state": "AVAILABLE",
        "scope": "MARKET_LEVEL_CONTEXT_ONLY",
        "as_of": _iso_date(row.get("date")),
        "fii_flow_score": _number(row.get("FII_flow_score"), 2),
        "dii_flow_score": _number(row.get("DII_flow_score"), 2),
        "limitation": "Market-level participant context is not attributed to this stock.",
    }


def _participant_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    statuses: dict[str, int] = {}
    unique_names: dict[str, dict[str, Any]] = {}
    for record in records:
        participant = record["participant"]
        label = participant["normalized_class"]
        counts[label] = counts.get(label, 0) + 1
        status = participant["classification_status"]
        statuses[status] = statuses.get(status, 0) + 1
        name = participant.get("participant_normalized_name") or "UNKNOWN"
        unique_names[name] = participant
    unique_statuses = {"SOURCE_REPORTED": 0, "REGULATORY_OR_CURATED": 0, "DETERMINISTIC_HIGH_CONFIDENCE_RULE": 0, "HEURISTIC": 0, "UNKNOWN": 0, "AMBIGUOUS": 0}
    for participant in unique_names.values():
        method = participant.get("classification_method")
        if method == "HEURISTIC":
            unique_statuses["HEURISTIC"] += 1
        elif method == "UNKNOWN":
            unique_statuses["UNKNOWN"] += 1
        elif method in unique_statuses:
            unique_statuses[method] += 1
    return {
        "counts": counts,
        "classification_status_counts": statuses,
        "unique_participant_names": len(unique_names),
        "unique_participant_metrics": unique_statuses,
        "raw_names_preserved": True,
        "high_confidence_count": unique_statuses["SOURCE_REPORTED"] + unique_statuses["REGULATORY_OR_CURATED"] + unique_statuses["DETERMINISTIC_HIGH_CONFIDENCE_RULE"],
        "unknown_remains_unknown": True,
        "note": "FII/MF/INSURANCE/PROMOTER labels are conditional heuristic classifications in this local deal extract; the RETAIL fallback is not treated as a reported class.",
    }


def build_stock_institutional_evidence(symbol: str, *, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    symbol = str(symbol).upper().strip()
    identity = identity or {"symbol": symbol, "identity_state": "NOT_PROVIDED"}
    identity_status = _identity_status(identity)
    raw_deals = _frame_symbol(data_loader.get("block_deals"), symbol)
    source_companies = set(raw_deals.get("company", pd.Series(dtype=str)).dropna().astype(str)) if not raw_deals.empty else set()
    security_resolution = _security_resolution(identity, source_companies)
    deal_meta, deal_records = _deal_evidence(raw_deals, security_resolution)
    ownership = _ownership_evidence(symbol)
    derived_signal = _derived_signal(symbol, raw_deals)
    market_context = _market_context()
    has_identity = identity.get("identity_state") == "IDENTIFIED"
    if not has_identity:
        scope = "IDENTITY_REVIEW_REQUIRED"
        data_state = "REVIEW_REQUIRED"
    elif deal_records:
        scope = "DEAL_ACTIVITY_CONTEXT"
        data_state = "PARTIAL"
    elif ownership.get("state") == "AVAILABLE":
        scope = "DERIVED_OWNERSHIP_CONFIRMATION"
        data_state = "PARTIAL"
    elif market_context.get("state") == "AVAILABLE":
        scope = "MARKET_LEVEL_CONTEXT_ONLY"
        data_state = "NOT_AVAILABLE"
    else:
        scope = "NOT_SUPPORTED"
        data_state = "NOT_AVAILABLE"

    component_dates = {
        "latest_deal_source_date": deal_meta.get("latest_source_date"),
        "latest_ownership_quarter_end": (ownership.get("latest") or {}).get("quarter_end_date"),
        "latest_ownership_submission": (ownership.get("latest") or {}).get("submission_date"),
        "derived_signal_as_of": (derived_signal or {}).get("as_of_date"),
    }
    return {
        "contract_version": CONTRACT_VERSION,
        "symbol": symbol,
        "isin": identity.get("isin"),
        "identity": {
            "symbol": symbol,
            "company": identity.get("company"),
            "isin": identity.get("isin"),
            "identity_state": identity.get("identity_state"),
            "identity_status": identity_status,
            "identity_source": identity.get("identity_source"),
            "security_resolution": security_resolution,
        },
        "scope": scope,
        "evidence_taxonomy": EVIDENCE_TAXONOMY,
        "as_of": component_dates,
        "data_status": {
            "state": data_state,
            "frequency": "MIXED_DISCLOSED_DEALS_AND_QUARTERLY_OWNERSHIP",
            "direct_daily_stock_flow_decision": DIRECT_DAILY_FLOW_DECISION,
            "direct_sector_flow_decision": DIRECT_SECTOR_FLOW_DECISION,
            "freshness_for_frequency": {
                "deals": deal_meta.get("freshness_for_frequency"),
                "ownership": ownership.get("freshness_for_frequency"),
                "derived_signal": _freshness_for_frequency((derived_signal or {}).get("as_of_date"), "DAILY"),
            },
        },
        "source_access": {
            "deal_tape": {
                "source_id": DEAL_SOURCE_ID,
                "authority": "NSE_DISCLOSED_REPORTS / SEBI_DISCLOSURE_FRAMEWORK",
                "access_state": "AVAILABLE_WITH_RESTRICTIONS",
                "stock_specific": True,
                "participant_specific": True,
                "transaction_level": True,
                "automation": "CONDITIONAL",
                "license": "NO_SEPARATE_LICENSE_RECORDED_FOR_CURRENT_LOCAL_EXTRACT",
                "reproducibility": "LOCAL_ARCHIVE_DEPENDENT",
            },
            "ownership": {
                "source_id": OWNERSHIP_SOURCE_ID,
                "authority": "NSE_SHAREHOLDING_FILINGS",
                "access_state": "AVAILABLE_WITH_RESTRICTIONS",
                "stock_specific": True,
                "participant_specific": False,
                "ownership_level": True,
                "automation": "CONDITIONAL",
                "license": "NO_SEPARATE_LICENSE_RECORDED_FOR_CURRENT_LOCAL_EXTRACT",
                "reproducibility": "REPRODUCIBLE_FROM_LOCAL_SNAPSHOT",
            },
        },
        "direct_transactions": {
            "state": deal_meta["state"],
            "records": deal_records,
            "source_semantics": "NSE_DISCLOSED_BULK_BLOCK_DEAL_ACTIVITY",
            "date_semantics": "SOURCE_DATE_ONLY; transaction and disclosure dates are not separately available in the local extract",
        },
        "bulk_deals": [record for record in deal_records if record.get("deal_type") == "BULK"],
        "block_deals": [record for record in deal_records if record.get("deal_type") == "BLOCK"],
        "ownership": ownership,
        "market_level_context": market_context,
        "participant_classes": _participant_summary(deal_records),
        "derived_signals": {"institutional_deal_summary": derived_signal},
        "evidence_quality": {
            "state": "CONDITIONAL" if deal_records or ownership.get("state") == "AVAILABLE" else "LIMITED",
            "type": "EVIDENCE_QUALITY_NOT_PREDICTIVE_CONFIDENCE",
            "reasons": [
                "Daily stock-level FII/DII flow is not available as a governed complete source.",
                "Client-name participant labels are heuristic and remain conditional.",
                "Ownership evidence is periodic and is not a transaction ledger.",
            ],
        },
        "facts": {
            "deal_activity": deal_meta,
            "ownership_change": ownership.get("change", {}),
            "dates": component_dates,
        },
        "signals": {
            "stock_specific_evidence": scope not in {"MARKET_LEVEL_CONTEXT_ONLY", "IDENTITY_REVIEW_REQUIRED"},
            "daily_fii_dii_flow": "NOT_AVAILABLE",
            "ownership_change_available": ownership.get("state") == "AVAILABLE" and bool(ownership.get("prior")),
            "deal_activity_available": bool(deal_records),
        },
        "interpretation": (
            "Disclosed bulk/block activity and/or periodic ownership evidence is available for this exact symbol; "
            "it does not establish a complete daily FII/DII flow or a universal institutional accumulation claim."
            if scope not in {"MARKET_LEVEL_CONTEXT_ONLY", "NOT_SUPPORTED", "IDENTITY_REVIEW_REQUIRED"}
            else "No governed stock-specific direct FII/DII flow evidence is available for this symbol."
        ),
        "limitations": [
            "Market-level FII/DII participant data is not attributed to this stock.",
            "No direct daily stock-level FII/DII flow source is currently governed in this repository.",
            "No direct sector-level FII/DII flow source is currently governed in this repository.",
            "A deal disclosure does not imply no other activity occurred outside the disclosed deal categories.",
            "An ownership change does not identify the individual transactions that produced it.",
        ],
        "provenance": {
            "deal_tape": "data/intelligence/block_bulk_deals.csv; NSE bulk/block deal reports via block_bulk_deal_engine.py",
            "ownership": "data/NSE/shareholding/quarterly_shp.csv; NSE XBRL and explicitly preserved secondary rows",
            "derived_signal": "data/intelligence/institutional_deal_signals.csv; derived 30-day summary, not direct evidence",
            "identity": identity.get("identity_source"),
            "security_resolution": security_resolution,
            "direct_record_lineage": "Each returned deal record has a deterministic source_record_id derived from immutable source fields.",
            "ownership_lineage": ownership.get("lineage"),
            "reproducibility": {
                "deal_tape": deal_meta.get("reproducibility_state"),
                "ownership": ownership.get("lineage", {}).get("state"),
                "derived_signal": (derived_signal or {}).get("lineage_state"),
            },
        },
        "frequency": {
            "deal_activity": "DAILY",
            "ownership": "QUARTERLY",
            "derived_signal": "DAILY_WINDOWED_DERIVED",
            "unknown": [],
        },
        "coverage": {
            "stock_specific": scope not in {"MARKET_LEVEL_CONTEXT_ONLY", "IDENTITY_REVIEW_REQUIRED"},
            "deal_evidence": bool(deal_records),
            "ownership_evidence": ownership.get("state") == "AVAILABLE",
            "both": bool(deal_records) and ownership.get("state") == "AVAILABLE",
            "identity_state": security_resolution.get("state"),
        },
    }


def build_evidence_coverage() -> dict[str, Any]:
    """Return deterministic coverage metrics for documentation/dashboard use."""
    deals = data_loader.get("block_deals")
    ownership = data_loader.get("shareholding")
    deals = deals if deals is not None else pd.DataFrame()
    ownership = ownership if ownership is not None else pd.DataFrame()
    deal_symbols = set(deals.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    ownership_symbols = set(ownership.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    master_symbols: set[str] = set()
    resolved_isins: set[str] = set()
    fundamentals_path = Path("data/NSE/equity_master/company_fundamentals_master.csv")
    equity_path = Path("data/NSE/equity_master/equity_master.csv")
    if fundamentals_path.exists():
        fundamentals = pd.read_csv(fundamentals_path, dtype=str)
        master_symbols.update(fundamentals.get("symbol", pd.Series(dtype=str)).dropna().astype(str).str.upper())
        if "isin" in fundamentals.columns:
            resolved_isins.update(fundamentals.loc[fundamentals["isin"].fillna("").str.strip().ne(""), "symbol"].astype(str).str.upper())
    if equity_path.exists():
        equity = pd.read_csv(equity_path, dtype=str)
        master_symbols.update(equity.get("SYMBOL", pd.Series(dtype=str)).dropna().astype(str).str.upper())
    evidence_symbols = deal_symbols | ownership_symbols
    return {
        "master_symbols": len(master_symbols),
        "symbols_with_any_evidence": len(evidence_symbols),
        "symbols_with_deal_evidence": len(deal_symbols),
        "symbols_with_ownership_evidence": len(ownership_symbols),
        "symbols_with_both": len(deal_symbols & ownership_symbols),
        "symbols_resolved_to_master": len(evidence_symbols & master_symbols),
        "symbols_unresolved": len(evidence_symbols - master_symbols),
        "symbols_with_resolved_isin": len(evidence_symbols & resolved_isins),
        "latest_deal_date": _latest_frame_date(deals, "date"),
        "latest_ownership_quarter_end": _latest_frame_date(ownership, "quarter_end_date"),
        "participant_unique_names": int(deals.get("client_name", pd.Series(dtype=str)).dropna().astype(str).nunique()),
        "coverage_source": "current local FII-DII evidence files; no external data added",
    }
