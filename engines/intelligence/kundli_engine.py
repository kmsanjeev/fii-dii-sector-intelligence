"""
Kundli Engine — Phase KU-1
Computes Vedic natal charts (Kundli) for stocks, companies, humans, and countries
using the Swiss Ephemeris (pyswisseph) with Lahiri ayanamsha.

Key features:
- All 9 Vedic grahas + Rahu/Ketu (True Node)
- Whole Sign house system (Parashari standard)
- D-1 through D-12 + D-16, D-20, D-30, D-60 divisional charts
- Vimshottari Dasha/Antardasha/Pratyantardasha (5 levels)
- Planetary dignities: exalted / moolatrikona / own / neutral / debilitated
- Special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10)
- Major Yoga detection (Dhana, Raja, Gaja-Kesari, Viparita, Neecha-Bhanga)
- Financial house analysis (2H wealth, 5H speculation, 8H volatility, 11H gains)
- Transit analysis: current positions vs natal
- Financial signal: BUY / HOLD / CAUTION / EXIT / AVOID with score

Run standalone:
  py -3.11 -m engines.intelligence.kundli_engine
"""

from __future__ import annotations
import json
import math
import sys
import time as _time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Zodiac signs ──────────────────────────────────────────────────────────────
SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]
SIGN_SYMBOLS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']

# Sign modalities for D9 Navamsa calculation
MOVABLE_SIGNS = {0, 3, 6, 9}    # Aries, Cancer, Libra, Capricorn
FIXED_SIGNS   = {1, 4, 7, 10}   # Taurus, Leo, Scorpio, Aquarius
DUAL_SIGNS    = {2, 5, 8, 11}   # Gemini, Virgo, Sagittarius, Pisces

# Ruling lords of each sign
SIGN_LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
              'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

# Element groupings
FIRE_SIGNS  = {0, 4, 8}   # Aries, Leo, Sagittarius
EARTH_SIGNS = {1, 5, 9}   # Taurus, Virgo, Capricorn
AIR_SIGNS   = {2, 6, 10}  # Gemini, Libra, Aquarius
WATER_SIGNS = {3, 7, 11}  # Cancer, Scorpio, Pisces

# ── 27 Nakshatras ────────────────────────────────────────────────────────────
# (name, start_deg, end_deg, dasha_lord, symbol)
NAKSHATRAS = [
    ('Ashwini',          0.000,  13.333, 'Ketu',    'Horse Head'),
    ('Bharani',         13.333,  26.667, 'Venus',   'Yoni / Womb'),
    ('Krittika',        26.667,  40.000, 'Sun',     'Flame / Razor'),
    ('Rohini',          40.000,  53.333, 'Moon',    'Chariot / Ox'),
    ('Mrigashira',      53.333,  66.667, 'Mars',    'Deer Head'),
    ('Ardra',           66.667,  80.000, 'Rahu',    'Teardrop / Diamond'),
    ('Punarvasu',       80.000,  93.333, 'Jupiter', 'Bow & Quiver'),
    ('Pushya',          93.333, 106.667, 'Saturn',  'Lotus / Udder'),
    ('Ashlesha',       106.667, 120.000, 'Mercury', 'Coiled Serpent'),
    ('Magha',          120.000, 133.333, 'Ketu',    'Palanquin / Throne'),
    ('Purva Phalguni', 133.333, 146.667, 'Venus',   'Fig Tree / Swinging Hammock'),
    ('Uttara Phalguni',146.667, 160.000, 'Sun',     'Fig Tree / Bed'),
    ('Hasta',          160.000, 173.333, 'Moon',    'Palm of Hand'),
    ('Chitra',         173.333, 186.667, 'Mars',    'Bright Pearl / Jewel'),
    ('Swati',          186.667, 200.000, 'Rahu',    'Coral / Young Shoot'),
    ('Vishakha',       200.000, 213.333, 'Jupiter', 'Triumphal Arch'),
    ('Anuradha',       213.333, 226.667, 'Saturn',  'Lotus / Umbrella'),
    ('Jyeshtha',       226.667, 240.000, 'Mercury', 'Circular Talisman'),
    ('Mula',           240.000, 253.333, 'Ketu',    'Bunch of Roots'),
    ('Purva Ashadha',  253.333, 266.667, 'Venus',   'Elephant Tusk / Fan'),
    ('Uttara Ashadha', 266.667, 280.000, 'Sun',     'Elephant Tusk / Small Bed'),
    ('Shravana',       280.000, 293.333, 'Moon',    'Three Footprints / Ear'),
    ('Dhanishtha',     293.333, 306.667, 'Mars',    'Drum / Flute'),
    ('Shatabhisha',    306.667, 320.000, 'Rahu',    'Empty Circle / 100 Stars'),
    ('Purva Bhadra',   320.000, 333.333, 'Jupiter', 'Front of Funeral Cot'),
    ('Uttara Bhadra',  333.333, 346.667, 'Saturn',  'Back of Funeral Cot'),
    ('Revati',         346.667, 360.000, 'Mercury', 'Fish / Drum'),
]

# ── Vimshottari Dasha ─────────────────────────────────────────────────────────
VIMSHOTTARI_SEQ   = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
VIMSHOTTARI_YEARS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,
                     'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}
VIMSHOTTARI_TOTAL = 120.0

# ── Planetary dignities ───────────────────────────────────────────────────────
# Exaltation: (sign_index, exact_degree)
EXALTATION = {
    'Sun': (0, 10), 'Moon': (1, 3), 'Mars': (9, 28), 'Mercury': (5, 15),
    'Jupiter': (3, 5), 'Venus': (11, 27), 'Saturn': (6, 20),
    'Rahu': (1, 20), 'Ketu': (7, 20),
}
# Debilitation sign index
DEBILITATION = {
    'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
    'Jupiter': 9, 'Venus': 5, 'Saturn': 0,
    'Rahu': 7, 'Ketu': 1,
}
# Own signs
OWN_SIGNS = {
    'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
    'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10],
}
# Moolatrikona (partial own sign, stronger)
MOOLATRIKONA = {
    'Sun': (4, 0, 20), 'Moon': (1, 4, 30), 'Mars': (0, 0, 12),
    'Mercury': (5, 16, 20), 'Jupiter': (8, 0, 10), 'Venus': (6, 0, 15),
    'Saturn': (10, 0, 20),
}
# Planetary friendships
FRIENDS = {
    'Sun':     ['Moon','Mars','Jupiter'],
    'Moon':    ['Sun','Mercury'],
    'Mars':    ['Sun','Moon','Jupiter'],
    'Mercury': ['Sun','Venus'],
    'Jupiter': ['Sun','Moon','Mars'],
    'Venus':   ['Mercury','Saturn'],
    'Saturn':  ['Mercury','Venus'],
    'Rahu':    ['Venus','Saturn'],
    'Ketu':    ['Mars','Venus'],
}
ENEMIES = {
    'Sun':     ['Venus','Saturn'],
    'Moon':    ['None'],
    'Mars':    ['Mercury'],
    'Mercury': ['Moon'],
    'Jupiter': ['Mercury','Venus','Saturn'],
    'Venus':   ['Sun','Moon'],
    'Saturn':  ['Sun','Moon','Mars'],
    'Rahu':    ['Sun','Moon','Mars'],
    'Ketu':    ['Sun','Moon'],
}

# ── Special aspects (beyond universal 7th aspect) ────────────────────────────
SPECIAL_ASPECTS = {
    'Mars':    [4, 8],     # 4th and 8th houses from Mars
    'Jupiter': [5, 9],     # 5th and 9th houses from Jupiter
    'Saturn':  [3, 10],    # 3rd and 10th houses from Saturn
    'Rahu':    [5, 9],     # 5th and 9th (Parashari tradition)
    'Ketu':    [5, 9],
}

# ── Stock exchange registry ────────────────────────────────────────────────────
# NSE/BSE ipo_hour=10:00 (Phase ASTRO-FIX spike, 2026-07-15): this is NOT an
# arbitrary approximation. Per NSE's mandatory "Special Pre-Open Session"
# procedure for every new listing (SEBI-mandated, applies market-wide) --
# order collection/price discovery runs 09:00-09:45/09:55 IST, and normal
# continuous trading (the moment the stock actually becomes tradable at a
# market-discovered price) commences at 10:00 IST. NSE does not publish a
# more precise first-trade timestamp than this via any public API or
# nselib -- 10:00 is the genuine session-open moment, not a guess. The one
# known exception is a rare ceremonial "Muhurat listing" for a marquee IPO
# (special bell-ringing session with its own announced timing) -- these are
# uncommon enough that no per-symbol override exists yet; revisit if one is
# encountered.
EXCHANGES = {
    'NSE':  {'city': 'Mumbai',        'lat': 18.9340,   'lon': 72.8296,   'tz': 'Asia/Kolkata',      'ipo_hour': 10, 'ipo_min': 0},
    'BSE':  {'city': 'Mumbai',        'lat': 18.9340,   'lon': 72.8296,   'tz': 'Asia/Kolkata',      'ipo_hour': 10, 'ipo_min': 0},
    'NYSE': {'city': 'New York',      'lat': 40.7069,   'lon': -74.0089,  'tz': 'America/New_York',  'ipo_hour':  9, 'ipo_min': 30},
    'NASDAQ':{'city':'New York',      'lat': 40.7580,   'lon': -73.9855,  'tz': 'America/New_York',  'ipo_hour':  9, 'ipo_min': 30},
    'LSE':  {'city': 'London',        'lat': 51.5142,   'lon': -0.0931,   'tz': 'Europe/London',     'ipo_hour':  8, 'ipo_min': 0},
    'TSE':  {'city': 'Tokyo',         'lat': 35.6895,   'lon': 139.6917,  'tz': 'Asia/Tokyo',        'ipo_hour':  9, 'ipo_min': 0},
    'SSE':  {'city': 'Shanghai',      'lat': 31.2304,   'lon': 121.4737,  'tz': 'Asia/Shanghai',     'ipo_hour':  9, 'ipo_min': 30},
    'HKEX': {'city': 'Hong Kong',     'lat': 22.2819,   'lon': 114.1581,  'tz': 'Asia/Hong_Kong',    'ipo_hour':  9, 'ipo_min': 30},
    'SGX':  {'city': 'Singapore',     'lat':  1.2897,   'lon': 103.8501,  'tz': 'Asia/Singapore',    'ipo_hour':  9, 'ipo_min': 0},
    'ASX':  {'city': 'Sydney',        'lat': -33.8688,  'lon': 151.2093,  'tz': 'Australia/Sydney',  'ipo_hour': 10, 'ipo_min': 0},
    'DB':   {'city': 'Frankfurt',     'lat': 50.1109,   'lon':  8.6821,   'tz': 'Europe/Berlin',     'ipo_hour':  9, 'ipo_min': 0},
}

# ── Country charts ────────────────────────────────────────────────────────────
COUNTRY_CHARTS = {
    'India':     {'date': '1947-08-15', 'time': '00:00:00', 'tz_offset': 5.5,   'city': 'New Delhi',  'lat': 28.6139,  'lon': 77.2090},
    'USA':       {'date': '1776-07-04', 'time': '17:10:00', 'tz_offset': -5.0,  'city': 'Philadelphia','lat': 39.9526, 'lon': -75.1652},
    'UK':        {'date': '1801-01-01', 'time': '00:00:00', 'tz_offset':  0.0,  'city': 'London',     'lat': 51.5074,  'lon': -0.1278},
    'China':     {'date': '1949-10-01', 'time': '15:01:00', 'tz_offset':  8.0,  'city': 'Beijing',    'lat': 39.9042,  'lon': 116.4074},
    'Japan':     {'date': '1947-05-03', 'time': '00:00:00', 'tz_offset':  9.0,  'city': 'Tokyo',      'lat': 35.6762,  'lon': 139.6503},
    'Germany':   {'date': '1949-05-23', 'time': '00:00:00', 'tz_offset':  1.0,  'city': 'Bonn',       'lat': 50.7374,  'lon':  7.0982},
    'Pakistan':  {'date': '1947-08-14', 'time': '09:30:00', 'tz_offset':  5.5,  'city': 'Karachi',    'lat': 24.8607,  'lon': 67.0011},
    'Russia':    {'date': '1991-12-25', 'time': '19:38:00', 'tz_offset':  3.0,  'city': 'Moscow',     'lat': 55.7558,  'lon': 37.6173},
    'France':    {'date': '1958-10-04', 'time': '18:30:00', 'tz_offset':  1.0,  'city': 'Paris',      'lat': 48.8566,  'lon':  2.3522},
    'Brazil':    {'date': '1822-09-07', 'time': '16:30:00', 'tz_offset': -3.0,  'city': 'Salvador',   'lat': -12.9714, 'lon': -38.5014},
}

# ── Financial yoga rules ───────────────────────────────────────────────────────
# Maps yogas to financial interpretation and score delta
YOGA_FINANCIAL = {
    'Gaja Kesari':     {'effect': 'Fame, institutional trust, consistent growth',      'score': +15, 'signal': 'BUY'},
    'Dhana Yoga':      {'effect': 'Wealth accumulation, strong revenue cycle',          'score': +20, 'signal': 'BUY'},
    'Raja Yoga':       {'effect': 'Authority, market leadership, strong brand',         'score': +18, 'signal': 'BUY'},
    'Viparita Raja':   {'effect': 'Thrives in adverse conditions, counter-cyclical',    'score': +12, 'signal': 'HOLD'},
    'Neecha Bhanga':   {'effect': 'Debilitation cancelled, eventual recovery',          'score': +8,  'signal': 'HOLD'},
    'Kemdrum':         {'effect': 'Isolation, lack of support, erratic performance',   'score': -15, 'signal': 'CAUTION'},
    'Kala Sarpa':      {'effect': 'Extremes — sharp rises and sharp falls',             'score': -10, 'signal': 'CAUTION'},
    'Parivartana':     {'effect': 'Mutual exchange — complex, context-dependent',       'score':  +5, 'signal': 'HOLD'},
    'Graha Yuddha':    {'effect': 'Planetary war — instability in that sector',         'score': -8,  'signal': 'CAUTION'},
    'Mahabhagya':      {'effect': 'Great fortune yoga, long-term outperformance',       'score': +25, 'signal': 'BUY'},
}

# ── House interpretations for financial entities ───────────────────────────────
FINANCIAL_HOUSES = {
    1:  'Identity, brand, overall health of the entity',
    2:  'Cash reserves, balance sheet, P&L, accumulated wealth',
    3:  'Communication, marketing, media, short-distance expansion',
    4:  'Physical assets, real estate, fixed assets, domestic market',
    5:  'Speculation, derivatives, creative R&D, investor sentiment',
    6:  'Debt, competition, litigation, employees, operational costs',
    7:  'Partnerships, M&A, foreign collaborations, JV ventures',
    8:  'Sudden events, transformation, debt restructuring, M&A target',
    9:  'Long-term fortune, overseas expansion, dharma of the entity',
    10: 'Management, CEO, government relations, market reputation',
    11: 'Revenue, profits, cash inflows, shareholder returns',
    12: 'Losses, write-offs, foreign operations, R&D expenditure',
}


class KundliEngine:
    """Computes a complete Vedic natal chart for any entity."""

    def __init__(self):
        try:
            import swisseph as swe
            self._swe = swe
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except ImportError as e:
            raise ImportError(
                f"pyswisseph import failed: {e}. "
                "Fix: py -3.11 -m pip install --force-reinstall pyswisseph"
            ) from e

        self.output_dir = cfg.INTELLIGENCE_DIR / 'kundli'
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Public entry points ───────────────────────────────────────────────────

    def compute_stock(self, symbol: str, listing_date: str,
                      exchange: str = 'NSE') -> Optional[dict]:
        """Compute Kundli for a stock using its IPO/listing date."""
        ex = EXCHANGES.get(exchange.upper(), EXCHANGES['NSE'])
        time_str = f"{ex['ipo_hour']:02d}:{ex['ipo_min']:02d}:00"
        tz_offset = self._tz_offset(ex['tz'])
        chart = self._compute(
            date_str=listing_date,
            time_str=time_str,
            lat=ex['lat'],
            lon=ex['lon'],
            tz_offset=tz_offset,
            entity_type='STOCK',
            entity_name=symbol,
        )
        if chart:
            chart['symbol']   = symbol
            chart['exchange'] = exchange
        return chart

    def compute_human(self, name: str, date_str: str, time_str: str,
                      lat: float, lon: float, tz_offset: float) -> Optional[dict]:
        """Compute Kundli for a human being."""
        chart = self._compute(date_str, time_str, lat, lon, tz_offset,
                              'HUMAN', name)
        return chart

    def compute_country(self, country_name: str) -> Optional[dict]:
        """Compute Kundli for a country using hardcoded inception data."""
        cc = COUNTRY_CHARTS.get(country_name)
        if cc is None:
            return {'error': f"Country '{country_name}' not found. Available: {list(COUNTRY_CHARTS.keys())}"}
        chart = self._compute(
            date_str=cc['date'],
            time_str=cc['time'],
            lat=cc['lat'],
            lon=cc['lon'],
            tz_offset=cc['tz_offset'],
            entity_type='COUNTRY',
            entity_name=country_name,
        )
        return chart

    # ── Core computation ──────────────────────────────────────────────────────

    def _compute(self, date_str: str, time_str: str,
                 lat: float, lon: float, tz_offset: float,
                 entity_type: str, entity_name: str) -> Optional[dict]:
        try:
            jd_natal   = self._to_jd(date_str, time_str, tz_offset)
            jd_now     = self._now_jd()
            planets    = self._planet_positions(jd_natal)
            lagna      = self._ascendant(jd_natal, lat, lon)
            lagna_sign = int(lagna / 30)

            enriched = {}
            for name, lon_deg in planets.items():
                sign_num   = int(lon_deg / 30)
                deg_in_sign = lon_deg % 30
                house      = (sign_num - lagna_sign) % 12 + 1
                nakshatra  = self._nakshatra(lon_deg)
                dignity    = self._dignity(name, sign_num, deg_in_sign)
                retrograde = self._is_retrograde(jd_natal, name)
                enriched[name] = {
                    'longitude':    round(lon_deg, 4),
                    'sign':         SIGNS[sign_num],
                    'sign_num':     sign_num,
                    'degree':       round(deg_in_sign, 2),
                    'house':        house,
                    'nakshatra':    nakshatra['name'],
                    'pada':         nakshatra['pada'],
                    'nakshatra_lord': nakshatra['lord'],
                    'dignity':      dignity,
                    'retrograde':   retrograde,
                }

            lagna_sign_name = SIGNS[lagna_sign]
            lagna_lord      = SIGN_LORDS[lagna_sign]

            div_charts  = self._divisional_charts(planets)
            dasha       = self._vimshottari_dasha(planets['Moon'], jd_natal, jd_now)  # planets['Moon'] is raw float
            yogas       = self._detect_yogas(enriched, lagna_sign)
            fin_houses  = self._financial_houses(enriched, lagna_sign)
            transits    = self._current_transits(enriched, jd_now)
            score, action = self._financial_score(enriched, lagna_sign, dasha, yogas, transits)

            return {
                'entity': {
                    'type':          entity_type,
                    'name':          entity_name,
                    'inception_date': date_str,
                    'inception_time': time_str,
                    'lat':           lat,
                    'lon':           lon,
                    'tz_offset':     tz_offset,
                },
                'lagna': {
                    'sign':         lagna_sign_name,
                    'sign_num':     lagna_sign,
                    'degree':       round(lagna % 30, 2),
                    'lord':         lagna_lord,
                    'full_longitude': round(lagna, 4),
                },
                'planets':            enriched,
                'divisional_charts':  div_charts,
                'current_dasha':      dasha,
                'financial_houses':   fin_houses,
                'yogas':              yogas,
                'transits':           transits,
                'astro_score':        round(score, 1),
                'astro_action':       action,
                'computed_date':      datetime.now().strftime('%Y-%m-%d'),
            }
        except Exception as exc:
            logger.error('[KundliEngine] Compute failed for %s: %s', entity_name, exc)
            return None

    # ── Julian Day ────────────────────────────────────────────────────────────

    def _to_jd(self, date_str: str, time_str: str, tz_offset: float) -> float:
        d = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M:%S')
        # Convert local time to UT
        d_ut = d - timedelta(hours=tz_offset)
        hour_decimal = d_ut.hour + d_ut.minute / 60.0 + d_ut.second / 3600.0
        return self._swe.julday(d_ut.year, d_ut.month, d_ut.day, hour_decimal)

    def _now_jd(self) -> float:
        now = datetime.now(timezone.utc)
        h   = now.hour + now.minute / 60.0 + now.second / 3600.0
        return self._swe.julday(now.year, now.month, now.day, h)

    # ── Planetary positions ────────────────────────────────────────────────────

    _PLANET_IDS = {
        'Sun': 0, 'Moon': 1, 'Mercury': 2, 'Venus': 3, 'Mars': 4,
        'Jupiter': 5, 'Saturn': 6, 'Uranus': 7, 'Neptune': 8,
    }

    def _planet_positions(self, jd: float) -> dict[str, float]:
        swe    = self._swe
        flags  = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result = {}
        for name, pid in self._PLANET_IDS.items():
            xx, _ = swe.calc_ut(jd, pid, flags)
            result[name] = xx[0] % 360

        # Rahu (True Node) and Ketu
        xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
        rahu  = xx[0] % 360
        ketu  = (rahu + 180) % 360
        result['Rahu'] = rahu
        result['Ketu'] = ketu
        return result

    def _ascendant(self, jd: float, lat: float, lon: float) -> float:
        """Return sidereal Ascendant longitude using Whole Sign."""
        swe = self._swe
        # Get tropical houses first
        cusps, ascmc = swe.houses(jd, lat, lon, b'W')
        # Apply Lahiri ayanamsha to get sidereal Ascendant
        ayanamsha = swe.get_ayanamsa_ut(jd)
        sidereal_asc = (ascmc[0] - ayanamsha) % 360
        return sidereal_asc

    def _is_retrograde(self, jd: float, planet: str) -> bool:
        if planet in ('Rahu', 'Ketu'):
            return True  # Nodes are always technically retrograde
        pid   = self._PLANET_IDS.get(planet)
        if pid is None:
            return False
        flags = self._swe.FLG_SIDEREAL | self._swe.FLG_SPEED
        xx, _ = self._swe.calc_ut(jd, pid, flags)
        return xx[3] < 0  # Negative speed = retrograde

    # ── Nakshatra ─────────────────────────────────────────────────────────────

    def _nakshatra(self, longitude: float) -> dict:
        lon = longitude % 360
        for name, start, end, lord, symbol in NAKSHATRAS:
            if start <= lon < end:
                pada = int((lon - start) / (13.333 / 4)) + 1
                return {'name': name, 'lord': lord, 'symbol': symbol, 'pada': min(pada, 4)}
        # Revati edge case (360°)
        return {'name': 'Revati', 'lord': 'Mercury', 'symbol': 'Fish', 'pada': 4}

    # ── Dignity ───────────────────────────────────────────────────────────────

    def _dignity(self, planet: str, sign_num: int, deg_in_sign: float) -> str:
        if planet in ('Uranus', 'Neptune'):
            return 'neutral'
        # Exaltation
        if planet in EXALTATION:
            ex_sign, ex_deg = EXALTATION[planet]
            if sign_num == ex_sign:
                if abs(deg_in_sign - ex_deg) <= 2:
                    return 'exalted_exact'
                return 'exalted'
        # Debilitation
        if planet in DEBILITATION and sign_num == DEBILITATION[planet]:
            return 'debilitated'
        # Moolatrikona
        if planet in MOOLATRIKONA:
            mt_sign, mt_start, mt_end = MOOLATRIKONA[planet]
            if sign_num == mt_sign and mt_start <= deg_in_sign <= mt_end:
                return 'moolatrikona'
        # Own sign
        if planet in OWN_SIGNS and sign_num in OWN_SIGNS[planet]:
            return 'own_sign'
        # Friend/Enemy sign
        lord = SIGN_LORDS[sign_num]
        if lord in FRIENDS.get(planet, []):
            return 'friendly'
        if lord in ENEMIES.get(planet, []):
            return 'enemy'
        return 'neutral'

    # ── Divisional charts ─────────────────────────────────────────────────────

    def _divisional_charts(self, planets: dict[str, float]) -> dict:
        charts = {}
        for d_num, method in [
            (1,  'identity'), (2,  'hora'),    (3,  'drekkana'),
            (4,  'general'),  (7,  'saptamsa'), (9,  'navamsa'),
            (10, 'dasamsa'),  (11, 'general'),  (12, 'dwadasamsa'),
            (16, 'general'),  (20, 'general'),  (30, 'trimshamsa'),
            (60, 'general'),
        ]:
            chart_signs = {}
            for planet, lon in planets.items():
                chart_signs[planet] = self._varga_sign(lon, d_num, method)
            charts[f'D{d_num}'] = chart_signs
        return charts

    def _varga_sign(self, longitude: float, divisor: int, method: str) -> str:
        lon    = longitude % 360
        s_num  = int(lon / 30)           # 0-11 natal sign
        d_in_s = lon % 30                # 0-30 degree within sign
        amsa   = int(d_in_s / (30 / divisor))  # 0..(divisor-1)

        if method == 'identity':
            return SIGNS[s_num]

        elif method == 'hora':
            # Only 2 divisions: Sun's hora (Leo) or Moon's hora (Cancer)
            if s_num % 2 == 0:  # Odd sign (Aries=0)
                return 'Leo' if d_in_s < 15 else 'Cancer'
            else:               # Even sign
                return 'Cancer' if d_in_s < 15 else 'Leo'

        elif method == 'drekkana':
            # 3 divisions of 10° each
            if amsa == 0:   base = s_num
            elif amsa == 1: base = (s_num + 4) % 12   # 5th from
            else:           base = (s_num + 8) % 12   # 9th from
            return SIGNS[base]

        elif method == 'navamsa':
            # Each navamsa = 3°20', 9 per sign
            # Starting sign depends on sign modality
            if s_num in MOVABLE_SIGNS:
                start = s_num
            elif s_num in FIXED_SIGNS:
                start = (s_num + 8) % 12   # 9th from
            else:  # Dual
                start = (s_num + 4) % 12   # 5th from
            return SIGNS[(start + amsa) % 12]

        elif method == 'dasamsa':
            # Odd sign: start from same; Even sign: start from 9th
            if s_num % 2 == 0:  # Odd sign
                start = s_num
            else:               # Even sign
                start = (s_num + 8) % 12
            return SIGNS[(start + amsa) % 12]

        elif method == 'saptamsa':
            # Odd sign: start from same; Even: from 7th
            if s_num % 2 == 0:
                start = s_num
            else:
                start = (s_num + 6) % 12
            return SIGNS[(start + amsa) % 12]

        elif method == 'dwadasamsa':
            # 12 divisions of 2.5°, always start from same sign
            return SIGNS[(s_num + amsa) % 12]

        elif method == 'trimshamsa':
            # D30: special unequal divisions per Parasara
            # 5 sections per sign: lords are Mars/Saturn/Jupiter/Mercury/Venus
            # Odd signs: 5°Mars, 5°Saturn, 8°Jupiter, 7°Mercury, 5°Venus
            # Even signs: 5°Venus, 7°Mercury, 8°Jupiter, 5°Saturn, 5°Mars
            odd_boundaries  = [5, 10, 18, 25, 30]
            even_boundaries = [5, 12, 20, 25, 30]
            odd_lords  = ['Aries','Aquarius','Sagittarius','Gemini','Libra']
            even_lords = ['Taurus','Virgo','Pisces','Capricorn','Scorpio']
            boundaries = odd_boundaries if s_num % 2 == 0 else even_boundaries
            signs_map  = odd_lords      if s_num % 2 == 0 else even_lords
            for idx, boundary in enumerate(boundaries):
                if d_in_s < boundary:
                    return signs_map[idx]
            return signs_map[-1]

        else:
            # General formula: odd=same start, even=7th start
            if s_num % 2 == 0:
                start = s_num
            else:
                start = (s_num + 6) % 12
            return SIGNS[(start + amsa) % 12]

    # ── Vimshottari Dasha ─────────────────────────────────────────────────────

    def _vimshottari_dasha(self, moon_lon: float, jd_natal: float,
                           jd_now: float) -> dict:
        # 1. Find birth nakshatra and its dasha lord
        nak_idx = min(int(moon_lon / 13.3333), 26)
        nak     = NAKSHATRAS[nak_idx]
        nak_end = nak[2]  # end degree of nakshatra
        nak_lord = nak[3]  # dasha lord

        # 2. Balance of first dasha at birth
        fraction_remaining = (nak_end - moon_lon) / 13.3333
        balance_years = fraction_remaining * VIMSHOTTARI_YEARS[nak_lord]

        # 3. Build mahadasha timeline from birth
        birth_year = self._jd_to_year(jd_natal)
        now_year   = self._jd_to_year(jd_now)

        seq_start = VIMSHOTTARI_SEQ.index(nak_lord)
        mahadashas = []
        cursor = birth_year

        # First dasha (partial)
        mahadashas.append({
            'planet': nak_lord,
            'start':  round(cursor, 6),
            'end':    round(cursor + balance_years, 6),
        })
        cursor += balance_years

        # Complete subsequent dashas (2 full 120-year cycles covers any lifespan)
        for cycle in range(2):
            for i in range(9):
                idx    = (seq_start + 1 + i + cycle * 9) % 9
                planet = VIMSHOTTARI_SEQ[idx]
                years  = VIMSHOTTARI_YEARS[planet]
                mahadashas.append({
                    'planet': planet,
                    'start':  round(cursor, 6),
                    'end':    round(cursor + years, 6),
                })
                cursor += years

        # 4. Find current mahadasha
        current_maha = None
        for m in mahadashas:
            if m['start'] <= now_year < m['end']:
                current_maha = m
                break

        if current_maha is None:
            current_maha = mahadashas[-1]

        # 5. Compute antardasha within current mahadasha
        maha_dur = VIMSHOTTARI_YEARS[current_maha['planet']]
        maha_start = current_maha['start']
        maha_planet_idx = VIMSHOTTARI_SEQ.index(current_maha['planet'])
        antardashas = []
        ad_cursor = maha_start
        for i in range(9):
            idx    = (maha_planet_idx + i) % 9
            planet = VIMSHOTTARI_SEQ[idx]
            dur    = (maha_dur * VIMSHOTTARI_YEARS[planet]) / VIMSHOTTARI_TOTAL
            antardashas.append({
                'planet': planet,
                'start':  round(ad_cursor, 6),
                'end':    round(ad_cursor + dur, 6),
            })
            ad_cursor += dur

        current_antar = None
        for a in antardashas:
            if a['start'] <= now_year < a['end']:
                current_antar = a
                break
        if current_antar is None:
            current_antar = antardashas[-1]

        # 6. Pratyantardasha
        antar_dur = (maha_dur * VIMSHOTTARI_YEARS[current_antar['planet']]) / VIMSHOTTARI_TOTAL
        antar_start = current_antar['start']
        antar_planet_idx = VIMSHOTTARI_SEQ.index(current_antar['planet'])
        pratyantar = []
        pt_cursor  = antar_start
        for i in range(9):
            idx    = (antar_planet_idx + i) % 9
            planet = VIMSHOTTARI_SEQ[idx]
            dur    = (antar_dur * VIMSHOTTARI_YEARS[planet]) / VIMSHOTTARI_TOTAL
            pratyantar.append({
                'planet': planet,
                'start':  round(pt_cursor, 6),
                'end':    round(pt_cursor + dur, 6),
            })
            pt_cursor += dur

        current_pratyantar = None
        for p in pratyantar:
            if p['start'] <= now_year < p['end']:
                current_pratyantar = p
                break
        if current_pratyantar is None:
            current_pratyantar = pratyantar[-1]

        def yr_to_date(y: float) -> str:
            year  = int(y)
            frac  = y - year
            doy   = int(frac * 365.25)
            try:
                d = datetime(year, 1, 1) + timedelta(days=doy)
                return d.strftime('%Y-%m-%d')
            except Exception:
                return str(year)

        return {
            'mahadasha':       {**current_maha,       'start_date': yr_to_date(current_maha['start']),      'end_date': yr_to_date(current_maha['end'])},
            'antardasha':      {**current_antar,       'start_date': yr_to_date(current_antar['start']),     'end_date': yr_to_date(current_antar['end'])},
            'pratyantardasha': {**current_pratyantar,  'start_date': yr_to_date(current_pratyantar['start']),'end_date': yr_to_date(current_pratyantar['end'])},
            'all_mahadashas':  [{'planet': m['planet'], 'start_date': yr_to_date(m['start']), 'end_date': yr_to_date(m['end'])} for m in mahadashas[:18]],
        }

    def _jd_to_year(self, jd: float) -> float:
        """Convert Julian Day to decimal year."""
        y, m, d, h = self._swe.revjul(jd)
        # Days in year
        jd_jan1    = self._swe.julday(y, 1, 1, 0)
        jd_jan1_nx = self._swe.julday(y + 1, 1, 1, 0)
        return y + (jd - jd_jan1) / (jd_jan1_nx - jd_jan1)

    # ── Yoga detection ────────────────────────────────────────────────────────

    def _detect_yogas(self, planets: dict, lagna_sign: int) -> list[dict]:
        yogas = []
        p = planets  # shorthand

        def sign(planet):
            return p[planet]['sign_num']

        def house(planet):
            return p[planet]['house']

        def in_kendra(planet):
            return house(planet) in (1, 4, 7, 10)

        def in_trikona(planet):
            return house(planet) in (1, 5, 9)

        def kendra_lords():
            return [SIGN_LORDS[(lagna_sign + k - 1) % 12] for k in (1, 4, 7, 10)]

        def trikona_lords():
            return [SIGN_LORDS[(lagna_sign + k - 1) % 12] for k in (1, 5, 9)]

        # Gaja Kesari: Jupiter in Kendra from Moon
        moon_house = house('Moon')
        jup_house  = house('Jupiter')
        dist = (jup_house - moon_house) % 12
        if dist in (0, 3, 6, 9):
            yogas.append({'name': 'Gaja Kesari', 'planets': ['Jupiter', 'Moon'],
                          'strength': 'strong' if dist == 0 else 'moderate',
                          **YOGA_FINANCIAL['Gaja Kesari']})

        # Dhana Yoga: Lords of 2H, 11H in mutual kendra/trikona, or conjunct
        lord_2h  = SIGN_LORDS[(lagna_sign + 1) % 12]
        lord_11h = SIGN_LORDS[(lagna_sign + 10) % 12]
        lord_5h  = SIGN_LORDS[(lagna_sign + 4) % 12]
        lord_9h  = SIGN_LORDS[(lagna_sign + 8) % 12]
        if lord_2h in p and lord_11h in p:
            h2 = house(lord_2h); h11 = house(lord_11h)
            if h2 in (1,2,5,9,11) and h11 in (1,2,5,9,11):
                yogas.append({'name': 'Dhana Yoga', 'planets': [lord_2h, lord_11h],
                              'strength': 'strong', **YOGA_FINANCIAL['Dhana Yoga']})

        # Raja Yoga: Kendra lord + Trikona lord conjunction or mutual aspect
        kl = set(kendra_lords())
        tl = set(trikona_lords())
        for kp in kl:
            for tp in tl:
                if kp == tp:
                    continue
                if kp in p and tp in p and house(kp) == house(tp):
                    yogas.append({'name': 'Raja Yoga', 'planets': [kp, tp],
                                  'strength': 'strong', **YOGA_FINANCIAL['Raja Yoga']})

        # Viparita Raja Yoga: Lords of 6H, 8H, 12H in those houses
        lords_6_8_12 = [
            SIGN_LORDS[(lagna_sign + 5) % 12],
            SIGN_LORDS[(lagna_sign + 7) % 12],
            SIGN_LORDS[(lagna_sign + 11) % 12],
        ]
        vr_count = sum(1 for l in lords_6_8_12 if l in p and house(l) in (6, 8, 12))
        if vr_count >= 2:
            yogas.append({'name': 'Viparita Raja', 'planets': lords_6_8_12,
                          'strength': 'present', **YOGA_FINANCIAL['Viparita Raja']})

        # Kemdrum Yoga: Moon with no planets in 2nd or 12th from Moon
        moon_sign = sign('Moon')
        neighbors = {(moon_sign + 1) % 12, (moon_sign - 1) % 12}
        has_neighbor = any(
            p[pl]['sign_num'] in neighbors
            for pl in p if pl not in ('Moon', 'Rahu', 'Ketu', 'Uranus', 'Neptune')
        )
        if not has_neighbor:
            yogas.append({'name': 'Kemdrum', 'planets': ['Moon'],
                          'strength': 'present', **YOGA_FINANCIAL['Kemdrum']})

        # Neecha Bhanga: Debilitated planet with cancellation
        for planet, deb_sign in DEBILITATION.items():
            if planet not in p:
                continue
            if sign(planet) == deb_sign:
                # Cancellation: lord of debilitation sign in kendra from Lagna or Moon
                deb_lord = SIGN_LORDS[deb_sign]
                if deb_lord in p and (in_kendra(deb_lord) or
                        abs(house(deb_lord) - moon_house) % 6 == 0):
                    yogas.append({'name': 'Neecha Bhanga', 'planets': [planet, deb_lord],
                                  'strength': 'partial', **YOGA_FINANCIAL['Neecha Bhanga']})

        # Kala Sarpa: All planets between Rahu and Ketu (one hemisphere)
        rahu_lon = p['Rahu']['longitude']
        ketu_lon = p['Ketu']['longitude']
        all_in_arc = all(
            self._in_arc(p[pl]['longitude'], rahu_lon, ketu_lon)
            for pl in ('Sun','Moon','Mercury','Venus','Mars','Jupiter','Saturn')
            if pl in p
        )
        if all_in_arc:
            yogas.append({'name': 'Kala Sarpa', 'planets': ['Rahu', 'Ketu'],
                          'strength': 'present', **YOGA_FINANCIAL['Kala Sarpa']})

        # Parivartana: Two planets in each other's signs
        for pa in list(p.keys()):
            for pb in list(p.keys()):
                if pa >= pb:
                    continue
                if pa in ('Rahu','Ketu','Uranus','Neptune') or pb in ('Rahu','Ketu','Uranus','Neptune'):
                    continue
                if (pa in OWN_SIGNS and sign(pb) in OWN_SIGNS[pa] and
                        pb in OWN_SIGNS and sign(pa) in OWN_SIGNS[pb]):
                    yogas.append({'name': 'Parivartana', 'planets': [pa, pb],
                                  'strength': 'present', **YOGA_FINANCIAL['Parivartana']})

        return yogas

    def _in_arc(self, lon: float, from_lon: float, to_lon: float) -> bool:
        """Check if longitude is in the arc from from_lon to to_lon (clockwise)."""
        lon    = lon % 360
        f      = from_lon % 360
        t      = to_lon % 360
        if f < t:
            return f <= lon <= t
        return lon >= f or lon <= t

    # ── Financial houses summary ───────────────────────────────────────────────

    def _financial_houses(self, planets: dict, lagna_sign: int) -> dict:
        result = {}
        for house_num in (2, 5, 8, 10, 11):
            sign_num = (lagna_sign + house_num - 1) % 12
            lord     = SIGN_LORDS[sign_num]
            occupants = [
                p for p, data in planets.items()
                if data['house'] == house_num
            ]
            lord_house = planets.get(lord, {}).get('house', None)
            lord_dignity = planets.get(lord, {}).get('dignity', 'unknown')

            # Simple qualitative assessment
            if lord_dignity in ('exalted', 'exalted_exact', 'moolatrikona', 'own_sign'):
                strength = 'strong'
            elif lord_dignity in ('debilitated',):
                strength = 'weak'
            elif lord_house and lord_house in (1, 2, 5, 9, 10, 11):
                strength = 'moderate-strong'
            elif lord_house and lord_house in (6, 8, 12):
                strength = 'weak'
            else:
                strength = 'moderate'

            result[f'{house_num}H'] = {
                'sign':          SIGNS[sign_num],
                'lord':          lord,
                'lord_house':    lord_house,
                'lord_dignity':  lord_dignity,
                'occupants':     occupants,
                'strength':      strength,
                'signification': FINANCIAL_HOUSES[house_num],
            }
        return result

    # ── Transit analysis ──────────────────────────────────────────────────────

    def _current_transits(self, natal_planets: dict, jd_now: float) -> dict:
        current_pos = self._planet_positions(jd_now)
        transits = {}
        for planet, curr_lon in current_pos.items():
            if planet not in natal_planets:
                continue
            natal_lon  = natal_planets[planet]['longitude']
            angle      = (curr_lon - natal_lon) % 360
            aspect     = self._classify_aspect(angle)
            curr_sign  = int(curr_lon / 30)
            natal_sign = natal_planets[planet]['sign_num']

            # Is transit planet conjunct any natal planets?
            conjunctions = []
            for np, ndata in natal_planets.items():
                diff = abs(curr_lon - ndata['longitude']) % 360
                if diff > 180:
                    diff = 360 - diff
                if diff < 8:
                    conjunctions.append(np)

            transits[planet] = {
                'current_sign':   SIGNS[curr_sign],
                'natal_sign':     SIGNS[natal_sign],
                'transit_angle':  round(angle, 1),
                'aspect':         aspect,
                'conjunct_natal': conjunctions,
            }
        return transits

    def _classify_aspect(self, angle: float) -> str:
        a = angle if angle <= 180 else 360 - angle
        if a < 8:    return 'conjunction'
        if 52 < a < 68:   return 'sextile'
        if 82 < a < 98:   return 'square'
        if 112 < a < 128: return 'trine'
        if 172 < a < 188: return 'opposition'
        return 'separating'

    # ── Financial score ───────────────────────────────────────────────────────

    def _financial_score(self, planets: dict, lagna_sign: int,
                         dasha: dict, yogas: list, transits: dict) -> tuple[float, str]:
        score = 0.0

        # 1. 11th house lord dignity
        lord_11h = SIGN_LORDS[(lagna_sign + 10) % 12]
        if lord_11h in planets:
            d = planets[lord_11h]['dignity']
            score += {'exalted_exact': 20, 'exalted': 15, 'moolatrikona': 12,
                      'own_sign': 10, 'friendly': 5, 'neutral': 0,
                      'enemy': -5, 'debilitated': -15}.get(d, 0)

        # 2. Current Mahadasha planet in financial house?
        maha_planet = dasha['mahadasha']['planet']
        if maha_planet in planets:
            mh = planets[maha_planet]['house']
            score += {1: 5, 2: 15, 5: 12, 9: 12, 10: 10, 11: 20}.get(mh, 0)
            score += {6: -10, 8: -15, 12: -10}.get(mh, 0)

        # 3. Yoga scores
        for yoga in yogas:
            score += yoga.get('score', 0)

        # 4. Jupiter transiting natal 11H, 2H, 5H = bullish
        jup_transit = transits.get('Jupiter', {})
        jup_aspect  = jup_transit.get('aspect', '')
        if jup_aspect in ('conjunction', 'trine', 'sextile'):
            score += 10
        elif jup_aspect == 'square':
            score += 2
        elif jup_aspect == 'opposition':
            score -= 5

        # 5. Saturn transiting natal 8H = bearish
        sat_transit = transits.get('Saturn', {})
        if sat_transit.get('aspect') == 'conjunction':
            score -= 12
        elif sat_transit.get('aspect') == 'opposition':
            score -= 6

        # 6. 5H (speculation) and 8H (volatility) lord dignity
        lord_5h = SIGN_LORDS[(lagna_sign + 4) % 12]
        lord_8h = SIGN_LORDS[(lagna_sign + 7) % 12]
        if lord_5h in planets:
            d5 = planets[lord_5h]['dignity']
            score += {'exalted': 8, 'own_sign': 6, 'debilitated': -8}.get(d5, 0)
        if lord_8h in planets:
            d8 = planets[lord_8h]['dignity']
            score += {'exalted': -5, 'debilitated': -12}.get(d8, 0)

        score = max(-100, min(100, score))

        if score >= 40:   action = 'BUY'
        elif score >= 15: action = 'HOLD'
        elif score >= -5: action = 'CAUTION'
        elif score >= -25: action = 'EXIT'
        else:             action = 'AVOID'

        return score, action

    # ── Timezone helper ───────────────────────────────────────────────────────

    @staticmethod
    def _tz_offset(tz_name: str) -> float:
        offsets = {
            'Asia/Kolkata':    5.5,
            'America/New_York': -5.0,
            'Europe/London':    0.0,
            'Asia/Tokyo':       9.0,
            'Asia/Shanghai':    8.0,
            'Asia/Hong_Kong':   8.0,
            'Asia/Singapore':   8.0,
            'Australia/Sydney': 10.0,
            'Europe/Berlin':    1.0,
        }
        return offsets.get(tz_name, 5.5)

    # ── Bulk stock runner ─────────────────────────────────────────────────────

    def run(self) -> bool:
        """Process all NSE stocks with listing dates. Saves per-symbol JSON + summary CSV."""
        import pandas as pd
        import csv
        import shutil

        em_path = cfg.NSE_DIR / 'equity_master' / 'equity_master.csv'
        if not em_path.exists():
            logger.error('[KundliEngine] equity_master.csv not found at %s', em_path)
            return False

        em = pd.read_csv(em_path)
        em.columns = [c.lower() for c in em.columns]   # normalize to lowercase
        em = em[em['series'] == 'EQ'].copy()

        if 'listing_date' not in em.columns:
            logger.error('[KundliEngine] equity_master has no listing_date column')
            return False

        em = em.dropna(subset=['listing_date'])
        symbols = em[['symbol', 'listing_date']].values.tolist()
        logger.info('[KundliEngine] Processing %d symbols', len(symbols))

        summary_rows = []
        done = 0

        for symbol, listing_date in symbols:
            try:
                listing_date = str(listing_date)[:10]  # ensure YYYY-MM-DD
                chart = self.compute_stock(symbol, listing_date, 'NSE')
                if chart is None:
                    continue

                # Save per-symbol JSON
                out = self.output_dir / f'{symbol}_kundli.json'
                tmp = out.with_suffix('.tmp.json')
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(chart, f, indent=2, default=str)
                shutil.move(str(tmp), str(out))

                # Summary row
                lagna   = chart['lagna']['sign']
                moon_sign = chart['planets'].get('Moon', {}).get('sign', '')
                maha    = chart['current_dasha']['mahadasha']['planet']
                antar   = chart['current_dasha']['antardasha']['planet']
                maha_end = chart['current_dasha']['mahadasha']['end_date']
                summary_rows.append({
                    'symbol':         symbol,
                    'listing_date':   listing_date,
                    'lagna':          lagna,
                    'lagna_lord':     chart['lagna']['lord'],
                    'moon_sign':      moon_sign,
                    'mahadasha':      maha,
                    'antardasha':     antar,
                    'maha_end_date':  maha_end,
                    'yogas':          '|'.join(y['name'] for y in chart['yogas'][:5]),
                    'astro_score':    chart['astro_score'],
                    'astro_action':   chart['astro_action'],
                })
                done += 1

                if done % 100 == 0:
                    logger.info('[KundliEngine] %d/%d done', done, len(symbols))

            except Exception as exc:
                logger.warning('[KundliEngine] Skip %s: %s', symbol, exc)

        if not summary_rows:
            logger.error('[KundliEngine] No charts computed')
            return False

        # Save summary CSV (atomic write)
        out_csv = cfg.INTELLIGENCE_DIR / 'kundli_signals.csv'
        tmp_csv = out_csv.with_suffix('.tmp.csv')
        df = pd.DataFrame(summary_rows)
        df.to_csv(tmp_csv, index=False)
        shutil.move(str(tmp_csv), str(out_csv))
        logger.info('[KundliEngine] Complete — %d symbols, saved to %s', done, out_csv)
        return True


if __name__ == '__main__':
    engine = KundliEngine()
    # Quick test: compute for a single stock
    test_date = '2000-11-18'   # Reliance approximate NSE listing
    chart = engine.compute_stock('RELIANCE', test_date, 'NSE')
    if chart:
        print(f"Lagna: {chart['lagna']['sign']} | Moon: {chart['planets']['Moon']['sign']}")
        print(f"Mahadasha: {chart['current_dasha']['mahadasha']['planet']} until {chart['current_dasha']['mahadasha']['end_date']}")
        print(f"Yogas: {[y['name'] for y in chart['yogas']]}")
        print(f"Financial Score: {chart['astro_score']} | Signal: {chart['astro_action']}")
    else:
        print('Kundli computation failed.')
