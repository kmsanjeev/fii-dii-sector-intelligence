"""VEDA-P031 spirituality, dharma and inner-development governance."""

SPIRITUALITY_DOMAIN = {
    "domain_id": "SPIRITUALITY_DHARMA",
    "capability_id": "VEDA-CAP-DOMAIN-P031",
    "status": "IMPLEMENTED_FROZEN",
    "trust_state": "RESEARCH_CANDIDATE",
    "house_evidence": {"5": "RESEARCH_CANDIDATE", "8": "RESEARCH_CANDIDATE", "9": "RESEARCH_CANDIDATE", "12": "RESEARCH_CANDIDATE"},
    "planet_evidence": {"Jupiter": "RESEARCH_CANDIDATE", "Ketu": "RESEARCH_CANDIDATE", "Saturn": "RESEARCH_CANDIDATE", "Moon": "REFERENCE_LEVEL", "Sun": "REFERENCE_LEVEL"},
    "varga_policy": {"D20": "CALCULATION_AVAILABLE_INTERPRETATION_NOT_VALIDATED", "D9": "NOT_VALIDATED_FOR_SPIRITUALITY", "D12": "NOT_VALIDATED_FOR_SPIRITUALITY"},
    "blocked_outputs": [
        "ENLIGHTENMENT_CERTAINTY", "MOKSHA_CERTAINTY", "SAINTHOOD_CERTAINTY", "FORMAL_RENUNCIATION_CERTAINTY",
        "CLINICAL_DIAGNOSIS", "MENTAL_HEALTH_DIAGNOSIS", "RELIGIOUS_AUTHORITY_CLAIM", "GURU_SELECTION_ADVICE",
    ],
}


def registry() -> dict:
    return {"domains": [SPIRITUALITY_DOMAIN.copy()], "p027_owner": True, "no_second_jyotisha_engine": True}


__all__ = ["SPIRITUALITY_DOMAIN", "registry"]
