"""Empirical case normalization and eligibility on the shared PRED store."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engines.common import config as cfg

CASE_CLASSES = (
    "PROSPECTIVE_VERIFIED", "PROSPECTIVE_PENDING", "HISTORICAL_VERIFIED",
    "HISTORICAL_DOCUMENTED", "HISTORICAL_USER_REPORTED", "WORKED_ASTROLOGY_CASE",
    "PRACTITIONER_CASE", "SYNTHETIC_TEST", "FIXTURE_ONLY", "UNVERIFIED",
    "LEAKAGE_INVALID", "UNUSABLE",
)
QUALITY_STATES = ("HIGH", "MODERATE", "LOW", "UNVERIFIED")
EMPIRICAL_CLASSES = {"PROSPECTIVE_VERIFIED", "HISTORICAL_VERIFIED"}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(slots=True)
class CaseRecord:
    case_id: str
    subject_id: str
    source_id: str
    subject_label: str = ""
    source_type: str = ""
    source_title: str = ""
    author: str = ""
    publication: str = ""
    source_page: str = ""
    original_case_source: str = ""
    independent_verification: str = ""
    passage_reference: str = "REFERENCE_NOT_VERIFIED"
    domain: str = "GENERAL"
    case_class: str = "UNVERIFIED"
    chart_input: dict[str, Any] = field(default_factory=dict)
    chart_facts: dict[str, Any] = field(default_factory=dict)
    prediction_cutoff: str | None = None
    knowledge_cutoff: str | None = None
    outcome_cutoff: str | None = None
    outcome: dict[str, Any] | None = None
    outcome_source: str = "UNVERIFIED"
    verification_quality: str = "UNVERIFIED"
    birth_data_provenance: str = "UNVERIFIED"
    event_provenance: str = "UNVERIFIED"
    case_family: str | None = None
    independent_source_family: str | None = None
    quality: str = "UNVERIFIED"
    leakage_status: str = "UNREVIEWED"
    notes: str = ""
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def empirical_eligible(self) -> bool:
        return self.case_class in EMPIRICAL_CLASSES and self.quality in {"HIGH", "MODERATE"} and self.leakage_status == "VALID" and bool(self.outcome)


def case_id_for(*, subject_id: str, source_id: str, event: str = "") -> str:
    seed = "|".join((subject_id, source_id, event)).lower()
    return "CASE-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def normalize_case(payload: dict[str, Any], *, source_path: str | Path | None = None) -> CaseRecord:
    source_id = str(payload.get("source_id") or payload.get("document_id") or source_path or "UNKNOWN_SOURCE")
    subject_id = str(payload.get("subject_id") or payload.get("case_subject") or "UNKNOWN_SUBJECT")
    event = str((payload.get("outcome") or {}).get("event_type") if isinstance(payload.get("outcome"), dict) else payload.get("event_type") or "")
    case_class = str(payload.get("case_class") or ("FIXTURE_ONLY" if source_path and "fixture" in str(source_path).lower() else "UNVERIFIED"))
    if case_class not in CASE_CLASSES:
        case_class = "UNVERIFIED"
    return CaseRecord(
        case_id=str(payload.get("case_id") or case_id_for(subject_id=subject_id, source_id=source_id, event=event)),
        subject_id=subject_id,
        source_id=source_id,
        subject_label=str(payload.get("subject_label") or payload.get("subject_name") or ""),
        source_type=str(payload.get("source_type") or ""),
        source_title=str(payload.get("source_title") or payload.get("title") or ""),
        author=str(payload.get("author") or payload.get("author_attributed") or ""),
        publication=str(payload.get("publication") or payload.get("publisher") or ""),
        source_page=str(payload.get("source_page") or ""),
        original_case_source=str(payload.get("original_case_source") or source_id),
        independent_verification=str(payload.get("independent_verification") or ""),
        passage_reference=str(payload.get("passage_reference") or payload.get("citation_label") or "REFERENCE_NOT_VERIFIED"),
        domain=str(payload.get("domain") or "GENERAL").upper(),
        case_class=case_class,
        chart_input=dict(payload.get("chart_input") or payload.get("chart") or {}),
        chart_facts=dict(payload.get("chart_facts") or {}),
        prediction_cutoff=payload.get("prediction_cutoff"),
        knowledge_cutoff=payload.get("knowledge_cutoff"),
        outcome_cutoff=payload.get("outcome_cutoff"),
        outcome=dict(payload.get("outcome")) if isinstance(payload.get("outcome"), dict) else None,
        outcome_source=str(payload.get("outcome_source") or "UNVERIFIED"),
        verification_quality=str(payload.get("verification_quality") or "UNVERIFIED"),
        birth_data_provenance=str(payload.get("birth_data_provenance") or "UNVERIFIED"),
        event_provenance=str(payload.get("event_provenance") or "UNVERIFIED"),
        case_family=payload.get("case_family") or case_id_for(subject_id=subject_id, source_id=source_id),
        independent_source_family=payload.get("independent_source_family") or source_id,
        quality=str(payload.get("quality") or "UNVERIFIED"),
        leakage_status=str(payload.get("leakage_status") or "UNREVIEWED"),
        notes=str(payload.get("notes") or ""),
    )


def assess_quality(case: CaseRecord) -> str:
    score = 0
    score += 1 if case.birth_data_provenance in {"VERIFIED", "DOCUMENT_VERIFIED"} else 0
    score += 1 if case.event_provenance in {"VERIFIED", "DOCUMENT_VERIFIED", "SYSTEM_VERIFIED"} else 0
    score += 1 if case.verification_quality in {"DOCUMENT_VERIFIED", "DATA_VERIFIED", "SYSTEM_VERIFIED", "MULTI_SOURCE_VERIFIED"} else 0
    score += 1 if case.prediction_cutoff and case.knowledge_cutoff else 0
    return "HIGH" if score >= 4 else "MODERATE" if score >= 2 else "LOW" if score else "UNVERIFIED"


class CaseRegistry:
    """Raw cases live beside PRED-001 records; no second case database."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or cfg.VEDA_RESEARCH_PLATFORM_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.db_path)) as con:
            con.execute("CREATE TABLE IF NOT EXISTS pred_cases (case_id TEXT PRIMARY KEY, case_family TEXT, independent_source_family TEXT, case_class TEXT NOT NULL, quality TEXT NOT NULL, leakage_status TEXT NOT NULL, payload TEXT NOT NULL)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_pred_cases_family ON pred_cases(case_family)")

    def add(self, case: CaseRecord) -> tuple[CaseRecord, str]:
        case.quality = assess_quality(case) if case.quality == "UNVERIFIED" else case.quality
        with sqlite3.connect(str(self.db_path)) as con:
            duplicate = con.execute("SELECT payload FROM pred_cases WHERE case_family=? AND independent_source_family=?", (case.case_family, case.independent_source_family)).fetchone()
            if duplicate:
                return normalize_case(json.loads(duplicate[0])), "DUPLICATE_CASE_FAMILY"
            con.execute("INSERT OR IGNORE INTO pred_cases VALUES (?,?,?,?,?,?,?)", (case.case_id, case.case_family, case.independent_source_family, case.case_class, case.quality, case.leakage_status, _json(case.to_dict())))
        return case, "ADDED"

    def counts(self) -> dict[str, int]:
        with sqlite3.connect(str(self.db_path)) as con:
            rows = con.execute("SELECT case_class, COUNT(*) FROM pred_cases GROUP BY case_class").fetchall()
        return {str(key): int(value) for key, value in rows}

    def eligible(self) -> list[CaseRecord]:
        with sqlite3.connect(str(self.db_path)) as con:
            rows = con.execute("SELECT payload FROM pred_cases WHERE case_class IN ('PROSPECTIVE_VERIFIED','HISTORICAL_VERIFIED') AND quality IN ('HIGH','MODERATE') AND leakage_status='VALID'").fetchall()
        return [normalize_case(json.loads(row[0])) for row in rows if normalize_case(json.loads(row[0])).empirical_eligible]


__all__ = ["CASE_CLASSES", "QUALITY_STATES", "EMPIRICAL_CLASSES", "CaseRecord", "CaseRegistry", "case_id_for", "normalize_case", "assess_quality"]
