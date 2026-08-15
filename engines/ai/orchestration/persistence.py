"""Durable, idempotent PRED-001 persistence on the shared research SQLite DB."""

from __future__ import annotations

import json
import hashlib
import sqlite3
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from engines.common import config as cfg

from .prediction import OutcomeRecord, PredictionRecord, PredictionRegistry, compare_prediction_outcome, utc_now

CONFIDENCE_BANDS = ("VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH")
VERIFICATION_STATES = ("UNVERIFIED", "USER_REPORTED", "DOCUMENT_VERIFIED", "DATA_VERIFIED", "SYSTEM_VERIFIED", "MULTI_SOURCE_VERIFIED")
EVENT_TYPES = {
    "CAREER": ("JOB_CHANGE", "ROLE_CHANGE", "PROMOTION", "RESPONSIBILITY_INCREASE", "JOB_LOSS", "BUSINESS_START", "CAREER_STABILITY", "POSITION_START", "POSITION_END", "PUBLIC_APPOINTMENT", "ELECTION_WIN", "ELECTION_LOSS", "RETIREMENT", "DEATH"),
    "RECOGNITION": ("AWARD_RECEIVED",),
    "WEALTH": ("INCOME_INCREASE", "INCOME_DECLINE", "MAJOR_EXPENSE", "ASSET_ACQUISITION", "LIQUIDITY_STRESS"),
    "EDUCATION": ("COURSE_START", "COURSE_COMPLETION", "ADMISSION", "EXAM_SUCCESS", "ACADEMIC_INTERRUPTION"),
    "MARRIAGE": ("RELATIONSHIP_START", "ENGAGEMENT", "MARRIAGE", "RELATIONSHIP_STRESS", "SEPARATION"),
    "PROGENY": ("FAMILY_EXPANSION_EVENT", "PROGENY_SUPPORT_PERIOD"),
    "HEALTH": ("HEALTH_CHALLENGE_PERIOD", "RECOVERY_SUPPORT_PERIOD"),
    "ASTROFINANCE": ("MARKET_DIRECTION", "SECTOR_RELATIVE_STRENGTH", "STOCK_DIRECTION", "VOLATILITY_REGIME"),
}


def false_negative_status(*, observation_coverage: str) -> str:
    """False negatives require complete observation, never assumption."""
    return "MEASURABLE" if observation_coverage in {"COMPLETE", "MULTI_SOURCE_COMPLETE"} else "INSUFFICIENT_OBSERVATION_COVERAGE"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _record(payload: str | dict[str, Any]) -> PredictionRecord:
    value = json.loads(payload) if isinstance(payload, str) else dict(payload)
    value.pop("outcome_locked", None)
    value.pop("_outcome_locked", None)
    return PredictionRecord(**value)


def _date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def score_prediction(prediction: PredictionRecord, outcome: OutcomeRecord) -> dict[str, Any]:
    result = compare_prediction_outcome(prediction, outcome)
    start = _date(prediction.window_start)
    end = _date(prediction.window_end)
    event_start = _date(outcome.event_start)
    inside = bool(start and end and event_start and start <= event_start <= end)
    early = late = None
    if event_start and start and end:
        if event_start < start:
            early = (start - event_start).days
        elif event_start > end:
            late = (event_start - end).days
    event_hit = result["event_correct"]
    direction_hit = result["direction_correct"]
    timing_hit = inside if event_start else None
    if not event_hit and direction_hit is False:
        state = "INCORRECT"
    elif event_hit and direction_hit is not False and timing_hit is not False:
        state = "CORRECT"
    elif event_hit or direction_hit:
        state = "PARTIALLY_CORRECT"
    else:
        state = "AMBIGUOUS_OUTCOME"
    return {"scoring_version": "PRED-001-1", "comparison_state": state, "event_hit": event_hit, "direction_hit": direction_hit, "timing_hit": timing_hit, "inside_window": inside, "days_early": early, "days_late": late, "absolute_timing_error": min((early, late), key=lambda item: item is None) if any(item is not None for item in (early, late)) else 0}


class DurablePredictionRegistry:
    """Raw records are authoritative; all performance tables are rebuildable."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or cfg.VEDA_RESEARCH_PLATFORM_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path), timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS pred_predictions (
                prediction_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, subject_id TEXT NOT NULL,
                domain TEXT NOT NULL, lock_state TEXT NOT NULL, prediction_state TEXT NOT NULL,
                created_at TEXT NOT NULL, payload TEXT NOT NULL
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pred_idempotency ON pred_predictions(request_id, subject_id, domain, prediction_state);
            CREATE TABLE IF NOT EXISTS pred_outcomes (
                outcome_id TEXT PRIMARY KEY, prediction_id TEXT NOT NULL, subject_id TEXT NOT NULL,
                domain TEXT NOT NULL, verification_quality TEXT NOT NULL, recorded_at TEXT NOT NULL, payload TEXT NOT NULL,
                UNIQUE(prediction_id, outcome_id)
            );
            CREATE TABLE IF NOT EXISTS pred_evaluations (
                evaluation_id TEXT PRIMARY KEY, prediction_id TEXT NOT NULL, outcome_id TEXT NOT NULL,
                scoring_version TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(prediction_id, outcome_id)
            );
            CREATE TABLE IF NOT EXISTS pred_domain_performance (
                domain TEXT NOT NULL, method_version TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(domain, method_version)
            );
            CREATE TABLE IF NOT EXISTS pred_signal_performance (
                signal_id TEXT NOT NULL, signal_type TEXT NOT NULL, domain TEXT NOT NULL,
                method_version TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(signal_id, signal_type, domain, method_version)
            );
            CREATE TABLE IF NOT EXISTS pred_audit_ledger (
                event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pred_human_evaluations (
                evaluation_id TEXT PRIMARY KEY, benchmark_id TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL
            );
            """)

    def create(self, record: PredictionRecord, *, lock: bool = True) -> PredictionRecord:
        with self._connect() as con:
            existing = con.execute("SELECT payload FROM pred_predictions WHERE request_id=? AND subject_id=? AND domain=? AND lock_state != 'SUPERSEDED'", (record.request_id, record.subject_id, record.domain)).fetchone()
            if existing:
                return _record(existing["payload"])
            if lock:
                record.lock()
            payload = record.to_dict()
            con.execute("INSERT INTO pred_predictions VALUES (?,?,?,?,?,?,?,?)", (record.prediction_id, record.request_id, record.subject_id, record.domain, record.lock_state, record.prediction_state, record.prediction_created_at, _json(payload)))
            con.execute("INSERT INTO pred_audit_ledger VALUES (?,?,?,?)", (record.prediction_id + ":created", "PREDICTION_CREATED", utc_now(), _json({"prediction_id": record.prediction_id, "request_id": record.request_id})))
        return record

    def get(self, prediction_id: str) -> PredictionRecord | None:
        with self._connect() as con:
            row = con.execute("SELECT payload FROM pred_predictions WHERE prediction_id=?", (prediction_id,)).fetchone()
        return _record(row["payload"]) if row else None

    def record_outcome(self, prediction_id: str, outcome: OutcomeRecord) -> dict[str, Any]:
        record = self.get(prediction_id)
        if record is None:
            raise KeyError(prediction_id)
        scoring = score_prediction(record, outcome)
        payload = asdict(outcome)
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO pred_outcomes VALUES (?,?,?,?,?,?,?)", (outcome.outcome_id, prediction_id, outcome.subject_id, outcome.domain, outcome.verification_quality, utc_now(), _json(payload)))
            con.execute("INSERT OR IGNORE INTO pred_evaluations VALUES (?,?,?,?,?)", (prediction_id + ":" + outcome.outcome_id, prediction_id, outcome.outcome_id, scoring["scoring_version"], _json(scoring)))
            updated = record.to_dict()
            updated.update({"actual_outcome": payload, "outcome_timestamp": utc_now(), "comparison_state": scoring["comparison_state"], "direction_correct": scoring["direction_hit"], "timing_error": scoring["absolute_timing_error"], "outcome_locked": True, "lock_state": "RESOLVED", "prediction_state": "RESOLVED"})
            con.execute("UPDATE pred_predictions SET lock_state=?, prediction_state=?, payload=? WHERE prediction_id=? AND lock_state != 'SUPERSEDED'", ("RESOLVED", "RESOLVED", _json(updated), prediction_id))
            con.execute("INSERT OR IGNORE INTO pred_audit_ledger VALUES (?,?,?,?)", (prediction_id + ":" + outcome.outcome_id, "OUTCOME_EVALUATED", utc_now(), _json({"prediction_id": prediction_id, "outcome_id": outcome.outcome_id, "scoring": scoring})))
        self.rebuild_performance()
        return {"prediction_id": prediction_id, "outcome_id": outcome.outcome_id, **scoring}

    def supersede(self, prediction_id: str, replacement: PredictionRecord) -> PredictionRecord:
        current = self.get(prediction_id)
        if current is None:
            raise KeyError(prediction_id)
        replacement.supersedes_prediction_id = prediction_id
        if replacement.prediction_id == prediction_id:
            import hashlib
            replacement.prediction_id = "PRED-" + hashlib.sha256((prediction_id + replacement.request_id + replacement.prediction_description).encode("utf-8")).hexdigest()[:16]
        with self._connect() as con:
            payload = current.to_dict()
            payload["lock_state"] = "SUPERSEDED"
            con.execute("UPDATE pred_predictions SET lock_state=?, payload=? WHERE prediction_id=?", ("SUPERSEDED", _json(payload), prediction_id))
        return self.create(replacement, lock=True)

    def resolve_no_event(self, prediction_id: str, *, verification_quality: str = "DATA_VERIFIED", note: str = "Window expired with sufficient observation coverage") -> dict[str, Any]:
        record = self.get(prediction_id)
        if record is None:
            raise KeyError(prediction_id)
        outcome = OutcomeRecord("NO_EVENT:" + prediction_id, record.subject_id, record.domain, "NO_EVENT", evidence_source="OBSERVATION_DATA", verification_quality=verification_quality, notes=note)
        result = self.record_outcome(prediction_id, outcome)
        result["comparison_state"] = "FALSE_POSITIVE"
        with self._connect() as con:
            con.execute("UPDATE pred_evaluations SET payload=? WHERE prediction_id=? AND outcome_id=?", (_json(result), prediction_id, outcome.outcome_id))
        self.rebuild_performance()
        return result

    def confidence_calibration(self, *, domain: str | None = None, minimum_sample: int = 10) -> dict[str, Any]:
        with self._connect() as con:
            rows = con.execute("SELECT p.payload, e.payload AS evaluation FROM pred_predictions p JOIN pred_evaluations e ON e.prediction_id=p.prediction_id").fetchall()
        bands: dict[str, dict[str, Any]] = {}
        for row in rows:
            prediction = json.loads(row["payload"])
            if domain and prediction.get("domain") != domain:
                continue
            evaluation = json.loads(row["evaluation"])
            band = prediction.get("confidence_state", "UNKNOWN")
            item = bands.setdefault(band, {"issued_predictions": 0, "resolved_predictions": 0, "correct": 0, "partial": 0, "incorrect": 0})
            item["issued_predictions"] += 1
            item["resolved_predictions"] += 1
            item["correct"] += evaluation.get("comparison_state") == "CORRECT"
            item["partial"] += evaluation.get("comparison_state") == "PARTIALLY_CORRECT"
            item["incorrect"] += evaluation.get("comparison_state") in {"INCORRECT", "FALSE_POSITIVE"}
        return {"state": "CALIBRATED" if bands and all(item["resolved_predictions"] >= minimum_sample for item in bands.values()) else "INSUFFICIENT_SAMPLE", "minimum_sample": minimum_sample, "bands": bands}

    def rebuild_performance(self) -> dict[str, Any]:
        with self._connect() as con:
            rows = con.execute("SELECT p.domain, p.payload, e.payload AS evaluation FROM pred_predictions p JOIN pred_evaluations e ON e.prediction_id=p.prediction_id").fetchall()
            grouped: dict[tuple[str, str], list[tuple[dict[str, Any], dict[str, Any]]]] = {}
            for row in rows:
                prediction = json.loads(row["payload"]); evaluation = json.loads(row["evaluation"])
                grouped.setdefault((prediction["domain"], prediction.get("method_version", "UNKNOWN")), []).append((prediction, evaluation))
            for (domain, method), items in grouped.items():
                count = len(items)
                payload = {"domain": domain, "method_version": method, "total_predictions": count, "resolved_predictions": count, "pending_predictions": 0, "correct": sum(x[1]["comparison_state"] == "CORRECT" for x in items), "partial": sum(x[1]["comparison_state"] == "PARTIALLY_CORRECT" for x in items), "incorrect": sum(x[1]["comparison_state"] == "INCORRECT" for x in items), "ambiguous": sum(x[1]["comparison_state"] == "AMBIGUOUS_OUTCOME" for x in items), "event_hit_rate": round(sum(bool(x[1]["event_hit"]) for x in items) / count, 3), "direction_hit_rate": round(sum(x[1]["direction_hit"] is True for x in items) / count, 3), "timing_hit_rate": round(sum(x[1]["timing_hit"] is True for x in items) / count, 3), "sample_size": count, "confidence_calibration_state": "INSUFFICIENT_SAMPLE", "last_updated": utc_now()}
                con.execute("INSERT OR REPLACE INTO pred_domain_performance VALUES (?,?,?)", (domain, method, _json(payload)))
                signals: dict[tuple[str, str], list[dict[str, Any]]] = {}
                for prediction, evaluation in items:
                    evidence_rows = []
                    for key in ("deterministic_facts", "classical_evidence", "expert_reasoning_evidence", "empirical_evidence", "ml_evidence"):
                        evidence_rows.extend(prediction.get(key) or [])
                    for evidence in evidence_rows:
                        signal_id = str(evidence.get("signal_id") or evidence.get("rule_id") or evidence.get("pattern_id") or evidence.get("evidence_id") or "UNIDENTIFIED")
                        signal_type = str(evidence.get("signal_type") or evidence.get("type") or "EVIDENCE")
                        signals.setdefault((signal_id, signal_type), []).append(evaluation)
                for (signal_id, signal_type), evaluations in signals.items():
                    signal_payload = {"identifier": signal_id, "type": signal_type, "domain": domain, "method_version": method, "prediction_count": len(evaluations), "resolved_count": len(evaluations), "supporting_hits": sum(item.get("comparison_state") == "CORRECT" for item in evaluations), "supporting_misses": sum(item.get("comparison_state") in {"INCORRECT", "FALSE_POSITIVE"} for item in evaluations), "conditional_hits": sum(item.get("comparison_state") == "PARTIALLY_CORRECT" for item in evaluations), "sample_size": len(evaluations), "performance_state": "INSUFFICIENT_SAMPLE"}
                    con.execute("INSERT OR REPLACE INTO pred_signal_performance VALUES (?,?,?,?,?)", (signal_id, signal_type, domain, method, _json(signal_payload)))
            return {"domains": len(grouped), "evaluations": len(rows), "signals": sum(1 for _ in con.execute("SELECT 1 FROM pred_signal_performance"))}

    def counts(self) -> dict[str, int]:
        with self._connect() as con:
            return {"predictions": con.execute("SELECT COUNT(*) FROM pred_predictions").fetchone()[0], "outcomes": con.execute("SELECT COUNT(*) FROM pred_outcomes").fetchone()[0], "evaluations": con.execute("SELECT COUNT(*) FROM pred_evaluations").fetchone()[0]}

    def record_audit_event(self, event_type: str, payload: dict[str, Any], *, event_id: str | None = None) -> str:
        """Append an idempotent workflow/audit event to the shared ledger."""
        identifier = event_id or f"{event_type}:{hashlib.sha256(_json(payload).encode('utf-8')).hexdigest()[:16]}"
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO pred_audit_ledger VALUES (?,?,?,?)", (identifier, event_type, utc_now(), _json(payload)))
        return identifier

    def record_human_evaluation(self, benchmark_id: str, ratings: dict[str, int], *, insight: str | None = None, evaluator_id: str = "FOUNDER") -> str:
        """Persist voluntary human feedback without altering predictions or answers."""
        evaluation_id = hashlib.sha256((benchmark_id + _json(ratings) + evaluator_id).encode("utf-8")).hexdigest()[:20]
        payload = {"benchmark_id": benchmark_id, "ratings": ratings, "insight": insight, "evaluator_id": evaluator_id}
        with self._connect() as con:
            con.execute("INSERT OR IGNORE INTO pred_human_evaluations VALUES (?,?,?,?)", (evaluation_id, benchmark_id, utc_now(), _json(payload)))
        return evaluation_id


__all__ = ["CONFIDENCE_BANDS", "EVENT_TYPES", "VERIFICATION_STATES", "DurablePredictionRegistry", "false_negative_status", "score_prediction"]
