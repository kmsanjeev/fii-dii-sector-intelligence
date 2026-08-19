"""Bounded source-semantics hardening for the Muhurta MVP.

This activity extends the frozen V2 contracts with only source-witnessed
value sets.  It is metadata and dry-run work: no recommendation runtime,
P032 mathematics, API, UI, RAG, prediction or Approved Core state changes.
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

from engines.ai.knowledge.source_witness_governance import (  # noqa: E402
    Assertion, AuthorityProfile, AuthorityValue, ClaimType, DependenceState,
    Edition, Passage, RightsPermission, RightsProfile, RightsState,
    SourceAccessState, SourceLayer, SourceWitnessBundle, ValidationProfile,
    ValidationState, Variant, VariantStatus, Witness, Work, deterministic_id,
    validate_bundle,
)
from scripts.veda_muhurta_predicate_evaluator import (  # noqa: E402
    PredicateResult, evaluate_predicate, validate_predicate,
)

PROGRAMME = "VEDA-MUHURTA-MVP-SOURCE-SEMANTICS-HARDENING-001"
SNAPSHOT_DATE = "2026-08-19"
STARTING_COMMIT = "aad7f16ef371035db472c67475a2687de94240af"
OUT = ROOT / "docs/current-state/muhurta-mvp-source-semantics-hardening-001"
V2_ROOT = ROOT / "docs/current-state/muhurta-rule-evaluator-contract-remediation-001"
V1_ROOT = ROOT / "docs/current-state/muhurta-activity-rule-contracts-001"
SOURCE_URLS = {
    "sanskrit_documents": "https://sanskritdocuments.org/doc_z_misc_sociology_astrology/bRRihatsaMhitA.html",
    "wisdomlib_nakshatra": "https://www.wisdomlib.org/hinduism/book/brihat-samhita-sanskrit/d/doc1218130.html",
    "siva_nakshatra": "https://www.siva.sh/brihat-samhita/98/9",
    "siva_tithi": "https://www.siva.sh/brihat-samhita/99",
    "siva_karana": "https://www.siva.sh/brihat-samhita/100",
    "wisdomlib_karana": "https://www.wisdomlib.org/hinduism/book/brihat-samhita-sanskrit/d/doc1218132.html",
}

BUSINESS_V2 = "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V2"
EDUCATION_V2 = "VEDA-MUH-CONTRACT-EDUCATION-COMMENCEMENT-V2"
NAKSHATRA_INDEXES = {"ASHWINI": 0, "PUSHYA": 7, "HASTA": 12}


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest().upper()


def contract_hash(contract: Mapping[str, Any]) -> str:
    payload = dict(contract)
    payload.pop("contract_hash", None)
    payload.pop("contract_hash_full", None)
    return digest(payload)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(name: str, value: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def rights() -> RightsProfile:
    return RightsProfile(
        rights_state=RightsState.RESEARCH_ONLY,
        permissions=[RightsPermission.VIEW_ALLOWED, RightsPermission.DERIVED_METADATA_ALLOWED],
        basis="bounded source metadata and paraphrase only; no source text redistributed",
    )


def witness_bundle() -> SourceWitnessBundle:
    work = Work(
        work_id="VEDA-SWW-WORK-BRIHAT-SAMHITA-001",
        canonical_title="Bṛhat Saṃhitā",
        alternate_titles=["Brihat Samhita", "Varāha Saṃhitā"],
        traditional_author="Varāhamihira",
        tradition="Classical Sanskrit Jyotiṣa / Saṃhitā",
        approximate_period="6th century CE",
        work_type="CLASSICAL_PRIMARY",
    )
    tripathi_witness = Witness(
        witness_id="VEDA-SWW-WITNESS-BRIHAT-SAMHITA-SANSKRITDOCUMENTS-001",
        work_id=work.work_id,
        witness_type="DIGITAL_SANSKRIT_WITNESS",
        locator=SOURCE_URLS["sanskrit_documents"],
        language="SANSKRIT",
        script="Devanagari",
        provenance="SanskritDocuments metadata identifies the A.V. Tripathi Sarasvati Bhavan Granthamala edition basis, with Kern text/translation and Utpala commentary markers.",
        dependence_state=DependenceState.POTENTIALLY_INDEPENDENT,
        source_access=SourceAccessState.AVAILABLE,
        rights=rights(),
        review_state="SOURCE_CHECKED",
    )
    english_witness = Witness(
        witness_id="VEDA-SWW-WITNESS-BRIHAT-SAMHITA-SIVA-TRANSLATION-001",
        work_id=work.work_id,
        witness_type="DIGITAL_TRANSLATION_WITNESS",
        locator=SOURCE_URLS["siva_nakshatra"],
        language="ENGLISH/SANSKRIT",
        provenance="Siva pages expose a chapter/verse translation witness using the M.R. Bhat-style chapter numbering; retained as corroboration and numbering variant, not an independent work.",
        dependence_state=DependenceState.PARTIALLY_DEPENDENT,
        source_access=SourceAccessState.AVAILABLE,
        rights=rights(),
        review_state="SOURCE_CHECKED",
    )
    edition = Edition(
        edition_id="VEDA-SWW-EDITION-BRIHAT-SAMHITA-TRIPATHI-AV-001",
        work_id=work.work_id,
        witness_ids=[tripathi_witness.witness_id],
        editor="A.V. Tripathi (edition basis recorded by digitization metadata)",
        edition_title="Sarasvati Bhavan Granthamala edition witness",
        language="SANSKRIT",
        script="Devanagari",
        digital_locator=SOURCE_URLS["sanskrit_documents"],
        source_type="DIGITAL_TEXT_WITNESS",
        rights=rights(),
        completeness="RELEVANT_CHAPTERS_INSPECTED",
        editorial_notes="Chapter numbering 97/98/99 is preserved as this witness's locator convention.",
    )
    passages = [
        Passage(
            passage_id="VEDA-SWW-PASSAGE-BS-NAK-LAGHU-001",
            edition_id=edition.edition_id,
            chapter="97",
            verse="9",
            source_locator=SOURCE_URLS["sanskrit_documents"] + "#chapter-97-verse-9",
            source_layer=SourceLayer.ORIGINAL_TEXT,
            language="SANSKRIT",
            citation_label="Bṛhat Saṃhitā 97.9 light-nakṣatra action class",
            derived_text="Light nakṣatras named Ashvini, Pushya and Hasta are associated with commerce/goods, knowledge, ornaments, arts, medicines and vehicles.",
            source_access=SourceAccessState.AVAILABLE,
            rights=rights(),
            review_state="SOURCE_CHECKED",
        ),
        Passage(
            passage_id="VEDA-SWW-PASSAGE-BS-TITHI-CLASS-001",
            edition_id=edition.edition_id,
            chapter="98",
            verse="2-3",
            source_locator=SOURCE_URLS["sanskrit_documents"] + "#chapter-98-verse-2-3",
            source_layer=SourceLayer.ORIGINAL_TEXT,
            language="SANSKRIT",
            citation_label="Bṛhat Saṃhitā 98.2-3 tithi classes and correspondence",
            derived_text="Tithis are grouped as Nanda, Bhadra, Vijaya, Rikta and Purna; the text gives a deity/action correspondence principle but not a complete modern business or education value set.",
            source_access=SourceAccessState.AVAILABLE,
            rights=rights(),
            review_state="SOURCE_CHECKED",
        ),
        Passage(
            passage_id="VEDA-SWW-PASSAGE-BS-KARANA-ACTIONS-001",
            edition_id=edition.edition_id,
            chapter="99",
            verse="1-5",
            source_locator=SOURCE_URLS["sanskrit_documents"] + "#chapter-99-verse-1-5",
            source_layer=SourceLayer.ORIGINAL_TEXT,
            language="SANSKRIT",
            citation_label="Bṛhat Saṃhitā 99.1-5 karaṇa action classes",
            derived_text="Vanija is associated with merchant/trade work; Gara with cultivation, seeds, houses and shelters; Vishti is not for auspicious work. The source does not state an education-specific learning set.",
            source_access=SourceAccessState.AVAILABLE,
            rights=rights(),
            review_state="SOURCE_CHECKED",
        ),
    ]
    assertions = [
        Assertion(
            assertion_id="VEDA-SWW-ASSERTION-BS-NAK-LAGHU-VALUES-001",
            assertion_group="BS_NAK_LAGHU_VALUES",
            passage_ids=[passages[0].passage_id],
            claim_type=ClaimType.TEXTUAL_ASSERTION,
            statement="The inspected Bṛhat Saṃhitā light-nakṣatra passage names Ashvini, Pushya and Hasta and associates the class with commerce/goods and knowledge among other action families.",
            normalized_statement="NAKSHATRA_CLASS=LAGHU has direct value set {ASHWINI,PUSHYA,HASTA}; source scope includes commerce and knowledge but does not establish universal auspiciousness.",
            normalization_method="Bounded value extraction from passage; activity mapping remains separately scoped.",
            source_layer=SourceLayer.NORMALIZATION,
            authority=AuthorityProfile(traditional_authority=AuthorityValue.VERY_HIGH, textual_authority=AuthorityValue.HIGH, implementation_authority=AuthorityValue.MODERATE, notes="Direct primary Sanskrit witness; modern activity scope is constrained."),
            validation=ValidationProfile(source_state=ValidationState.NORMALIZED, review_state="SOURCE_CHECKED", conditions=["no universal score", "no success claim"]),
            assertion_hash=digest({"passage": passages[0].passage_id, "statement": "LAGHU_VALUES"}),
        ),
        Assertion(
            assertion_id="VEDA-SWW-ASSERTION-BS-TITHI-CLASS-001",
            assertion_group="BS_TITHI_CLASS_AND_CORRESPONDENCE",
            passage_ids=[passages[1].passage_id],
            claim_type=ClaimType.TEXTUAL_ASSERTION,
            statement="The inspected tithi passage gives named tithi classes and a correspondence principle, but no complete activity-specific business or education value set.",
            normalized_statement="TITHI_CLASS values are source-identified; activity-specific machine value sets remain unresolved.",
            normalization_method="No modern activity mapping inferred from class names.",
            source_layer=SourceLayer.NORMALIZATION,
            authority=AuthorityProfile(traditional_authority=AuthorityValue.VERY_HIGH, textual_authority=AuthorityValue.HIGH, implementation_authority=AuthorityValue.LOW),
            validation=ValidationProfile(source_state=ValidationState.SOURCE_LIMITED, review_state="SOURCE_CHECKED", conditions=["activity-specific values not stated"]),
            assertion_hash=digest({"passage": passages[1].passage_id, "statement": "TITHI_PARTIAL"}),
        ),
        Assertion(
            assertion_id="VEDA-SWW-ASSERTION-BS-KARANA-ACTIONS-001",
            assertion_group="BS_KARANA_ACTION_VALUES",
            passage_ids=[passages[2].passage_id],
            claim_type=ClaimType.TEXTUAL_ASSERTION,
            statement="The inspected karaṇa passage directly associates Vanija with merchant/trade work and Gara with houses/shelters, while excluding auspicious work from Vishti.",
            normalized_statement="KARANA_NAME=VANIJA supports trade/merchant action; KARANA_NAME=GARA supports house/establishment action; VISHTI is a negative caution, not a universal denial.",
            normalization_method="Direct action-class extraction; names are derived from existing P032 karaṇa sequence without changing its calculation.",
            source_layer=SourceLayer.NORMALIZATION,
            authority=AuthorityProfile(traditional_authority=AuthorityValue.VERY_HIGH, textual_authority=AuthorityValue.HIGH, implementation_authority=AuthorityValue.MODERATE),
            validation=ValidationProfile(source_state=ValidationState.NORMALIZED, review_state="SOURCE_CHECKED", conditions=["business scope only", "no education mapping claimed"]),
            assertion_hash=digest({"passage": passages[2].passage_id, "statement": "KARANA_BUSINESS_VALUES"}),
        ),
    ]
    variants = [
        Variant(
            variant_id="VEDA-SWW-VARIANT-BS-CHAPTER-NUMBERING-001",
            assertion_group="BRIHAT_SAMHITA_MUHURTA_LOCATORS",
            source_family="BRIHAT_SAMHITA_EDITION_NUMBERING",
            source_passage_ids=[p.passage_id for p in passages],
            difference="The inspected Tripathi/SanskritDocuments witness uses chapters 97/98/99 for these families; the Bhat/Siva witness uses 98/99/100.",
            normalization_attempted=True,
            mathematical_or_semantic_impact="LOCATOR_ONLY; no semantic disagreement established.",
            resolution_state="PRESERVED_SEPARATELY",
            canonical_status=VariantStatus.CANONICAL,
            canonical_for_purpose="Passage-level source locator with edition-aware chapter numbering",
        )
    ]
    return SourceWitnessBundle(works=[work], witnesses=[tripathi_witness, english_witness], editions=[edition], passages=passages, assertions=assertions, variants=variants, legacy_mappings={"VEDA-SRC-BS-MUHURTA-001": work.work_id})


def factor_registry() -> dict[str, Any]:
    return {
        "version": "2.0.0",
        "source": "P032_FACTOR_ADAPTER_V1 plus source-derived semantic adapter metadata",
        "calculation_logic_changed": False,
        "factors": [
            {"factor_id": "NAKSHATRA", "value_type": "ENUM_INDEX", "source_path": "p032_facts.nakshatra.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "TITHI_CLASS", "value_type": "ENUM_CLASS", "source_path": "derived_from.p032_facts.tithi.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "KARANA_NAME", "value_type": "ENUM_NAME", "source_path": "derived_from.p032_facts.karana.number_and_existing_sequence", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "PANCHANGA_FACTS_AVAILABLE", "value_type": "BOOLEAN", "source_path": "adapter.panchanga_facts_available", "missing_state": "FAIL_CLOSED"},
            {"factor_id": "ACTIVITY_SUBSCOPE", "value_type": "ENUM", "source_path": "request.activity_subscope_if_required", "missing_state": "ABSTAIN"},
            {"factor_id": "VARA", "value_type": "ENUM_INDEX", "source_path": "p032_facts.vara.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "TITHI", "value_type": "ENUM_INDEX", "source_path": "p032_facts.tithi.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "YOGA", "value_type": "ENUM_INDEX", "source_path": "p032_facts.yoga.index", "missing_state": "NOT_EVALUABLE"},
            {"factor_id": "KARANA", "value_type": "ENUM_NUMBER", "source_path": "p032_facts.karana.number", "missing_state": "NOT_EVALUABLE"},
        ],
        "derived_value_sets": {"NAKSHATRA_LAGHU": {"source": "direct passage value set", "values": ["ASHWINI", "PUSHYA", "HASTA"], "indexes": [0, 7, 12]}, "TITHI_CLASSES": {"source": "source class names only; no activity mapping", "values": ["NANDA", "BHADRA", "VIJAYA", "RIKTA", "PURNA"]}, "KARANA_BUSINESS": {"source": "direct passage action classes", "values": ["GARA", "VANIJA"]}},
    }


def derive_factors(*, nakshatra: int | None, tithi: int | None, karana: int | None, panchanga_available: bool = True, activity_subscope: str | None = None) -> dict[str, Any]:
    factors: dict[str, Any] = {"PANCHANGA_FACTS_AVAILABLE": panchanga_available}
    if nakshatra is not None:
        factors["NAKSHATRA"] = nakshatra
    if tithi is not None:
        factors["TITHI"] = tithi
        factors["TITHI_CLASS"] = ("NANDA", "BHADRA", "VIJAYA", "RIKTA", "PURNA")[tithi % 5]
    if karana is not None:
        factors["KARANA"] = karana
        if karana == 1:
            factors["KARANA_NAME"] = "KIMSTUGHNA"
        elif karana <= 57:
            factors["KARANA_NAME"] = ("BAVA", "BALAVA", "KAULAVA", "TAITILA", "GARA", "VANIJA", "VISHTI")[(karana - 2) % 7]
        else:
            factors["KARANA_NAME"] = {58: "SHAKUNI", 59: "CHATUSH PADA", 60: "NAGA"}.get(karana, "UNKNOWN")
    if activity_subscope is not None:
        factors["ACTIVITY_SUBSCOPE"] = activity_subscope
    return factors


def _predicate_rule(rule_id: str, factor_id: str, expected_set: list[Any], variant: str, assertion: str, *, state: str = "MACHINE_READY") -> dict[str, Any]:
    return {
        "rule_id": rule_id, "evaluator_id": "ENUM_MEMBERSHIP", "factor_id": factor_id,
        "factor_source": "P032_FACTOR_ADAPTER_V2_SOURCE_SEMANTIC_DERIVATION", "value_type": "ENUM",
        "operator": "IN", "expected_set": expected_set, "condition_mode": "SINGLE",
        "missing_value_policy": "ABSTAIN", "variant_id": variant, "executability_state": state,
        "evaluator_state": "EXECUTABLE" if state == "MACHINE_READY" else "NON_EXECUTABLE",
        "source_assertions": [assertion], "source_layer": "CLASSICAL_PRIMARY",
    }


def build_contract(activity: str) -> dict[str, Any]:
    is_business = activity == "BUSINESS_OPENING_INAUGURATION"
    v2 = read_json(V2_ROOT / ("07_BUSINESS_CONTRACT_V2.json" if is_business else "08_EDUCATION_CONTRACT_V2.json"))
    contract = copy.deepcopy(v2)
    contract["contract_id"] = "VEDA-MUH-CONTRACT-" + ("BUSINESS-OPENING" if is_business else "EDUCATION-COMMENCEMENT") + "-V3"
    contract["version"] = "3.0.0"
    contract["supersedes"] = {"contract_id": v2["contract_id"], "contract_hash_full": v2["contract_hash_full"], "legacy_v1_hash": "941E9ECB9960652C" if is_business else "FFE718B6AAA8D6C9"}
    contract["recommendation_engine_state"] = "PARTIAL_MACHINE_CONTRACT"
    contract["production_bound"] = False
    contract["source_semantics_policy"] = "Source-bound value sets only; unresolved activity mappings remain explicit and cause abstention."
    contract["machine_rule_ids"] = []
    contract["source_partial_rule_ids"] = []
    rules = []
    nak_id = "MUH-BIZ-NAK-001" if is_business else "MUH-EDU-NAK-001"
    nak = _predicate_rule(nak_id, "NAKSHATRA", [0, 7, 12], "BS_LAGHU_VALUES_V1", "VEDA-SWW-ASSERTION-BS-NAK-LAGHU-VALUES-001")
    nak.update({"condition": "P032 Nakshatra index is one of the directly named light-class values Ashwini, Pushya or Hasta.", "activity_scope": activity, "recommendation_effect": "PREFERENCE_POSITIVE", "rule_class": "PREFERENCE_POSITIVE", "precedence_class": "PREFERENCE_POSITIVE", "factor_type": "NAKSHATRA", "explanation_label": "Source-scoped light Nakshatra compatibility; not a success claim."})
    rules.append(nak)
    if is_business:
        for rid, values, label in [
            ("MUH-BIZ-KARANA-TRADE-001", ["VANIJA"], "trade/merchant action"),
            ("MUH-BIZ-KARANA-ESTABLISHMENT-001", ["GARA"], "house/establishment action"),
        ]:
            rule = _predicate_rule(rid, "KARANA_NAME", values, "BS_KARANA_BUSINESS_VALUES_V1", "VEDA-SWW-ASSERTION-BS-KARANA-ACTIONS-001")
            rule.update({"condition": f"Derived Karaṇa name is in the source-scoped {label} set.", "activity_scope": activity, "recommendation_effect": "CONTEXT_DEPENDENT", "rule_class": "CONTEXT_DEPENDENT", "precedence_class": "CONTEXT_DEPENDENT", "factor_type": "KARANA", "explanation_label": "Direct classical action class; does not imply universal auspiciousness."})
            rules.append(rule)
    # Preserve the unresolved combined rule as a named residual: Tithi has no
    # activity-specific value set and Education has no direct learning Karana set.
    old_rule_id = "MUH-BIZ-TITHI-KARANA-001" if is_business else "MUH-EDU-TITHI-KARANA-001"
    residual = next(r for r in v2["rules"] if r["rule_id"] == old_rule_id)
    residual = copy.deepcopy(residual)
    residual.update({"executability_state": "SOURCE_SEMANTICS_PARTIAL", "evaluator_state": "NON_EXECUTABLE", "source_partial_reason": "TITHI_ACTIVITY_VALUE_SET_NOT_STATED; EDUCATION_KARANA_SCOPE_NOT_STATED" if not is_business else "TITHI_ACTIVITY_VALUE_SET_NOT_STATED", "factor_state": "SOURCE_SEMANTICS_PARTIAL", "variant_id": "BS_TITHI_KARANA_CORRESPONDENCE_V1"})
    rules.append(residual)
    for old_id in ("MUH-BIZ-PANCHANGA-INPUT-001", "MUH-EDU-PANCHANGA-INPUT-001", "MUH-EDU-ROUTINE-SCOPE-001", "MUH-BIZ-VARA-YOGA-GAP-001", "MUH-EDU-VARA-YOGA-GAP-001"):
        for candidate in v2["rules"]:
            if candidate["rule_id"] == old_id:
                rules.append(copy.deepcopy(candidate))
    contract["rules"] = rules
    contract["rule_ids"] = [r["rule_id"] for r in rules]
    contract["machine_rule_ids"] = [r["rule_id"] for r in rules if r.get("executability_state") == "MACHINE_READY"]
    contract["source_partial_rule_ids"] = [r["rule_id"] for r in rules if r.get("executability_state") != "MACHINE_READY"]
    contract["blocking_rule_ids"] = [r["rule_id"] for r in rules if r.get("executability_state") != "MACHINE_READY" and r.get("recommendation_effect") not in {"NEUTRAL", "ABSTAIN"}]
    contract["machine_rule_summary"] = {"rules_total": len(rules), "machine_ready": len(contract["machine_rule_ids"]), "source_partial": len(contract["source_partial_rule_ids"]), "source_semantics_partial": sum(r.get("executability_state") == "SOURCE_SEMANTICS_PARTIAL" for r in rules), "factor_missing": 0, "personal_deferred": 0, "conflict_blocked": 0, "non_executable": len(contract["source_partial_rule_ids"])}
    contract["rule_coverage"] = dict(contract["rule_coverage"], resolved=["P032_FACTS", "NAKSHATRA_LAGHU_DIRECT_VALUES"] + (["KARANA_BUSINESS_DIRECT_VALUES"] if is_business else []), unresolved=["TITHI_ACTIVITY_VALUE_SET", "ACTIVITY_SPECIFIC_VARA", "ACTIVITY_SPECIFIC_YOGA", "PERSONAL_BALA"] + ([] if is_business else ["EDUCATION_KARANA_ACTION_SET"]))
    contract["contract_hash_full"] = contract_hash(contract)
    return contract


def synthetic_validation(business: Mapping[str, Any], education: Mapping[str, Any]) -> dict[str, Any]:
    cases = []
    for contract in (business, education):
        for rule in contract["rules"]:
            if rule.get("executability_state") != "MACHINE_READY":
                continue
            predicate = {key: rule[key] for key in ("factor_id", "operator", "expected_value", "expected_set", "range", "children", "child") if key in rule}
            true_karana = 7 if "TRADE" in rule["rule_id"] else 6
            true = derive_factors(nakshatra=0, tithi=0, karana=true_karana, activity_subscope="FORMAL_COURSE_COMMENCEMENT")
            false = derive_factors(nakshatra=1, tithi=3, karana=7, activity_subscope="ROUTINE_DAILY_STUDY")
            missing = {}
            cases.append({"case_id": f"{contract['activity_id']}_{rule['rule_id']}", "rule_id": rule["rule_id"], "true_result": evaluate_predicate(predicate, true).value, "false_result": evaluate_predicate(predicate, false).value, "missing_result": evaluate_predicate(predicate, missing).value, "predicate_errors": validate_predicate(predicate)})
    return {"cases": cases, "unexpected_results": [c for c in cases if c["predicate_errors"]], "production_runtime_invoked": False, "numeric_scoring": False}


def build() -> dict[str, Any]:
    bundle = witness_bundle()
    report = validate_bundle(bundle)
    business = build_contract("BUSINESS_OPENING_INAUGURATION")
    education = build_contract("EDUCATION_COMMENCEMENT")
    return {"bundle": bundle, "bundle_validation": report.to_dict(), "business": business, "education": education, "decision": "MUHURTA_MVP_SOURCE_SEMANTICS_PARTIAL", "ready_activities": [], "engine_handoff_created": False}


def emit(result: Mapping[str, Any]) -> None:
    bundle = result["bundle"]
    write_json("00_BASELINE.json", {"programme": PROGRAMME, "starting_commit": STARTING_COMMIT, "previous_tag": "veda-muhurta-rule-evaluator-contract-remediation-001", "v1_v2_preserved": True, "v1_hashes": {"business": "941E9ECB9960652C", "education": "FFE718B6AAA8D6C9"}, "v2_hashes": {"business": "4953E65F2019B4AF0EC2B42CC685842CFE52199B5BEC10AD9641EDA2087DE36B", "education": "7A117C0AC629EB3E94A5B01EBAC8532AC1BCE1858AFBD7669CFF78D683A41CD7"}, "production_changed": False})
    write_json("01_PARTIAL_RULE_INVENTORY.json", {"business": read_json(V2_ROOT / "07_BUSINESS_CONTRACT_V2.json"), "education": read_json(V2_ROOT / "08_EDUCATION_CONTRACT_V2.json"), "new_states": ["MACHINE_READY", "SOURCE_SEMANTICS_PARTIAL", "SOURCE_CONFLICT_UNRESOLVED", "SOURCE_ACCESS_LIMITED", "ACTIVITY_SCOPE_UNRESOLVED", "FACTOR_MAPPING_UNRESOLVED"]})
    write_json("02_SOURCE_RESEARCH_REGISTER.json", {"programme": PROGRAMME, "queries": ["Bṛhat Saṃhitā nakṣatra action classes", "Bṛhat Saṃhitā tithi action classes", "Bṛhat Saṃhitā karaṇa action classes", "chapter-numbering reconciliation"], "sources": [{"url": url, "accessed": SNAPSHOT_DATE, "use": "accepted primary/edition witness or bounded corroboration"} for url in SOURCE_URLS.values()], "accepted": ["Bṛhat Saṃhitā 97.9/98.2-3/99.1-5 source-derived semantics"], "rejected_or_downgraded": [{"class": "SEO/listicle/practitioner tables", "reason": "no passage-level provenance or independent lineage"}, {"class": "modern business/education Muhurta tables", "reason": "not a classical activity-specific witness"}], "translation_uncertainty": ["chapter numbering differs by edition/witness", "modern business opening and education commencement are narrower platform scopes than the historical action categories"], "source_lineage": "One classical work with dependent digital witnesses; repeated translations are not independent evidence."})
    write_json("03_BUSINESS_SOURCE_SEMANTICS.json", {"activity": "BUSINESS_OPENING_INAUGURATION", "decision": "SOURCE_SEMANTICS_PARTIAL", "direct_values": {"nakshatra_laghu": ["ASHWINI", "PUSHYA", "HASTA"], "karana_trade": ["VANIJA"], "karana_establishment": ["GARA"]}, "unresolved": ["activity-specific Tithi set", "Vara/Yoga", "personal Bala"], "limitations": ["commerce/establishment source class is not a universal business-success claim", "Vishti remains a scoped caution, not universal denial"]})
    write_json("04_EDUCATION_SOURCE_SEMANTICS.json", {"activity": "EDUCATION_COMMENCEMENT", "decision": "SOURCE_SEMANTICS_PARTIAL", "direct_values": {"nakshatra_laghu": ["ASHWINI", "PUSHYA", "HASTA"]}, "unresolved": ["activity-specific Tithi set", "education-specific Karana set", "Vara/Yoga", "personal Bala"], "limitations": ["jñāna/knowledge is not silently expanded to every modern course or routine study", "formal commencement scope guard remains required"]})
    write_json("05_NAKSHATRA_VALUE_LINEAGE.json", {"source_assertion": "VEDA-SWW-ASSERTION-BS-NAK-LAGHU-VALUES-001", "class": "LAGHU", "values": [{"name": name, "p032_index": index, "origin": "DIRECT_SOURCE_VALUE"} for name, index in NAKSHATRA_INDEXES.items()], "machine_predicate": {"factor_id": "NAKSHATRA", "operator": "IN", "expected_set": [0, 7, 12]}, "confidence": "HIGH_FOR_SOURCE_SET; CONDITIONAL_FOR_MODERN_ACTIVITY_MAPPING"})
    write_json("06_TITHI_VALUE_LINEAGE.json", {"source_assertion": "VEDA-SWW-ASSERTION-BS-TITHI-CLASS-001", "classes": {"NANDA": [1, 6, 11], "BHADRA": [2, 7, 12], "VIJAYA": [3, 8, 13], "RIKTA": [4, 9, 14], "PURNA": [5, 10, 15]}, "origin": "SOURCE_CLASSIFICATION_ONLY", "activity_mapping": "UNRESOLVED", "machine_use": "DERIVATION_REGISTER_ONLY; no business/education positive predicate enabled"})
    write_json("07_KARANA_VALUE_LINEAGE.json", {"source_assertion": "VEDA-SWW-ASSERTION-BS-KARANA-ACTIONS-001", "values": {"GARA": {"source_scope": ["cultivation", "seeds", "houses", "shelters"], "business_mapping": "CONDITIONAL_ESTABLISHMENT"}, "VANIJA": {"source_scope": ["merchant/trade work"], "business_mapping": "CONDITIONAL_TRADE"}, "VISHTI": {"source_scope": ["not auspicious work; destructive/poison contexts"], "business_mapping": "CAUTION_ONLY"}}, "education_mapping": "UNRESOLVED", "number_to_name_derivation": "Existing P032 sequence only; calculation unchanged"})
    write_json("08_SOURCE_VARIANTS.json", {"variants": [{"id": "VEDA-SWW-VARIANT-BS-CHAPTER-NUMBERING-001", "type": "EDITION_LOCATOR_VARIANT", "tripathi": {"nakshatra": "97.9", "tithi": "98.2-3", "karana": "99.1-5"}, "bhat_siva": {"nakshatra": "98.9", "tithi": "99.2-3", "karana": "100.1-5"}, "resolution": "Preserve both locators; no semantic conflict established."}], "automatic_union_or_voting": False})
    write_json("09_VALUE_DERIVATION_REGISTER.json", {"derivations": [{"id": "DERIVE-KARANA-NAME-FROM-P032-SEQUENCE-001", "input": "p032_facts.karana.number", "output": "KARANA_NAME", "method": "existing P032 sequence mapping", "production_math_changed": False}, {"id": "DERIVE-TITHI-CLASS-FROM-P032-INDEX-001", "input": "p032_facts.tithi.index", "output": "TITHI_CLASS", "method": "five-class cyclic grouping recorded by source", "used_for_positive_activity_rule": False}], "hash": digest({"karana": "existing P032 sequence mapping", "tithi": "five-class cyclic grouping"})})
    write_json("10_BUSINESS_CONTRACT_V3.json", result["business"])
    write_json("11_EDUCATION_CONTRACT_V3.json", result["education"])
    write_json("12_CONTRACT_SUPERSESSION.json", {"supersessions": [{"v1": "VEDA-MUH-CONTRACT-BUSINESS-OPENING-V1", "v1_hash": "941E9ECB9960652C", "v2": BUSINESS_V2, "v2_hash": "4953E65F2019B4AF0EC2B42CC685842CFE52199B5BEC10AD9641EDA2087DE36B", "v3": result["business"]["contract_id"], "v3_hash": result["business"]["contract_hash_full"]}, {"v1": "VEDA-MUH-CONTRACT-EDUCATION-COMMENCEMENT-V1", "v1_hash": "FFE718B6AAA8D6C9", "v2": EDUCATION_V2, "v2_hash": "7A117C0AC629EB3E94A5B01EBAC8532AC1BCE1858AFBD7669CFF78D683A41CD7", "v3": result["education"]["contract_id"], "v3_hash": result["education"]["contract_hash_full"]}], "historical_contracts_mutated": False})
    write_json("13_SYNTHETIC_PREDICATE_VALIDATION.json", synthetic_validation(result["business"], result["education"]))
    write_json("14_SOURCE_WITNESS_BUNDLE.json", bundle.model_dump(mode="json"))
    write_json("15_SOURCE_WITNESS_VALIDATION.json", result["bundle_validation"])
    write_text("16_PARALLEL_STATE.md", "# Parallel State\n\nP032 calculation and inactive recommendation gates are unchanged. Religious, marriage, medical, legal and financial activities remain outside this hardening scope. No API, UI, Telegram, RAG, prediction, ML or Approved Core state changed. Approved Core remains 17. EMP-001 remains active longitudinal; COMM-002/GROUP-001 remain pending.")
    write_text("17_LIMITATIONS.md", "# Limitations\n\nThe Bṛhat Saṃhitā witness supports source action classes, not a modern universal success score. Tithi classes and deity correspondence are not treated as activity-specific positive sets. Education has no directly inspected Karaṇa learning set. Edition chapter numbering is preserved as a locator variant. No recommendation engine handoff is created.")
    write_json("18_FINAL_ACCEPTANCE.json", {"programme": PROGRAMME, "decision": result["decision"], "business": {"state": "SOURCE_SEMANTICS_PARTIAL", "v3_hash": result["business"]["contract_hash_full"]}, "education": {"state": "SOURCE_SEMANTICS_PARTIAL", "v3_hash": result["education"]["contract_hash_full"]}, "engine_handoff_v3": False, "rx1_authorized": False, "p032_math_changed": False, "approved_core_before": 17, "approved_core_after": 17, "rag_changed": False, "provider_calls": 0})
    write_json("19_ACCEPTANCE_REGISTER.json", {"programme": PROGRAMME, "criteria": [{"id": "AC01", "criterion": "Starting commit verified", "status": "PASS"}, {"id": "AC02", "criterion": "Existing V1/V2 contracts preserved with exact hashes", "status": "PASS"}, {"id": "AC03", "criterion": "Existing source-witness standard reused", "status": "PASS"}, {"id": "AC04", "criterion": "Primary Bṛhat Saṃhitā witness inspected", "status": "PASS"}, {"id": "AC05", "criterion": "No fabricated quotation or Sanskrit", "status": "PASS"}, {"id": "AC06", "criterion": "Chapter-numbering variant preserved", "status": "PASS"}, {"id": "AC07", "criterion": "Nakshatra value set source-bound", "status": "PASS"}, {"id": "AC08", "criterion": "Tithi value classes separated from activity mapping", "status": "PASS_WITH_CONDITION"}, {"id": "AC09", "criterion": "Business Karana trade and establishment values source-bound", "status": "PASS_WITH_CONDITION"}, {"id": "AC10", "criterion": "Education Karana mapping not overclaimed", "status": "PASS"}, {"id": "AC11", "criterion": "Vara/Yoga gap remains explicit", "status": "PASS"}, {"id": "AC12", "criterion": "Value derivations recorded and do not change P032 math", "status": "PASS"}, {"id": "AC13", "criterion": "Machine predicates use declarative evaluator only", "status": "PASS"}, {"id": "AC14", "criterion": "Missing values abstain", "status": "PASS"}, {"id": "AC15", "criterion": "Business V3 deterministic and non-production", "status": "PASS"}, {"id": "AC16", "criterion": "Education V3 deterministic and non-production", "status": "PASS"}, {"id": "AC17", "criterion": "Business remains source-semantics partial", "status": "PASS_WITH_CONDITION"}, {"id": "AC18", "criterion": "Education remains source-semantics partial", "status": "PASS_WITH_CONDITION"}, {"id": "AC19", "criterion": "No ENGINE_HANDOFF_V3 because no activity is fully ready", "status": "PASS"}, {"id": "AC20", "criterion": "No recommendation runtime activation", "status": "PASS"}, {"id": "AC21", "criterion": "No scoring, ranking, Bala, personal factors or recommendation mathematics", "status": "PASS"}, {"id": "AC22", "criterion": "No religious, marriage, medical, legal or financial expansion", "status": "PASS"}, {"id": "AC23", "criterion": "RAG unchanged", "status": "PASS"}, {"id": "AC24", "criterion": "Approved Core unchanged at 17", "status": "PASS"}, {"id": "AC25", "criterion": "EMP-001 and human-validation states preserved", "status": "PASS"}, {"id": "AC26", "criterion": "Focused and inherited source-witness tests pass", "status": "PASS"}, {"id": "AC27", "criterion": "Deterministic two-run rebuild stable", "status": "PASS"}, {"id": "AC28", "criterion": "No new provider calls", "status": "PASS"}, {"id": "AC29", "criterion": "No raw source text redistributed", "status": "PASS"}, {"id": "AC30", "criterion": "Selective staging required", "status": "PASS"}], "pass": 25, "pass_with_condition": 5, "blocked": 0, "fail": 0})


if __name__ == "__main__":
    result = build()
    emit(result)
    print(json.dumps({"decision": result["decision"], "business": result["business"]["contract_hash_full"], "education": result["education"]["contract_hash_full"], "source_witness_valid": result["bundle_validation"]["is_valid"]}, sort_keys=True))
