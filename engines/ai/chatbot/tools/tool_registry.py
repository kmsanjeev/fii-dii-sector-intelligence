"""
Tool Registry -- Phase 14A
Defines Anthropic API tool schemas for the chatbot.
Each tool maps to a data_tools function.

Tools are passed to the Claude API as the `tools` parameter.
"""

from __future__ import annotations

TOOLS: list[dict] = [
    {
        "name": "get_market_regime",
        "description": (
            "Get the current market regime and institutional participant flow scores. "
            "Returns FII/DII/PRO/CLIENT flow scores and the overall Market_Regime "
            "(STRONG_ACCUMULATION, ACCUMULATION, NEUTRAL, DISTRIBUTION, STRONG_DISTRIBUTION)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_participant_history",
        "description": (
            "Get historical participant flow scores for the last N trading days. "
            "Useful for trend analysis: are FII/DII flows improving or deteriorating?"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "n_days": {
                    "type": "integer",
                    "description": "Number of past trading days to return (default: 30)",
                    "default": 30,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_all_sectors",
        "description": (
            "Get all 29 sectors with their rotation signals, FII/DII flow scores, "
            "and combined institutional flow scores."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sector_detail",
        "description": "Get detailed intelligence for a specific sector by name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Sector name (e.g. IT, PHARMA, BANKING, METAL, POWER)",
                }
            },
            "required": ["sector"],
        },
    },
    {
        "name": "get_sectors_by_signal",
        "description": (
            "Get all sectors matching a specific rotation signal. "
            "Signals: EARLY_ROTATION, LEADING, MOMENTUM, EMERGING, LAGGING, DECLINING, NEUTRAL, PRICE_LED, DISTRIBUTION."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "signal": {
                    "type": "string",
                    "description": "Rotation signal to filter by (e.g. EARLY_ROTATION, LEADING)",
                }
            },
            "required": ["signal"],
        },
    },
    {
        "name": "get_top_stocks",
        "description": (
            "Get the top stocks for a given label by bull_run_score, enriched with "
            "ML scores and technical trend signal. "
            "Current valid labels: BULL_RUN (score>=65), EMERGING (>=45), WATCHLIST (>=30), "
            "NEUTRAL (>=15), ACCUMULATION (institutional base-building), MARKDOWN (declining). "
            "Use BULL_RUN for strongest candidates, EMERGING for upcoming movers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Label to filter by (default: EMERGING). Valid: BULL_RUN, EMERGING, WATCHLIST, NEUTRAL, ACCUMULATION, MARKDOWN",
                    "default": "EMERGING",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of stocks to return (default: 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_fno_stocks",
        "description": (
            "Get F&O (futures & options) stocks filtered by OI signal. "
            "ONLY use this tool for questions about F&O stocks, futures OI, long buildup, "
            "short buildup, short covering, or open interest trends. "
            "Results are real NSE F&O-eligible stocks (210 universe), sorted by 5-day OI change. "
            "Valid signals: LONG_BUILDUP (bullish, rising price+OI), SHORT_BUILDUP (bearish), "
            "LONG_UNWINDING (bulls exiting), SHORT_COVERING (shorts being squeezed)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "signal": {
                    "type": "string",
                    "description": "OI signal to filter by (default: LONG_BUILDUP). Valid: LONG_BUILDUP, SHORT_BUILDUP, LONG_UNWINDING, SHORT_COVERING",
                    "default": "LONG_BUILDUP",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of stocks to return (default: 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_stock_detail",
        "description": (
            "Get the full intelligence profile for a specific stock symbol. "
            "Returns bull_run_score, label, price_score, deal_score, corporate_score, "
            "ML scores, sector, and corporate confidence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "NSE stock symbol (e.g. RELIANCE, TCS, INFY, ADANIENSOL)",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_stocks_by_sector",
        "description": "Get top stocks in a specific sector ranked by bull_run_score.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Sector name (e.g. IT, PHARMA, BANKING)",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of stocks to return (default: 10)",
                    "default": 10,
                },
            },
            "required": ["sector"],
        },
    },
    {
        "name": "get_institutional_deals",
        "description": (
            "Get recent institutional block/bulk deal signals. "
            "Returns deals above the minimum value threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "integer",
                    "description": "Number of deals to return (default: 20)",
                    "default": 20,
                },
                "min_value_cr": {
                    "type": "number",
                    "description": "Minimum deal value in crores (default: 10.0)",
                    "default": 10.0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_top_corporate_confidence",
        "description": (
            "Get stocks with the highest corporate confidence scores "
            "(based on promoter actions, buybacks, dividends, board announcements)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "top_n": {
                    "type": "integer",
                    "description": "Number of stocks to return (default: 20)",
                    "default": 20,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_astro_signal",
        "description": (
            "Get AstroFinance planetary intelligence. Returns current planetary positions, "
            "retrograde warnings (Mercury retrograde = avoid IT/TELECOM/MEDIA), Moon phase, "
            "eclipse status, and BUY/HOLD/CAUTION/EXIT/AVOID action for a sector. "
            "Based on Vedic Indian planet-sector mapping (Banerjee 2009) + Western aspect theory "
            "(Pesavento 2015). Use when user asks about astrology, planets, cosmic signals, "
            "astro trading, or sector planetary analysis. "
            "If no sector specified, returns all sectors ranked by astro score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "description": "Sector name to get astro signal for (optional). If omitted, returns all sectors. Examples: BANKING, IT, PHARMA, METAL, REALTY",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_corporate_catalysts",
        "description": "Get upcoming corporate events and catalysts within the next N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "upcoming_days": {
                    "type": "integer",
                    "description": "Days ahead to look for events (default: 30)",
                    "default": 30,
                }
            },
            "required": [],
        },
    },
    {
        "name": "generate_personal_kundli",
        "description": (
            "Generate a complete Vedic (Jyotish) natal birth chart for a PERSON based on their "
            "date of birth, time of birth, and place of birth. "
            "Returns: Lagna (Ascendant), all 9 planetary positions with sign/house/nakshatra/dignity, "
            "Vimshottari Dasha timeline (current Mahadasha/Antardasha/Pratyantardasha), "
            "financial houses analysis (2H wealth, 5H speculation, 8H transformation, 10H career, 11H income), "
            "active Yogas (Hamsa, Gaja Kesari, Dhana, Kaal Sarp, etc.), "
            "and a complete bullish/bearish life factor analysis with narrative. "
            "ALWAYS use this tool when a user asks for their Kundli, horoscope, birth chart, "
            "Janam Kundali, or provides date/time/place of birth for personal chart reading. "
            "Uses Lahiri ayanamsha (sidereal zodiac) and whole-sign house system. "
            "For IST birthplace, timezone_offset_hours=5.5 (default). "
            "City lookup covers 80+ Indian cities and 30+ global cities. "
            "If city is not found, ask the user for latitude and longitude."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date_of_birth": {
                    "type": "string",
                    "description": "Date of birth in DD-MM-YYYY or YYYY-MM-DD format. Example: '15-08-1985' or '1985-08-15'",
                },
                "time_of_birth": {
                    "type": "string",
                    "description": "Time of birth in HH:MM (24-hour) format. Example: '14:30'. Use 'unknown' if time is not known.",
                    "default": "unknown",
                },
                "place_name": {
                    "type": "string",
                    "description": "City of birth. Examples: 'Mumbai', 'Delhi', 'Jaipur', 'London', 'Dubai'. Used for lat/lon lookup.",
                },
                "latitude": {
                    "type": "number",
                    "description": "Optional: Geographic latitude in decimal degrees (N positive). Overrides place_name lookup.",
                },
                "longitude": {
                    "type": "number",
                    "description": "Optional: Geographic longitude in decimal degrees (E positive). Overrides place_name lookup.",
                },
                "timezone_offset_hours": {
                    "type": "number",
                    "description": "UTC timezone offset in hours. Default 5.5 for IST. Use 0 for London, 4 for Dubai, 8 for Singapore.",
                    "default": 5.5,
                },
            },
            "required": ["date_of_birth", "place_name"],
        },
    },
]

# Map tool name -> python function
from engines.ai.chatbot.tools.data_tools import (
    get_market_regime,
    get_participant_history,
    get_all_sectors,
    get_sector_detail,
    get_sectors_by_signal,
    get_top_stocks,
    get_fno_stocks,
    get_stock_detail,
    get_stocks_by_sector,
    get_institutional_deals,
    get_top_corporate_confidence,
    get_corporate_catalysts,
    get_astro_signal,
    generate_personal_kundli,
)

TOOL_FUNCTIONS: dict[str, callable] = {
    "get_market_regime":          get_market_regime,
    "get_participant_history":    get_participant_history,
    "get_all_sectors":            get_all_sectors,
    "get_sector_detail":          get_sector_detail,
    "get_sectors_by_signal":      get_sectors_by_signal,
    "get_top_stocks":             get_top_stocks,
    "get_fno_stocks":             get_fno_stocks,
    "get_stock_detail":           get_stock_detail,
    "get_stocks_by_sector":       get_stocks_by_sector,
    "get_institutional_deals":    get_institutional_deals,
    "get_top_corporate_confidence": get_top_corporate_confidence,
    "get_corporate_catalysts":    get_corporate_catalysts,
    "get_astro_signal":           get_astro_signal,
    "generate_personal_kundli":   generate_personal_kundli,
}
