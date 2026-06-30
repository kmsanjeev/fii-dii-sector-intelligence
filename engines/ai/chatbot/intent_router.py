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
    ],
    "STOCK": [
        "stock", "symbol", "share", "equity", "watchlist", "emerging", "strong candidate",
        "bull run", "score", "accumulation score", "which stocks",
    ],
    "CORPORATE": [
        "deal", "bulk", "block", "buyback", "dividend", "corporate", "promoter",
        "confidence", "catalyst", "announcement", "board", "event",
    ],
}


@dataclass
class Intent:
    intent_type: str   # MARKET | SECTOR | STOCK | CORPORATE | RESEARCH
    entity: str | None  # specific symbol/sector if detected
    confidence: float   # 0-1


def detect_intent(user_message: str) -> Intent:
    """Detect the primary intent from a user message."""
    text = user_message.lower()

    # Check for specific stock symbol (all-caps word 2-15 chars, optionally with &)
    symbol_match = re.search(r"\b([A-Z][A-Z0-9&]{1,14})\b", user_message)
    entity = symbol_match.group(1) if symbol_match else None

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
            "EARLY_ROTATION is the most actionable signal -- FII entering before retail. "
            "LEADING means sector is in confirmed uptrend with institutional support. "
            "Compare sectors and highlight rotation opportunities."
        ),
        "STOCK": (
            " Focus on stock-level accumulation signals. "
            "Bull run score > 65 = STRONG_CANDIDATE. "
            "Explain the capital flow cascade: participant -> sector -> stock. "
            "Always mention the sector context for any stock."
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
    }

    return base + domain_hints.get(intent.intent_type, "")
