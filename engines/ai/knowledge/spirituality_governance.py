"""VEDA-P031 spirituality, dharma and inner-development governance."""

SPIRITUALITY_DOMAIN = {
    "domain_id": "SPIRITUALITY_DHARMA",
    "capability_id": "VEDA-CAP-DOMAIN-P031",
    "status": "IMPLEMENTED_FROZEN",
    "trust_state": "RESEARCH_CANDIDATE",
    "house_evidence": {"5": "RESEARCH_CANDIDATE", "8": "RESEARCH_CANDIDATE", "9": "RESEARCH_CANDIDATE", "12": "RESEARCH_CANDIDATE"},
    "planet_evidence": {"Jupiter": "RESEARCH_CANDIDATE", "Ketu": "RESEARCH_CANDIDATE", "Saturn": "RESEARCH_CANDIDATE", "Moon": "REFERENCE_LEVEL", "Sun": "REFERENCE_LEVEL", "Rahu": "RESEARCH_CANDIDATE", "Venus": "RESEARCH_CANDIDATE", "Mercury": "RESEARCH_CANDIDATE", "Mars": "RESEARCH_CANDIDATE"},
    "varga_policy": {"D20": "CALCULATION_AVAILABLE_INTERPRETATION_NOT_VALIDATED", "D9": "NOT_VALIDATED_FOR_SPIRITUALITY", "D12": "NOT_VALIDATED_FOR_SPIRITUALITY", "D24": "NOT_VALIDATED_FOR_SPIRITUALITY", "D60": "NOT_VALIDATED_FOR_SPIRITUALITY"},
    "d20_audit": {"method": "general", "method_version": None, "calculation_status": "IMPLEMENTED_WITH_CONDITIONS", "source_status": "P004_VALIDATED_WITH_CONDITIONS; broader provenance unresolved", "interpretation_status": "NOT_VALIDATED", "fallback": "existing general Varga path; P031 never interprets D20", "p015_remediation_required": "NO_FOR_P031"},
    "yoga_dosha_policy": {"spiritual_yogas": "NOT_IMPORTED", "sannyasa": "NOT_ACTIVATED", "moksha": "ORIENTATION_ONLY_IF_SOURCE_VALIDATED", "p017_reuse": "GOVERNED_RULES_ONLY"},
    "claim_layers": {"classical": "NOT_VALIDATED_FOR_P031", "traditional_commentary": "RESEARCH_CANDIDATE", "practitioner": "DISCOVERY_ONLY", "modern": "DISCOVERY_ONLY", "platform_synthesis": "GOVERNANCE_ONLY"},
    "blocked_outputs": [
        "ENLIGHTENMENT_CERTAINTY", "MOKSHA_CERTAINTY", "SAINTHOOD_CERTAINTY", "FORMAL_RENUNCIATION_CERTAINTY",
        "CLINICAL_DIAGNOSIS", "MENTAL_HEALTH_DIAGNOSIS", "RELIGIOUS_AUTHORITY_CLAIM", "GURU_SELECTION_ADVICE",
    ],
}


def registry() -> dict:
    return {"domains": [SPIRITUALITY_DOMAIN.copy()], "p027_owner": True, "no_second_jyotisha_engine": True}


__all__ = ["SPIRITUALITY_DOMAIN", "registry"]
