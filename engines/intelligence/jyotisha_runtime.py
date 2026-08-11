from __future__ import annotations

import hashlib
import threading
import uuid
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Optional
from zoneinfo import ZoneInfo

from engines.common import config as cfg
from engines.intelligence.kundli_engine import COUNTRY_CHARTS, EXCHANGES, KundliEngine


RUNTIME_CONTRACT_VERSION = "2026-08-11"
CALCULATION_PROVIDER_VERSION = "swisseph-lahiri-true-node"
LAGNA_ENTITY_ID = "VEDA-LAGNA-ASCENDANT"
DASHA_ENTITY_ID = "VEDA-DASHA-VIMSHOTTARI"

CORE_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
NON_CORE_GRAHAS = ("Uranus", "Neptune")
ALL_GRAHAS = CORE_GRAHAS + NON_CORE_GRAHAS
SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
SIGN_LORDS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}
NAKSHATRA_ID_OVERRIDES = {
    "Purva Bhadra": "VEDA-NAK-PURVA_BHADRAPADA",
    "Purva Bhadrapada": "VEDA-NAK-PURVA_BHADRAPADA",
    "Uttara Bhadra": "VEDA-NAK-UTTARA_BHADRAPADA",
    "Uttara Bhadrapada": "VEDA-NAK-UTTARA_BHADRAPADA",
    "Dhanishta": "VEDA-NAK-DHANISHTHA",
    "Dhanishtha": "VEDA-NAK-DHANISHTHA",
    "Purva Phalguni": "VEDA-NAK-PURVA_PHALGUNI",
    "Uttara Phalguni": "VEDA-NAK-UTTARA_PHALGUNI",
    "Purva Ashadha": "VEDA-NAK-PURVA_ASHADHA",
    "Uttara Ashadha": "VEDA-NAK-UTTARA_ASHADHA",
}
VARGA_ID_OVERRIDES = {
    "d9_navamsa": "VEDA-VARGA-D09",
    "d10_dasamsa": "VEDA-VARGA-D10",
}
CONTRACT_CHART_TYPES = {
    "PERSON": "PERSONAL_KUNDLI",
    "STOCK": "STOCK_KUNDLI",
    "COUNTRY": "COUNTRY_KUNDLI",
    "EVENT": "GENERIC",
    "MARKET": "GENERIC",
}

SURFACE_PERSONAL = "personal_kundli_chat_path"
SURFACE_REST = "rest_human_kundli_path"
SURFACE_STOCK = "stock_kundli_route"
SURFACE_COUNTRY = "country_kundli_route"


def _slug(value: str) -> str:
    return (
        value.strip()
        .upper()
        .replace("-", "_")
        .replace("/", "_")
        .replace(" ", "_")
        .replace(".", "_")
    )


def _graha_entity_id(name: str) -> str:
    return f"VEDA-GRAHA-{_slug(name)}"


def _rashi_entity_id(name: str) -> str:
    return f"VEDA-RASHI-{_slug(name)}"


def _bhava_entity_id(number: int) -> str:
    return f"VEDA-BHAVA-{number:02d}"


def _nakshatra_entity_id(name: str) -> str:
    return NAKSHATRA_ID_OVERRIDES.get(name, f"VEDA-NAK-{_slug(name)}")


def _varga_entity_id(name: str) -> str:
    key = name.strip()
    if key in VARGA_ID_OVERRIDES:
        return VARGA_ID_OVERRIDES[key]
    normalized = key.upper()
    if normalized.startswith("D") and normalized[1:].isdigit():
        return f"VEDA-VARGA-D{int(normalized[1:]):02d}"
    return f"VEDA-VARGA-{_slug(key)}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _stable_hash(parts: list[Any]) -> str:
    raw = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(slots=True, frozen=True)
class RuntimeProfile:
    profile_id: str
    runtime_surface: str
    subject_types: tuple[str, ...]
    timezone_policy: str
    node_policy: str
    house_policy: str
    ayanamsha_policy: str
    varga_surface: tuple[str, ...]
    dasha_surface: tuple[str, ...]
    confidence_status: str
    notes: str


@dataclass(slots=True)
class JyotishaRuntimeRequest:
    request_id: str
    runtime_profile: str
    subject_type: str
    datetime_local: str
    timezone: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    location_name: Optional[str]
    calculation_options: dict[str, Any] = field(default_factory=dict)
    requested_facts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NormalizedRuntimeInput:
    request: JyotishaRuntimeRequest
    profile: RuntimeProfile
    local_datetime: datetime
    utc_datetime: datetime
    timezone_name: str
    timezone_offset_hours: float
    julian_day: float


@dataclass(slots=True)
class RuntimeExecution:
    request: JyotishaRuntimeRequest
    profile: RuntimeProfile
    runtime_surface: str
    legacy_payload: dict[str, Any]
    chart_facts: dict[str, Any]
    diagnostics: dict[str, Any]


@dataclass(slots=True)
class ShadowComparison:
    request_id: str
    primary_surface: str
    comparison_surface: str
    primary_profile: str
    comparison_profile: str
    divergences: list[dict[str, Any]]
    divergence_count: int
    status: str


RUNTIME_PROFILES: dict[str, RuntimeProfile] = {
    "PERSONAL": RuntimeProfile(
        profile_id="PERSONAL",
        runtime_surface=SURFACE_PERSONAL,
        subject_types=("PERSON",),
        timezone_policy="USER_PROVIDED_OFFSET",
        node_policy="TRUE_NODE",
        house_policy="WHOLE_SIGN",
        ayanamsha_policy="LAHIRI",
        varga_surface=("D9", "D10"),
        dasha_surface=("MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA", "ALL_ANTARDASHAS"),
        confidence_status="VALIDATED_WITH_CONDITIONS",
        notes="Personal path accepts caller-supplied offset rather than governed IANA timezone history.",
    ),
    "REST_STANDARD": RuntimeProfile(
        profile_id="REST_STANDARD",
        runtime_surface=SURFACE_REST,
        subject_types=("PERSON",),
        timezone_policy="USER_PROVIDED_OFFSET",
        node_policy="TRUE_NODE",
        house_policy="WHOLE_SIGN",
        ayanamsha_policy="LAHIRI",
        varga_surface=("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"),
        dasha_surface=("MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"),
        confidence_status="VALIDATED_WITH_CONDITIONS",
        notes="REST human path preserves broader varga output and fixed-offset caller semantics.",
    ),
    "STOCK_MARKET": RuntimeProfile(
        profile_id="STOCK_MARKET",
        runtime_surface=SURFACE_STOCK,
        subject_types=("STOCK", "MARKET"),
        timezone_policy="HARDCODED_OFFSET",
        node_policy="TRUE_NODE",
        house_policy="WHOLE_SIGN",
        ayanamsha_policy="LAHIRI",
        varga_surface=("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"),
        dasha_surface=("MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"),
        confidence_status="VALIDATED_WITH_CONDITIONS",
        notes="Exchange offsets are still fixed in the legacy engine and remain DST-sensitive under P004 conditions.",
    ),
    "COUNTRY_EVENT": RuntimeProfile(
        profile_id="COUNTRY_EVENT",
        runtime_surface=SURFACE_COUNTRY,
        subject_types=("COUNTRY", "EVENT"),
        timezone_policy="HARDCODED_OFFSET",
        node_policy="TRUE_NODE",
        house_policy="WHOLE_SIGN",
        ayanamsha_policy="LAHIRI",
        varga_surface=("D1", "D2", "D3", "D4", "D7", "D9", "D10", "D11", "D12", "D16", "D20", "D30", "D60"),
        dasha_surface=("MAHADASHA", "ANTARDASHA", "PRATYANTARDASHA"),
        confidence_status="VALIDATED_WITH_CONDITIONS",
        notes="Country/event inception data carries historical civil-time provenance conditions from P004.",
    ),
}


class SwissEphemerisCalculationProvider:
    _sidereal_lock = threading.RLock()

    def __init__(self) -> None:
        self.engine = KundliEngine()

    def _ensure_sidereal_mode(self) -> None:
        self.engine._swe.set_sid_mode(self.engine._swe.SIDM_LAHIRI)

    def version(self) -> str:
        return CALCULATION_PROVIDER_VERSION

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider": "SWISS_EPHEMERIS_KUNDLI_ENGINE",
            "version": self.version(),
            "profiles": sorted(RUNTIME_PROFILES),
            "subject_types": sorted({subject for profile in RUNTIME_PROFILES.values() for subject in profile.subject_types}),
            "sidereal_mode": "SIDM_LAHIRI",
            "node_method": "TRUE_NODE",
            "house_method": "WHOLE_SIGN_DOWNSTREAM",
        }

    def health(self) -> dict[str, Any]:
        with self._sidereal_lock:
            self._ensure_sidereal_mode()
            return {
                "ready": True,
                "provider": "SWISS_EPHEMERIS_KUNDLI_ENGINE",
                "sidereal_mode": "SIDM_LAHIRI",
                "version": self.version(),
            }

    def julian_day(self, dt_utc: datetime) -> float:
        with self._sidereal_lock:
            self._ensure_sidereal_mode()
            hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
            return float(self.engine._swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour))


class BaseLegacyAdapter:
    runtime_surface: str = ""
    runtime_profile: str = ""
    classification: str = "LEGACY_RUNTIME"

    def execute(self, provider: SwissEphemerisCalculationProvider, normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        raise NotImplementedError


class LegacyPersonalAdapter(BaseLegacyAdapter):
    runtime_surface = SURFACE_PERSONAL
    runtime_profile = "PERSONAL"
    classification = "PRIMARY_RUNTIME"

    def execute(self, provider: SwissEphemerisCalculationProvider, normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli

        req = normalized.request
        raw_date = str(req.metadata.get("date_of_birth_raw") or normalized.local_datetime.strftime("%Y-%m-%d"))
        raw_time = str(req.metadata.get("time_of_birth_raw") or normalized.local_datetime.strftime("%H:%M"))
        with provider._sidereal_lock:
            provider._ensure_sidereal_mode()
            return compute_personal_kundli(
                date_of_birth=raw_date,
                time_of_birth=raw_time,
                place_name=req.location_name or str(req.metadata.get("place_name") or "Unknown"),
                latitude=req.latitude,
                longitude=req.longitude,
                timezone_offset_hours=normalized.timezone_offset_hours,
            )


class LegacyRestAdapter(BaseLegacyAdapter):
    runtime_surface = SURFACE_REST
    runtime_profile = "REST_STANDARD"
    classification = "PRIMARY_RUNTIME"

    def execute(self, provider: SwissEphemerisCalculationProvider, normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        req = normalized.request
        with provider._sidereal_lock:
            provider._ensure_sidereal_mode()
            return provider.engine.compute_human(
                name=str(req.metadata.get("name") or req.location_name or "Unnamed"),
                date_str=normalized.local_datetime.strftime("%Y-%m-%d"),
                time_str=normalized.local_datetime.strftime("%H:%M:%S"),
                lat=float(req.latitude),
                lon=float(req.longitude),
                tz_offset=normalized.timezone_offset_hours,
            )


class LegacyStockAdapter(BaseLegacyAdapter):
    runtime_surface = SURFACE_STOCK
    runtime_profile = "STOCK_MARKET"
    classification = "SPECIALIZED_RUNTIME"

    def execute(self, provider: SwissEphemerisCalculationProvider, normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        req = normalized.request
        symbol = str(req.metadata.get("symbol") or req.location_name or "UNKNOWN").upper()
        listing_date = str(req.metadata.get("listing_date") or normalized.local_datetime.strftime("%Y-%m-%d"))
        exchange = str(req.metadata.get("exchange") or req.calculation_options.get("exchange") or "NSE")
        with provider._sidereal_lock:
            provider._ensure_sidereal_mode()
            return provider.engine.compute_stock(symbol, listing_date, exchange)


class LegacyCountryAdapter(BaseLegacyAdapter):
    runtime_surface = SURFACE_COUNTRY
    runtime_profile = "COUNTRY_EVENT"
    classification = "SPECIALIZED_RUNTIME"

    def execute(self, provider: SwissEphemerisCalculationProvider, normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        req = normalized.request
        country_name = str(req.metadata.get("country_name") or req.location_name or "India")
        with provider._sidereal_lock:
            provider._ensure_sidereal_mode()
            return provider.engine.compute_country(country_name)


class JyotishaRuntimeService:
    def __init__(self) -> None:
        self.provider = SwissEphemerisCalculationProvider()
        self._adapters: dict[str, BaseLegacyAdapter] = {
            SURFACE_PERSONAL: LegacyPersonalAdapter(),
            SURFACE_REST: LegacyRestAdapter(),
            SURFACE_STOCK: LegacyStockAdapter(),
            SURFACE_COUNTRY: LegacyCountryAdapter(),
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "contract_version": RUNTIME_CONTRACT_VERSION,
            "provider": self.provider.capabilities(),
            "profiles": [asdict(profile) for profile in RUNTIME_PROFILES.values()],
            "surfaces": [
                {
                    "runtime_surface": adapter.runtime_surface,
                    "runtime_profile": adapter.runtime_profile,
                    "classification": adapter.classification,
                }
                for adapter in self._adapters.values()
            ],
        }

    def health(self) -> dict[str, Any]:
        health = self.provider.health()
        health["contract_version"] = RUNTIME_CONTRACT_VERSION
        return health

    def build_personal_request(
        self,
        date_of_birth: str,
        time_of_birth: str,
        place_name: str,
        *,
        latitude: Optional[float],
        longitude: Optional[float],
        timezone_offset_hours: float,
    ) -> JyotishaRuntimeRequest:
        date_value = self._normalize_date_for_contract(date_of_birth)
        time_value = self._normalize_time_for_contract(time_of_birth)
        return JyotishaRuntimeRequest(
            request_id=f"veda-p12-{uuid.uuid4().hex[:12]}",
            runtime_profile="PERSONAL",
            subject_type="PERSON",
            datetime_local=f"{date_value}T{time_value}",
            timezone=self._offset_label(timezone_offset_hours),
            latitude=latitude,
            longitude=longitude,
            location_name=place_name,
            calculation_options={"timezone_offset_hours": timezone_offset_hours},
            requested_facts=["lagna", "grahas", "nakshatra", "vimshottari", "vargas"],
            metadata={
                "place_name": place_name,
                "date_of_birth_raw": date_of_birth,
                "time_of_birth_raw": time_of_birth,
                "time_approximate": time_of_birth.strip().lower() in ("unknown", "", "?", "not known", "nn"),
            },
        )

    def build_rest_human_request(
        self,
        name: str,
        date_str: str,
        time_str: str,
        *,
        lat: float,
        lon: float,
        tz_offset: float,
    ) -> JyotishaRuntimeRequest:
        time_value = time_str if time_str.count(":") == 2 else f"{time_str}:00"
        return JyotishaRuntimeRequest(
            request_id=f"veda-p12-{uuid.uuid4().hex[:12]}",
            runtime_profile="REST_STANDARD",
            subject_type="PERSON",
            datetime_local=f"{date_str}T{time_value}",
            timezone=self._offset_label(tz_offset),
            latitude=lat,
            longitude=lon,
            location_name=name,
            calculation_options={"timezone_offset_hours": tz_offset},
            requested_facts=["lagna", "grahas", "nakshatra", "vimshottari", "vargas"],
            metadata={"name": name},
        )

    def build_stock_request(self, symbol: str, listing_date: str, exchange: str = "NSE") -> JyotishaRuntimeRequest:
        ex = EXCHANGES.get(exchange.upper(), EXCHANGES["NSE"])
        time_str = f"{ex['ipo_hour']:02d}:{ex['ipo_min']:02d}:00"
        tz_offset = float(self.provider.engine._tz_offset(ex["tz"]))
        return JyotishaRuntimeRequest(
            request_id=f"veda-p12-{uuid.uuid4().hex[:12]}",
            runtime_profile="STOCK_MARKET",
            subject_type="STOCK",
            datetime_local=f"{listing_date}T{time_str}",
            timezone=self._offset_label(tz_offset),
            latitude=float(ex["lat"]),
            longitude=float(ex["lon"]),
            location_name=symbol.upper(),
            calculation_options={"exchange": exchange.upper(), "timezone_offset_hours": tz_offset},
            requested_facts=["lagna", "grahas", "nakshatra", "vimshottari", "vargas"],
            metadata={
                "symbol": symbol.upper(),
                "listing_date": listing_date,
                "exchange": exchange.upper(),
                "exchange_timezone_name": ex["tz"],
            },
        )

    def build_country_request(self, country_name: str) -> JyotishaRuntimeRequest:
        country = COUNTRY_CHARTS[country_name]
        return JyotishaRuntimeRequest(
            request_id=f"veda-p12-{uuid.uuid4().hex[:12]}",
            runtime_profile="COUNTRY_EVENT",
            subject_type="COUNTRY",
            datetime_local=f"{country['date']}T{country['time']}",
            timezone=self._offset_label(float(country["tz_offset"])),
            latitude=float(country["lat"]),
            longitude=float(country["lon"]),
            location_name=country_name,
            calculation_options={"timezone_offset_hours": float(country["tz_offset"])},
            requested_facts=["lagna", "grahas", "nakshatra", "vimshottari", "vargas"],
            metadata={"country_name": country_name},
        )

    def compute_personal_chart(self, **kwargs: Any) -> RuntimeExecution:
        return self.execute(self.build_personal_request(**kwargs), SURFACE_PERSONAL)

    def compute_rest_human_chart(self, **kwargs: Any) -> RuntimeExecution:
        return self.execute(self.build_rest_human_request(**kwargs), SURFACE_REST)

    def compute_stock_chart(self, symbol: str, listing_date: str, exchange: str = "NSE") -> RuntimeExecution:
        return self.execute(self.build_stock_request(symbol, listing_date, exchange), SURFACE_STOCK)

    def compute_country_chart(self, country_name: str) -> RuntimeExecution:
        return self.execute(self.build_country_request(country_name), SURFACE_COUNTRY)

    def execute(self, request: JyotishaRuntimeRequest, runtime_surface: str) -> RuntimeExecution:
        adapter = self._adapters[runtime_surface]
        effective_request = request if request.runtime_profile == adapter.runtime_profile else replace(request, runtime_profile=adapter.runtime_profile)
        normalized = self.normalize_request(effective_request)
        legacy_payload = adapter.execute(self.provider, normalized)
        chart_facts = self._canonical_chart_facts(runtime_surface, normalized, legacy_payload)
        diagnostics = {
            "runtime_surface": runtime_surface,
            "runtime_profile": normalized.profile.profile_id,
            "classification": adapter.classification,
            "provider": "SWISS_EPHEMERIS_KUNDLI_ENGINE",
            "provider_version": self.provider.version(),
            "normalized_datetime": {
                "datetime_local": normalized.local_datetime.isoformat(),
                "timezone": normalized.timezone_name,
                "timezone_offset_hours": normalized.timezone_offset_hours,
                "utc_datetime": normalized.utc_datetime.isoformat(),
                "julian_day": round(normalized.julian_day, 6),
            },
        }
        return RuntimeExecution(
            request=effective_request,
            profile=normalized.profile,
            runtime_surface=runtime_surface,
            legacy_payload=legacy_payload,
            chart_facts=chart_facts,
            diagnostics=diagnostics,
        )

    def shadow_compare(
        self,
        request: JyotishaRuntimeRequest,
        *,
        primary_surface: str,
        comparison_surface: str,
    ) -> ShadowComparison:
        primary = self.execute(request, primary_surface)
        comparison = self.execute(request, comparison_surface)
        divergences = self._compare_chart_facts(primary.chart_facts, comparison.chart_facts)
        status = "MATCH" if not divergences else "KNOWN_DIVERGENCE"
        return ShadowComparison(
            request_id=request.request_id,
            primary_surface=primary_surface,
            comparison_surface=comparison_surface,
            primary_profile=primary.profile.profile_id,
            comparison_profile=comparison.profile.profile_id,
            divergences=divergences,
            divergence_count=len(divergences),
            status=status,
        )

    def normalize_request(self, request: JyotishaRuntimeRequest) -> NormalizedRuntimeInput:
        profile = RUNTIME_PROFILES[request.runtime_profile]
        raw = request.datetime_local.strip().replace(" ", "T")
        naive = datetime.fromisoformat(raw)
        tz_name = (request.timezone or "").strip()
        aware_local: datetime
        offset_hours = request.calculation_options.get("timezone_offset_hours")
        if tz_name and "/" in tz_name:
            aware_local = naive.replace(tzinfo=ZoneInfo(tz_name))
            offset = aware_local.utcoffset() or timedelta(0)
            offset_hours = offset.total_seconds() / 3600.0
        else:
            if offset_hours is None:
                offset_hours = request.metadata.get("timezone_offset_hours", 0.0)
            aware_local = naive.replace(tzinfo=timezone(timedelta(hours=float(offset_hours))))
            if not tz_name:
                tz_name = self._offset_label(float(offset_hours))
        utc_dt = aware_local.astimezone(timezone.utc)
        jd = self.provider.julian_day(utc_dt)
        return NormalizedRuntimeInput(
            request=request,
            profile=profile,
            local_datetime=aware_local,
            utc_datetime=utc_dt,
            timezone_name=tz_name,
            timezone_offset_hours=float(offset_hours),
            julian_day=jd,
        )

    def build_retrieval_fact_context(self, chart_facts: dict[str, Any]) -> dict[str, Any]:
        lagna = chart_facts.get("lagna") or {}
        planets = list(chart_facts.get("planets") or [])
        current_dasha = list(chart_facts.get("dashas") or [])
        fact_tags: list[str] = []
        if lagna:
            fact_tags.append(f"Lagna in {lagna.get('display_name')}")
        for item in planets[:9]:
            fact_tags.append(
                f"{item.get('display_name')} in {item.get('rashi_display_name')} bhava {item.get('bhava_number')}"
            )
        if current_dasha:
            maha = (current_dasha[0].get("current_periods") or {}).get("mahadasha") or {}
            if maha.get("planet"):
                fact_tags.append(f"Current Mahadasha {maha['planet']}")
        return {
            "chart_id": chart_facts.get("chart_id"),
            "runtime_profile": chart_facts.get("runtime_profile"),
            "fact_tags": [tag for tag in fact_tags if tag],
            "ontology_tokens": sorted(
                {
                    lagna.get("rashi_entity_id", ""),
                    *(planet.get("entity_id", "") for planet in planets),
                    *(planet.get("rashi_entity_id", "") for planet in planets),
                    *(planet.get("bhava_entity_id", "") for planet in planets),
                }
            ),
        }

    def _canonical_chart_facts(
        self,
        runtime_surface: str,
        normalized: NormalizedRuntimeInput,
        legacy_payload: dict[str, Any],
    ) -> dict[str, Any]:
        chart_type = CONTRACT_CHART_TYPES.get(normalized.request.subject_type, "GENERIC")
        chart_id = f"veda-chart-{_stable_hash([runtime_surface, normalized.request.request_id, normalized.utc_datetime.isoformat()])}"
        planet_facts, outer_grahas = self._planet_facts(legacy_payload)
        lagna = self._lagna_fact(legacy_payload)
        houses = self._house_facts(legacy_payload, lagna)
        vargas = self._varga_facts(legacy_payload)
        dashas = self._dasha_facts(legacy_payload)
        status = normalized.profile.confidence_status
        return {
            "contract_version": RUNTIME_CONTRACT_VERSION,
            "chart_id": chart_id,
            "chart_type": chart_type,
            "request_id": normalized.request.request_id,
            "runtime_profile": normalized.profile.profile_id,
            "runtime_surface": runtime_surface,
            "subject_type": normalized.request.subject_type,
            "normalized_datetime": {
                "datetime_local": normalized.local_datetime.isoformat(),
                "timezone": normalized.timezone_name,
                "timezone_offset_hours": round(normalized.timezone_offset_hours, 6),
                "utc_datetime": normalized.utc_datetime.isoformat(),
                "julian_day": round(normalized.julian_day, 6),
            },
            "ayanamsha": self._ayanamsha_fact(legacy_payload, normalized),
            "lagna": lagna,
            "planets": planet_facts,
            "houses": houses,
            "vargas": vargas,
            "dashas": dashas,
            "metadata": {
                "status": status,
                "confidence_status": status,
                "calculation_provider": "SWISS_EPHEMERIS_KUNDLI_ENGINE",
                "algorithm_version": self.provider.version(),
                "house_method": normalized.profile.house_policy,
                "node_method": normalized.profile.node_policy,
                "ayanamsha_policy": normalized.profile.ayanamsha_policy,
                "timezone_policy": normalized.profile.timezone_policy,
                "raw_entity": _jsonable(legacy_payload.get("entity") or {}),
                "non_core_grahas": outer_grahas,
                "requested_facts": list(normalized.request.requested_facts),
            },
        }

    def _ayanamsha_fact(self, legacy_payload: dict[str, Any], normalized: NormalizedRuntimeInput) -> dict[str, Any]:
        if "birth_details" in legacy_payload:
            ayanamsha = legacy_payload.get("birth_details", {}).get("ayanamsha")
            ayanamsha_type = legacy_payload.get("birth_details", {}).get("ayanamsha_type")
        else:
            with self.provider._sidereal_lock:
                self.provider._ensure_sidereal_mode()
                ayanamsha = round(float(self.provider.engine._swe.get_ayanamsa_ut(normalized.julian_day)), 4)
            ayanamsha_type = "Lahiri"
        return {
            "entity_id": "VEDA-AYANAMSHA-LAHIRI",
            "display_name": "Lahiri",
            "value": ayanamsha,
            "raw_legacy_value": ayanamsha,
            "source": ayanamsha_type or "Lahiri",
        }

    def _lagna_fact(self, legacy_payload: dict[str, Any]) -> dict[str, Any]:
        lagna = legacy_payload.get("lagna") or {}
        sign = str(lagna.get("sign") or "")
        return {
            "entity_id": LAGNA_ENTITY_ID,
            "display_name": "Ascendant",
            "rashi_entity_id": _rashi_entity_id(sign) if sign else None,
            "display_name_rashi": sign or None,
            "display_name_lord": lagna.get("lord"),
            "longitude": lagna.get("full_longitude"),
            "degree": lagna.get("degree"),
            "raw_legacy_value": _jsonable(lagna),
        }

    def _planet_facts(self, legacy_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        planets = legacy_payload.get("planets") or {}
        canonical: list[dict[str, Any]] = []
        outer: list[dict[str, Any]] = []
        for name, item in planets.items():
            sign = str(item.get("sign") or "")
            nak = str(item.get("nakshatra") or "")
            entry = {
                "entity_id": _graha_entity_id(name),
                "display_name": name,
                "longitude": item.get("longitude"),
                "degree": item.get("degree"),
                "rashi_entity_id": _rashi_entity_id(sign) if sign else None,
                "rashi_display_name": sign or None,
                "bhava_entity_id": _bhava_entity_id(int(item.get("house"))) if item.get("house") else None,
                "bhava_number": item.get("house"),
                "nakshatra_entity_id": _nakshatra_entity_id(nak) if nak else None,
                "nakshatra_display_name": nak or None,
                "pada": item.get("pada"),
                "retrograde": bool(item.get("retrograde", False)),
                "dignity": item.get("dignity"),
                "raw_legacy_value": _jsonable(item),
            }
            if name in CORE_GRAHAS:
                canonical.append(entry)
            else:
                outer.append(entry)
        canonical.sort(key=lambda row: CORE_GRAHAS.index(row["display_name"]))
        outer.sort(key=lambda row: row["display_name"])
        return canonical, outer

    def _house_facts(self, legacy_payload: dict[str, Any], lagna: dict[str, Any]) -> list[dict[str, Any]]:
        raw_houses = legacy_payload.get("all_houses") or {}
        if raw_houses:
            rows: list[dict[str, Any]] = []
            for house_num in range(1, 13):
                key = f"H{house_num}"
                item = raw_houses.get(key) or {}
                sign = str(item.get("sign") or "")
                rows.append(
                    {
                        "entity_id": _bhava_entity_id(house_num),
                        "house_number": house_num,
                        "rashi_entity_id": _rashi_entity_id(sign) if sign else None,
                        "display_name": sign or None,
                        "lord": item.get("lord"),
                        "occupants": list(item.get("occupants") or []),
                        "raw_legacy_value": _jsonable(item),
                    }
                )
            return rows

        lagna_sign = str(lagna.get("display_name_rashi") or "")
        if lagna_sign not in SIGN_LORDS:
            return []
        lagna_idx = SIGNS.index(lagna_sign)
        planet_rows = legacy_payload.get("planets") or {}
        rows = []
        for house_num in range(1, 13):
            sign = SIGNS[(lagna_idx + house_num - 1) % 12]
            occupants = sorted(
                planet_name for planet_name, pdata in planet_rows.items() if int(pdata.get("house", 0) or 0) == house_num
            )
            rows.append(
                {
                    "entity_id": _bhava_entity_id(house_num),
                    "house_number": house_num,
                    "rashi_entity_id": _rashi_entity_id(sign),
                    "display_name": sign,
                    "lord": SIGN_LORDS[sign],
                    "occupants": occupants,
                    "raw_legacy_value": {
                        "derived_from": "whole_sign_runtime_normalization",
                    },
                }
            )
        return rows

    def _varga_facts(self, legacy_payload: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if "vargas" in legacy_payload:
            for key, entries in (legacy_payload.get("vargas") or {}).items():
                chart_signs: dict[str, str] = {}
                for entry in entries:
                    planet = str(entry.get("planet") or "")
                    sign = str(entry.get("navamsa_sign") or entry.get("dasamsa_sign") or "")
                    if planet and sign:
                        chart_signs[_graha_entity_id(planet)] = _rashi_entity_id(sign)
                rows.append(
                    {
                        "entity_id": _varga_entity_id(key),
                        "varga_key": key,
                        "chart_signs": chart_signs,
                        "raw_legacy_value": _jsonable(entries),
                    }
                )
            rows.sort(key=lambda row: row["entity_id"])
            return rows

        for key, entries in (legacy_payload.get("divisional_charts") or {}).items():
            chart_signs = {
                _graha_entity_id(planet): _rashi_entity_id(sign)
                for planet, sign in (entries or {}).items()
                if planet in ALL_GRAHAS
            }
            rows.append(
                {
                    "entity_id": _varga_entity_id(key),
                    "varga_key": key,
                    "chart_signs": chart_signs,
                    "raw_legacy_value": _jsonable(entries),
                }
            )
        rows.sort(key=lambda row: row["entity_id"])
        return rows

    def _dasha_facts(self, legacy_payload: dict[str, Any]) -> list[dict[str, Any]]:
        current = legacy_payload.get("current_dasha") or {}
        periods = {}
        for key in ("mahadasha", "antardasha", "pratyantardasha"):
            if key in current:
                periods[key] = _jsonable(current[key])
        rows = [
            {
                "entity_id": DASHA_ENTITY_ID,
                "current_periods": periods,
                "mahadasha_sequence": [
                    item.get("planet")
                    for item in current.get("all_mahadashas", [])
                    if isinstance(item, dict) and item.get("planet")
                ],
                "has_all_antardashas": "all_antardashas" in current,
                "raw_legacy_value": _jsonable(current),
            }
        ]
        return rows

    def _compare_chart_facts(self, primary: dict[str, Any], comparison: dict[str, Any]) -> list[dict[str, Any]]:
        divergences: list[dict[str, Any]] = []
        p_lagna = primary.get("lagna") or {}
        c_lagna = comparison.get("lagna") or {}
        if p_lagna.get("display_name_rashi") != c_lagna.get("display_name_rashi"):
            divergences.append(
                {
                    "fact": "lagna_sign",
                    "value_a": p_lagna.get("display_name_rashi"),
                    "value_b": c_lagna.get("display_name_rashi"),
                    "difference": None,
                    "classification": "CALCULATION_DEFECT" if primary.get("runtime_profile") == comparison.get("runtime_profile") else "KNOWN_DIVERGENCE",
                    "known_reason": "Lagna sign differs between runtime families.",
                    "severity": "HIGH",
                    "disposition": "RESEARCH_REQUIRED",
                }
            )
        if p_lagna.get("longitude") is not None and c_lagna.get("longitude") is not None:
            delta = round(abs(float(p_lagna["longitude"]) - float(c_lagna["longitude"])), 6)
            if delta > 0.01:
                divergences.append(
                    {
                        "fact": "lagna_longitude",
                        "value_a": p_lagna.get("longitude"),
                        "value_b": c_lagna.get("longitude"),
                        "difference": delta,
                        "classification": "PRECISION_ONLY" if delta <= 0.25 else "KNOWN_DIVERGENCE",
                        "known_reason": "Ascendant derivation differs slightly between personal and REST surfaces.",
                        "severity": "MEDIUM" if delta > 0.25 else "LOW",
                        "disposition": "PRESERVE",
                    }
                )

        primary_planets = {item["display_name"]: item for item in primary.get("planets", [])}
        comparison_planets = {item["display_name"]: item for item in comparison.get("planets", [])}
        primary_outer = [item.get("display_name") for item in (primary.get("metadata", {}).get("non_core_grahas") or [])]
        comparison_outer = [item.get("display_name") for item in (comparison.get("metadata", {}).get("non_core_grahas") or [])]
        if primary_outer != comparison_outer:
            divergences.append(
                {
                    "fact": "non_core_graha_surface",
                    "value_a": primary_outer,
                    "value_b": comparison_outer,
                    "difference": None,
                    "classification": "LEGACY_COMPATIBILITY",
                    "known_reason": "REST-family runtimes surface Uranus/Neptune while the personal path limits canonical grahas to the classical set.",
                    "severity": "LOW",
                    "disposition": "PRESERVE",
                }
            )
        shared = sorted(set(primary_planets) & set(comparison_planets))
        for name in shared:
            p_item = primary_planets[name]
            c_item = comparison_planets[name]
            if p_item.get("longitude") is None or c_item.get("longitude") is None:
                continue
            delta = round(abs(float(p_item["longitude"]) - float(c_item["longitude"])), 6)
            if delta > 0.001:
                divergences.append(
                    {
                        "fact": f"{name}_longitude",
                        "value_a": p_item["longitude"],
                        "value_b": c_item["longitude"],
                        "difference": delta,
                        "classification": "PRECISION_ONLY" if delta <= 0.01 else "CALCULATION_DEFECT",
                        "known_reason": "Canonical graha longitude should normally align across shared Swiss-Ephemeris runtime families.",
                        "severity": "MEDIUM" if delta > 0.01 else "LOW",
                        "disposition": "RESEARCH_REQUIRED" if delta > 0.01 else "PRESERVE",
                    }
                )
            if p_item.get("dignity") != c_item.get("dignity"):
                divergences.append(
                    {
                        "fact": f"{name}_dignity",
                        "value_a": p_item.get("dignity"),
                        "value_b": c_item.get("dignity"),
                        "difference": None,
                        "classification": "LEGACY_COMPATIBILITY",
                        "known_reason": "Dignity tables remain surface-specific in current legacy personal and REST runtimes.",
                        "severity": "LOW",
                        "disposition": "PRESERVE",
                    }
                )

        if len(primary.get("vargas", [])) != len(comparison.get("vargas", [])):
            divergences.append(
                {
                    "fact": "varga_surface",
                    "value_a": [row.get("varga_key") for row in primary.get("vargas", [])],
                    "value_b": [row.get("varga_key") for row in comparison.get("vargas", [])],
                    "difference": None,
                    "classification": "EXPECTED_PROFILE_DIFFERENCE",
                    "known_reason": "Personal path exposes fewer surfaced vargas than REST/stock/country paths.",
                    "severity": "LOW",
                    "disposition": "PRESERVE",
                }
            )
        if (primary.get("dashas") or [{}])[0].get("has_all_antardashas") != (comparison.get("dashas") or [{}])[0].get("has_all_antardashas"):
            divergences.append(
                {
                    "fact": "all_antardashas_presence",
                    "value_a": (primary.get("dashas") or [{}])[0].get("has_all_antardashas"),
                    "value_b": (comparison.get("dashas") or [{}])[0].get("has_all_antardashas"),
                    "difference": None,
                    "classification": "EXPECTED_PROFILE_DIFFERENCE",
                    "known_reason": "Personal path exposes deeper dasha surface than REST/stock/country paths.",
                    "severity": "LOW",
                    "disposition": "PRESERVE",
                }
            )
        return divergences

    @staticmethod
    def _offset_label(offset_hours: float) -> str:
        sign = "+" if offset_hours >= 0 else "-"
        magnitude = abs(offset_hours)
        hours = int(magnitude)
        minutes = int(round((magnitude - hours) * 60))
        return f"UTC{sign}{hours:02d}:{minutes:02d}"

    @staticmethod
    def _normalize_date_for_contract(date_value: str) -> str:
        raw = date_value.strip()
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return raw

    @staticmethod
    def _normalize_time_for_contract(time_value: str) -> str:
        raw = time_value.strip()
        if raw.lower() in ("unknown", "", "?", "not known", "nn"):
            return "06:00:00"
        if raw.count(":") == 1:
            return f"{raw}:00"
        return raw


@lru_cache(maxsize=1)
def get_jyotisha_runtime_service() -> JyotishaRuntimeService:
    return JyotishaRuntimeService()


__all__ = [
    "CONTRACT_CHART_TYPES",
    "JyotishaRuntimeRequest",
    "JyotishaRuntimeService",
    "NormalizedRuntimeInput",
    "RUNTIME_CONTRACT_VERSION",
    "RUNTIME_PROFILES",
    "RuntimeExecution",
    "RuntimeProfile",
    "SURFACE_COUNTRY",
    "SURFACE_PERSONAL",
    "SURFACE_REST",
    "SURFACE_STOCK",
    "ShadowComparison",
    "get_jyotisha_runtime_service",
]
