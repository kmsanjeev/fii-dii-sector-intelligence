"""Deterministic, provider-free matrix for VEDA runtime exposure audit 001.

This is an audit harness, not a production router. It records the desired
capability for representative user behavior and the current observed route.
The historical predecessor report retained the pre-remediation gaps; this
live harness is intentionally rerun after the wiring remediation.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.capabilities.access_policy import resolve_intent
from engines.ai.chatbot.chat_engine import OPENAI_TOOLS, _tool_names_for_intent
from engines.ai.chatbot.intent_router import detect_intent


@dataclass(frozen=True)
class BehaviorCase:
    case_id: str
    prompt: str
    expected_capability: str
    expected_tools: str
    expected_rag_domain: str
    expected_access: str = "ENABLED"
    expected_answer_mode: str = "FULL_OR_QUALIFIED"


CASES: tuple[BehaviorCase, ...] = (
    BehaviorCase("B001", "hello there", "CORE_INTERACTION", "NONE", "NONE"),
    BehaviorCase("B002", "good morning", "CORE_INTERACTION", "NONE", "NONE"),
    BehaviorCase("B003", "thanks Veda", "CORE_INTERACTION", "NONE", "NONE"),
    BehaviorCase("B004", "explain photosynthesis", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B005", "draft an email", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B006", "write Python code", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B007", "help me plan my day", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B008", "I feel anxious today", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B009", "what is the latest market regime", "MARKET_INTELLIGENCE", "DOMAIN_TOOL_SET", "MARKET"),
    BehaviorCase("B010", "show FII DII flows", "MARKET_INTELLIGENCE", "DOMAIN_TOOL_SET", "MARKET"),
    BehaviorCase("B011", "what are participants buying", "MARKET_INTELLIGENCE", "DOMAIN_TOOL_SET", "MARKET"),
    BehaviorCase("B012", "which sectors are leading", "SECTOR_INTELLIGENCE", "DOMAIN_TOOL_SET", "SECTOR"),
    BehaviorCase("B013", "show sector rotation", "SECTOR_INTELLIGENCE", "DOMAIN_TOOL_SET", "SECTOR"),
    BehaviorCase("B014", "compare IT and pharma sector", "SECTOR_INTELLIGENCE", "DOMAIN_TOOL_SET", "SECTOR"),
    BehaviorCase("B015", "technical trend for RELIANCE stock", "STOCK_INTELLIGENCE", "DOMAIN_TOOL_SET", "STOCK"),
    BehaviorCase("B016", "which stocks are oversold", "STOCK_INTELLIGENCE", "DOMAIN_TOOL_SET", "STOCK"),
    BehaviorCase("B017", "show F&O long buildup", "STOCK_INTELLIGENCE", "DOMAIN_TOOL_SET", "STOCK"),
    BehaviorCase("B018", "what is the RSI for a share", "STOCK_INTELLIGENCE", "DOMAIN_TOOL_SET", "STOCK"),
    BehaviorCase("B019", "recent corporate announcements", "CORPORATE_INTELLIGENCE", "DOMAIN_TOOL_SET", "CORPORATE"),
    BehaviorCase("B020", "any buyback or dividend", "CORPORATE_INTELLIGENCE", "DOMAIN_TOOL_SET", "CORPORATE"),
    BehaviorCase("B021", "management confidence for TCS", "CORPORATE_INTELLIGENCE", "DOMAIN_TOOL_SET", "CORPORATE"),
    BehaviorCase("B022", "portfolio risk report", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B023", "run a backtest", "GENERAL_CHAT", "NONE", "GENERAL"),
    BehaviorCase("B024", "research latest evidence on D20", "RESEARCH", "RESEARCH_SERVICE", "RESEARCH"),
    BehaviorCase("B025", "compare sources for Shadbala", "RESEARCH", "RESEARCH_SERVICE", "RESEARCH"),
    BehaviorCase("B026", "research Jyotish sources", "RESEARCH", "RESEARCH_SERVICE", "RESEARCH"),
    BehaviorCase("B027", "what does D20 mean", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B028", "what is Nakshatra", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B029", "explain Shadbala", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B030", "what is Ashtakavarga", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B031", "what is Panchanga", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B032", "what is my Dasha", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B033", "generate my Kundli", "PERSONAL_KUNDLI", "KUNDLI_TOOL", "KUNDLI"),
    BehaviorCase("B034", "my date of birth is 1 Jan 1990", "PERSONAL_KUNDLI", "KUNDLI_TOOL", "KUNDLI"),
    BehaviorCase("B035", "what is my birth chart", "PERSONAL_KUNDLI", "KUNDLI_TOOL", "KUNDLI"),
    BehaviorCase("B036", "will Jupiter affect stock markets", "ASTRO_FINANCE", "ASTRO_FINANCE_TOOLS", "ASTRO_FINANCE"),
    BehaviorCase("B037", "show AstroFinance signal", "ASTRO_FINANCE", "ASTRO_FINANCE_TOOLS", "ASTRO_FINANCE"),
    BehaviorCase("B038", "is planetary transit bullish for NIFTY", "ASTRO_FINANCE", "ASTRO_FINANCE_TOOLS", "ASTRO_FINANCE"),
    BehaviorCase("B039", "what is Muhurta", "MUHURTA", "NONE", "MUHURTA"),
    BehaviorCase("B040", "find auspicious window for business opening", "MUHURTA", "NONE", "MUHURTA"),
    BehaviorCase("B041", "what Tithi is suitable for education commencement", "MUHURTA", "NONE", "MUHURTA"),
    BehaviorCase("B042", "can I enter my new house", "MUHURTA", "NONE", "MUHURTA"),
    BehaviorCase("B043", "what is Griha Pravesha", "MUHURTA", "NONE", "MUHURTA"),
    BehaviorCase("B044", "research market and compare sources", "RESEARCH", "RESEARCH_SERVICE", "RESEARCH"),
    BehaviorCase("B045", "what is market plus astrology", "ASTRO_FINANCE", "ASTRO_FINANCE_TOOLS", "ASTRO_FINANCE"),
    BehaviorCase("B046", "what is a stock share", "STOCK_INTELLIGENCE", "DOMAIN_TOOL_SET", "STOCK"),
    BehaviorCase("B047", "show corporate catalysts", "CORPORATE_INTELLIGENCE", "DOMAIN_TOOL_SET", "CORPORATE"),
    BehaviorCase("B048", "explain lagna", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B049", "what is D9 Navamsa", "ASTROLOGY", "NONE", "ASTRO"),
    BehaviorCase("B050", "what is D20 Vimshamsha", "ASTROLOGY", "NONE", "ASTRO"),
)


def _actual_tool_class(intent_type: str) -> str:
    if intent_type == "RESEARCH":
        return "RESEARCH_SERVICE"
    names = _tool_names_for_intent(intent_type)
    if names is None:
        return "ALL_REGISTERED_TOOLS"
    if not names:
        return "NONE"
    if names == {"generate_personal_kundli"}:
        return "KUNDLI_TOOL"
    return "ASTRO_FINANCE_TOOLS" if "get_astro_signal" in names else "SCOPED_TOOLS"


def run_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in CASES:
        intent = detect_intent(case.prompt).intent_type
        state = resolve_intent(intent)
        actual_tools = _actual_tool_class(intent)
        rows.append({
            **asdict(case),
            "actual_intent": intent,
            "actual_capability": state.capability_id,
            "actual_access": state.effective_access,
            "actual_answer_mode": state.effective_answer_mode,
            "actual_tools": actual_tools,
            "intent_status": "PASS" if state.capability_id == case.expected_capability else "GAP",
            "tool_status": "PASS" if case.expected_tools in {actual_tools, "DOMAIN_TOOL_SET"} and actual_tools != "ALL_REGISTERED_TOOLS" else ("PASS" if case.expected_tools == "ASTRO_FINANCE_TOOLS" and actual_tools == "ASTRO_FINANCE_TOOLS" else "OVERBROAD"),
        })
    return {
        "activity": "VEDA-RUNTIME-CAPABILITY-EXPOSURE-AUDIT-001",
        "case_count": len(rows),
        "registered_tools": len(OPENAI_TOOLS),
        "rows": rows,
        "intent_pass": sum(row["intent_status"] == "PASS" for row in rows),
        "intent_gaps": sum(row["intent_status"] == "GAP" for row in rows),
        "tool_overbroad": sum(row["tool_status"] == "OVERBROAD" for row in rows),
    }


if __name__ == "__main__":
    print(json.dumps(run_matrix(), ensure_ascii=False, indent=2, sort_keys=True))
