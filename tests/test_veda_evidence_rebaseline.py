"""Focused research-only controls for VEDA evidence rebaseline."""

import json

import pytest

from scripts.veda_power_planner import build_plan, two_proportion_required
from scripts.veda_wikidata_enrichment import enrich_records, validate_external_id_mapping


def test_p4782_cannot_be_mapped_to_astro_databank():
    with pytest.raises(ValueError, match="Movieplayer"):
        validate_external_id_mapping("P4782", "Astro-Databank")


def test_non_astro_external_ids_remain_possible():
    validate_external_id_mapping("P4782", "Movieplayer")


def test_enrichment_rejects_nested_forbidden_mapping():
    with pytest.raises(ValueError):
        enrich_records({"records": []}, {"x": [{"external_id_claims": [{"property_id": "P4782", "target_system": "Astro-Databank"}]}]})


def test_power_plan_is_reproducible_and_research_only():
    assert json.dumps(build_plan(), sort_keys=True) == json.dumps(build_plan(), sort_keys=True)
    assert build_plan()["status"] == "RESEARCH_ONLY"
    assert two_proportion_required(.10, .20)["approximate_independent_subjects"] > 0

