"""Source-governed Muhurta claims; no recommendation logic."""

from __future__ import annotations


KNOW_MUH_001 = {
    "activity_id": "VEDA-KNOW-MUH-001",
    "status": "PASS_WITH_CONDITION",
    "approved_core_promoted": 0,
    "claims": {
        "NAKSHATRA_ACTION_CLASSES": {
            "status": "VALIDATED_KNOWLEDGE",
            "authority": "CLASSICAL_PRIMARY",
            "source": "BRIHAT_SAMHITA_CH97_06_12",
            "scope": "SCOPED_EVENT_ACTION_CLASSES_ONLY",
            "production_activation": "DISABLED",
        },
        "TITHI_KARANA_ACTION_CLASSES": {
            "status": "VALIDATED_KNOWLEDGE",
            "authority": "CLASSICAL_PRIMARY",
            "source": "BRIHAT_SAMHITA_CH98_02_03;CH99_03_05",
            "scope": "SCOPED_EVENT_ACTION_CLASSES_ONLY",
            "production_activation": "DISABLED",
        },
        "MARRIAGE_SPECIFIC_KARANA_CONDITIONS": {
            "status": "VALIDATED_KNOWLEDGE",
            "authority": "CLASSICAL_PRIMARY",
            "source": "BRIHAT_SAMHITA_CH99_06_08",
            "scope": "MARRIAGE_CONTEXT_ONLY",
            "production_activation": "DISABLED",
        },
        "TARABALA": {
            "status": "RESEARCH_CANDIDATE",
            "authority": "REFERENCE_NOT_VERIFIED",
            "source": "MUHURTA_CHINTAMANI_CANDIDATE_SCAN",
            "scope": "NOT_EXECUTABLE",
            "production_activation": "DISABLED",
        },
        "CHANDRABALA": {
            "status": "RESEARCH_CANDIDATE",
            "authority": "REFERENCE_NOT_VERIFIED",
            "source": "MUHURTA_CHINTAMANI_CANDIDATE_SCAN",
            "scope": "NOT_EXECUTABLE",
            "production_activation": "DISABLED",
        },
    },
}
