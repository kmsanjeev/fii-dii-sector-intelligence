# VEDA-P005 Legacy Rule Audit

| Legacy Rule ID | Source Status | Domain | Logic Type | Location |
| --- | --- | --- | --- | --- |
| `VEDA-P005-LGC-0001` | `LEGACY_UNSOURCED` | `YOGA` | `RULE_SET` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0002` | `SOURCE_CANDIDATE_FOUND` | `YOGA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0003` | `LEGACY_UNSOURCED` | `YOGA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0004` | `LEGACY_UNSOURCED` | `YOGA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0005` | `LEGACY_UNSOURCED` | `YOGA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0006` | `LEGACY_UNSOURCED` | `YOGA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0007` | `LEGACY_UNSOURCED` | `DOSHA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0008` | `LEGACY_UNSOURCED` | `DOSHA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0009` | `LEGACY_UNSOURCED` | `DOSHA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0010` | `LEGACY_UNSOURCED` | `DOSHA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0011` | `LEGACY_UNSOURCED` | `DOSHA` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0012` | `LEGACY_UNSOURCED` | `REMEDIES` | `LOOKUP_AND_AGGREGATION` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0013` | `HEURISTIC` | `SUMMARY_SCORING` | `SCORING` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0014` | `HEURISTIC` | `SUMMARY_FACTORS` | `FACTOR_LIST` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0015` | `HEURISTIC` | `SUMMARY_NARRATIVE` | `TEMPLATE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0016` | `SOURCE_VALIDATED` | `DASHA_INTERPRETATION` | `RULE` | engines/ai/chatbot/tools/kundli_calculator.py |
| `VEDA-P005-LGC-0017` | `LEGACY_UNSOURCED` | `GRAHA_BHAVA_INTERPRETATION` | `TABLE` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0018` | `LEGACY_UNSOURCED` | `LORDSHIP_INTERPRETATION` | `TABLE` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0019` | `LEGACY_UNSOURCED` | `CAREER` | `SECTION_SYNTHESIS` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0020` | `LEGACY_UNSOURCED` | `FINANCE` | `SECTION_SYNTHESIS` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0021` | `LEGACY_UNSOURCED` | `MARRIAGE` | `SECTION_SYNTHESIS` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0022` | `LEGACY_UNSOURCED` | `HEALTH_LONGEVITY` | `SECTION_SYNTHESIS` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0023` | `LEGACY_PARTIALLY_SOURCED` | `DASHA_INTERPRETATION` | `SECTION_SYNTHESIS` | engines/ai/chatbot/tools/kundli_interpreter.py |
| `VEDA-P005-LGC-0024` | `HEURISTIC` | `DASHA_GUIDANCE` | `SCORING_AND_ADVICE` | engines/ai/chatbot/tools/kundli_life_guide.py |
| `VEDA-P005-LGC-0025` | `LEGACY_UNSOURCED` | `STOCK_YOGA` | `RULE_SET` | engines/intelligence/kundli_engine.py |
| `VEDA-P005-LGC-0026` | `HEURISTIC` | `STOCK_FINANCIAL_HOUSES` | `SCORING` | engines/intelligence/kundli_engine.py |
| `VEDA-P005-LGC-0027` | `ASTROFINANCE_HYPOTHESIS` | `STOCK_SIGNAL` | `WEIGHTED_SCORE` | engines/intelligence/kundli_engine.py |
| `VEDA-P005-LGC-0028` | `ASTROFINANCE_HYPOTHESIS` | `STOCK_DASHA_FINANCE` | `LOOKUP_AND_SYNTHESIS` | engines/intelligence/kundli_interpretator.py |
| `VEDA-P005-LGC-0029` | `HEURISTIC` | `STOCK_LLM_SUMMARY` | `PROMPT_TEMPLATE` | engines/intelligence/kundli_interpretator.py |
| `VEDA-P005-LGC-0030` | `MODERN_INTERPRETATION` | `ASTROFINANCE` | `MAPPING_TABLE` | engines/intelligence/astro_engine.py |
| `VEDA-P005-LGC-0031` | `ASTROFINANCE_HYPOTHESIS` | `ASTROFINANCE` | `SIGNAL_LOGIC` | engines/intelligence/astro_engine.py |
| `VEDA-P005-LGC-0032` | `MODERN_INTERPRETATION` | `ASTROFINANCE_UI` | `UI_EXPLANATION` | frontend/src/components/platform/AstroSignalCard.tsx |

Summary:

- Source-validated: `1`
- Legacy-unsourced: `18`
- Heuristic: `6`
- Modern-only / AstroFinance-hypothesis: `5`
