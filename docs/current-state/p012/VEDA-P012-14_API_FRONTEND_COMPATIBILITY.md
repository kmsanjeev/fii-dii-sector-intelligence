# API & Frontend Compatibility

Migrated route status:

| Surface | Runtime Surface | Status | Facade Routed |
| --- | --- | --- | --- |
| `generate_personal_kundli_tool` | `personal_kundli_chat_path` | `MIGRATED_WITH_FALLBACK` | `True` |
| `backend_human_kundli_route` | `rest_human_kundli_path` | `MIGRATED` | `True` |
| `backend_stock_kundli_route` | `stock_kundli_route` | `MIGRATED_ON_CACHE_MISS` | `True` |
| `backend_country_kundli_route` | `country_kundli_route` | `MIGRATED` | `True` |
| `personal_kundli_chat_path` | `personal_kundli_chat_path` | `LEGACY_ENGINE_PRESERVED` | `False` |
| `rest_human_kundli_path` | `rest_human_kundli_path` | `LEGACY_ENGINE_PRESERVED` | `False` |
| `stock_kundli_route` | `stock_kundli_route` | `LEGACY_ENGINE_PRESERVED` | `False` |
| `country_kundli_route` | `country_kundli_route` | `LEGACY_ENGINE_PRESERVED` | `False` |
