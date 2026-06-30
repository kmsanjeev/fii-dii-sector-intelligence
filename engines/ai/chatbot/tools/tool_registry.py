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
            "Get the top stocks for a given accumulation label by bull_run_score. "
            "Labels: STRONG_CANDIDATE, EMERGING, WATCHLIST, NEUTRAL, AVOID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Accumulation label to filter by (default: EMERGING)",
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
]

# Map tool name -> python function
from engines.ai.chatbot.tools.data_tools import (
    get_market_regime,
    get_participant_history,
    get_all_sectors,
    get_sector_detail,
    get_sectors_by_signal,
    get_top_stocks,
    get_stock_detail,
    get_stocks_by_sector,
    get_institutional_deals,
    get_top_corporate_confidence,
    get_corporate_catalysts,
)

TOOL_FUNCTIONS: dict[str, callable] = {
    "get_market_regime": get_market_regime,
    "get_participant_history": get_participant_history,
    "get_all_sectors": get_all_sectors,
    "get_sector_detail": get_sector_detail,
    "get_sectors_by_signal": get_sectors_by_signal,
    "get_top_stocks": get_top_stocks,
    "get_stock_detail": get_stock_detail,
    "get_stocks_by_sector": get_stocks_by_sector,
    "get_institutional_deals": get_institutional_deals,
    "get_top_corporate_confidence": get_top_corporate_confidence,
    "get_corporate_catalysts": get_corporate_catalysts,
}
