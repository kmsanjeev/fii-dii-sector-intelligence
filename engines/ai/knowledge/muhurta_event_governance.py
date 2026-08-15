"""Scoped event-family provenance; no electional recommendation logic."""

KNOW_MUH_003 = {
    "activity_id": "VEDA-KNOW-MUH-003",
    "status": "PASS_WITH_CONDITION",
    "approved_core_promoted": 0,
    "production_activation": "DISABLED",
    "claims": {
        "NAKSHATRA_ACTION_FAMILIES": {
            "status": "VALIDATED_KNOWLEDGE",
            "source": "BRIHAT_SAMHITA_CH97_06_12",
            "scope": "EVENT_CLASS_CONTEXT_ONLY",
        },
        "TITHI_KARANA_ACTION_FAMILIES": {
            "status": "VALIDATED_KNOWLEDGE",
            "source": "BRIHAT_SAMHITA_CH98_02_03;CH99_03_05",
            "scope": "EVENT_CLASS_CONTEXT_ONLY",
        },
        "MARRIAGE_KARANA_CONDITIONS": {
            "status": "VALIDATED_KNOWLEDGE",
            "source": "BRIHAT_SAMHITA_CH99_06_08",
            "scope": "MARRIAGE_CONTEXT_ONLY",
        },
        "GENERAL_AUSPICIOUSNESS_SCORE": {
            "status": "DEFERRED",
            "source": "NO_SINGLE_VERIFIED_METHOD",
            "scope": "NOT_EXECUTABLE",
        },
    },
}
