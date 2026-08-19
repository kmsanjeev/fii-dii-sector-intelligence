"""Focused acceptance checks for Shadbala component remediation R1."""

from __future__ import annotations

import json
from pathlib import Path

from engines.ai.knowledge import shadbala_engine as runtime
from scripts import veda_calc_shadbala_component_remediation_r1_001 as activity


def test_independent_component_oracles_and_contracts_pass():
    result = activity.build()
    assert result["final_decision"] == "SHADBALA_R1_NAISARGIKA_DIG_REMEDIATED_WITH_LEGACY_COMPATIBILITY"
    assert result["failures"] == []
    assert result["synthetic_corpus_summary"] == {
        "charts": 100,
        "records": 700,
        "matches": 700,
        "all_match": True,
        "corpus_digest": result["synthetic_corpus_summary"]["corpus_digest"],
    }
    assert result["source_binding"]["components"]["NAISARGIKA_BALA"]["contract_id"] == runtime.NAISARGIKA_CONTRACT_ID
    assert result["source_binding"]["components"]["DIG_BALA"]["contract_id"] == runtime.DIG_CONTRACT_ID


def test_oracles_are_independent_from_production_constants(monkeypatch):
    original_naisargika = dict(runtime.NAISARGIKA_BALA)
    original_dig = dict(runtime.DIG_BALA_MAXIMUM_HOUSE)
    monkeypatch.setitem(runtime.NAISARGIKA_BALA, "Sun", -999.0)
    monkeypatch.setitem(runtime.DIG_BALA_MAXIMUM_HOUSE, "Venus", 12)
    assert activity.oracle_naisargika("Sun") == 60.0
    assert activity.oracle_dig("Venus", 10.0, 190.0) == 60.0
    runtime.NAISARGIKA_BALA.clear()
    runtime.NAISARGIKA_BALA.update(original_naisargika)
    runtime.DIG_BALA_MAXIMUM_HOUSE.clear()
    runtime.DIG_BALA_MAXIMUM_HOUSE.update(original_dig)


def test_aggregate_remains_explicit_legacy_and_unvalidated():
    result = runtime.calculate_shadbala("Sun", 10, 1, 100.0)
    components = {item["component"]: item for item in result["components"]}
    assert components["NAISARGIKA_BALA"]["calculation_rule_id"] == runtime.LEGACY_NAISARGIKA_METHOD_ID
    assert components["DIG_BALA"]["calculation_rule_id"] == "P018-R2-DIG-001"
    assert components["NAISARGIKA_BALA"]["validation_status"] == "IMPLEMENTED_UNVALIDATED"
    assert components["DIG_BALA"]["validation_status"] == "IMPLEMENTED_UNVALIDATED"
    assert result["total"] is None


def test_emitted_artifacts_have_expected_deterministic_shape(tmp_path, monkeypatch):
    monkeypatch.setattr(activity, "OUT", tmp_path)
    result = activity.build()
    activity.emit(result)
    binding = json.loads((tmp_path / "01_COMPONENT_CONTRACT_BINDING.json").read_text(encoding="utf-8"))
    corpus = json.loads((tmp_path / "08_SYNTHETIC_VALIDATION.json").read_text(encoding="utf-8"))
    assert binding["lineage_order"] == ["runtime", "contract", "assertion", "passage", "edition", "witness", "work"]
    assert binding["unit_contract"]["canonical_unit"] == "VIRUPA"
    assert len(corpus["records"]) == 700
    assert corpus["summary"]["all_match"] is True
