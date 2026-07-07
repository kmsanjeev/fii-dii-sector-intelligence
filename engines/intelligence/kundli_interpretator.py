"""
Kundli Interpretator — Phase KU-3
Rule-based financial interpretation of Vedic natal charts + LLM narrative.

Given a computed Kundli dict, produces:
  - Structured financial interpretation (bullish / bearish factors)
  - Dasha phase outlook (current + next 3 transitions)
  - Gann confluence summary
  - Short LLM narrative via llm_client.py (2-3 sentences)
  - Final STRONG_BUY / BUY / HOLD / CAUTION / EXIT / AVOID signal

Run standalone:
  py -3.11 engines/intelligence/kundli_interpretator.py
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Planet financial keywords ──────────────────────────────────────────────────
PLANET_FINANCIAL = {
    'Sun':     'management authority, corporate governance, CEO quality',
    'Moon':    'market sentiment, retail flows, brand perception, liquidity',
    'Mars':    'expansion, M&A activity, aggressive competition, energy sector',
    'Mercury': 'communication, IT sector, analyst coverage, earnings clarity',
    'Jupiter': 'growth trajectory, institutional confidence, banking/finance sector',
    'Venus':   'luxury/FMCG sector, cash flow generation, dividends',
    'Saturn':  'operational efficiency, debt management, long-term discipline',
    'Rahu':    'disruptive technology, unconventional plays, speculative fervor',
    'Ketu':    'restructuring, divestments, sector transformation, past karma',
}

# ── Dasha financial interpretations ───────────────────────────────────────────
DASHA_FINANCIAL = {
    'Sun':     'Strong management initiatives; good for frontline blue-chips',
    'Moon':    'Sentiment-driven phase; liquidity flows dominate; volatile',
    'Mars':    'Expansion phase; M&A deals, capex, energy stocks outperform',
    'Mercury': 'IT/communication sector boost; earnings revision period',
    'Jupiter': 'Institutional buying; banking/finance outperform; debt resolution',
    'Venus':   'FMCG/auto/luxury perform well; steady cash generation',
    'Saturn':  'Efficiency focus; operational fixes; high-debt companies lag',
    'Rahu':    'Speculative excess; tech/pharma/crypto themes; high volatility',
    'Ketu':    'Restructuring; promoter selling possible; deep-value search',
}

# ── House lord rulerships (financial significance) ────────────────────────────
BULLISH_HOUSES  = {2, 5, 9, 10, 11}
BEARISH_HOUSES  = {6, 8, 12}
NEUTRAL_HOUSES  = {1, 3, 4, 7}

# ── Dignity scores (used in interpretation) ───────────────────────────────────
DIGNITY_SCORE = {
    'exalted_exact': 5, 'exalted': 4, 'moolatrikona': 3,
    'own_sign': 3, 'friendly': 1, 'neutral': 0,
    'enemy': -1, 'debilitated': -4,
}


class KundliInterpretator:
    """
    Interprets a Kundli dict and produces financial signals and narrative.
    """

    def interpret(self, kundli: dict, gann: Optional[dict] = None,
                  generate_narrative: bool = True) -> dict:
        """
        Produce full interpretation for a Kundli dict.

        Args:
            kundli:   Output from KundliEngine.compute()
            gann:     Optional output from GannEngine.analyse()
            generate_narrative: If True, calls llm_client.call_llm for a short summary

        Returns dict with:
            bullish_factors, bearish_factors, dasha_outlook,
            gann_summary, signal, score, narrative
        """
        if kundli is None or 'planets' not in kundli:
            return {'error': 'Invalid kundli data'}

        planets    = kundli.get('planets', {})
        lagna      = kundli.get('lagna', {})
        dasha      = kundli.get('current_dasha', {})
        yogas      = kundli.get('yogas', [])
        fin_houses = kundli.get('financial_houses', {})
        transits   = kundli.get('transits', {})
        entity     = kundli.get('entity', {})

        bullish  = []
        bearish  = []
        score    = kundli.get('astro_score', 0.0)

        # ── 1. Dasha analysis ──────────────────────────────────────────────────
        maha_planet  = dasha.get('mahadasha', {}).get('planet', '')
        antar_planet = dasha.get('antardasha', {}).get('planet', '')
        maha_end     = dasha.get('mahadasha', {}).get('end_date', '')

        dasha_interpretation = DASHA_FINANCIAL.get(maha_planet, 'Mixed signals')
        antar_interpretation = DASHA_FINANCIAL.get(antar_planet, '')

        if maha_planet in ('Jupiter', 'Venus', 'Sun', 'Moon'):
            bullish.append(f"Mahadasha: {maha_planet} — {dasha_interpretation} (until {maha_end})")
        elif maha_planet in ('Rahu', 'Ketu'):
            bearish.append(f"Mahadasha: {maha_planet} — {dasha_interpretation} (until {maha_end})")
        else:  # Mars, Mercury, Saturn
            if planets.get(maha_planet, {}).get('dignity', '') in ('exalted', 'moolatrikona', 'own_sign'):
                bullish.append(f"Mahadasha: {maha_planet} (dignified) — {dasha_interpretation}")
            elif planets.get(maha_planet, {}).get('dignity', '') == 'debilitated':
                bearish.append(f"Mahadasha: {maha_planet} (debilitated) — {dasha_interpretation}")
            else:
                bullish.append(f"Mahadasha: {maha_planet} — {dasha_interpretation}")

        # ── 2. Key house lords ─────────────────────────────────────────────────
        for house_key, house_data in fin_houses.items():
            lord     = house_data.get('lord', '')
            strength = house_data.get('strength', '')
            h_num    = int(house_key.replace('H', ''))
            sign     = house_data.get('sign', '')
            dignity  = house_data.get('lord_dignity', '')

            if h_num in (11, 2) and strength in ('strong', 'moderate-strong'):
                bullish.append(
                    f"{house_key} lord {lord} in {sign} ({dignity}) — "
                    f"Strong {FINANCIAL_HOUSES_SHORT.get(h_num, 'profits')}"
                )
            elif h_num in (11, 2) and strength == 'weak':
                bearish.append(
                    f"{house_key} lord {lord} in {sign} ({dignity}) — "
                    f"Weak {FINANCIAL_HOUSES_SHORT.get(h_num, 'profits')}"
                )

            if h_num == 8 and strength in ('strong',):
                bearish.append(
                    f"8H (volatility) lord {lord} strong — "
                    "sudden reversals, possible M&A disruption"
                )

        # ── 3. Yogas ──────────────────────────────────────────────────────────
        for yoga in yogas:
            name   = yoga.get('name', '')
            effect = yoga.get('effect', '')
            signal = yoga.get('signal', 'HOLD')
            if signal == 'BUY':
                bullish.append(f"Yoga: {name} — {effect}")
            elif signal in ('CAUTION', 'EXIT', 'AVOID'):
                bearish.append(f"Yoga: {name} — {effect}")

        # ── 4. Transit triggers ───────────────────────────────────────────────
        jup_transit = transits.get('Jupiter', {})
        if jup_transit.get('aspect') == 'trine':
            bullish.append("Jupiter trine natal Jupiter — expansion, institutional confidence building")
        elif jup_transit.get('aspect') == 'conjunction':
            bullish.append("Jupiter conjunct natal Jupiter — Jupiter Return, major growth cycle begins")

        sat_transit = transits.get('Saturn', {})
        if sat_transit.get('aspect') == 'opposition':
            bearish.append("Saturn opposing natal Saturn — Saturn Opposition, operational stress, restructuring")
        elif sat_transit.get('aspect') == 'conjunction':
            bearish.append("Saturn Return — consolidation phase, clearing old structures before renewal")

        rahu_transit = transits.get('Rahu', {})
        if rahu_transit.get('aspect') == 'conjunction':
            bearish.append("Rahu transiting natal Rahu — 18-year cycle completion, speculative reset")

        # ── 5. Planetary dignities (key planets) ──────────────────────────────
        for planet in ('Jupiter', 'Venus', 'Moon'):
            if planet in planets:
                dignity = planets[planet].get('dignity', '')
                house   = planets[planet].get('house', 0)
                if dignity in ('exalted', 'exalted_exact'):
                    bullish.append(
                        f"{planet} exalted in H{house} — "
                        f"{PLANET_FINANCIAL.get(planet, '').split(',')[0]} enhanced"
                    )
                elif dignity == 'debilitated':
                    bearish.append(
                        f"{planet} debilitated in H{house} — "
                        f"{PLANET_FINANCIAL.get(planet, '').split(',')[0]} under stress"
                    )

        # ── 6. Retrograde planets in key houses ───────────────────────────────
        for planet in ('Jupiter', 'Saturn', 'Mars'):
            if planet in planets and planets[planet].get('retrograde'):
                house = planets[planet].get('house', 0)
                if house in (1, 2, 5, 10, 11):
                    bearish.append(
                        f"{planet} retrograde in H{house} — "
                        "internalized energy, delayed manifestation"
                    )

        # ── 7. Gann summary ───────────────────────────────────────────────────
        gann_summary = self._gann_summary(gann) if gann else {}

        # ── 8. Dasha outlook (next transitions) ───────────────────────────────
        dasha_outlook = self._dasha_outlook(dasha)

        # ── 9. Determine final signal ─────────────────────────────────────────
        bull_weight = len(bullish) * 2
        bear_weight = len(bearish) * 2
        raw_score   = score + (bull_weight - bear_weight) * 3

        if raw_score >= 50:  signal = 'STRONG_BUY'
        elif raw_score >= 30: signal = 'BUY'
        elif raw_score >= 10: signal = 'HOLD'
        elif raw_score >= -10: signal = 'CAUTION'
        elif raw_score >= -25: signal = 'EXIT'
        else:                  signal = 'AVOID'

        interpretation = {
            'entity':           entity.get('name', ''),
            'entity_type':      entity.get('type', ''),
            'signal':           signal,
            'astro_score':      round(raw_score, 1),
            'bullish_factors':  bullish[:10],
            'bearish_factors':  bearish[:10],
            'dasha_outlook':    dasha_outlook,
            'gann_summary':     gann_summary,
            'yogas':            [y['name'] for y in yogas],
            'computed_date':    datetime.now().strftime('%Y-%m-%d'),
        }

        # ── 10. LLM narrative ─────────────────────────────────────────────────
        if generate_narrative:
            interpretation['narrative'] = self._generate_narrative(
                interpretation, kundli
            )
        else:
            interpretation['narrative'] = ''

        return interpretation

    # ── Gann summary ─────────────────────────────────────────────────────────

    def _gann_summary(self, gann: dict) -> dict:
        so9    = gann.get('square_of_9', {})
        levels = gann.get('gann_levels', {})
        cycles = gann.get('time_cycles', {})

        # Identify near-turn dates
        near_turns = [
            k for k, v in cycles.get('solar_year_quarters', {}).items()
            if v.get('near_turn')
        ]

        return {
            'current_degree':  so9.get('current_degree'),
            'nearest_angle':   so9.get('nearest_angle'),
            'key_resistance':  levels.get('key_r1'),
            'key_support':     levels.get('key_s1'),
            'near_turn_dates': near_turns,
            'all_resistance':  levels.get('resistance', [])[:3],
            'all_support':     levels.get('support', [])[:3],
        }

    # ── Dasha outlook ─────────────────────────────────────────────────────────

    def _dasha_outlook(self, dasha: dict) -> list[dict]:
        """Return next 3 dasha transitions with financial context."""
        all_mahadashas = dasha.get('all_mahadashas', [])
        result = []
        for m in all_mahadashas[:5]:
            planet = m.get('planet', '')
            result.append({
                'period':      f"{planet} Mahadasha",
                'start':       m.get('start_date', ''),
                'end':         m.get('end_date', ''),
                'outlook':     DASHA_FINANCIAL.get(planet, ''),
                'planet_role': PLANET_FINANCIAL.get(planet, ''),
            })
        return result[:4]

    # ── LLM narrative ─────────────────────────────────────────────────────────

    def _generate_narrative(self, interpretation: dict, kundli: dict) -> str:
        try:
            from engines.common.llm_client import call_llm
        except ImportError:
            return ''

        entity_name = interpretation.get('entity', 'this entity')
        entity_type = interpretation.get('entity_type', 'stock')
        signal      = interpretation.get('signal', 'HOLD')
        score       = interpretation.get('astro_score', 0)
        maha        = kundli.get('current_dasha', {}).get('mahadasha', {})
        yogas       = interpretation.get('yogas', [])

        bullish_pts = '; '.join(interpretation.get('bullish_factors', [])[:3])
        bearish_pts = '; '.join(interpretation.get('bearish_factors', [])[:2])

        system = (
            "You are a senior Vedic astrology analyst specializing in financial markets. "
            "Produce concise, actionable 2-3 sentence financial interpretations. "
            "Be specific about planetary influences. Avoid vague generalities. "
            "Always mention the current Mahadasha period and its financial implication."
        )

        user = (
            f"Entity: {entity_name} ({entity_type})\n"
            f"Signal: {signal} (score: {score})\n"
            f"Mahadasha: {maha.get('planet','')} until {maha.get('end_date','')}\n"
            f"Active Yogas: {', '.join(yogas) if yogas else 'None'}\n"
            f"Bullish factors: {bullish_pts}\n"
            f"Bearish factors: {bearish_pts}\n\n"
            "Write a 2-3 sentence financial outlook based on these planetary influences. "
            "Be direct. Start with the most important factor."
        )

        try:
            text = call_llm(system=system, user=user, max_tokens=200, temperature=0.2)
            return text.strip() if text else ''
        except Exception as exc:
            logger.warning('[KundliInterpretator] LLM narrative failed: %s', exc)
            return ''


# ── House short names ─────────────────────────────────────────────────────────
FINANCIAL_HOUSES_SHORT = {
    1:  'brand/identity',
    2:  'balance sheet',
    3:  'marketing',
    4:  'fixed assets',
    5:  'speculation/R&D',
    6:  'debt/competition',
    7:  'partnerships',
    8:  'volatility',
    9:  'long-term fortune',
    10: 'management',
    11: 'revenue/profits',
    12: 'losses/write-offs',
}


if __name__ == '__main__':
    from engines.intelligence.kundli_engine import KundliEngine
    from engines.intelligence.gann_engine import GannEngine

    ke = KundliEngine()
    ge = GannEngine()
    ki = KundliInterpretator()

    chart = ke.compute_stock('RELIANCE', '2000-11-18', 'NSE')
    if chart:
        gann = ge.analyse(2800.0)
        result = ki.interpret(chart, gann, generate_narrative=False)

        print(f"Signal: {result['signal']}  |  Score: {result['astro_score']}")
        print("Bullish:")
        for b in result['bullish_factors']:
            print(f"  + {b}")
        print("Bearish:")
        for b in result['bearish_factors']:
            print(f"  - {b}")
        if result.get('narrative'):
            print(f"Narrative: {result['narrative']}")
    else:
        print('Kundli computation failed.')
