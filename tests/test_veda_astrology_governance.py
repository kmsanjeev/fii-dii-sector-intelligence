from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError, validate
from pydantic import ValidationError

from engines.ai.knowledge.astrology_governance import (
    ApprovalRecord,
    AstrologySourceRecord,
    ClaimRecord,
    validate_registry_directory,
    write_json_schemas,
)
from engines.common import config as cfg


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = ROOT / "data" / "veda" / "research" / "astrology"
SCHEMA_DIR = ROOT / "schemas" / "astrology"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_registry_dirs(root: Path) -> None:
    for name in ("sources", "passages", "claims", "conflicts", "approvals", "policies", "legacy"):
        (root / name).mkdir(parents=True, exist_ok=True)


def test_astrology_governance_registry_validates_tracked_pilot_data():
    report = validate_registry_directory(REGISTRY_ROOT)

    assert report.is_valid is True
    assert report.source_count == 10
    assert report.passage_count == 13
    assert report.claim_count == 13
    assert report.conflict_count == 2
    assert report.approval_count == 3
    assert report.policy_count == 6
    assert report.legacy_register_count == 1
    assert report.errors == []


def test_astrology_governance_schema_files_match_models_and_validate_live_records(tmp_dir):
    written = write_json_schemas(tmp_dir)
    exported = {path.name: _load(path) for path in written}
    tracked = {name: _load(SCHEMA_DIR / name) for name in exported}

    assert set(exported) == set(tracked)
    assert exported == tracked

    for schema in exported.values():
        Draft202012Validator.check_schema(schema)

    validate(
        _load(REGISTRY_ROOT / "sources" / "VEDA-SRC-000001.json"),
        exported["source.schema.json"],
    )
    validate(
        _load(REGISTRY_ROOT / "passages" / "VEDA-PSG-000001.json"),
        exported["passage.schema.json"],
    )
    validate(
        _load(REGISTRY_ROOT / "claims" / "VEDA-CLM-000001.json"),
        exported["claim.schema.json"],
    )
    validate(
        _load(REGISTRY_ROOT / "conflicts" / "VEDA-CNF-000001.json"),
        exported["conflict.schema.json"],
    )
    validate(
        _load(REGISTRY_ROOT / "approvals" / "VEDA-APR-000001.json"),
        exported["approval.schema.json"],
    )


def test_astrology_governance_rejects_invalid_ids_source_classes_workflow_states_and_versions():
    source_payload = _load(REGISTRY_ROOT / "sources" / "VEDA-SRC-000001.json")
    claim_payload = _load(REGISTRY_ROOT / "claims" / "VEDA-CLM-000001.json")
    approval_payload = _load(REGISTRY_ROOT / "approvals" / "VEDA-APR-000001.json")

    missing_id = copy.deepcopy(source_payload)
    missing_id.pop("source_id")
    with pytest.raises(ValidationError):
        AstrologySourceRecord.model_validate(missing_id)

    bad_source_class = copy.deepcopy(source_payload)
    bad_source_class["source_class"] = "NOT_A_REAL_CLASS"
    with pytest.raises(ValidationError):
        AstrologySourceRecord.model_validate(bad_source_class)

    bad_workflow = copy.deepcopy(claim_payload)
    bad_workflow["research_status"] = "NOT_A_WORKFLOW_STATE"
    with pytest.raises(ValidationError):
        ClaimRecord.model_validate(bad_workflow)

    bad_version = copy.deepcopy(approval_payload)
    bad_version["version"] = "2026-08-10"
    with pytest.raises(ValidationError):
        ApprovalRecord.model_validate(bad_version)


def test_astrology_governance_detects_broken_registry_relationships(tmp_dir):
    root = tmp_dir / "astrology"
    _ensure_registry_dirs(root)

    source_payload = _load(REGISTRY_ROOT / "sources" / "VEDA-SRC-000001.json")
    claim_payload = _load(REGISTRY_ROOT / "claims" / "VEDA-CLM-000001.json")
    conflict_payload = _load(REGISTRY_ROOT / "conflicts" / "VEDA-CNF-000001.json")

    claim_payload["source_passages"] = ["VEDA-PSG-999999"]
    conflict_payload["claim_b"] = "VEDA-CLM-999999"

    (root / "sources" / "VEDA-SRC-000001.json").write_text(
        json.dumps(source_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "claims" / "VEDA-CLM-000001.json").write_text(
        json.dumps(claim_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "conflicts" / "VEDA-CNF-000001.json").write_text(
        json.dumps(conflict_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = validate_registry_directory(root)

    assert report.is_valid is False
    assert any("missing passage reference VEDA-PSG-999999" in error for error in report.errors)
    assert any("missing claim_b reference VEDA-CLM-999999" in error for error in report.errors)


def test_astrology_governance_json_schema_rejects_invalid_source_class():
    schema = _load(SCHEMA_DIR / "source.schema.json")
    payload = _load(REGISTRY_ROOT / "sources" / "VEDA-SRC-000001.json")
    payload["source_class"] = "INVALID_SOURCE_CLASS"

    with pytest.raises(JsonSchemaValidationError):
        validate(payload, schema)
