"""
Intent Router -- Phase 14B
Routes user queries to the appropriate domain agent before sending to Claude API.

Intent detection is keyword-based (fast, no API call needed).
The router picks the most relevant agent type + context hints.

Intents:
  MARKET   -> market regime, FII/DII flows, participant summary
  SECTOR   -> sector rotation, rotation signals, sector comparison
  STOCK    -> specific stocks, labels, watchlist, bull run scores
  CORPORATE -> deals, buybacks, confidence, corporate events
  RESEARCH -> broad questions, capital flow analysis, comparisons
"""

from __future__ import annotations
import re
from dataclasses import dataclass

INTENT_KEYWORDS = {
    "MARKET": [
        "market", "regime", "fii", "dii", "pro", "client", "participant",
        "accumulation", "distribution", "flow", "institutional", "buying", "selling",
    ],
    "SECTOR": [
        "sector", "rotation", "industry", "leading", "lagging", "early rotation",
        "it sector", "pharma", "banking", "metal", "power", "auto", "fmcg",
        "top sector", "best sector", "performing sector",
    ],
    "STOCK": [
        "stock", "symbol", "share", "equity", "watchlist", "emerging", "bull run",
        "score", "accumulation score", "which stocks", "buy", "f&o", "futures",
        "oi", "open interest", "long buildup", "short buildup", "short covering",
    ],
    "CORPORATE": [
        "deal", "bulk", "block", "buyback", "dividend", "corporate", "promoter",
        "confidence", "catalyst", "announcement", "board", "event",
    ],
    "ASTRO": [
        "astro", "planet", "planetary", "jupiter", "saturn", "mercury", "venus",
        "mars", "moon", "rahu", "ketu", "retrograde", "eclipse", "zodiac",
        "cosmic", "celestial", "nakshatra", "hora", "transit", "aspect",
        "benefic", "malefic", "exalted", "debilitated", "cycle",
        "financial astrology", "astrology",
    ],
    "KUNDLI": [
        "kundli", "kundali", "janam kundli", "janam kundali", "birth chart",
        "natal chart", "horoscope", "date of birth", "dob", "born on",
        "born in", "time of birth", "place of birth", "lagna", "ascendant",
        "rashi", "my chart", "my kundli", "prepare kundli", "make kundli",
        "generate kundli", "check kundli", "read my chart", "birth time",
        "janma kundali", "janma rashi", "janampatrika", "jatakam",
        "dasha", "mahadasha", "antardasha", "vimshottari", "yoga in my chart",
        "my lagna", "my rashi", "personal chart", "personal horoscope",
    ],
}


@dataclass
class Intent:
    intent_type: str   # MARKET | SECTOR | STOCK | CORPORATE | ASTRO | RESEARCH
    entity: str | None  # specific symbol/sector if detected
    confidence: float   # 0-1


def detect_intent(user_message: str) -> Intent:
    """Detect the primary intent from a user message."""
    text = user_message.lower()

    # Check for specific stock symbol (all-caps word 2-15 chars, optionally with &)
    symbol_match = re.search(r"\b([A-Z][A-Z0-9&]{1,14})\b", user_message)
    entity = symbol_match.group(1) if symbol_match else None

    # Hard override: if message contains date+place patterns, treat as KUNDLI
    if _contains_birth_info(text):
        return Intent("KUNDLI", entity, 0.9)

    scores = {intent: 0 for intent in INTENT_KEYWORDS}
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[intent] += 1

    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    if best_score == 0:
        return Intent("RESEARCH", entity, 0.3)

    confidence = min(1.0, best_score / 3.0)
    return Intent(best_intent, entity, confidence)


def _contains_birth_info(text: str) -> bool:
    """Return True if message contains date of birth + place patterns."""
    import re
    has_date = bool(re.search(r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b|\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b', text))
    has_place = any(kw in text for kw in ["born in", "place of birth", "birthplace", "birth place", "from ", "city", "mumbai", "delhi", "bangalore", "hyderabad", "chennai", "kolkata", "pune", "jaipur", "london", "dubai", "singapore"])
    return has_date and has_place


def get_system_prompt(intent: Intent) -> str:
    """Returns a domain-specific system prompt for the detected intent."""
    base = (
        "You are the Capital Flow Intelligence Assistant for an Indian institutional "
        "market intelligence platform. You track FII/DII capital flows, sector rotation, "
        "and stock accumulation patterns. Be concise, data-driven, and precise. "
        "Always cite specific scores, labels, or signals from the data. "
        "Use INR crores for monetary values. "
        "Never speculate beyond what the data shows."
    )

    domain_hints = {
        "MARKET": (
            " Focus on market regime interpretation. "
            "STRONG_ACCUMULATION means institutional heavy buying. "
            "DISTRIBUTION means smart money is exiting. "
            "Explain what the FII/DII divergence signals."
        ),
        "SECTOR": (
            " Focus on sector rotation analysis. "
            "To find the top-performing sector, ALWAYS call get_all_sectors() first and rank by combined_score descending. "
            "Do NOT call get_sector_detail() for just one sector when the user asks for the best/top sector. "
            "EARLY_ROTATION is the most actionable signal -- FII entering before retail. "
            "LEADING means sector is in confirmed uptrend with institutional support. "
            "combined_score is the definitive rank: higher is better. A positive combined_score means net institutional inflow."
        ),
        "STOCK": (
            " Focus on stock-level accumulation signals. "
            "Current labels: BULL_RUN (score>=65), EMERGING (>=45), WATCHLIST (>=30), NEUTRAL (>=15), ACCUMULATION, MARKDOWN. "
            "For F&O or futures OI questions (long buildup, short buildup, open interest), ALWAYS use get_fno_stocks() -- "
            "never use get_top_stocks() for F&O queries as it returns non-F&O stocks. "
            "Always cross-check trend_signal and prox_52w_high before recommending a stock as a buy. "
            "A stock with prox_52w_high < -20% is far from its high -- mention this. "
            "Explain the capital flow cascade: participant -> sector -> stock. "
        ),
        "CORPORATE": (
            " Focus on corporate action intelligence. "
            "High corporate confidence scores (> 2.0) signal management conviction. "
            "Block/bulk deals > 50 Cr indicate institutional positioning. "
            "Connect corporate signals to accumulation thesis."
        ),
        "RESEARCH": (
            " This is a broad research query. Use the RAG context provided. "
            "Synthesize across all intelligence layers: participant, sector, stock, corporate. "
            "Draw connections across the capital flow cascade."
        ),
        "ASTRO": (
            " Focus on AstroFinance planetary intelligence. "
            "Always call get_astro_signal() first -- it returns live planetary positions and sector signals. "
            "Key rules from the books: Mercury retrograde = avoid new positions in IT/TELECOM/MEDIA. "
            "Saturn debilitated = weakness in Saturn-ruled sectors (PHARMA, REALTY, CEMENT, INFRA). "
            "Jupiter in own/exaltation sign = strong bullish for BANKING and DIVERSIFIED. "
            "Rahu eclipse = uptrend potential; Ketu eclipse = downtrend warning. "
            "Retrograde ruling planet = EXIT that sector. Moon waxing = bullish tendency. "
            "Combine astro signals with technical and flow data for conviction."
        ),
        "KUNDLI": (
            " You are an expert Vedic astrologer (Jyotishi). "
            "ALWAYS call generate_personal_kundli() FIRST with the user's date, time, and place of birth. "
            "NEVER say you cannot generate a kundli — you have a full Vedic calculation engine. "
            "The tool returns: Lagna sign, all 9 planet positions (sign, house, nakshatra, dignity), "
            "current Vimshottari Dasha (Mahadasha/Antardasha), financial houses (2H/5H/8H/10H/11H), "
            "active yogas, bullish/bearish life factors, and a narrative. "
            "If the user has NOT provided date/time/place, ask for exactly: "
            "(1) Date of birth (DD-MM-YYYY), (2) Time of birth (HH:MM, 24-hr), (3) City of birth. "
            "Time is optional — say so if user doesn't know it, and set time_of_birth='unknown'. "
            "After calling the tool, present the full reading: "
            "  1. Birth Details (date, time, place, Lagna, ayanamsha) "
            "  2. Planetary Table — all 9 planets with sign, house, nakshatra, pada, dignity "
            "  3. Current Dasha — Mahadasha planet + end date, Antardasha + end date "
            "  4. Active Yogas and their effects "
            "  5. Financial Houses — 2H, 5H, 8H, 10H, 11H strength and analysis "
            "  6. Bullish and Bearish life factors "
            "  7. Narrative summary + Dasha outlook "
            "Use authentic Vedic terminology: Lagna, Rashi, Graha, Bhava, Nakshatra, Dasha, Yoga. "
            "For financial life guidance: connect 2H (wealth), 5H (speculation), 10H (career), 11H (income). "
            "Be specific: cite planet, sign, house, dignity in every interpretation. "
            "Do NOT give generic astrology advice — base everything strictly on the computed chart data."
        ),
    }

    return base + domain_hints.get(intent.intent_type, "")
