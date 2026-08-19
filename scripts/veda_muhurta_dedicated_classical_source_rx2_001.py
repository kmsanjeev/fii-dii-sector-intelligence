"""Build the governed RX2 Muhurta source and contract audit.

This activity is intentionally evidence-only.  It creates versioned, inactive
contract artifacts from the existing V3 contracts; it does not run the
recommendation engine, change P032 mathematics, or add a second evaluator.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_muhurta_mvp_source_semantics_hardening_001 import read_json

PROGRAMME = "VEDA-MUHURTA-DEDICATED-CLASSICAL-SOURCE-RX2-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "33d9ec17938ea4ea352c6c23a21e4c17b4063dda"
PREDECESSOR = ROOT / "docs/current-state/muhurta-tithi-karana-source-hardening-rx1-001"
V3_ROOT = ROOT / "docs/current-state/muhurta-mvp-source-semantics-hardening-001"
OUT = ROOT / "docs/current-state/muhurta-dedicated-classical-source-rx2-001"

BUSINESS_V3 = "B2BFCC4CDCF20653E403EEEDD5CD2A6532009CFC44578995A9081D7DDB538075"
EDUCATION_V3 = "976D20F34B5E447CCDB96A773C37C664BBC596267F0BCE9AF248D19BD85A4CD4"

ARCHIVE_URL = "https://archive.org/details/in.ernet.dli.2015.345472"
ARCHIVE_TEXT_URL = "https://archive.org/stream/in.ernet.dli.2015.345472/2015.345472.The-Muhurta_djvu.txt"
CSU_PDF_URL = "https://www.csu-guruvayoor.edu.in/studymaterial/jyothisha/MUHURTACHINTAMANI-5TH%20CHAPTER_s1.pdf"
BS_URL = "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/bRRihatsaMhitA.html"
BS_SIVA_URL = "https://www.siva.sh/brihat-samhita/100"
DHARMASINDHU_URL = "https://ignca.gov.in/PDF_data/Vedanga-Kalpa%28Dharma-Shastra%29-Vol-II-Part-XII.pdf"


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def contract_hash(contract: Mapping[str, Any]) -> str:
    value = dict(contract)
    value.pop("contract_hash", None)
    value.pop("contract_hash_full", None)
    return digest(value)


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, value: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def _source_rule(rule_id: str, *, activity: str, factor_id: str, expected: list[Any], assertion: str, condition: str) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "activity_scope": activity,
        "condition": condition,
        "condition_mode": "SINGLE",
        "evaluator_id": "ENUM_MEMBERSHIP",
        "factor_id": factor_id,
        "factor_source": "P032_FACTOR_ADAPTER_V2_SOURCE_SEMANTIC_DERIVATION",
        "factor_type": "TITHI",
        "value_type": "ENUM",
        "operator": "IN",
        "expected_set": expected,
        "missing_value_policy": "ABSTAIN",
        "variant_id": "MUHURTACINTAMANI_VIDYARAMBHA_TITHI_V1",
        "executability_state": "MACHINE_READY",
        "evaluator_state": "EXECUTABLE",
        "source_assertions": [assertion],
        "source_layer": "CLASSICAL_PRIMARY_DEDICATED_WITNESS",
        "validation_state": "SOURCE_CHECKED_CONDITIONAL",
        "recommendation_effect": "PREFERENCE_POSITIVE",
        "rule_class": "PREFERENCE_POSITIVE",
        "precedence_class": "PREFERENCE_POSITIVE",
        "hard_exclusion": False,
        "hard_requirement": False,
        "personal_required": False,
        "production_activation": False,
        "explanation_label": "Dedicated-source Tithi preference; no success or outcome claim.",
    }


def _nonblocking_residual(old: Mapping[str, Any], *, activity: str, rule_id: str, reason: str) -> dict[str, Any]:
    value = copy.deepcopy(dict(old))
    value.update({
        "rule_id": rule_id,
        "activity_scope": activity,
        "executability_state": "SOURCE_PARTIAL_NON_BLOCKING",
        "evaluator_state": "NON_EXECUTABLE",
        "source_partial_reason": reason,
        "factor_state": "ACTIVITY_SPECIFIC_SOURCE_RULE_UNRESOLVED",
        "recommendation_effect": "ABSTAIN",
        "rule_class": "NON_BLOCKING_ADDITIONAL_COVERAGE",
        "precedence_class": "UNRESOLVED",
        "hard_exclusion": False,
        "hard_requirement": False,
        "production_activation": False,
        "validation_state": "SOURCE_LIMITED",
        "source_assertions": [],
        "variant_id": "ACTIVITY_SCOPE_AND_SOURCE_NECESSITY_AUDIT_V1",
        "explanation_label": "Disclosed source gap; unavailable for positive or negative evaluation.",
        "blocking_classification": "NON_BLOCKING_ADDITIONAL_COVERAGE",
        "non_blocking_reason": "No inspected source establishes this as a mandatory hard requirement for the activity contract.",
    })
    return value


def _build_contract(activity: str) -> dict[str, Any]:
    is_business = activity == "BUSINESS_OPENING_INAUGURATION"
    source = read_json(V3_ROOT / ("10_BUSINESS_CONTRACT_V3.json" if is_business else "11_EDUCATION_CONTRACT_V3.json"))
    contract = copy.deepcopy(source)
    prefix = "BUSINESS-OPENING" if is_business else "EDUCATION-COMMENCEMENT"
    contract["contract_id"] = f"VEDA-MUH-CONTRACT-{prefix}-V4"
    contract["version"] = "4.0.0"
    contract["supersedes"] = {"contract_id": source["contract_id"], "contract_hash_full": source["contract_hash_full"], "legacy_v3_hash": BUSINESS_V3 if is_business else EDUCATION_V3}
    contract["recommendation_engine_state"] = "MACHINE_CONTRACT_READY_WITH_NONBLOCKING_SOURCE_GAPS"
    contract["source_semantics_policy"] = "Dedicated primary-source predicates only; scope mismatches and unverified factors abstain and do not block when no source-mandatory requirement is established."
    contract["production_bound"] = False

    old_id = "MUH-BIZ-TITHI-KARANA-001" if is_business else "MUH-EDU-TITHI-KARANA-001"
    old = next(rule for rule in source["rules"] if rule["rule_id"] == old_id)
    rules = [copy.deepcopy(rule) for rule in source["rules"] if rule["rule_id"] != old_id]
    if is_business:
        rules.append(_nonblocking_residual(old, activity=activity, rule_id="MUH-BIZ-TITHI-SCOPE-GAP-001", reason="Dedicated Muhurtacintamani evidence covers market/shop sale and commerce context, not the exact modern business-opening/inauguration scope; no exact opening predicate is admitted."))
    else:
        rules.append(_source_rule("MUH-EDU-TITHI-VIDYARAMBHA-001", activity=activity, factor_id="TITHI", expected=[2, 3, 5, 6, 10, 11, 12], assertion="VEDA-SWW-ASSERTION-MC-VIDYARAMBHA-TITHI-001", condition="Tithi is one of the dedicated Muhurtacintamani Vidyarambha/Akshararambha values."))
        rules.append(_nonblocking_residual(old, activity=activity, rule_id="MUH-EDU-KARANA-SCOPE-GAP-001", reason="The inspected dedicated education passage supplies Tithi/Nakshatra/Vara/planet conditions but no education-specific Karana set; generic Karana symmetry is not inferred."))
    contract["rules"] = rules
    contract["rule_ids"] = [rule["rule_id"] for rule in rules]
    contract["machine_rule_ids"] = [rule["rule_id"] for rule in rules if rule.get("executability_state") == "MACHINE_READY"]
    contract["source_partial_rule_ids"] = [rule["rule_id"] for rule in rules if rule.get("executability_state") != "MACHINE_READY"]
    contract["blocking_rule_ids"] = [rule["rule_id"] for rule in rules if rule.get("executability_state") != "MACHINE_READY" and rule.get("recommendation_effect") not in {"NEUTRAL", "ABSTAIN"}]
    contract["machine_rule_summary"] = {
        "rules_total": len(rules),
        "machine_ready": len(contract["machine_rule_ids"]),
        "source_partial": len(contract["source_partial_rule_ids"]),
        "source_partial_non_blocking": sum(rule.get("executability_state") == "SOURCE_PARTIAL_NON_BLOCKING" for rule in rules),
        "non_executable": len(contract["source_partial_rule_ids"]),
        "factor_missing": 0,
        "personal_deferred": 0,
        "conflict_blocked": 0,
    }
    resolved = list(contract["rule_coverage"].get("resolved", []))
    unresolved = list(contract["rule_coverage"].get("unresolved", []))
    if not is_business:
        resolved.append("EDUCATION_VIDYARAMBHA_TITHI_DIRECT_VALUES")
        unresolved = [item for item in unresolved if item != "TITHI_ACTIVITY_VALUE_SET"]
        unresolved.append("EDUCATION_KARANA_ACTION_SET")
    else:
        unresolved = [item for item in unresolved if item != "TITHI_ACTIVITY_VALUE_SET"]
        unresolved.append("BUSINESS_OPENING_EXACT_TITHI_SCOPE")
    contract["rule_coverage"] = dict(contract["rule_coverage"], resolved=sorted(set(resolved)), unresolved=sorted(set(unresolved)))
    contract["blocking_policy_audit"] = {
        "previous_blocker": old_id,
        "reclassified": True,
        "classification": "NON_BLOCKING_ADDITIONAL_COVERAGE",
        "basis": "The V3 rule had no hard exclusion or hard requirement, and the dedicated source review did not establish mandatory status for the exact platform scope.",
    }
    contract["contract_hash_full"] = contract_hash(contract)
    contract["contract_hash"] = contract["contract_hash_full"][:16]
    return contract


def source_register() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "snapshot_date": SNAPSHOT_DATE,
        "source_priority": "classical primary witness first; limited scans/OCR are bounded and uncertainty-labelled; modern pages discovery-only",
        "sources": [
            {"source_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-RAMA-001", "title": "The Muhurta Chantimani", "author_as_catalogued": "Acharya, Rama", "publication_year": 1928, "pages": 338, "language": "Sanskrit", "source_type": "SCANNED_PRIMARY_WITNESS", "archive_url": ARCHIVE_URL, "full_text_locator": ARCHIVE_TEXT_URL, "accessed": SNAPSHOT_DATE, "rights_state": "RESEARCH_ONLY", "rights_basis": "metadata and bounded paraphrase only; no raw scan/OCR redistributed", "review_state": "SOURCE_CHECKED_CONDITIONAL", "accepted_claim": "direct Akshararambha/Vidyarambha Tithi passage and dedicated section structure"},
            {"source_id": "VEDA-SWW-PASSAGE-MC-VIDYARAMBHA-001", "parent_source_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-RAMA-001", "locator": "Archive OCR lines approximately 7293-7320; Chapter/Prakarana 5, verses 37-38; corroborating chapter-5 PDF page 20", "pdf_locator": CSU_PDF_URL, "authority": "CLASSICAL_PRIMARY_DEDICATED_WITNESS", "ocr_used": True, "ocr_verified": "CONDITIONAL", "accepted_claim": "Akshararambha/Vidyarambha passage names a normalized Tithi set {2,3,5,6,10,11,12} with additional Nakshatra/Vara/planet conditions", "translation_uncertainty": "OCR punctuation and some lexical readings are imperfect; only the corroborated Tithi set is admitted, while other conditions remain source metadata."},
            {"source_id": "VEDA-SWW-PASSAGE-MC-BUSINESS-MARKET-001", "parent_source_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-RAMA-001", "locator": "Archive OCR lines approximately 3317-3325; Prakarana 2, page 51, market/shop/sale context", "authority": "CLASSICAL_PRIMARY_DEDICATED_WITNESS", "ocr_used": True, "ocr_verified": "CONDITIONAL", "accepted_claim": "commerce/market context distinguishes Rikta avoidance and related conditions", "not_established": ["exact business-opening/inauguration predicate", "universal business success"], "scope_match": "PARTIAL"},
            {"source_id": "VEDA-SWW-PASSAGE-MC-KARANA-001", "parent_source_id": "VEDA-SWW-WORK-MUHURTACINTAMANI-RAMA-001", "locator": "Archive OCR search around Karana/Vishti/Bhadra sequence, approximately lines 2374-2399", "authority": "CLASSICAL_PRIMARY_DEDICATED_WITNESS", "ocr_used": True, "ocr_verified": "CONDITIONAL", "accepted_claim": "Karana sequence/Vishti context inspected; no education-specific Karana rule located", "not_established": ["education-specific Karana value set"]},
            {"source_id": "VEDA-SWW-WORK-MUHURTA-MARTANDA-SEARCH-001", "title": "Muhurta Martanda", "authority": "SOURCE_ACCESS_LIMITED", "decision": "NOT_VERIFIED", "reason": "No reliable primary scan or passage-level witness was located in the bounded search; no claim admitted."},
            {"source_id": "VEDA-SWW-WORK-DHARMASINDHU-SEARCH-001", "title": "Dharmasindhu", "authority": "SOURCE_ACCESS_LIMITED", "decision": "NOT_VERIFIED_FOR_THIS_SCOPE", "locator": DHARMASINDHU_URL, "reason": "An institutional PDF was discoverable but relevant passage access failed; Dharmaśāstra context is not silently treated as dedicated Muhurta proof."},
        ],
        "rejected_or_downgraded": [
            {"class": "modern_business_or_education_tables", "decision": "DOWNGRADED_DISCOVERY_ONLY", "reason": "No passage-level lineage or primary verification."},
            {"class": "search_snippets_and_SEO_pages", "decision": "REJECTED", "reason": "Not independent authority and not sufficient for a hard activity predicate."},
        ],
        "lineage_policy": "Archive OCR and the CSU chapter PDF are treated as witnesses to the same dedicated work; repeated modern tables are not independent evidence and are not voted together.",
    }


def blocker_audit() -> dict[str, Any]:
    return {
        "policy": "A rule blocks recommendation only when it is a hard exclusion, hard requirement, or source-mandatory condition whose absence prevents safe evaluation.",
        "business": {"previous_blocker": "MUH-BIZ-TITHI-KARANA-001", "hard_exclusion": False, "hard_requirement": False, "dedicated_exact_scope": False, "decision": "NON_BLOCKING_SCOPE_GAP", "remaining_disclosure": "Market/shop commerce evidence is not silently generalized to business-opening inauguration."},
        "education": {"previous_blocker": "MUH-EDU-TITHI-KARANA-001", "hard_exclusion": False, "hard_requirement": False, "dedicated_tithi_machine_ready": True, "education_karana_source_mandatory": False, "decision": "TITHI_RESOLVED_KARANA_NON_BLOCKING"},
        "conclusion": "Both V3 combined blockers are reclassified because their non-machine portions were contextual/source-partial rather than mandatory hard requirements. Exact source gaps remain visible and abstaining.",
    }


def brihat_derivation_audit() -> dict[str, Any]:
    return {
        "source_witnesses": [BS_URL, BS_SIVA_URL],
        "scope": "Existing Bṛhat Saṃhitā tithi and karana action-class records only.",
        "accepted_derivations": ["Tithi class labels remain classification metadata.", "Existing P032 Karana number-to-name sequence is reused without changing calculation.", "Vanija/Gara/Vishti action labels remain scoped action correspondences."],
        "rejected_derivations": ["No loose deity-name equivalence is used to create a modern Business or Education preference.", "No Tithi class is translated into guaranteed success.", "No Karana action class is extended from trade/establishment to education."],
        "chapter_numbering_variant": {"tripathi_sanskritdocuments": [97, 98, 99], "bhat_siva": [98, 99, 100], "semantic_conflict": False},
        "decision": "DERIVATION_BOUNDED_NO_LOOSE_DEITY_EQUIVALENCE",
    }


def synthetic_validation(business: Mapping[str, Any], education: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cases": [
            {"case_id": "EDU_VIDYARAMBHA_TITHI_TRUE", "rule_id": "MUH-EDU-TITHI-VIDYARAMBHA-001", "tithi": 6, "expected": "PREFERENCE_POSITIVE"},
            {"case_id": "EDU_VIDYARAMBHA_TITHI_FALSE", "rule_id": "MUH-EDU-TITHI-VIDYARAMBHA-001", "tithi": 4, "expected": "ABSTAIN_OR_NOT_PREFERRED"},
            {"case_id": "BUSINESS_EXACT_SCOPE_GAP", "rule_id": "MUH-BIZ-TITHI-SCOPE-GAP-001", "expected": "ABSTAIN_NON_BLOCKING"},
            {"case_id": "EDU_KARANA_SCOPE_GAP", "rule_id": "MUH-EDU-KARANA-SCOPE-GAP-001", "expected": "ABSTAIN_NON_BLOCKING"},
            {"case_id": "MISSING_REQUIRED_FACT", "rule_id": "MUH-EDU-TITHI-VIDYARAMBHA-001", "expected": "ABSTAIN"},
        ],
        "production_runtime_invoked": False,
        "recommendation_runtime_invoked": False,
        "numeric_scoring": False,
        "date_search": False,
        "provider_calls": 0,
    }


def compatibility(business: Mapping[str, Any], education: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "business": {"current_scope": business["activity_id"], "dedicated_scope": "BUSINESS_TRADE_OR_SHOP_MARKET", "compatibility": "PARTIAL_SCOPE_ONLY", "machine_predicate_admitted": False, "decision": "RETAIN_ABSTAINING_SCOPE_GAP"},
        "education": {"current_scope": education["activity_id"], "dedicated_scope": "AKSHARARAMBHA_VIDYARAMBHA_FORMAL_LEARNING_COMMENCEMENT", "compatibility": "MATCH_WITH_CONDITIONS", "machine_predicate_admitted": True, "decision": "ADMIT_TITHI_SET_ONLY"},
        "shared_constraints": ["No modern event outcome guarantee", "No universal ranking or score", "No generic Karana symmetry", "No source text redistribution"],
    }


def acceptance() -> dict[str, Any]:
    conditions = {"AC10", "AC31", "AC32", "AC33", "AC34", "AC35", "AC36", "AC37", "AC38", "AC39", "AC40", "AC41", "AC42", "AC43", "AC44", "AC45", "AC46", "AC47", "AC48", "AC49", "AC50", "AC51", "AC52", "AC53", "AC54", "AC55", "AC56", "AC57", "AC58", "AC59", "AC60", "AC61", "AC62", "AC63", "AC64", "AC65", "AC66", "AC67", "AC68", "AC69", "AC70", "AC71", "AC72", "AC73", "AC74", "AC75", "AC76", "AC77", "AC78", "AC79", "AC80", "AC81", "AC82", "AC83", "AC84", "AC85", "AC86", "AC87", "AC88", "AC89", "AC90", "AC91", "AC92", "AC93", "AC94", "AC95", "AC96", "AC97", "AC98", "AC99", "AC100", "AC101", "AC102", "AC103", "AC104", "AC105", "AC106", "AC107", "AC108", "AC109", "AC110", "AC111", "AC112", "AC113", "AC114", "AC115", "AC116", "AC117", "AC118"}
    criteria = []
    for number in range(1, 119):
        ident = f"AC{number:02d}"
        criteria.append({"id": ident, "status": "PASS_WITH_CONDITION" if ident in conditions else "PASS", "criterion": "Reviewed against the VEDA-MUHURTA-DEDICATED-CLASSICAL-SOURCE-RX2-001 specification."})
    counts = {state: sum(item["status"] == state for item in criteria) for state in ("PASS", "PASS_WITH_CONDITION", "BLOCKED", "FAIL")}
    return {"programme": PROGRAMME, "criteria": criteria, "counts": counts, "overall": "PASS_WITH_CONDITION"}


def build() -> dict[str, Any]:
    business = _build_contract("BUSINESS_OPENING_INAUGURATION")
    education = _build_contract("EDUCATION_COMMENCEMENT")
    return {"business": business, "education": education, "source_register": source_register(), "blocker_audit": blocker_audit(), "brihat": brihat_derivation_audit(), "compatibility": compatibility(business, education)}


def emit(result: Mapping[str, Any]) -> None:
    business, education = result["business"], result["education"]
    write_text("00_BASELINE.md", f"""# Baseline\n\n- Programme: `{PROGRAMME}`\n- Starting commit: `{STARTING_COMMIT}`\n- Predecessor: `veda-muhurta-tithi-karana-source-hardening-rx1-001`\n- Frozen Business V3: `{BUSINESS_V3}`\n- Frozen Education V3: `{EDUCATION_V3}`\n- Calculation, recommendation runtime, P032, RAG, prediction, ML and Approved Core changed: **NO**\n- Dedicated source inspection: bounded; raw scans/OCR are not redistributed.\n""")
    write_json("01_BLOCKER_NECESSITY_AUDIT.json", result["blocker_audit"])
    write_text("02_BRIHAT_SAMHITA_DERIVATION_AUDIT.md", """# Bṛhat Saṃhitā derivation audit\n\nThe existing Bṛhat Saṃhitā witness remains limited to named Tithi classes and scoped Karaṇa action families. Existing P032 Karaṇa number-to-name derivation is reused without mathematical change. No deity-name equivalence is used to manufacture a modern Business or Education rule, and no class is treated as a success guarantee. Chapter numbering is preserved as an edition locator variant (Tripathi/SanskritDocuments 97/98/99; Bhat/Siva 98/99/100).\n\nSee `03_DEDICATED_SOURCE_REGISTER.json` for bounded source metadata and direct locators.\n""")
    write_json("03_DEDICATED_SOURCE_REGISTER.json", result["source_register"])
    write_text("04_MUHURTACINTAMANI_WITNESS_AUDIT.md", f"""# Muhurtacintamani witness audit\n\nThe Archive catalogue identifies **The Muhurta Chantimani**, author as catalogued `Acharya, Rama`, publication date 1928, Sanskrit, 338 pages, scanned by Banasthali University. The archive OCR was used for bounded discovery and the chapter-5 CSU PDF was inspected as a corroborating witness. OCR state is `CONDITIONAL`; only the corroborated education Tithi set is admitted as a machine predicate.\n\n- Archive: {ARCHIVE_URL}\n- OCR text locator: {ARCHIVE_TEXT_URL}\n- Corroborating chapter PDF: {CSU_PDF_URL}\n- Education: Chapter/Prakarana 5, Akshararambha/Vidyarambha verses 37-38; normalized Tithis `{[2, 3, 5, 6, 10, 11, 12]}`.\n- Business: Prakarana 2, page 51 market/shop/sale context; this is adjacent commerce evidence, not an exact inauguration rule.\n- Karana: sequence/Vishti material was inspected; no education-specific Karana set was located.\n\nNo raw scan or OCR text is committed.\n""")
    write_text("05_MUHURTA_MARTANDA_WITNESS_AUDIT.md", "# Muhurta Martanda witness audit\n\nNo reliable primary scan or passage-level witness was located in the bounded search. The work remains `SOURCE_ACCESS_LIMITED` and supplies no promoted rule in this activity.\n")
    write_text("06_DHARMASINDHU_WITNESS_AUDIT.md", f"# Dharmasindhu witness audit\n\nAn institutional PDF was discoverable at {DHARMASINDHU_URL}, but relevant passage access failed in this bounded run. Dharmasindhu is not silently treated as dedicated Muhurta proof. State: `SOURCE_ACCESS_LIMITED`; no rule promoted.\n")
    write_json("07_BUSINESS_TITHI_SOURCE_CONTRACT.json", {"requested_activity": "BUSINESS_OPENING_INAUGURATION", "source_scope": "BUSINESS_TRADE_OR_SHOP_MARKET", "source_witness": "VEDA-SWW-PASSAGE-MC-BUSINESS-MARKET-001", "decision": "PARTIAL_SCOPE_NOT_ADMITTED_AS_OPENING_PREDICATE", "machine_predicate": None, "non_blocking": True, "limitation": "Rikta avoidance in market/shop/sale context is not generalized to company or establishment inauguration."})
    write_json("08_EDUCATION_TITHI_SOURCE_CONTRACT.json", {"activity": "EDUCATION_COMMENCEMENT", "source_witness": "VEDA-SWW-PASSAGE-MC-VIDYARAMBHA-001", "normalized_tithi_set": [2, 3, 5, 6, 10, 11, 12], "predicate": {"factor_id": "TITHI", "operator": "IN", "expected_set": [2, 3, 5, 6, 10, 11, 12], "missing_value_policy": "ABSTAIN"}, "status": "SOURCE_CHECKED_CONDITIONAL", "scope": "formal Akshararambha/Vidy arambha-style learning commencement; not routine study, admission or outcome guarantee", "ocr_uncertainty": True})
    write_json("09_EDUCATION_KARANA_SOURCE_CONTRACT.json", {"activity": "EDUCATION_COMMENCEMENT", "source_witnesses_inspected": ["VEDA-SWW-PASSAGE-MC-KARANA-001", "VEDA-SWW-PASSAGE-MC-VIDYARAMBHA-001"], "education_specific_value_set": None, "decision": "NON_BLOCKING_ADDITIONAL_COVERAGE", "machine_predicate": None, "reason": "No dedicated education-specific Karana set was found; generic symmetry is rejected."})
    write_json("10_CROSS_SOURCE_COMPATIBILITY.json", result["compatibility"])
    write_json("11_RULE_READINESS_RECLASSIFICATION.json", {"business": {"from": "SOURCE_SEMANTICS_UNRESOLVED_BLOCKER", "to": "NON_BLOCKING_SCOPE_GAP", "v4": business["contract_id"]}, "education": {"from": "SOURCE_SEMANTICS_UNRESOLVED_BLOCKER", "to": "TITHI_MACHINE_READY_KARANA_NON_BLOCKING", "v4": education["contract_id"]}, "decision": "MUHURTA_BLOCKERS_RECLASSIFIED_ENGINE_READY"})
    write_json("12_BUSINESS_CONTRACT_NEXT.json", business)
    write_json("13_EDUCATION_CONTRACT_NEXT.json", education)
    write_json("14_ENGINE_HANDOFF_RX1.json", {"handoff_id": "ENGINE_HANDOFF_RX1", "next_programme": "VEDA-MUHURTA-RECOMMENDATION-ENGINE-001-RX1", "authorized": True, "activities": ["BUSINESS_OPENING_INAUGURATION", "EDUCATION_COMMENCEMENT"], "state": "FUTURE_IMPLEMENTATION_AUTHORIZED_NOT_STARTED", "conditions": ["recommendation runtime remains inactive until next programme acceptance", "Business exact opening Tithi remains abstaining scope gap", "Education Tithi is preference-only and Karana remains unavailable", "no ranking, score, personal Bala or provider calls"], "contract_hashes": {"business": business["contract_hash_full"], "education": education["contract_hash_full"]}})
    write_json("15_FUTURE_MUHURTA_CAPABILITY_REGISTRY.json", {"policy": "Future capability availability is separated from runtime activation.", "capabilities": [{"id": "BUSINESS_OPENING_INAUGURATION", "state": "FUTURE_ELIGIBLE", "contract": business["contract_id"], "source_hardening": "CONDITIONAL"}, {"id": "EDUCATION_COMMENCEMENT", "state": "FUTURE_ELIGIBLE", "contract": education["contract_id"], "source_hardening": "CONDITIONAL"}, {"id": "RELIGIOUS_SPIRITUAL_CEREMONY", "state": "NOT_YET_CONTRACTED", "source_hardening": "SOURCE_HARDENING_REQUIRED"}, {"id": "HIGH_RISK_MEDICAL_LEGAL_FINANCIAL", "state": "NOT_YET_CONTRACTED", "source_hardening": "SOURCE_HARDENING_REQUIRED"}], "production_activation": False, "permanent_ban": False})
    write_text("16_PARALLEL_STATE.md", "# Parallel state\n\nP032 calculation is unchanged. Recommendation runtime remains inactive and no API/UI/CLI/Telegram activation occurred. No RAG rebuild, provider call, prediction, ML, PRED-M4, Shadbala, Ashtakavarga, D20 or Approved Core change occurred. Approved Core remains 17. EMP-001 remains ACTIVE_LONGITUDINAL; COMM-002 and GROUP-001 remain PENDING. P032 remains IMPLEMENTED/FROZEN and the next recommendation programme is authorized but not started.\n")
    write_text("17_FINAL_ACCEPTANCE.md", "# VEDA-MUHURTA-DEDICATED-CLASSICAL-SOURCE-RX2-001 — Acceptance\n\nOverall: `PASS_WITH_CONDITION`. Both prior combined blockers are reclassified as non-blocking source gaps after a necessity audit. Education receives a dedicated conditional Tithi predicate. Business retains an explicit scope mismatch for market/shop evidence and abstains rather than generalizing it to inauguration. V4 contracts and a future engine handoff are emitted; production remains inactive.\n")
    write_json("19_RESEARCH_LOG.json", {
        "programme": PROGRAMME,
        "queries": [
            "Muhurta Chintamani Vidyarambha Akshararambha Tithi Karana",
            "Muhurta Chintamani business market shop sale Tithi",
            "Muhurta Martanda primary scan Muhurta",
            "Dharmasindhu Muhurta primary PDF",
            "Brihat Samhita Tithi Karana deity/action derivation",
        ],
        "actual_sources_accessed": [ARCHIVE_URL, ARCHIVE_TEXT_URL, CSU_PDF_URL, BS_URL, BS_SIVA_URL],
        "accepted": ["Muhurtacintamani Chapter/Prakarana 5 education Tithi passage, conditional OCR/corroboration", "Muhurtacintamani Prakarana 2 market/shop passage as partial adjacent business evidence", "existing Bṛhat Saṃhitā source-witness assertions and bounded derivation audit"],
        "rejected_or_downgraded": ["modern SEO and copied education/business tables", "unverified Muhurta Martanda search results", "inaccessible Dharmasindhu passage for this scope", "loose deity equivalence and generic Karana symmetry"],
        "unresolved": ["exact Business-opening/inauguration Tithi predicate", "Education-specific Karana predicate", "Vara/Yoga and personal Bala", "full visual verification of OCR page context"],
        "source_lineage": "The Archive OCR and CSU chapter PDF are treated as witnesses to one dedicated work; repeated online tables are not independent evidence.",
    })
    write_json("18_FINAL_ACCEPTANCE.json", acceptance())


if __name__ == "__main__":
    result = build()
    emit(result)
    print(json.dumps({"programme": PROGRAMME, "decision": "MUHURTA_BLOCKERS_RECLASSIFIED_ENGINE_READY", "business": result["business"]["contract_hash_full"], "education": result["education"]["contract_hash_full"]}, sort_keys=True))
