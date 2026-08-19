"""Source-hardening audit for the remaining Muhurta MVP blockers.

This activity deliberately does not create a recommendation contract.  It
records what the inspected classical witness does and does not establish for
Business and Education, preserving the frozen V1/V2/V3 contracts unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_muhurta_mvp_source_semantics_hardening_001 import (
    build as build_predecessor,
    derive_factors,
    read_json,
)

PROGRAMME = "VEDA-MUHURTA-TITHI-KARANA-SOURCE-HARDENING-RX1-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "0899581dbe5020baac0a62ada178a9478198d592"
PREDECESSOR_TAG = "veda-muhurta-mvp-source-semantics-hardening-001"
OUT = ROOT / "docs/current-state/muhurta-tithi-karana-source-hardening-rx1-001"
PREDECESSOR = ROOT / "docs/current-state/muhurta-mvp-source-semantics-hardening-001"

BUSINESS_V1 = "941E9ECB9960652C"
BUSINESS_V2 = "4953E65F2019B4AF0EC2B42CC685842CFE52199B5BEC10AD9641EDA2087DE36B"
BUSINESS_V3 = "B2BFCC4CDCF20653E403EEEDD5CD2A6532009CFC44578995A9081D7DDB538075"
EDUCATION_V1 = "FFE718B6AAA8D6C9"
EDUCATION_V2 = "7A117C0AC629EB3E94A5B01EBAC8532AC1BCE1858AFBD7669CFF78D683A41CD7"
EDUCATION_V3 = "976D20F34B5E447CCDB96A773C37C664BBC596267F0BCE9AF248D19BD85A4CD4"

SOURCE_URLS = {
    "primary_sanskrit_witness": "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/bRRihatsaMhitA.html",
    "primary_translation_witness": "https://www.siva.sh/brihat-samhita/99",
    "primary_karana_witness": "https://www.siva.sh/brihat-samhita/100",
    "secondary_vidyarambha_discovery": "https://www.drikpanchang.com/shubh-dates/sanskara/education/vidyarambha/vidyarambha-dates-with-muhurat.html",
    "secondary_vidyarambha_discovery_2": "https://dekhopanchang.com/ta/learn/modules/17-4",
}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(name: str, value: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def source_register() -> dict[str, Any]:
    return {
        "programme": PROGRAMME,
        "snapshot_date": SNAPSHOT_DATE,
        "source_priority": "classical primary witness first; secondary sources discovery-only",
        "sources": [
            {
                "source_id": "VEDA-SWW-PASSAGE-BS-TITHI-CLASS-001",
                "url": SOURCE_URLS["primary_sanskrit_witness"],
                "locator": "Bṛhat Saṃhitā 98.2-3 in Tripathi/SanskritDocuments numbering; 99.2-3 in Bhat/Siva numbering",
                "authority": "CLASSICAL_PRIMARY",
                "accessed": SNAPSHOT_DATE,
                "accepted_claim": "Tithi class names and a general correspondence principle",
                "not_established": ["business-opening Tithi value set", "education-commencement Tithi value set"],
            },
            {
                "source_id": "VEDA-SWW-PASSAGE-BS-KARANA-ACTIONS-001",
                "url": SOURCE_URLS["primary_karana_witness"],
                "locator": "Bṛhat Saṃhitā 99.1-5 in Tripathi/SanskritDocuments numbering; 100.1-5 in Bhat/Siva numbering",
                "authority": "CLASSICAL_PRIMARY",
                "accessed": SNAPSHOT_DATE,
                "accepted_claim": "Vanija is merchant/trade-scoped; Gara is houses/shelters/establishment-scoped; Vishti is a caution",
                "not_established": ["education-specific learning/study Karana set"],
            },
            {
                "source_id": "MODERN-VIDYARAMBHA-TABLES-DISCOVERY-001",
                "url": SOURCE_URLS["secondary_vidyarambha_discovery"],
                "authority": "MODERN_SECONDARY_DISCOVERY_ONLY",
                "accessed": SNAPSHOT_DATE,
                "accepted_claim": "Modern table claims a Vidyarambha Tithi list",
                "decision": "DOWNGRADED",
                "reason": "No passage-level primary Jyotisha provenance was established in the accessed page; not admitted to a governed predicate.",
            },
            {
                "source_id": "MODERN-EDUCATION-MUHURTA-TABLES-DISCOVERY-002",
                "url": SOURCE_URLS["secondary_vidyarambha_discovery_2"],
                "authority": "MODERN_SECONDARY_DISCOVERY_ONLY",
                "accessed": SNAPSHOT_DATE,
                "accepted_claim": "Modern education Muhurta page combines Tithi, Vara, Yoga and Karana claims",
                "decision": "REJECTED_FOR_PROMOTION",
                "reason": "Method lineage and primary passage provenance are not supplied; cannot close a hard source-semantic blocker.",
            },
        ],
        "source_lineage": "Repeated online education tables are not independent evidence and are not merged or voted.",
        "translation_uncertainty": [
            "Tithi class/action correspondence is not equivalent to an activity-specific modern opening rule.",
            "Business opening and education commencement are narrower modern scopes than the historical action categories.",
            "Chapter numbering differs between digital witnesses; locator difference has no established semantic impact.",
        ],
    }


def tithi_semantics(activity: str) -> dict[str, Any]:
    return {
        "activity": activity,
        "decision": "SOURCE_SEMANTICS_UNRESOLVED",
        "status": "RESEARCH_CANDIDATE",
        "source_witnesses": ["VEDA-SWW-ASSERTION-BS-TITHI-CLASS-001"],
        "source_supported": {
            "classes": {
                "NANDA": [1, 6, 11],
                "BHADRA": [2, 7, 12],
                "VIJAYA": [3, 8, 13],
                "RIKTA": [4, 9, 14],
                "PURNA": [5, 10, 15],
            },
            "scope": "classification and general correspondence only",
        },
        "activity_specific_value_set": None,
        "machine_predicate": None,
        "blocker": True,
        "reason": "The inspected classical passage does not state a Business-opening or Education-commencement Tithi set. Modern tables are secondary discovery evidence only.",
        "no_inference": ["class name to modern activity preference", "Tithi class to guaranteed success", "secondary table to classical rule"],
    }


def education_karana_semantics() -> dict[str, Any]:
    return {
        "activity": "EDUCATION_COMMENCEMENT",
        "decision": "SOURCE_SEMANTICS_UNRESOLVED",
        "status": "RESEARCH_CANDIDATE",
        "source_witnesses": ["VEDA-SWW-ASSERTION-BS-KARANA-ACTIONS-001"],
        "source_supported": {
            "VANIJA": "merchant/trade action",
            "GARA": "cultivation, houses and shelters/establishment",
            "VISHTI": "caution against auspicious work; not a universal denial",
        },
        "education_specific_value_set": None,
        "machine_predicate": None,
        "blocker": True,
        "reason": "The inspected Karana passage contains no education-specific learning, study or instruction action set.",
        "no_inference": ["knowledge in a separate Nakshatra passage to education Karana", "Vanija/Gara to learning", "Vishti caution to an education universal exclusion"],
    }


def vara_yoga_audit() -> dict[str, Any]:
    return {
        "activity": "BUSINESS_OPENING_INAUGURATION",
        "decision": "NON_BLOCKING_UNRESOLVED",
        "status": "RESEARCH_CANDIDATE",
        "current_rule_id": "MUH-BIZ-VARA-YOGA-GAP-001",
        "current_effect": "ABSTAIN",
        "blocking_classification": "NON_BLOCKING_UNRESOLVED",
        "reason": "The current rule has no hard exclusion, no mandatory requirement and no preference value; it abstains and discloses that no activity-specific Vara/Yoga semantics are established.",
        "engine_readiness_effect": "Does not independently block, but remains disclosed and unavailable for positive or negative evaluation.",
        "source_witnesses": [],
        "not_promoted": True,
    }


def contract_hash(contract: Mapping[str, Any]) -> str:
    value = dict(contract)
    value.pop("contract_hash", None)
    value.pop("contract_hash_full", None)
    return digest(value)


def contract_hash_check(path: Path, expected: str) -> dict[str, Any]:
    contract = read_json(path)
    actual = contract_hash(contract)
    return {"path": str(path.relative_to(ROOT)), "expected": expected, "actual": actual, "match": actual == expected}


def blocking_inventory(business: Mapping[str, Any], education: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "business": {
            "principal_blockers": ["MUH-BIZ-TITHI-KARANA-001"],
            "non_blocking_unresolved": ["MUH-BIZ-VARA-YOGA-GAP-001"],
            "resolved_source_rules": ["MUH-BIZ-NAK-001", "MUH-BIZ-KARANA-TRADE-001", "MUH-BIZ-KARANA-ESTABLISHMENT-001"],
            "current_contract": business["contract_id"],
        },
        "education": {
            "principal_blockers": ["MUH-EDU-TITHI-KARANA-001"],
            "non_blocking_unresolved": ["MUH-EDU-VARA-YOGA-GAP-001"],
            "resolved_source_rules": ["MUH-EDU-NAK-001"],
            "current_contract": education["contract_id"],
        },
        "classification_policy": "A missing positive predicate is not converted into a permissive rule; only an explicitly ABSTAIN/non-mandatory gap is non-blocking.",
    }


def synthetic_validation() -> dict[str, Any]:
    cases = [
        {"case_id": "TITHI_CLASS_DERIVATION_ONLY", "facts": derive_factors(nakshatra=0, tithi=4, karana=7), "expected": "DERIVED_ONLY_NO_ACTIVITY_PREDICATE"},
        {"case_id": "BUSINESS_VARA_YOGA_ABSTAIN", "facts": {"VARA": None, "YOGA": None}, "expected": "ABSTAIN_NON_BLOCKING"},
        {"case_id": "EDUCATION_KARANA_MISSING_MAPPING", "facts": derive_factors(nakshatra=0, tithi=4, karana=7), "expected": "NOT_EVALUABLE_NO_EDUCATION_PREDICATE"},
    ]
    return {"cases": cases, "production_runtime_invoked": False, "recommendation_runtime_invoked": False, "numeric_scoring": False, "date_search": False, "all_expected_states_explicit": True}


def build() -> dict[str, Any]:
    predecessor = build_predecessor()
    business_path = PREDECESSOR / "10_BUSINESS_CONTRACT_V3.json"
    education_path = PREDECESSOR / "11_EDUCATION_CONTRACT_V3.json"
    business = read_json(business_path)
    education = read_json(education_path)
    hashes = {
        "business_v1": BUSINESS_V1,
        "business_v2": BUSINESS_V2,
        "business_v3": BUSINESS_V3,
        "education_v1": EDUCATION_V1,
        "education_v2": EDUCATION_V2,
        "education_v3": EDUCATION_V3,
    }
    computed = {
        "business_v3": contract_hash(business),
        "education_v3": contract_hash(education),
    }
    return {
        "programme": PROGRAMME,
        "starting_commit": STARTING_COMMIT,
        "predecessor": predecessor["decision"],
        "business": business,
        "education": education,
        "hashes": hashes,
        "computed_hashes": computed,
        "hashes_preserved": computed["business_v3"] == BUSINESS_V3 and computed["education_v3"] == EDUCATION_V3,
        "business_tithi": tithi_semantics("BUSINESS_OPENING_INAUGURATION"),
        "education_tithi": tithi_semantics("EDUCATION_COMMENCEMENT"),
        "education_karana": education_karana_semantics(),
        "business_vara_yoga": vara_yoga_audit(),
        "decision": "MUHURTA_BLOCKING_SEMANTICS_PARTIAL",
        "business_ready": False,
        "education_ready": False,
        "engine_handoff_created": False,
        "rx1_authorized": False,
    }


def emit(result: Mapping[str, Any]) -> None:
    write_text("00_BASELINE.md", f"""# Baseline

- Programme: `{PROGRAMME}`
- Starting commit: `{STARTING_COMMIT}`
- Predecessor: `{PREDECESSOR_TAG}`
- Predecessor decision: `{result['predecessor']}`
- Production calculation/recommendation code changed: **NO**
- P032 status, Recommendation runtime, RAG, Approved Core, EMP-001 and human-validation states preserved.
""")
    write_json("01_BLOCKING_RULE_INVENTORY.json", blocking_inventory(result["business"], result["education"]))
    write_json("02_TITHI_SOURCE_REGISTER.json", source_register())
    write_json("03_BUSINESS_TITHI_SEMANTICS.json", result["business_tithi"])
    write_json("04_EDUCATION_TITHI_SEMANTICS.json", result["education_tithi"])
    write_json("05_EDUCATION_KARANA_SEMANTICS.json", result["education_karana"])
    write_json("06_BUSINESS_VARA_YOGA_BLOCKER_AUDIT.json", result["business_vara_yoga"])
    write_json("07_VALUE_LINEAGE.json", {
        "tithi_class": {"source_assertion": "VEDA-SWW-ASSERTION-BS-TITHI-CLASS-001", "derivation": "P032 tithi index modulo five", "use": "classification only; no activity predicate"},
        "business_karana": {"source_assertion": "VEDA-SWW-ASSERTION-BS-KARANA-ACTIONS-001", "values": {"VANIJA": "conditional trade", "GARA": "conditional establishment", "VISHTI": "caution only"}, "production_math_changed": False},
        "education_karana": {"mapping": None, "state": "UNRESOLVED"},
        "value_lineage_hash": digest({"tithi": "classification only", "business_karana": ["VANIJA", "GARA"], "education_karana": None}),
    })
    write_json("08_VARIANT_REGISTER.json", {
        "variants": [{"id": "VEDA-SWW-VARIANT-BS-CHAPTER-NUMBERING-001", "classification": "EDITION_LOCATOR_VARIANT", "tripathi": {"tithi": "98.2-3", "karana": "99.1-5"}, "bhat_siva": {"tithi": "99.2-3", "karana": "100.1-5"}, "semantic_conflict": False}],
        "modern_education_tables": {"classification": "PRACTITIONER_MODERN_VARIANT", "status": "DOWNGRADED_NOT_PROMOTED"},
    })
    write_json("09_CONTRACT_SUPERSESSION.json", {
        "new_v4_created": False,
        "reason": "Neither activity's blocking source semantics became machine-ready; no frozen contract may be superseded.",
        "preserved": {"business_v1": BUSINESS_V1, "business_v2": BUSINESS_V2, "business_v3": BUSINESS_V3, "education_v1": EDUCATION_V1, "education_v2": EDUCATION_V2, "education_v3": EDUCATION_V3},
        "contract_mutation": False,
    })
    write_json("10_SYNTHETIC_VALIDATION.json", synthetic_validation())
    write_json("11_RESEARCH_LOG.json", {"queries": ["classical muhurta vidyarambha tithi karana", "Muhurta Chintamani education commencement", "Bṛhat Saṃhitā tithi and karana action classes"], "actual_sources": SOURCE_URLS, "accepted": ["existing Bṛhat Saṃhitā source-witness assertions"], "rejected_or_downgraded": ["modern Vidyarambha tables without passage-level provenance", "SEO/practitioner lists without method lineage"], "unresolved": ["business activity-specific Tithi", "education activity-specific Tithi", "education-specific Karana"]})
    write_text("12_PARALLEL_STATE.md", """# Parallel state

P032 calculation is unchanged. Recommendation runtime remains inactive. No date-range search, ranking, scoring, personal Bala, Tara Bala, Chandra Bala, prediction, ML, RAG or provider call was added. Approved Core remains 17. P032 remains NOT STARTED. Religious, marriage, medical, legal and financial Muhurta scopes remain outside this activity. EMP-001 remains ACTIVE LONGITUDINAL; COMM-002 and GROUP-001 remain PENDING.
""")
    write_json("13_FINAL_ACCEPTANCE.json", {
        "programme": PROGRAMME,
        "decision": result["decision"],
        "business": {"tithi": result["business_tithi"]["decision"], "vara_yoga": result["business_vara_yoga"]["decision"], "ready": False},
        "education": {"tithi": result["education_tithi"]["decision"], "karana": result["education_karana"]["decision"], "ready": False},
        "contracts_preserved": result["hashes_preserved"],
        "engine_handoff_created": False,
        "rx1_authorized": False,
        "p032_changed": False,
        "approved_core_before": 17,
        "approved_core_after": 17,
        "rag_changed": False,
        "provider_calls": 0,
    })


if __name__ == "__main__":
    value = build()
    emit(value)
    print(json.dumps({"decision": value["decision"], "hashes_preserved": value["hashes_preserved"], "business_ready": value["business_ready"], "education_ready": value["education_ready"]}, sort_keys=True))
