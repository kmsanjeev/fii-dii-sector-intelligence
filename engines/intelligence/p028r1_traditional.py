"""P028-R1 deterministic Ashtakoota foundation.

The tables are explicitly RESEARCH_CANDIDATE / REFERENCE_NOT_VERIFIED until
source promotion. They are never treated as a complete relationship verdict.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


METHOD_ID = "ASHTAKOOTA_NORTH_INDIAN_RESEARCH_CANDIDATE"
METHOD_VERSION = "1.0"
AUTHORITY = "RESEARCH_CANDIDATE"
SOURCE = "REFERENCE_NOT_VERIFIED"
MAX_TOTAL = 36

_NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadra", "Uttara Bhadra", "Revati"]
_RASHIS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]
_NAK_GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Deva", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
_NAK_YONI = ["Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant"]
_NAK_NADI = ["Adi", "Madhya", "Antya"] * 9
_VARNA = {"Cancer": 0, "Scorpio": 0, "Pisces": 0, "Aries": 1, "Leo": 1, "Sagittarius": 1, "Taurus": 2, "Virgo": 2, "Capricorn": 2, "Gemini": 3, "Libra": 3, "Aquarius": 3}
_VASHYA = {"Aries": "Quadruped", "Taurus": "Quadruped", "Gemini": "Human", "Cancer": "Water", "Leo": "Wild", "Virgo": "Human", "Libra": "Human", "Scorpio": "Insect", "Sagittarius": "Human", "Capricorn": "Quadruped", "Aquarius": "Human", "Pisces": "Water"}
_FRIEND = {"Sun": {"Sun", "Moon", "Mars", "Jupiter"}, "Moon": {"Sun", "Moon", "Mars", "Jupiter"}, "Mars": {"Sun", "Moon", "Mars", "Jupiter"}, "Mercury": {"Sun", "Venus"}, "Jupiter": {"Sun", "Moon", "Mars"}, "Venus": {"Mercury", "Saturn"}, "Saturn": {"Mercury", "Venus"}}


@dataclass(slots=True)
class KutaComponent:
    name: str
    score: int | None
    maximum: int
    state: str
    reason: str
    lineage_id: str
    source: str = SOURCE
    authority: str = AUTHORITY


@dataclass(slots=True)
class TraditionalCompatibilityResult:
    method_id: str
    method_version: str
    subject_a_id: str
    subject_b_id: str
    nakshatra_a: str
    nakshatra_b: str
    rashi_a: str
    rashi_b: str
    components: dict[str, KutaComponent]
    raw_total: int | None
    max_total: int
    warnings: list[str] = field(default_factory=list)
    mitigations: list[dict[str, Any]] = field(default_factory=list)
    source: str = SOURCE
    authority: str = AUTHORITY
    confidence: str = "LOW"
    data_quality: str = "EXACT"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["components"] = {key: asdict(item) for key, item in self.components.items()}
        return value


def _index(value: str, values: list[str]) -> int | None:
    normalized = value.strip().casefold()
    return next((i for i, item in enumerate(values) if item.casefold() == normalized), None)


def _component(name: str, score: int | None, maximum: int, reason: str, lineage: str, state: str = "CALCULATED") -> KutaComponent:
    return KutaComponent(name, score, maximum, state, reason, lineage)


def calculate_ashtakoota(*, subject_a_id: str, subject_b_id: str, nakshatra_a: str, nakshatra_b: str, rashi_a: str, rashi_b: str, data_quality: str = "EXACT") -> TraditionalCompatibilityResult:
    na, nb = _index(nakshatra_a, _NAKSHATRAS), _index(nakshatra_b, _NAKSHATRAS)
    ra, rb = _index(rashi_a, _RASHIS), _index(rashi_b, _RASHIS)
    components: dict[str, KutaComponent] = {}
    if None in {na, nb, ra, rb}:
        return TraditionalCompatibilityResult(METHOD_ID, METHOD_VERSION, subject_a_id, subject_b_id, nakshatra_a, nakshatra_b, rashi_a, rashi_b, {name: _component(name, None, maximum, "Input not recognized", name, "INSUFFICIENT_DATA") for name, maximum in {"VARNA": 1, "VASHYA": 2, "TARA": 3, "YONI": 4, "GRAHA_MAITRI": 5, "GANA": 6, "BHAKOOT": 7, "NADI": 8}.items()}, None, MAX_TOTAL, ["INSUFFICIENT_DATA: use trusted calculated Moon/Nakshatra/Rashi inputs"], data_quality=data_quality)
    assert na is not None and nb is not None and ra is not None and rb is not None
    components["VARNA"] = _component("VARNA", 1 if _VARNA[_RASHIS[ra]] >= _VARNA[_RASHIS[rb]] else 0, 1, "Traditional Varna classification; not a social hierarchy", "RASHI_RELATIONSHIP")
    components["VASHYA"] = _component("VASHYA", 2 if _VASHYA[_RASHIS[ra]] == _VASHYA[_RASHIS[rb]] else 1 if "Human" in {_VASHYA[_RASHIS[ra]], _VASHYA[_RASHIS[rb]]} else 0, 2, "Governed symbolic Vashya category", "RASHI_RELATIONSHIP")
    tara_distance = (nb - na) % 27 + 1
    components["TARA"] = _component("TARA", 3 if ((tara_distance - 1) % 9) in {0, 2, 4, 6, 8} else 0, 3, f"Cyclic Nakshatra distance={tara_distance}", "NAKSHATRA_RELATIONSHIP")
    components["YONI"] = _component("YONI", 4 if _NAK_YONI[na] == _NAK_YONI[nb] else 2 if _NAK_YONI[na] != _NAK_YONI[nb] else 0, 4, "Traditional symbolic Yoni classification; not literal personality", "NAKSHATRA_RELATIONSHIP")
    la, lb = _LORDS[ra], _LORDS[rb]
    components["GRAHA_MAITRI"] = _component("GRAHA_MAITRI", 5 if la == lb else 4 if lb in _FRIEND.get(la, set()) and la in _FRIEND.get(lb, set()) else 2 if lb in _FRIEND.get(la, set()) or la in _FRIEND.get(lb, set()) else 0, 5, f"Moon-sign lords={la}/{lb}", "RASHI_RELATIONSHIP")
    components["GANA"] = _component("GANA", 6 if _NAK_GANA[na] == _NAK_GANA[nb] else 3 if "Manushya" in {_NAK_GANA[na], _NAK_GANA[nb]} else 0, 6, f"Technical Gana labels={_NAK_GANA[na]}/{_NAK_GANA[nb]}", "NAKSHATRA_RELATIONSHIP")
    sign_distance = (rb - ra) % 12 + 1
    reverse_distance = (ra - rb) % 12 + 1
    components["BHAKOOT"] = _component("BHAKOOT", 7 if sign_distance not in {2, 5, 6, 8, 9, 12} else 0, 7, f"Rashi distances={sign_distance}/{reverse_distance}; method variant requires further source validation", "RASHI_RELATIONSHIP")
    components["NADI"] = _component("NADI", 8 if _NAK_NADI[na] != _NAK_NADI[nb] else 0, 8, f"Technical Nadi labels={_NAK_NADI[na]}/{_NAK_NADI[nb]}; no fertility or health inference", "NAKSHATRA_RELATIONSHIP")
    total = sum(item.score or 0 for item in components.values())
    warnings = ["RESEARCH_CANDIDATE: tables require source promotion before Approved Core use", "Guna total is one evidence family, not a relationship guarantee", "No Manglik/Kuja mitigation is inferred"]
    if data_quality != "EXACT":
        warnings.append("SENSITIVE_INPUT: birth-data quality may change Moon/Nakshatra/Rashi")
    return TraditionalCompatibilityResult(METHOD_ID, METHOD_VERSION, subject_a_id, subject_b_id, nakshatra_a, nakshatra_b, rashi_a, rashi_b, components, total, MAX_TOTAL, warnings, data_quality=data_quality)


def traditional_evidence(result: TraditionalCompatibilityResult) -> list[dict[str, Any]]:
    return [{"evidence_id": f"P028R1-{name}", "claim": f"{name} score {component.score}/{component.maximum}", "evidence_type": "TRADITIONAL_MATCHING", "direction": "SUPPORTS" if (component.score or 0) >= component.maximum / 2 else "OPPOSES", "authority_class": result.authority, "knowledge_zone": result.authority, "lineage_id": component.lineage_id, "chart_id": None, "subject_id": None, "method_variant": result.method_id} for name, component in result.components.items()]


__all__ = ["KutaComponent", "TraditionalCompatibilityResult", "calculate_ashtakoota", "traditional_evidence", "METHOD_ID", "METHOD_VERSION"]
