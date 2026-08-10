# VEDA-P005 Interpretation Surface Inventory

| Surface ID | Status | Domain | LLM | Path |
| --- | --- | --- | --- | --- |
| `VEDA-P005-SURF-0001` | `HYBRID` | `PERSONAL_KUNDLI_MULTI_DOMAIN` | `False` | engines/ai/chatbot/tools/data_tools.py -> generate_personal_kundli -> engines/ai/chatbot/tools/kundli_calculator.py::compute_personal_kundli |
| `VEDA-P005-SURF-0002` | `DETERMINISTIC` | `PERSONAL_FORMATTED_REPORT` | `False` | engines/ai/chatbot/tools/kundli_calculator.py::_build_formatted_report |
| `VEDA-P005-SURF-0003` | `RULE_BASED` | `PERSONAL_LIFE_AREAS` | `False` | engines/ai/chatbot/tools/kundli_interpreter.py::generate_life_readings |
| `VEDA-P005-SURF-0004` | `HEURISTIC` | `PERSONAL_LIFE_GUIDE_AND_TIMING` | `False` | engines/ai/chatbot/tools/kundli_life_guide.py::build_life_guide |
| `VEDA-P005-SURF-0005` | `DETERMINISTIC` | `CHAT_KUNDLI_VERBATIM` | `False` | engines/ai/chatbot/chat_engine.py::_run_turn |
| `VEDA-P005-SURF-0006` | `HYBRID` | `REST_HUMAN_FINANCE_ORIENTED_INTERPRETATION` | `OPTIONAL` | backend/routers/kundli.py::human_kundli -> engines/intelligence/kundli_interpretator.py::KundliInterpretator.interpret |
| `VEDA-P005-SURF-0007` | `HYBRID` | `STOCK_KUNDLI_FINANCE` | `OPTIONAL` | backend/routers/kundli.py::stock_kundli -> engines/intelligence/kundli_engine.py::_detect_yogas/_financial_score -> engines/intelligence/kundli_interpretator.py::interpret |
| `VEDA-P005-SURF-0008` | `HYBRID` | `COUNTRY_KUNDLI_FINANCE_STYLE` | `OPTIONAL` | backend/routers/kundli.py::country_kundli -> engines/intelligence/kundli_interpretator.py::interpret |
| `VEDA-P005-SURF-0009` | `LLM_SYNTHESIZED` | `STOCK_COUNTRY_OPTIONAL_LLM_SUMMARY` | `True` | engines/intelligence/kundli_interpretator.py::_generate_narrative |
| `VEDA-P005-SURF-0010` | `RULE_BASED` | `ASTROFINANCE_SECTOR_SIGNAL` | `False` | engines/ai/chatbot/tools/data_tools.py::get_astro_signal |
| `VEDA-P005-SURF-0011` | `HEURISTIC` | `ASTROFINANCE_UI_EXPLANATION` | `False` | frontend/src/components/platform/AstroSignalCard.tsx |
| `VEDA-P005-SURF-0012` | `DETERMINISTIC` | `STOCK_KUNDLI_UI` | `False` | frontend/src/components/platform/KundliCard.tsx |
| `VEDA-P005-SURF-0013` | `HYBRID` | `STOCK_REPORT_UI` | `False` | frontend/src/pages/ReportPage.tsx |
| `VEDA-P005-SURF-0014` | `DETERMINISTIC` | `CHAT_QUICK_ACTIONS` | `False` | frontend/src/pages/ChatPage.tsx |

Notes:

- Personal kundli uses deterministic section builders and appends two extra deterministic layers (`generate_life_readings` and `build_life_guide`).
- REST human, stock, and country outputs are materially different: they surface finance-oriented factor lists and optional LLM summaries through `KundliInterpretator`.
- AstroFinance is a separate sector-level interpretation family and should not be conflated with natal Jyotisha.
