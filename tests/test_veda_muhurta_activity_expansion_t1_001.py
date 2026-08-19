import json

from scripts.veda_muhurta_activity_expansion_t1 import (
    ACTIVITIES,
    FIXED_NAKSHATRAS,
    LIGHT_NAKSHATRAS,
    build_handoff,
    contract_hash,
    evaluate_activity,
)


def test_two_activity_inventory_is_unique_and_contracts_are_non_production():
    assert len(ACTIVITIES) == 2
    assert len(set(ACTIVITIES)) == 2
    handoff = build_handoff()
    assert handoff["production_activation"] is False
    assert {row["runtime_state"] for row in handoff["activities"]} == {"INACTIVE"}
    assert all(len(contract_hash(activity_id)) == 64 for activity_id in ACTIVITIES)


def test_vehicle_light_nakshatra_predicate_and_abstention():
    activity = "VEHICLE_CONVEYANCE_COMMENCEMENT"
    assert evaluate_activity(activity, {"nakshatra": LIGHT_NAKSHATRAS[0]})["status"] == "PREFERENCE_POSITIVE"
    assert evaluate_activity(activity, {"nakshatra": FIXED_NAKSHATRAS[0]})["status"] == "ABSTAIN"
    assert evaluate_activity(activity, {})["reason"] == "MISSING_NAKSHATRA"


def test_installation_fixed_nakshatra_requires_explicit_subtype():
    activity = "CONSECRATION_INSTALLATION_COMMENCEMENT"
    assert evaluate_activity(activity, {"nakshatra": FIXED_NAKSHATRAS[0]})["reason"] == "CEREMONY_SUBTYPE_MISSING"
    result = evaluate_activity(activity, {"nakshatra": FIXED_NAKSHATRAS[0], "ceremony_subtype": "DEITY_INSTALLATION"})
    assert result["status"] == "PREFERENCE_POSITIVE"
    assert evaluate_activity(activity, {"nakshatra": LIGHT_NAKSHATRAS[0], "ceremony_subtype": "DEITY_INSTALLATION"})["status"] == "ABSTAIN"


def test_handoff_is_json_serializable_and_has_lineage():
    handoff = build_handoff()
    json.dumps(handoff, sort_keys=True)
    for row in handoff["activities"]:
        assert row["source_lineage"]["assertions"]
        assert row["source_lineage"]["passages"]
        assert row["blocking_gaps"] == []
