from __future__ import annotations

import json
import datetime as datetime_module
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli
from engines.intelligence.kundli_engine import KundliEngine
from engines.intelligence.kundli_interpretator import KundliInterpretator


PHASE_ID = "VEDA-P005"
PHASE_DATE = "2026-08-10"
FROZEN_NOW_UTC = datetime(2026, 8, 10, 0, 0, 0, tzinfo=timezone.utc)

PERSONAL_FIXTURE = {
    "date_of_birth": "1984-11-03",
    "time_of_birth": "06:30",
    "place_name": "Mumbai",
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone_offset_hours": 5.5,
}
REST_FIXTURE = {
    "name": "Fixture Mumbai 1984",
    "date_str": "1984-11-03",
    "time_str": "06:30:00",
    "lat": 19.076,
    "lon": 72.8777,
    "tz_offset": 5.5,
}
STOCK_FIXTURE = {"symbol": "RELIANCE", "listing_date": "1995-11-29", "exchange": "NSE"}
COUNTRY_FIXTURE = {"country_name": "India"}


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: timezone | None = None) -> datetime:
        if tz is None:
            return FROZEN_NOW_UTC.replace(tzinfo=None)
        return FROZEN_NOW_UTC.astimezone(tz)


def _phase_iso() -> str:
    return FROZEN_NOW_UTC.isoformat().replace("+00:00", "Z")


def _to_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _snippet(text: str, marker: str, limit: int = 560) -> str:
    idx = text.find(marker)
    if idx < 0:
        return ""
    return text[idx:idx + limit].strip()


def _runtime_patches() -> ExitStack:
    stack = ExitStack()
    stack.enter_context(patch.object(datetime_module, "datetime", FrozenDateTime))
    for target in (
        "engines.ai.chatbot.tools.kundli_calculator.datetime",
        "engines.ai.chatbot.tools.kundli_life_guide.datetime",
        "engines.intelligence.kundli_engine.datetime",
        "engines.intelligence.kundli_interpretator.datetime",
    ):
        stack.enter_context(patch(target, FrozenDateTime))
    return stack


def collect_runtime_samples() -> dict[str, Any]:
    with _runtime_patches():
        engine = KundliEngine()
        interpretator = KundliInterpretator()

        personal = compute_personal_kundli(**PERSONAL_FIXTURE)
        rest_chart = engine.compute_human(**REST_FIXTURE)
        rest_interp = interpretator.interpret(rest_chart, generate_narrative=False)
        stock_chart = engine.compute_stock(**STOCK_FIXTURE)
        stock_interp = interpretator.interpret(stock_chart, generate_narrative=False)
        country_chart = engine.compute_country(**COUNTRY_FIXTURE)
        country_interp = interpretator.interpret(country_chart, generate_narrative=False)

    report = personal["formatted_report"]
    return {
        "frozen_now_utc": _phase_iso(),
        "personal": {
            "lagna": personal["lagna"]["sign"],
            "mahadasha": personal["current_dasha"]["mahadasha"]["planet"],
            "antardasha": personal["current_dasha"]["antardasha"]["planet"],
            "yoga_names": [item["name"] for item in personal.get("yogas", [])],
            "dosha_names": [item["name"] for item in personal.get("doshas", [])],
            "astro_score": personal.get("astro_score"),
            "astro_action": personal.get("astro_action"),
            "bullish_factors": personal.get("bullish_factors", []),
            "bearish_factors": personal.get("bearish_factors", []),
            "report_sections": {
                "career": "CAREER, STATUS & AUTHORITY" in report,
                "finance": "WEALTH & FINANCE" in report,
                "marriage": "LOVE LIFE, ROMANCE & MARRIAGE" in report,
                "health": "HEALTH & LONGEVITY" in report,
                "longevity": "LONGEVITY & LIFE SPAN" in report,
                "current_period": "CURRENT PERIOD & PREDICTIONS" in report,
                "remedies": "Three simple remedies that matter most for you:" in report,
            },
            "report_snippets": {
                "finance": _snippet(report, "WEALTH & FINANCE"),
                "marriage": _snippet(report, "LOVE LIFE, ROMANCE & MARRIAGE"),
                "health": _snippet(report, "HEALTH & LONGEVITY"),
                "longevity": _snippet(report, "LONGEVITY & LIFE SPAN (AYURDAYA PRINCIPLES)"),
                "current_period": _snippet(report, "CURRENT PERIOD & PREDICTIONS (DASHA ANALYSIS)"),
                "doshas": _snippet(report, "DOSHAS  (AFFLICTIONS & WARNINGS)"),
                "remedies": _snippet(report, "Three simple remedies that matter most for you:"),
            },
        },
        "rest_human": {
            "lagna": rest_chart["lagna"]["sign"],
            "mahadasha": rest_chart["current_dasha"]["mahadasha"]["planet"],
            "yoga_names": [item["name"] for item in rest_chart.get("yogas", [])],
            "astro_score": rest_chart.get("astro_score"),
            "astro_action": rest_chart.get("astro_action"),
            "interpretation_signal": rest_interp.get("signal"),
            "bullish_factors": rest_interp.get("bullish_factors", []),
            "bearish_factors": rest_interp.get("bearish_factors", []),
            "divisional_chart_keys": sorted(rest_chart.get("divisional_charts", {}).keys()),
            "financial_house_keys": sorted(rest_chart.get("financial_houses", {}).keys()),
        },
        "stock": {
            "lagna": stock_chart["lagna"]["sign"],
            "mahadasha": stock_chart["current_dasha"]["mahadasha"]["planet"],
            "yoga_names": [item["name"] for item in stock_chart.get("yogas", [])],
            "astro_score": stock_chart.get("astro_score"),
            "astro_action": stock_chart.get("astro_action"),
            "interpretation_signal": stock_interp.get("signal"),
            "interpretation_score": stock_interp.get("astro_score"),
            "bullish_factors": stock_interp.get("bullish_factors", []),
            "bearish_factors": stock_interp.get("bearish_factors", []),
        },
        "country": {
            "lagna": country_chart["lagna"]["sign"],
            "mahadasha": country_chart["current_dasha"]["mahadasha"]["planet"],
            "yoga_names": [item["name"] for item in country_chart.get("yogas", [])],
            "astro_score": country_chart.get("astro_score"),
            "astro_action": country_chart.get("astro_action"),
            "interpretation_signal": country_interp.get("signal"),
            "interpretation_score": country_interp.get("astro_score"),
            "bullish_factors": country_interp.get("bullish_factors", []),
            "bearish_factors": country_interp.get("bearish_factors", []),
        },
    }


def _surface_inventory(samples: dict[str, Any]) -> list[dict[str, Any]]:
    personal = samples["personal"]
    rest_human = samples["rest_human"]
    stock = samples["stock"]
    country = samples["country"]
    return [
        {
            "surface_id": "VEDA-P005-SURF-0001",
            "path": "engines/ai/chatbot/tools/data_tools.py -> generate_personal_kundli -> engines/ai/chatbot/tools/kundli_calculator.py::compute_personal_kundli",
            "function_class": "generate_personal_kundli / compute_personal_kundli",
            "user_facing": True,
            "domain": "PERSONAL_KUNDLI_MULTI_DOMAIN",
            "input_facts": ["birth date", "birth time", "birth place", "latitude/longitude override", "timezone offset"],
            "rule_source": [
                "engines/ai/chatbot/tools/kundli_calculator.py::_yogas",
                "engines/ai/chatbot/tools/kundli_calculator.py::_doshas",
                "engines/ai/chatbot/tools/kundli_calculator.py::_astro_score_and_action",
                "engines/ai/chatbot/tools/kundli_calculator.py::_build_formatted_report",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "WEAK -- rule-level passage links are absent; only file-level source claims are present.",
            "test_coverage": [
                "tests/test_veda_astrology_golden.py::test_personal_kundli_golden_fixtures",
                "tests/test_veda_interpretation_validation.py::test_personal_kundli_surface_preserves_sections_and_flags",
            ],
            "status": "HYBRID",
            "notes": f"Frozen sample exposes yogas {personal['yoga_names']} and doshas {personal['dosha_names']} plus formatted-report sections for career, finance, marriage, health, longevity, and remedies.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0002",
            "path": "engines/ai/chatbot/tools/kundli_calculator.py::_build_formatted_report",
            "function_class": "_build_formatted_report",
            "user_facing": True,
            "domain": "PERSONAL_FORMATTED_REPORT",
            "input_facts": ["lagna", "planets", "dasha", "all_houses", "financial_houses", "yogas", "doshas", "vargas", "remedies"],
            "rule_source": [
                "engines/ai/chatbot/tools/kundli_calculator.py::_dasha_interpretation",
                "engines/ai/chatbot/tools/kundli_calculator.py::_functional_nature",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "WEAK -- section headers and prose are deterministic but not passage-linked.",
            "test_coverage": [
                "tests/test_veda_interpretation_validation.py::test_personal_kundli_surface_preserves_sections_and_flags",
            ],
            "status": "DETERMINISTIC",
            "notes": "Returns a single long text report with panchang, lagna, grahas, Vimshottari, yogas, doshas, bhava analysis, vargas, drishti, remedies, and appended life readings.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0003",
            "path": "engines/ai/chatbot/tools/kundli_interpreter.py::generate_life_readings",
            "function_class": "generate_life_readings",
            "user_facing": True,
            "domain": "PERSONAL_LIFE_AREAS",
            "input_facts": ["planets", "lagna", "all_houses", "dasha", "yogas"],
            "rule_source": [
                "PLANET_IN_HOUSE",
                "LORD_IN_HOUSE",
                "_read_career",
                "_read_finance",
                "_read_love_marriage",
                "_read_children",
                "_read_health",
                "_read_father_fortune",
                "_read_spirituality",
                "_read_longevity",
                "_read_current_period",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "VERY_WEAK -- file header cites BPHS/Phaladeepika/Saravali/Uttara Kalamrita, but no rule-level mapping exists.",
            "test_coverage": [
                "tests/test_veda_interpretation_validation.py::test_personal_kundli_surface_preserves_sections_and_flags",
            ],
            "status": "RULE_BASED",
            "notes": "Appends deterministic multi-domain prose for personality, education, career, wealth, marriage, children, health, home, siblings, father, spirituality, longevity, and current-period analysis.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0004",
            "path": "engines/ai/chatbot/tools/kundli_life_guide.py::build_life_guide",
            "function_class": "build_life_guide",
            "user_facing": True,
            "domain": "PERSONAL_LIFE_GUIDE_AND_TIMING",
            "input_facts": ["planets", "lagna", "dasha", "remedies", "current Saturn transit sign"],
            "rule_source": [
                "_rate_dasha",
                "_sade_sati",
                "PERIOD_ADVICE",
                "DASHA_THEMES",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "WEAK -- custom rating and advice heuristics are not governed by P002/P003 artifacts.",
            "test_coverage": [
                "tests/test_veda_interpretation_validation.py::test_personal_kundli_surface_preserves_sections_and_flags",
            ],
            "status": "HEURISTIC",
            "notes": "Adds plain-English good/bad periods, Sade Sati status, best/careful windows, and simple remedy restatements.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0005",
            "path": "engines/ai/chatbot/chat_engine.py::_run_turn",
            "function_class": "ChatEngine._run_turn",
            "user_facing": True,
            "domain": "CHAT_KUNDLI_VERBATIM",
            "input_facts": ["tool result formatted_report"],
            "rule_source": ["generate_personal_kundli tool result only"],
            "llm_used": False,
            "prompt_used": ["engines/ai/chatbot/intent_router.py::get_system_prompt[KUNDLI]"],
            "hardcoded_text": False,
            "provenance": "INHERITED -- chat returns the formatted_report without adding governed traceability.",
            "test_coverage": [
                "tests/test_veda_chat_engine.py (known inherited failures remain outside P005 scope)",
            ],
            "status": "DETERMINISTIC",
            "notes": "Special-case path bypasses final LLM synthesis and returns the kundli report verbatim when the tool succeeds.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0006",
            "path": "backend/routers/kundli.py::human_kundli -> engines/intelligence/kundli_interpretator.py::KundliInterpretator.interpret",
            "function_class": "human_kundli / KundliInterpretator.interpret",
            "user_facing": True,
            "domain": "REST_HUMAN_FINANCE_ORIENTED_INTERPRETATION",
            "input_facts": ["kundli.planets", "current_dasha", "yogas", "financial_houses", "transits"],
            "rule_source": [
                "engines/intelligence/kundli_interpretator.py::DASHA_FINANCIAL",
                "engines/intelligence/kundli_interpretator.py::interpret",
            ],
            "llm_used": "OPTIONAL",
            "prompt_used": ["engines/intelligence/kundli_interpretator.py::_generate_narrative"],
            "hardcoded_text": True,
            "provenance": "WEAK -- finance-facing interpretation layer has no governed classical provenance.",
            "test_coverage": [
                "tests/test_veda_astrology_golden.py::test_rest_human_kundli_golden_fixtures",
                "tests/test_veda_interpretation_validation.py::test_rest_human_surface_remains_divergent_from_personal",
            ],
            "status": "HYBRID",
            "notes": f"Frozen sample human REST path surfaces yogas {rest_human['yoga_names']} and finance-style signal {rest_human['interpretation_signal']} rather than the personal life-reading report.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0007",
            "path": "backend/routers/kundli.py::stock_kundli -> engines/intelligence/kundli_engine.py::_detect_yogas/_financial_score -> engines/intelligence/kundli_interpretator.py::interpret",
            "function_class": "stock_kundli / KundliEngine / KundliInterpretator",
            "user_facing": True,
            "domain": "STOCK_KUNDLI_FINANCE",
            "input_facts": ["listing-date chart", "transits", "yogas", "financial_houses", "dasha", "Gann output optional"],
            "rule_source": [
                "engines/intelligence/kundli_engine.py::_detect_yogas",
                "engines/intelligence/kundli_engine.py::_financial_score",
                "engines/intelligence/kundli_interpretator.py::interpret",
            ],
            "llm_used": "OPTIONAL",
            "prompt_used": ["engines/intelligence/kundli_interpretator.py::_generate_narrative"],
            "hardcoded_text": True,
            "provenance": "ASTROFINANCE_HEURISTIC -- finance-market meanings are coded, not source-governed.",
            "test_coverage": [
                "tests/test_veda_astrology_golden.py::test_stock_kundli_golden_fixtures",
                "tests/test_veda_interpretation_validation.py::test_stock_interpretation_preserves_finance_signal_shape",
            ],
            "status": "HYBRID",
            "notes": f"Frozen RELIANCE sample yields kundli action {stock['astro_action']} and interpretation signal {stock['interpretation_signal']} with yogas {stock['yoga_names'][:5]}.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0008",
            "path": "backend/routers/kundli.py::country_kundli -> engines/intelligence/kundli_interpretator.py::interpret",
            "function_class": "country_kundli / KundliInterpretator.interpret",
            "user_facing": True,
            "domain": "COUNTRY_KUNDLI_FINANCE_STYLE",
            "input_facts": ["country inception chart", "dasha", "yogas", "financial_houses", "transits"],
            "rule_source": [
                "engines/intelligence/kundli_engine.py::_detect_yogas",
                "engines/intelligence/kundli_interpretator.py::interpret",
            ],
            "llm_used": "OPTIONAL",
            "prompt_used": ["engines/intelligence/kundli_interpretator.py::_generate_narrative"],
            "hardcoded_text": True,
            "provenance": "WEAK -- finance-market heuristics are reused for geopolitical country charts.",
            "test_coverage": [
                "tests/test_veda_astrology_golden.py::test_country_kundli_golden_fixtures",
                "tests/test_veda_interpretation_validation.py::test_country_surface_stays_finance_oriented",
            ],
            "status": "HYBRID",
            "notes": f"Frozen India sample yields interpretation signal {country['interpretation_signal']} with repeated Raja Yoga labels and finance-style bullish factors.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0009",
            "path": "engines/intelligence/kundli_interpretator.py::_generate_narrative",
            "function_class": "KundliInterpretator._generate_narrative",
            "user_facing": True,
            "domain": "STOCK_COUNTRY_OPTIONAL_LLM_SUMMARY",
            "input_facts": ["signal", "astro_score", "mahadasha", "yogas", "bullish_factors", "bearish_factors"],
            "rule_source": ["system prompt", "user prompt assembled from deterministic factors"],
            "llm_used": True,
            "prompt_used": ["inline system/user prompt in kundli_interpretator.py"],
            "hardcoded_text": False,
            "provenance": "NO_GOVERNED_PROVENANCE -- LLM output is not mapped to source claims or rule IDs.",
            "test_coverage": [],
            "status": "LLM_SYNTHESIZED",
            "notes": "Optional two- to three-sentence financial narrative; disabled by default in most frontend calls (`generate_narrative=false`).",
        },
        {
            "surface_id": "VEDA-P005-SURF-0010",
            "path": "engines/ai/chatbot/tools/data_tools.py::get_astro_signal",
            "function_class": "get_astro_signal",
            "user_facing": True,
            "domain": "ASTROFINANCE_SECTOR_SIGNAL",
            "input_facts": ["astro_signals.csv", "market_astro_context.json", "optional sector name"],
            "rule_source": [
                "engines/intelligence/astro_engine.py::_compute_sector_signals",
                "engines/intelligence/astro_engine.py::SECTOR_RULERS",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "MODERN_ONLY -- explicitly cites Banerjee/Pesavento style sources, not classical natal Jyotisha.",
            "test_coverage": [
                "tests/test_veda_interpretation_validation.py::test_astrofinance_sector_signal_shape",
            ],
            "status": "RULE_BASED",
            "notes": "Sector-level real-time signal is separate from natal kundli logic and should remain separately governed.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0011",
            "path": "frontend/src/components/platform/AstroSignalCard.tsx",
            "function_class": "AstroSignalCard",
            "user_facing": True,
            "domain": "ASTROFINANCE_UI_EXPLANATION",
            "input_facts": ["astro score", "action", "planet state", "moon phase", "market signal"],
            "rule_source": [
                "buildPlainReason",
                "STATE_PLAIN",
                "PHASE_PLAIN",
                "MARKET_PLAIN",
            ],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "MODERN_ONLY -- UI expands AstroFinance heuristics into plain-English educational text.",
            "test_coverage": ["frontend Vitest baseline only"],
            "status": "HEURISTIC",
            "notes": "UI restates sector action logic and explicitly labels AstroFinance as supplementary to technical and fundamental analysis.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0012",
            "path": "frontend/src/components/platform/KundliCard.tsx",
            "function_class": "KundliCard",
            "user_facing": True,
            "domain": "STOCK_KUNDLI_UI",
            "input_facts": ["kundli payload", "interpretation payload"],
            "rule_source": ["backend /api/stocks/{symbol}/kundli output only"],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": False,
            "provenance": "INHERITED_FROM_BACKEND",
            "test_coverage": ["frontend Vitest baseline only"],
            "status": "DETERMINISTIC",
            "notes": "Displays IPO chart, financial houses, yogas, dasha timeline, and interpretation factors without adding new reasoning.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0013",
            "path": "frontend/src/pages/ReportPage.tsx",
            "function_class": "ReportPage",
            "user_facing": True,
            "domain": "STOCK_REPORT_UI",
            "input_facts": ["stock detail payload", "kundli endpoint payload", "astrofinance payload"],
            "rule_source": ["API payload composition only"],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": False,
            "provenance": "INHERITED_FROM_BACKEND",
            "test_coverage": ["frontend Vitest baseline only"],
            "status": "HYBRID",
            "notes": "Combines fixed company natal chart output and daily AstroFinance output in the same stock report while keeping them visually distinct.",
        },
        {
            "surface_id": "VEDA-P005-SURF-0014",
            "path": "frontend/src/pages/ChatPage.tsx",
            "function_class": "ChatPage quick commands",
            "user_facing": True,
            "domain": "CHAT_QUICK_ACTIONS",
            "input_facts": ["templated quick query strings"],
            "rule_source": ["static quick-command labels and queries"],
            "llm_used": False,
            "prompt_used": [],
            "hardcoded_text": True,
            "provenance": "NONE",
            "test_coverage": ["frontend Vitest baseline only"],
            "status": "DETERMINISTIC",
            "notes": "Surfaces personal kundli, current dasha, career/wealth, and love/marriage prompts directly in the chat UI.",
        },
    ]


def _rule(
    legacy_rule_id: str,
    location: str,
    function: str,
    domain: str,
    logic_type: str,
    condition: str,
    result: str,
    source_status: str,
    source_reference: list[str],
    production_usage: list[str],
    confidence: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "legacy_rule_id": legacy_rule_id,
        "location": location,
        "function": function,
        "domain": domain,
        "logic_type": logic_type,
        "condition": condition,
        "result": result,
        "source_status": source_status,
        "source_reference": source_reference,
        "production_usage": production_usage,
        "confidence": confidence,
        "notes": notes,
    }


def _legacy_rule_registry() -> list[dict[str, Any]]:
    return [
        _rule("VEDA-P005-LGC-0001", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE_SET", "Planet is own-sign/exalted/moolatrikona and in H1/H4/H7/H10", "Emit one of Hamsa, Malavya, Bhadra, Ruchaka, or Sasa Yoga with score 18 / BUY", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "HIGH", "Pancha Mahapurusha family is implemented as a simplified kendra+dignity check only."),
        _rule("VEDA-P005-LGC-0002", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE", "Jupiter in a kendra from Moon by house offset 0/3/6/9", "Emit Gaja Kesari Yoga with score 15 / BUY", "SOURCE_CANDIDATE_FOUND", ["data/veda/rules/draft/VEDA-RUL-YOGA-000001"], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "HIGH", "Governed pilot mapping exists in P003, but it is still marked legacy-unsourced rather than text-validated."),
        _rule("VEDA-P005-LGC-0003", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE", "2H lord placed in 11H or 11H lord in 2H or same planet rules both", "Emit Dhana Yoga with score 12 / BUY", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "Current personal rule is a narrow wealth-house connection heuristic."),
        _rule("VEDA-P005-LGC-0004", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE", "Debilitated planet whose debilitation-sign lord is in H1/H4/H7/H10", "Emit Neecha Bhanga (<planet>) with score 8 / HOLD", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "Cancellation logic is materially simplified and ignores multiple classical exceptions."),
        _rule("VEDA-P005-LGC-0005", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE", "All seven classical planets fall between Rahu and Ketu by a min/max longitude arc heuristic", "Emit Kaal Sarp Yoga with score -12 / CAUTION", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "LOW", "Name differs from stock path (`Kala Sarpa`) and no cancellation school logic is implemented."),
        _rule("VEDA-P005-LGC-0006", "engines/ai/chatbot/tools/kundli_calculator.py", "_yogas", "YOGA", "RULE", "No non-node planet occupies adjacent houses from Moon", "Emit Kemadruma Yoga with score -6 / CAUTION", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "LOW", "House-based adjacency test is a simplified loneliness heuristic."),
        _rule("VEDA-P005-LGC-0007", "engines/ai/chatbot/tools/kundli_calculator.py", "_doshas", "DOSHA", "RULE", "Mars in H1/H2/H4/H7/H8/H12", "Emit Manglik Dosha with marriage-specific description and remedy", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "HIGH", "Current rule is direct and user-facing in marriage contexts, but no school-variance handling is present."),
        _rule("VEDA-P005-LGC-0008", "engines/ai/chatbot/tools/kundli_calculator.py", "_doshas", "DOSHA", "RULE", "Saturn in H1/H4/H7 from Lagna, plus a mild Moon-relative variant", "Emit Shani Dosha or Shani Dosha (from Moon)", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "This is a bespoke platform dosha rather than a governed classical rule."),
        _rule("VEDA-P005-LGC-0009", "engines/ai/chatbot/tools/kundli_calculator.py", "_doshas", "DOSHA", "RULE", "Sun and Rahu conjunct by same house", "Emit Surya Chandal Dosha with remedy text", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "No orb handling or source linkage is present."),
        _rule("VEDA-P005-LGC-0010", "engines/ai/chatbot/tools/kundli_calculator.py", "_doshas", "DOSHA", "RULE", "Jupiter and Rahu conjunct by same house", "Emit Guru Chandal Dosha with remedy text", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "Same-house logic is treated as sufficient for the full dosha label."),
        _rule("VEDA-P005-LGC-0011", "engines/ai/chatbot/tools/kundli_calculator.py", "_doshas", "DOSHA", "RULE", "Moon and Saturn conjunct by same house", "Emit Shani-Chandra Yoga with mental-health colored prose and remedy text", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "MEDIUM", "High-stakes emotional language is deterministic but unsourced."),
        _rule("VEDA-P005-LGC-0012", "engines/ai/chatbot/tools/kundli_calculator.py", "_lal_kitab_remedies", "REMEDIES", "LOOKUP_AND_AGGREGATION", "Weak planets, active doshas, or Kaal Sarp Yoga", "Return Lal Kitab farmans and dosha remedies", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002", "VEDA-P005-SURF-0004"], "HIGH", "Remedial content is tradition-specific, cost-bearing in effect, and not governed by source passages."),
        _rule("VEDA-P005-LGC-0013", "engines/ai/chatbot/tools/kundli_calculator.py", "_astro_score_and_action", "SUMMARY_SCORING", "SCORING", "Benefic dignities + selected malefic adjustments + Mahadasha dignity multiplier", "Return numeric score and one of POSITIVE/MODERATE/NEUTRAL/CHALLENGING/DIFFICULT", "HEURISTIC", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "HIGH", "This is a platform-specific chart-quality summary, not a governed classical measure."),
        _rule("VEDA-P005-LGC-0014", "engines/ai/chatbot/tools/kundli_calculator.py", "_factors", "SUMMARY_FACTORS", "FACTOR_LIST", "Selected benefics/malefics, Mahadasha dignity, 2H/11H strength", "Return bullish_factors and bearish_factors lists", "HEURISTIC", [], ["VEDA-P005-SURF-0001", "VEDA-P005-SURF-0002"], "HIGH", "Factor list drives much of the top-level readable summary and is materially custom."),
        _rule("VEDA-P005-LGC-0015", "engines/ai/chatbot/tools/kundli_calculator.py", "_narrative", "SUMMARY_NARRATIVE", "TEMPLATE", "Lagna, lagna lord, positive yogas, current dasha, Jupiter/Saturn dignity, score bucket", "Return one-paragraph personal chart summary", "HEURISTIC", [], ["VEDA-P005-SURF-0001"], "MEDIUM", "Narrative is deterministic template prose, not LLM-generated."),
        _rule("VEDA-P005-LGC-0016", "engines/ai/chatbot/tools/kundli_calculator.py", "_functional_nature / _dasha_interpretation", "DASHA_INTERPRETATION", "RULE", "Yogakaraka and house-lord nature override raw dignity when framing a Dasha period", "Return chart-conditioned Dasha interpretation text", "SOURCE_VALIDATED", ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002", "VEDA-CLM-000004"], ["VEDA-P005-SURF-0002"], "MEDIUM", "Only the period-selection/governance layer is governed; the actual planet-theme sentences remain unsourced."),
        _rule("VEDA-P005-LGC-0017", "engines/ai/chatbot/tools/kundli_interpreter.py", "PLANET_IN_HOUSE", "GRAHA_BHAVA_INTERPRETATION", "TABLE", "Planet name + house number", "Return a full narrative sentence for the graha in that bhava", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "The file cites classical works at the header but does not map any individual row to a passage."),
        _rule("VEDA-P005-LGC-0018", "engines/ai/chatbot/tools/kundli_interpreter.py", "LORD_IN_HOUSE", "LORDSHIP_INTERPRETATION", "TABLE", "House number + placement house of its lord", "Return a lord-in-house interpretation sentence", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "This is a large hardcoded lookup table with no governed provenance."),
        _rule("VEDA-P005-LGC-0019", "engines/ai/chatbot/tools/kundli_interpreter.py", "_read_career", "CAREER", "SECTION_SYNTHESIS", "H10 sign/lord/occupants + Saturn + Sun + current Mahadasha", "Return career section with timing commentary", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "No D10 facts are actually used despite in-code comment about a D10 hint."),
        _rule("VEDA-P005-LGC-0020", "engines/ai/chatbot/tools/kundli_interpreter.py", "_read_finance", "FINANCE", "SECTION_SYNTHESIS", "H2/H11/H5 lords + Jupiter + Venus + Dhana yogas", "Return wealth and finance section", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "Combines hardcoded lookup text and summary heuristics without source citations."),
        _rule("VEDA-P005-LGC-0021", "engines/ai/chatbot/tools/kundli_interpreter.py", "_read_love_marriage", "MARRIAGE", "SECTION_SYNTHESIS", "H5/H7 lords + Venus + Mars + Moon + simple timing heuristics", "Return love life and marriage section", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "Marriage timing mentions Venus/7th-lord Dasha but does not use D9 or governed passage evidence."),
        _rule("VEDA-P005-LGC-0022", "engines/ai/chatbot/tools/kundli_interpreter.py", "_read_health / _read_longevity", "HEALTH_LONGEVITY", "SECTION_SYNTHESIS", "H1/H6/H8 strength + Saturn + Mars + Moon + Lagna-sign body map + maraka note", "Return health and longevity prose", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0003"], "HIGH", "High-stakes wording includes lifespan-oriented statements and maraka references without safety gating."),
        _rule("VEDA-P005-LGC-0023", "engines/ai/chatbot/tools/kundli_interpreter.py", "_read_current_period / _combined_dasha_reading", "DASHA_INTERPRETATION", "SECTION_SYNTHESIS", "Current Mahadasha + Antardasha + dignity + yogakaraka override + theme tables", "Return multi-line current-period prediction block", "LEGACY_PARTIALLY_SOURCED", ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"], ["VEDA-P005-SURF-0003"], "MEDIUM", "Period selection is governed; descriptive themes and prediction language remain unsourced."),
        _rule("VEDA-P005-LGC-0024", "engines/ai/chatbot/tools/kundli_life_guide.py", "_rate_dasha / build_life_guide", "DASHA_GUIDANCE", "SCORING_AND_ADVICE", "Functional lordship + dignity + house + natural benefic/malefic weighting", "Rate upcoming Mahadashas as EXCELLENT/GOOD/MIXED/CHALLENGING and add lay advice", "HEURISTIC", [], ["VEDA-P005-SURF-0004"], "MEDIUM", "This is an explicitly plain-English heuristic overlay rather than governed doctrine."),
        _rule("VEDA-P005-LGC-0025", "engines/intelligence/kundli_engine.py", "_detect_yogas", "STOCK_YOGA", "RULE_SET", "Kendra/trikona and finance-house combinations in the stock/company chart", "Emit Gaja Kesari, Dhana, Raja Yoga, Viparita Raja, Neecha Bhanga, Kemdrum, Kala Sarpa, Parivartana", "LEGACY_UNSOURCED", [], ["VEDA-P005-SURF-0007", "VEDA-P005-SURF-0008"], "HIGH", "Finance-oriented yoga detector duplicates names but uses materially different conditions from the personal path."),
        _rule("VEDA-P005-LGC-0026", "engines/intelligence/kundli_engine.py", "_financial_houses", "STOCK_FINANCIAL_HOUSES", "SCORING", "Selected houses 2/5/8/10/11 with lord dignity, house, and occupants", "Return strong/moderate/weak qualitative financial-house summaries", "HEURISTIC", [], ["VEDA-P005-SURF-0006", "VEDA-P005-SURF-0007", "VEDA-P005-SURF-0008"], "HIGH", "This is operationally important but explicitly finance-market specific."),
        _rule("VEDA-P005-LGC-0027", "engines/intelligence/kundli_engine.py", "_financial_score", "STOCK_SIGNAL", "WEIGHTED_SCORE", "11H/5H/8H dignity, current Mahadasha house, yoga scores, Jupiter/Saturn transit aspects", "Return BUY/HOLD/CAUTION/EXIT/AVOID chart-level action", "ASTROFINANCE_HYPOTHESIS", [], ["VEDA-P005-SURF-0007", "VEDA-P005-SURF-0008"], "HIGH", "The stock action model is deterministic but not governed by classical-source evidence."),
        _rule("VEDA-P005-LGC-0028", "engines/intelligence/kundli_interpretator.py", "DASHA_FINANCIAL / interpret", "STOCK_DASHA_FINANCE", "LOOKUP_AND_SYNTHESIS", "Current Mahadasha and selected dignities or yogas", "Return bullish/bearish factor lines and final stock signal", "ASTROFINANCE_HYPOTHESIS", [], ["VEDA-P005-SURF-0006", "VEDA-P005-SURF-0007", "VEDA-P005-SURF-0008"], "HIGH", "Mahadasha meanings are directly finance-coded rather than sourced from P002 passages."),
        _rule("VEDA-P005-LGC-0029", "engines/intelligence/kundli_interpretator.py", "_generate_narrative", "STOCK_LLM_SUMMARY", "PROMPT_TEMPLATE", "Structured finance factors become an LLM prompt", "Return two- to three-sentence financial outlook", "HEURISTIC", [], ["VEDA-P005-SURF-0009"], "MEDIUM", "Narrative is optional and provider-dependent; no citations or rule IDs are returned."),
        _rule("VEDA-P005-LGC-0030", "engines/intelligence/astro_engine.py", "SECTOR_RULERS", "ASTROFINANCE", "MAPPING_TABLE", "NSE sector label", "Map sector to one or more ruling planets", "MODERN_INTERPRETATION", ["docs/modules/ASTRO.md", "docs/decisions/ADR-022-AstroFinance-Vedic-Intelligence-Layer.md"], ["VEDA-P005-SURF-0010", "VEDA-P005-SURF-0011"], "HIGH", "Explicitly separated from classical natal Jyotisha under P002/P003 policy."),
        _rule("VEDA-P005-LGC-0031", "engines/intelligence/astro_engine.py", "_compute_sector_signals", "ASTROFINANCE", "SIGNAL_LOGIC", "Planet sign strength, retrograde state, aspects, Moon phase, eclipse state", "Return sector astro_score, action, and astro_reason", "ASTROFINANCE_HYPOTHESIS", ["docs/modules/ASTRO.md", "docs/decisions/ADR-022-AstroFinance-Vedic-Intelligence-Layer.md"], ["VEDA-P005-SURF-0010", "VEDA-P005-SURF-0011"], "HIGH", "No empirical backtest registry is wired into this rule path."),
        _rule("VEDA-P005-LGC-0032", "frontend/src/components/platform/AstroSignalCard.tsx", "buildPlainReason / STATE_PLAIN / PHASE_PLAIN", "ASTROFINANCE_UI", "UI_EXPLANATION", "AstroFinance API payload values", "Expand terse sector signal fields into plain-English guidance and warnings", "MODERN_INTERPRETATION", ["frontend/src/components/platform/AstroSignalCard.tsx"], ["VEDA-P005-SURF-0011"], "MEDIUM", "Frontend explanation increases interpretive certainty but does not add provenance."),
    ]


def _yoga_dosha_matrix() -> list[dict[str, Any]]:
    return [
        {"kind": "YOGA", "name": "Hamsa Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_yogas"], "current_conditions": "Jupiter dignified and in H1/H4/H7/H10", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed score 18 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Positive yoga list in personal report", "school_variance": "low", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "YOGA", "name": "Malavya Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_yogas"], "current_conditions": "Venus dignified and in H1/H4/H7/H10", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed score 18 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Positive yoga list in personal report", "school_variance": "low", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "YOGA", "name": "Bhadra Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_yogas"], "current_conditions": "Mercury dignified and in H1/H4/H7/H10", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed score 18 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Positive yoga list in personal report", "school_variance": "low", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "YOGA", "name": "Ruchaka Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_yogas"], "current_conditions": "Mars dignified and in H1/H4/H7/H10", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed score 18 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Positive yoga list in personal report", "school_variance": "low", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "YOGA", "name": "Sasa Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_yogas"], "current_conditions": "Saturn dignified and in H1/H4/H7/H10", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed score 18 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Positive yoga list in personal report", "school_variance": "low", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "YOGA", "name": "Gaja Kesari", "surfaces": ["personal", "rest", "stock", "country"], "legacy_locations": ["kundli_calculator::_yogas", "kundli_engine::_detect_yogas"], "current_conditions": "Jupiter in a kendra from Moon; stock path labels conjunction as strong", "source_status": "SOURCE_CANDIDATE_FOUND", "source_conditions": "P003 draft rule VEDA-RUL-YOGA-000001 exists but remains legacy-unsourced", "match": "PARTIAL_SIMPLIFICATION", "exceptions": "none", "cancellations": "none", "strength_rules": "personal fixed +15; stock uses strong/moderate field", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Appears in personal and stock/country output", "school_variance": "medium", "condition_variance": "medium", "source_conflict": "no governed conflict record yet", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Dhana Yoga", "surfaces": ["personal", "stock", "country"], "legacy_locations": ["kundli_calculator::_yogas", "kundli_engine::_detect_yogas"], "current_conditions": "Personal path uses 2H/11H placement shortcuts; stock path checks both lords in 1/2/5/9/11", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "personal +12 / BUY; stock +20 / BUY", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Wealth-positive yoga label", "school_variance": "medium", "condition_variance": "high", "source_conflict": "none recorded", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Raja Yoga", "surfaces": ["stock", "country", "rest_human"], "legacy_locations": ["kundli_engine::_detect_yogas"], "current_conditions": "Kendra lord and trikona lord conjunct in same house", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed +18 / BUY; duplicates may appear multiple times", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Multiple repeated Raja Yoga entries appear in stock/country outputs", "school_variance": "medium", "condition_variance": "high", "source_conflict": "none recorded", "recommendation": "REWRITE_LATER"},
        {"kind": "YOGA", "name": "Viparita Raja", "surfaces": ["stock", "country"], "legacy_locations": ["kundli_engine::_detect_yogas"], "current_conditions": "At least two of the 6H/8H/12H lords occupy 6/8/12", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed +12 / HOLD", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Counter-cyclical positive finance yoga", "school_variance": "medium", "condition_variance": "high", "source_conflict": "none recorded", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Neecha Bhanga", "surfaces": ["personal", "stock", "country"], "legacy_locations": ["kundli_calculator::_yogas", "kundli_engine::_detect_yogas"], "current_conditions": "Cancellation via debility-sign lord in kendra; stock path also checks Moon-relative kendra pattern", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "partial only", "cancellations": "built into the yoga name", "strength_rules": "personal +8 HOLD; stock +8 HOLD partial", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Recovery/cancellation yoga", "school_variance": "high", "condition_variance": "high", "source_conflict": "none recorded", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Kaal / Kala Sarpa", "surfaces": ["personal", "stock", "country"], "legacy_locations": ["kundli_calculator::_yogas", "kundli_engine::_detect_yogas"], "current_conditions": "All seven classical planets fall inside the Rahu/Ketu arc; personal and stock use different arc tests", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "NAME_AND_METHOD_DIVERGENT", "exceptions": "none", "cancellations": "none", "strength_rules": "personal -12 / CAUTION; stock -10 / CAUTION", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Challenge/extreme-volatility yoga", "school_variance": "very high", "condition_variance": "very high", "source_conflict": "definition variance likely but unregistered", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Kemadruma / Kemdrum", "surfaces": ["personal", "stock", "country", "rest_human"], "legacy_locations": ["kundli_calculator::_yogas", "kundli_engine::_detect_yogas"], "current_conditions": "No adjacent-house or adjacent-sign support around the Moon depending on path", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED_AND_DIVERGENT", "exceptions": "none", "cancellations": "none", "strength_rules": "negative score and CAUTION output", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Isolation / erratic support warning", "school_variance": "high", "condition_variance": "high", "source_conflict": "none recorded", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "YOGA", "name": "Parivartana", "surfaces": ["stock", "country"], "legacy_locations": ["kundli_engine::_detect_yogas"], "current_conditions": "Two planets occupy each other's own signs", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLAUSIBLE_BUT_UNVERIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "fixed +5 / HOLD", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Context-dependent exchange yoga", "school_variance": "medium", "condition_variance": "medium", "source_conflict": "none recorded", "recommendation": "KEEP_WITH_CAVEAT"},
        {"kind": "DOSHA", "name": "Manglik Dosha", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_doshas"], "current_conditions": "Mars in H1/H2/H4/H7/H8/H12", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "COMMON_MODERN_FORM", "exceptions": "not modeled", "cancellations": "not modeled", "strength_rules": "fixed moderate severity", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Marriage warning plus remedy", "school_variance": "very high", "condition_variance": "very high", "source_conflict": "likely, but unregistered", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "DOSHA", "name": "Shani Dosha", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_doshas"], "current_conditions": "Saturn in H1/H4/H7 plus Moon-relative mild variant", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "PLATFORM_SPECIFIC", "exceptions": "none", "cancellations": "none", "strength_rules": "moderate or mild severity buckets", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Delay/obstacle warning plus remedy", "school_variance": "high", "condition_variance": "high", "source_conflict": "not governed", "recommendation": "REWRITE_LATER"},
        {"kind": "DOSHA", "name": "Surya Chandal Dosha", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_doshas"], "current_conditions": "Sun and Rahu in same house", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "moderate severity", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Authority/father conflict warning", "school_variance": "medium", "condition_variance": "medium", "source_conflict": "not governed", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "DOSHA", "name": "Guru Chandal Dosha", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_doshas"], "current_conditions": "Jupiter and Rahu in same house", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "significant severity", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Ethics/belief distortion warning", "school_variance": "medium", "condition_variance": "medium", "source_conflict": "not governed", "recommendation": "RESEARCH_FURTHER"},
        {"kind": "DOSHA", "name": "Shani-Chandra Yoga", "surfaces": ["personal"], "legacy_locations": ["kundli_calculator::_doshas"], "current_conditions": "Moon and Saturn in same house", "source_status": "LEGACY_UNSOURCED", "source_conditions": "", "match": "SIMPLIFIED", "exceptions": "none", "cancellations": "none", "strength_rules": "moderate severity", "dasha_activation": "not modeled", "varga_confirmation": "not modeled", "current_output": "Melancholy / emotional suppression warning", "school_variance": "medium", "condition_variance": "medium", "source_conflict": "not governed", "recommendation": "KEEP_WITH_CAVEAT"},
    ]


def _dasha_interpretation_matrix() -> list[dict[str, Any]]:
    return [
        {
            "dasha_rule_id": "VEDA-P005-DASHA-0001",
            "dasha_planet": "MULTI",
            "subperiod": "MAHADASHA",
            "domain": "PERSONAL_REPORT",
            "current_text_logic": "kundli_calculator::_dasha_interpretation chooses text by planet themes, dignity, and lagna-specific functional nature.",
            "source_status": "LEGACY_PARTIALLY_SOURCED",
            "source_claims": ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002", "VEDA-CLM-000004"],
            "conflicts": [],
            "context_dependencies": ["lagna sign", "planet dignity", "functional nature"],
            "recommendation": "SOURCE_AND_MIGRATE",
        },
        {
            "dasha_rule_id": "VEDA-P005-DASHA-0002",
            "dasha_planet": "MULTI",
            "subperiod": "MAHADASHA_ANTARDASHA",
            "domain": "PERSONAL_CURRENT_PERIOD",
            "current_text_logic": "kundli_interpreter::_combined_dasha_reading combines Mahadasha and Antardasha planet-theme tables with dignity and yogakaraka overrides.",
            "source_status": "LEGACY_UNSOURCED",
            "source_claims": [],
            "conflicts": [],
            "context_dependencies": ["planet dignity", "house position", "yogakaraka flag", "theme lookup table"],
            "recommendation": "REWRITE_AFTER_RESEARCH",
        },
        {
            "dasha_rule_id": "VEDA-P005-DASHA-0003",
            "dasha_planet": "MULTI",
            "subperiod": "MAHADASHA",
            "domain": "PERSONAL_LIFE_GUIDE",
            "current_text_logic": "kundli_life_guide::_rate_dasha scores upcoming Mahadashas by functional lordship, dignity, house, combustion, and natural benefic/malefic character.",
            "source_status": "HEURISTIC",
            "source_claims": [],
            "conflicts": [],
            "context_dependencies": ["lagna sign", "house lordship", "combustion", "natural planet set"],
            "recommendation": "KEEP_AS_HEURISTIC",
        },
        {
            "dasha_rule_id": "VEDA-P005-DASHA-0004",
            "dasha_planet": "Sun..Ketu",
            "subperiod": "MAHADASHA",
            "domain": "STOCK_FINANCE",
            "current_text_logic": "kundli_interpretator::DASHA_FINANCIAL maps each Mahadasha planet to a finance-market sentence used in bullish/bearish factors and dasha outlook.",
            "source_status": "ASTROFINANCE_HYPOTHESIS",
            "source_claims": [],
            "conflicts": [],
            "context_dependencies": ["current Mahadasha planet", "selected dignity branch for Mars/Mercury/Saturn"],
            "recommendation": "KEEP_AS_ASTROFINANCE_EXPERIMENT",
        },
        {
            "dasha_rule_id": "VEDA-P005-DASHA-0005",
            "dasha_planet": "CURRENT_PERIOD_SELECTION",
            "subperiod": "MAHADASHA_ANTARDASHA_PRATYANTARDASHA",
            "domain": "PERSONAL_AND_REST_SELECTION",
            "current_text_logic": "Current Mahadasha, Antardasha, and Pratyantardasha are surfaced from the deterministic Vimshottari timeline without additional narrative transformation.",
            "source_status": "SOURCE_VALIDATED",
            "source_claims": ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"],
            "conflicts": ["VEDA-CNF-000001"],
            "context_dependencies": ["Moon Nakshatra", "elapsed fraction", "frozen evaluation date"],
            "recommendation": "PRESERVE",
        },
    ]


def _domain_validation_matrix() -> list[dict[str, Any]]:
    return [
        {"domain": "CAREER", "current_rules": ["_read_career", "_functional_nature", "stock H10/management heuristics"], "source_coverage": "NONE", "varga_use": "D10 displayed but not actually interpreted in personal runtime", "dasha_use": "Yes", "transit_use": "Stock path only", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "FINANCE", "current_rules": ["_read_finance", "personal score/factors", "stock financial score"], "source_coverage": "NONE", "varga_use": "No active varga confirmation", "dasha_use": "Yes", "transit_use": "Stock path yes", "confidence": "LOW", "action": "RESEARCH_FURTHER", "status": "HEURISTIC"},
        {"domain": "MARRIAGE", "current_rules": ["_read_love_marriage", "Manglik note"], "source_coverage": "NONE", "varga_use": "D9 displayed but not applied inside the marriage section", "dasha_use": "Timing mention only", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "CHILDREN", "current_rules": ["_read_children"], "source_coverage": "NONE", "varga_use": "No D7 usage", "dasha_use": "Timing mention only", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "HEALTH", "current_rules": ["_read_health", "dosha prose"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "Indirect", "transit_use": "No", "confidence": "LOW", "action": "REWRITE_AFTER_RESEARCH", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "LONGEVITY", "current_rules": ["_read_longevity", "maraka note"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "Maraka warning only", "transit_use": "No", "confidence": "VERY_LOW", "action": "REWRITE_AFTER_RESEARCH", "status": "HEURISTIC"},
        {"domain": "REMEDIES", "current_rules": ["_lal_kitab_remedies", "dosha remedies", "life-guide restatement"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "No", "transit_use": "No", "confidence": "VERY_LOW", "action": "RESEARCH_FURTHER", "status": "HEURISTIC"},
        {"domain": "EDUCATION", "current_rules": ["_read_education"], "source_coverage": "NONE", "varga_use": "No D24 usage", "dasha_use": "No", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "HOME_AND_FAMILY", "current_rules": ["_read_home_family"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "No", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "SIBLINGS_AND_COURAGE", "current_rules": ["_read_siblings"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "No", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "FATHER_AND_FORTUNE", "current_rules": ["_read_father_fortune"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "No", "transit_use": "No", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "SPIRITUALITY", "current_rules": ["_read_spirituality", "life-guide summary"], "source_coverage": "NONE", "varga_use": "No", "dasha_use": "Indirect", "transit_use": "Sade Sati note in life guide only", "confidence": "LOW", "action": "SOURCE_AND_MIGRATE", "status": "FUNCTIONAL_UNSOURCED"},
        {"domain": "ASTROFINANCE", "current_rules": ["SECTOR_RULERS", "_compute_sector_signals", "AstroSignalCard explanations"], "source_coverage": "MODERN_ONLY", "varga_use": "Not applicable", "dasha_use": "No", "transit_use": "Yes", "confidence": "LOW", "action": "KEEP_AS_ASTROFINANCE_EXPERIMENT", "status": "HEURISTIC"},
    ]


def _astrofinance_matrix() -> list[dict[str, Any]]:
    return [
        {
            "astrofinance_rule_id": "VEDA-P005-AF-0001",
            "current_formula": "Hardcoded sector -> ruling planets mapping in SECTOR_RULERS",
            "rationale": "Indian/NSE sector-planet mapping per AstroFinance module comments",
            "textual_support": "MODERN_ASTROLOGY_ONLY",
            "empirical_support": "NONE_IN_REPOSITORY",
            "backtest_status": "NOT_FOUND",
            "production_use": ["get_astro_signal", "ReportPage", "AstroSignalCard"],
            "classification": "MODERN_ASTROLOGY",
        },
        {
            "astrofinance_rule_id": "VEDA-P005-AF-0002",
            "current_formula": "Sign-strength scoring: exalted +4, own sign +3, neutral 0, enemy/debilitated negative",
            "rationale": "Planetary dignity strength translated into sector scoring",
            "textual_support": "MODERN_ASTROLOGY_ONLY",
            "empirical_support": "NONE_IN_REPOSITORY",
            "backtest_status": "NOT_FOUND",
            "production_use": ["astro_engine::_compute_sector_signals"],
            "classification": "TRADITIONAL_INTERPRETIVE",
        },
        {
            "astrofinance_rule_id": "VEDA-P005-AF-0003",
            "current_formula": "Retrograde penalty, aspect contributions, Moon contribution, eclipse penalty/boost, then action thresholds",
            "rationale": "Daily sector action label generation",
            "textual_support": "MODERN_ASTROLOGY_ONLY",
            "empirical_support": "NONE_IN_REPOSITORY",
            "backtest_status": "NOT_FOUND",
            "production_use": ["astro_engine::_compute_sector_signals", "get_astro_signal"],
            "classification": "ASTROFINANCE_HYPOTHESIS",
        },
        {
            "astrofinance_rule_id": "VEDA-P005-AF-0004",
            "current_formula": "Eclipse type Rahu -> hold/uptrend potential, Ketu -> avoid/downtrend pressure",
            "rationale": "AstroFinance eclipse timing note",
            "textual_support": "MODERN_ASTROLOGY_ONLY",
            "empirical_support": "NONE_IN_REPOSITORY",
            "backtest_status": "NOT_FOUND",
            "production_use": ["astro_engine::_compute_sector_signals", "AstroSignalCard"],
            "classification": "ASTROFINANCE_HYPOTHESIS",
        },
        {
            "astrofinance_rule_id": "VEDA-P005-AF-0005",
            "current_formula": "Frontend buildPlainReason restates astro_action into explanatory prose",
            "rationale": "Improve user comprehension of sector signal",
            "textual_support": "INTERNAL_HEURISTIC",
            "empirical_support": "NOT_APPLICABLE",
            "backtest_status": "NOT_APPLICABLE",
            "production_use": ["AstroSignalCard"],
            "classification": "INTERNAL_HEURISTIC",
        },
    ]


def _high_stakes_register(samples: dict[str, Any]) -> list[dict[str, Any]]:
    personal = samples["personal"]
    return [
        {
            "high_stakes_id": "VEDA-P005-HS-0001",
            "surface_id": "VEDA-P005-SURF-0007",
            "domain": "FINANCE",
            "classification": "FINANCIAL_LIKE",
            "severity": "P0",
            "current_output": "Stock kundli produces BUY/HOLD/CAUTION/EXIT/AVOID style actions and STRONG_BUY/BUY/HOLD/CAUTION/EXIT/AVOID interpretation signals.",
            "evidence": stock_factor_excerpt(samples),
            "risk": "Deterministic investment-like labels are produced without governed provenance or user-facing uncertainty controls.",
        },
        {
            "high_stakes_id": "VEDA-P005-HS-0002",
            "surface_id": "VEDA-P005-SURF-0010",
            "domain": "FINANCE",
            "classification": "FINANCIAL_LIKE",
            "severity": "P0",
            "current_output": "AstroFinance sector tool emits BUY/HOLD/CAUTION/EXIT/AVOID actions with directive reason strings.",
            "evidence": "astro_engine.py action ladder and get_astro_signal() sector payload fields `astro_action` + `astro_reason`.",
            "risk": "Sector-level trading guidance is modern/hypothesis-driven and not separated by confidence or research approval state inside the API output itself.",
        },
        {
            "high_stakes_id": "VEDA-P005-HS-0003",
            "surface_id": "VEDA-P005-SURF-0003",
            "domain": "HEALTH",
            "classification": "MEDICAL_LIKE",
            "severity": "P1",
            "current_output": "Personal report includes a dedicated HEALTH & LONGEVITY section with constitution and disease-oriented language.",
            "evidence": personal["report_snippets"]["health"],
            "risk": "Traditional interpretation is presented as direct health guidance without a strong health-specific caution block.",
        },
        {
            "high_stakes_id": "VEDA-P005-HS-0004",
            "surface_id": "VEDA-P005-SURF-0003",
            "domain": "LONGEVITY",
            "classification": "PREDICTIVE",
            "severity": "P0",
            "current_output": "Personal report includes a LONGEVITY & LIFE SPAN (AYURDAYA PRINCIPLES) section and maraka warning.",
            "evidence": personal["report_snippets"]["longevity"],
            "risk": "Lifespan-oriented language is inherently high-stakes and currently lacks governed sourcing and safety gating.",
        },
        {
            "high_stakes_id": "VEDA-P005-HS-0005",
            "surface_id": "VEDA-P005-SURF-0001",
            "domain": "REMEDIES",
            "classification": "REMEDIAL",
            "severity": "P1",
            "current_output": "Personal report and life-guide restate Lal Kitab remedies as concrete actions.",
            "evidence": personal["report_snippets"]["remedies"] or personal["report_snippets"]["doshas"],
            "risk": "Remedies are operational user guidance with no governed cost/safety or source registry linkage.",
        },
    ]


def stock_factor_excerpt(samples: dict[str, Any]) -> str:
    stock = samples["stock"]
    parts = stock["bullish_factors"][:2] + stock["bearish_factors"][:2]
    return " | ".join(parts)


def _traceability_cases(samples: dict[str, Any]) -> list[dict[str, Any]]:
    personal = samples["personal"]
    stock = samples["stock"]
    return [
        {
            "trace_case_id": "VEDA-P005-TRACE-0001",
            "output_id": "personal_current_dasha_header",
            "surface_id": "VEDA-P005-SURF-0002",
            "interpretation_id": "VEDA-P005-LGC-0016",
            "sample_output_excerpt": personal["report_snippets"]["current_period"],
            "chart_facts": ["Moon Nakshatra", "current Mahadasha", "current Antardasha", "lagna sign", "planet dignity"],
            "rule_ids": ["VEDA-RUL-DASHA-000001", "VEDA-RUL-DASHA-000002"],
            "claim_ids": ["VEDA-CLM-000001", "VEDA-CLM-000002", "VEDA-CLM-000004"],
            "passage_ids": ["VEDA-PSG-000001", "VEDA-PSG-000002", "VEDA-PSG-000003", "VEDA-PSG-000006"],
            "source_ids": ["VEDA-SRC-000001", "VEDA-SRC-000002", "VEDA-SRC-000003"],
            "status": "COMPLETE_CHAIN",
            "missing_links": [],
            "notes": "Complete chain exists only for the governed Vimshottari timing baseline, not for the full descriptive narrative layer.",
        },
        {
            "trace_case_id": "VEDA-P005-TRACE-0002",
            "output_id": "personal_finance_section",
            "surface_id": "VEDA-P005-SURF-0003",
            "interpretation_id": "VEDA-P005-LGC-0020",
            "sample_output_excerpt": personal["report_snippets"]["finance"],
            "chart_facts": ["H2 sign/lord", "H11 sign/lord", "Jupiter position", "Venus position", "Dhana yoga list"],
            "rule_ids": ["VEDA-P005-LGC-0020"],
            "claim_ids": [],
            "passage_ids": [],
            "source_ids": [],
            "status": "INCOMPLETE_CHAIN",
            "missing_links": ["governed claim", "passage", "source"],
            "notes": "Important finance interpretation surface is operational but unsourced.",
        },
        {
            "trace_case_id": "VEDA-P005-TRACE-0003",
            "output_id": "personal_marriage_section",
            "surface_id": "VEDA-P005-SURF-0003",
            "interpretation_id": "VEDA-P005-LGC-0021",
            "sample_output_excerpt": personal["report_snippets"]["marriage"],
            "chart_facts": ["H5 sign/lord", "H7 sign/lord", "Venus position", "Mars position", "Moon position"],
            "rule_ids": ["VEDA-P005-LGC-0021", "VEDA-P005-LGC-0007"],
            "claim_ids": [],
            "passage_ids": [],
            "source_ids": [],
            "status": "INCOMPLETE_CHAIN",
            "missing_links": ["governed claim", "passage", "source"],
            "notes": "Marriage section includes direct timing and Manglik logic without governed provenance.",
        },
        {
            "trace_case_id": "VEDA-P005-TRACE-0004",
            "output_id": "personal_health_longevity_sections",
            "surface_id": "VEDA-P005-SURF-0003",
            "interpretation_id": "VEDA-P005-LGC-0022",
            "sample_output_excerpt": personal["report_snippets"]["health"] + "\n\n" + personal["report_snippets"]["longevity"],
            "chart_facts": ["H1/H6/H8 strength", "Saturn position", "Mars position", "Moon position", "maraka lords"],
            "rule_ids": ["VEDA-P005-LGC-0022"],
            "claim_ids": [],
            "passage_ids": [],
            "source_ids": [],
            "status": "INCOMPLETE_CHAIN",
            "missing_links": ["governed claim", "passage", "source"],
            "notes": "This is the most sensitive unsourced interpretation chain in the personal path.",
        },
        {
            "trace_case_id": "VEDA-P005-TRACE-0005",
            "output_id": "stock_gaja_kesari_factor",
            "surface_id": "VEDA-P005-SURF-0007",
            "interpretation_id": "VEDA-P005-LGC-0025",
            "sample_output_excerpt": " | ".join(stock["bullish_factors"][:4]),
            "chart_facts": ["Moon house", "Jupiter house", "yoga list", "Mahadasha", "2H/11H house summaries"],
            "rule_ids": ["VEDA-P005-LGC-0025", "VEDA-RUL-YOGA-000001"],
            "claim_ids": [],
            "passage_ids": [],
            "source_ids": [],
            "status": "PARTIAL_CHAIN",
            "missing_links": ["governed source evidence for the runtime stock yoga logic"],
            "notes": "P003 pilot mapping exists for Gaja Kesari, but the active stock-path implementation is not source-linked.",
        },
        {
            "trace_case_id": "VEDA-P005-TRACE-0006",
            "output_id": "astrofinance_sector_action",
            "surface_id": "VEDA-P005-SURF-0010",
            "interpretation_id": "VEDA-P005-LGC-0031",
            "sample_output_excerpt": "Sector API returns astro_action plus astro_reason based on sector rulers, current sign state, aspects, Moon phase, and eclipse state.",
            "chart_facts": ["sector rule set", "current planetary positions", "aspects", "Moon phase", "eclipse flags"],
            "rule_ids": ["VEDA-P005-LGC-0030", "VEDA-P005-LGC-0031"],
            "claim_ids": [],
            "passage_ids": [],
            "source_ids": [],
            "status": "INCOMPLETE_CHAIN",
            "missing_links": ["P002-registered source", "claim", "passage"],
            "notes": "AstroFinance is intentionally separate from classical Jyotisha but is not yet represented in the research-governance registry.",
        },
    ]


def _disposition_for_rule(rule: dict[str, Any]) -> tuple[str, str]:
    rule_id = rule["legacy_rule_id"]
    source_status = rule["source_status"]
    domain = rule["domain"]
    if rule_id in {"VEDA-P005-LGC-0016", "VEDA-P005-LGC-0023"}:
        return ("SOURCE_AND_MIGRATE", "P1")
    if domain in {"HEALTH_LONGEVITY", "REMEDIES"}:
        return ("REWRITE_AFTER_RESEARCH", "P0")
    if source_status == "SOURCE_VALIDATED":
        return ("PRESERVE", "P1")
    if source_status in {"ASTROFINANCE_HYPOTHESIS", "MODERN_INTERPRETATION"}:
        return ("KEEP_AS_ASTROFINANCE_EXPERIMENT", "P3")
    if source_status == "HEURISTIC":
        return ("KEEP_AS_HEURISTIC", "P2")
    if domain in {"YOGA", "DOSHA", "CAREER", "FINANCE", "MARRIAGE"}:
        return ("SOURCE_AND_MIGRATE", "P1")
    return ("RESEARCH_FURTHER", "P2")


def _disposition_matrix(legacy_rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for rule in legacy_rules:
        disposition, priority = _disposition_for_rule(rule)
        rows.append(
            {
                "legacy_rule_id": rule["legacy_rule_id"],
                "location": rule["location"],
                "domain": rule["domain"],
                "source_status": rule["source_status"],
                "future_disposition": disposition,
                "priority": priority,
            }
        )
    return rows


def _summary(
    surfaces: list[dict[str, Any]],
    legacy_rules: list[dict[str, Any]],
    yoga_dosha: list[dict[str, Any]],
    dasha_rows: list[dict[str, Any]],
    domains: list[dict[str, Any]],
    astrofinance: list[dict[str, Any]],
    high_stakes: list[dict[str, Any]],
    traces: list[dict[str, Any]],
    disposition: list[dict[str, Any]],
) -> dict[str, Any]:
    source_validated = sum(1 for rule in legacy_rules if rule["source_status"] == "SOURCE_VALIDATED")
    legacy_unsourced = sum(1 for rule in legacy_rules if rule["source_status"] == "LEGACY_UNSOURCED")
    heuristic = sum(1 for rule in legacy_rules if rule["source_status"] == "HEURISTIC")
    modern_only = sum(1 for rule in legacy_rules if rule["source_status"] in {"MODERN_INTERPRETATION", "ASTROFINANCE_HYPOTHESIS"})
    yoga_rows = [row for row in yoga_dosha if row["kind"] == "YOGA"]
    dosha_rows = [row for row in yoga_dosha if row["kind"] == "DOSHA"]
    yoga_conflicts = sum(1 for row in yoga_rows if row["source_conflict"] not in {"", "none recorded", "not governed"})
    dosha_conflicts = sum(1 for row in dosha_rows if row["source_conflict"] not in {"", "none recorded", "not governed"})
    complete_traces = sum(1 for row in traces if row["status"] == "COMPLETE_CHAIN")
    return {
        "phase_id": PHASE_ID,
        "phase_date": PHASE_DATE,
        "surface_count": len(surfaces),
        "legacy_rule_count": len(legacy_rules),
        "source_validated_count": source_validated,
        "legacy_unsourced_count": legacy_unsourced,
        "heuristic_count": heuristic,
        "modern_only_count": modern_only,
        "yoga_count": len(yoga_rows),
        "dosha_count": len(dosha_rows),
        "yoga_conflict_count": yoga_conflicts,
        "dosha_conflict_count": dosha_conflicts,
        "dasha_pattern_count": len(dasha_rows),
        "domain_count": len(domains),
        "astrofinance_rule_count": len(astrofinance),
        "high_stakes_count": len(high_stakes),
        "p0_high_stakes_count": sum(1 for row in high_stakes if row["severity"] == "P0"),
        "trace_case_count": len(traces),
        "complete_trace_count": complete_traces,
        "incomplete_trace_count": len(traces) - complete_traces,
        "preserve_count": sum(1 for row in disposition if row["future_disposition"] == "PRESERVE"),
        "source_and_migrate_count": sum(1 for row in disposition if row["future_disposition"] == "SOURCE_AND_MIGRATE"),
        "research_further_count": sum(1 for row in disposition if row["future_disposition"] == "RESEARCH_FURTHER"),
        "rewrite_after_research_count": sum(1 for row in disposition if row["future_disposition"] == "REWRITE_AFTER_RESEARCH"),
        "deprecate_after_replacement_count": sum(1 for row in disposition if row["future_disposition"] == "DEPRECATE_AFTER_REPLACEMENT"),
        "production_astrology_behaviour_changed": "NO",
        "production_rules_migrated": 0,
        "known_inherited_failures": ["tests/test_veda_chat_engine.py (8 baseline failures)"],
        "final_verdict": "PASS WITH CONDITIONS",
        "verdict_basis": [
            "Major interpretation surfaces are mapped and machine-readable.",
            "Representative traceability chains exist, but most interpretation rules remain unsourced.",
            "High-stakes health, longevity, finance, and remedies outputs remain operational and need governed follow-up before stronger acceptance.",
        ],
    }


def build_phase_bundle() -> dict[str, Any]:
    samples = collect_runtime_samples()
    surfaces = _surface_inventory(samples)
    legacy_rules = _legacy_rule_registry()
    yoga_dosha = _yoga_dosha_matrix()
    dasha_rows = _dasha_interpretation_matrix()
    domains = _domain_validation_matrix()
    astrofinance = _astrofinance_matrix()
    high_stakes = _high_stakes_register(samples)
    traces = _traceability_cases(samples)
    disposition = _disposition_matrix(legacy_rules)
    summary = _summary(surfaces, legacy_rules, yoga_dosha, dasha_rows, domains, astrofinance, high_stakes, traces, disposition)
    return {
        "meta": {
            "phase_id": PHASE_ID,
            "phase_date": PHASE_DATE,
            "generated_at": _phase_iso(),
            "frozen_now_utc": _phase_iso(),
        },
        "runtime_samples": samples,
        "surface_inventory": surfaces,
        "legacy_rule_registry": legacy_rules,
        "yoga_dosha_matrix": yoga_dosha,
        "dasha_interpretation_matrix": dasha_rows,
        "domain_validation_matrix": domains,
        "astrofinance_matrix": astrofinance,
        "high_stakes_register": high_stakes,
        "traceability_cases": traces,
        "disposition_matrix": disposition,
        "summary": summary,
    }


def export_phase_bundle(root: Path | None = None) -> list[Path]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    out_root = root / "data" / "veda" / "validation" / "interpretations"
    files = {
        "p005_surface_inventory.json": bundle["surface_inventory"],
        "p005_legacy_rule_registry.json": bundle["legacy_rule_registry"],
        "p005_yoga_dosha_matrix.json": bundle["yoga_dosha_matrix"],
        "p005_dasha_interpretation_matrix.json": bundle["dasha_interpretation_matrix"],
        "p005_domain_validation_matrix.json": bundle["domain_validation_matrix"],
        "p005_astrofinance_matrix.json": bundle["astrofinance_matrix"],
        "p005_high_stakes_register.json": bundle["high_stakes_register"],
        "p005_traceability_cases.json": bundle["traceability_cases"],
        "p005_disposition_matrix.json": bundle["disposition_matrix"],
        "p005_summary.json": {"meta": bundle["meta"], "runtime_samples": bundle["runtime_samples"], "summary": bundle["summary"]},
    }
    written: list[Path] = []
    for name, payload in files.items():
        path = out_root / name
        _to_json(path, payload)
        written.append(path)
    return written


def render_phase_docs(root: Path | None = None) -> list[Path]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    docs_root = root / "docs" / "current-state" / "p005"
    docs_root.mkdir(parents=True, exist_ok=True)

    summary = bundle["summary"]
    surfaces = bundle["surface_inventory"]
    legacy_rules = bundle["legacy_rule_registry"]
    yoga_rows = [row for row in bundle["yoga_dosha_matrix"] if row["kind"] == "YOGA"]
    dosha_rows = [row for row in bundle["yoga_dosha_matrix"] if row["kind"] == "DOSHA"]
    dasha_rows = bundle["dasha_interpretation_matrix"]
    domains = bundle["domain_validation_matrix"]
    astrofinance = bundle["astrofinance_matrix"]
    high_stakes = bundle["high_stakes_register"]
    traces = bundle["traceability_cases"]
    disposition = bundle["disposition_matrix"]
    samples = bundle["runtime_samples"]

    surface_lines = "\n".join(
        f"| `{row['surface_id']}` | `{row['status']}` | `{row['domain']}` | `{row['llm_used']}` | {row['path']} |"
        for row in surfaces
    )
    legacy_lines = "\n".join(
        f"| `{row['legacy_rule_id']}` | `{row['source_status']}` | `{row['domain']}` | `{row['logic_type']}` | {row['location']} |"
        for row in legacy_rules
    )
    yoga_lines = "\n".join(
        f"| {row['name']} | {', '.join(row['surfaces'])} | `{row['source_status']}` | `{row['recommendation']}` | {row['current_conditions']} |"
        for row in yoga_rows
    )
    dosha_lines = "\n".join(
        f"| {row['name']} | `{row['source_status']}` | `{row['recommendation']}` | {row['current_conditions']} |"
        for row in dosha_rows
    )
    dasha_lines = "\n".join(
        f"| `{row['dasha_rule_id']}` | `{row['source_status']}` | `{row['domain']}` | {row['current_text_logic']} |"
        for row in dasha_rows
    )
    domain_lines = "\n".join(
        f"| {row['domain']} | `{row['status']}` | {row['source_coverage']} | {row['varga_use']} | {row['dasha_use']} | {row['transit_use']} | {row['confidence']} | `{row['action']}` |"
        for row in domains
    )
    astrofinance_lines = "\n".join(
        f"| `{row['astrofinance_rule_id']}` | `{row['classification']}` | {row['current_formula']} | {row['empirical_support']} |"
        for row in astrofinance
    )
    high_stakes_lines = "\n".join(
        f"| `{row['high_stakes_id']}` | {row['domain']} | `{row['severity']}` | {row['classification']} | {row['risk']} |"
        for row in high_stakes
    )
    trace_lines = "\n".join(
        f"| `{row['trace_case_id']}` | `{row['status']}` | `{row['surface_id']}` | {', '.join(row['chart_facts'])} | {', '.join(row['missing_links']) or '--'} |"
        for row in traces
    )
    disposition_lines = "\n".join(
        f"| `{row['legacy_rule_id']}` | `{row['future_disposition']}` | `{row['priority']}` | {row['domain']} |"
        for row in disposition
    )

    docs = {
        "VEDA-P005-00_EXECUTIVE_SUMMARY.md": f"""# VEDA-P005 Executive Summary

Date baseline: `{PHASE_DATE}`

VEDA-P005 validated the current interpretation layer without changing production astrology behavior. The phase mapped the personal kundli report stack, the REST/stock/country finance-oriented interpretation stack, the chat kundli verbatim path, and the separate AstroFinance sector-signal surface.

Current reality:

- personal kundli is the broadest interpretation surface and is entirely deterministic once the chart is computed;
- REST human, stock, and country endpoints reuse the finance-oriented `KundliInterpretator`, which is materially different from the personal life-reading path;
- most interpretation rules remain unsourced at rule level even where files cite classical works in headers;
- the only governed traceability chain that reaches the P002/P003 registry today is the protected Vimshottari timing baseline, not the narrative meaning layer;
- high-stakes domains remain active: finance-style actions, health, longevity, and remedies.

Core counts:

- Interpretation surfaces: `{summary['surface_count']}`
- Legacy rules inventoried: `{summary['legacy_rule_count']}`
- Source-validated legacy rules: `{summary['source_validated_count']}`
- Unsourced legacy rules: `{summary['legacy_unsourced_count']}`
- Yoga rows audited: `{summary['yoga_count']}`
- Dosha rows audited: `{summary['dosha_count']}`
- Traceability cases: `{summary['trace_case_count']}` (`{summary['complete_trace_count']}` complete)
- P0 high-stakes findings: `{summary['p0_high_stakes_count']}`

Representative runtime evidence under frozen `{summary['phase_date']}`:

- Personal sample lagna: `{samples['personal']['lagna']}`; Mahadasha: `{samples['personal']['mahadasha']}`
- Personal sample yogas: `{", ".join(samples['personal']['yoga_names'])}`
- Personal sample doshas: `{", ".join(samples['personal']['dosha_names'])}`
- REST human sample interpretation signal: `{samples['rest_human']['interpretation_signal']}`
- Stock sample interpretation signal: `{samples['stock']['interpretation_signal']}` with stock action `{samples['stock']['astro_action']}`
- Country sample interpretation signal: `{samples['country']['interpretation_signal']}`
""",
        "VEDA-P005-01_INTERPRETATION_SURFACE_INVENTORY.md": f"""# VEDA-P005 Interpretation Surface Inventory

| Surface ID | Status | Domain | LLM | Path |
| --- | --- | --- | --- | --- |
{surface_lines}

Notes:

- Personal kundli uses deterministic section builders and appends two extra deterministic layers (`generate_life_readings` and `build_life_guide`).
- REST human, stock, and country outputs are materially different: they surface finance-oriented factor lists and optional LLM summaries through `KundliInterpretator`.
- AstroFinance is a separate sector-level interpretation family and should not be conflated with natal Jyotisha.
""",
        "VEDA-P005-02_LEGACY_RULE_AUDIT.md": f"""# VEDA-P005 Legacy Rule Audit

| Legacy Rule ID | Source Status | Domain | Logic Type | Location |
| --- | --- | --- | --- | --- |
{legacy_lines}

Summary:

- Source-validated: `{summary['source_validated_count']}`
- Legacy-unsourced: `{summary['legacy_unsourced_count']}`
- Heuristic: `{summary['heuristic_count']}`
- Modern-only / AstroFinance-hypothesis: `{summary['modern_only_count']}`
""",
        "VEDA-P005-03_GRAHA_BHAVA_DIGNITY_VALIDATION.md": f"""# VEDA-P005 Graha, Bhava & Dignity Interpretation Validation

The dominant personal-path interpretation substrate is still:

- `PLANET_IN_HOUSE`
- `LORD_IN_HOUSE`
- `_karaka_area_sentence`
- `_lord_sentence`

These tables and helper functions drive the sections for finance, marriage, health, spirituality, and current Dasha interpretation. They are operational, deterministic, and unsourced at rule level.

Representative personal finance excerpt:

```text
{samples['personal']['report_snippets']['finance']}
```

Representative personal marriage excerpt:

```text
{samples['personal']['report_snippets']['marriage']}
```

Assessment:

- Graha-in-bhava meanings: `FUNCTIONAL_UNSOURCED`
- Lordship and dignity prose: `FUNCTIONAL_UNSOURCED`
- Functional yogakaraka override in Dasha reading: `PARTIALLY_VALIDATED`
""",
        "VEDA-P005-04_YOGA_DOSHA_VALIDATION.md": f"""# VEDA-P005 Yoga & Dosha Validation

Yogas:

| Name | Surfaces | Source Status | Recommendation | Current Conditions |
| --- | --- | --- | --- | --- |
{yoga_lines}

Doshas:

| Name | Source Status | Recommendation | Current Conditions |
| --- | --- | --- | --- |
{dosha_lines}

Observations:

- Personal and stock paths use different yoga catalogs and different condition logic.
- `Kaal Sarp` versus `Kala Sarpa` is a naming and algorithm divergence, not just spelling.
- No yoga or dosha currently reaches a research-grade, source-linked implementation state.
""",
        "VEDA-P005-05_VIMSHOTTARI_INTERPRETATION_VALIDATION.md": f"""# VEDA-P005 Vimshottari Interpretation Validation

| Rule ID | Source Status | Domain | Current Logic |
| --- | --- | --- | --- |
{dasha_lines}

Key distinction:

- P004 validated the deterministic Vimshottari calculation layer.
- P005 shows that the descriptive meaning attached to those periods is still mostly heuristic or legacy-unsourced.
- Only the period-selection baseline currently links through the P002/P003 governed chain.
""",
        "VEDA-P005-06_DOMAIN_VALIDATION.md": f"""# VEDA-P005 Domain Validation

| Domain | Status | Source Coverage | Varga Use | Dasha Use | Transit Use | Confidence | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
{domain_lines}

Interpretation:

- Marriage, finance, and career are implemented, but they remain unsourced at rule level.
- Health, longevity, and remedies are active and require tighter future governance because of the stakes.
- Education, home/family, siblings, father/fortune, and spirituality are present as deterministic prose sections rather than governed rule sets.
""",
        "VEDA-P005-07_ASTROFINANCE_VALIDATION.md": f"""# VEDA-P005 AstroFinance Validation

| Rule ID | Classification | Current Formula | Empirical Support |
| --- | --- | --- | --- |
{astrofinance_lines}

Boundary:

- AstroFinance is active and production-wired.
- AstroFinance is not classical natal Jyotisha in the current repository.
- AstroFinance source handling remains modern-only and outside the P002 registry at this point.
""",
        "VEDA-P005-08_HIGH_STAKES_REVIEW.md": f"""# VEDA-P005 High-Stakes Review

| High-Stakes ID | Domain | Severity | Classification | Risk |
| --- | --- | --- | --- | --- |
{high_stakes_lines}

Representative longevity excerpt:

```text
{samples['personal']['report_snippets']['longevity']}
```

Representative health excerpt:

```text
{samples['personal']['report_snippets']['health']}
```
""",
        "VEDA-P005-09_TRACEABILITY_REPORT.md": f"""# VEDA-P005 Traceability Report

| Trace Case | Status | Surface | Chart Facts | Missing Links |
| --- | --- | --- | --- | --- |
{trace_lines}

Result:

- Complete chains: `{summary['complete_trace_count']}`
- Incomplete chains: `{summary['incomplete_trace_count']}`

The interpretation layer is therefore explainable only in a narrow subset today, mainly where the governed Vimshottari baseline can be reused.
""",
        "VEDA-P005-10_RULE_DISPOSITION_MATRIX.md": f"""# VEDA-P005 Rule Disposition Matrix

| Legacy Rule ID | Future Disposition | Priority | Domain |
| --- | --- | --- | --- |
{disposition_lines}
""",
        "VEDA-P005-11_VALIDATION_REPORT.md": f"""# VEDA-P005 Validation Report

Bundle integrity expectations:

- exported interpretation validation files under `data/veda/validation/interpretations/`
- generated documentation under `docs/current-state/p005/`
- regression checks for personal, REST human, stock, country, and AstroFinance surfaces

Inherited baseline conditions:

- `tests/test_veda_chat_engine.py` still has 8 known failures outside P005 scope
- P004 calculation issues remain inherited and are not normalized by this phase

Production behavior statement:

- `Production Astrology Behaviour Changed: NO`
- `Production Rules Migrated: 0`
""",
        "VEDA-P005-12_FINAL_ACCEPTANCE.md": f"""# VEDA-P005 Final Acceptance

Recommended result: `{summary['final_verdict']}`

Conditions:

1. Most interpretation rules remain unsourced at rule level.
2. High-stakes health, longevity, finance, and remedies outputs remain active.
3. AstroFinance remains operational but governed separately from classical Jyotisha.
4. The personal, REST, stock, and country interpretation paths remain divergent and should not be silently merged.

Positive outcome:

- The interpretation layer is now machine-readable enough to support later research migration.
- Current user-facing surfaces and high-risk rule families are explicitly identified.
- The protected P001-P004 baselines can now be used to validate future interpretation changes without losing evidence of current behavior.
""",
    }

    written: list[Path] = []
    for name, content in docs.items():
        path = docs_root / name
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def validate_exported_bundle(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[3]
    bundle = build_phase_bundle()
    data_root = root / "data" / "veda" / "validation" / "interpretations"
    expected_files = {
        "p005_surface_inventory.json": bundle["surface_inventory"],
        "p005_legacy_rule_registry.json": bundle["legacy_rule_registry"],
        "p005_yoga_dosha_matrix.json": bundle["yoga_dosha_matrix"],
        "p005_dasha_interpretation_matrix.json": bundle["dasha_interpretation_matrix"],
        "p005_domain_validation_matrix.json": bundle["domain_validation_matrix"],
        "p005_astrofinance_matrix.json": bundle["astrofinance_matrix"],
        "p005_high_stakes_register.json": bundle["high_stakes_register"],
        "p005_traceability_cases.json": bundle["traceability_cases"],
        "p005_disposition_matrix.json": bundle["disposition_matrix"],
        "p005_summary.json": {"meta": bundle["meta"], "runtime_samples": bundle["runtime_samples"], "summary": bundle["summary"]},
    }
    missing: list[str] = []
    mismatched: list[str] = []
    for name, expected in expected_files.items():
        path = data_root / name
        if not path.exists():
            missing.append(name)
            continue
        actual = _load_json(path)
        if actual != expected:
            mismatched.append(name)
    return {
        "surface_count": bundle["summary"]["surface_count"],
        "legacy_rule_count": bundle["summary"]["legacy_rule_count"],
        "high_stakes_count": bundle["summary"]["high_stakes_count"],
        "trace_case_count": bundle["summary"]["trace_case_count"],
        "missing_files": missing,
        "mismatched_files": mismatched,
        "is_valid": not missing and not mismatched,
    }


__all__ = [
    "PHASE_DATE",
    "PHASE_ID",
    "build_phase_bundle",
    "collect_runtime_samples",
    "export_phase_bundle",
    "render_phase_docs",
    "validate_exported_bundle",
]
