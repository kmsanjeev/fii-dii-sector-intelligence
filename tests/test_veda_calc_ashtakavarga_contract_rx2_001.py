import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/veda_calc_ashtakavarga_contract_rx2_001.py"


def module():
    spec = importlib.util.spec_from_file_location("veda_calc_ashtakavarga_contract_rx2_001", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(loaded)
    return loaded


def test_v1_hash_and_supersession_are_preserved():
    m = module()
    binding = m.v1_binding()
    assert binding["hash_verified"] is True
    assert binding["recorded_hash"] == m.V1_HASH
    assert binding["status"] == "SUPERSEDED_INVALID_HYBRID"
    assert binding["immutable"] is True
    assert binding["contents_modified"] is False


def test_v2_contract_has_source_consistent_totals_and_required_fields():
    m = module()
    contract = m.build_contract()
    required = {"CONTRACT_ID", "VERSION", "STATUS", "SOURCE_FAMILY", "SOURCE_WITNESS", "SOURCE_MATRIX_HASH", "TARGETS", "CONTRIBUTORS", "TARGET_TOTALS", "PLANETARY_TOTAL", "LAGNA_TOTAL", "COMBINED_TOTAL", "SELF_POLICY", "LAGNA_POLICY", "NODE_POLICY", "POLARITY", "SAV_POLICY", "VARIANT_POLICY", "REDUCTION_POLICY", "SOURCE_PROVENANCE", "SUPERSEDES", "SUPERSESSION_REASON", "CONTRACT_HASH"}
    assert required <= set(contract)
    assert contract["CONTRACT_ID"] == "ASHTAKAVARGA_RAW_BPHS_PRIMARY_V2"
    assert contract["STATUS"] == "CANONICAL_SOURCE_CONTRACT"
    assert contract["SOURCE_MATRIX_HASH"] == "0B7A869F3A3682A3BFFADA28E82AC23DC96EFE7E6FF3763997317C5050EE159D"
    assert contract["PLANETARY_TOTAL"] == 336
    assert contract["LAGNA_TOTAL"] == 49
    assert contract["COMBINED_TOTAL"] == 385
    assert contract["RUNTIME_IMPLEMENTATION_STATUS"] == "NOT_YET_IMPLEMENTED_IN_PRODUCTION"


def test_target_totals_and_policies_are_exact():
    m = module()
    contract = m.build_contract()
    assert contract["TARGET_TOTALS"] == {"Sun": 49, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 54, "Venus": 52, "Saturn": 39, "Lagna": 49}
    assert contract["TARGETS"] == ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    assert contract["CONTRIBUTORS"] == contract["TARGETS"] + ["Lagna"]
    assert "RAHU" in contract["NODE_POLICY"] and "KETU" in contract["NODE_POLICY"]
    assert contract["LAGNA_POLICY"]["ordinary_sav_inclusion"] == "EXCLUDED"
    assert all(value == "DEFERRED" for key, value in contract["REDUCTION_POLICY"].items() if key != "scope")


def test_phaladeepika_variants_are_isolated():
    m = module()
    variants = m.variant_policy()
    assert variants["phala_pair_count"] == 56
    assert variants["exact_bphs_matches"] == 49
    assert variants["variant_pair_count"] == 7
    assert variants["mixing_allowed"] is False
    assert variants["varahamihira_variant"]["status"] == "PRESERVED_NOT_MERGED"


def test_contract_hash_is_deterministic_and_v1_file_is_not_written():
    m = module()
    before = m.V1_PATH.read_bytes()
    first = m.build_contract()
    second = m.build_contract()
    assert first["CONTRACT_HASH"] == second["CONTRACT_HASH"]
    m.export()
    assert m.V1_PATH.read_bytes() == before
    exported = json.loads((m.OUT / "03_V2_CANONICAL_CONTRACT.json").read_text(encoding="utf-8"))
    assert exported["CONTRACT_HASH"] == first["CONTRACT_HASH"]


def test_acceptance_register_has_no_failures_or_blocks():
    m = module()
    m.export()
    register = json.loads((m.OUT / "13_ACCEPTANCE_REGISTER.json").read_text(encoding="utf-8"))
    statuses = {item["status"] for item in register["criteria"]}
    assert register["overall"] == "ASHTAKAVARGA_V2_CONTRACT_ACCEPTED_WITH_CONDITION"
    assert "FAIL" not in statuses
    assert "BLOCKED" not in statuses
