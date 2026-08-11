from __future__ import annotations

import json
from pathlib import Path

from engines.ai.research.platform.validation import validate_snapshot_directory


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = ROOT / "data" / "research" / "vedic_astrology_pilot"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_astrology_snapshot_and_summary_are_structurally_valid():
    report = validate_snapshot_directory(SNAPSHOT_ROOT)
    summary = _load(SNAPSHOT_ROOT / "p007_pilot_summary.json")
    coverage = _load(SNAPSHOT_ROOT / "p007_coverage_matrix.json")
    templates = _load(SNAPSHOT_ROOT / "p007_mission_templates.json")
    gaps = _load(SNAPSHOT_ROOT / "p007_gap_missions.json")

    assert report.is_valid is True
    assert report.domain_count == 2
    assert report.core_knowledge_count == 10
    assert report.mission_count == 4
    assert report.schedule_count == 0
    assert report.run_count == 6
    assert report.observation_count == 15
    assert report.evidence_count == 19
    assert report.candidate_count == 6
    assert report.validation_count == 190
    assert report.conflict_count == 5
    assert report.approval_count == 3
    assert report.ledger_event_count == 268
    assert report.errors == []

    assert summary["phase"] == "VEDA-P007"
    assert summary["date"] == "2026-08-11"
    assert summary["domain_id"] == "VEDA-DOMAIN-VEDIC-ASTROLOGY"
    assert summary["snapshot_counts"] == {
        "domains": 2,
        "core_knowledge": 8,
        "missions": 4,
        "runs": 6,
        "observations": 15,
        "evidence": 19,
        "candidates": 6,
        "validations": 190,
        "conflicts": 5,
        "approvals": 3,
        "ledger_events": 268,
    }
    assert summary["continuity"]["research_continues_while_pending"] is True
    assert summary["continuity"]["needs_more_research_follow_up_created"] is True
    assert summary["continuity"]["rejected_candidate_rediscovery_same_candidate"] is True
    assert summary["continuity"]["rejected_candidate_support_count"] == 4
    assert summary["continuity"]["rejected_candidate_evidence_ids"] == 8

    assert len(coverage) == 15
    assert len(templates) == 10
    assert len(gaps) == 12
