from __future__ import annotations

from contextlib import contextmanager
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Iterator

from engines.ai.research.platform.contracts import (
    ApprovalStatus,
    KnowledgeZone,
    MissionStatus,
    ResearchApprovalRecord,
    ResearchCandidateRecord,
    ResearchConflictRecord,
    ResearchCoreKnowledgeRecord,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchLedgerEventRecord,
    ResearchMissionRecord,
    ResearchRunRecord,
    ResearchScheduleRecord,
    ResearchValidationRecord,
    RunStatus,
    SourceAccessStatus,
    SourceObservationRecord,
)
from engines.common import config as cfg


class ResearchPlatformStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path or cfg.VEDA_RESEARCH_PLATFORM_DB)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(str(self.db_path), check_same_thread=False)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA journal_mode = WAL")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_db(self) -> None:
        with self._conn() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS counters (
                    kind TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS research_domains (
                    domain_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS research_core_knowledge (
                    core_id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    normalized_claim TEXT NOT NULL,
                    topic_key TEXT NOT NULL,
                    stance TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_core_domain_claim
                    ON research_core_knowledge (domain_id, normalized_claim);
                CREATE INDEX IF NOT EXISTS idx_core_domain_topic
                    ON research_core_knowledge (domain_id, topic_key);

                CREATE TABLE IF NOT EXISTS research_missions (
                    mission_id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    schedule_id TEXT,
                    parent_candidate_id TEXT,
                    parent_mission_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_mission_domain_status
                    ON research_missions (domain_id, status);

                CREATE TABLE IF NOT EXISTS research_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    next_run_at TEXT,
                    last_run_at TEXT,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id TEXT PRIMARY KEY,
                    mission_id TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_runs_mission_started
                    ON research_runs (mission_id, started_at);

                CREATE TABLE IF NOT EXISTS research_observations (
                    observation_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    provider_id TEXT NOT NULL,
                    canonical_uri TEXT NOT NULL,
                    access_status TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_observations_run
                    ON research_observations (run_id);

                CREATE TABLE IF NOT EXISTS research_evidence (
                    evidence_id TEXT PRIMARY KEY,
                    observation_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    domain_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_evidence_run
                    ON research_evidence (run_id);

                CREATE TABLE IF NOT EXISTS research_candidates (
                    candidate_id TEXT PRIMARY KEY,
                    domain_id TEXT NOT NULL,
                    mission_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    normalized_claim TEXT NOT NULL,
                    topic_key TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    knowledge_zone TEXT NOT NULL,
                    novelty_status TEXT NOT NULL,
                    contradiction_status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_candidates_claim
                    ON research_candidates (domain_id, normalized_claim);
                CREATE INDEX IF NOT EXISTS idx_candidates_topic
                    ON research_candidates (domain_id, topic_key);
                CREATE INDEX IF NOT EXISTS idx_candidates_approval
                    ON research_candidates (approval_status, knowledge_zone);

                CREATE TABLE IF NOT EXISTS research_validations (
                    validation_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    validator TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_validations_candidate
                    ON research_validations (candidate_id, created_at);

                CREATE TABLE IF NOT EXISTS research_conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    conflict_type TEXT NOT NULL,
                    resolution_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_conflicts_candidate
                    ON research_conflicts (candidate_id, created_at);

                CREATE TABLE IF NOT EXISTS research_approvals (
                    approval_id TEXT PRIMARY KEY,
                    candidate_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_approvals_candidate
                    ON research_approvals (candidate_id, decided_at);

                CREATE TABLE IF NOT EXISTS research_ledger (
                    event_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    domain_id TEXT,
                    mission_id TEXT,
                    run_id TEXT,
                    candidate_id TEXT,
                    actor_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ledger_time
                    ON research_ledger (timestamp);
                """
            )

    def next_id(self, kind: str, prefix: str) -> str:
        with self._conn() as con:
            row = con.execute("SELECT value FROM counters WHERE kind = ?", (kind,)).fetchone()
            current = int(row["value"]) if row else 0
            new_value = current + 1
            con.execute(
                "INSERT INTO counters (kind, value) VALUES (?, ?) "
                "ON CONFLICT(kind) DO UPDATE SET value = excluded.value",
                (kind, new_value),
            )
        return f"{prefix}{new_value:06d}"

    def recover_stale_runs(self) -> int:
        recovered = 0
        with self._conn() as con:
            rows = con.execute("SELECT run_id, payload FROM research_runs WHERE status = ?", (RunStatus.RUNNING.value,)).fetchall()
            for row in rows:
                payload = json.loads(row["payload"])
                payload["status"] = RunStatus.RECOVERABLE.value
                con.execute(
                    "UPDATE research_runs SET status = ?, payload = ? WHERE run_id = ?",
                    (RunStatus.RECOVERABLE.value, json.dumps(payload), row["run_id"]),
                )
                recovered += 1
        return recovered

    def _dump(self, model: Any) -> str:
        if hasattr(model, "model_dump"):
            payload = model.model_dump(mode="json")
        else:
            payload = model
        return json.dumps(payload)

    def _load(self, row: sqlite3.Row | None, model_cls):
        if row is None:
            return None
        return model_cls.model_validate(json.loads(row["payload"]))

    def upsert_domain(self, record: ResearchDomainRecord) -> ResearchDomainRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_domains (domain_id, status, updated_at, payload) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(domain_id) DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at, payload = excluded.payload",
                (record.domain_id, record.status.value, record.updated_at, self._dump(record)),
            )
        return record

    def get_domain(self, domain_id: str) -> ResearchDomainRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_domains WHERE domain_id = ?", (domain_id,)).fetchone()
        return self._load(row, ResearchDomainRecord)

    def list_domains(self) -> list[ResearchDomainRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_domains ORDER BY domain_id").fetchall()
        return [ResearchDomainRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def upsert_core_knowledge(self, record: ResearchCoreKnowledgeRecord) -> ResearchCoreKnowledgeRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_core_knowledge (core_id, domain_id, normalized_claim, topic_key, stance, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(core_id) DO UPDATE SET normalized_claim = excluded.normalized_claim, topic_key = excluded.topic_key, "
                "stance = excluded.stance, updated_at = excluded.updated_at, payload = excluded.payload",
                (
                    record.core_id,
                    record.domain_id,
                    record.normalized_claim,
                    record.topic_key,
                    record.stance,
                    record.updated_at,
                    self._dump(record),
                ),
            )
        return record

    def list_core_knowledge(self, domain_id: str) -> list[ResearchCoreKnowledgeRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_core_knowledge WHERE domain_id = ? ORDER BY core_id",
                (domain_id,),
            ).fetchall()
        return [ResearchCoreKnowledgeRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def create_mission(self, record: ResearchMissionRecord) -> ResearchMissionRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_missions (mission_id, domain_id, status, priority, schedule_id, parent_candidate_id, parent_mission_id, created_at, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.mission_id,
                    record.domain_id,
                    record.status.value,
                    record.priority.value,
                    record.schedule_id,
                    record.parent_candidate_id,
                    record.parent_mission_id,
                    record.created_at,
                    record.updated_at,
                    self._dump(record),
                ),
            )
        return record

    def update_mission(self, record: ResearchMissionRecord) -> ResearchMissionRecord:
        with self._conn() as con:
            con.execute(
                "UPDATE research_missions SET status = ?, priority = ?, schedule_id = ?, parent_candidate_id = ?, parent_mission_id = ?, updated_at = ?, payload = ? WHERE mission_id = ?",
                (
                    record.status.value,
                    record.priority.value,
                    record.schedule_id,
                    record.parent_candidate_id,
                    record.parent_mission_id,
                    record.updated_at,
                    self._dump(record),
                    record.mission_id,
                ),
            )
        return record

    def get_mission(self, mission_id: str) -> ResearchMissionRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_missions WHERE mission_id = ?", (mission_id,)).fetchone()
        return self._load(row, ResearchMissionRecord)

    def list_missions(self) -> list[ResearchMissionRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_missions ORDER BY created_at, mission_id").fetchall()
        return [ResearchMissionRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def find_follow_up_mission(self, parent_candidate_id: str) -> ResearchMissionRecord | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT payload FROM research_missions WHERE parent_candidate_id = ? ORDER BY created_at LIMIT 1",
                (parent_candidate_id,),
            ).fetchone()
        return self._load(row, ResearchMissionRecord)

    def upsert_schedule(self, record: ResearchScheduleRecord) -> ResearchScheduleRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_schedules (schedule_id, domain_id, mission_id, enabled, next_run_at, last_run_at, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(schedule_id) DO UPDATE SET enabled = excluded.enabled, next_run_at = excluded.next_run_at, "
                "last_run_at = excluded.last_run_at, updated_at = excluded.updated_at, payload = excluded.payload",
                (
                    record.schedule_id,
                    record.domain_id,
                    record.mission_id,
                    1 if record.enabled else 0,
                    record.next_run_at,
                    record.last_run_at,
                    record.updated_at,
                    self._dump(record),
                ),
            )
        return record

    def get_schedule(self, schedule_id: str) -> ResearchScheduleRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        return self._load(row, ResearchScheduleRecord)

    def list_schedules(self) -> list[ResearchScheduleRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_schedules ORDER BY schedule_id").fetchall()
        return [ResearchScheduleRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def insert_run(self, record: ResearchRunRecord) -> ResearchRunRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_runs (run_id, mission_id, domain_id, status, trigger_type, started_at, completed_at, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.run_id,
                    record.mission_id,
                    record.domain_id,
                    record.status.value,
                    record.trigger_type.value,
                    record.started_at,
                    record.completed_at,
                    self._dump(record),
                ),
            )
        return record

    def update_run(self, record: ResearchRunRecord) -> ResearchRunRecord:
        with self._conn() as con:
            con.execute(
                "UPDATE research_runs SET status = ?, completed_at = ?, payload = ? WHERE run_id = ?",
                (record.status.value, record.completed_at, self._dump(record), record.run_id),
            )
        return record

    def get_run(self, run_id: str) -> ResearchRunRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_runs WHERE run_id = ?", (run_id,)).fetchone()
        return self._load(row, ResearchRunRecord)

    def list_runs(self) -> list[ResearchRunRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_runs ORDER BY started_at, run_id").fetchall()
        return [ResearchRunRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_runs_for_mission(self, mission_id: str) -> list[ResearchRunRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_runs WHERE mission_id = ? ORDER BY started_at, run_id",
                (mission_id,),
            ).fetchall()
        return [ResearchRunRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def insert_observation(self, record: SourceObservationRecord) -> SourceObservationRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_observations (observation_id, run_id, provider_id, canonical_uri, access_status, retrieved_at, content_hash, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.observation_id,
                    record.run_id,
                    record.provider_id,
                    record.canonical_uri,
                    record.access_status.value,
                    record.retrieved_at,
                    record.content_hash,
                    self._dump(record),
                ),
            )
        return record

    def list_observations(self) -> list[SourceObservationRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_observations ORDER BY retrieved_at, observation_id").fetchall()
        return [SourceObservationRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_observations_for_run(self, run_id: str) -> list[SourceObservationRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_observations WHERE run_id = ? ORDER BY retrieved_at, observation_id",
                (run_id,),
            ).fetchall()
        return [SourceObservationRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def get_observation(self, observation_id: str) -> SourceObservationRecord | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT payload FROM research_observations WHERE observation_id = ?",
                (observation_id,),
            ).fetchone()
        return self._load(row, SourceObservationRecord)

    def insert_evidence(self, record: ResearchEvidenceRecord) -> ResearchEvidenceRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_evidence (evidence_id, observation_id, run_id, mission_id, domain_id, created_at, content_hash, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.evidence_id,
                    record.observation_id,
                    record.run_id,
                    record.mission_id,
                    record.domain_id,
                    record.created_at,
                    record.content_hash,
                    self._dump(record),
                ),
            )
        return record

    def list_evidence(self) -> list[ResearchEvidenceRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_evidence ORDER BY created_at, evidence_id").fetchall()
        return [ResearchEvidenceRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def get_evidence(self, evidence_id: str) -> ResearchEvidenceRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_evidence WHERE evidence_id = ?", (evidence_id,)).fetchone()
        return self._load(row, ResearchEvidenceRecord)

    def upsert_candidate(self, record: ResearchCandidateRecord) -> ResearchCandidateRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_candidates (candidate_id, domain_id, mission_id, run_id, normalized_claim, topic_key, approval_status, knowledge_zone, novelty_status, contradiction_status, updated_at, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(candidate_id) DO UPDATE SET mission_id = excluded.mission_id, run_id = excluded.run_id, "
                "approval_status = excluded.approval_status, knowledge_zone = excluded.knowledge_zone, "
                "novelty_status = excluded.novelty_status, contradiction_status = excluded.contradiction_status, updated_at = excluded.updated_at, payload = excluded.payload",
                (
                    record.candidate_id,
                    record.domain_id,
                    record.mission_id,
                    record.run_id,
                    record.normalized_claim,
                    record.topic_key,
                    record.approval_status.value,
                    record.knowledge_zone.value,
                    record.novelty_status.value,
                    record.contradiction_status.value,
                    record.updated_at,
                    self._dump(record),
                ),
            )
        return record

    def get_candidate(self, candidate_id: str) -> ResearchCandidateRecord | None:
        with self._conn() as con:
            row = con.execute("SELECT payload FROM research_candidates WHERE candidate_id = ?", (candidate_id,)).fetchone()
        return self._load(row, ResearchCandidateRecord)

    def list_candidates(self) -> list[ResearchCandidateRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_candidates ORDER BY updated_at, candidate_id").fetchall()
        return [ResearchCandidateRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def find_candidate_by_normalized_claim(
        self,
        domain_id: str,
        normalized_claim: str,
        *,
        exclude_archived: bool = True,
    ) -> ResearchCandidateRecord | None:
        query = "SELECT payload FROM research_candidates WHERE domain_id = ? AND normalized_claim = ?"
        args: list[Any] = [domain_id, normalized_claim]
        if exclude_archived:
            query += " AND knowledge_zone != ?"
            args.append(KnowledgeZone.RESEARCH_ARCHIVE.value)
        query += " ORDER BY updated_at LIMIT 1"
        with self._conn() as con:
            row = con.execute(query, tuple(args)).fetchone()
        return self._load(row, ResearchCandidateRecord)

    def find_candidates_by_topic(self, domain_id: str, topic_key: str) -> list[ResearchCandidateRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_candidates WHERE domain_id = ? AND topic_key = ? AND knowledge_zone != ? ORDER BY updated_at, candidate_id",
                (domain_id, topic_key, KnowledgeZone.RESEARCH_ARCHIVE.value),
            ).fetchall()
        return [ResearchCandidateRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def insert_validation(self, record: ResearchValidationRecord) -> ResearchValidationRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_validations (validation_id, candidate_id, validator, status, created_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.validation_id,
                    record.candidate_id,
                    record.validator.value,
                    record.status.value,
                    record.created_at,
                    self._dump(record),
                ),
            )
        return record

    def list_validations(self) -> list[ResearchValidationRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_validations ORDER BY created_at, validation_id").fetchall()
        return [ResearchValidationRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_validations_for_candidate(self, candidate_id: str) -> list[ResearchValidationRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_validations WHERE candidate_id = ? ORDER BY created_at, validation_id",
                (candidate_id,),
            ).fetchall()
        return [ResearchValidationRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def insert_conflict(self, record: ResearchConflictRecord) -> ResearchConflictRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_conflicts (conflict_id, candidate_id, conflict_type, resolution_status, created_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.conflict_id,
                    record.candidate_id,
                    record.conflict_type.value,
                    record.resolution_status.value,
                    record.created_at,
                    self._dump(record),
                ),
            )
        return record

    def update_conflict(self, record: ResearchConflictRecord) -> ResearchConflictRecord:
        with self._conn() as con:
            con.execute(
                "UPDATE research_conflicts SET conflict_type = ?, resolution_status = ?, payload = ? WHERE conflict_id = ?",
                (
                    record.conflict_type.value,
                    record.resolution_status.value,
                    self._dump(record),
                    record.conflict_id,
                ),
            )
        return record

    def list_conflicts(self) -> list[ResearchConflictRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_conflicts ORDER BY created_at, conflict_id").fetchall()
        return [ResearchConflictRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_conflicts_for_candidate(self, candidate_id: str) -> list[ResearchConflictRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_conflicts WHERE candidate_id = ? ORDER BY created_at, conflict_id",
                (candidate_id,),
            ).fetchall()
        return [ResearchConflictRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def get_conflict(self, conflict_id: str) -> ResearchConflictRecord | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT payload FROM research_conflicts WHERE conflict_id = ?",
                (conflict_id,),
            ).fetchone()
        return self._load(row, ResearchConflictRecord)

    def insert_approval(self, record: ResearchApprovalRecord) -> ResearchApprovalRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_approvals (approval_id, candidate_id, action, status, decided_at, payload) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    record.approval_id,
                    record.candidate_id,
                    record.action.value,
                    record.status.value,
                    record.decided_at,
                    self._dump(record),
                ),
            )
        return record

    def list_approvals(self) -> list[ResearchApprovalRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_approvals ORDER BY decided_at, approval_id").fetchall()
        return [ResearchApprovalRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_approvals_for_candidate(self, candidate_id: str) -> list[ResearchApprovalRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_approvals WHERE candidate_id = ? ORDER BY decided_at, approval_id",
                (candidate_id,),
            ).fetchall()
        return [ResearchApprovalRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def append_ledger_event(self, record: ResearchLedgerEventRecord) -> ResearchLedgerEventRecord:
        with self._conn() as con:
            con.execute(
                "INSERT INTO research_ledger (event_id, timestamp, event_type, domain_id, mission_id, run_id, candidate_id, actor_type, action, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    record.event_id,
                    record.timestamp,
                    record.event_type.value,
                    record.domain_id,
                    record.mission_id,
                    record.run_id,
                    record.candidate_id,
                    record.actor_type.value,
                    record.action,
                    self._dump(record),
                ),
            )
        return record

    def list_ledger_events(self) -> list[ResearchLedgerEventRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_ledger ORDER BY timestamp, event_id").fetchall()
        return [ResearchLedgerEventRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def list_ledger_for_candidate(self, candidate_id: str) -> list[ResearchLedgerEventRecord]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT payload FROM research_ledger WHERE candidate_id = ? ORDER BY timestamp, event_id",
                (candidate_id,),
            ).fetchall()
        return [ResearchLedgerEventRecord.model_validate(json.loads(row["payload"])) for row in rows]

    def dashboard_metrics(self) -> dict[str, Any]:
        missions = self.list_missions()
        runs = self.list_runs()
        observations = self.list_observations()
        candidates = self.list_candidates()
        conflicts = self.list_conflicts()
        approvals = self.list_approvals()
        return {
            "missions_active": sum(1 for mission in missions if mission.status == MissionStatus.ACTIVE),
            "runs_total": len(runs),
            "runs_failed": sum(1 for run in runs if run.status == RunStatus.FAILED),
            "sources_discovered": len(observations),
            "sources_rejected": sum(1 for obs in observations if obs.access_status != SourceAccessStatus.ACCEPTED),
            "evidence_created": len(self.list_evidence()),
            "candidates_created": len(candidates),
            "candidate_duplicates": sum(1 for candidate in candidates if candidate.support_count > 1),
            "contradictions_found": len(conflicts),
            "pending_reviews": sum(1 for candidate in candidates if candidate.approval_status == ApprovalStatus.PENDING),
            "approvals": sum(1 for approval in approvals if approval.status in {ApprovalStatus.APPROVED, ApprovalStatus.APPROVED_WITH_CONDITIONS}),
            "rejections": sum(1 for approval in approvals if approval.status == ApprovalStatus.REJECTED),
            "follow_ups": sum(1 for mission in missions if mission.parent_candidate_id is not None),
        }

    def export_records(self) -> dict[str, list[dict[str, Any]]]:
        def dump_all(records: Iterable[Any]) -> list[dict[str, Any]]:
            return [record.model_dump(mode="json") for record in records]

        return {
            "research_domains": dump_all(self.list_domains()),
            "research_core_knowledge": dump_all(self.list_core_knowledge_records()),
            "research_missions": dump_all(self.list_missions()),
            "research_schedules": dump_all(self.list_schedules()),
            "research_runs": dump_all(self.list_runs()),
            "source_observations": dump_all(self.list_observations()),
            "research_evidence": dump_all(self.list_evidence()),
            "research_candidates": dump_all(self.list_candidates()),
            "research_validations": dump_all(self.list_validations()),
            "research_conflicts": dump_all(self.list_conflicts()),
            "research_approvals": dump_all(self.list_approvals()),
            "research_ledger_events": dump_all(self.list_ledger_events()),
        }

    def list_core_knowledge_records(self) -> list[ResearchCoreKnowledgeRecord]:
        with self._conn() as con:
            rows = con.execute("SELECT payload FROM research_core_knowledge ORDER BY core_id").fetchall()
        return [ResearchCoreKnowledgeRecord.model_validate(json.loads(row["payload"])) for row in rows]
