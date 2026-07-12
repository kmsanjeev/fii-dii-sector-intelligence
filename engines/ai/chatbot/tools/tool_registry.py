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
        "name": "get_stock_fundamentals",
        "description": (
            "Get valuation (P/E, P/B, ROE, valuation label) and extended financials "
            "(OPM%, ROCE%, book value/share, sales growth CAGR) plus the most recent "
            "quarterly result (revenue, net profit, EPS) for a stock. Use for any "
            "question about a company's financial health, profitability, or whether "
            "it looks cheap/expensive -- NOT covered by get_stock_detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol (e.g. RELIANCE, TCS)"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_shareholding_pattern",
        "description": (
            "Get the last 4 quarters of promoter/FII/DII/public shareholding % for a "
            "stock, plus the latest quarter-on-quarter deltas and a conviction_signal "
            "(is promoter or institutional stake increasing or decreasing). Use when "
            "asked about promoter holding, FII/DII ownership trends, or stake changes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_stock_announcements",
        "description": (
            "Get recent NSE corporate announcements for a stock (results, board "
            "outcomes, management changes, acquisitions, regulatory filings), signal-"
            "scored, plus a 30D/90D announcement-activity summary. Use for 'what has "
            "this company announced recently' or 'any news on X'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"},
                "days": {"type": "integer", "description": "Lookback window in days (default: 30)", "default": 30},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_management_sentiment",
        "description": (
            "Get AI-scored management tone/sentiment for a stock (Claude-analysed "
            "from board announcements and holding trends): holding_signal, "
            "ai_tone_score, management_score, management_label. Use when asked about "
            "management quality, confidence, or tone."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"}
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_corporate_action_history",
        "description": (
            "Get historical corporate actions (dividends, bonuses, splits, buybacks, "
            "rights issues) for a stock over the last N years, most recent first. Use "
            "for 'has this company given bonus/split before' or dividend history "
            "questions -- distinct from get_corporate_catalysts, which is upcoming events only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"},
                "years": {"type": "integer", "description": "Years of history to look back (default: 5)", "default": 5},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_conviction_picks",
        "description": (
            "Get the platform's efficacy-weighted conviction screener -- stocks ranked "
            "by a composite score backtested against realized forward returns (real "
            "Information Coefficient per factor, not just rule-based scoring), with "
            "supporting evidence and a primary risk flag per pick. Tiers: HIGH, MEDIUM, "
            "WATCH. This is the platform's single most rigorously validated signal -- "
            "PREFER this over get_top_stocks whenever the user asks what to actually "
            "invest in, not just which stocks look strong."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "string", "description": "Filter by tier: HIGH, MEDIUM, or WATCH (optional -- omit for all)"},
                "top_n": {"type": "integer", "description": "Number of picks to return (default: 20)", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "get_deal_tape",
        "description": (
            "Get individual client block/bulk deal transactions, sequence-paired into "
            "LONG_BUILD_SQUAREOFF (bought then squared off), SHORT_BUILD_COVER (sold "
            "then covered), BUY_ONLY, or SELL_ONLY records -- same-day same-client legs "
            "matched by execution order and quantity. More granular than "
            "get_institutional_deals (which is a 30D aggregate). Filter by symbol for "
            "one stock's deal history, or omit for the largest deals market-wide."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol (optional -- omit for market-wide)"},
                "top_n": {"type": "integer", "description": "Number of records to return (default: 15)", "default": 15},
            },
            "required": [],
        },
    },
    {
        "name": "get_price_history",
        "description": (
            "Get the actual daily OHLCV candle history for a stock. Use this for exact "
            "moving-average crossover dates, specific historical prices, or any question "
            "that needs the real price series rather than a derived trend/score -- "
            "get_stock_detail's technical fields are pre-computed signals, not raw data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"},
                "days": {"type": "integer", "description": "Number of trading sessions to return (default: 90, max: 500)", "default": 90},
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_technical_screener",
        "description": (
            "Screen the stock universe by a technical condition. Valid conditions: "
            "OVERSOLD (RSI<30, potential bounce), OVERBOUGHT (RSI>70, potential "
            "pullback), BULLISH_MACD (MACD crossed above signal), BEARISH_MACD "
            "(crossed below), BB_SQUEEZE (Bollinger Bands compressed, breakout setup), "
            "STRONG_TREND (ADX>25, trending not choppy). Use for 'which stocks are "
            "oversold' or 'show me MACD bullish crossovers' style questions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "OVERSOLD, OVERBOUGHT, BULLISH_MACD, BEARISH_MACD, BB_SQUEEZE, or STRONG_TREND",
                    "default": "OVERSOLD",
                },
                "top_n": {"type": "integer", "description": "Number of stocks to return (default: 20)", "default": 20},
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
            "City lookup works GLOBALLY: built-in list, learned cache, then online "
            "OpenStreetMap geocoding -- any city or town worldwide resolves automatically. "
            "Only ask for latitude/longitude if the tool returns a lookup error."
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
    get_stock_fundamentals,
    get_shareholding_pattern,
    get_stock_announcements,
    get_management_sentiment,
    get_corporate_action_history,
    get_conviction_picks,
    get_deal_tape,
    get_price_history,
    get_technical_screener,
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
    "get_stock_fundamentals":     get_stock_fundamentals,
    "get_shareholding_pattern":   get_shareholding_pattern,
    "get_stock_announcements":    get_stock_announcements,
    "get_management_sentiment":   get_management_sentiment,
    "get_corporate_action_history": get_corporate_action_history,
    "get_conviction_picks":       get_conviction_picks,
    "get_deal_tape":              get_deal_tape,
    "get_price_history":          get_price_history,
    "get_technical_screener":     get_technical_screener,
    "generate_personal_kundli":   generate_personal_kundli,
}
