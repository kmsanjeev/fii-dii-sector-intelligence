import json

from scripts.veda_calc_ashtakavarga_normalization_rx2_001 import PARENT, build_bundle, sha


def test_normalization_gaps_are_explicit():
    bundle = build_bundle()
    assert len(bundle["classical"]["sources"]) == 5
    assert bundle["normalization"]["BRIHAT_JATAKA"]["state_counts"]["UNRESOLVED"] == 768
    assert bundle["normalization"]["SARAVALI"]["status"] == "INCOMPLETE_WITNESS"
    assert bundle["normalization"]["JATAKA_PARIJATA"]["status"] == "REFERENCE_NOT_VERIFIED"


def test_knr_is_practitioner_axis_and_337_386_are_separate():
    bundle = build_bundle()
    assert bundle["knr"]["authority_axis"] == "PRIMARY_PRACTITIONER_SOURCE; NOT_CLASSICAL_PRIMARY"
    assert "KNR_IMPLEMENTATION_TRADITION" in bundle["knr"]["lineage_policy"]
    assert bundle["raw_contract"]["sav_policy"].startswith("337 = sum of seven planetary BAVs")
    assert bundle["raw_contract"]["nodes"].startswith("Rahu/Ketu excluded")


def test_raw_ready_reductions_deferred_production_unchanged():
    bundle = build_bundle()
    assert bundle["decision"] == "ASHTAKAVARGA_RAW_CONTRACT_REMEDIATION_READY_REDUCTIONS_DEFERRED"
    assert bundle["raw_contract"]["created"] is True
    assert bundle["reduction_contract"]["created"] is False
    assert bundle["production_remediation_authorized"] is False
    runtime = json.loads((PARENT.parent / "calc-ashtakavarga-decision-001/01_RUNTIME_METHOD_FREEZE.json").read_text(encoding="utf-8"))
    assert bundle["runtime"]["implementation_hash"] == runtime["implementation_hash"]


def test_comparison_and_contract_hash_are_deterministic():
    first = build_bundle()
    second = build_bundle()
    assert sha(first["comparison"]) == sha(second["comparison"])
    assert first["raw_contract"]["contract_hash"] == second["raw_contract"]["contract_hash"]
