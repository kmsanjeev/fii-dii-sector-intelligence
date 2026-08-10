from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from engines.ai.research.platform.contracts import write_json_schemas
from engines.ai.research.platform.validation import validate_snapshot_directory


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas" / "research"
SNAPSHOT_ROOT = ROOT / "data" / "research" / "synthetic_pilot"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_research_platform_schema_files_match_models_and_validate_tracked_snapshot(tmp_dir):
    written = write_json_schemas(tmp_dir)
    exported = {path.name: _load(path) for path in written}
    tracked = {name: _load(SCHEMA_DIR / name) for name in exported}

    assert set(exported) == set(tracked)
    assert exported == tracked

    for schema in tracked.values():
        Draft202012Validator.check_schema(schema)

    report = validate_snapshot_directory(SNAPSHOT_ROOT)

    assert report.is_valid is True
    assert report.domain_count == 1
    assert report.core_knowledge_count == 2
    assert report.mission_count == 2
    assert report.schedule_count == 1
    assert report.run_count == 3
    assert report.observation_count == 7
    assert report.evidence_count == 6
    assert report.candidate_count == 4
    assert report.validation_count == 60
    assert report.conflict_count == 1
    assert report.approval_count == 3
    assert report.errors == []


def test_research_platform_snapshot_validation_detects_broken_references(tmp_dir):
    for path in SNAPSHOT_ROOT.glob("*.json"):
        (tmp_dir / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

    candidate_payload = _load(tmp_dir / "research_candidate.json")
    broken_payload = copy.deepcopy(candidate_payload)
    broken_payload[0]["evidence_ids"] = ["VEDA-EVD-999999"]
    (tmp_dir / "research_candidate.json").write_text(
        json.dumps(broken_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    report = validate_snapshot_directory(tmp_dir)

    assert report.is_valid is False
    assert any("missing evidence reference VEDA-EVD-999999" in error for error in report.errors)
