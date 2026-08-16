"""Validate event-first empirical candidates without chart-based selection."""

from __future__ import annotations

from typing import Any

ALLOWED_PRECISION = {"EXACT", "MONTH", "YEAR"}
ALLOWED_CLASSES = {
    "MARRIAGE",
    "CHILD_BIRTH",
    "EDUCATION_COMPLETION",
    "CAREER_COMMENCEMENT",
    "BUSINESS_START",
    "RELOCATION",
    "PROPERTY_ACQUISITION",
    "RETIREMENT",
    "HEALTH_EVENT",
    "DEATH",
}


def build_event_first_candidate(*, event_id: str, event_class: str, event_date: str, date_precision: str, event_sources: list[str], birth_source: str | None = None, subject_id: str | None = None) -> dict[str, Any]:
    """Return a provenance record; never infer a chart, subject, or outcome."""
    if not event_id or event_class not in ALLOWED_CLASSES or not event_date:
        raise ValueError("EVENT_FIRST_REQUIRED_FIELDS_INVALID")
    if date_precision not in ALLOWED_PRECISION:
        raise ValueError("EVENT_FIRST_DATE_PRECISION_INVALID")
    if not event_sources:
        raise ValueError("EVENT_FIRST_EVENT_SOURCE_REQUIRED")
    return {
        "acquisition_lane": "EVENT_FIRST",
        "event_id": event_id,
        "event_class": event_class,
        "event_date": event_date,
        "date_precision": date_precision,
        "event_sources": list(event_sources),
        "birth_source": birth_source,
        "subject_id": subject_id,
        "chart_fit_used_for_selection": False,
        "eligibility_state": "EVENT_EVIDENCE_CAPTURED_BIRTH_VALIDATION_PENDING" if not birth_source else "BIRTH_VALIDATION_REQUIRED",
    }
