"""VEDA-P031 spirituality, dharma and inner-development governance."""

SPIRITUALITY_DOMAIN = {
    "domain_id": "SPIRITUALITY_DHARMA",
    "capability_id": "VEDA-CAP-DOMAIN-P031",
    "status": "IMPLEMENTED_FROZEN",
    "trust_state": "RESEARCH_CANDIDATE",
    "house_evidence": {"5": "RESEARCH_CANDIDATE", "8": "RESEARCH_CANDIDATE", "9": "RESEARCH_CANDIDATE", "12": "RESEARCH_CANDIDATE"},
    "planet_evidence": {"Jupiter": "RESEARCH_CANDIDATE", "Ketu": "RESEARCH_CANDIDATE", "Saturn": "RESEARCH_CANDIDATE", "Moon": "REFERENCE_LEVEL", "Sun": "REFERENCE_LEVEL", "Rahu": "RESEARCH_CANDIDATE", "Venus": "RESEARCH_CANDIDATE", "Mercury": "RESEARCH_CANDIDATE", "Mars": "RESEARCH_CANDIDATE"},
    "varga_policy": {"D20": "CALCULATION_AVAILABLE_INTERPRETATION_NOT_VALIDATED", "D9": "NOT_VALIDATED_FOR_SPIRITUALITY", "D12": "NOT_VALIDATED_FOR_SPIRITUALITY", "D24": "NOT_VALIDATED_FOR_SPIRITUALITY", "D60": "NOT_VALIDATED_FOR_SPIRITUALITY"},
    "d20_audit": {"method": "d20_vimshamsha_bphs_category_start_v1", "method_id": "D20_VIMSHAMSHA_BPHS_CATEGORY_START_V1", "method_version": "1.0", "calculation_status": "PARTIALLY_VALIDATED", "source_status": "BPHS_CH6_17_20; BPHS_CH7_4; destination-sign mapping remains source-incomplete", "interpretive_scope": "UPASANA_WORSHIP_ONLY", "interpretive_scope_status": "VALIDATED_KNOWLEDGE", "interpretation_status": "NOT_VALIDATED", "production_interpretation": "DISABLED", "fallback": "legacy generic method retained only for historical comparison; P031 never interprets D20", "p015_remediation_required": "NO_FOR_P031"},
    "yoga_dosha_policy": {"spiritual_yogas": "NOT_IMPORTED", "sannyasa": "NOT_ACTIVATED", "moksha": "ORIENTATION_ONLY_IF_SOURCE_VALIDATED", "p017_reuse": "GOVERNED_RULES_ONLY"},
    "claim_layers": {"classical": "NOT_VALIDATED_FOR_P031", "traditional_commentary": "RESEARCH_CANDIDATE", "practitioner": "DISCOVERY_ONLY", "modern": "DISCOVERY_ONLY", "platform_synthesis": "GOVERNANCE_ONLY"},
    "know_spirit_001": {"status": "PASS_WITH_CONDITION", "d20_calculation_decision": "D20_CALCULATION_PARTIALLY_VALIDATED", "d20_interpretation_decision": "D20_INTERPRETATION_RESEARCH_CANDIDATE", "p015_rx2_required": "RESOLVED_BY_P015_RX2", "approved_core_promoted": 0},
    "know_d20_001": {"status": "PASS_WITH_CONDITION", "narrow_scope": "D20 -> upasana/worship", "narrow_scope_zone": "VALIDATED_KNOWLEDGE", "full_interpretation": "RESEARCH_CANDIDATE", "production_interpretation": "DISABLED", "approved_core_promoted": 0},
    "blocked_outputs": [
        "ENLIGHTENMENT_CERTAINTY", "MOKSHA_CERTAINTY", "SAINTHOOD_CERTAINTY", "FORMAL_RENUNCIATION_CERTAINTY",
        "CLINICAL_DIAGNOSIS", "MENTAL_HEALTH_DIAGNOSIS", "RELIGIOUS_AUTHORITY_CLAIM", "GURU_SELECTION_ADVICE",
    ],
}


def registry() -> dict:
    return {"domains": [SPIRITUALITY_DOMAIN.copy()], "p027_owner": True, "no_second_jyotisha_engine": True}


__all__ = ["SPIRITUALITY_DOMAIN", "registry"]
