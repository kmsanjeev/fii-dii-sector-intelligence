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

import re
from datetime import datetime
from typing import Any

import pandas as pd

from backend.services import data_loader

CONTRACT_VERSION = "stock-institutional-evidence-1.0"
DIRECT_DAILY_FLOW_DECISION = "NO_GOVERNED_DIRECT_DAILY_STOCK_FLOW_SOURCE"
DIRECT_SECTOR_FLOW_DECISION = "NO_GOVERNED_DIRECT_SECTOR_FLOW_SOURCE"
MAX_TRANSACTION_ROWS = 50
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


def _classify_participant(raw: Any) -> dict[str, Any]:
    """Preserve the engine label without treating its fallback as reported.

    The upstream engine uses keyword heuristics over client names and falls
    back to ``RETAIL``.  That fallback is not an exchange participant field,
    so it is intentionally exposed as UNKNOWN here.
    """
    label = str(_value(raw) or "").upper().strip()
    if label in _KNOWN_DERIVED_CLASSES:
        return {
            "raw_label": label,
            "normalized_class": label,
            "classification_status": "DERIVED_HEURISTIC",
            "authority": "PRACTITIONER_OR_PLATFORM_HEURISTIC",
            "confidence": "CONDITIONAL",
        }
    return {
        "raw_label": label or None,
        "normalized_class": "UNKNOWN",
        "classification_status": "UNKNOWN",
        "authority": "NOT_REPORTED_IN_CURRENT_SOURCE",
        "confidence": "LOW",
    }


def _deal_record(row: pd.Series) -> dict[str, Any]:
    participant = _classify_participant(row.get("participant"))
    source_date = _iso_date(row.get("date"))
    return {
        "symbol": str(_value(row.get("symbol")) or "").upper(),
        "company": _value(row.get("company")),
        "deal_type": str(_value(row.get("deal_type")) or "").upper(),
        "client_name": _value(row.get("client_name")),
        "participant": participant,
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
            "source_date": source_date,
            "source_date_semantics": "NSE_DAILY_DEAL_REPORT_DATE; transaction-versus-disclosure distinction is not separately present in this local extract",
        },
        "seq_id": _number(row.get("seq_id"), 0),
    }


def _deal_evidence(deals: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if deals.empty:
        return {
            "state": "NOT_AVAILABLE",
            "record_count": 0,
            "latest_source_date": None,
            "source": "NSE_BULK_BLOCK_DEAL_REPORT_LOCAL_EXTRACT",
        }, []
    deals = deals.copy()
    deals["_date"] = deals.get("date").map(_iso_date).pipe(pd.to_datetime, errors="coerce")
    deals = deals.sort_values(["_date", "seq_id"], ascending=[False, False], na_position="last")
    records = [_deal_record(row) for _, row in deals.head(MAX_TRANSACTION_ROWS).iterrows()]
    return {
        "state": "AVAILABLE",
        "record_count": len(deals),
        "returned_record_count": len(records),
        "latest_source_date": _iso_date(deals["_date"].max()),
        "source": "NSE_BULK_BLOCK_DEAL_REPORT_LOCAL_EXTRACT",
        "truncated": len(deals) > len(records),
        "limitations": [
            "A disclosed bulk/block deal is direct deal activity, not a complete daily FII/DII stock-flow tape.",
            "Participant classes in this local extract are derived from client-name heuristics unless the source reports the class explicitly.",
        ],
    }, records


def _ownership_row(row: pd.Series) -> dict[str, Any]:
    return {
        "quarter_end_date": _iso_date(row.get("quarter_end_date")),
        "submission_date": _iso_date(row.get("submission_date")),
        "reporting_period": _value(row.get("window_label", row.get("period"))),
        "promoter_pct": _number(row.get("promoter_pct"), 4),
        "fii_pct": _number(row.get("fii_pct"), 4),
        "dii_pct": _number(row.get("dii_pct"), 4),
        "public_pct": _number(row.get("public_pct"), 4),
        "source": _value(row.get("source")),
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
    return {
        "state": "AVAILABLE",
        "frequency": "QUARTERLY",
        "latest": latest,
        "prior": prior,
        "change": change,
        "period": {"latest": latest.get("reporting_period"), "prior": prior.get("reporting_period") if prior else None},
        "limitations": [
            "Quarterly ownership change is an ownership snapshot comparison, not a daily transaction flow.",
            "Submission date and quarter-end date are preserved separately.",
        ],
    }


def _derived_signal(symbol: str) -> dict[str, Any] | None:
    row = _frame_symbol(data_loader.get("deal_signals"), symbol)
    if row.empty:
        return None
    item = row.iloc[0]
    return {
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
        "as_of_date": _iso_date(item.get("as_of_date")),
        "lineage": "institutional_deal_signals.csv derived from block_bulk_deals.csv using client-name keyword heuristics",
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
    for record in records:
        participant = record["participant"]
        label = participant["normalized_class"]
        counts[label] = counts.get(label, 0) + 1
        status = participant["classification_status"]
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "counts": counts,
        "classification_status_counts": statuses,
        "unknown_remains_unknown": True,
        "note": "FII/MF/INSURANCE/PROMOTER labels are conditional heuristic classifications in this local deal extract; the RETAIL fallback is not treated as a reported class.",
    }


def build_stock_institutional_evidence(symbol: str, *, identity: dict[str, Any] | None = None) -> dict[str, Any]:
    symbol = str(symbol).upper().strip()
    identity = identity or {"symbol": symbol, "identity_state": "NOT_PROVIDED"}
    identity_status = _identity_status(identity)
    raw_deals = _frame_symbol(data_loader.get("block_deals"), symbol)
    deal_meta, deal_records = _deal_evidence(raw_deals)
    ownership = _ownership_evidence(symbol)
    derived_signal = _derived_signal(symbol)
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
        },
        "scope": scope,
        "evidence_taxonomy": EVIDENCE_TAXONOMY,
        "as_of": component_dates,
        "data_status": {
            "state": data_state,
            "frequency": "MIXED_DISCLOSED_DEALS_AND_QUARTERLY_OWNERSHIP",
            "direct_daily_stock_flow_decision": DIRECT_DAILY_FLOW_DECISION,
            "direct_sector_flow_decision": DIRECT_SECTOR_FLOW_DECISION,
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
        },
    }
