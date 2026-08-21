"""Deterministic, provenance-aware Corporate Intelligence contract.

This module is deliberately limited to structured provider-local evidence.  It
does not call an LLM, score price direction, or reinterpret institutional,
fundamental, or predictive signals.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

import pandas as pd

from backend.services import data_loader

CONTRACT_VERSION = "corporate-intelligence-1.0"
DEFAULT_WINDOW_DAYS = 90
MAX_WINDOW_DAYS = 3650
DEFAULT_LIMIT = 25
MAX_LIMIT = 100

SOURCE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "announcements": {
        "source_id": "NSE_CORPORATE_ANNOUNCEMENTS",
        "authority": "PRIMARY_EXCHANGE_DISCLOSURE",
        "source_type": "STRUCTURED_EXCHANGE_DISCLOSURE",
        "directness": "DIRECT",
        "reproducibility": "SOURCE_ACCESS_DEPENDENT",
        "date_column": "date",
        "symbol_column": "symbol",
        "limitations": ["NSE announcement classification is source/feed dependent."],
    },
    "event_calendar": {
        "source_id": "NSE_EVENT_CALENDAR",
        "authority": "PRIMARY_EXCHANGE_DISCLOSURE",
        "source_type": "STRUCTURED_EXCHANGE_CALENDAR",
        "directness": "DIRECT",
        "reproducibility": "SOURCE_ACCESS_DEPENDENT",
        "date_column": "event_date",
        "symbol_column": "symbol",
        "limitations": ["Calendar records do not prove completion of a scheduled event."],
    },
    "corp_actions": {
        "source_id": "NSE_CORPORATE_ACTIONS",
        "authority": "DERIVED_FROM_PRIMARY",
        "source_type": "NORMALIZED_EXCHANGE_CORPORATE_ACTION",
        "directness": "DERIVED",
        "reproducibility": "SOURCE_ACCESS_DEPENDENT",
        "date_column": "ex_date",
        "symbol_column": "symbol",
        "limitations": ["Action rows preserve effective/record dates but do not imply direction."],
    },
    "quarterly_results": {
        "source_id": "NSE_FINANCIAL_RESULTS",
        "authority": "PRIMARY_EXCHANGE_DISCLOSURE",
        "source_type": "NORMALIZED_FINANCIAL_RESULT",
        "directness": "DIRECT",
        "reproducibility": "SOURCE_ACCESS_DEPENDENT",
        "date_column": "filing_date",
        "symbol_column": "symbol",
        "limitations": ["Financial metrics remain owned by fundamental-evidence-1.0."],
    },
}

_INDEXES: dict[tuple[int, str], tuple[pd.DataFrame, dict[str, list[int]]]] = {}
_SUMMARY_CACHE: dict[int, dict[str, Any]] = {}


def _clean(value: Any) -> Any:
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


def _text(value: Any, limit: int = 600) -> str | None:
    value = _clean(value)
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] if text else None


def _date(value: Any) -> str | None:
    value = _clean(value)
    if value is None:
        return None
    if isinstance(value, str) and re.match(r"^\d{4}[-/]", value.strip()):
        parsed = pd.to_datetime(value, errors="coerce", format="mixed", dayfirst=False)
    else:
        parsed = pd.to_datetime(value, errors="coerce", dayfirst=True, format="mixed")
    if pd.isna(parsed) or not 1900 <= parsed.year <= 2100:
        return None
    return parsed.date().isoformat()


def _dates(values: Any) -> pd.Series:
    """Parse ISO dates without day/month inversion; support legacy local dates."""
    if not isinstance(values, pd.Series):
        values = pd.Series(values, dtype="object")
    text = values.astype("string")
    year_first = text.str.match(r"^\d{4}[-/]").fillna(False)
    parsed = pd.Series(pd.NaT, index=values.index, dtype="datetime64[us]")
    if year_first.any():
        parsed.loc[year_first] = pd.to_datetime(
            values.loc[year_first], errors="coerce", dayfirst=False, format="mixed"
        )
    if (~year_first).any():
        parsed.loc[~year_first] = pd.to_datetime(
            values.loc[~year_first], errors="coerce", dayfirst=True, format="mixed"
        )
    valid_year = parsed.dt.year.between(1900, 2100)
    parsed.loc[~valid_year] = pd.NaT
    return parsed


def _number(value: Any) -> float | None:
    value = _clean(value)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) and abs(number) != float("inf") else None


def _lifecycle_state(text: Any, default: str) -> tuple[str, str]:
    """Map only explicit source language to a lifecycle state."""
    value = str(_clean(text) or "").lower()
    if re.search(r"\b(cancelled|canceled|withdrawn|terminated|abandoned)\b", value):
        return ("CANCELLED" if "cancel" in value else "WITHDRAWN" if "withdrawn" in value else "TERMINATED", "SOURCE_REPORTED")
    if re.search(r"\b(rescheduled|postponed|deferred)\b", value):
        return "RESCHEDULED", "SOURCE_REPORTED"
    if re.search(r"\b(amended|amendment|revised|revision)\b", value):
        return "AMENDED", "SOURCE_REPORTED"
    explicit_completion = re.search(
        r"\b(completed|commissioned|allotted|paid|acquired)\b|"
        r"\bcompletion\s+(?:was|has been|is)\s+(?:achieved|completed|concluded)\b",
        value,
    )
    if explicit_completion and not re.search(
        r"\b(not completed|yet to be completed|pending completion|subject to approval|to be acquired)\b",
        value,
    ):
        return "COMPLETED", "EXPLICIT_SOURCE_LANGUAGE"
    return default, "UNKNOWN"


def _lineage_fields(event_id: str) -> dict[str, Any]:
    return {
        "parent_event_id": None,
        "related_event_ids": [],
        "lifecycle_group_id": event_id,
        "version": 1,
        "lineage_method": "UNKNOWN",
        "lineage_confidence": "UNKNOWN",
    }


def _event_id(source_id: str, values: list[Any]) -> str:
    raw = "|".join("" if value is None else str(value).strip() for value in values)
    digest = hashlib.sha256(f"{source_id}|{raw}".encode()).hexdigest()[:24]
    return f"CORP-{digest}"


def _frame_rows(frame: pd.DataFrame | None, symbol: str | None, column: str) -> pd.DataFrame:
    if frame is None or frame.empty or column not in frame.columns:
        return pd.DataFrame()
    if not symbol:
        return frame
    key = (id(frame), column)
    cached = _INDEXES.get(key)
    if cached is None or cached[0] is not frame:
        mapping: dict[str, list[int]] = {}
        for index, value in frame[column].astype(str).str.upper().items():
            mapping.setdefault(value, []).append(index)
        _INDEXES[key] = (frame, mapping)
        cached = _INDEXES[key]
    positions = cached[1].get(symbol.upper(), [])
    return frame.loc[positions] if positions else frame.iloc[0:0]


def _source_summary(key: str, frame: pd.DataFrame | None) -> dict[str, Any]:
    if frame is None:
        return {
            **SOURCE_DEFINITIONS[key],
            "source_id": SOURCE_DEFINITIONS[key]["source_id"],
            "rows": 0,
            "symbols": 0,
            "date_range": {"oldest": None, "latest": None},
            "access_state": "NOT_AVAILABLE",
            "freshness": "UNAVAILABLE",
        }
    cached = _SUMMARY_CACHE.get(id(frame))
    if cached is not None:
        return cached
    definition = SOURCE_DEFINITIONS[key]
    freshness = data_loader.freshness_for((), (key,))
    try:
        dataset_meta = data_loader.freshness_metadata().get("datasets", {}).get(key, {})
    except AttributeError:
        dataset_meta = {}
    date_column = dataset_meta.get("date_column") or definition["date_column"]
    date_values = frame.get(date_column, pd.Series(dtype="object"))
    dates = _dates(date_values)
    valid = dates.dropna()
    symbols = frame.get(definition["symbol_column"], pd.Series(dtype=str)).astype(str).str.upper().nunique()
    retrieved_rows = int(dataset_meta.get("retrieved_rows", 0) or 0)
    retrieval_column = dataset_meta.get("retrieval_column")
    result = {
        "source_id": definition["source_id"],
        "authority": definition["authority"],
        "source_type": definition["source_type"],
        "rows": len(frame),
        "symbols": symbols,
        "date_range": {
            "oldest": valid.min().date().isoformat() if not valid.empty else None,
            "latest": valid.max().date().isoformat() if not valid.empty else None,
        },
        "directness": definition["directness"],
        "frequency": "EVENT_DRIVEN",
        "reproducibility": definition["reproducibility"],
        "freshness": freshness.get("state", "UNKNOWN"),
        "last_successful_update": dataset_meta.get("last_successful_update"),
        "dataset_build_at": dataset_meta.get("dataset_build_at"),
        "date_column": date_column,
        "retrieval_metadata": {
            "row_retrieval_column": retrieval_column,
            "retrieved_rows": retrieved_rows,
            "row_count": len(frame),
            "coverage": dataset_meta.get(
                "retrieval_coverage",
                "LEGACY_RETRIEVAL_TIMESTAMP_UNAVAILABLE",
            ),
        },
        "access_state": "AVAILABLE",
        "limitations": list(definition["limitations"]),
    }
    _SUMMARY_CACHE[id(frame)] = result
    return result


def _dataset_build_at(key: str) -> str | None:
    """Return the file/build timestamp for event-level provenance."""
    try:
        metadata = data_loader.freshness_metadata().get("datasets", {}).get(key, {})
    except AttributeError:
        return None
    return _text(metadata.get("dataset_build_at"), 64)


def _identity(symbol: str | None) -> dict[str, Any]:
    if not symbol:
        return {"identity_state": "NOT_REQUESTED"}
    try:
        from backend.services.stock_intelligence import _load_identity

        result = dict(_load_identity(symbol.upper()))
    except (ImportError, OSError, ValueError, KeyError):
        result = {"symbol": symbol.upper(), "identity_state": "IDENTITY_SOURCE_UNAVAILABLE"}
    if result.get("identity_state") != "IDENTIFIED":
        result["identity_state"] = "IDENTITY_REVIEW_REQUIRED"
    return result


def _classify_announcement(row: pd.Series) -> tuple[str, str, str]:
    raw_type = str(row.get("announcement_type", "")).upper()
    raw = f"{row.get('desc_raw', '')} {row.get('title_snippet', '')}".lower()
    if "memorandum of understanding" in raw or "mou" in raw or "letter of intent" in raw or " loi" in raw:
        return "MOU_LOI", "DETERMINISTIC_RULE", "CONDITIONAL"
    mapping = {
        "RESULT_UPDATE": "FINANCIAL_RESULTS",
        "ACQUISITION": "ACQUISITION",
        "ORDER_WIN": "ORDER_CONTRACT",
        "FUNDRAISE": "FUNDRAISING",
        "BUYBACK": "BUYBACK",
        "BOARD_OUTCOME": "BOARD_MEETING",
        "DIVIDEND": "DIVIDEND",
        "BONUS": "BONUS",
        "STOCK_SPLIT": "STOCK_SPLIT",
        "CAPEX_EXPANSION": "CAPACITY_EXPANSION",
        "CREDIT_RATING": "CREDIT_RATING",
        "MANAGEMENT_CHANGE": "MANAGEMENT_CHANGE",
        "REGULATORY": "REGULATORY",
        "DISTRESS": "INSOLVENCY",
    }
    category = mapping.get(raw_type, "UNKNOWN")
    return category, "DETERMINISTIC_MAPPING", "HIGH" if category != "UNKNOWN" else "UNKNOWN"


def _result_linkage(symbol: str, results: pd.DataFrame | None) -> dict[str, Any]:
    try:
        dataset_meta = data_loader.freshness_metadata().get("datasets", {}).get(
            "quarterly_results", {}
        )
    except AttributeError:
        dataset_meta = {}
    rows = _frame_rows(results, symbol, "symbol")
    if rows.empty:
        return {
            "state": "RESULT_EVENT_SOURCE_UNKNOWN",
            "announcement_source_status": "SOURCE_AVAILABLE" if results is not None else "SOURCE_UNAVAILABLE",
            "latest_announcement_date": None,
            "contract": "fundamental-evidence-1.0",
            "latest_period_end": None,
            "latest_filing_date": None,
            "fundamental_evidence_available": False,
            "fundamental_evidence_freshness": dataset_meta.get("freshness", "UNKNOWN"),
            "fundamental_freshness_basis": dataset_meta.get("date_column"),
            "filing_date_coverage": "UNAVAILABLE",
            "metrics_inlined": False,
        }
    period_values = rows.get("date_end", pd.Series(dtype="object"))
    filing_values = rows.get("filing_date", pd.Series(dtype="object"))
    period = _dates(period_values).dropna()
    filing = _dates(filing_values).dropna()
    filing_coverage = (
        "COMPLETE"
        if len(rows) and len(filing) == len(rows)
        else "PARTIAL"
        if len(filing)
        else "UNAVAILABLE"
    )
    return {
        "state": "FUNDAMENTAL_EVIDENCE_AVAILABLE",
        "announcement_source_status": "SOURCE_AVAILABLE",
        "latest_announcement_date": filing.max().date().isoformat() if not filing.empty else None,
        "contract": "fundamental-evidence-1.0",
        "latest_period_end": period.max().date().isoformat() if not period.empty else None,
        "latest_filing_date": filing.max().date().isoformat() if not filing.empty else None,
        "fundamental_evidence_available": True,
        "fundamental_evidence_freshness": dataset_meta.get("freshness", "UNKNOWN"),
        "fundamental_freshness_basis": dataset_meta.get("date_column"),
        "filing_date_coverage": filing_coverage,
        "metrics_inlined": False,
    }


def _announcement_event(row: pd.Series, results: pd.DataFrame | None) -> dict[str, Any]:
    symbol = str(row.get("symbol", "")).upper()
    category, method, confidence = _classify_announcement(row)
    announced = _date(row.get("date"))
    source_text = f"{row.get('desc_raw', '')} {row.get('title_snippet', '')}"
    source_id = SOURCE_DEFINITIONS["announcements"]["source_id"]
    source_reference = _text(row.get("seq_id"), 100)
    status, lifecycle_method = _lifecycle_state(source_text, "ANNOUNCED")
    event_id = _event_id(source_id, [symbol, announced, category, source_reference, row.get("title_snippet")])
    event = {
        "event_id": event_id,
        "category": category,
        "status": status,
        "symbol": symbol,
        "announcement_date": announced,
        "effective_date": None,
        "completion_date": None,
        "result_period_end": None,
        "headline": _text(row.get("title_snippet")),
        "facts": {
            "source_category": _text(row.get("announcement_type"), 120),
            "source_subject": _text(row.get("desc_raw")),
            "reference_id": source_reference,
            "reference_url": _text(row.get("pdf_url"), 500),
        },
        "quantitative_fields": {},
        "classification": {"method": method, "confidence": confidence},
        "provenance": {
            "source_id": source_id,
            "authority": SOURCE_DEFINITIONS["announcements"]["authority"],
            "source_record": source_reference,
            "retrieved_at": _text(row.get("retrieved_at"), 64),
            "dataset_build_at": _dataset_build_at("announcements"),
        },
        "lifecycle": {
            **_lineage_fields(event_id),
            "state_method": lifecycle_method,
        },
        "materiality_context": {"state": "UNKNOWN_MATERIALITY", "predictive": False},
        "limitations": [
            "Announcement confirms disclosure, not completion, revenue recognition, or price direction."
        ],
    }
    if category == "FINANCIAL_RESULTS":
        event["fundamental_linkage"] = _result_linkage(symbol, results)
        event["result_period_end"] = event["fundamental_linkage"].get("latest_period_end")
    return event


def _calendar_event(row: pd.Series) -> dict[str, Any]:
    symbol = str(row.get("symbol", "")).upper()
    event_date = _date(row.get("event_date"))
    today = datetime.now().astimezone().date().isoformat()
    status = "SCHEDULED" if event_date and event_date >= today else "UNKNOWN"
    status, lifecycle_method = _lifecycle_state(row.get("bm_desc"), status)
    source_id = SOURCE_DEFINITIONS["event_calendar"]["source_id"]
    purpose = _text(row.get("purpose_type"), 120) or "UNKNOWN"
    event_id = _event_id(source_id, [symbol, event_date, purpose, row.get("bm_desc")])
    return {
        "event_id": event_id,
        "category": {"FINANCIAL_RESULTS": "FINANCIAL_RESULTS", "BOARD_MEETING": "BOARD_MEETING"}.get(purpose, "UNKNOWN"),
        "status": status,
        "symbol": symbol,
        "announcement_date": None,
        "effective_date": event_date,
        "completion_date": None,
        "result_period_end": None,
        "headline": purpose,
        "facts": {"source_category": purpose, "source_subject": _text(row.get("bm_desc"))},
        "quantitative_fields": {},
        "classification": {"method": "SOURCE_REPORTED", "confidence": "CONDITIONAL" if purpose != "UNKNOWN" else "UNKNOWN"},
        "provenance": {
            "source_id": source_id,
            "authority": SOURCE_DEFINITIONS["event_calendar"]["authority"],
            "source_record": None,
            "retrieved_at": _text(row.get("retrieved_at"), 64),
            "dataset_build_at": _dataset_build_at("event_calendar"),
        },
        "lifecycle": {
            **_lineage_fields(event_id),
            "state_method": lifecycle_method,
        },
        "materiality_context": {"state": "UNKNOWN_MATERIALITY", "predictive": False},
        "limitations": ["Calendar date is scheduled/contextual evidence and does not prove completion."],
    }


def _action_event(row: pd.Series) -> dict[str, Any]:
    symbol = str(row.get("symbol", "")).upper()
    event_date = _date(row.get("ex_date"))
    record_date = _date(row.get("rec_date"))
    today = datetime.now().astimezone().date().isoformat()
    status = "SCHEDULED" if event_date and event_date >= today else "UNKNOWN"
    status, lifecycle_method = _lifecycle_state(row.get("subject"), status)
    source_id = SOURCE_DEFINITIONS["corp_actions"]["source_id"]
    category = str(row.get("action_type", "UNKNOWN")).upper()
    category = {"AGM_EGM": "BOARD_MEETING", "MERGER": "MERGER_DEMERGER"}.get(category, category)
    event_id = _event_id(source_id, [symbol, event_date, record_date, category, row.get("subject")])
    return {
        "event_id": event_id,
        "category": category if category else "UNKNOWN",
        "status": status,
        "symbol": symbol,
        "announcement_date": None,
        "effective_date": event_date,
        "record_date": record_date,
        "completion_date": None,
        "result_period_end": None,
        "headline": _text(row.get("subject")),
        "facts": {"source_category": category, "source_subject": _text(row.get("subject"))},
        "quantitative_fields": {
            key: _clean(row.get(key))
            for key in ("dividend_rs", "bonus_ratio", "split_new_fv")
            if _clean(row.get(key)) is not None
        },
        "classification": {"method": "SOURCE_REPORTED", "confidence": "HIGH" if category != "UNKNOWN" else "UNKNOWN"},
        "provenance": {
            "source_id": source_id,
            "authority": SOURCE_DEFINITIONS["corp_actions"]["authority"],
            "source_record": None,
            "retrieved_at": _text(row.get("retrieved_at"), 64),
            "dataset_build_at": _dataset_build_at("corp_actions"),
        },
        "lifecycle": {
            **_lineage_fields(event_id),
            "state_method": lifecycle_method,
        },
        "materiality_context": {"state": "UNKNOWN_MATERIALITY", "predictive": False},
        "limitations": ["Corporate action is a dated fact, not an automatic bullish or bearish signal."],
    }


def _next_watch(events: list[dict[str, Any]]) -> list[str]:
    watches: list[str] = []
    for event in events:
        category = event.get("category")
        status = event.get("status")
        if status == "SCHEDULED" and category == "FINANCIAL_RESULTS":
            watches.append("result announcement or fundamental-evidence ingestion")
        elif status == "SCHEDULED" and category == "BOARD_MEETING":
            watches.append("board meeting outcome")
        elif status == "ANNOUNCED" and category in {"ORDER_CONTRACT", "MOU_LOI"}:
            watches.append("order/MOU execution or amendment evidence")
        elif status == "ANNOUNCED" and category in {"ACQUISITION", "MERGER_DEMERGER"}:
            watches.append("transaction approval or completion evidence")
    return list(dict.fromkeys(watches))[:8]


def _retrieval_metadata(frames: dict[str, pd.DataFrame | None]) -> dict[str, Any]:
    datasets: dict[str, dict[str, Any]] = {}
    for key, frame in frames.items():
        row_count = len(frame) if frame is not None else 0
        retrieved_rows = 0
        if frame is not None and "retrieved_at" in frame.columns:
            retrieved_rows = int(frame["retrieved_at"].notna().sum())
        datasets[key] = {
            "row_retrieval_column": "retrieved_at" if frame is not None and "retrieved_at" in frame.columns else None,
            "retrieved_rows": retrieved_rows,
            "row_count": row_count,
            "coverage": (
                "COMPLETE" if row_count and retrieved_rows == row_count
                else "PARTIAL" if retrieved_rows
                else "LEGACY_RETRIEVAL_TIMESTAMP_UNAVAILABLE"
            ),
        }
    try:
        metadata = data_loader.freshness_metadata().get("datasets", {})
    except AttributeError:
        metadata = {}
    for key, value in datasets.items():
        value["dataset_build_at"] = metadata.get(key, {}).get("dataset_build_at")
        value["last_successful_update"] = metadata.get(key, {}).get("last_successful_update")
    return {
        "row_timestamp_field": "retrieved_at",
        "dataset_timestamp_field": "dataset_build_at",
        "datasets": datasets,
        "limitations": [
            "retrieved_at is populated for newly acquired calendar rows only.",
            "Legacy rows retain null retrieved_at; no historical timestamp is fabricated.",
            "dataset_build_at is file/build metadata, not source publication or event time.",
        ],
    }


def _lifecycle_coverage(events: list[dict[str, Any]]) -> dict[str, Any]:
    states: dict[str, int] = {}
    lineage_methods: dict[str, int] = {}
    for event in events:
        state = str(event.get("status", "UNKNOWN"))
        states[state] = states.get(state, 0) + 1
        method = str(event.get("lifecycle", {}).get("lineage_method", "UNKNOWN"))
        lineage_methods[method] = lineage_methods.get(method, 0) + 1
    return {
        "events": len(events),
        "states": states,
        "linked_events": sum(count for method, count in lineage_methods.items() if method != "UNKNOWN"),
        "lineage_methods": lineage_methods,
        "limitation": "Only explicit source references are eligible for linkage; fuzzy lifecycle joins are not performed.",
    }


def build_corporate_intelligence(
    symbol: str | None = None,
    *,
    days: int = DEFAULT_WINDOW_DAYS,
    limit: int = DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Build the bounded authoritative corporate evidence contract."""
    days = max(1, min(days, MAX_WINDOW_DAYS))
    limit = max(1, min(limit, MAX_LIMIT))
    symbol = symbol.upper().strip() if symbol else None
    identity = _identity(symbol)
    frames = {key: data_loader.get(key) for key in SOURCE_DEFINITIONS}
    source_summary = {key: _source_summary(key, frame) for key, frame in frames.items()}
    data_status = data_loader.freshness_for((), tuple(SOURCE_DEFINITIONS))
    if symbol and identity.get("identity_state") != "IDENTIFIED":
        return {
            "contract_version": CONTRACT_VERSION,
            "symbol": symbol,
            "isin": identity.get("isin"),
            "as_of": data_status.get("as_of"),
            "data_status": {**data_status, "state": "IDENTITY_REVIEW_REQUIRED"},
            "identity": identity,
            "source_summary": source_summary,
            "recent_events": [],
            "events_by_category": {},
            "results_context": {"state": "IDENTITY_REVIEW_REQUIRED"},
            "retrieval_metadata": _retrieval_metadata(frames),
            "lifecycle_coverage": _lifecycle_coverage([]),
            "evidence_quality": "INSUFFICIENT",
            "facts": [],
            "interpretation": "Corporate evidence is unavailable until canonical security identity is resolved.",
            "limitations": ["No fuzzy identity substitution was performed."],
            "next_watch_items": [],
        }
    cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()
    events: list[dict[str, Any]] = []
    announcements = _frame_rows(frames["announcements"], symbol, "symbol")
    if not announcements.empty:
        dates = _dates(announcements["date"])
        candidates = announcements.loc[dates.dt.date >= cutoff].copy()
        candidates["_event_sort_date"] = dates.loc[candidates.index]
        candidates = candidates.sort_values("_event_sort_date", ascending=False).head(limit)
        for _, row in candidates.iterrows():
            events.append(_announcement_event(row, frames["quarterly_results"]))
    calendar = _frame_rows(frames["event_calendar"], symbol, "symbol")
    if not calendar.empty:
        dates = _dates(calendar["event_date"])
        candidates = calendar.loc[dates >= pd.Timestamp(cutoff)].copy()
        candidates["_event_sort_date"] = dates.loc[candidates.index]
        candidates = candidates.sort_values("_event_sort_date", ascending=False).head(limit)
        for _, row in candidates.iterrows():
            events.append(_calendar_event(row))
    actions = _frame_rows(frames["corp_actions"], symbol, "symbol")
    if not actions.empty:
        dates = _dates(actions["ex_date"])
        candidates = actions.loc[dates >= pd.Timestamp(cutoff)].copy()
        candidates["_event_sort_date"] = dates.loc[candidates.index]
        candidates = candidates.sort_values("_event_sort_date", ascending=False).head(limit)
        for _, row in candidates.iterrows():
            events.append(_action_event(row))
    events.sort(key=lambda item: (item.get("announcement_date") or item.get("effective_date") or "", item["event_id"]), reverse=True)
    deduped: dict[str, dict[str, Any]] = {}
    for event in events:
        deduped.setdefault(event["event_id"], event)
    events = list(deduped.values())[:limit]
    by_category: dict[str, int] = {}
    for event in events:
        by_category[event["category"]] = by_category.get(event["category"], 0) + 1
    resolved = identity.get("identity_state") in {"IDENTIFIED", "NOT_REQUESTED"}
    quality = "HIGH" if resolved and events and all(event["provenance"].get("source_id") for event in events) else "MEDIUM" if resolved else "INSUFFICIENT"
    results_context = _result_linkage(symbol, frames["quarterly_results"]) if symbol else {"state": "RESULT_EVENT_SOURCE_UNKNOWN", "contract": "fundamental-evidence-1.0", "metrics_inlined": False}
    return {
        "contract_version": CONTRACT_VERSION,
        "symbol": symbol,
        "isin": identity.get("isin"),
        "as_of": data_status.get("as_of"),
        "data_status": data_status,
        "identity": identity,
        "source_summary": source_summary,
        "recent_events": events,
        "events_by_category": by_category,
        "results_context": results_context,
        "retrieval_metadata": _retrieval_metadata(frames),
        "lifecycle_coverage": _lifecycle_coverage(events),
        "evidence_quality": quality,
        "facts": [event["facts"] for event in events],
        "interpretation": "Corporate evidence describes disclosed facts and dates; it is not a recommendation, forecast, or price signal.",
        "limitations": [
            "Announcement date, event date, completion date and source freshness remain separate.",
            "Order, MOU, approval, completion, revenue and price interpretation are not interchangeable.",
            "Historical events remain queryable but are not automatically current.",
        ],
        "next_watch_items": _next_watch(events),
    }


def corporate_coverage_snapshot() -> dict[str, Any]:
    """Return inventory metrics for governance documentation and tests."""
    frames = {key: data_loader.get(key) for key in SOURCE_DEFINITIONS}
    source_summary = {key: _source_summary(key, frame) for key, frame in frames.items()}
    symbols: set[str] = set()
    for key in ("announcements", "event_calendar", "corp_actions"):
        frame = frames[key]
        if frame is not None and "symbol" in frame.columns:
            symbols.update(frame["symbol"].dropna().astype(str).str.upper())
    recent_symbols: set[str] = set()
    recent_events = 0
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=90)
    for key in ("announcements", "event_calendar", "corp_actions"):
        frame = frames[key]
        if frame is None or frame.empty:
            continue
        column = SOURCE_DEFINITIONS[key]["date_column"]
        dates = _dates(frame[column])
        subset = frame[dates >= cutoff]
        recent_events += len(subset)
        if "symbol" in subset.columns:
            recent_symbols.update(subset["symbol"].dropna().astype(str).str.upper())
    return {
        "master_symbols": len(symbols),
        "symbols_with_any_evidence": len(symbols),
        "symbols_with_recent_evidence": len(recent_symbols),
        "events_total": int(sum(item["rows"] for item in source_summary.values() if item["source_id"] != "NSE_FINANCIAL_RESULTS")),
        "recent_events_90d": int(recent_events),
        "sources": source_summary,
    }
