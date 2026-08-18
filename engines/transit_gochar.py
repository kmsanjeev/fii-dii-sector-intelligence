"""P019 Transit / Gochar foundation.

This module provides a read-only transit comparison layer on top of the
existing Kundli runtime. It deliberately reuses the canonical Swiss Ephemeris
path from :mod:`engines.intelligence.kundli_engine` and does not introduce a
separate astronomy engine.

The scope is factual:
  - compute sidereal transit positions for a requested datetime
  - compare transit positions to natal reference points
  - expose house, sign, nakshatra and angular relationships
  - label structural timing rules such as Sade Sati and Dhaiya

Predictive synthesis remains out of scope.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from engines.common import config as cfg
from engines.common.astronomy_policy import calc_ut as governed_calc_ut
from engines.intelligence.kundli_engine import KundliEngine, NAKSHATRAS, SIGNS

TRANSIT_OUTPUT_DIR = cfg.DATA_DIR / "gochar"
TRANSIT_FOUNDATION_PATH = TRANSIT_OUTPUT_DIR / "transit_foundation.parquet"
TRANSIT_RUNTIME_VERSION = "P019"
HISTORICAL_TRANSIT_METHOD_ID = "VEDA-TRANSIT-FND-001-HISTORICAL-V1"
DEFAULT_TIMEZONE = "Asia/Kolkata"
SUPPORTED_HISTORICAL_PLANETS = ("Jupiter", "Saturn")


class TransitReferenceType(str, Enum):
    LAGNA = "LAGNA"
    MOON = "MOON"
    PLANET = "PLANET"
    CUSTOM = "CUSTOM"


class TransitValidationStatus(str, Enum):
    IMPLEMENTED_UNVALIDATED = "IMPLEMENTED_UNVALIDATED"
    RESEARCH_REQUIRED = "RESEARCH_REQUIRED"
    BLOCKED = "BLOCKED"


class TransitFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transit_time_utc: str
    transit_time_local: str
    graha: str
    longitude: float
    sign: str
    sign_num: int
    nakshatra: str
    pada: int
    retrograde: bool
    speed_deg_per_day: float
    natal_reference_type: TransitReferenceType
    natal_reference_entity: str
    natal_reference_sign: str
    natal_reference_sign_num: int
    relative_house: int
    angular_separation: float
    aspect_relation: str
    method_id: str
    validation_status: TransitValidationStatus
    runtime_version: str = TRANSIT_RUNTIME_VERSION


class TransitWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graha: str
    sign: str
    pass_number: int
    entry_utc: str
    exit_utc: str
    retrograde_pass: bool
    method_id: str
    validation_status: TransitValidationStatus


class TransitRuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    title: str
    graha: str
    reference_type: TransitReferenceType
    reference_entity: str
    matched: bool
    evaluation_status: TransitValidationStatus
    reason: str
    source_claim_ids: list[str] = Field(default_factory=list)
    matched_fact_indexes: list[int] = Field(default_factory=list)
    method_id: str


class TransitSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    entity_id: str
    location_id: str
    transit_time_utc: str
    transit_time_local: str
    timezone_name: str
    julian_day: float
    runtime_version: str = TRANSIT_RUNTIME_VERSION
    transit_chart: dict[str, dict[str, Any]]
    relationship_facts: list[TransitFact]
    rule_results: list[TransitRuleResult]
    transit_windows: list[TransitWindow]
    gochar_metrics: dict[str, Any]
    source_ephemeris_version: str = "Swiss Ephemeris (Lahiri, True Node)"


class HistoricalTransitPosition(BaseModel):
    """Factual historical transit position; interpretation remains separate."""

    model_config = ConfigDict(extra="forbid")

    transit_time_utc: str
    julian_day: float
    planet: str
    tropical_longitude: float
    ayanamsha: float
    sidereal_longitude: float
    sign_num: int
    sign: str
    retrograde: bool
    speed_deg_per_day: float
    method_id: str = HISTORICAL_TRANSIT_METHOD_ID
    method_version: str = "1.0"
    ephemeris: str = "Swiss Ephemeris"
    ayanamsha_method: str = "LAHIRI"


def _sign_num_to_name(sign_num: int) -> str:
    return SIGNS[sign_num % 12]


def _nakshatra(longitude: float) -> dict[str, Any]:
    lon = longitude % 360
    for name, start, end, lord, symbol in NAKSHATRAS:
        if start <= lon < end:
            pada = int((lon - start) / (13.333 / 4)) + 1
            return {
                "name": name,
                "lord": lord,
                "symbol": symbol,
                "pada": min(pada, 4),
            }
    return {"name": "Revati", "lord": "Mercury", "symbol": "Fish", "pada": 4}


def _aspect_relation(angle: float) -> str:
    a = angle if angle <= 180 else 360 - angle
    a = round(a, 6)
    if a < 8:
        return "conjunction"
    if 52 < a <= 68:
        return "sextile"
    if 82 < a <= 98:
        return "square"
    if 112 < a <= 128:
        return "trine"
    if 172 < a <= 188:
        return "opposition"
    return "separating"


def _smallest_angle(a: float, b: float) -> float:
    diff = abs((a - b) % 360)
    return diff if diff <= 180 else 360 - diff


def _relative_house(transit_sign_num: int, reference_sign_num: int) -> int:
    return ((transit_sign_num - reference_sign_num) % 12) + 1


def _coerce_datetime(value: datetime | None, timezone_name: str | None = None) -> tuple[datetime, datetime, str]:
    tz_name = timezone_name or DEFAULT_TIMEZONE
    tz = ZoneInfo(tz_name)
    if value is None:
        local = datetime.now(tz)
    elif value.tzinfo is None:
        local = value.replace(tzinfo=tz)
    else:
        local = value.astimezone(tz)
    return local.astimezone(timezone.utc), local, tz_name


class TransitGocharEngine:
    """Read-only transit comparison engine using the existing Kundli core."""

    def __init__(self) -> None:
        self._kundli = KundliEngine()
        self._historical_cache: dict[tuple[str, str, str], HistoricalTransitPosition] = {}

    def _jd(self, dt_utc: datetime) -> float:
        return self._kundli._swe.julday(  # noqa: SLF001 - reuse canonical astronomy core
            dt_utc.year,
            dt_utc.month,
            dt_utc.day,
            dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3_600_000_000.0,
        )

    def _planet_positions(self, dt_utc: datetime) -> dict[str, dict[str, Any]]:
        jd = self._jd(dt_utc)
        return self._kundli._planet_positions_extended(jd)  # noqa: SLF001 - read-only runtime reuse

    def calculate_transit(
        self,
        timestamp: datetime,
        planet: str,
        configuration: dict[str, Any] | None = None,
    ) -> HistoricalTransitPosition:
        """Calculate one deterministic historical Jupiter/Saturn position.

        This is a factual research API. It intentionally does not select a
        natal target, infer an event, or apply a predictive transit rule.
        """
        if planet not in SUPPORTED_HISTORICAL_PLANETS:
            raise ValueError(f"historical foundation supports only {SUPPORTED_HISTORICAL_PLANETS}")
        dt_utc, _, _ = _coerce_datetime(timestamp, "UTC")
        config = configuration or {}
        config_key = json.dumps(config, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        key = (dt_utc.isoformat(), planet, config_key)
        cached = self._historical_cache.get(key)
        if cached is not None:
            return cached
        jd = self._jd(dt_utc)
        pid = self._kundli._PLANET_IDS[planet]  # noqa: SLF001 - canonical engine IDs
        sidereal_flags = self._kundli._swe.FLG_SIDEREAL | self._kundli._swe.FLG_SPEED  # noqa: SLF001
        sidereal, _ = governed_calc_ut(self._kundli._swe, jd, pid, sidereal_flags)  # noqa: SLF001
        flags = self._kundli._swe.FLG_SPEED  # noqa: SLF001 - tropical reference only
        tropical, _ = governed_calc_ut(self._kundli._swe, jd, pid, flags)  # noqa: SLF001
        ayanamsha = float(self._kundli._swe.get_ayanamsa_ut(jd))  # noqa: SLF001
        position = HistoricalTransitPosition(
            transit_time_utc=dt_utc.isoformat().replace("+00:00", "Z"),
            julian_day=round(jd, 8),
            planet=planet,
            tropical_longitude=round(float(tropical[0]) % 360.0, 8),
            ayanamsha=round(ayanamsha, 8),
            sidereal_longitude=round(float(sidereal[0]) % 360.0, 8),
            sign_num=int(float(sidereal[0]) // 30) % 12,
            sign=_sign_num_to_name(int(float(sidereal[0]) // 30)),
            retrograde=bool(sidereal[3] < 0),
            speed_deg_per_day=round(float(sidereal[3]), 8),
        )
        self._historical_cache[key] = position
        return position

    def _chart_entity_id(self, natal_chart: dict[str, Any]) -> str:
        entity = natal_chart.get("entity") or {}
        return str(entity.get("symbol") or entity.get("name") or entity.get("type") or "UNKNOWN")

    def _reference_signs(self, natal_chart: dict[str, Any], reference_type: TransitReferenceType, reference_entity: str) -> tuple[int, str, float]:
        if reference_type == TransitReferenceType.LAGNA:
            lagna = natal_chart.get("lagna") or {}
            return int(lagna.get("sign_num", 0)), str(lagna.get("sign", "Aries")), float(lagna.get("full_longitude", 0.0))
        if reference_type == TransitReferenceType.MOON:
            moon = (natal_chart.get("planets") or {}).get("Moon") or {}
            return int(moon.get("sign_num", 0)), str(moon.get("sign", "Aries")), float(moon.get("longitude", 0.0))
        planet = (natal_chart.get("planets") or {}).get(reference_entity) or {}
        return int(planet.get("sign_num", 0)), str(planet.get("sign", "Aries")), float(planet.get("longitude", 0.0))

    def build_snapshot(
        self,
        natal_chart: dict[str, Any],
        transit_time: datetime | None = None,
        timezone_name: str | None = None,
        reference_bases: Iterable[TransitReferenceType] | None = None,
    ) -> TransitSnapshot:
        dt_utc, dt_local, tz_name = _coerce_datetime(transit_time, timezone_name)
        jd = self._jd(dt_utc)
        positions = self._planet_positions(dt_utc)
        references = list(reference_bases or (TransitReferenceType.LAGNA, TransitReferenceType.MOON))

        relationship_facts: list[TransitFact] = []
        for reference_type in references:
            reference_entity = "Lagna" if reference_type == TransitReferenceType.LAGNA else "Moon"
            if reference_type == TransitReferenceType.PLANET:
                raise ValueError("PLANET reference requires explicit reference_entity selection")

            reference_sign_num, reference_sign, reference_longitude = self._reference_signs(natal_chart, reference_type, reference_entity)
            for graha, fact in positions.items():
                transit_sign_num = int(fact["longitude"] / 30)
                transit_sign = _sign_num_to_name(transit_sign_num)
                angle = _smallest_angle(float(fact["longitude"]), reference_longitude)
                natal_sign_num = reference_sign_num
                relative_house = _relative_house(transit_sign_num, natal_sign_num)
                relationship_facts.append(
                    TransitFact(
                        transit_time_utc=dt_utc.isoformat().replace("+00:00", "Z"),
                        transit_time_local=dt_local.isoformat(),
                        graha=graha,
                        longitude=round(float(fact["longitude"]), 4),
                        sign=transit_sign,
                        sign_num=transit_sign_num,
                        nakshatra=_nakshatra(float(fact["longitude"]))["name"],
                        pada=int(_nakshatra(float(fact["longitude"]))["pada"]),
                        retrograde=bool(fact["retrograde"]),
                        speed_deg_per_day=round(float(fact["longitude_speed_deg_per_day"]), 6),
                        natal_reference_type=reference_type,
                        natal_reference_entity=reference_entity,
                        natal_reference_sign=reference_sign,
                        natal_reference_sign_num=natal_sign_num,
                        relative_house=relative_house,
                        angular_separation=round(angle, 4),
                        aspect_relation=_aspect_relation(angle),
                        method_id="P019-GOCHAR-FACT-001",
                        validation_status=TransitValidationStatus.IMPLEMENTED_UNVALIDATED,
                    )
                )

        windows = self._compute_windows(dt_utc, positions, ("Saturn", "Jupiter", "Rahu", "Ketu"))
        rules = self._evaluate_rules(relationship_facts)
        gochar_metrics = self._summarize_metrics(relationship_facts, rules, windows)

        return TransitSnapshot(
            entity_id=self._chart_entity_id(natal_chart),
            location_id="LAGNA+MOON",
            transit_time_utc=dt_utc.isoformat().replace("+00:00", "Z"),
            transit_time_local=dt_local.isoformat(),
            timezone_name=tz_name,
            julian_day=round(jd, 6),
            transit_chart={name: self._serialize_position(name, fact) for name, fact in positions.items()},
            relationship_facts=relationship_facts,
            rule_results=rules,
            transit_windows=windows,
            gochar_metrics=gochar_metrics,
        )

    def _serialize_position(self, graha: str, fact: dict[str, Any]) -> dict[str, Any]:
        nak = _nakshatra(float(fact["longitude"]))
        sign_num = int(float(fact["longitude"]) / 30)
        return {
            "graha": graha,
            "longitude": round(float(fact["longitude"]), 4),
            "sign": _sign_num_to_name(sign_num),
            "sign_num": sign_num,
            "nakshatra": nak["name"],
            "pada": int(nak["pada"]),
            "retrograde": bool(fact["retrograde"]),
            "speed_deg_per_day": round(float(fact["longitude_speed_deg_per_day"]), 6),
            "motion_state": fact.get("motion_state", "DIRECT"),
        }

    def _evaluate_rules(self, facts: list[TransitFact]) -> list[TransitRuleResult]:
        results: list[TransitRuleResult] = []
        lookup: dict[tuple[str, TransitReferenceType, str], list[tuple[int, TransitFact]]] = {}
        for idx, fact in enumerate(facts):
            lookup.setdefault((fact.graha, fact.natal_reference_type, fact.natal_reference_entity), []).append((idx, fact))

        for reference_type, reference_entity in (
            (TransitReferenceType.MOON, "Moon"),
            (TransitReferenceType.LAGNA, "Lagna"),
        ):
            saturn_facts = lookup.get(("Saturn", reference_type, reference_entity), [])
            moon_saturn = [item for item in saturn_facts if item[1].natal_reference_type == reference_type]
            if moon_saturn:
                idx, fact = moon_saturn[0]
                if reference_type == TransitReferenceType.MOON and fact.relative_house in (12, 1, 2):
                    results.append(
                        TransitRuleResult(
                            rule_id="VEDA-P019-RUL-001",
                            title="Sade Sati structural window",
                            graha="Saturn",
                            reference_type=reference_type,
                            reference_entity=reference_entity,
                            matched=True,
                            evaluation_status=TransitValidationStatus.RESEARCH_REQUIRED,
                            reason=f"Transit Saturn is in the {fact.relative_house}th house from natal Moon.",
                            source_claim_ids=["VEDA-P019-CLM-000004"],
                            matched_fact_indexes=[idx],
                            method_id="P019-GOCHAR-RULE-001",
                        )
                    )
                elif reference_type == TransitReferenceType.MOON and fact.relative_house in (4, 8):
                    results.append(
                        TransitRuleResult(
                            rule_id="VEDA-P019-RUL-002",
                            title="Dhaiya / Kantaka structural window",
                            graha="Saturn",
                            reference_type=reference_type,
                            reference_entity=reference_entity,
                            matched=True,
                            evaluation_status=TransitValidationStatus.RESEARCH_REQUIRED,
                            reason=f"Transit Saturn is in the {fact.relative_house}th house from natal Moon.",
                            source_claim_ids=["VEDA-P019-CLM-000005"],
                            matched_fact_indexes=[idx],
                            method_id="P019-GOCHAR-RULE-002",
                        )
                    )

        # Keep the rule layer transparent even when no classical window matches.
        if not results:
            results.append(
                TransitRuleResult(
                    rule_id="VEDA-P019-RUL-000",
                    title="Transit rule evaluation baseline",
                    graha="ALL",
                    reference_type=TransitReferenceType.LAGNA,
                    reference_entity="Lagna",
                    matched=False,
                    evaluation_status=TransitValidationStatus.RESEARCH_REQUIRED,
                    reason="No governed structural rule matched the requested snapshot.",
                    source_claim_ids=[],
                    matched_fact_indexes=[],
                    method_id="P019-GOCHAR-RULE-BASELINE",
                )
            )
        return results

    def _compute_windows(
        self,
        transit_time_utc: datetime,
        positions: dict[str, dict[str, Any]],
        planets: Iterable[str],
        window_days: int = 180,
    ) -> list[TransitWindow]:
        windows: list[TransitWindow] = []
        start = transit_time_utc - timedelta(days=window_days)
        end = transit_time_utc + timedelta(days=window_days)
        for planet in planets:
            if planet not in positions:
                continue
            planet_windows = self._sign_windows(planet, start, end)
            for idx, window in enumerate(planet_windows, start=1):
                if window["entry_utc"] <= transit_time_utc <= window["exit_utc"]:
                    windows.append(
                        TransitWindow(
                            graha=planet,
                            sign=window["sign"],
                            pass_number=idx,
                            entry_utc=window["entry_utc"].isoformat().replace("+00:00", "Z"),
                            exit_utc=window["exit_utc"].isoformat().replace("+00:00", "Z"),
                            retrograde_pass=window["retrograde_pass"],
                            method_id="P019-GOCHAR-WINDOW-001",
                            validation_status=TransitValidationStatus.IMPLEMENTED_UNVALIDATED,
                        )
                    )
        return windows

    def _sign_windows(self, planet: str, start_utc: datetime, end_utc: datetime) -> list[dict[str, Any]]:
        sample_points: list[tuple[datetime, int, bool]] = []
        cursor = start_utc
        while cursor <= end_utc:
            fact = self._planet_positions(cursor).get(planet)
            if fact is None:
                break
            sign_num = int(float(fact["longitude"]) / 30)
            sample_points.append((cursor, sign_num, bool(fact["retrograde"])))
            cursor += timedelta(days=1)
        if not sample_points:
            return []

        windows: list[dict[str, Any]] = []
        current_start = sample_points[0][0]
        current_sign = sample_points[0][1]
        current_retro = sample_points[0][2]

        for (prev_dt, prev_sign, prev_retro), (next_dt, next_sign, next_retro) in zip(sample_points, sample_points[1:]):
            if next_sign != current_sign:
                boundary = self._refine_boundary(planet, prev_dt, next_dt, current_sign, next_sign)
                windows.append(
                    {
                        "sign": _sign_num_to_name(current_sign),
                        "entry_utc": current_start,
                        "exit_utc": boundary,
                        "retrograde_pass": current_retro or prev_retro or next_retro,
                    }
                )
                current_start = boundary
                current_sign = next_sign
                current_retro = next_retro
        windows.append(
            {
                "sign": _sign_num_to_name(current_sign),
                "entry_utc": current_start,
                "exit_utc": end_utc,
                "retrograde_pass": current_retro,
            }
        )
        return windows

    def _refine_boundary(
        self,
        planet: str,
        start_dt: datetime,
        end_dt: datetime,
        lower_sign: int,
        upper_sign: int,
    ) -> datetime:
        lower = start_dt
        upper = end_dt
        while (upper - lower).total_seconds() > 60:
            midpoint = lower + (upper - lower) / 2
            fact = self._planet_positions(midpoint).get(planet)
            if fact is None:
                break
            sign_num = int(float(fact["longitude"]) / 30)
            if sign_num == lower_sign:
                lower = midpoint
            else:
                upper = midpoint
        return upper

    def _summarize_metrics(
        self,
        facts: list[TransitFact],
        rules: list[TransitRuleResult],
        windows: list[TransitWindow],
    ) -> dict[str, Any]:
        per_reference: dict[str, int] = {}
        for fact in facts:
            key = fact.natal_reference_type.value
            per_reference[key] = per_reference.get(key, 0) + 1
        return {
            "fact_count": len(facts),
            "rule_count": len(rules),
            "window_count": len(windows),
            "reference_counts": per_reference,
            "interpretation_state": "RESEARCH_ONLY",
        }

    def save_foundation_snapshot(self, snapshot: TransitSnapshot, path: Path | None = None) -> Path:
        target = path or TRANSIT_FOUNDATION_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "entity_id": snapshot.entity_id,
            "location_id": snapshot.location_id,
            "epoch_utc": snapshot.transit_time_utc,
            "julian_date": snapshot.julian_day,
            "body_positions": json.dumps(snapshot.transit_chart, ensure_ascii=False, sort_keys=True),
            "gochar_metrics": json.dumps(snapshot.gochar_metrics, ensure_ascii=False, sort_keys=True),
            "source_ephemeris_version": snapshot.source_ephemeris_version,
            "computed_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        df = pd.DataFrame([row])
        if df.empty:
            raise ValueError("cannot write empty transit snapshot")
        df.to_parquet(target, index=False)
        return target


def build_gochar_snapshot(
    natal_chart: dict[str, Any],
    transit_time: datetime | None = None,
    timezone_name: str | None = None,
    reference_bases: Iterable[TransitReferenceType] | None = None,
) -> TransitSnapshot:
    return TransitGocharEngine().build_snapshot(natal_chart, transit_time, timezone_name, reference_bases)
