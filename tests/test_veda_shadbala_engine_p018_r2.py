"""P018-R2 Shadbala Engine Tests.

Tests the six-component Shadbala calculation, BAV/SAV, and provenance tracking.
The Ashtakavarga assertions cover the canonical BPHS V2 production contract;
legacy P018-R2 replay is tested through its explicit compatibility route.
"""

import json
from pathlib import Path

import jsonschema

from engines.ai.knowledge.shadbala_engine import (
    NAISARGIKA_BALA,
    NAISARGIKA_TOTAL,
    DIG_BALA_MAXIMUM_HOUSE,
    BAV_CONTRIBUTIONS,
    VIMSHOPAKA_WEIGHTS,
    VIMSHOPAKA_TOTAL,
    DRIK_BALA_CONTRIBUTIONS,
    STANDARD_ASPECTS,
    calculate_naisargika_bala,
    calculate_dig_bala,
    calculate_sthana_bala,
    calculate_kala_bala,
    calculate_cheshta_bala,
    calculate_drik_bala,
    calculate_shadbala,
    calculate_bav,
    calculate_sav,
    ASHTAKAVARGA_RUNTIME_VALIDATED,
)


# ---------------------------------------------------------------------------
# M007: Naisargika Bala
# ---------------------------------------------------------------------------

class TestNaisargikaBala:
    """Tests for natural-strength (Naisargika Bala) calculation."""

    def test_sun_has_maximum_naisargika(self):
        result = calculate_naisargika_bala("Sun")
        assert result["raw_value"] == 60.0
        assert result["unit"] == "RUPA"
        assert result["validation_status"] == "IMPLEMENTED_UNVALIDATED"

    def test_saturn_has_minimum_naisargika(self):
        result = calculate_naisargika_bala("Saturn")
        assert result["raw_value"] == 8.5714

    def test_all_planets_have_naisargika(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            result = calculate_naisargika_bala(planet)
            assert result["raw_value"] is not None
            assert result["raw_value"] > 0

    def test_naisargika_total_is_420(self):
        # The canonical NAISARGIKA total is a defined classical constant (420 rupas).
        # The per-planet table contains proportional allocations; the module exposes
        # NAISARGIKA_TOTAL for the canonical total.
        assert abs(NAISARGIKA_TOTAL - 420.0) < 0.1

    def test_naisargika_has_source_claim(self):
        result = calculate_naisargika_bala("Sun")
        assert "VEDA-R2-CLM-000005" in result["source_claim_ids"]

    def test_naisargika_produces_canonical_fact(self):
        result = calculate_naisargika_bala("Jupiter")
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas" / "astrology" / "strength_fact.schema.json")
            .read_text(encoding="utf-8")
        )
        jsonschema.validate(result, schema)


# ---------------------------------------------------------------------------
# M005: Dig Bala
# ---------------------------------------------------------------------------

class TestDigBala:
    """Tests for directional strength (Dig Bala) calculation."""

    def test_jupiter_maximum_at_first_house(self):
        result = calculate_dig_bala("Jupiter", 1)
        assert result["raw_value"] == 60.0

    def test_sun_maximum_at_tenth_house(self):
        result = calculate_dig_bala("Sun", 10)
        assert result["raw_value"] == 60.0

    def test_moon_maximum_at_fourth_house(self):
        result = calculate_dig_bala("Moon", 4)
        assert result["raw_value"] == 60.0

    def test_venus_maximum_at_seventh_house(self):
        result = calculate_dig_bala("Venus", 7)
        assert result["raw_value"] == 60.0

    def test_saturn_maximum_at_seventh_house(self):
        result = calculate_dig_bala("Saturn", 7)
        assert result["raw_value"] == 60.0

    def test_dig_bala_decreases_away_from_maximum(self):
        result_max = calculate_dig_bala("Jupiter", 1)
        result_away = calculate_dig_bala("Jupiter", 4)
        assert result_max["raw_value"] > result_away["raw_value"]

    def test_dig_bala_opposite_house_is_minimum(self):
        result_max = calculate_dig_bala("Jupiter", 1)
        result_opp = calculate_dig_bala("Jupiter", 7)
        assert result_max["raw_value"] > result_opp["raw_value"]

    def test_dig_bala_has_source_claim(self):
        result = calculate_dig_bala("Sun", 10)
        assert "VEDA-R2-CLM-000003" in result["source_claim_ids"]

    def test_unknown_planet_returns_blocked(self):
        result = calculate_dig_bala("Rahu", 1)
        assert result["raw_value"] is None
        assert result["validation_status"] == "RESEARCH_REQUIRED"


# ---------------------------------------------------------------------------
# M004: Sthana Bala
# ---------------------------------------------------------------------------

class TestSthanaBala:
    """Tests for positional strength (Sthana Bala) calculation."""

    def test_sthana_bala_positive_for_normal_position(self):
        # Sun at 10 degrees Aries, Ascendant at 0 degrees Aries
        result = calculate_sthana_bala("Sun", 10.0, 0.0)
        assert result["raw_value"] is not None
        assert result["raw_value"] > 0

    def test_sthana_bala_has_kendra_component(self):
        # Planet in 1st house (kendra)
        result = calculate_sthana_bala("Sun", 10.0, 0.0)
        assert result["raw_value"] >= 60.0  # At least kendra_bala

    def test_sthana_bala_lower_for_non_kendra(self):
        # Planet in 2nd house (panaphara)
        result_kendra = calculate_sthana_bala("Sun", 10.0, 0.0)
        result_panaphara = calculate_sthana_bala("Sun", 40.0, 0.0)
        assert result_kendra["raw_value"] > result_panaphara["raw_value"]

    def test_sthana_bala_has_source_claim(self):
        result = calculate_sthana_bala("Sun", 10.0, 0.0)
        assert "VEDA-R2-CLM-000002" in result["source_claim_ids"]


# ---------------------------------------------------------------------------
# M006: Kala Bala
# ---------------------------------------------------------------------------

class TestKalaBala:
    """Tests for temporal strength (Kala Bala) calculation."""

    def test_diurnal_planet_stronger_by_day(self):
        result_day = calculate_kala_bala("Sun", is_daytime=True)
        result_night = calculate_kala_bala("Sun", is_daytime=False)
        assert result_day["raw_value"] > result_night["raw_value"]

    def test_nocturnal_planet_stronger_by_night(self):
        result_day = calculate_kala_bala("Moon", is_daytime=True)
        result_night = calculate_kala_bala("Moon", is_daytime=False)
        assert result_night["raw_value"] > result_day["raw_value"]

    def test_kala_bala_has_source_claim(self):
        result = calculate_kala_bala("Jupiter", is_daytime=True)
        assert "VEDA-R2-CLM-000004" in result["source_claim_ids"]


# ---------------------------------------------------------------------------
# M008: Cheshta Bala (motion dependency)
# ---------------------------------------------------------------------------

class TestCheshtaBala:
    """Tests for motional strength (Cheshta Bala) — motion dependency."""

    def test_cheshta_blocked_without_motion_facts(self):
        result = calculate_cheshta_bala("Sun")
        assert result["raw_value"] is None
        assert result["validation_status"] == "RESEARCH_REQUIRED"
        assert result["classification"] == "BLOCKED_BY_MOTION_FACTS"

    def test_cheshta_calculated_with_motion(self):
        result = calculate_cheshta_bala("Moon", daily_motion_arcsec=13.0 * 3600)
        assert result["raw_value"] is not None
        assert result["raw_value"] > 0

    def test_cheshta_has_source_claim(self):
        result = calculate_cheshta_bala("Sun")
        assert "VEDA-R2-CLM-000006" in result["source_claim_ids"]


# ---------------------------------------------------------------------------
# M010-M011: Drik Bala (aspect dependency)
# ---------------------------------------------------------------------------

class TestDrikBala:
    """Tests for aspectual strength (Drik Bala) — aspect dependency."""

    def test_drik_blocked_without_aspect_data(self):
        result = calculate_drik_bala("Sun")
        assert result["raw_value"] is None
        assert result["validation_status"] == "RESEARCH_REQUIRED"
        assert result["classification"] == "BLOCKED_BY_ASPECT_FOUNDATION"

    def test_drik_calculated_with_aspects(self):
        aspects = [{"from_planet": "Jupiter", "aspect_type": "FULL"}]
        result = calculate_drik_bala("Sun", aspects_received=aspects)
        assert result["raw_value"] == 2.0  # Jupiter contributes 2.0

    def test_drik_multiple_aspects(self):
        aspects = [
            {"from_planet": "Jupiter", "aspect_type": "FULL"},
            {"from_planet": "Mars", "aspect_type": "FULL"},
            {"from_planet": "Saturn", "aspect_type": "FULL"},
        ]
        result = calculate_drik_bala("Sun", aspects_received=aspects)
        assert result["raw_value"] == 3.0  # 2.0 + 0.5 + 0.5

    def test_drik_has_source_claim(self):
        result = calculate_drik_bala("Sun")
        assert "VEDA-R2-CLM-000007" in result["source_claim_ids"]


# ---------------------------------------------------------------------------
# M014: Shadbala Aggregation
# ---------------------------------------------------------------------------

class TestShadbalaAggregation:
    """Tests for total Shadbala aggregation."""

    def test_shadbala_blocks_when_components_missing(self):
        result = calculate_shadbala(
            planet="Sun",
            lon_deg=10.0,
            ascendant_lon=0.0,
            is_daytime=True,
        )
        assert result["status"] == "BLOCKED_BY_COMPONENTS"
        assert result["total"] is None

    def test_shadbala_calculates_when_all_available(self):
        result = calculate_shadbala(
            planet="Sun",
            lon_deg=10.0,
            ascendant_lon=0.0,
            is_daytime=True,
            daily_motion_arcsec=0.5 * 3600,  # Sun's daily motion
            aspects_received=[{"from_planet": "Jupiter", "aspect_type": "FULL"}],
        )
        assert result["status"] == "IMPLEMENTED_UNVALIDATED"
        assert result["total"] is not None
        assert result["total"] > 0

    def test_shadbala_has_all_six_components(self):
        result = calculate_shadbala(
            planet="Sun",
            lon_deg=10.0,
            ascendant_lon=0.0,
            is_daytime=True,
        )
        component_names = {c["component"] for c in result["components"]}
        assert component_names == {
            "NAISARGIKA_BALA", "DIG_BALA", "STHANA_BALA",
            "KALA_BALA", "CHESHTA_BALA", "DRIK_BALA"
        }

    def test_shadbala_has_source_claim(self):
        result = calculate_shadbala(
            planet="Sun",
            lon_deg=10.0,
            ascendant_lon=0.0,
            is_daytime=True,
        )
        assert "VEDA-R2-CLM-000001" in result["source_claim_ids"]

    def test_shadbala_result_matches_schema(self):
        result = calculate_shadbala(
            planet="Sun",
            lon_deg=10.0,
            ascendant_lon=0.0,
            is_daytime=True,
            daily_motion_arcsec=0.5 * 3600,
            aspects_received=[],
        )
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas" / "astrology" / "shadbala_result.schema.json")
            .read_text(encoding="utf-8")
        )
        jsonschema.validate(result, schema)


# ---------------------------------------------------------------------------
# M012: BAV Table Verification
# ---------------------------------------------------------------------------

class TestBAV:
    """Tests for Bhinna Ashtakavarga calculation."""

    def test_bav_contribution_table_is_complete(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            assert planet in BAV_CONTRIBUTIONS
            assert len(BAV_CONTRIBUTIONS[planet]) == 12

    def test_bav_produces_bindu_count(self):
        planet_rashis = {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
            "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 10,
        }
        result = calculate_bav("Sun", planet_rashis)
        assert result["status"] == ASHTAKAVARGA_RUNTIME_VALIDATED
        assert result["total_bindus"] >= 0
        assert len(result["rashis"]) == 12

    def test_bav_has_source_claim(self):
        planet_rashis = {"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10, "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 10}
        result = calculate_bav("Sun", planet_rashis)
        assert "VEDA-CALC-ASHTAKAVARGA-CONTRACT-RX2-001" in result["source_claim_ids"]

    def test_bav_is_target_sign_sensitive(self):
        result = calculate_bav("Sun", {"Sun": 1, "Moon": 3, "Mars": 7, "Mercury": 10, "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 4})
        by_sign = {item["sign"]: item["bindus"] for item in result["rashis"]}
        assert by_sign[3] >= 1
        assert by_sign[7] >= 1
        assert len({item["bindus"] for item in result["rashis"]}) > 1

    def test_bav_result_matches_schema(self):
        planet_rashis = {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
            "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 10,
        }
        result = calculate_bav("Sun", planet_rashis)
        schema = json.loads(
            (Path(__file__).parents[1] / "schemas" / "astrology" / "ashtakavarga_result.schema.json")
            .read_text(encoding="utf-8")
        )
        jsonschema.validate(result, schema)


# ---------------------------------------------------------------------------
# M013: SAV Method Verification
# ---------------------------------------------------------------------------

class TestSAV:
    """Tests for Sarvashtakavarga calculation."""

    def test_sav_aggregates_all_bav(self):
        planet_rashis = {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
            "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 10,
        }
        result = calculate_sav(planet_rashis)
        assert result["status"] == ASHTAKAVARGA_RUNTIME_VALIDATED
        assert result["total_bindus"] >= 0
        assert len(result["rashis"]) == 12

    def test_sav_total_is_sum_of_bav_totals(self):
        planet_rashis = {
            "Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10,
            "Jupiter": 1, "Venus": 4, "Saturn": 7,
        }
        result = calculate_sav(planet_rashis)
        bav_total = sum(result["bav_results"].values())
        assert result["total_bindus"] == bav_total

    def test_sav_has_source_claim(self):
        planet_rashis = {"Sun": 1, "Moon": 4, "Mars": 7, "Mercury": 10, "Jupiter": 1, "Venus": 4, "Saturn": 7, "Lagna": 10}
        result = calculate_sav(planet_rashis)
        assert "VEDA-CALC-ASHTAKAVARGA-CONTRACT-RX2-001" in result["source_claim_ids"]


# ---------------------------------------------------------------------------
# M010: Aspect Geometry Investigation
# ---------------------------------------------------------------------------

class TestAspectGeometry:
    """Tests for aspect geometry constants and standard aspects."""

    def test_all_planets_have_aspect_definitions(self):
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            assert planet in STANDARD_ASPECTS
            assert 7 in STANDARD_ASPECTS[planet]  # All aspects 7th

    def test_mars_aspects_4th_7th_8th(self):
        assert set(STANDARD_ASPECTS["Mars"]) == {4, 7, 8}

    def test_jupiter_aspects_5th_7th_9th(self):
        assert set(STANDARD_ASPECTS["Jupiter"]) == {5, 7, 9}

    def test_saturn_aspects_3rd_7th_10th(self):
        assert set(STANDARD_ASPECTS["Saturn"]) == {3, 7, 10}

    def test_drik_contributions_are_non_negative(self):
        for planet, value in DRIK_BALA_CONTRIBUTIONS.items():
            assert value >= 0


# ---------------------------------------------------------------------------
# M015: Conflict Reconciliation
# ---------------------------------------------------------------------------

class TestConflictReconciliation:
    """Tests for method variant visibility and conflict tracking."""

    def test_naisargika_values_match_classical_sources(self):
        # BPHS Ch.29 values
        assert NAISARGIKA_BALA["Sun"] == 60.0
        assert abs(NAISARGIKA_BALA["Moon"] - 51.4286) < 0.01
        assert abs(NAISARGIKA_BALA["Saturn"] - 8.5714) < 0.01

    def test_vimshopaka_total_is_16(self):
        assert VIMSHOPAKA_TOTAL == 16.0

    def test_bav_contributions_match_bphs(self):
        # Sun contributes in signs 1,2,4,7,8,9,10,11 (0-indexed: 0,1,3,6,7,8,9,10)
        expected_sun = [1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0]
        assert BAV_CONTRIBUTIONS["Sun"] == expected_sun


# ---------------------------------------------------------------------------
# M001: Baseline & Source Diversity
# ---------------------------------------------------------------------------

class TestSourceDiversity:
    """Tests for source diversification improvement over P018-R1."""

    def test_source_quality_file_exists(self):
        path = Path(__file__).parents[1] / "data" / "veda" / "research" / "astrology" / "p018-r2" / "source_quality.json"
        assert path.exists()

    def test_source_quality_shows_diversification(self):
        path = Path(__file__).parents[1] / "data" / "veda" / "research" / "astrology" / "p018-r2" / "source_quality.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["summary"]["independent_source_families"] >= 3
        assert data["summary"]["classical_primary_sources"] >= 1

    def test_research_execution_file_exists(self):
        path = Path(__file__).parents[1] / "data" / "veda" / "research" / "astrology" / "p018-r2" / "research_execution.json"
        assert path.exists()

    def test_claims_file_exists(self):
        path = Path(__file__).parents[1] / "data" / "veda" / "research" / "astrology" / "p018-r2" / "claims.json"
        assert path.exists()
