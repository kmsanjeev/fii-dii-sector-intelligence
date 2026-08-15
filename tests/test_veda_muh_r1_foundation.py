from datetime import date

import pytest

from engines.ai.knowledge.muhurta_foundation import (
    METHOD_ID,
    MuhurtaRequest,
    build_muhurta_foundation,
    compute_solar_day,
)
from engines.ai.knowledge.astrology_capability_framework import JyotishaCapabilityLifecycleService


def test_solar_day_is_deterministic_and_location_aware():
    request = MuhurtaRequest(date(2026, 6, 21), 28.6139, 77.2090, "Asia/Kolkata")
    first = compute_solar_day(request)
    second = compute_solar_day(request)

    assert first == second
    assert first.method_id == METHOD_ID
    assert first.sunrise_status == "AVAILABLE"
    assert first.sunset_status == "AVAILABLE"
    assert first.sunrise_local < first.sunset_local
    assert first.sunrise_local.tzinfo is not None


def test_foundation_contract_exposes_gates_without_recommendation():
    result = build_muhurta_foundation(
        MuhurtaRequest(date(2026, 8, 15), 19.0760, 72.8777, "Asia/Kolkata", "MARRIAGE")
    )

    assert result["activation_status"] == "INACTIVE"
    assert result["recommendation_status"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["event_rules"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["tarabala"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["chandrabala"] == "NOT_IMPLEMENTED"
    assert result["dependencies"]["prashna"] == "OUT_OF_SCOPE"


def test_request_rejects_invalid_coordinates_timezone_and_event():
    with pytest.raises(ValueError):
        MuhurtaRequest(date(2026, 1, 1), 91, 0, "UTC").validate()
    with pytest.raises(ValueError):
        MuhurtaRequest(date(2026, 1, 1), 0, 0, "Not/AZone").validate()
    with pytest.raises(ValueError):
        MuhurtaRequest(date(2026, 1, 1), 0, 0, "UTC", "UNKNOWN").validate()


def test_capability_registry_records_foundation_only_state():
    record = next(
        item
        for item in JyotishaCapabilityLifecycleService().registry_records()
        if item.capability_id == "VEDA-CAP-ADVANCED-000002"
    )
    assert record.implementation_status == "FOUNDATION_ONLY_NO_ELECTIONAL_SELECTION"
    assert record.activation_status.value == "INACTIVE"
    assert record.validation_status == "PARTIAL_FOUNDATION_VALIDATED"
