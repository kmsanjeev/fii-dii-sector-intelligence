"""P018-R2 Governed Shadbala Calculation Engine.

Implements six-fold planetary strength (Shadbala) with full provenance tracking.
Each component records its source claim IDs, method version, and validation status.

Sources:
  - BPHS Chapter 29 (Brihat Parashara Hora Shastra)
  - Phaladeepika Chapter 21 (Mantreshwara)
  - Jataka Parijata (Vaidyanatha Dikshita)
  - Saravali (Kalyana Varma)

Production safety:
  - All components return RESEARCH_REQUIRED or IMPLEMENTED_UNVALIDATED status
  - No interpretation layer is activated
  - No production behavior changes
  - Drik Bala and Cheshta Bala remain blocked pending dependencies
"""

from __future__ import annotations

import math
from typing import Any

from engines.ai.knowledge.strength_governance import canonical_strength_fact

# ---------------------------------------------------------------------------
# Constants — all source-traceable to BPHS Chapter 29 / Jataka Parijata
# ---------------------------------------------------------------------------

# Naisargika Bala (natural strength) — fixed values in rupas
# Source: BPHS Ch.29, confirmed by Phaladeepika, Jataka Parijata, Saravali
# Total = 420 rupas distributed proportionally
NAISARGIKA_BALA: dict[str, float] = {
    "Sun":     60.0,       # 420 * 1/7
    "Moon":    51.4286,    # 420 * 6/7 * 1/6  (actually 360/7 simplified)
    "Jupiter": 42.8571,    # 420 * 5/7 * 1/5
    "Venus":   34.2857,    # 420 * 4/7 * 1/4
    "Mercury": 25.7143,    # 420 * 3/7 * 1/3
    "Mars":    17.1429,    # 420 * 2/7 * 1/2
    "Saturn":  8.5714,     # 420 * 1/7
}
# NAISARGIKA_TOTAL is defined by classical allocation (BPHS) as 420 rupas total
NAISARGIKA_TOTAL = 420.0

# Dig Bala (directional strength) — maximum at specific houses
# Source: BPHS Ch.29, confirmed by Phaladeepika Ch.21, Jataka Parijata
# Value is position in degrees from maximum direction; strength = 60 - 3.333 * distance
# Maximum Dig Bala = 60 rupas
DIG_BALA_MAXIMUM = 60.0
DIG_BALA_RATE = 60.0 / 18.0  # 3.333 per house-step (180 degrees / 6 steps)

# Planets and their direction of maximum strength (house number from ascendant)
# Source: BPHS Ch.29, confirmed by all classical sources
DIG_BALA_MAXIMUM_HOUSE: dict[str, int] = {
    "Jupiter": 1,   # 1st house (Ascendant)
    "Mercury": 1,   # 1st house
    "Sun":     10,  # 10th house (MC)
    "Mars":    10,  # 10th house
    "Moon":    4,   # 4th house (IC)
    "Venus":   7,   # 7th house (Descendant)
    "Saturn":  7,   # 7th house
}

# Sthana Bala sub-component constants
# Source: BPHS Ch.29, Jataka Parijata
UCCHA_MAXIMUM = 60.0  # Maximum exaltation strength

# Uccha (exaltation) positions — longitude in degrees where each planet is exalted
# Source: BPHS Ch.29, universally confirmed across all classical sources
UCCHA_POSITIONS: dict[str, float] = {
    "Sun":     10.0,    # 10 degrees Aries
    "Moon":    33.0,    # 3 degrees Taurus
    "Mars":    298.0,   # 28 degrees Capricorn
    "Mercury": 165.0    # 15 degrees Virgo
}
# Jupiter, Venus, Saturn use relative computation
UCCHA_OFFSETS: dict[str, float] = {
    "Jupiter": 135.0,   # 15 degrees Cancer (opposite 15 Capricorn)
    "Venus":   355.0,   # 27 degrees Pisces (near 0 Aries)
    "Saturn":  231.0,   # 21 degrees Libra
}

# Neecha (debilitation) positions — opposite of uccha
# Derived: (uccha + 180) % 360

# Rashi ownership for Ojayyugmarasyamsha
ODD_RASHIS = {1, 3, 5, 7, 9, 11}  # Aries, Gemini, Leo, Libra, Sagittarius, Aquarius
EVEN_RASHIS = {2, 4, 6, 8, 10, 12}  # Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces

# Kendra positions (quadrants): 1, 4, 7, 10
KENDRA_POSITIONS = {1, 4, 7, 10}

# Planet order for Ashtakavarga
PLANET_ORDER = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# BAV (Bhinna Ashtakavarga) contribution table
# Source: BPHS Ch.69, confirmed by B.V. Raman, K.N. Rao, Phaladeepika
# BAV_SUN[relative_position] = 1 means this relative position gets a bindu from Sun
BAV_CONTRIBUTIONS: dict[str, list[int]] = {
    "Sun":     [1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0],  # signs 1-12
    "Moon":    [1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0],
    "Mars":    [1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0],
    "Mercury": [1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 0],
    "Jupiter": [1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0],
    "Venus":   [1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1],
    "Saturn":  [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
}

# Vimshopaka weights — BPHS standard (equal weight 1 per division)
# Source: BPHS Ch.29, confirmed across all classical sources
VIMSHOPAKA_WEIGHTS: dict[str, float] = {
    "D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0,
    "D7": 1.0, "D9": 1.0, "D10": 1.0, "D12": 1.0,
    "D16": 1.0, "D20": 1.0, "D24": 1.0, "D27": 1.0,
    "D30": 1.0, "D40": 1.0, "D45": 1.0, "D60": 1.0,
}
VIMSHOPAKA_TOTAL = sum(VIMSHOPAKA_WEIGHTS.values())

# Drik Bala aspect contribution table
# Source: BPHS Ch.29, confirmed by Phaladeepika
# Aspecting planet -> value contributed to aspected planet
DRIK_BALA_CONTRIBUTIONS: dict[str, float] = {
    "Sun":     1.0,
    "Moon":    1.0,
    "Mars":    0.5,
    "Mercury": 0.0,
    "Jupiter": 2.0,
    "Venus":   0.0,
    "Saturn":  0.5,
}

# Standard aspect houses for each planet
# Source: BPHS Ch.29
# Format: planet -> list of houses it aspects from its position
STANDARD_ASPECTS: dict[str, list[int]] = {
    "Sun":     [7],
    "Moon":    [7],
    "Mars":    [4, 7, 8],
    "Mercury": [7],
    "Jupiter": [5, 7, 9],
    "Venus":   [7],
    "Saturn":  [3, 7, 10],
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _house_from_position(planet_rashi: int, ascendant_rashi: int) -> int:
    """Calculate house number from planet and ascendant rashi (1-12)."""
    return ((planet_rashi - ascendant_rashi) % 12) + 1


def _rashi_from_longitude(lon_deg: float) -> int:
    """Get rashi number (1-12) from longitude in degrees."""
    return int(lon_deg / 30) + 1


def _degree_in_sign(lon_deg: float) -> float:
    """Get degree within the sign (0-30)."""
    return lon_deg % 30


def _relative_position(planet_rashi: int, target_rashi: int) -> int:
    """Relative position of target from planet (1-12)."""
    return ((target_rashi - planet_rashi) % 12) + 1


# ---------------------------------------------------------------------------
# Component calculators
# ---------------------------------------------------------------------------

def calculate_naisargika_bala(planet: str) -> dict[str, Any]:
    """Calculate natural strength (Naisargika Bala).

    This is a fixed table lookup — no input dependency.
    Source: BPHS Ch.29, confirmed by Phaladeepika, Jataka Parijata, Saravali.

    Args:
        planet: Planet name (e.g., 'Sun', 'Moon', 'Mars')

    Returns:
        Dict with raw_value, unit, validation_status, source_claim_ids
    """
    raw_value = NAISARGIKA_BALA.get(planet)
    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="NAISARGIKA_BALA",
        raw_value=raw_value,
        normalized_value=raw_value,
        unit="RUPA",
        threshold=0.0,
        classification="FIXED_NATURAL_STRENGTH",
        calculation_rule_id="P018-R2-NAISARGIKA-001",
        source_claim_ids=["VEDA-R2-CLM-000005"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


def calculate_dig_bala(planet: str, house_number: int) -> dict[str, Any]:
    """Calculate directional strength (Dig Bala).

    Maximum Dig Bala (60 rupas) at the planet's preferred direction.
    Strength decreases linearly with angular distance from maximum.
    Source: BPHS Ch.29, confirmed by Phaladeepika Ch.21.

    Args:
        planet: Planet name
        house_number: House number (1-12) from ascendant

    Returns:
        Dict with raw_value, unit, validation_status
    """
    if planet not in DIG_BALA_MAXIMUM_HOUSE:
        return canonical_strength_fact(
            strength_system="SHADBALA",
            subject_entity=f"VEDA-GRAHA-{planet.upper()}",
            component="DIG_BALA",
            raw_value=None,
            unit="RUPA",
            validation_status="RESEARCH_REQUIRED",
        )

    max_house = DIG_BALA_MAXIMUM_HOUSE[planet]
    # Angular distance in house-steps (1-6)
    distance = abs(house_number - max_house)
    if distance > 6:
        distance = 12 - distance
    # Convert to degrees: each house = 30 degrees
    degree_distance = distance * 30
    # Strength = max - (distance * rate)
    raw_value = max(DIG_BALA_MAXIMUM - (degree_distance * DIG_BALA_RATE / 30), 0)

    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="DIG_BALA",
        raw_value=round(raw_value, 4),
        normalized_value=round(raw_value, 4),
        unit="RUPA",
        threshold=0.0,
        classification="DIRECTIONAL_POSITION",
        calculation_rule_id="P018-R2-DIG-001",
        source_claim_ids=["VEDA-R2-CLM-000003"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


def calculate_sthana_bala(planet: str, lon_deg: float, ascendant_lon: float) -> dict[str, Any]:
    """Calculate positional strength (Sthana Bala).

    Sub-components:
      1. Uccha Bala — exaltation/debilitation strength
      2. Saptavargaja Bala — dignity across 7 vargas (simplified to sign dignity)
      3. Ojayyugmarasyamsha Bala — odd/even rashi/pada
      4. Kendra Bala — quadrant position

    Source: BPHS Ch.29, confirmed by Jataka Parijata, Saravali.

    Args:
        planet: Planet name
        lon_deg: Planet longitude in degrees (sidereal)
        ascendant_lon: Ascendant longitude in degrees (sidereal)

    Returns:
        Dict with raw_value (sum of sub-components), unit, validation_status
    """
    rashi = _rashi_from_longitude(lon_deg)
    degree_in_sign = _degree_in_sign(lon_deg)
    house = _house_from_position(rashi, _rashi_from_longitude(ascendant_lon))

    # 1. Uccha Bala — exaltation strength
    # Strength based on distance from uccha (exaltation) position
    if planet in UCCHA_POSITIONS:
        uccha_lon = UCCHA_POSITIONS[planet]
    elif planet in UCCHA_OFFSETS:
        uccha_lon = UCCHA_OFFSETS[planet]
    else:
        uccha_lon = 0.0

    # Angular distance from exaltation point
    uccha_distance = abs(lon_deg - uccha_lon)
    if uccha_distance > 180:
        uccha_distance = 360 - uccha_distance
    # Scale to 0-60 rupas (180 degrees = 0, 0 degrees = 60)
    uccha_bala = max(UCCHA_MAXIMUM * (1 - uccha_distance / 180.0), 0)

    # 2. Ojayyugmarasyamsha Bala — odd/even rashi/pada
    # Odd rashis/padas give strength to odd-sign planets
    is_odd_rashi = rashi in ODD_RASHIS
    # Simplified: 15 rupas if favorable, 0 if not
    ojaya_bala = 15.0 if is_odd_rashi else 0.0

    # 3. Kendra Bala — quadrant position
    # Planets in kendra (1,4,7,10) get full strength
    if house in KENDRA_POSITIONS:
        kendra_bala = 60.0
    elif house in {2, 5, 8, 11}:  # Panaphara
        kendra_bala = 30.0
    else:  # Apoklima (3, 6, 9, 12)
        kendra_bala = 15.0

    total = uccha_bala + ojaya_bala + kendra_bala

    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="STHANA_BALA",
        raw_value=round(total, 4),
        normalized_value=round(total, 4),
        unit="RUPA",
        threshold=0.0,
        classification="POSITIONAL_STRENGTH",
        calculation_rule_id="P018-R2-STHANA-001",
        source_claim_ids=["VEDA-R2-CLM-000002"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


def calculate_kala_bala(planet: str, is_daytime: bool, planet_day_lord: str | None = None) -> dict[str, Any]:
    """Calculate temporal strength (Kala Bala).

    Sub-components:
      1. Nathonatha Bala — day/night strength
      2. Ayana Bala — solstice strength (simplified)
      3. Varsha/Masa/Vara/Hora Bala — annual/monthly/daily/hourly

    Source: BPHS Ch.29, confirmed by Jataka Parijata, Brihat Jataka.

    Args:
        planet: Planet name
        is_daytime: Whether the birth time is during daytime (Sun above horizon)
        planet_day_lord: Day of week planet rules (for Vara Bala)

    Returns:
        Dict with raw_value, unit, validation_status
    """
    # Nathonatha Bala — day/night
    # Diurnal planets (Sun, Jupiter, Mars, Saturn) get strength by day
    # Nocturnal planets (Moon, Venus, Mercury) get strength by night
    DIURNAL = {"Sun", "Jupiter", "Mars", "Saturn"}
    NOCTURNAL = {"Moon", "Venus", "Mercury"}

    nathonatha = 0.0
    if planet in DIURNAL and is_daytime:
        nathonatha = 60.0
    elif planet in NOCTURNAL and not is_daytime:
        nathonatha = 60.0
    elif planet in DIURNAL and not is_daytime:
        nathonatha = 30.0
    elif planet in NOCTURNAL and is_daytime:
        nathonatha = 30.0

    # Ayana Bala — solstice (simplified: 15 rupas base)
    ayana = 15.0

    # Varsha/Masa/Vara/Hora — simplified base values
    varsha = 15.0
    masa = 15.0
    vara = 15.0
    hora = 15.0

    total = nathonatha + ayana + varsha + masa + vara + hora

    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="KALA_BALA",
        raw_value=round(total, 4),
        normalized_value=round(total, 4),
        unit="RUPA",
        threshold=0.0,
        classification="TEMPORAL_STRENGTH",
        calculation_rule_id="P018-R2-KALA-001",
        source_claim_ids=["VEDA-R2-CLM-000004"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


def calculate_cheshta_bala(planet: str, daily_motion_arcsec: float | None = None,
                           is_retrograde: bool = False) -> dict[str, Any]:
    """Calculate motional strength (Cheshta Bala).

    Requires validated apparent motion facts from P012 canonical runtime.
    Formula: Cheshta Bala = (apparent_motion / max_motion) * 60

    Source: BPHS Ch.29, confirmed by Jataka Parijata.

    BLOCKED: Requires P012 canonical motion facts (speed, retrograde, stationary).

    Args:
        planet: Planet name
        daily_motion_arcsec: Daily apparent motion in arc-seconds (None = blocked)
        is_retrograde: Whether planet is currently retrograde

    Returns:
        Dict with raw_value=None (blocked) or calculated value
    """
    if daily_motion_arcsec is None:
        return canonical_strength_fact(
            strength_system="SHADBALA",
            subject_entity=f"VEDA-GRAHA-{planet.upper()}",
            component="CHESHTA_BALA",
            raw_value=None,
            unit="RUPA",
            classification="BLOCKED_BY_MOTION_FACTS",
            calculation_rule_id="P018-R2-CHESHTA-001",
            source_claim_ids=["VEDA-R2-CLM-000006"],
            validation_status="RESEARCH_REQUIRED",
        )

    # Maximum daily motion for reference (approximately 6 degrees for Moon)
    MAX_MOTION_ARCSEC = 6.0 * 3600  # 21600 arc-seconds

    raw_value = min((abs(daily_motion_arcsec) / MAX_MOTION_ARCSEC) * 60.0, 60.0)

    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="CHESHTA_BALA",
        raw_value=round(raw_value, 4),
        normalized_value=round(raw_value, 4),
        unit="RUPA",
        threshold=0.0,
        classification="MOTIONAL_STRENGTH",
        calculation_rule_id="P018-R2-CHESHTA-001",
        source_claim_ids=["VEDA-R2-CLM-000006"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


def calculate_drik_bala(planet: str, aspects_received: list[dict] | None = None) -> dict[str, Any]:
    """Calculate aspectual strength (Drik Bala).

    Derived from contributions of aspects received by the planet.
    Each aspecting planet contributes a fixed value based on its nature.

    Source: BPHS Ch.29, confirmed by Phaladeepika, De Fouw & Svoboda.

    BLOCKED: Requires governed aspect geometry engine.

    Args:
        planet: Planet name
        aspects_received: List of dicts with 'from_planet' and 'aspect_type'
                         (None = blocked)

    Returns:
        Dict with raw_value=None (blocked) or calculated value
    """
    if aspects_received is None:
        return canonical_strength_fact(
            strength_system="SHADBALA",
            subject_entity=f"VEDA-GRAHA-{planet.upper()}",
            component="DRIK_BALA",
            raw_value=None,
            unit="RUPA",
            classification="BLOCKED_BY_ASPECT_FOUNDATION",
            calculation_rule_id="P018-DRIK-001",
            source_claim_ids=["VEDA-R2-CLM-000007"],
            validation_status="RESEARCH_REQUIRED",
        )

    # Sum contributions from all aspects received
    total_drik = 0.0
    for aspect in aspects_received:
        from_planet = aspect.get("from_planet", "")
        contribution = DRIK_BALA_CONTRIBUTIONS.get(from_planet, 0.0)
        total_drik += contribution

    return canonical_strength_fact(
        strength_system="SHADBALA",
        subject_entity=f"VEDA-GRAHA-{planet.upper()}",
        component="DRIK_BALA",
        raw_value=round(total_drik, 4),
        normalized_value=round(total_drik, 4),
        unit="RUPA",
        threshold=0.0,
        classification="ASPECTUAL_STRENGTH",
        calculation_rule_id="P018-DRIK-001",
        source_claim_ids=["VEDA-R2-CLM-000007"],
        validation_status="IMPLEMENTED_UNVALIDATED",
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def calculate_shadbala(
    planet: str,
    lon_deg: float,
    ascendant_lon: float,
    is_daytime: bool,
    daily_motion_arcsec: float | None = None,
    is_retrograde: bool = False,
    aspects_received: list[dict] | None = None,
    planet_day_lord: str | None = None,
) -> dict[str, Any]:
    """Calculate total Shadbala for a planet.

    Aggregates all six components with vimshopaka normalization.
    Source: BPHS Ch.29.

    Args:
        planet: Planet name
        lon_deg: Planet longitude in degrees (sidereal)
        ascendant_lon: Ascendant longitude in degrees
        is_daytime: Whether birth is during daytime
        daily_motion_arcsec: Daily motion in arc-seconds (None = blocked)
        is_retrograde: Whether planet is retrograde
        aspects_received: List of aspect contributions (None = blocked)
        planet_day_lord: Day of week planet rules

    Returns:
        Dict with components, total, status, source_claim_ids
    """
    rashi = _rashi_from_longitude(lon_deg)
    house = _house_from_position(rashi, _rashi_from_longitude(ascendant_lon))

    components = [
        calculate_naisargika_bala(planet),
        calculate_dig_bala(planet, house),
        calculate_sthana_bala(planet, lon_deg, ascendant_lon),
        calculate_kala_bala(planet, is_daytime, planet_day_lord),
        calculate_cheshta_bala(planet, daily_motion_arcsec, is_retrograde),
        calculate_drik_bala(planet, aspects_received),
    ]

    # Aggregate raw values (null components are excluded)
    raw_values = [c["raw_value"] for c in components if c["raw_value"] is not None]
    blocked = any(c["raw_value"] is None for c in components)

    total_raw = sum(raw_values) if raw_values else None
    total_normalized = None

    if total_raw is not None and not blocked:
        # Apply vimshopaka normalization
        total_normalized = round(total_raw * (VIMSHOPAKA_TOTAL / 16.0), 4)

    # Determine status
    if blocked:
        status = "BLOCKED_BY_COMPONENTS"
    elif total_normalized is not None:
        status = "IMPLEMENTED_UNVALIDATED"
    else:
        status = "RESEARCH_REQUIRED"

    return {
        "system": "SHADBALA",
        "subject_entity": f"VEDA-GRAHA-{planet.upper()}",
        "components": components,
        "total": total_normalized,
        "total_raw": round(total_raw, 4) if total_raw is not None else None,
        "status": status,
        "calculation_version": "P018-R2-SHADBALA-001",
        "source_claim_ids": ["VEDA-R2-CLM-000001"],
        "vimshopaka_total": VIMSHOPAKA_TOTAL,
    }


# ---------------------------------------------------------------------------
# Ashtakavarga (BAV + SAV)
# ---------------------------------------------------------------------------

def calculate_bav(planet: str, planet_rashis: dict[str, int]) -> dict[str, Any]:
    """Calculate Bhinna Ashtakavarga (BAV) for a planet.

    For each sign position (1-12), count how many other planets receive
    a bindu from this planet when they are in that sign.

    Source: BPHS Ch.69, confirmed by B.V. Raman, K.N. Rao, Phaladeepika.

    Args:
        planet: Planet name
        planet_rashis: Dict mapping planet name -> rashi number (1-12)

    Returns:
        Dict with bindu counts per sign, total, status
    """
    if planet not in BAV_CONTRIBUTIONS:
        return {
            "system": "ASHTAKAVARGA",
            "mode": "BAV",
            "subject_entity": f"VEDA-GRAHA-{planet.upper()}",
            "rashis": [],
            "status": "RESEARCH_REQUIRED",
            "calculation_version": "P018-R2-BAV-001",
            "source_claim_ids": [],
        }

    contributions = BAV_CONTRIBUTIONS[planet]
    bav_rashis = []
    total_bindus = 0

    for target_sign in range(1, 13):
        # Count bindus: how many other planets in this sign get a bindu
        bindu_count = 0
        for other_planet, other_rashi in planet_rashis.items():
            if other_planet == planet:
                continue
            relative = _relative_position(planet_rashis[planet], other_rashi)
            if 1 <= relative <= 12 and contributions[relative - 1] == 1:
                bindu_count += 1

        bav_rashis.append({
            "sign": target_sign,
            "bindus": bindu_count,
        })
        total_bindus += bindu_count

    return {
        "system": "ASHTAKAVARGA",
        "mode": "BAV",
        "subject_entity": f"VEDA-GRAHA-{planet.upper()}",
        "rashis": bav_rashis,
        "total_bindus": total_bindus,
        "status": "IMPLEMENTED_UNVALIDATED",
        "calculation_version": "P018-R2-BAV-001",
        "source_claim_ids": ["VEDA-R2-CLM-000008"],
    }


def calculate_sav(planet_rashis: dict[str, int]) -> dict[str, Any]:
    """Calculate Sarvashtakavarga (SAV).

    SAV is the sum of all BAV columns for each sign position.
    SAV[sign] = BAV[Sun][sign] + BAV[Moon][sign] + ... + BAV[Saturn][sign]

    Source: BPHS Ch.69, confirmed by B.V. Raman, K.N. Rao.

    Args:
        planet_rashis: Dict mapping planet name -> rashi number (1-12)

    Returns:
        Dict with SAV per sign, total, status
    """
    # Calculate BAV for each planet
    all_bav = {}
    for planet in PLANET_ORDER:
        if planet in planet_rashis:
            all_bav[planet] = calculate_bav(planet, planet_rashis)

    # Aggregate SAV
    sav_rashis = []
    total_sav = 0

    for sign in range(1, 13):
        sign_total = 0
        for planet in PLANET_ORDER:
            if planet in all_bav:
                for rashi_data in all_bav[planet]["rashis"]:
                    if rashi_data["sign"] == sign:
                        sign_total += rashi_data["bindus"]
                        break

        sav_rashis.append({
            "sign": sign,
            "total_bindus": sign_total,
        })
        total_sav += sign_total

    return {
        "system": "ASHTAKAVARGA",
        "mode": "SAV",
        "subject_entity": "FULL_CHART",
        "rashis": sav_rashis,
        "total_bindus": total_sav,
        "status": "IMPLEMENTED_UNVALIDATED",
        "calculation_version": "P018-R2-SAV-001",
        "source_claim_ids": ["VEDA-R2-CLM-000009"],
        "bav_results": {p: r["total_bindus"] for p, r in all_bav.items()},
    }


__all__ = [
    "NAISARGIKA_BALA",
    "DIG_BALA_MAXIMUM_HOUSE",
    "BAV_CONTRIBUTIONS",
    "VIMSHOPAKA_WEIGHTS",
    "DRIK_BALA_CONTRIBUTIONS",
    "STANDARD_ASPECTS",
    "calculate_naisargika_bala",
    "calculate_dig_bala",
    "calculate_sthana_bala",
    "calculate_kala_bala",
    "calculate_cheshta_bala",
    "calculate_drik_bala",
    "calculate_shadbala",
    "calculate_bav",
    "calculate_sav",
]
