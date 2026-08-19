from engines.ai.capabilities import access_policy
from scripts.veda_runtime_capability_exposure_audit_001 import run_matrix


def test_deterministic_behavior_matrix_records_current_gaps_without_hiding_them():
    result = run_matrix()
    assert result["case_count"] == 50
    assert result["registered_tools"] == 23
    assert result["intent_pass"] == 42
    assert result["intent_gaps"] == 8
    assert {row["case_id"] for row in result["rows"] if row["intent_status"] == "GAP"} == {
        "B003", "B025", "B026", "B031", "B038", "B040", "B042", "B048",
    }


def test_configuration_surface_has_fifteen_entries_and_default_reset_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "engines.common.config.VEDA_CONVERSATIONAL_ACCESS_CONFIG",
        tmp_path / "conversation_access.json",
    )
    states = access_policy.get_states()
    assert len(states) == 15
    assert all(row["admin_access_state"] == access_policy.ENABLED for row in states)
    for row in states:
        access_policy.set_access(row["capability_id"], access_policy.DISABLED)
        assert access_policy.get_state(row["capability_id"]).effective_access == access_policy.DISABLED
    restored = access_policy.reset_defaults()
    assert all(row["effective_access"] in {access_policy.ENABLED, "UNAVAILABLE"} for row in restored)


def test_core_and_domain_routing_remain_separate():
    assert access_policy.resolve_intent("GREETING").capability_id == "CORE_INTERACTION"
    assert access_policy.resolve_intent("GENERAL").capability_id == "GENERAL_CHAT"
    assert access_policy.resolve_intent("ASTRO").capability_id == "ASTROLOGY"
    assert access_policy.resolve_intent("KUNDLI").capability_id == "PERSONAL_KUNDLI"
    assert access_policy.resolve_intent("MUHURTA").capability_id == "MUHURTA"
    assert access_policy.resolve_intent("ASTRO_FINANCE").capability_id == "ASTRO_FINANCE"
