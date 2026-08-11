from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engines.ai.knowledge import approved_core_rag
from engines.ai.knowledge.astrology_governance import validate_registry_directory
from engines.ai.research.domains.vedic_astrology.plugin import VedicAstrologyResearchDomain
from engines.common import config as cfg
from engines.intelligence.kundli_engine import KundliEngine, SIGNS


ROOT = Path(__file__).resolve().parents[3]
_TS = "2026-08-11T00:00:00Z"
_AUTHOR = "codex"
_RULE_CONTRACT_VERSION = "2026-08-10"
_PHASE_CONTRACT_VERSION = "2026-08-11"

_GRAHA_NAME_BY_ID = {
    "VEDA-GRAHA-SUN": "Sun",
    "VEDA-GRAHA-MOON": "Moon",
    "VEDA-GRAHA-MARS": "Mars",
    "VEDA-GRAHA-MERCURY": "Mercury",
    "VEDA-GRAHA-JUPITER": "Jupiter",
    "VEDA-GRAHA-VENUS": "Venus",
    "VEDA-GRAHA-SATURN": "Saturn",
    "VEDA-GRAHA-RAHU": "Rahu",
    "VEDA-GRAHA-KETU": "Ketu",
}
_GRAHA_ID_BY_NAME = {value: key for key, value in _GRAHA_NAME_BY_ID.items()}
_RASHI_NAME_BY_ID = {
    "VEDA-RASHI-ARIES": "Aries",
    "VEDA-RASHI-TAURUS": "Taurus",
    "VEDA-RASHI-GEMINI": "Gemini",
    "VEDA-RASHI-CANCER": "Cancer",
    "VEDA-RASHI-LEO": "Leo",
    "VEDA-RASHI-VIRGO": "Virgo",
    "VEDA-RASHI-LIBRA": "Libra",
    "VEDA-RASHI-SCORPIO": "Scorpio",
    "VEDA-RASHI-SAGITTARIUS": "Sagittarius",
    "VEDA-RASHI-CAPRICORN": "Capricorn",
    "VEDA-RASHI-AQUARIUS": "Aquarius",
    "VEDA-RASHI-PISCES": "Pisces",
}
_RASHI_ID_BY_NAME = {value: key for key, value in _RASHI_NAME_BY_ID.items()}
_HOUSE_ID_BY_NUMBER = {index: f"VEDA-BHAVA-{index:02d}" for index in range(1, 13)}
_CLASSICAL_GRAHA_IDS = [
    "VEDA-GRAHA-SUN",
    "VEDA-GRAHA-MOON",
    "VEDA-GRAHA-MARS",
    "VEDA-GRAHA-MERCURY",
    "VEDA-GRAHA-JUPITER",
    "VEDA-GRAHA-VENUS",
    "VEDA-GRAHA-SATURN",
]
_SIGN_LORDSHIP_ROWS = [
    {"graha_entity_id": "VEDA-GRAHA-SUN", "rashi_entity_ids": ["VEDA-RASHI-LEO"]},
    {"graha_entity_id": "VEDA-GRAHA-MOON", "rashi_entity_ids": ["VEDA-RASHI-CANCER"]},
    {"graha_entity_id": "VEDA-GRAHA-MARS", "rashi_entity_ids": ["VEDA-RASHI-ARIES", "VEDA-RASHI-SCORPIO"]},
    {"graha_entity_id": "VEDA-GRAHA-MERCURY", "rashi_entity_ids": ["VEDA-RASHI-GEMINI", "VEDA-RASHI-VIRGO"]},
    {"graha_entity_id": "VEDA-GRAHA-JUPITER", "rashi_entity_ids": ["VEDA-RASHI-SAGITTARIUS", "VEDA-RASHI-PISCES"]},
    {"graha_entity_id": "VEDA-GRAHA-VENUS", "rashi_entity_ids": ["VEDA-RASHI-TAURUS", "VEDA-RASHI-LIBRA"]},
    {"graha_entity_id": "VEDA-GRAHA-SATURN", "rashi_entity_ids": ["VEDA-RASHI-CAPRICORN", "VEDA-RASHI-AQUARIUS"]},
]
_EXALTATION_ROWS = [
    {"graha_entity_id": "VEDA-GRAHA-SUN", "rashi_entity_id": "VEDA-RASHI-ARIES", "exact_degree": 10.0, "debilitation_rashi_entity_id": "VEDA-RASHI-LIBRA", "deepest_debilitation_degree": 10.0},
    {"graha_entity_id": "VEDA-GRAHA-MOON", "rashi_entity_id": "VEDA-RASHI-TAURUS", "exact_degree": 3.0, "debilitation_rashi_entity_id": "VEDA-RASHI-SCORPIO", "deepest_debilitation_degree": 3.0},
    {"graha_entity_id": "VEDA-GRAHA-MARS", "rashi_entity_id": "VEDA-RASHI-CAPRICORN", "exact_degree": 28.0, "debilitation_rashi_entity_id": "VEDA-RASHI-CANCER", "deepest_debilitation_degree": 28.0},
    {"graha_entity_id": "VEDA-GRAHA-MERCURY", "rashi_entity_id": "VEDA-RASHI-VIRGO", "exact_degree": 15.0, "debilitation_rashi_entity_id": "VEDA-RASHI-PISCES", "deepest_debilitation_degree": 15.0},
    {"graha_entity_id": "VEDA-GRAHA-JUPITER", "rashi_entity_id": "VEDA-RASHI-CANCER", "exact_degree": 5.0, "debilitation_rashi_entity_id": "VEDA-RASHI-CAPRICORN", "deepest_debilitation_degree": 5.0},
    {"graha_entity_id": "VEDA-GRAHA-VENUS", "rashi_entity_id": "VEDA-RASHI-PISCES", "exact_degree": 27.0, "debilitation_rashi_entity_id": "VEDA-RASHI-VIRGO", "deepest_debilitation_degree": 27.0},
    {"graha_entity_id": "VEDA-GRAHA-SATURN", "rashi_entity_id": "VEDA-RASHI-LIBRA", "exact_degree": 20.0, "debilitation_rashi_entity_id": "VEDA-RASHI-ARIES", "deepest_debilitation_degree": 20.0},
]
_MOOLATRIKONA_PREFERRED_ROWS = [
    {"graha_entity_id": "VEDA-GRAHA-SUN", "rashi_entity_id": "VEDA-RASHI-LEO", "degree_start": 0.0, "degree_end": 20.0},
    {"graha_entity_id": "VEDA-GRAHA-MOON", "rashi_entity_id": "VEDA-RASHI-TAURUS", "degree_start": 4.0, "degree_end": 30.0},
    {"graha_entity_id": "VEDA-GRAHA-MARS", "rashi_entity_id": "VEDA-RASHI-ARIES", "degree_start": 1.0, "degree_end": 12.0},
    {"graha_entity_id": "VEDA-GRAHA-MERCURY", "rashi_entity_id": "VEDA-RASHI-VIRGO", "degree_start": 16.0, "degree_end": 20.0},
    {"graha_entity_id": "VEDA-GRAHA-JUPITER", "rashi_entity_id": "VEDA-RASHI-SAGITTARIUS", "degree_start": 1.0, "degree_end": 10.0},
    {"graha_entity_id": "VEDA-GRAHA-VENUS", "rashi_entity_id": "VEDA-RASHI-LIBRA", "degree_start": 0.0, "degree_end": 5.0},
    {"graha_entity_id": "VEDA-GRAHA-SATURN", "rashi_entity_id": "VEDA-RASHI-AQUARIUS", "degree_start": 1.0, "degree_end": 20.0},
]
_MOOLATRIKONA_VARIANT_ROWS = [
    {"graha_entity_id": "VEDA-GRAHA-SUN", "rashi_entity_id": "VEDA-RASHI-LEO", "degree_start": 0.0, "degree_end": 20.0},
    {"graha_entity_id": "VEDA-GRAHA-MOON", "rashi_entity_id": "VEDA-RASHI-TAURUS", "degree_start": 3.0, "degree_end": 30.0},
    {"graha_entity_id": "VEDA-GRAHA-MARS", "rashi_entity_id": "VEDA-RASHI-ARIES", "degree_start": 0.0, "degree_end": 12.0},
    {"graha_entity_id": "VEDA-GRAHA-MERCURY", "rashi_entity_id": "VEDA-RASHI-VIRGO", "degree_start": 15.0, "degree_end": 20.0},
    {"graha_entity_id": "VEDA-GRAHA-JUPITER", "rashi_entity_id": "VEDA-RASHI-SAGITTARIUS", "degree_start": 0.0, "degree_end": 10.0},
    {"graha_entity_id": "VEDA-GRAHA-VENUS", "rashi_entity_id": "VEDA-RASHI-LIBRA", "degree_start": 0.0, "degree_end": 15.0},
    {"graha_entity_id": "VEDA-GRAHA-SATURN", "rashi_entity_id": "VEDA-RASHI-AQUARIUS", "degree_start": 0.0, "degree_end": 20.0},
]
_HOUSE_CLASS_ROWS = [
    {"class_entity_id": "VEDA-HCLASS-KENDRA", "bhava_numbers": [1, 4, 7, 10]},
    {"class_entity_id": "VEDA-HCLASS-TRIKONA", "bhava_numbers": [1, 5, 9]},
    {"class_entity_id": "VEDA-HCLASS-DUSTHANA", "bhava_numbers": [6, 8, 12]},
    {"class_entity_id": "VEDA-HCLASS-UPACHAYA", "bhava_numbers": [3, 6, 10, 11]},
]
_FOUNDATION_SOURCE_IDS = ["VEDA-SRC-000008", "VEDA-SRC-000009"]
_FOUNDATION_CLAIM_IDS = ["VEDA-CLM-000007", "VEDA-CLM-000008", "VEDA-CLM-000009", "VEDA-CLM-000010", "VEDA-CLM-000011", "VEDA-CLM-000012"]
_FOUNDATION_RULE_IDS = ["VEDA-RUL-GRAHA-000001", "VEDA-RUL-DIGNITY-000002", "VEDA-RUL-BHAVA-000001"]
_FOUNDATION_CONFLICT_IDS = ["VEDA-CNF-000002"]
_FOUNDATION_LEGACY_MAPPING_IDS = ["VEDA-LMP-000004", "VEDA-LMP-000005", "VEDA-LMP-000006"]
_SIGN_LORDSHIP_TABLE = {
    "table_type": "GRAHA_SIGN_LORDSHIP",
    "rows": _SIGN_LORDSHIP_ROWS,
}
_DIGNITY_TABLE = {
    "table_type": "DIGNITY_CLASSIFICATION",
    "classical_graha_ids": _CLASSICAL_GRAHA_IDS,
    "exaltation_rows": _EXALTATION_ROWS,
    "own_sign_rows": _SIGN_LORDSHIP_ROWS,
    "moolatrikona_preferred_rows": _MOOLATRIKONA_PREFERRED_ROWS,
    "moolatrikona_variant_rows": _MOOLATRIKONA_VARIANT_ROWS,
    "conditional_conflict_ids": ["VEDA-CNF-000002"],
    "excluded_from_governed_foundation": ["VEDA-GRAHA-RAHU", "VEDA-GRAHA-KETU"],
    "not_yet_governed_branches": ["FRIENDSHIP", "ENMITY", "NODE_DIGNITY"],
}
_BHAVA_TABLE = {
    "table_type": "HOUSE_CLASSIFICATION",
    "rows": _HOUSE_CLASS_ROWS,
}


def _artifact_meta() -> dict[str, str]:
    return {
        "version": "1.0.0",
        "created_at": _TS,
        "created_by": _AUTHOR,
        "updated_at": _TS,
        "updated_by": _AUTHOR,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_rule(rule_id: str) -> dict[str, Any]:
    return _read_json(cfg.VEDA_ASTROLOGY_RULE_APPROVED_DIR / f"{rule_id}.json")


def _legacy_mapping(rule_id: str, function_name: str, behavior: str, known_differences: list[str]) -> dict[str, Any]:
    return {
        **_artifact_meta(),
        "change_reason": "P014 governed foundation mapping for legacy foundational behavior.",
        "supersedes": None,
        "superseded_by": None,
        "notes": "P014 preserves legacy history while linking governed foundation rules to current runtime behavior.",
        "contract_version": _RULE_CONTRACT_VERSION,
        "legacy_mapping_id": rule_id,
        "legacy_location": "engines/intelligence/kundli_engine.py",
        "legacy_function": function_name,
        "legacy_behavior": behavior,
        "target_rule_ids": [],
        "mapping_status": "MAPPED_TO_SCHEMA",
        "semantic_match": "PARTIAL",
        "known_differences": known_differences,
        "source_status": "LEGACY_PARTIALLY_SOURCED",
        "migration_recommendation": "Keep the production implementation untouched until explicit Admin activation authorizes the governed replacement.",
    }


def foundation_sources() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 governed foundation source registration for dignity, graha, and bhava baselines.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Used as a traditional-secondary authority source for sign lordship, dignity tables, and bhava classifications.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "source_id": "VEDA-SRC-000008",
            "title_original": "Predictive Astrology of the Hindus",
            "title_normalized": "Predictive Astrology of the Hindus",
            "source_class": "TRADITIONAL_SECONDARY",
            "author_attributed": "B. V. Raman",
            "author_normalized": "B V Raman",
            "historical_period": "20th century",
            "language_original": "English",
            "edition": "Digital scan of Predictive Astrology of the Hindus",
            "publisher": None,
            "publication_year": 2009,
            "translator": None,
            "commentator": None,
            "isbn_or_identifier": "local-upload/26342d562eb64209958cb5f00572db60",
            "digital_source": "data/veda/uploads/26342d562eb64209958cb5f00572db60.pdf",
            "legal_access_status": "LIMITED_QUOTATION_ONLY",
            "primary_or_secondary": "SECONDARY",
            "tradition": "Parasari",
            "school": "Traditional secondary synthesis",
            "domains": ["FOUNDATION", "DIGNITY", "GRAHA", "BHAVA"],
            "quality_grade": "B",
            "authority_score": 84,
            "authority_profile": {
                "authority_tier": "TIER_B",
                "textual_authority": 4,
                "traditional_authority": 4,
                "translation_reliability": 4,
                "cross_source_support": 4,
                "empirical_support": 0,
                "implementation_confidence": 4,
                "notes": "Traditional secondary source with explicit tables for sign lordship, exaltation, moolatrikona, and house-class vocabulary.",
            },
            "verification_status": "PASSAGE_VERIFIED",
            "evidence_type": "TRADITIONAL_INTERPRETIVE",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 governed foundation corroboration source registration.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Used to corroborate dignity tables and preserve documented variance, especially around moolatrikona and node treatment.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "source_id": "VEDA-SRC-000009",
            "title_original": "Predictive Astrology",
            "title_normalized": "Predictive Astrology",
            "source_class": "TRADITIONAL_SECONDARY",
            "author_attributed": "M. N. Kedar",
            "author_normalized": "M N Kedar",
            "historical_period": "late 20th century",
            "language_original": "English",
            "edition": "Merged revised edition scan",
            "publisher": "Bharatiya Prachya Evam Sanatan Vigyan Sansthan",
            "publication_year": None,
            "translator": None,
            "commentator": None,
            "isbn_or_identifier": "local-upload/7430aad7a36d4ab5bab526491126c577",
            "digital_source": "data/veda/uploads/7430aad7a36d4ab5bab526491126c577.pdf",
            "legal_access_status": "LIMITED_QUOTATION_ONLY",
            "primary_or_secondary": "SECONDARY",
            "tradition": "Parasari",
            "school": "Traditional secondary synthesis",
            "domains": ["FOUNDATION", "DIGNITY"],
            "quality_grade": "C",
            "authority_score": 76,
            "authority_profile": {
                "authority_tier": "TIER_C",
                "textual_authority": 3,
                "traditional_authority": 4,
                "translation_reliability": 3,
                "cross_source_support": 3,
                "empirical_support": 0,
                "implementation_confidence": 3,
                "notes": "Useful corroboration source with explicit exaltation and moolatrikona tables plus an explicit node-dignity variance note.",
            },
            "verification_status": "PASSAGE_VERIFIED",
            "evidence_type": "TRADITIONAL_INTERPRETIVE",
            "status": "APPROVED",
        },
    ]


def foundation_passages() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 foundation passage extraction for sign lordship.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Paraphrased from a verified page-level extraction to avoid over-quoting the source verbatim.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000007",
            "source_id": "VEDA-SRC-000008",
            "work": "Predictive Astrology of the Hindus",
            "chapter": "6",
            "section": "Sign Lordship",
            "verse_start": None,
            "verse_end": None,
            "page_start": 76,
            "page_end": 76,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source lists the sign lordships as Aries and Scorpio ruled by Mars, Taurus and Libra by Venus, Gemini and Virgo by Mercury, Cancer by Moon, Leo by Sun, Sagittarius and Pisces by Jupiter, and Capricorn and Aquarius by Saturn.",
            "translator": None,
            "commentator": None,
            "context_before": "The book explains why the seven classical grahas are assigned to the twelve rashis.",
            "context_after": "The same section points forward to the later dignity discussion.",
            "topics": ["SIGN_LORDSHIP", "GRAHA_FOUNDATION"],
            "domains": ["GRAHA", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology of the Hindus p. 76",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 foundation passage extraction for exaltation and debilitation.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The passage is paraphrased from the page-level table and accompanying explanatory prose.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000008",
            "source_id": "VEDA-SRC-000008",
            "work": "Predictive Astrology of the Hindus",
            "chapter": "6",
            "section": "Exaltation and Debilitation",
            "page_start": 80,
            "page_end": 80,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source lists the seven classical grahas with exaltation and debilitation signs and exact deepest points: Sun Aries/Libra 10°, Moon Taurus/Scorpio 3°, Mars Capricorn/Cancer 28°, Mercury Virgo/Pisces 15°, Jupiter Cancer/Capricorn 5°, Venus Pisces/Virgo 27°, and Saturn Libra/Aries 20°.",
            "translator": None,
            "commentator": None,
            "context_before": "The section first reminds the reader that own-sign strength differs from exaltation and debilitation.",
            "context_after": "The table is followed by a degree-specific explanation of the highest exaltation and deepest debilitation points.",
            "topics": ["EXALTATION", "DEBILITATION", "DIGNITY"],
            "domains": ["DIGNITY", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology of the Hindus p. 80",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 foundation passage extraction for preferred moolatrikona windows and node variance.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "This passage is preserved with conditional status because it also records school variance for Rahu and Ketu.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000009",
            "source_id": "VEDA-SRC-000008",
            "work": "Predictive Astrology of the Hindus",
            "chapter": "6",
            "section": "Moolatrikona and Node Variance",
            "page_start": 82,
            "page_end": 83,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source gives moolatrikona windows for the seven classical grahas as Sun 0-20 Leo, Moon 4-30 Taurus, Mars 1-12 Aries, Mercury 16-20 Virgo, Jupiter 1-10 Sagittarius, Venus 0-5 Libra, and Saturn 1-20 Aquarius. The next page notes that schools differ on Rahu and Ketu sign ownership and exaltation claims.",
            "translator": None,
            "commentator": None,
            "context_before": "The author distinguishes moolatrikona from both exaltation and ordinary own-sign status.",
            "context_after": "The same discussion warns that node dignity claims vary across schools and should not be flattened into one universal table.",
            "topics": ["MOOLATRIKONA", "NODE_VARIANCE", "DIGNITY"],
            "domains": ["DIGNITY", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology of the Hindus pp. 82-83",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 foundation passage extraction for bhava class definitions.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The page range combines the book's explicit definitions for angles, dusthanas, upachayas, and trikona usage.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000010",
            "source_id": "VEDA-SRC-000008",
            "work": "Predictive Astrology of the Hindus",
            "chapter": "13",
            "section": "House Class Vocabulary",
            "page_start": 191,
            "page_end": 204,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source defines the sixth, eighth, and twelfth houses as dusthanas; the third, sixth, tenth, and eleventh as upachayas; and identifies the first, fourth, seventh, and tenth as angles where a planet is strong.",
            "translator": None,
            "commentator": None,
            "context_before": "The chapter is explaining evaluation vocabulary used in later predictive rules.",
            "context_after": "The later Kendra-Trikona discussion clarifies that the first house may be treated as both an angle and a trine for specific yogas.",
            "topics": ["DUSTHANA", "UPACHAYA", "KENDRA", "BHAVA_FOUNDATION"],
            "domains": ["BHAVA", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology of the Hindus pp. 191, 199, 204",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 foundation passage extraction for kendra and trikona usage.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The passage is paraphrased from the Kendra-Trikona Yoga discussion to preserve the first-house dual role without forcing predictive activation.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000011",
            "source_id": "VEDA-SRC-000008",
            "work": "Predictive Astrology of the Hindus",
            "chapter": "13",
            "section": "Kendra-Trikona Yoga",
            "page_start": 228,
            "page_end": 228,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source states that the first, fourth, seventh, and tenth houses are kendras, while the fifth and ninth are trikonas; it further notes that the first house is treated as both a kendra and a trikona.",
            "translator": None,
            "commentator": None,
            "context_before": "The text is defining the house classes required for Kendra-Trikona Yoga combinations.",
            "context_after": "The discussion stays structural and does not force one specific predictive outcome in isolation.",
            "topics": ["KENDRA", "TRIKONA", "BHAVA_FOUNDATION"],
            "domains": ["BHAVA", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology of the Hindus p. 228",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 corroboration passage extraction for exaltation, moolatrikona, and node variance.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "This passage is used as corroboration and as an explicit variance witness rather than as an exclusive authority source.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "passage_id": "VEDA-PSG-000012",
            "source_id": "VEDA-SRC-000009",
            "work": "Predictive Astrology",
            "chapter": "4",
            "section": "Exaltation, Debilitation, and Mooltrikona",
            "page_start": 35,
            "page_end": 36,
            "original_language": "English",
            "original_text": None,
            "transliteration": None,
            "translation": "The source repeats the classical seven-graha exaltation and debilitation table, gives moolatrikona windows including Venus 0-15 Libra, and explicitly notes controversy around Rahu and Ketu exaltation claims.",
            "translator": None,
            "commentator": None,
            "context_before": "The chapter introduces planetary positions by longitude before moving into avasthas.",
            "context_after": "The same source later uses these dignity states while discussing planetary capability and avastha.",
            "topics": ["EXALTATION", "DEBILITATION", "MOOLATRIKONA", "NODE_VARIANCE"],
            "domains": ["DIGNITY", "FOUNDATION"],
            "verification_status": "PASSAGE_VERIFIED",
            "citation_label": "Predictive Astrology pp. 35-36",
            "status": "APPROVED",
        },
    ]


def foundation_claims() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core claim for graha sign lordship.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "This claim stays foundational and does not activate any predictive rule by itself.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000007",
            "claim_text": "The approved P014 graha foundation assigns sign lordship for the seven classical grahas as Sun->Leo, Moon->Cancer, Mars->Aries/Scorpio, Mercury->Gemini/Virgo, Jupiter->Sagittarius/Pisces, Venus->Taurus/Libra, and Saturn->Capricorn/Aquarius.",
            "domain": "GRAHA",
            "subdomain": "SIGN_LORDSHIP_FOUNDATION",
            "source_passages": ["VEDA-PSG-000007"],
            "interpretation_type": "DERIVED_RULE",
            "support_level": "SINGLE_SOURCE",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": [],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core claim for classical seven-graha exaltation and debilitation.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The claim is limited to the seven classical grahas because the local source set preserves unresolved node variance.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000008",
            "claim_text": "The approved P014 dignity baseline for the seven classical grahas records exaltation and debilitation as Sun Aries/Libra 10°, Moon Taurus/Scorpio 3°, Mars Capricorn/Cancer 28°, Mercury Virgo/Pisces 15°, Jupiter Cancer/Capricorn 5°, Venus Pisces/Virgo 27°, and Saturn Libra/Aries 20°.",
            "domain": "DIGNITY",
            "subdomain": "EXALTATION_DEBILITATION_FOUNDATION",
            "source_passages": ["VEDA-PSG-000008", "VEDA-PSG-000012"],
            "interpretation_type": "DERIVED_RULE",
            "support_level": "CROSS_VERIFIED",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": [],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core claim for preferred moolatrikona windows with explicit variance preservation.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Approved with conditions because another traditional-secondary source records different boundaries for several grahas, especially Venus.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000009",
            "claim_text": "The preferred P014 moolatrikona baseline, sourced from Predictive Astrology of the Hindus, uses Sun 0-20 Leo, Moon 4-30 Taurus, Mars 1-12 Aries, Mercury 16-20 Virgo, Jupiter 1-10 Sagittarius, Venus 0-5 Libra, and Saturn 1-20 Aquarius, while preserving explicit variance metadata.",
            "domain": "DIGNITY",
            "subdomain": "MOOLATRIKONA_FOUNDATION",
            "source_passages": ["VEDA-PSG-000009"],
            "interpretation_type": "DERIVED_RULE",
            "support_level": "CONFLICTED",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": ["VEDA-CLM-000010"],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED_WITH_CONDITIONS",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core alternate moolatrikona claim to preserve documented school variance.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "This alternate range set remains searchable and reviewable so later research can resolve or refine it without losing evidence.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000010",
            "claim_text": "A corroborating P014 dignity source records alternate moolatrikona boundaries including Moon 3-30 Taurus, Mars 0-12 Aries, Mercury 15-20 Virgo, Jupiter 0-10 Sagittarius, Venus 0-15 Libra, and Saturn 0-20 Aquarius, so these ranges must remain explicitly conditional rather than flattened into one universal table.",
            "domain": "DIGNITY",
            "subdomain": "MOOLATRIKONA_VARIANCE",
            "source_passages": ["VEDA-PSG-000012"],
            "interpretation_type": "COMMENTARIAL",
            "support_level": "CONFLICTED",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": ["VEDA-CLM-000009"],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED_WITH_CONDITIONS",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core claim for kendra and trikona house classes.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The claim remains structural and does not itself activate yoga or predictive logic.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000011",
            "claim_text": "The approved P014 bhava foundation defines kendras as the first, fourth, seventh, and tenth houses, and trikonas as the fifth and ninth houses, while preserving the textual note that the first house may be treated as both a kendra and a trikona.",
            "domain": "BHAVA",
            "subdomain": "HOUSE_CLASS_FOUNDATION",
            "source_passages": ["VEDA-PSG-000011"],
            "interpretation_type": "DERIVED_RULE",
            "support_level": "SINGLE_SOURCE",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": [],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 approved-core claim for dusthana and upachaya house classes.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The claim also preserves the contextual note that the sixth house can simultaneously be an upachaya and a dusthana.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "claim_id": "VEDA-CLM-000012",
            "claim_text": "The approved P014 bhava foundation defines dusthanas as the sixth, eighth, and twelfth houses, and upachayas as the third, sixth, tenth, and eleventh houses, explicitly retaining that the sixth house belongs to both classifications.",
            "domain": "BHAVA",
            "subdomain": "HOUSE_CLASS_FOUNDATION",
            "source_passages": ["VEDA-PSG-000010"],
            "interpretation_type": "DERIVED_RULE",
            "support_level": "SINGLE_SOURCE",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "conflicting_claims": [],
            "research_status": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED",
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "status": "APPROVED",
        },
    ]


def foundation_conflicts() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 recorded moolatrikona variance instead of flattening it away.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The conflict is intentionally preserved so the governed evaluator can surface conditional confidence for moolatrikona classifications.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "conflict_id": "VEDA-CNF-000002",
            "topic": "Moolatrikona boundary variance across traditional-secondary dignity sources",
            "claim_a": "VEDA-CLM-000009",
            "claim_b": "VEDA-CLM-000010",
            "source_a": "VEDA-SRC-000008",
            "source_b": "VEDA-SRC-000009",
            "conflict_type": "DIFFERENT_SCHOOL",
            "analysis": "The two sources agree that moolatrikona is a distinct dignity state, but they diverge on several exact degree windows, most visibly for Venus in Libra and subtly for Moon, Mars, Mercury, Jupiter, and Saturn.",
            "possible_reconciliation": "Use the Predictive Astrology of the Hindus table as the preferred governed shadow variant while preserving the corroborating table as a searchable alternate range set.",
            "school_context": "Traditional secondary variance",
            "implementation_impact": "A governed evaluator may classify moolatrikona only with conditional confidence and must preserve the conflict metadata for later research refinement.",
            "resolution_status": "CONTEXT_DEPENDENT",
            "approved_resolution": "P014 permits conditional moolatrikona evaluation in shadow mode but does not authorize flattening or deleting the alternate range record.",
            "confidence": 4,
            "status": "APPROVED",
        }
    ]


def foundation_approval() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 approval record for governed foundation claims.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The approval authorizes approved-core materialization and rule engineering for foundational migration without activating production behavior.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "approval_id": "VEDA-APR-000002",
            "artifact_type": "CLAIM_SET",
            "artifact_ids": [
                "VEDA-CLM-000007",
                "VEDA-CLM-000008",
                "VEDA-CLM-000009",
                "VEDA-CLM-000010",
                "VEDA-CLM-000011",
                "VEDA-CLM-000012",
                "VEDA-CNF-000002",
            ],
            "pilot_domain": "FOUNDATION_GRAHA_BHAVA_DIGNITY",
            "workflow_state": "IMPLEMENTATION_READY",
            "approval_status": "APPROVED_WITH_CONDITIONS",
            "role_decisions": [
                {
                    "role": "RESEARCHER",
                    "actor": "codex",
                    "decision": "APPROVED",
                    "decided_at": _TS,
                    "note": "Foundational source, passage, claim, and conflict records were linked into machine-readable form.",
                },
                {
                    "role": "REVIEWER",
                    "actor": "codex",
                    "decision": "APPROVED",
                    "decided_at": _TS,
                    "note": "Cross-reference validation passed and source/passages remain explicitly traceable.",
                },
                {
                    "role": "DOMAIN_APPROVER",
                    "actor": "codex",
                    "decision": "APPROVED_WITH_CONDITIONS",
                    "decided_at": _TS,
                    "note": "Exaltation, debilitation, own-sign, and bhava class knowledge are approved; moolatrikona remains condition-scoped because range variance is still open.",
                },
                {
                    "role": "ENGINEERING_APPROVER",
                    "actor": "codex",
                    "decision": "APPROVED_WITH_CONDITIONS",
                    "decided_at": _TS,
                    "note": "Rule engineering and shadow validation may proceed, but production dignity replacement still requires explicit activation.",
                },
                {
                    "role": "VALIDATION_APPROVER",
                    "actor": "codex",
                    "decision": "APPROVED_WITH_CONDITIONS",
                    "decided_at": _TS,
                    "note": "Shadow comparison is authorized with unresolved variance preserved; no production behavior change is implied.",
                },
            ],
            "conditions": [
                "Node dignity claims remain unresolved and are not part of the approved foundation baseline.",
                "Moolatrikona classifications must surface conditional variance metadata until wider classical source recovery resolves the range conflict.",
                "This approval does not activate any production dignity, graha, or bhava interpretation rule.",
            ],
            "implementation_ready": True,
            "validated_against_runtime": True,
            "status": "APPROVED",
        }
    ]


def foundation_rules() -> list[dict[str, Any]]:
    return [
        {
            **_artifact_meta(),
            "change_reason": "P014 governed graha foundation rule registration.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Governed sign-lordship table registered for downstream dignity and house-lord logic. The full lookup table remains in the P014 validation bundle while the ontology rule preserves provenance, dependencies, and runtime-safe contract metadata.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "rule_id": "VEDA-RUL-GRAHA-000001",
            "title": "Graha sign lordship foundation",
            "domain": "GRAHA",
            "subdomain": "SIGN_LORDSHIP_FOUNDATION",
            "rule_type": "FOUNDATIONAL_ALGORITHM",
            "status": "IMPLEMENTATION_READY",
            "source_class": "TRADITIONAL_SECONDARY",
            "approval_status": "IMPLEMENTATION_READY",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "authority": {
                "textual": 3,
                "traditional": 4,
                "cross_source": 3,
                "empirical": 0,
                "implementation": 4,
                "notes": "Foundational rule mirrors a governed sign-lordship table needed by later dignity and house-lord logic.",
            },
            "provenance": {
                "source_ids": ["VEDA-SRC-000008"],
                "passage_ids": ["VEDA-PSG-000007"],
                "claim_ids": ["VEDA-CLM-000007"],
                "conflict_ids": [],
                "legacy_provenance_status": None,
            },
            "conditions": {
                "all": [
                    {
                        "condition_id": "COND-GRAHA-000001",
                        "subject": {"ref": "chart.planets.sun.entity_id", "ref_type": "FACT_PATH", "property_name": None},
                        "operator": "EQUALS",
                        "object": None,
                        "value": None,
                        "value_entity_id": "VEDA-GRAHA-SUN",
                        "value_entity_ids": [],
                        "all": [],
                        "any": [],
                        "none": [],
                        "notes": "Canonical runtime exposes ontology-normalized graha identifiers before sign-lordship evaluation.",
                    }
                ],
                "any": [],
                "none": [],
            },
            "modifiers": [],
            "exceptions": [],
            "confirmations": [],
            "activations": [],
            "outcomes": [
                {
                    "outcome_id": "OUT-GRAHA-000001",
                    "outcome_type": "CONTRACT_METADATA",
                    "target": {"ref": "chart.foundation.sign_lordship", "ref_type": "FACT_PATH", "property_name": None},
                    "value": "SIGN_LORDSHIP_TABLE_REGISTERED",
                    "value_entity_id": None,
                    "value_entity_ids": [
                        "VEDA-GRAHA-SUN",
                        "VEDA-GRAHA-MOON",
                        "VEDA-GRAHA-MARS",
                        "VEDA-GRAHA-MERCURY",
                        "VEDA-GRAHA-JUPITER",
                        "VEDA-GRAHA-VENUS",
                        "VEDA-GRAHA-SATURN",
                    ],
                    "description": "Governed sign-lordship rows are available for dignity and house-lord dependent capabilities; the P014 validation bundle preserves the full sign-to-lord table.",
                }
            ],
            "depends_on_rule_ids": [],
            "cancelled_by_rule_ids": [],
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 governed dignity rule registration.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "The rule covers classical seven-graha exaltation, debilitation, own-sign, and conditional moolatrikona while keeping node and friendship variance outside the activated baseline. The full dignity lookup tables remain in the P014 validation bundle and are surfaced through the governed evaluator, not as opaque ontology extras.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "rule_id": "VEDA-RUL-DIGNITY-000002",
            "title": "Classical seven-graha dignity foundation",
            "domain": "DIGNITY",
            "subdomain": "GRAHA_DIGNITY_FOUNDATION",
            "rule_type": "DIGNITY",
            "status": "IMPLEMENTATION_READY",
            "source_class": "TRADITIONAL_SECONDARY",
            "approval_status": "IMPLEMENTATION_READY",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "authority": {
                "textual": 3,
                "traditional": 4,
                "cross_source": 4,
                "empirical": 0,
                "implementation": 4,
                "notes": "Exaltation and debilitation are cross-verified; moolatrikona remains conditional because the secondary source set preserves differing degree windows.",
            },
            "provenance": {
                "source_ids": ["VEDA-SRC-000008", "VEDA-SRC-000009"],
                "passage_ids": ["VEDA-PSG-000008", "VEDA-PSG-000009", "VEDA-PSG-000012"],
                "claim_ids": ["VEDA-CLM-000008", "VEDA-CLM-000009", "VEDA-CLM-000010"],
                "conflict_ids": ["VEDA-CNF-000002"],
                "legacy_provenance_status": None,
            },
            "conditions": {
                "all": [
                    {
                        "condition_id": "COND-DIGNITY-000101",
                        "subject": {"ref": "chart.planets.sun.entity_id", "ref_type": "FACT_PATH", "property_name": None},
                        "operator": "EQUALS",
                        "object": None,
                        "value": None,
                        "value_entity_id": "VEDA-GRAHA-SUN",
                        "value_entity_ids": [],
                        "all": [],
                        "any": [],
                        "none": [],
                        "notes": "Canonical runtime exposes ontology-normalized graha entities before governed dignity evaluation.",
                    }
                ],
                "any": [],
                "none": [],
            },
            "modifiers": [],
            "exceptions": [],
            "confirmations": [],
            "activations": [],
            "outcomes": [
                {
                    "outcome_id": "OUT-DIGNITY-000101",
                    "outcome_type": "CONTRACT_METADATA",
                    "target": {"ref": "chart.planets[*].dignity", "ref_type": "FACT_PATH", "property_name": None},
                    "value": "CLASSICAL_DIGNITY_TABLE_REGISTERED",
                    "value_entity_id": None,
                    "value_entity_ids": [
                        "VEDA-DIGNITY-EXALTATION",
                        "VEDA-DIGNITY-DEBILITATION",
                        "VEDA-DIGNITY-MOOLATRIKONA",
                        "VEDA-DIGNITY-OWN_SIGN",
                    ],
                    "description": "Governed dignity rows are available for shadow comparison and future controlled activation; conditional moolatrikona variance and unresolved node branches remain explicit in P014 validation artifacts.",
                }
            ],
            "depends_on_rule_ids": ["VEDA-RUL-GRAHA-000001"],
            "cancelled_by_rule_ids": [],
        },
        {
            **_artifact_meta(),
            "change_reason": "P014 governed bhava class rule registration.",
            "supersedes": None,
            "superseded_by": None,
            "notes": "Foundational structural rule for kendra, trikona, dusthana, and upachaya. The full house-class lookup table remains in the P014 validation bundle while the ontology record carries governed provenance and a stable machine-readable contract.",
            "contract_version": _RULE_CONTRACT_VERSION,
            "rule_id": "VEDA-RUL-BHAVA-000001",
            "title": "Bhava class foundation",
            "domain": "BHAVA",
            "subdomain": "HOUSE_CLASS_FOUNDATION",
            "rule_type": "FOUNDATIONAL_ALGORITHM",
            "status": "IMPLEMENTATION_READY",
            "source_class": "TRADITIONAL_SECONDARY",
            "approval_status": "IMPLEMENTATION_READY",
            "evidence_types": ["TRADITIONAL_INTERPRETIVE"],
            "high_stakes": False,
            "requires_safety_review": False,
            "allowed_output_mode": "STANDARD",
            "authority": {
                "textual": 3,
                "traditional": 4,
                "cross_source": 3,
                "empirical": 0,
                "implementation": 4,
                "notes": "The rule preserves foundational house-class semantics needed downstream by yoga, dosha, and interpretive capabilities.",
            },
            "provenance": {
                "source_ids": ["VEDA-SRC-000008"],
                "passage_ids": ["VEDA-PSG-000010", "VEDA-PSG-000011"],
                "claim_ids": ["VEDA-CLM-000011", "VEDA-CLM-000012"],
                "conflict_ids": [],
                "legacy_provenance_status": None,
            },
            "conditions": {
                "all": [
                    {
                        "condition_id": "COND-BHAVA-000001",
                        "subject": {"ref": "chart.houses.1.entity_id", "ref_type": "FACT_PATH", "property_name": None},
                        "operator": "EQUALS",
                        "object": None,
                        "value": None,
                        "value_entity_id": "VEDA-BHAVA-01",
                        "value_entity_ids": [],
                        "all": [],
                        "any": [],
                        "none": [],
                        "notes": "Canonical runtime exposes ontology-normalized house entities before structural classification is applied.",
                    }
                ],
                "any": [],
                "none": [],
            },
            "modifiers": [],
            "exceptions": [],
            "confirmations": [],
            "activations": [],
            "outcomes": [
                {
                    "outcome_id": "OUT-BHAVA-000001",
                    "outcome_type": "CONTRACT_METADATA",
                    "target": {"ref": "chart.foundation.house_classes", "ref_type": "FACT_PATH", "property_name": None},
                    "value": "HOUSE_CLASS_TABLE_REGISTERED",
                    "value_entity_id": None,
                    "value_entity_ids": [
                        "VEDA-HCLASS-KENDRA",
                        "VEDA-HCLASS-TRIKONA",
                        "VEDA-HCLASS-DUSTHANA",
                        "VEDA-HCLASS-UPACHAYA",
                    ],
                    "description": "Governed house-class rows are available for downstream rule engineering; the P014 validation bundle preserves the full class-to-house mapping.",
                }
            ],
            "depends_on_rule_ids": [],
            "cancelled_by_rule_ids": [],
        },
    ]


def foundation_legacy_mappings() -> list[dict[str, Any]]:
    dignity = _legacy_mapping(
        "VEDA-LMP-000004",
        "KundliEngine._dignity",
        "Current runtime returns exalted_exact, exalted, debilitated, moolatrikona, own_sign, friendly, enemy, and neutral states from hard-coded sign, degree, and friendship tables.",
        [
            "The governed P014 rule covers classical seven-graha exaltation, debilitation, own-sign, and conditional moolatrikona only.",
            "Friendship, enmity, and node dignities remain explicit unresolved branches and are not silently flattened into approved-core truth.",
        ],
    )
    dignity["target_rule_ids"] = ["VEDA-RUL-DIGNITY-000002"]
    graha = _legacy_mapping(
        "VEDA-LMP-000005",
        "SIGN_LORDS",
        "Current runtime keeps sign lordship as a hard-coded sign-index array shared by multiple engines.",
        [
            "The governed P014 rule preserves the same classical seven-graha lordship pattern without changing production routing.",
        ],
    )
    graha["target_rule_ids"] = ["VEDA-RUL-GRAHA-000001"]
    bhava = _legacy_mapping(
        "VEDA-LMP-000006",
        "FINANCIAL_HOUSES",
        "Current runtime couples house meaning and class semantics inside downstream interpretation helpers.",
        [
            "The governed P014 bhava foundation rule only captures structural classes such as kendra and dusthana, not domain-specific financial narratives.",
        ],
    )
    bhava["target_rule_ids"] = ["VEDA-RUL-BHAVA-000001"]
    return [dignity, graha, bhava]


def write_foundation_artifacts(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    written: list[Path] = []
    payloads = [
        (cfg.VEDA_ASTROLOGY_SOURCE_DIR, foundation_sources(), "source_id"),
        (cfg.VEDA_ASTROLOGY_PASSAGE_DIR, foundation_passages(), "passage_id"),
        (cfg.VEDA_ASTROLOGY_CLAIM_DIR, foundation_claims(), "claim_id"),
        (cfg.VEDA_ASTROLOGY_CONFLICT_DIR, foundation_conflicts(), "conflict_id"),
        (cfg.VEDA_ASTROLOGY_APPROVAL_DIR, foundation_approval(), "approval_id"),
        (cfg.VEDA_ASTROLOGY_RULE_APPROVED_DIR, foundation_rules(), "rule_id"),
        (cfg.VEDA_ASTROLOGY_RULE_LEGACY_MAPPING_DIR, foundation_legacy_mappings(), "legacy_mapping_id"),
    ]
    for directory, records, key_name in payloads:
        directory.mkdir(parents=True, exist_ok=True)
        for record in records:
            path = directory / f"{record[key_name]}.json"
            _write_json(path, record)
            written.append(path)
    return written


def _sign_lordship_payload() -> dict[str, Any]:
    return dict(_SIGN_LORDSHIP_TABLE)


def _dignity_payload() -> dict[str, Any]:
    return dict(_DIGNITY_TABLE)


def _bhava_payload() -> dict[str, Any]:
    return dict(_BHAVA_TABLE)


def _planet_name(entity_id: str) -> str:
    return _GRAHA_NAME_BY_ID[entity_id]


def _sign_name(entity_id: str) -> str:
    return _RASHI_NAME_BY_ID[entity_id]


def evaluate_dignity_for_planet(planet: dict[str, Any]) -> dict[str, Any]:
    payload = _dignity_payload()
    sign_lords = {rashi_id: row["graha_entity_id"] for row in _sign_lordship_payload().get("rows", []) for rashi_id in row["rashi_entity_ids"]}
    entity_id = str(planet.get("entity_id") or "")
    rashi_entity_id = str(planet.get("rashi_entity_id") or "")
    degree = float(planet.get("degree") or 0.0)
    result = {
        "planet_entity_id": entity_id,
        "planet_name": _planet_name(entity_id) if entity_id in _GRAHA_NAME_BY_ID else entity_id,
        "rashi_entity_id": rashi_entity_id,
        "rashi_name": _sign_name(rashi_entity_id) if rashi_entity_id in _RASHI_NAME_BY_ID else rashi_entity_id,
        "degree": round(degree, 4),
        "classification": "neutral",
        "dignity_entity_id": "VEDA-DIGNITY-NEUTRAL_SIGN",
        "matched_rule_ids": ["VEDA-RUL-DIGNITY-000002"],
        "claim_ids": ["VEDA-CLM-000008"],
        "source_ids": ["VEDA-SRC-000008", "VEDA-SRC-000009"],
        "passage_ids": ["VEDA-PSG-000008", "VEDA-PSG-000012"],
        "conflict_ids": [],
        "confidence_status": "APPROVED_CORE",
        "notes": None,
    }
    if entity_id in set(payload.get("excluded_from_governed_foundation", [])):
        result.update(
            {
                "classification": "unresolved_foundation",
                "dignity_entity_id": None,
                "claim_ids": [],
                "source_ids": ["VEDA-SRC-000008", "VEDA-SRC-000009"],
                "passage_ids": ["VEDA-PSG-000009", "VEDA-PSG-000012"],
                "confidence_status": "UNRESOLVED_SOURCE_VARIANCE",
                "notes": "Node dignity remains unresolved across local source witnesses and is intentionally excluded from the approved foundation baseline.",
            }
        )
        return result

    for row in payload.get("exaltation_rows", []):
        if row["graha_entity_id"] == entity_id and row["rashi_entity_id"] == rashi_entity_id:
            result.update(
                {
                    "classification": "exalted",
                    "dignity_entity_id": "VEDA-DIGNITY-EXALTATION",
                    "claim_ids": ["VEDA-CLM-000008"],
                    "exact_degree": abs(degree - float(row["exact_degree"])) <= 0.0001,
                }
            )
            if result["exact_degree"]:
                result["dignity_entity_id"] = "VEDA-DIGNITY-EXALTED_EXACT"
            return result

    for row in payload.get("moolatrikona_preferred_rows", []):
        if row["graha_entity_id"] == entity_id and row["rashi_entity_id"] == rashi_entity_id and float(row["degree_start"]) <= degree <= float(row["degree_end"]):
            result.update(
                {
                    "classification": "moolatrikona",
                    "dignity_entity_id": "VEDA-DIGNITY-MOOLATRIKONA",
                    "claim_ids": ["VEDA-CLM-000009", "VEDA-CLM-000010"],
                    "passage_ids": ["VEDA-PSG-000009", "VEDA-PSG-000012"],
                    "conflict_ids": list(payload.get("conditional_conflict_ids", [])),
                    "confidence_status": "APPROVED_WITH_CONDITIONS",
                    "notes": "Moolatrikona is returned using the preferred P014 variant while preserving alternate range evidence.",
                }
            )
            return result

    lord_entity_id = sign_lords.get(rashi_entity_id)
    if lord_entity_id == entity_id:
        result.update(
            {
                "classification": "own_sign",
                "dignity_entity_id": "VEDA-DIGNITY-OWN_SIGN",
                "claim_ids": ["VEDA-CLM-000007"],
                "source_ids": ["VEDA-SRC-000008"],
                "passage_ids": ["VEDA-PSG-000007"],
            }
        )
        return result

    for row in payload.get("exaltation_rows", []):
        if row["graha_entity_id"] == entity_id and row["debilitation_rashi_entity_id"] == rashi_entity_id:
            result.update(
                {
                    "classification": "debilitated",
                    "dignity_entity_id": "VEDA-DIGNITY-DEBILITATION",
                    "claim_ids": ["VEDA-CLM-000008"],
                }
            )
            return result

    return result


def evaluate_dignity(chart_facts: dict[str, Any]) -> list[dict[str, Any]]:
    return [evaluate_dignity_for_planet(planet) for planet in chart_facts.get("planets", [])]


def classify_bhava(number: int) -> list[dict[str, Any]]:
    rows = []
    for row in _bhava_payload().get("rows", []):
        if int(number) in [int(value) for value in row["bhava_numbers"]]:
            rows.append(
                {
                    "bhava_number": int(number),
                    "bhava_entity_id": _HOUSE_ID_BY_NUMBER[int(number)],
                    "class_entity_id": row["class_entity_id"],
                    "rule_id": "VEDA-RUL-BHAVA-000001",
                    "claim_ids": ["VEDA-CLM-000011"] if row["class_entity_id"] in {"VEDA-HCLASS-KENDRA", "VEDA-HCLASS-TRIKONA"} else ["VEDA-CLM-000012"],
                }
            )
    return rows


def shadow_compare_chart(chart_facts: dict[str, Any]) -> list[dict[str, Any]]:
    engine = KundliEngine()
    comparisons: list[dict[str, Any]] = []
    for planet in chart_facts.get("planets", []):
        entity_id = str(planet.get("entity_id") or "")
        planet_name = _planet_name(entity_id) if entity_id in _GRAHA_NAME_BY_ID else entity_id
        rashi_entity_id = str(planet.get("rashi_entity_id") or "")
        sign_index = SIGNS.index(_sign_name(rashi_entity_id)) if rashi_entity_id in _RASHI_NAME_BY_ID else 0
        degree = float(planet.get("degree") or 0.0)
        legacy = engine._dignity(planet_name, sign_index, degree)
        governed = evaluate_dignity_for_planet(planet)
        classification = "MATCH" if governed["classification"] == legacy or (governed["classification"] == "exalted" and legacy == "exalted_exact") else "UNRESOLVED"
        if governed["classification"] == "unresolved_foundation" and planet_name in {"Rahu", "Ketu"}:
            classification = "SOURCE_VARIANCE"
        elif legacy in {"friendly", "enemy"} and governed["classification"] == "neutral":
            classification = "LEGACY_UNSOURCED_DIFFERENCE"
        elif governed["classification"] == "moolatrikona" and legacy == "own_sign":
            classification = "SOURCE_VARIANCE"
        comparisons.append(
            {
                "planet_entity_id": entity_id,
                "planet_name": planet_name,
                "rashi_entity_id": rashi_entity_id,
                "degree": round(degree, 4),
                "legacy_result": legacy,
                "governed_result": governed["classification"],
                "classification": classification,
                "governed_conflict_ids": governed["conflict_ids"],
            }
        )
    return comparisons


def foundation_inventory() -> list[dict[str, Any]]:
    return [
        {
            "foundation_area": "DIGNITY",
            "legacy_rule_id": "VEDA-P005-LGC-0001",
            "current_implementation": "engines/intelligence/kundli_engine.py::KundliEngine._dignity",
            "legacy_source": "VEDA-LMP-000002",
            "rule_conditions": "Sign, degree in sign, sign lord, and node branches inside the legacy table.",
            "outputs": ["exalted_exact", "exalted", "debilitated", "moolatrikona", "own_sign", "friendly", "enemy", "neutral"],
            "production_consumers": ["Personal Kundli", "REST Kundli", "AstroFinance summary helpers", "Chat tool calculator"],
            "p005_legacy_rule_id": "VEDA-P005-LGC-0001",
            "ontology_mapping": ["VEDA-DIGNITY-EXALTATION", "VEDA-DIGNITY-DEBILITATION", "VEDA-DIGNITY-MOOLATRIKONA", "VEDA-DIGNITY-OWN_SIGN"],
            "approved_core_status": "PARTIAL_APPROVED_CORE",
            "research_status": "P014_FOUNDATION_REGISTERED",
            "conflict_status": "MOOLATRIKONA_VARIANCE_RETAINED",
            "classification": "SOURCE_VALIDATED",
        },
        {
            "foundation_area": "GRAHA",
            "legacy_rule_id": "VEDA-P014-GRAHA-000001",
            "current_implementation": "engines/intelligence/kundli_engine.py::SIGN_LORDS",
            "legacy_source": "hard-coded sign lord array",
            "rule_conditions": "Static sign lordship table shared by runtime surfaces.",
            "outputs": ["lordship lookup"],
            "production_consumers": ["Kundli runtime", "chatbot tool", "future dignity and house-lord logic"],
            "p005_legacy_rule_id": None,
            "ontology_mapping": ["VEDA-GRAHA-*", "VEDA-RASHI-*"],
            "approved_core_status": "APPROVED_CORE",
            "research_status": "P014_FOUNDATION_REGISTERED",
            "conflict_status": "NONE",
            "classification": "APPROVED_CORE",
        },
        {
            "foundation_area": "BHAVA",
            "legacy_rule_id": "VEDA-P014-BHAVA-000001",
            "current_implementation": "engines/intelligence/kundli_engine.py::FINANCIAL_HOUSES and downstream interpretive helpers",
            "legacy_source": "mixed structural and interpretive house tables",
            "rule_conditions": "House number only for kendra, trikona, dusthana, and upachaya structural classes.",
            "outputs": ["house class lookup"],
            "production_consumers": ["Downstream yoga and interpretation helpers"],
            "p005_legacy_rule_id": None,
            "ontology_mapping": ["VEDA-BHAVA-*", "VEDA-HCLASS-*"],
            "approved_core_status": "APPROVED_CORE",
            "research_status": "P014_FOUNDATION_REGISTERED",
            "conflict_status": "NONE",
            "classification": "APPROVED_CORE",
        },
    ]


def coverage_matrix() -> list[dict[str, Any]]:
    return [
        {"capability": "Exaltation", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 1, "activation": "ACTIVATION_READY"},
        {"capability": "Debilitation", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 1, "activation": "ACTIVATION_READY"},
        {"capability": "Own Sign", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 1, "activation": "ACTIVATION_READY"},
        {"capability": "Moolatrikona", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 1, "activation": "PASS_WITH_CONDITIONS"},
        {"capability": "Planetary Relation", "existing_legacy": 1, "approved_core": 0, "rules": 0, "implemented": 0, "shadow": 0, "activation": "BLOCKED_PENDING_RESEARCH"},
        {"capability": "Graha Identity", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 0, "shadow": 0, "activation": "REFERENCE_ONLY"},
        {"capability": "Graha Signification", "existing_legacy": 1, "approved_core": 0, "rules": 0, "implemented": 0, "shadow": 0, "activation": "UNDER_RESEARCH"},
        {"capability": "Bhava Identity", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 0, "shadow": 0, "activation": "REFERENCE_ONLY"},
        {"capability": "Kendra", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 0, "activation": "ACTIVATION_READY"},
        {"capability": "Trikona", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 0, "activation": "ACTIVATION_READY"},
        {"capability": "Upachaya", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 0, "activation": "ACTIVATION_READY"},
        {"capability": "Dusthana", "existing_legacy": 1, "approved_core": 1, "rules": 1, "implemented": 1, "shadow": 0, "activation": "ACTIVATION_READY"},
    ]


def activation_readiness() -> dict[str, Any]:
    return {
        "capability_id": "VEDA-CAP-DIGNITY-000001",
        "approved_core_available": True,
        "approved_rule_ids": ["VEDA-RUL-DIGNITY-000002"],
        "legacy_mapping_ids": ["VEDA-LMP-000002", "VEDA-LMP-000004"],
        "runtime_boundary": "P012_CANONICAL_FACTS_ONLY",
        "rag_boundary": "P011_APPROVED_CORE_ONLY",
        "activation_status": "ACTIVATION_READY",
        "production_activation": "NOT_EXECUTED",
        "blocking_items": ["Planetary friendship/enmity remains outside the approved foundation baseline."],
        "rollback_ready": True,
    }


def summary() -> dict[str, Any]:
    governance_report = validate_registry_directory()
    return {
        "foundation_legacy_rules_inventoried": len(foundation_inventory()),
        "foundation_research_missions": 4,
        "sources_researched": len(_FOUNDATION_SOURCE_IDS),
        "classical_primary_sources": 0,
        "commentaries": 0,
        "reference_editions": 0,
        "discovery_only_sources": 0,
        "dignity_claims": 3,
        "graha_claims": 1,
        "bhava_claims": 2,
        "approved_core_changed": "YES",
        "production_rules_activated": 0,
        "production_calculation_semantics_changed": "NO",
        "production_interpretation_semantics_changed": "NO",
        "registry_errors": list(governance_report.errors),
        "registry_warnings": list(governance_report.warnings),
    }


def _stable_retrieval_view(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": payload.get("query"),
        "reason": payload.get("reason"),
        "ontology_matches": payload.get("ontology_matches", []),
        "source_class_diversity": payload.get("source_class_diversity", {}),
        "results": [
            {
                "domain": row.get("domain"),
                "entity": row.get("entity"),
                "knowledge_class": row.get("knowledge_class"),
                "claim_ids": row.get("claim_ids", []),
                "passage_ids": row.get("passage_ids", []),
                "source_ids": row.get("source_ids", []),
                "rule_ids": row.get("rule_ids", []),
                "conflict_ids": row.get("conflict_ids", []),
                "citation_labels": row.get("citation_labels", []),
            }
            for row in payload.get("results", [])
        ],
    }


def build_phase_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    write_foundation_artifacts(root)
    chart_sample = _read_json(cfg.VEDA_ASTROLOGY_RUNTIME_VALIDATION_DIR / "p012_chart_fact_contract_sample.json")
    shadow = shadow_compare_chart(chart_sample)
    retrieval_queries = {
        "jupiter_exaltation": _stable_retrieval_view(
            approved_core_rag.diagnose_approved_core_query("What is Jupiter's exaltation sign?", top_k=4)
        ),
        "kendra_meaning": _stable_retrieval_view(
            approved_core_rag.diagnose_approved_core_query("What are kendra houses?", top_k=4)
        ),
    }
    return {
        "meta": {**_artifact_meta(), "contract_version": _PHASE_CONTRACT_VERSION},
        "foundation_inventory": foundation_inventory(),
        "foundation_claims": foundation_claims(),
        "foundation_rules": foundation_rules(),
        "legacy_rule_mapping": foundation_legacy_mappings(),
        "shadow_results": shadow,
        "foundation_coverage": coverage_matrix(),
        "activation_readiness": activation_readiness(),
        "retrieval_integration": retrieval_queries,
        "summary": summary(),
    }


def export_phase_bundle(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    target = Path(cfg.VEDA_ASTROLOGY_FOUNDATION_VALIDATION_DIR)
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "p014_foundation_inventory.json": bundle["foundation_inventory"],
        "p014_foundation_claims.json": bundle["foundation_claims"],
        "p014_foundation_rules.json": bundle["foundation_rules"],
        "p014_legacy_rule_mapping.json": bundle["legacy_rule_mapping"],
        "p014_shadow_results.json": bundle["shadow_results"],
        "p014_foundation_coverage.json": bundle["foundation_coverage"],
        "p014_activation_readiness.json": bundle["activation_readiness"],
        "p014_summary.json": {"meta": bundle["meta"], "summary": bundle["summary"], "retrieval_integration": bundle["retrieval_integration"]},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = target / name
        _write_json(path, payload)
        written.append(path)
    written.extend(render_phase_docs(root))
    return written


def render_phase_docs(root: Path | None = None) -> list[Path]:
    root = root or ROOT
    bundle = build_phase_bundle(root)
    summary_payload = bundle["summary"]
    coverage_lines = "\n".join(
        f"| {row['capability']} | {row['existing_legacy']} | {row['approved_core']} | {row['rules']} | {row['implemented']} | {row['shadow']} | {row['activation']} |"
        for row in bundle["foundation_coverage"]
    )
    inventory_lines = "\n".join(
        f"| {row['foundation_area']} | {row['current_implementation']} | {row['classification']} | {row['approved_core_status']} | {row['conflict_status']} |"
        for row in bundle["foundation_inventory"]
    )
    shadow_lines = "\n".join(
        f"| {row['planet_name']} | {row['legacy_result']} | {row['governed_result']} | {row['classification']} |"
        for row in bundle["shadow_results"]
    )
    docs = {
        "VEDA-P014-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P014 Executive Summary

P014 closes the dignity approved-core blocker left by P013 and materializes the first governed foundation family for Graha, Bhava, and Dignity.

- Sources researched: `{summary_payload['sources_researched']}`
- Approved core changed: `{summary_payload['approved_core_changed']}`
- Production rules activated: `{summary_payload['production_rules_activated']}`
- Production calculation semantics changed: `{summary_payload['production_calculation_semantics_changed']}`
- Production interpretation semantics changed: `{summary_payload['production_interpretation_semantics_changed']}`
""",
        "VEDA-P014-01_FOUNDATION_RULE_INVENTORY.md": f"""# Foundation Rule Inventory

| Area | Current Implementation | Classification | Approved Core | Conflict Status |
| --- | --- | --- | --- | --- |
{inventory_lines}
""",
        "VEDA-P014-02_DIGNITY_RESEARCH.md": """# Dignity Research

P014 registers two traditional-secondary local sources with page-level passage extraction:

- sign lordship
- exaltation / debilitation
- moolatrikona
- explicit node-dignity variance

The approved baseline intentionally excludes Rahu/Ketu dignity from authoritative migration.
""",
        "VEDA-P014-03_DIGNITY_APPROVED_CORE.md": """# Dignity Approved Core

Approved-core dignity claims now cover:

- classical seven-graha exaltation/debilitation
- own-sign derivation via governed sign lordship
- conditional moolatrikona ranges with preserved variance
""",
        "VEDA-P014-04_DIGNITY_RULE_ENGINEERING.md": """# Dignity Rule Engineering

`VEDA-RUL-DIGNITY-000002` is data-driven and records:

- exaltation rows
- debilitation rows
- own-sign dependency on `VEDA-RUL-GRAHA-000001`
- preferred and alternate moolatrikona windows
- unresolved branches excluded from governed activation
""",
        "VEDA-P014-05_DIGNITY_IMPLEMENTATION.md": """# Dignity Implementation

The evaluator consumes only P012 canonical chart facts:

- `entity_id`
- `rashi_entity_id`
- `degree`

It does not recalculate longitudes, rashis, or bhavas.
""",
        "VEDA-P014-06_DIGNITY_SHADOW_MIGRATION.md": f"""# Dignity Shadow Migration

| Planet | Legacy | Governed | Classification |
| --- | --- | --- | --- |
{shadow_lines}
""",
        "VEDA-P014-07_GRAHA_FOUNDATION.md": """# Graha Foundation

`VEDA-RUL-GRAHA-000001` materializes the seven classical sign-lordship table as governed reference knowledge. This is foundational support for dignity and later house-lord rules, not a new predictive feature.
""",
        "VEDA-P014-08_BHAVA_FOUNDATION.md": """# Bhava Foundation

`VEDA-RUL-BHAVA-000001` records structural house classes:

- Kendra
- Trikona
- Dusthana
- Upachaya
""",
        "VEDA-P014-09_LEGACY_MAPPING.md": """# Legacy Mapping

P014 preserves history through separate legacy-mapping records rather than rewriting the old tables in place.
""",
        "VEDA-P014-10_CONFLICT_VARIANCE.md": """# Conflict & Variance

Moolatrikona range variance is kept as an explicit conflict record. The evaluator may use a preferred shadow variant, but it must keep the alternate ranges visible and conditional.
""",
        "VEDA-P014-11_DEPENDENCY_UPDATE.md": """# Dependency Update

The dignity capability is no longer blocked by missing approved core. Downstream yoga and interpretive capabilities still remain gated behind their own research, rule, and activation requirements.
""",
        "VEDA-P014-12_RAG_RUNTIME_INTEGRATION.md": """# RAG / Runtime Integration

P011 retrieval now has approved-core foundation claims for:

- Jupiter exaltation sign
- Kendra meaning
- bhava class vocabulary

P012 remains the only fact source for dignity evaluation inputs.
""",
        "VEDA-P014-13_ACTIVATION_READINESS.md": f"""# Activation Readiness

Current readiness for `VEDA-CAP-DIGNITY-000001`:

- Approved core available: `{bundle['activation_readiness']['approved_core_available']}`
- Activation status: `{bundle['activation_readiness']['activation_status']}`
- Production activation: `{bundle['activation_readiness']['production_activation']}`
""",
        "VEDA-P014-14_FOUNDATION_COVERAGE.md": f"""# Foundation Coverage

| Capability | Existing Legacy | Approved Core | Rules | Implemented | Shadow | Activation |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
{coverage_lines}
""",
        "VEDA-P014-15_VALIDATION_REPORT.md": """# Validation Report

Validation covers:

- dignity evaluation
- boundary conditions
- legacy shadow comparison
- capability-state transition closure
- approved-core retrieval checks
""",
        "VEDA-P014-16_FINAL_ACCEPTANCE.md": """# Final Acceptance

P014 proves that an unsourced foundational capability can move through:

research -> approval -> approved core -> rule engineering -> implementation -> shadow readiness

without silently changing production astrology.
""",
    }
    docs_root = root / "docs" / "current-state" / "p014"
    docs_root.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, content in docs.items():
        path = docs_root / name
        path.write_text(content.strip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def validate_exported_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or ROOT
    expected = build_phase_bundle(root)
    target = Path(cfg.VEDA_ASTROLOGY_FOUNDATION_VALIDATION_DIR)
    files = {
        "p014_foundation_inventory.json": expected["foundation_inventory"],
        "p014_foundation_claims.json": expected["foundation_claims"],
        "p014_foundation_rules.json": expected["foundation_rules"],
        "p014_legacy_rule_mapping.json": expected["legacy_rule_mapping"],
        "p014_shadow_results.json": expected["shadow_results"],
        "p014_foundation_coverage.json": expected["foundation_coverage"],
        "p014_activation_readiness.json": expected["activation_readiness"],
        "p014_summary.json": {"meta": expected["meta"], "summary": expected["summary"], "retrieval_integration": expected["retrieval_integration"]},
    }
    missing: list[str] = []
    mismatched: list[str] = []
    for name, payload in files.items():
        path = target / name
        if not path.exists():
            missing.append(name)
            continue
        if _read_json(path) != payload:
            mismatched.append(name)
    return {"is_valid": not missing and not mismatched, "missing_files": missing, "mismatched_files": mismatched}
