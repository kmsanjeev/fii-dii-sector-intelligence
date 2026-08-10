from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from engines.ai.research.platform.contracts import (
    ResearchApprovalRecord,
    ResearchCandidateRecord,
    ResearchConflictRecord,
    ResearchCoreKnowledgeRecord,
    ResearchDashboardRecord,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchLedgerEventRecord,
    ResearchMissionRecord,
    ResearchRunRecord,
    ResearchScheduleRecord,
    ResearchValidationRecord,
    SourceObservationRecord,
)
from engines.common import config as cfg


SNAPSHOT_FILE_MODELS: dict[str, tuple[type[Any], bool]] = {
    "research_domain.json": (ResearchDomainRecord, True),
    "research_core_knowledge.json": (ResearchCoreKnowledgeRecord, True),
    "research_missions.json": (ResearchMissionRecord, True),
    "research_schedule.json": (ResearchScheduleRecord, True),
    "research_run.json": (ResearchRunRecord, True),
    "source_observation.json": (SourceObservationRecord, True),
    "research_evidence.json": (ResearchEvidenceRecord, True),
    "research_candidate.json": (ResearchCandidateRecord, True),
    "research_validation.json": (ResearchValidationRecord, True),
    "research_conflict.json": (ResearchConflictRecord, True),
    "research_approval.json": (ResearchApprovalRecord, True),
    "research_ledger_event.json": (ResearchLedgerEventRecord, True),
    "research_dashboard.json": (ResearchDashboardRecord, False),
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(slots=True)
class SnapshotValidationReport:
    domain_count: int = 0
    core_knowledge_count: int = 0
    mission_count: int = 0
    schedule_count: int = 0
    run_count: int = 0
    observation_count: int = 0
    evidence_count: int = 0
    candidate_count: int = 0
    validation_count: int = 0
    conflict_count: int = 0
    approval_count: int = 0
    ledger_event_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def assert_valid(self) -> None:
        if self.errors:
            raise AssertionError("Research platform snapshot validation failed:\n- " + "\n- ".join(self.errors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_count": self.domain_count,
            "core_knowledge_count": self.core_knowledge_count,
            "mission_count": self.mission_count,
            "schedule_count": self.schedule_count,
            "run_count": self.run_count,
            "observation_count": self.observation_count,
            "evidence_count": self.evidence_count,
            "candidate_count": self.candidate_count,
            "validation_count": self.validation_count,
            "conflict_count": self.conflict_count,
            "approval_count": self.approval_count,
            "ledger_event_count": self.ledger_event_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "is_valid": self.is_valid,
        }


def validate_snapshot_directory(root: Path | None = None) -> SnapshotValidationReport:
    base_dir = Path(root or cfg.VEDA_RESEARCH_PLATFORM_EXPORT_DIR)
    report = SnapshotValidationReport()

    loaded: dict[str, Any] = {}
    for filename, (model_cls, is_list) in SNAPSHOT_FILE_MODELS.items():
        path = base_dir / filename
        if not path.exists():
            report.errors.append(f"missing snapshot file: {path}")
            loaded[filename] = [] if is_list else None
            continue
        payload = _load_json(path)
        try:
            if is_list:
                if not isinstance(payload, list):
                    raise TypeError("expected a JSON list")
                loaded[filename] = [model_cls.model_validate(item) for item in payload]
            else:
                if isinstance(payload, list):
                    raise TypeError("expected a JSON object")
                loaded[filename] = model_cls.model_validate(payload)
        except Exception as exc:  # pragma: no cover - exercised through invalid fixture tests
            report.errors.append(f"{path}: {exc}")
            loaded[filename] = [] if is_list else None

    domains = {item.domain_id: item for item in loaded["research_domain.json"]}
    core_knowledge = {item.core_id: item for item in loaded["research_core_knowledge.json"]}
    missions = {item.mission_id: item for item in loaded["research_missions.json"]}
    schedules = {item.schedule_id: item for item in loaded["research_schedule.json"]}
    runs = {item.run_id: item for item in loaded["research_run.json"]}
    observations = {item.observation_id: item for item in loaded["source_observation.json"]}
    evidence = {item.evidence_id: item for item in loaded["research_evidence.json"]}
    candidates = {item.candidate_id: item for item in loaded["research_candidate.json"]}
    validations = loaded["research_validation.json"]
    conflicts = loaded["research_conflict.json"]
    approvals = loaded["research_approval.json"]
    ledger_events = loaded["research_ledger_event.json"]
    dashboard = loaded["research_dashboard.json"]

    report.domain_count = len(domains)
    report.core_knowledge_count = len(core_knowledge)
    report.mission_count = len(missions)
    report.schedule_count = len(schedules)
    report.run_count = len(runs)
    report.observation_count = len(observations)
    report.evidence_count = len(evidence)
    report.candidate_count = len(candidates)
    report.validation_count = len(validations)
    report.conflict_count = len(conflicts)
    report.approval_count = len(approvals)
    report.ledger_event_count = len(ledger_events)

    for core in core_knowledge.values():
        if core.domain_id not in domains:
            report.errors.append(f"{core.core_id}: missing domain reference {core.domain_id}")

    for mission in missions.values():
        if mission.domain_id not in domains:
            report.errors.append(f"{mission.mission_id}: missing domain reference {mission.domain_id}")
        if mission.schedule_id and mission.schedule_id not in schedules:
            report.errors.append(f"{mission.mission_id}: missing schedule reference {mission.schedule_id}")
        if mission.parent_candidate_id and mission.parent_candidate_id not in candidates:
            report.errors.append(f"{mission.mission_id}: missing parent candidate reference {mission.parent_candidate_id}")
        if mission.parent_mission_id and mission.parent_mission_id not in missions:
            report.errors.append(f"{mission.mission_id}: missing parent mission reference {mission.parent_mission_id}")

    for schedule in schedules.values():
        if schedule.domain_id not in domains:
            report.errors.append(f"{schedule.schedule_id}: missing domain reference {schedule.domain_id}")
        if schedule.mission_id not in missions:
            report.errors.append(f"{schedule.schedule_id}: missing mission reference {schedule.mission_id}")

    for run in runs.values():
        if run.domain_id not in domains:
            report.errors.append(f"{run.run_id}: missing domain reference {run.domain_id}")
        if run.mission_id not in missions:
            report.errors.append(f"{run.run_id}: missing mission reference {run.mission_id}")

    for observation in observations.values():
        if observation.run_id not in runs:
            report.errors.append(f"{observation.observation_id}: missing run reference {observation.run_id}")

    for record in evidence.values():
        if record.observation_id not in observations:
            report.errors.append(f"{record.evidence_id}: missing observation reference {record.observation_id}")
        if record.run_id not in runs:
            report.errors.append(f"{record.evidence_id}: missing run reference {record.run_id}")
        if record.mission_id not in missions:
            report.errors.append(f"{record.evidence_id}: missing mission reference {record.mission_id}")
        if record.domain_id not in domains:
            report.errors.append(f"{record.evidence_id}: missing domain reference {record.domain_id}")

    for candidate in candidates.values():
        if candidate.domain_id not in domains:
            report.errors.append(f"{candidate.candidate_id}: missing domain reference {candidate.domain_id}")
        if candidate.mission_id not in missions:
            report.errors.append(f"{candidate.candidate_id}: missing mission reference {candidate.mission_id}")
        if candidate.run_id not in runs:
            report.errors.append(f"{candidate.candidate_id}: missing run reference {candidate.run_id}")
        for evidence_id in candidate.evidence_ids:
            if evidence_id not in evidence:
                report.errors.append(f"{candidate.candidate_id}: missing evidence reference {evidence_id}")
        for core_id in candidate.existing_knowledge_matches:
            if core_id not in core_knowledge:
                report.errors.append(f"{candidate.candidate_id}: missing core knowledge reference {core_id}")
        if candidate.merged_into_candidate_id and candidate.merged_into_candidate_id not in candidates:
            report.errors.append(
                f"{candidate.candidate_id}: missing merged-into candidate reference {candidate.merged_into_candidate_id}"
            )

    for validation in validations:
        if validation.candidate_id not in candidates:
            report.errors.append(f"{validation.validation_id}: missing candidate reference {validation.candidate_id}")

    for conflict in conflicts:
        if conflict.candidate_id not in candidates:
            report.errors.append(f"{conflict.conflict_id}: missing candidate reference {conflict.candidate_id}")
        if conflict.conflicting_candidate_id and conflict.conflicting_candidate_id not in candidates:
            report.errors.append(
                f"{conflict.conflict_id}: missing conflicting candidate reference {conflict.conflicting_candidate_id}"
            )
        if conflict.conflicting_core_id and conflict.conflicting_core_id not in core_knowledge:
            report.errors.append(
                f"{conflict.conflict_id}: missing conflicting core reference {conflict.conflicting_core_id}"
            )

    for approval in approvals:
        if approval.candidate_id not in candidates:
            report.errors.append(f"{approval.approval_id}: missing candidate reference {approval.candidate_id}")

    for event in ledger_events:
        if event.domain_id and event.domain_id not in domains:
            report.errors.append(f"{event.event_id}: missing domain reference {event.domain_id}")
        if event.mission_id and event.mission_id not in missions:
            report.errors.append(f"{event.event_id}: missing mission reference {event.mission_id}")
        if event.run_id and event.run_id not in runs:
            report.errors.append(f"{event.event_id}: missing run reference {event.run_id}")
        if event.candidate_id and event.candidate_id not in candidates:
            report.errors.append(f"{event.event_id}: missing candidate reference {event.candidate_id}")

    if dashboard is not None:
        pending_candidates = sum(1 for item in candidates.values() if item.approval_status.value == "PENDING")
        if dashboard.pending_approvals != pending_candidates:
            report.errors.append(
                "research_dashboard.json: pending_approvals does not match candidate approval state"
            )

    if not conflicts:
        report.warnings.append("snapshot contains no conflicts")
    if not approvals:
        report.warnings.append("snapshot contains no approvals")
    if not any(item.parent_candidate_id for item in missions.values()):
        report.warnings.append("snapshot contains no follow-up mission")

    return report
