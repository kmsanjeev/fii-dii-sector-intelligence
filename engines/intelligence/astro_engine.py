"""
AstroFinance Engine - Phase AF-2
Computes daily planetary positions and generates sector-level astro signals.

Knowledge sources:
  - A Trader's Guide to Financial Astrology (Pesavento & Smoleny, 2015)
  - Financial Astrology Almanac 2023 (planetary cycle frameworks)
  - Stock Market Astrology (Banerjee, 2009) -- Indian/NSE sector-planet mapping
  - Planetary Effects to Financial Market (eclipse & aspect timing)

Signal logic (strictly from book principles):
  BUY     -> Ruling planet direct + own/exaltation sign + Jupiter benefic aspect + Moon waxing
  HOLD    -> Ruling planet direct, neutral aspects, no eclipse, Moon neutral
  CAUTION -> Mercury retrograde (Mercury-ruled sectors) | Saturn hard aspect to ruler
  EXIT    -> Ruling planet retrograde | Mars/Saturn square or opposition to ruler
  AVOID   -> Eclipse in sector sign | Ketu eclipse active | multiple simultaneous malefics

Sidereal note (Phase ASTRO-FIX, 2026-07): sign placement now comes from
Swiss Ephemeris's native FLG_SIDEREAL calculation (swe.calc_ut), the same
path kundli_engine.py uses -- not PyEphem's tropical Ecliptic() longitude.
Two bugs existed before this fix: (1) PyEphem's Ecliptic(epoch=J2000) is
referenced to the fixed J2000 equinox, not precessed to the date, so
subtracting a date-of-epoch Lahiri ayanamsha left a ~26-year precession
error (~0.36 degrees as of 2026); (2) Rahu/Ketu used a hand-rolled MEAN
node formula while kundli_engine.py uses the TRUE node (up to ~1.5-2 degrees
apart). Both are fixed by delegating directly to Swiss Ephemeris. PyEphem
is still used below for retrograde-by-diff cross-checks, Moon phase
illumination %, and eclipse-zone proximity, where relative/frame-independent
quantities make the tropical-vs-sidereal distinction immaterial.

Outputs:
  data/intelligence/astro_signals.csv         -- sector-level astro scores
  data/intelligence/market_astro_context.json -- market-level planetary pulse
"""

from __future__ import annotations
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path

import ephem
import pandas as pd

try:
    import swisseph as swe
except ImportError:
    raise ImportError(
        "pyswisseph not installed. Run: py -3.11 -m pip install pyswisseph"
    )

from engines.common import config as cfg
from engines.common.astronomy_policy import calc_ut as governed_calc_ut
from engines.common.logger import get_logger

logger = get_logger(__name__)

# Dublin JD (PyEphem epoch, 1899/12/31 12:00 UT) -> standard Julian Day offset
DUBLIN_JD_OFFSET = 2415020.0

INTEL = cfg.INTELLIGENCE_DIR
ASTRO_SIGNALS_PATH = INTEL / "astro_signals.csv"
ASTRO_CONTEXT_PATH = INTEL / "market_astro_context.json"

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_RULERS = {
    "Aries": "Mars",     "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",    "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",    "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
}

# Each planet's exaltation and debilitation sign
EXALTATION = {
    "Sun": "Aries",    "Moon": "Taurus",    "Mercury": "Virgo",
    "Venus": "Pisces", "Mars": "Capricorn", "Jupiter": "Cancer",
    "Saturn": "Libra", "Rahu": "Gemini",    "Ketu": "Sagittarius",
}
DEBILITATION = {
    "Sun": "Libra",    "Moon": "Scorpio",    "Mercury": "Pisces",
    "Venus": "Virgo",  "Mars": "Cancer",     "Jupiter": "Capricorn",
    "Saturn": "Aries", "Rahu": "Sagittarius", "Ketu": "Gemini",
}

# Planet-sector ruling mapping (Banerjee Vedic/Indian system for NSE)
SECTOR_RULERS: dict[str, list[str]] = {
    "BANKING":       ["Jupiter"],
    "AMC":           ["Jupiter", "Mercury"],
    "IT":            ["Rahu", "Mercury"],
    "TECHNOLOGY":    ["Rahu", "Mercury", "Uranus"],
    "TELECOM":       ["Mercury", "Rahu"],
    "AUTO":          ["Mars"],
    "CAPITAL_GOODS": ["Mars", "Saturn"],
    "METAL":         ["Mars", "Saturn"],
    "CEMENT":        ["Saturn"],
    "CHEMICALS":     ["Saturn", "Mars"],
    "PHARMA":        ["Saturn", "Sun"],
    "HEALTHCARE":    ["Saturn", "Sun"],
    "FMCG":          ["Moon", "Venus"],
    "RETAIL":        ["Moon", "Mercury"],
    "HOSPITALITY":   ["Moon", "Venus"],
    "TEXTILE":       ["Moon", "Venus"],
    "GEMS_JEWELRY":  ["Venus"],
    "SUGAR":         ["Moon", "Venus"],
    "ENERGY":        ["Sun", "Mars"],
    "POWER":         ["Sun", "Mars"],
    "OIL_GAS":       ["Neptune", "Ketu"],
    "REALTY":        ["Saturn", "Mars"],
    "INFRASTRUCTURE":["Saturn", "Mars"],
    "MEDIA":         ["Mercury", "Moon"],
    "AVIATION":      ["Mercury", "Rahu"],
    "LOGISTICS":     ["Mercury", "Saturn"],
    "SHIPPING":      ["Neptune", "Moon"],
    "AGRICULTURE":   ["Moon", "Mercury"],
    "DIVERSIFIED":   ["Jupiter"],
    "AEROSPACE":     ["Sun", "Mars", "Rahu"],
    "UNCATEGORIZED": ["Jupiter"],
}

# Malefic planets (default negative when in hard aspect)
NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu"}
# Benefic planets (default positive influence)
NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury"}

# Aspect angles with orbs (degrees, orb)
ASPECTS = {
    "Conjunction":  (0,   8),
    "Sextile":      (60,  6),
    "Square":       (90,  8),
    "Trine":        (120, 8),
    "Opposition":   (180, 8),
    "Quincunx":     (150, 4),
}

# Aspect polarity for financial use
ASPECT_POLARITY = {
    "Conjunction": "variable",  # depends on planets
    "Sextile":     "benefic",
    "Square":      "malefic",
    "Trine":       "benefic",
    "Opposition":  "malefic",
    "Quincunx":    "mild_malefic",
}


class AstroEngine:
    """
    Computes daily planetary positions and generates sector-level astro signals
    for the NSE market using Indian/Vedic planet-sector mapping.
    """

    def __init__(self):
        swe.set_sid_mode(swe.SIDM_LAHIRI)

    def _ayanamsha(self, ephem_date: "ephem.Date") -> float:
        """Lahiri ayanamsha (degrees) for the given PyEphem date, via Swiss Ephemeris."""
        jd_ut = float(ephem_date) + DUBLIN_JD_OFFSET
        return swe.get_ayanamsa_ut(jd_ut)

    def run(self) -> bool:
        logger.info("[AstroEngine] Starting planetary computation")
        try:
            today = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            positions = self._compute_positions(today)
            aspects = self._compute_aspects(positions)
            moon_info = self._compute_moon_phase(today)
            eclipse_info = self._check_eclipse_proximity(today)
            market_pulse = self._compute_market_pulse(positions, aspects, moon_info, eclipse_info)

            sector_df = self._compute_sector_signals(positions, aspects, moon_info, eclipse_info)

            self._save_sector_signals(sector_df)
            ayanamsha = self._ayanamsha(ephem.Date(today))
            self._save_market_context(market_pulse, positions, today, ayanamsha)

            logger.info(f"[AstroEngine] Complete -- {len(sector_df)} sectors, {today}")
            return True
        except Exception as e:
            logger.error(f"[AstroEngine] Failed: {e}")
            raise

    _PLANET_IDS = {
        "Sun": 0, "Moon": 1, "Mercury": 2, "Venus": 3, "Mars": 4,
        "Jupiter": 5, "Saturn": 6, "Uranus": 7, "Neptune": 8,
    }

    def _compute_positions(self, date_str: str) -> dict[str, dict]:
        """
        Compute sidereal (Lahiri) ecliptic longitude, zodiac sign, and
        retrograde status for all planets via Swiss Ephemeris FLG_SIDEREAL --
        the same calculation path kundli_engine.py uses.
        Returns dict: planet_name -> {lon, sign, retrograde, sign_strength, state_label}
        """
        ephem_date = ephem.Date(date_str)
        jd_ut = float(ephem_date) + DUBLIN_JD_OFFSET
        flags = swe.FLG_SIDEREAL | swe.FLG_SPEED

        positions: dict[str, dict] = {}
        for name, pid in self._PLANET_IDS.items():
            xx, _ = governed_calc_ut(swe, jd_ut, pid, flags)
            lon = xx[0] % 360
            retrograde = xx[3] < 0  # longitude speed, deg/day; negative = retrograde

            sign_idx = int(lon / 30)
            sign = SIGNS[sign_idx]
            sign_strength = self._sign_strength(name, sign)
            state_label = self._state_label(name, sign, retrograde)

            positions[name] = {
                "lon": round(lon, 2),
                "sign": sign,
                "deg_in_sign": round(lon % 30, 2),
                "retrograde": retrograde,
                "sign_strength": sign_strength,
                "state_label": state_label,
            }

        # Rahu (True Node) and Ketu -- same convention as kundli_engine.py
        xx, _ = governed_calc_ut(swe, jd_ut, swe.TRUE_NODE, flags)
        rahu_lon = xx[0] % 360
        ketu_lon = (rahu_lon + 180) % 360
        for name, lon in [("Rahu", rahu_lon), ("Ketu", ketu_lon)]:
            sign = SIGNS[int(lon / 30)]
            sign_strength = self._sign_strength(name, sign)
            positions[name] = {
                "lon": round(lon, 2),
                "sign": sign,
                "deg_in_sign": round(lon % 30, 2),
                "retrograde": True,  # Nodes are always retrograde by convention
                "sign_strength": sign_strength,
                "state_label": self._state_label(name, sign, True),
            }

        return positions

    def _compute_rahu(self, ephem_date: ephem.Date) -> float:
        """
        Compute Mean North Node (Rahu) ecliptic longitude.
        Formula: Omega = 125.0445479 - 1934.136261 * T (J2000 centuries)
        """
        jd = ephem_date + 2415020  # Julian date offset for ephem
        T = (ephem_date + 2415020 - 2451545.0) / 36525.0
        omega = (125.0445479 - 1934.136261 * T) % 360
        if omega < 0:
            omega += 360
        return omega

    def _sign_strength(self, planet: str, sign: str) -> int:
        """
        Score planet strength in current sign.
          +4  exaltation
          +3  own sign (sign ruled by same planet)
           0  neutral
          -2  enemy sign (simplified: natural malefics in benefic signs, vice versa)
          -3  debilitation
        """
        if EXALTATION.get(planet) == sign:
            return 4
        if DEBILITATION.get(planet) == sign:
            return -3
        if SIGN_RULERS.get(sign) == planet:
            return 3
        # Friendship approximation: Jupiter in signs ruled by other benefics = +1
        sign_ruler = SIGN_RULERS.get(sign, "")
        if planet in NATURAL_BENEFICS and sign_ruler in NATURAL_BENEFICS:
            return 1
        if planet in NATURAL_MALEFICS and sign_ruler in NATURAL_MALEFICS:
            return 1
        if planet in NATURAL_MALEFICS and sign_ruler in NATURAL_BENEFICS:
            return -1
        return 0

    def _state_label(self, planet: str, sign: str, retrograde: bool) -> str:
        if retrograde and planet not in ("Rahu", "Ketu"):
            return "RETROGRADE"
        s = self._sign_strength(planet, sign)
        if s >= 4:
            return "EXALTED"
        if s >= 3:
            return "OWN_SIGN"
        if s <= -3:
            return "DEBILITATED"
        if s == -2:
            return "WEAK"
        return "NEUTRAL"

    def _compute_aspects(self, positions: dict[str, dict]) -> list[dict]:
        """
        Compute aspects between all planet pairs.
        Returns list of {p1, p2, aspect, orb, polarity, score}
        """
        planets = list(positions.keys())
        aspects_found = []

        for i in range(len(planets)):
            for j in range(i + 1, len(planets)):
                p1, p2 = planets[i], planets[j]
                lon1 = positions[p1]["lon"]
                lon2 = positions[p2]["lon"]
                diff = abs(lon1 - lon2)
                if diff > 180:
                    diff = 360 - diff

                for asp_name, (asp_deg, orb) in ASPECTS.items():
                    if abs(diff - asp_deg) <= orb:
                        actual_orb = round(abs(diff - asp_deg), 2)
                        polarity = self._aspect_polarity(p1, p2, asp_name)
                        score = self._aspect_score(p1, p2, asp_name, actual_orb, orb)
                        aspects_found.append({
                            "p1": p1, "p2": p2,
                            "aspect": asp_name,
                            "orb": actual_orb,
                            "polarity": polarity,
                            "score": score,
                        })

        return aspects_found

    def _aspect_polarity(self, p1: str, p2: str, aspect: str) -> str:
        """Determine if aspect is bullish/bearish from financial astrology perspective."""
        base = ASPECT_POLARITY.get(aspect, "neutral")
        if aspect == "Conjunction":
            # Jupiter conjunct anything = bullish; Saturn/Mars conjunct = bearish
            if "Jupiter" in (p1, p2):
                return "benefic"
            if "Saturn" in (p1, p2) or "Mars" in (p1, p2):
                return "malefic"
            if "Venus" in (p1, p2):
                return "benefic"
            return "neutral"
        return base

    def _aspect_score(self, p1: str, p2: str, aspect: str, orb: float, max_orb: float) -> float:
        """Score -3 to +3 based on aspect and planets involved."""
        polarity = self._aspect_polarity(p1, p2, aspect)
        strength = 1.0 - (orb / max_orb)  # closer = stronger

        base_scores = {
            "benefic":      3,
            "malefic":      -3,
            "mild_malefic": -1.5,
            "variable":     0,
            "neutral":      0,
        }
        base = base_scores.get(polarity, 0)

        # Jupiter amplifies benefic aspects
        if "Jupiter" in (p1, p2) and polarity == "benefic":
            base = min(4, base * 1.5)
        # Saturn/Mars amplify malefic aspects
        if "Saturn" in (p1, p2) and polarity == "malefic":
            base = max(-4, base * 1.5)

        return round(base * strength, 2)

    def _compute_moon_phase(self, date_str: str) -> dict:
        """Compute Moon phase and waxing/waning status."""
        moon = ephem.Moon(date_str)
        sun = ephem.Sun(date_str)
        illumination = moon.phase  # 0-100%

        if illumination < 5:
            phase_name = "NEW_MOON"
        elif illumination < 45:
            phase_name = "WAXING_CRESCENT"
        elif illumination < 55:
            phase_name = "FIRST_QUARTER" if illumination < 50 else "LAST_QUARTER"
        elif illumination < 95:
            # Determine waxing or waning by comparing yesterday's illumination
            moon_y = ephem.Moon(ephem.Date(ephem.Date(date_str) - 1))
            waxing = moon.phase > moon_y.phase
            phase_name = "WAXING_GIBBOUS" if waxing else "WANING_GIBBOUS"
        else:
            phase_name = "FULL_MOON"

        waxing = illumination < 50 or (illumination >= 50 and phase_name in (
            "WAXING_CRESCENT", "WAXING_GIBBOUS", "FIRST_QUARTER"
        ))

        # Score: +2 new moon area, +1 waxing, -1 full moon (top), -2 waning
        if phase_name == "NEW_MOON":
            score = 1  # potential reversal zone, neutral
        elif phase_name == "FULL_MOON":
            score = -1  # potential reversal zone
        elif phase_name in ("WAXING_CRESCENT", "FIRST_QUARTER", "WAXING_GIBBOUS"):
            score = 2
        else:
            score = -1

        return {
            "phase_name": phase_name,
            "illumination_pct": round(float(illumination), 1),
            "waxing": illumination < 50,
            "score": score,
        }

    def _check_eclipse_proximity(self, date_str: str) -> dict:
        """
        Check proximity to a solar/lunar eclipse.
        Returns eclipse_flag and estimated type (RAHU=uptrend, KETU=downtrend per Banerjee).
        Eclipses occur when New/Full Moon is near the lunar nodes.
        """
        moon = ephem.Moon(date_str)
        sun = ephem.Sun(date_str)
        moon.compute(date_str)
        sun.compute(date_str)

        moon_ecl = ephem.Ecliptic(moon, epoch=ephem.J2000)
        sun_ecl = ephem.Ecliptic(sun, epoch=ephem.J2000)

        moon_lon = math.degrees(moon_ecl.lon) % 360
        sun_lon = math.degrees(sun_ecl.lon) % 360

        rahu_lon = self._compute_rahu(ephem.Date(date_str))
        ketu_lon = (rahu_lon + 180) % 360

        # Check if moon/sun is within 18 degrees of nodes (eclipse zone)
        def near_node(planet_lon: float, node_lon: float, threshold: float = 18.0) -> bool:
            diff = abs((planet_lon - node_lon + 180) % 360 - 180)
            return diff <= threshold

        near_rahu = near_node(moon_lon, rahu_lon) or near_node(sun_lon, rahu_lon)
        near_ketu = near_node(moon_lon, ketu_lon) or near_node(sun_lon, ketu_lon)

        # New Moon proximity (solar eclipse possible) or Full Moon (lunar eclipse)
        sun_moon_diff = abs((moon_lon - sun_lon + 180) % 360 - 180)
        new_moon_zone = sun_moon_diff < 20
        full_moon_zone = abs(sun_moon_diff - 180) < 20

        eclipse_active = (near_rahu or near_ketu) and (new_moon_zone or full_moon_zone)

        if eclipse_active:
            eclipse_type = "RAHU" if near_rahu else "KETU"
            # Per Banerjee: Rahu eclipse = uptrend, Ketu eclipse = downtrend
            eclipse_signal = "UPTREND_POTENTIAL" if eclipse_type == "RAHU" else "DOWNTREND_WARNING"
        else:
            eclipse_type = None
            eclipse_signal = "NONE"

        return {
            "eclipse_active": eclipse_active,
            "eclipse_type": eclipse_type,
            "eclipse_signal": eclipse_signal,
            "near_eclipse_zone": near_rahu or near_ketu,
        }

    def _compute_market_pulse(
        self, positions: dict, aspects: list[dict],
        moon_info: dict, eclipse_info: dict
    ) -> dict:
        """
        Compute market-level astro pulse (Jupiter/Saturn cycle, Mercury, Venus status).
        Returns dict with overall market_astro_signal.
        """
        mercury_retrograde = positions.get("Mercury", {}).get("retrograde", False)
        venus_retrograde = positions.get("Venus", {}).get("retrograde", False)
        mars_retrograde = positions.get("Mars", {}).get("retrograde", False)
        jupiter_sign = positions.get("Jupiter", {}).get("sign", "")
        saturn_sign = positions.get("Saturn", {}).get("sign", "")
        jupiter_state = positions.get("Jupiter", {}).get("state_label", "NEUTRAL")
        saturn_state = positions.get("Saturn", {}).get("state_label", "NEUTRAL")

        # Jupiter/Saturn aspect (Gann Master Cycle key signal)
        js_aspect = None
        for asp in aspects:
            if set([asp["p1"], asp["p2"]]) == {"Jupiter", "Saturn"}:
                js_aspect = asp
                break

        # Bradley Siderograph-style market score (simplified)
        # Sum all benefic aspects minus malefic aspects involving key planets
        market_score = 0
        key_planets = {"Jupiter", "Saturn", "Mars", "Venus", "Mercury", "Sun", "Moon"}
        for asp in aspects:
            if asp["p1"] in key_planets or asp["p2"] in key_planets:
                market_score += asp["score"]

        market_score += moon_info["score"]

        # Penalties for retrogrades
        if mercury_retrograde:
            market_score -= 1
        if venus_retrograde:
            market_score -= 2  # stronger reversal signal per Almanac
        if mars_retrograde:
            market_score -= 1

        # Normalize to -100 to +100
        market_score = max(-100, min(100, market_score * 10))

        # Overall market signal
        if eclipse_info["eclipse_active"] and eclipse_info["eclipse_type"] == "KETU":
            market_astro_signal = "BEARISH"
        elif eclipse_info["eclipse_active"] and eclipse_info["eclipse_type"] == "RAHU":
            market_astro_signal = "BULLISH"
        elif market_score >= 20:
            market_astro_signal = "BULLISH"
        elif market_score >= 5:
            market_astro_signal = "NEUTRAL_POSITIVE"
        elif market_score >= -10:
            market_astro_signal = "NEUTRAL"
        elif market_score >= -25:
            market_astro_signal = "CAUTION"
        else:
            market_astro_signal = "BEARISH"

        # Moon phase market note
        phase = moon_info["phase_name"]
        if phase in ("NEW_MOON", "FULL_MOON"):
            reversal_note = f"{phase} -- potential trend reversal zone"
        else:
            reversal_note = None

        return {
            "market_astro_score": round(market_score, 1),
            "market_astro_signal": market_astro_signal,
            "mercury_retrograde": mercury_retrograde,
            "venus_retrograde": venus_retrograde,
            "mars_retrograde": mars_retrograde,
            "jupiter_sign": jupiter_sign,
            "jupiter_state": jupiter_state,
            "saturn_sign": saturn_sign,
            "saturn_state": saturn_state,
            "jupiter_saturn_aspect": js_aspect["aspect"] if js_aspect else "None",
            "moon_phase": moon_info["phase_name"],
            "moon_illumination": moon_info["illumination_pct"],
            "eclipse_active": eclipse_info["eclipse_active"],
            "eclipse_type": eclipse_info["eclipse_type"],
            "eclipse_signal": eclipse_info["eclipse_signal"],
            "reversal_note": reversal_note,
        }

    def _compute_sector_signals(
        self, positions: dict, aspects: list[dict],
        moon_info: dict, eclipse_info: dict
    ) -> pd.DataFrame:
        """
        Compute per-sector astro score and signal.
        """
        sectors = list(SECTOR_RULERS.keys())
        rows = []

        for sector in sectors:
            ruling_planets = SECTOR_RULERS.get(sector, ["Jupiter"])
            primary_planet = ruling_planets[0]

            # Score for each ruling planet
            planet_scores = []
            for planet in ruling_planets:
                pos = positions.get(planet)
                if pos is None:
                    continue

                score = pos["sign_strength"] * 2.0  # base strength

                # Retrograde penalty (per books)
                if pos["retrograde"] and planet not in ("Rahu", "Ketu"):
                    score -= 3.0

                # Aspect contributions from other planets
                for asp in aspects:
                    if planet in (asp["p1"], asp["p2"]):
                        score += asp["score"] * 0.5

                planet_scores.append(score)

            raw_score = sum(planet_scores) / len(planet_scores) if planet_scores else 0

            # Moon contribution for Moon-ruled sectors
            if "Moon" in ruling_planets:
                raw_score += moon_info["score"] * 0.5

            # Eclipse penalty/boost
            if eclipse_info["eclipse_active"]:
                if eclipse_info["eclipse_type"] == "KETU":
                    raw_score -= 3
                else:
                    raw_score += 2

            # Normalize to -100 to +100
            astro_score = max(-100, min(100, raw_score * 10))

            # Determine signal
            primary_pos = positions.get(primary_planet, {})
            retrograde = primary_pos.get("retrograde", False)
            state = primary_pos.get("state_label", "NEUTRAL")

            # Plain-English reason text for each condition
            mercury_retro = positions.get("Mercury", {}).get("retrograde", False)
            sign_name = primary_pos.get("sign", "")
            if primary_planet in ("Mercury", "Rahu") and mercury_retro:
                action = "CAUTION"
                reason = (
                    f"Mercury is moving backward (retrograde) today -- this disrupts "
                    f"communication, contracts, and decision-making in {sector} stocks. "
                    f"Avoid opening new positions until Mercury turns direct."
                )
            elif retrograde and primary_planet not in ("Rahu", "Ketu"):
                action = "EXIT"
                reason = (
                    f"{primary_planet} -- the planet governing {sector} stocks -- is retrograde "
                    f"(moving backward) in {sign_name}. A retrograde ruling planet weakens sector "
                    f"momentum and signals a higher risk of corrections or consolidation."
                )
            elif state == "DEBILITATED":
                action = "AVOID"
                reason = (
                    f"{primary_planet} (ruler of {sector}) is in {sign_name} -- its weakest zodiac "
                    f"position, where it has minimal positive energy to support sector performance. "
                    f"Strong astrological headwind for {sector} stocks."
                )
            elif eclipse_info["eclipse_active"] and eclipse_info["eclipse_type"] == "KETU":
                action = "AVOID"
                reason = (
                    "A Ketu eclipse is active -- this signals sudden downward pressure and "
                    "uncertainty across sectors. High-risk zone; avoid new positions and "
                    "consider reducing exposure."
                )
            elif eclipse_info["eclipse_active"] and eclipse_info["eclipse_type"] == "RAHU":
                action = "HOLD"
                reason = (
                    "A Rahu eclipse is active -- uptrend potential exists but volatility is "
                    "elevated. Sudden reversals are possible. Hold existing positions with "
                    "tight stop-losses; avoid chasing momentum."
                )
            elif astro_score >= 25:
                action = "BUY"
                state_desc = {
                    "EXALTED": "at peak strength", "OWN_SIGN": "strong in its own sign"
                }.get(state, "in a favorable position")
                reason = (
                    f"{primary_planet} is {state_desc} in {sign_name} and receiving supportive "
                    f"planetary aspects. Favorable astrological conditions -- a planetary tailwind "
                    f"for {sector} stocks."
                )
            elif astro_score >= 5:
                action = "HOLD"
                reason = (
                    f"Planetary alignment for {sector} is mildly positive. {primary_planet} in "
                    f"{sign_name} faces no major obstacles. Suitable for holding existing "
                    f"positions; no strong entry or exit signal from astrology."
                )
            elif astro_score >= -15:
                action = "HOLD"
                reason = (
                    f"Mixed planetary signals for {sector}: {primary_planet} in {sign_name} "
                    f"faces both supportive and challenging aspects. No clear directional bias "
                    f"from astrology -- monitor price action carefully."
                )
            elif astro_score >= -35:
                action = "CAUTION"
                reason = (
                    f"{primary_planet} (ruler of {sector}) in {sign_name} is under pressure from "
                    f"challenging planetary alignments today. The sector may underperform the "
                    f"broader market. Consider reducing position sizes or tightening stop-losses."
                )
            else:
                action = "EXIT"
                reason = (
                    f"{primary_planet} (ruler of {sector}) in {sign_name} faces severe stress "
                    f"from multiple adverse planetary positions. Strong astrological headwind -- "
                    f"Vedic astrology signals caution or reduced exposure for {sector} stocks."
                )

            # Build key aspects summary
            key_asps = []
            for asp in aspects:
                if primary_planet in (asp["p1"], asp["p2"]):
                    other = asp["p2"] if asp["p1"] == primary_planet else asp["p1"]
                    key_asps.append(f"{other} {asp['aspect']} ({asp['polarity']})")

            rows.append({
                "sector":          sector,
                "ruling_planets":  ", ".join(ruling_planets),
                "primary_planet":  primary_planet,
                "planet_sign":     primary_pos.get("sign", ""),
                "planet_state":    state,
                "planet_retrograde": retrograde,
                "key_aspects":     "; ".join(key_asps[:3]) if key_asps else "None",
                "astro_score":     round(astro_score, 1),
                "astro_action":    action,
                "astro_reason":    reason,
                "moon_phase":      moon_info["phase_name"],
                "eclipse_active":  eclipse_info["eclipse_active"],
                "as_of_date":      datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

        return pd.DataFrame(rows)

    def _save_sector_signals(self, df: pd.DataFrame):
        if df.empty:
            logger.warning("[AstroEngine] Empty sector signals -- skipping write")
            return
        tmp = ASTRO_SIGNALS_PATH.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(ASTRO_SIGNALS_PATH))
        logger.info(f"[AstroEngine] Saved {len(df)} sector signals to {ASTRO_SIGNALS_PATH}")

    def _save_market_context(self, pulse: dict, positions: dict, date_str: str, ayanamsha: float):
        pulse["planet_positions"] = {
            name: {
                "sign": pos["sign"],
                "deg": f"{pos['deg_in_sign']:.1f}",
                "retrograde": pos["retrograde"],
                "state": pos["state_label"],
            }
            for name, pos in positions.items()
        }
        pulse["computed_date"] = date_str.replace("/", "-")
        pulse["ayanamsha"] = "Lahiri"
        pulse["ayanamsha_deg"] = round(ayanamsha, 4)

        tmp = ASTRO_CONTEXT_PATH.with_suffix(".tmp.json")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(pulse, f, indent=2, default=str)
        shutil.move(str(tmp), str(ASTRO_CONTEXT_PATH))
        logger.info(f"[AstroEngine] Saved market astro context to {ASTRO_CONTEXT_PATH}")


if __name__ == "__main__":
    engine = AstroEngine()
    engine.run()
