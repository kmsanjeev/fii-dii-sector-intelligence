from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError as JsonSchemaValidationError, validate
from pydantic import ValidationError

from engines.ai.knowledge.astrology_ontology import (
    AstrologyRuleRecord,
    validate_ontology_directory,
    write_default_documents,
    write_json_schemas,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "veda"
RESEARCH_ROOT = DATA_ROOT / "research" / "astrology"
SCHEMA_DIR = ROOT / "schemas" / "astrology"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_payloads(root: Path) -> dict[str, object]:
    payloads: dict[str, object] = {}
    for path in sorted(root.rglob("*.json")):
        payloads[str(path.relative_to(root)).replace("\\", "/")] = _load(path)
    return payloads


def test_astrology_ontology_validation_succeeds_for_tracked_files():
    report = validate_ontology_directory(DATA_ROOT, RESEARCH_ROOT)

    assert report.is_valid is True
    assert report.entity_count == 131
    assert report.relation_count == 34
    assert report.approved_rule_count == 5
    assert report.draft_rule_count == 2
    assert report.legacy_mapping_count == 6
    assert report.chart_contract_count == 1
    assert report.evaluation_contract_count == 1
    assert report.errors == []


def test_astrology_ontology_exported_schemas_and_documents_match_tracked_files(tmp_path: Path):
    schema_dir = tmp_path / "schemas"
    data_root = tmp_path / "veda"

    written_schemas = write_json_schemas(schema_dir)
    write_default_documents(data_root)

    exported_schemas = {path.name: _load(path) for path in written_schemas}
    tracked_schemas = {name: _load(SCHEMA_DIR / name) for name in exported_schemas}

    assert set(exported_schemas) == set(tracked_schemas)
    assert exported_schemas == tracked_schemas

    for schema in exported_schemas.values():
        Draft202012Validator.check_schema(schema)

    exported_docs = _relative_payloads(data_root)
    tracked_docs = {
        key: value
        for key, value in _relative_payloads(DATA_ROOT).items()
        if key.startswith("ontology/") or key.startswith("rules/")
    }
    exported_subset = {
        key: value
        for key, value in exported_docs.items()
        if key.startswith("ontology/") or key.startswith("rules/")
    }
    assert exported_subset == tracked_docs


def test_astrology_ontology_rejects_invalid_approved_rule_without_governed_provenance():
    payload = _load(DATA_ROOT / "rules" / "approved" / "VEDA-RUL-DASHA-000001.json")
    invalid = copy.deepcopy(payload)
    invalid["provenance"] = {
        "source_ids": [],
        "passage_ids": [],
        "claim_ids": [],
        "conflict_ids": [],
        "legacy_provenance_status": None,
    }

    with pytest.raises(ValidationError):
        AstrologyRuleRecord.model_validate(invalid)


def test_astrology_ontology_detects_broken_refs_and_rule_cycles(tmp_path: Path):
    write_default_documents(tmp_path / "veda")
    rules_root = tmp_path / "veda" / "rules"
    ontology_root = tmp_path / "veda" / "ontology"

    relations_path = ontology_root / "relations" / "core_relations.json"
    relations_payload = _load(relations_path)
    relations_payload[0]["object_entity_id"] = "VEDA-RASHI-NOT_REAL"
    relations_path.write_text(json.dumps(relations_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    dignity_path = rules_root / "draft" / "VEDA-RUL-DIGNITY-000001.json"
    yoga_path = rules_root / "draft" / "VEDA-RUL-YOGA-000001.json"

    dignity_payload = _load(dignity_path)
    yoga_payload = _load(yoga_path)
    dignity_payload["depends_on_rule_ids"] = ["VEDA-RUL-YOGA-000001"]
    yoga_payload["depends_on_rule_ids"] = ["VEDA-RUL-DIGNITY-000001"]
    dignity_path.write_text(json.dumps(dignity_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    yoga_path.write_text(json.dumps(yoga_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = validate_ontology_directory(tmp_path / "veda", RESEARCH_ROOT)

    assert report.is_valid is False
    assert any("missing object entity reference VEDA-RASHI-NOT_REAL" in error for error in report.errors)
    assert any("circular rule dependency detected" in error for error in report.errors)


def test_astrology_ontology_json_schema_rejects_invalid_condition_operator():
    schema = _load(SCHEMA_DIR / "rule.schema.json")
    payload = _load(DATA_ROOT / "rules" / "draft" / "VEDA-RUL-YOGA-000001.json")
    payload["conditions"]["all"][0]["any"][0]["operator"] = "NOT_A_REAL_OPERATOR"

    with pytest.raises(JsonSchemaValidationError):
        validate(payload, schema)
