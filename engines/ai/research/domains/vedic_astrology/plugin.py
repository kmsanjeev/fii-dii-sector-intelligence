from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engines.ai.knowledge.astrology_governance import (
    ClaimRecord,
    ConflictRecord,
    DomainPolicyRecord,
    PassageRecord,
    SourceClass,
    VerificationStatus,
    load_registry as load_governance_registry,
)
from engines.ai.research.domains.vedic_astrology.mission_templates import build_astrology_mission_templates
from engines.ai.research.platform.contracts import (
    ConfidenceDimensions,
    ContradictionStatus,
    DomainStatus,
    KnowledgeZone,
    MissionPriority,
    ResearchCandidateRecord,
    ResearchCoreKnowledgeRecord,
    ResearchDomainPlugin,
    ResearchDomainRecord,
    ResearchEvidenceRecord,
    ResearchMissionRecord,
    SafetyClass,
    SourceObservationRecord,
)
from engines.common import config as cfg


_APPROVED_CLAIM_STATUSES = {"APPROVED", "APPROVED_WITH_CONDITIONS", "IMPLEMENTATION_READY"}
_HIGH_STAKES_DOMAINS = {"HEALTH", "LONGEVITY", "DEATH", "FERTILITY", "FINANCE", "REMEDIES"}
_QUALITY_SCORES = {"A": 1.0, "B": 0.85, "C": 0.7, "D": 0.55, "U": 0.35}
_VERIFICATION_SCORES = {
    VerificationStatus.VERIFIED.value: 1.0,
    VerificationStatus.PASSAGE_VERIFIED.value: 0.95,
    VerificationStatus.METADATA_VERIFIED.value: 0.8,
    VerificationStatus.PARTIAL.value: 0.65,
    VerificationStatus.REFERENCE_NOT_VERIFIED.value: 0.45,
    VerificationStatus.UNVERIFIED.value: 0.25,
    VerificationStatus.UNKNOWN.value: 0.2,
}
_SOURCE_CLASS_SCORES = {
    SourceClass.CLASSICAL_PRIMARY.value: 1.0,
    SourceClass.CLASSICAL_COMMENTARY.value: 0.9,
    SourceClass.TRADITIONAL_SECONDARY.value: 0.75,
    SourceClass.MODERN_PRACTITIONER.value: 0.55,
    SourceClass.ACADEMIC_SECONDARY.value: 0.7,
    SourceClass.EMPIRICAL_RESEARCH.value: 0.65,
    SourceClass.REFERENCE_EDITION.value: 0.7,
    SourceClass.DERIVED_INTERNAL.value: 0.4,
    SourceClass.HYPOTHESIS.value: 0.25,
    SourceClass.FOLKLORE_OR_UNVERIFIED.value: 0.15,
}
_CLAIM_STANCES = {
    "VEDA-CLM-000001": "SEQUENCE_DEFINED",
    "VEDA-CLM-000002": "BIRTH_BALANCE_FROM_JANMA_NAKSHATRA",
    "VEDA-CLM-000003": "LAGNA_STRENGTH_VARIANT",
    "VEDA-CLM-000004": "INTERPRET_BY_PLANET_HOUSE_ASPECT_YOGA",
    "VEDA-CLM-000005": "DEFAULT_FOR_GENERAL_POPULATION",
    "VEDA-CLM-000006": "ALTERNATE_SCOPES_PRESERVED",
}
_RULE_STANCES = {
    "VEDA-RUL-DASHA-000001": "GOVERNED_VIMSHOTTARI_BASELINE",
    "VEDA-RUL-DASHA-000002": "GOVERNED_DEFAULT_WITH_COEXISTENCE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _enum_value(value: Any) -> str:
    return value.value if hasattr(value, "value") else str(value)


def normalize_text(value: str) -> str:
    cleaned = value.lower()
    cleaned = cleaned.replace("’", "'").replace("`", "'")
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _slug(value: str) -> str:
    return normalize_text(value).replace(" ", "_").upper()


class VedicAstrologyResearchDomain(ResearchDomainPlugin):
    domain_id = "VEDA-DOMAIN-VEDIC-ASTROLOGY"

    def __init__(
        self,
        *,
        registry_root: Path | None = None,
        ontology_root: Path | None = None,
        rules_root: Path | None = None,
        uploads_root: Path | None = None,
        validation_root: Path | None = None,
    ):
        self.registry_root = Path(registry_root or cfg.VEDA_ASTROLOGY_RESEARCH_DIR)
        self.ontology_root = Path(ontology_root or cfg.VEDA_CACHE_DIR / "ontology")
        self.rules_root = Path(rules_root or (cfg.VEDA_CACHE_DIR / "rules"))
        self.uploads_root = Path(uploads_root or cfg.VEDA_CHAT_UPLOAD_DIR)
        self.validation_root = Path(validation_root or (cfg.VEDA_CACHE_DIR / "validation" / "interpretations"))

        self.registry = load_governance_registry(self.registry_root)
        self.sources = {item.source_id: item for item in self.registry["sources"]}
        self.passages = {item.passage_id: item for item in self.registry["passages"]}
        self.claims = {item.claim_id: item for item in self.registry["claims"]}
        self.conflicts = {item.conflict_id: item for item in self.registry["conflicts"]}
        self.policies = {item.domain: item for item in self.registry["policies"]}
        self.legacy_register = self.registry["legacy"][0] if self.registry["legacy"] else None
        self.approved_rules = self._load_rules(self.rules_root / "approved")
        self.draft_rules = self._load_rules(self.rules_root / "draft")
        self.p005_legacy_rules = _read_json(self.validation_root / "p005_legacy_rule_registry.json")
        self.p005_domain_matrix = _read_json(self.validation_root / "p005_domain_validation_matrix.json")
        self.p005_yoga_dosha_matrix = _read_json(self.validation_root / "p005_yoga_dosha_matrix.json")
        self.p005_high_stakes_register = _read_json(self.validation_root / "p005_high_stakes_register.json")
        self.entity_index, self.alias_index = self._load_ontology_aliases(self.ontology_root)
        self.claim_to_conflicts = self._build_claim_to_conflicts(self.conflicts.values())
        self.mission_catalog = build_astrology_mission_templates()
        self.ontology_namespace = "VEDA"
        self.source_policy = {
            "governed_registry_root": str(self.registry_root),
            "preferred_source_classes": [
                "CLASSICAL_PRIMARY",
                "CLASSICAL_COMMENTARY",
                "TRADITIONAL_SECONDARY",
                "REFERENCE_EDITION",
            ],
            "discovery_only_allowed": True,
            "requires_verifiable_passage_for_source_validated_claims": True,
        }
        self.authority_policy = {
            "dimensions": [
                "textual_authority",
                "source_quality",
                "provenance_quality",
                "cross_source_support",
                "legacy_match",
                "ontology_match",
                "contradiction_confidence",
            ],
            "primary_source_bonus": True,
            "discovery_only_caps_authority": 0.45,
        }
        self.validation_policy = {
            "minimum_independent_sources": 2,
            "supports_follow_up": True,
            "requires_ontology_mapping": True,
            "candidate_auto_promotion": False,
        }
        self.safety_policy = {
            "high_stakes_domains": sorted(_HIGH_STAKES_DOMAINS),
            "human_approval_required": True,
            "auto_promotion": False,
        }

    def domain_record(self) -> ResearchDomainRecord:
        now = utc_now()
        return ResearchDomainRecord(
            domain_id=self.domain_id,
            name="Vedic Astrology / Jyotisha",
            version="1.0.0",
            status=DomainStatus.ACTIVE,
            description="Governed autonomous research domain for Jyotisha source discovery, claim extraction, contradiction analysis, and legacy provenance recovery.",
            ontology_namespace=self.ontology_namespace,
            source_policy=self.source_policy,
            validation_policy=self.validation_policy,
            safety_policy=self.safety_policy,
            approval_policy={
                "admin_required": True,
                "auto_promotion": False,
                "promotion_state": "PROMOTION_READY",
                "high_stakes_human_approval_required": True,
            },
            provider_policy={
                "default_provider_id": "vedic-astrology-local",
                "allowed_provider_types": ["LOCAL_DOCUMENTS", "INTERNAL_KNOWLEDGE"],
            },
            schedule_policy={
                "hourly_focus": "pending missions, source discovery, follow-up research",
                "daily_focus": "cross-source comparison, provenance recovery, contradiction analysis",
                "weekly_focus": "coverage review, unresolved contradictions, synthesis planning",
                "default_cadence_type": "MANUAL_ONLY",
                "default_overlap_policy": "SKIP",
                "default_misfire_policy": "RUN_ONCE",
            },
            plugin_entrypoint="engines.ai.research.domains.vedic_astrology.plugin:VedicAstrologyResearchDomain",
            created_at=now,
            updated_at=now,
        )

    def seed_core_knowledge(self) -> list[ResearchCoreKnowledgeRecord]:
        records: list[ResearchCoreKnowledgeRecord] = []
        now = utc_now()
        for claim in self.claims.values():
            if _enum_value(claim.approval_status) not in _APPROVED_CLAIM_STATUSES:
                continue
            source_ids = sorted({self.passages[passage_id].source_id for passage_id in claim.source_passages if passage_id in self.passages})
            authority = self._source_authority_average(source_ids)
            contradiction_confidence = 0.45 if claim.conflicting_claims else 1.0
            cross_source_confidence = min(1.0, len(source_ids) / 2) if source_ids else 0.0
            source_confidence = cross_source_confidence
            provenance_confidence = 1.0 if source_ids else 0.0
            novelty_confidence = 0.85
            domain_confidence = round(
                (source_confidence + authority + cross_source_confidence + provenance_confidence + novelty_confidence + contradiction_confidence) / 6,
                4,
            )
            records.append(
                ResearchCoreKnowledgeRecord(
                    core_id=self._core_id_for_claim(claim.claim_id),
                    domain_id=self.domain_id,
                    title=self._claim_title(claim),
                    claim=claim.claim_text,
                    normalized_claim=normalize_text(claim.claim_text),
                    topic_key=self._topic_key(claim.domain, claim.subdomain, claim.claim_id),
                    stance=_CLAIM_STANCES.get(claim.claim_id, "SOURCE_VALIDATED"),
                    source_ids=source_ids,
                    knowledge_zone=KnowledgeZone.APPROVED_CORE,
                    confidence=ConfidenceDimensions(
                        source_confidence=round(source_confidence, 4),
                        authority_confidence=round(authority, 4),
                        cross_source_confidence=round(cross_source_confidence, 4),
                        provenance_confidence=round(provenance_confidence, 4),
                        novelty_confidence=round(novelty_confidence, 4),
                        contradiction_confidence=round(contradiction_confidence, 4),
                        domain_confidence=round(domain_confidence, 4),
                    ),
                    created_at=now,
                    updated_at=now,
                )
            )
        for rule_path, rule_payload in self.approved_rules.items():
            source_ids = list(rule_payload.get("provenance", {}).get("source_ids", []))
            authority = self._source_authority_average(source_ids)
            records.append(
                ResearchCoreKnowledgeRecord(
                    core_id=self._core_id_for_rule(rule_payload["rule_id"]),
                    domain_id=self.domain_id,
                    title=rule_payload["title"],
                    claim=f"Governed rule {rule_payload['rule_id']} for {rule_payload['title']}.",
                    normalized_claim=normalize_text(rule_payload["title"]),
                    topic_key=self._topic_key(rule_payload["domain"], rule_payload.get("subdomain"), rule_payload["rule_id"]),
                    stance=_RULE_STANCES.get(rule_payload["rule_id"], "GOVERNED_RULE"),
                    source_ids=source_ids,
                    knowledge_zone=KnowledgeZone.APPROVED_CORE,
                    confidence=ConfidenceDimensions(
                        source_confidence=1.0 if source_ids else 0.0,
                        authority_confidence=round(authority, 4),
                        cross_source_confidence=min(1.0, len(set(source_ids)) / 2) if source_ids else 0.0,
                        provenance_confidence=1.0 if source_ids else 0.0,
                        novelty_confidence=0.85,
                        contradiction_confidence=0.8 if rule_payload.get("provenance", {}).get("conflict_ids") else 1.0,
                        domain_confidence=round((authority + (1.0 if source_ids else 0.0) + 0.85 + (0.8 if rule_payload.get("provenance", {}).get("conflict_ids") else 1.0)) / 4, 4),
                    ),
                    created_at=now,
                    updated_at=now,
                )
            )
        return records

    def classify_source(self, source_metadata: dict[str, Any]) -> dict[str, Any]:
        source_class = str(source_metadata.get("source_class") or "").upper()
        verification_status = str(source_metadata.get("verification_status") or VerificationStatus.UNKNOWN.value)
        discovery_only = bool(source_metadata.get("discovery_only"))
        authority_score = float(source_metadata.get("authority_score", 0.0))
        if discovery_only:
            authority_score = min(authority_score, 0.45)
        return {
            "source_class": source_class or "UNKNOWN",
            "verification_status": verification_status,
            "discovery_only": discovery_only,
            "authority_score": round(authority_score, 4),
            "textual_authority": round(_SOURCE_CLASS_SCORES.get(source_class, 0.2), 4),
            "provenance_quality": round(_VERIFICATION_SCORES.get(verification_status, 0.2), 4),
        }

    def normalize_claim_text(self, text: str) -> str:
        return normalize_text(text)

    def map_ontology(self, text: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        metadata = dict(metadata or {})
        normalized = normalize_text(text)
        matched_entity_ids: list[str] = []
        for alias, entity_id in self.alias_index:
            if re.search(rf"(?:^| ){re.escape(alias)}(?:$| )", normalized):
                if entity_id not in matched_entity_ids:
                    matched_entity_ids.append(entity_id)
        ontology_gaps: list[str] = []
        if "pancha mahapurusha" in normalized and not any("MAHAPURUSHA" in item for item in matched_entity_ids):
            ontology_gaps.append("PANCHA_MAHAPURUSHA_FAMILY")
        if "guru chandal" in normalized and not any("GURU_CHANDAL" in item for item in matched_entity_ids):
            ontology_gaps.append("GURU_CHANDAL_DOSHA")
        if metadata.get("domain") in _HIGH_STAKES_DOMAINS and metadata.get("domain") not in matched_entity_ids:
            ontology_gaps.append(f"DOMAIN::{metadata['domain']}")
        return {
            "ontology_matches": matched_entity_ids,
            "ontology_gaps": sorted(set(ontology_gaps)),
        }

    def evaluate_authority(self, source_metadata: dict[str, Any]) -> dict[str, Any]:
        source_class = str(source_metadata.get("source_class") or "").upper()
        verification_status = str(source_metadata.get("verification_status") or VerificationStatus.UNKNOWN.value)
        quality_grade = str(source_metadata.get("quality_grade") or "U").upper()
        authority_score = float(source_metadata.get("authority_score", 0.0))
        if authority_score > 1.0:
            authority_score = authority_score / 100
        if bool(source_metadata.get("discovery_only")):
            authority_score = min(authority_score, 0.45)
        return {
            "textual_authority": round(_SOURCE_CLASS_SCORES.get(source_class, 0.2), 4),
            "source_quality": round(_QUALITY_SCORES.get(quality_grade, 0.35), 4),
            "provenance_quality": round(_VERIFICATION_SCORES.get(verification_status, 0.2), 4),
            "authority_score": round(authority_score or _SOURCE_CLASS_SCORES.get(source_class, 0.2), 4),
        }

    def evaluate_cross_source_support(self, candidate_payload: dict[str, Any], supporting_source_ids: list[str] | None = None) -> dict[str, Any]:
        source_ids = sorted(set(supporting_source_ids or []))
        confidence = min(1.0, len(source_ids) / 2) if source_ids else 0.0
        return {
            "supporting_source_ids": source_ids,
            "cross_source_confidence": round(confidence, 4),
            "support_level": "MULTI_SOURCE" if len(source_ids) >= 2 else "SINGLE_SOURCE",
        }

    def normalize_candidate(
        self,
        evidence: ResearchEvidenceRecord,
        observation: SourceObservationRecord,
        mission: ResearchMissionRecord,
    ) -> dict[str, Any]:
        metadata = dict(evidence.domain_metadata)
        claim_text = metadata.get("claim_text") or evidence.claim_hint
        normalized_claim = metadata.get("normalized_claim") or self.normalize_claim_text(claim_text)
        domain = str(metadata.get("domain") or "ASTROLOGY").upper()
        subdomain = str(metadata.get("subdomain") or "").upper() or None
        topic_key = metadata.get("topic_key") or self._topic_key(domain, subdomain, normalized_claim)
        ontology = self.map_ontology(claim_text, metadata)
        source_profile = self.classify_source(observation.domain_metadata)
        authority_profile = self.evaluate_authority(observation.domain_metadata)
        comparison_hint = metadata.get("comparison_hint")
        return {
            "title": metadata.get("title") or claim_text[:120],
            "claim": claim_text,
            "normalized_claim": normalized_claim,
            "topic_key": topic_key,
            "stance": metadata.get("stance") or "CANDIDATE",
            "candidate_type": metadata.get("candidate_type", "NEW_CLAIM"),
            "priority": metadata.get("priority", MissionPriority.P2.value),
            "safety_class": metadata.get("safety_class"),
            "metadata": {
                **metadata,
                **ontology,
                "source_profile": source_profile,
                "authority_profile": authority_profile,
                "domain": domain,
                "subdomain": subdomain,
                "current_knowledge_comparison_hint": comparison_hint,
            },
        }

    def validate_source(self, observation: SourceObservationRecord) -> tuple[bool, str | None]:
        metadata = dict(observation.domain_metadata)
        if metadata.get("possible_fabrication"):
            return False, "POSSIBLE_FABRICATION"
        if metadata.get("supports_claim") is False:
            return False, "PASSAGE_DOES_NOT_SUPPORT_CLAIM"
        if metadata.get("source_class") == SourceClass.FOLKLORE_OR_UNVERIFIED.value and not metadata.get("discovery_only"):
            return False, "LOW_AUTHORITY"
        if metadata.get("reference_not_verified") and metadata.get("requires_primary_source", True):
            return True, "REFERENCE_NOT_VERIFIED"
        return True, None

    def compare_to_core(self, candidate_payload: dict[str, Any], core_records: list[ResearchCoreKnowledgeRecord]) -> dict[str, Any]:
        normalized_claim = candidate_payload["normalized_claim"]
        topic_key = candidate_payload["topic_key"]
        stance = candidate_payload["stance"]
        exact_matches = [record for record in core_records if record.normalized_claim == normalized_claim]
        topic_matches = [record for record in core_records if record.topic_key == topic_key]
        legacy_rule_id = candidate_payload.get("metadata", {}).get("legacy_rule_id")
        comparison_outcome = "NEW"
        if exact_matches:
            comparison_outcome = "EXACT_MATCH"
            novelty_status = "KNOWN"
        elif topic_matches and any(record.stance == stance for record in topic_matches):
            comparison_outcome = "PARTIAL_MATCH"
            novelty_status = "REFINEMENT"
        elif topic_matches:
            comparison_outcome = "CONTRADICTS_EXISTING"
            novelty_status = "POSSIBLE_UPDATE"
        else:
            novelty_status = "NEW"

        legacy_match_status = None
        if legacy_rule_id:
            legacy_match_status = "SUPPORTS_LEGACY_RULE"
            for legacy_rule in self.p005_legacy_rules:
                if legacy_rule["legacy_rule_id"] == legacy_rule_id and legacy_rule["source_status"] in {"HEURISTIC", "ASTROFINANCE_HYPOTHESIS"}:
                    legacy_match_status = "PARTIAL_LEGACY_SUPPORT"
                    break

        return {
            "novelty_status": novelty_status,
            "comparison_outcome": comparison_outcome,
            "existing_knowledge_matches": [record.core_id for record in exact_matches or topic_matches],
            "topic_matches": [record.core_id for record in topic_matches],
            "legacy_match_status": legacy_match_status,
        }

    def detect_domain_conflict(
        self,
        candidate_payload: dict[str, Any],
        core_records: list[ResearchCoreKnowledgeRecord],
        pending_candidates: list[ResearchCandidateRecord],
    ) -> dict[str, Any]:
        topic_key = candidate_payload["topic_key"]
        stance = candidate_payload["stance"]
        metadata = candidate_payload.get("metadata", {})
        for conflict_id in metadata.get("conflict_ids", []):
            conflict = self.conflicts.get(conflict_id)
            if conflict is None:
                continue
            opposing_core = next((record for record in core_records if record.topic_key == topic_key and record.stance != stance), None)
            return {
                "contradiction_status": ContradictionStatus.CONTEXTUAL.value,
                "conflicting_core_id": opposing_core.core_id if opposing_core else None,
                "analysis": conflict.analysis,
                "conflict_id": conflict_id,
            }
        for record in core_records:
            if record.topic_key == topic_key and record.stance != stance:
                return {
                    "contradiction_status": ContradictionStatus.DIRECT.value,
                    "conflicting_core_id": record.core_id,
                    "analysis": f"Candidate stance {stance} conflicts with approved core stance {record.stance}.",
                }
        for candidate in pending_candidates:
            if candidate.topic_key == topic_key and candidate.stance != stance:
                return {
                    "contradiction_status": ContradictionStatus.DIRECT.value,
                    "conflicting_candidate_id": candidate.candidate_id,
                    "analysis": f"Candidate stance {stance} conflicts with pending candidate stance {candidate.stance}.",
                }
        return {
            "contradiction_status": ContradictionStatus.NONE.value,
            "analysis": "No contradiction detected.",
        }

    def classify_safety(self, candidate_payload: dict[str, Any]) -> SafetyClass:
        override = candidate_payload.get("safety_class")
        if override:
            return SafetyClass(override)
        metadata = candidate_payload.get("metadata", {})
        domain = str(metadata.get("domain") or "").upper()
        if domain in _HIGH_STAKES_DOMAINS:
            return SafetyClass.HIGH_STAKES
        if metadata.get("discovery_only") or metadata.get("candidate_type") in {"PROVENANCE_CANDIDATE", "ONTOLOGY_EXTENSION"}:
            return SafetyClass.MODERATE
        return SafetyClass.LOW

    def create_follow_up(self, candidate: ResearchCandidateRecord, reason: str) -> dict[str, Any] | None:
        metadata = dict(candidate.metadata)
        search_terms = list(metadata.get("search_terms") or [])
        include_uploads = bool(
            metadata.get("discovery_only")
            or metadata.get("legacy_rule_id")
            or metadata.get("ontology_gaps")
        )
        if metadata.get("ontology_gaps"):
            objective = f"Resolve ontology gaps for {candidate.title}."
            research_type = "ONTOLOGY_EXPANSION"
        elif candidate.contradiction_status != ContradictionStatus.NONE:
            objective = f"Resolve contradiction context for {candidate.title}."
            research_type = "CONTRADICTION_RESOLUTION"
        else:
            objective = f"Gather stronger cross-source support for {candidate.title}."
            research_type = "CROSS_SOURCE_VALIDATION"

        if not search_terms:
            search_terms = [candidate.claim]

        return {
            "domain_id": self.domain_id,
            "title": f"Follow-up: {candidate.title}",
            "objective": objective,
            "research_type": research_type,
            "priority": candidate.priority.value,
            "status": "QUEUED",
            "created_by": "system",
            "query_strategy": {
                "provider_id": "vedic-astrology-local",
                "queries": search_terms,
                "search_rounds": [{"queries": search_terms, "include_uploads": include_uploads}],
                "title": candidate.title,
                "claim_text": candidate.claim,
                "stance": candidate.stance,
                "legacy_rule_id": metadata.get("legacy_rule_id"),
                "claim_ids": metadata.get("claim_ids", []),
                "source_ids": metadata.get("source_ids", []),
                "domain": metadata.get("domain"),
                "subdomain": metadata.get("subdomain"),
                "topic_key": candidate.topic_key,
                "candidate_type": metadata.get("candidate_type", candidate.candidate_type.value),
                "follow_up_reason": reason,
            },
            "required_source_classes": ["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY", "REFERENCE_EDITION"],
            "minimum_independent_sources": 2,
            "known_claim_ids": metadata.get("claim_ids", []),
            "known_conflict_ids": metadata.get("conflict_ids", []),
            "known_gap_ids": metadata.get("ontology_gaps", []),
            "safety_class": candidate.safety_class.value,
            "completion_policy": {"auto_complete": False},
            "research_budget": {
                "max_queries": 2,
                "max_sources": 4,
                "max_provider_calls": 2,
                "max_runtime_seconds": 120,
                "max_model_calls": 0,
                "max_cost": 0,
                "max_follow_up_depth": 2,
                "max_retries": 1,
                "cooldown_seconds": 0,
            },
            "notes": reason,
            "follow_up_depth": metadata.get("follow_up_depth", 0) + 1,
            "parent_candidate_id": candidate.candidate_id,
            "parent_mission_id": candidate.mission_id,
        }

    def mission_templates(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.mission_catalog]

    def build_pilot_missions(self) -> list[dict[str, Any]]:
        return [
            {
                "domain_id": self.domain_id,
                "title": "Pilot A - Vimshottari Dasha Foundations",
                "objective": "Validate governed Vimshottari foundations through autonomous source discovery and cross-source comparison.",
                "research_type": "CLAIM_VALIDATION",
                "priority": "P1",
                "status": "QUEUED",
                "created_by": "admin",
                "query_strategy": {
                    "provider_id": "vedic-astrology-local",
                    "queries": [
                        "vimshottari dasha order janma nakshatra balance",
                        "hora sara vimshottari lagna stronger than moon",
                    ],
                    "search_rounds": [
                        {
                            "queries": ["vimshottari dasha order janma nakshatra balance"],
                            "source_ids": ["VEDA-SRC-000001"],
                            "claim_ids": ["VEDA-CLM-000001", "VEDA-CLM-000002"],
                        },
                        {
                            "queries": ["hora sara vimshottari lagna stronger than moon"],
                            "source_ids": ["VEDA-SRC-000002"],
                            "claim_ids": ["VEDA-CLM-000001", "VEDA-CLM-000003"],
                        },
                    ],
                },
                "required_source_classes": ["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY", "REFERENCE_EDITION"],
                "minimum_independent_sources": 2,
                "known_claim_ids": ["VEDA-CLM-000001", "VEDA-CLM-000002", "VEDA-CLM-000003"],
                "known_conflict_ids": [],
                "known_gap_ids": [],
                "safety_class": "LOW",
                "completion_policy": {"auto_complete": False},
                "research_budget": {
                    "max_queries": 2,
                    "max_sources": 6,
                    "max_provider_calls": 2,
                    "max_runtime_seconds": 120,
                    "max_model_calls": 0,
                    "max_cost": 0,
                    "max_follow_up_depth": 2,
                    "max_retries": 1,
                    "cooldown_seconds": 0,
                },
                "notes": "Controlled P007 pilot against the governed P002 Vimshottari baseline.",
            },
            {
                "domain_id": self.domain_id,
                "title": "Pilot B - Legacy Pancha Mahapurusha Provenance Recovery",
                "objective": "Recover or reject source provenance for the simplified Pancha Mahapurusha-family legacy detector.",
                "research_type": "LEGACY_RULE_PROVENANCE",
                "priority": "P2",
                "status": "QUEUED",
                "created_by": "admin",
                "query_strategy": {
                    "provider_id": "vedic-astrology-local",
                    "queries": [
                        "predictive astrology mooltrikona exaltation kendra",
                        "pancha mahapurusha exaltation mooltrikona kendra",
                    ],
                    "search_rounds": [
                        {
                            "queries": [
                                "predictive astrology mooltrikona exaltation kendra",
                                "pancha mahapurusha exaltation mooltrikona kendra",
                            ],
                            "include_uploads": True,
                            "legacy_rule_id": "VEDA-P005-LGC-0001",
                            "legacy_rule_claim": "Pancha Mahapurusha-family detections in VEDA currently depend on kendra placement and dignity heuristics and require governed provenance recovery before migration.",
                            "topic_key": "YOGA::PANCHA_MAHAPURUSHA_SIMPLIFIED",
                            "stance": "PROVENANCE_RECOVERY",
                            "candidate_type": "PROVENANCE_CANDIDATE",
                            "domain": "YOGA",
                            "subdomain": "PANCHA_MAHAPURUSHA",
                            "search_terms": ["predictive astrology", "pancha mahapurusha", "exaltation", "mooltrikona", "kendra"],
                            "requires_primary_source": True,
                        },
                        {
                            "queries": ["predictive astrology exaltation own sign mooltrikona kendra"],
                            "include_uploads": True,
                            "legacy_rule_id": "VEDA-P005-LGC-0001",
                            "legacy_rule_claim": "Pancha Mahapurusha-family detections in VEDA currently depend on kendra placement and dignity heuristics and require governed provenance recovery before migration.",
                            "topic_key": "YOGA::PANCHA_MAHAPURUSHA_SIMPLIFIED",
                            "stance": "PROVENANCE_RECOVERY",
                            "candidate_type": "PROVENANCE_CANDIDATE",
                            "domain": "YOGA",
                            "subdomain": "PANCHA_MAHAPURUSHA",
                            "search_terms": ["predictive astrology", "exaltation", "own sign", "mooltrikona", "kendra"],
                            "requires_primary_source": True,
                        },
                    ],
                },
                "required_source_classes": ["CLASSICAL_PRIMARY", "REFERENCE_EDITION"],
                "minimum_independent_sources": 2,
                "known_claim_ids": [],
                "known_conflict_ids": [],
                "known_gap_ids": ["VEDA-P005-LGC-0001"],
                "safety_class": "LOW",
                "completion_policy": {"auto_complete": False},
                "research_budget": {
                    "max_queries": 2,
                    "max_sources": 4,
                    "max_provider_calls": 2,
                    "max_runtime_seconds": 120,
                    "max_model_calls": 0,
                    "max_cost": 0,
                    "max_follow_up_depth": 2,
                    "max_retries": 1,
                    "cooldown_seconds": 0,
                },
                "notes": "The local upload corpus is treated as discovery-only unless a governed primary passage is verified.",
            },
            {
                "domain_id": self.domain_id,
                "title": "Pilot C - Vimshottari Scope Conflict",
                "objective": "Exercise the contradiction workflow on the governed Vimshottari default-versus-coexistence conflict.",
                "research_type": "CONTRADICTION_RESOLUTION",
                "priority": "P1",
                "status": "QUEUED",
                "created_by": "admin",
                "query_strategy": {
                    "provider_id": "vedic-astrology-local",
                    "queries": ["vimshottari default general populace alternate dashas source scope"],
                    "search_rounds": [
                        {
                            "queries": ["vimshottari default general populace alternate dashas source scope"],
                            "claim_ids": ["VEDA-CLM-000005", "VEDA-CLM-000006"],
                            "source_ids": ["VEDA-SRC-000001", "VEDA-SRC-000002"],
                            "conflict_ids": ["VEDA-CNF-000001"],
                        }
                    ],
                },
                "required_source_classes": ["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY"],
                "minimum_independent_sources": 2,
                "known_claim_ids": ["VEDA-CLM-000005", "VEDA-CLM-000006"],
                "known_conflict_ids": ["VEDA-CNF-000001"],
                "known_gap_ids": [],
                "safety_class": "LOW",
                "completion_policy": {"auto_complete": False},
                "research_budget": {
                    "max_queries": 1,
                    "max_sources": 4,
                    "max_provider_calls": 1,
                    "max_runtime_seconds": 120,
                    "max_model_calls": 0,
                    "max_cost": 0,
                    "max_follow_up_depth": 2,
                    "max_retries": 1,
                    "cooldown_seconds": 0,
                },
                "notes": "P005 did not contain a governed yoga/dosha conflict record, so this pilot uses the existing P002/P005 governed Vimshottari contradiction as the phase conflict-path proof.",
            },
        ]

    def generate_gap_missions(self, *, limit: int = 12) -> list[dict[str, Any]]:
        missions: list[dict[str, Any]] = []
        priority_domains = {
            "DASHA_INTERPRETATION": "P1",
            "GRAHA_BHAVA_INTERPRETATION": "P1",
            "LORDSHIP_INTERPRETATION": "P1",
            "YOGA": "P2",
            "DOSHA": "P2",
            "CAREER": "P2",
            "MARRIAGE": "P2",
            "FINANCE": "P2",
            "HEALTH_LONGEVITY": "P1",
            "REMEDIES": "P1",
            "ASTROFINANCE": "P3",
        }
        for item in self.p005_legacy_rules:
            if item["source_status"] not in {"LEGACY_UNSOURCED", "LEGACY_PARTIALLY_SOURCED", "SOURCE_CANDIDATE_FOUND"}:
                continue
            priority = priority_domains.get(item["domain"], "P3")
            missions.append(
                {
                    "domain_id": self.domain_id,
                    "title": f"Knowledge Gap - {item['legacy_rule_id']}",
                    "objective": f"Research provenance for {item['legacy_rule_id']} in domain {item['domain']}.",
                    "research_type": "LEGACY_RULE_PROVENANCE",
                    "priority": priority,
                    "status": "QUEUED",
                    "created_by": "system",
                    "query_strategy": {
                        "provider_id": "vedic-astrology-local",
                        "queries": [item["condition"], item["result"]],
                        "include_uploads": True,
                        "legacy_rule_id": item["legacy_rule_id"],
                        "legacy_rule_claim": item["notes"],
                        "topic_key": f"{item['domain']}::{_slug(item['legacy_rule_id'])}",
                        "stance": "PROVENANCE_RECOVERY",
                        "candidate_type": "PROVENANCE_CANDIDATE",
                        "domain": item["domain"],
                        "subdomain": item["legacy_rule_id"],
                        "search_terms": [item["condition"], item["result"]],
                        "requires_primary_source": item["domain"] not in {"ASTROFINANCE", "STOCK_SIGNAL"},
                    },
                    "required_source_classes": ["CLASSICAL_PRIMARY", "CLASSICAL_COMMENTARY", "REFERENCE_EDITION"],
                    "minimum_independent_sources": 2,
                    "known_claim_ids": [],
                    "known_conflict_ids": [],
                    "known_gap_ids": [item["legacy_rule_id"]],
                    "safety_class": "HIGH_STAKES" if item["domain"] in {"FINANCE", "HEALTH_LONGEVITY", "REMEDIES"} else "LOW",
                    "completion_policy": {"auto_complete": False},
                    "research_budget": {
                        "max_queries": 2,
                        "max_sources": 4,
                        "max_provider_calls": 2,
                        "max_runtime_seconds": 120,
                        "max_model_calls": 0,
                        "max_cost": 0,
                        "max_follow_up_depth": 2,
                        "max_retries": 1,
                        "cooldown_seconds": 0,
                    },
                    "notes": item["notes"],
                }
            )
            if len(missions) >= limit:
                break
        return missions

    def build_coverage_matrix(self) -> list[dict[str, Any]]:
        legacy_by_domain: dict[str, int] = {}
        for item in self.p005_legacy_rules:
            legacy_by_domain[item["domain"]] = legacy_by_domain.get(item["domain"], 0) + 1

        source_validated_by_domain: dict[str, int] = {}
        for claim in self.claims.values():
            source_validated_by_domain[claim.domain] = source_validated_by_domain.get(claim.domain, 0) + 1

        required_domains = [
            "GRAHA",
            "BHAVA",
            "DIGNITY",
            "NAKSHATRA",
            "VARGA",
            "DASHA",
            "YOGA",
            "DOSHA",
            "MARRIAGE",
            "FINANCE",
            "CAREER",
            "CHILDREN",
            "HEALTH",
            "LONGEVITY",
            "REMEDIES",
        ]
        rows: list[dict[str, Any]] = []
        domain_matrix_lookup = {row["domain"]: row for row in self.p005_domain_matrix}
        for domain in required_domains:
            matrix_row = domain_matrix_lookup.get(domain) or domain_matrix_lookup.get(f"{domain}_LONGEVITY") or {}
            existing_rules = legacy_by_domain.get(domain, 0)
            source_validated = source_validated_by_domain.get(domain, 0)
            conflicts = sum(
                1 for conflict in self.conflicts.values()
                if domain in conflict.topic.upper() or domain in getattr(self.claims.get(conflict.claim_a), "domain", "")
            )
            rows.append(
                {
                    "domain": domain,
                    "existing_rules": existing_rules,
                    "source_validated": source_validated,
                    "under_research": 1 if any(domain in mission["title"].upper() or domain in mission["objective"].upper() for mission in self.generate_gap_missions(limit=16)) else 0,
                    "conflicts": conflicts,
                    "coverage": matrix_row.get("status", "NOT_IMPLEMENTED"),
                    "recommended_action": matrix_row.get("action", "RESEARCH_FURTHER"),
                }
            )
        return rows

    def _load_rules(self, directory: Path) -> dict[Path, dict[str, Any]]:
        payloads: dict[Path, dict[str, Any]] = {}
        if not directory.exists():
            return payloads
        for path in sorted(directory.glob("*.json")):
            payloads[path] = _read_json(path)
        return payloads

    def _load_ontology_aliases(self, root: Path) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
        entity_index: dict[str, dict[str, Any]] = {}
        aliases: dict[str, str] = {}
        if not root.exists():
            return entity_index, []
        for path in sorted(root.rglob("*.json")):
            if "relations" in path.parts:
                continue
            payload = _read_json(path)
            if not isinstance(payload, list):
                continue
            for item in payload:
                entity_id = item.get("entity_id")
                if not entity_id:
                    continue
                entity_index[entity_id] = item
                names = [
                    item.get("canonical_name"),
                    item.get("sanskrit_name"),
                    item.get("transliteration"),
                    *(item.get("aliases") or []),
                    *(item.get("deprecated_aliases") or []),
                ]
                for name in names:
                    if not isinstance(name, str) or not name.strip():
                        continue
                    aliases[normalize_text(name)] = entity_id
        return entity_index, sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True)

    def _build_claim_to_conflicts(self, conflicts: list[ConflictRecord]) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for conflict in conflicts:
            mapping.setdefault(conflict.claim_a, []).append(conflict.conflict_id)
            mapping.setdefault(conflict.claim_b, []).append(conflict.conflict_id)
        return mapping

    def _claim_title(self, claim: ClaimRecord) -> str:
        if claim.subdomain:
            return f"{claim.domain} - {claim.subdomain.replace('_', ' ').title()}"
        return f"{claim.domain} - {claim.claim_id}"

    def _topic_key(self, domain: str, subdomain: str | None, fallback: str) -> str:
        if subdomain:
            return f"{str(domain).upper()}::{str(subdomain).upper()}"
        return f"{str(domain).upper()}::{_slug(str(fallback))}"

    def _source_authority_average(self, source_ids: list[str]) -> float:
        if not source_ids:
            return 0.0
        scores: list[float] = []
        for source_id in source_ids:
            source = self.sources.get(source_id)
            if source is None:
                continue
            scores.append(self.evaluate_authority(source.model_dump(mode="json"))["authority_score"])
        return round(sum(scores) / len(scores), 4) if scores else 0.0

    def _core_id_for_claim(self, claim_id: str) -> str:
        return f"VEDA-RCORE-{100000 + int(claim_id[-6:]):06d}"

    def _core_id_for_rule(self, rule_id: str) -> str:
        return f"VEDA-RCORE-{200000 + int(rule_id[-6:]):06d}"
