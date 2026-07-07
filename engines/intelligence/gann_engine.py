"""
Gann Engine — Phase KU-2
Implements W.D. Gann's mathematical tools for price/time analysis:
  - Square of 9: spiral grid price levels at 8 cardinal/fixed angles
  - Gann Fan: 1×1, 1×2, 2×1, 1×3, 3×1, 1×4, 4×1 angle lines from pivot
  - Gann Planetary Lines: geocentric longitude → price mapping
  - Time cycles: 90°, 180°, 270°, 360° of solar transit = seasonal turns
  - Price-Time convergence: where price level AND time angle coincide

Mathematical foundation:
  Square of 9 degree(N) = MOD((SQRT(N) × 180) - 225, 360)
  Resistance = (SQRT(P) + angle/180) ^ 2
  Support    = (SQRT(P) - angle/180) ^ 2

Run standalone:
  py -3.11 -m engines.intelligence.gann_engine
"""

from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Gann angles ───────────────────────────────────────────────────────────────
# Name: (numerator, denominator, degrees_from_base)
# All 8 angles from a pivot: the "octave" of price/time movement
GANN_ANGLES = [
    ('4×1',  4, 1,  75.96),  # Fastest angle — extremely bullish
    ('3×1',  3, 1,  71.57),
    ('2×1',  2, 1,  63.43),
    ('1×1',  1, 1,  45.00),  # Primary balance angle
    ('1×2',  1, 2,  26.57),
    ('1×3',  1, 3,  18.43),
    ('1×4',  1, 4,  14.04),  # Slowest — weakest support
]

# ── Square of 9 angles (8 compass points at 45° intervals) ───────────────────
# Starting from 0°/East — these mark the strongest support/resistance levels
SO9_ANGLES = {
    'East'      :   0,
    'Northeast' :  45,
    'North'     :  90,
    'Northwest' : 135,
    'West'      : 180,
    'Southwest' : 225,
    'South'     : 270,
    'Southeast' : 315,
}

# ── Vedic/Gann planetary price conversion factors ─────────────────────────────
# Gann used a 1° longitude = 1 price unit scale factor; we expose the ratio
# as a configurable multiplier. For NSE stocks the typical range is 1–10.
DEFAULT_PRICE_FACTOR = 1.0  # 1 degree longitude = 1 price unit


class GannEngine:
    """Gann Square of 9, Planetary Lines, and Time Cycle calculations."""

    def __init__(self):
        try:
            import swisseph as swe
            self._swe = swe
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except ImportError:
            raise ImportError("pyswisseph not installed. Run: py -3.11 -m pip install pyswisseph")

    # ── Public API ────────────────────────────────────────────────────────────

    def analyse(self, price: float, date_str: Optional[str] = None,
                price_factor: float = DEFAULT_PRICE_FACTOR) -> dict:
        """
        Return full Gann analysis for a price level on a given date.
        date_str: YYYY-MM-DD (defaults to today)
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        jd_now = self._date_to_jd(date_str)

        return {
            'price':              price,
            'date':               date_str,
            'square_of_9':        self.square_of_9(price),
            'gann_levels':        self.gann_price_levels(price),
            'gann_fan':           self.gann_fan(price),
            'planetary_lines':    self.planetary_lines(jd_now, price_factor),
            'time_cycles':        self.solar_time_cycles(date_str),
            'convergence_zones':  self.price_time_convergence(price, jd_now, price_factor),
            'price_angle':        self.price_degree(price),
        }

    # ── Square of 9 ───────────────────────────────────────────────────────────

    def price_degree(self, price: float) -> dict:
        """
        Convert a price to its angular position in the Square of 9 spiral.
        degree(N) = MOD((SQRT(N) * 180) - 225, 360)
        """
        if price <= 0:
            return {'degree': 0, 'cardinal': 'unknown', 'so9_value': 0}
        deg = (math.sqrt(price) * 180 - 225) % 360
        cardinal = self._nearest_cardinal(deg)
        return {
            'degree':   round(deg, 2),
            'cardinal': cardinal,
            'so9_value': price,
        }

    def square_of_9(self, price: float, num_rings: int = 3) -> dict:
        """
        Compute Square of 9 support/resistance levels at all 8 angles.
        Returns support/resistance for each compass direction.

        For each angle A (0, 45, 90, 135, 180, 225, 270, 315):
          Resistance = (SQRT(P) + (A + k*360) / 180) ^ 2
          Support    = (SQRT(P) - (A + k*360) / 180) ^ 2
          where k = 0, 1, 2...
        """
        if price <= 0:
            return {'error': 'Price must be positive'}

        sq = math.sqrt(price)
        current_deg = (sq * 180 - 225) % 360

        levels = {}
        for direction, angle in SO9_ANGLES.items():
            resistances = []
            supports    = []
            for k in range(num_rings):
                # Resistance levels (moving up the spiral)
                increment = (angle + k * 360) / 180
                r_val = (sq + increment) ** 2
                if r_val > price:
                    resistances.append(round(r_val, 2))

                # Support levels (moving down the spiral)
                decrement = (angle + k * 360) / 180
                s_val = (sq - decrement) ** 2
                if s_val > 0 and s_val < price:
                    supports.append(round(s_val, 2))

            # Distance from current price degree to this angle
            angle_diff = abs((current_deg - angle + 180) % 360 - 180)

            levels[direction] = {
                'angle':       angle,
                'distance_deg': round(angle_diff, 1),
                'resistances':  sorted(resistances)[:3],
                'supports':     sorted(supports, reverse=True)[:3],
                'is_nearest':   angle_diff < 10,
            }

        # Next turn date from nearest cardinal
        nearest = min(levels.items(), key=lambda x: x[1]['distance_deg'])

        return {
            'current_price':  price,
            'current_degree': round(current_deg, 2),
            'levels':         levels,
            'nearest_angle':  nearest[0],
            'nearest_gap_deg': nearest[1]['distance_deg'],
        }

    def gann_price_levels(self, price: float, num_levels: int = 5) -> dict:
        """
        Compute key Gann price levels at the 4 cardinal angles (0°, 90°, 180°, 270°).
        These are the strongest support/resistance points.
        """
        sq = math.sqrt(price)
        result = {}
        for k in range(1, num_levels + 1):
            for angle_name, angle in [('0deg', 0), ('90deg', 90), ('180deg', 180), ('270deg', 270)]:
                key = f'L{k}_{angle_name}'
                r = (sq + (angle / 180) + (k - 1) * 2) ** 2
                s = (sq - (angle / 180) - (k - 1) * 2) ** 2
                if r > price:
                    result.setdefault('resistance', []).append(round(r, 2))
                if s > 0 and s < price:
                    result.setdefault('support', []).append(round(s, 2))

        # Clean and deduplicate
        resistances = sorted(set(result.get('resistance', [])))[:num_levels]
        supports    = sorted(set(result.get('support',    [])), reverse=True)[:num_levels]

        return {
            'current_price': price,
            'resistance':    resistances,
            'support':       supports,
            'key_r1':        resistances[0] if resistances else None,
            'key_s1':        supports[0]    if supports    else None,
        }

    # ── Gann Fan ─────────────────────────────────────────────────────────────

    def gann_fan(self, pivot_price: float, pivot_date_str: str = None,
                 current_date_str: str = None) -> dict:
        """
        Compute Gann Fan angle prices for the current date from a pivot.
        Returns where each fan line stands today.
        If dates not provided, returns the angle slopes only.
        """
        if pivot_date_str and current_date_str:
            d1 = datetime.strptime(pivot_date_str, '%Y-%m-%d')
            d2 = datetime.strptime(current_date_str, '%Y-%m-%d')
            trading_days = max(1, (d2 - d1).days * 252 / 365)
        else:
            trading_days = 0

        fan_lines = {}
        for angle_name, num, den, degrees in GANN_ANGLES:
            slope = num / den  # price units per time unit
            if trading_days > 0:
                price_at_date = pivot_price + slope * trading_days
                fan_lines[angle_name] = {
                    'slope':          round(slope, 4),
                    'degrees':        degrees,
                    'price_at_date':  round(price_at_date, 2),
                    'above_current':  price_at_date > pivot_price,
                }
            else:
                fan_lines[angle_name] = {
                    'slope':   round(slope, 4),
                    'degrees': degrees,
                }

        return {
            'pivot_price': pivot_price,
            'fan_lines':   fan_lines,
            'primary_1x1': fan_lines.get('1×1', {}),
        }

    # ── Planetary Lines ───────────────────────────────────────────────────────

    _PLANET_IDS = {
        'Sun':     0, 'Moon':    1, 'Mercury': 2, 'Venus':  3,
        'Mars':    4, 'Jupiter': 5, 'Saturn':  6, 'Uranus': 7,
        'Neptune': 8,
    }

    def planetary_lines(self, jd: float,
                        price_factor: float = DEFAULT_PRICE_FACTOR) -> dict:
        """
        Map geocentric sidereal planet longitudes to price levels.
        Gann formula: Price = Longitude * price_factor

        Also compute 90°, 180°, 270° multiples for harmonic levels.
        """
        swe    = self._swe
        flags  = swe.FLG_SIDEREAL | swe.FLG_SPEED
        result = {}

        for planet, pid in self._PLANET_IDS.items():
            xx, _ = swe.calc_ut(jd, pid, flags)
            lon   = xx[0] % 360

            base_price   = lon * price_factor
            harmonics    = [
                round(base_price, 2),
                round(lon * price_factor * 2, 2),
                round(lon * price_factor * 0.5, 2),
            ]
            # 90° intervals
            quadrant_prices = [
                round((lon + 90 * k) % 360 * price_factor, 2)
                for k in range(4)
            ]

            result[planet] = {
                'longitude':        round(lon, 2),
                'base_price':       round(base_price, 2),
                'harmonics':        sorted(set(harmonics)),
                'quadrant_levels':  sorted(set(quadrant_prices)),
            }

        # Rahu (True Node)
        xx, _ = swe.calc_ut(jd, swe.TRUE_NODE, flags)
        rahu_lon = xx[0] % 360
        result['Rahu'] = {
            'longitude':  round(rahu_lon, 2),
            'base_price': round(rahu_lon * price_factor, 2),
            'harmonics':  [round(rahu_lon * price_factor * m, 2) for m in [0.5, 1, 2]],
        }
        result['Ketu'] = {
            'longitude':  round((rahu_lon + 180) % 360, 2),
            'base_price': round(((rahu_lon + 180) % 360) * price_factor, 2),
        }

        return result

    # ── Solar Time Cycles ─────────────────────────────────────────────────────

    def solar_time_cycles(self, date_str: str) -> dict:
        """
        Compute the 4 cardinal solar transit dates from the most recent
        major cycle start: 90°, 180°, 270°, 360° of solar travel.

        These correspond to seasonal turns (equinoxes/solstices) that
        Gann observed as high-probability turning point zones.
        """
        swe     = self._swe
        jd      = self._date_to_jd(date_str)
        flags   = swe.FLG_SIDEREAL | swe.FLG_SPEED
        xx, _   = swe.calc_ut(jd, 0, flags)  # Sun
        sun_lon = xx[0] % 360

        # Find last time Sun was at 0° (Aries ingress = Vedic New Year)
        # Walk back to find approximate date
        days_since_aries = (sun_lon / 360) * 365.25
        jd_aries_start   = jd - days_since_aries

        cycle_dates = {}
        for label, deg in [('Q1_90deg', 90), ('Q2_180deg', 180),
                           ('Q3_270deg', 270), ('Q4_360deg', 360)]:
            jd_target = jd_aries_start + (deg / 360) * 365.25
            date = self._jd_to_date(jd_target)
            elapsed_days = (jd_target - jd_aries_start)
            is_past = jd > jd_target
            cycle_dates[label] = {
                'date':         date,
                'degree':       deg,
                'elapsed_days': round(elapsed_days, 0),
                'is_past':      is_past,
                'near_turn':    abs(jd - jd_target) < 7,  # within 1 week
            }

        # Planetary periods (approximate synodic cycles in days)
        synodic_cycles = {
            'Mars_synodic':    780,
            'Jupiter_synodic': 399,
            'Saturn_synodic':  378,
            'Venus_synodic':   584,
            'Mercury_synodic':  116,
        }
        planetary_turns = {}
        for name, period in synodic_cycles.items():
            # Quarters of the synodic cycle from today
            for fraction, label in [(0.25, 'Q1'), (0.5, 'Q2'), (0.75, 'Q3'), (1.0, 'Full')]:
                jd_turn = jd + period * fraction
                near    = period * fraction < 14  # within 2 weeks
                planetary_turns[f'{name}_{label}'] = {
                    'date':     self._jd_to_date(jd_turn),
                    'days_out': round(period * fraction, 0),
                    'near_turn': near,
                }

        # 90-day, 180-day, 270-day, 360-day from today
        fixed_cycles = {}
        for days in [45, 90, 180, 270, 360]:
            fixed_cycles[f'{days}d'] = self._jd_to_date(jd + days)

        return {
            'current_sun_degree': round(sun_lon, 2),
            'solar_year_quarters': cycle_dates,
            'fixed_future_dates':  fixed_cycles,
        }

    # ── Price-Time Convergence ────────────────────────────────────────────────

    def price_time_convergence(self, price: float, jd: float,
                               price_factor: float) -> list[dict]:
        """
        Find zones where a planetary price level AND a time cycle coincide.
        These are Gann's highest-probability turning points.
        """
        swe     = self._swe
        flags   = swe.FLG_SIDEREAL | swe.FLG_SPEED
        zones   = []

        for planet, pid in list(self._PLANET_IDS.items())[:7]:  # Main planets
            xx, _ = swe.calc_ut(jd, pid, flags)
            lon   = xx[0] % 360
            speed = xx[3]  # degrees/day

            # Price level from this planet
            pl_price = lon * price_factor

            # How many days until this planet's longitude creates
            # a Square of 9 confluence with current price?
            target_lon = price / price_factor
            if abs(target_lon - 360) < 180:
                days_to_lon = abs(target_lon - lon) / abs(speed) if speed != 0 else None
                if days_to_lon is not None and days_to_lon < 90:
                    confluence_date = self._jd_to_date(jd + days_to_lon)
                    price_diff_pct  = abs(pl_price - price) / price * 100

                    if price_diff_pct < 20:
                        strength = 'strong' if price_diff_pct < 5 else 'moderate'
                        zones.append({
                            'planet':            planet,
                            'planet_longitude':  round(lon, 2),
                            'planet_price':      round(pl_price, 2),
                            'current_price':     price,
                            'price_diff_pct':    round(price_diff_pct, 1),
                            'days_to_confluence': round(days_to_lon, 0),
                            'confluence_date':   confluence_date,
                            'strength':          strength,
                        })

        zones.sort(key=lambda x: x['price_diff_pct'])
        return zones[:5]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _nearest_cardinal(deg: float) -> str:
        for direction, angle in SO9_ANGLES.items():
            if abs(deg - angle) < 22.5 or abs(deg - angle - 360) < 22.5:
                return direction
        return 'East'

    def _date_to_jd(self, date_str: str) -> float:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return self._swe.julday(d.year, d.month, d.day, 12.0)

    def _jd_to_date(self, jd: float) -> str:
        y, m, d, h = self._swe.revjul(jd)
        try:
            return datetime(y, m, int(d)).strftime('%Y-%m-%d')
        except Exception:
            return f'{y}-{m:02d}-{int(d):02d}'

    # ── Bulk runner ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        """
        Compute Gann levels for all stocks in kundli_signals.csv
        and append gann_* columns to a new gann_signals.csv.
        """
        import pandas as pd
        import shutil

        kundli_csv = cfg.INTELLIGENCE_DIR / 'kundli_signals.csv'
        if not kundli_csv.exists():
            logger.error('[GannEngine] kundli_signals.csv not found — run kundli_engine first')
            return False

        # Load latest prices from price_momentum.csv
        momentum_csv = cfg.INTELLIGENCE_DIR / 'price_momentum.csv'
        if not momentum_csv.exists():
            logger.error('[GannEngine] price_momentum.csv not found')
            return False

        prices = pd.read_csv(momentum_csv, usecols=['symbol', 'close'])\
                   .set_index('symbol')['close'].to_dict()

        kundli = pd.read_csv(kundli_csv)
        today  = datetime.now().strftime('%Y-%m-%d')
        rows   = []

        for _, row in kundli.iterrows():
            symbol = row['symbol']
            price  = prices.get(symbol)
            if not price or price <= 0:
                continue

            try:
                jd     = self._date_to_jd(today)
                so9    = self.square_of_9(price)
                levels = self.gann_price_levels(price)
                rows.append({
                    'symbol':          symbol,
                    'price':           price,
                    'so9_degree':      so9['current_degree'],
                    'so9_nearest':     so9['nearest_angle'],
                    'so9_r1':          levels['key_r1'],
                    'so9_s1':          levels['key_s1'],
                    'all_resistance':  '|'.join(str(x) for x in levels['resistance']),
                    'all_support':     '|'.join(str(x) for x in levels['support']),
                    'computed_date':   today,
                })
            except Exception as exc:
                logger.warning('[GannEngine] Skip %s: %s', symbol, exc)

        if not rows:
            logger.error('[GannEngine] No rows computed')
            return False

        out_csv = cfg.INTELLIGENCE_DIR / 'gann_signals.csv'
        tmp_csv = out_csv.with_suffix('.tmp.csv')
        df = pd.DataFrame(rows)
        df.to_csv(tmp_csv, index=False)
        shutil.move(str(tmp_csv), str(out_csv))
        logger.info('[GannEngine] Complete — %d rows saved to %s', len(rows), out_csv)
        return True


if __name__ == '__main__':
    engine = GannEngine()
    price  = 2800.0  # Test price (e.g. Reliance CMP)
    result = engine.analyse(price)

    so9 = result['square_of_9']
    print(f"Price: {price}")
    print(f"SO9 Degree: {so9['current_degree']} deg  |  Nearest: {so9['nearest_angle']}")

    levels = result['gann_levels']
    print(f"R1: {levels.get('key_r1')}  |  S1: {levels.get('key_s1')}")
    print(f"Resistances: {levels['resistance']}")
    print(f"Supports:    {levels['support']}")

    cycles = result['time_cycles']
    print(f"Sun at {cycles['current_sun_degree']} degrees sidereal")
    print(f"Fixed future dates: {cycles['fixed_future_dates']}")
