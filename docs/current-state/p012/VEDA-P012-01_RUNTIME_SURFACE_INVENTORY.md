# Runtime Surface Inventory

| Surface | Classification | Consumer | Timezone Handling | Interpretation Coupling |
| --- | --- | --- | --- | --- |
| `personal_kundli_chat_path` | `PRIMARY_RUNTIME` | `chatbot personal-kundli calculation core` | `USER_PROVIDED_OFFSET` | `HIGH` |
| `generate_personal_kundli_tool` | `ADAPTER_CANDIDATE` | `chat tool registry` | `USER_PROVIDED_OFFSET` | `HIGH` |
| `rest_human_kundli_path` | `LEGACY_RUNTIME` | `REST human backend route` | `USER_PROVIDED_OFFSET` | `MEDIUM` |
| `backend_human_kundli_route` | `ADAPTER_CANDIDATE` | `HTTP API` | `USER_PROVIDED_OFFSET` | `HIGH` |
| `stock_kundli_route` | `SPECIALIZED_RUNTIME` | `stock route, AstroFinance, bulk intelligence` | `HARDCODED_OFFSET` | `HIGH` |
| `backend_stock_kundli_route` | `ADAPTER_CANDIDATE` | `HTTP API / stock detail views` | `HARDCODED_OFFSET` | `HIGH` |
| `country_kundli_route` | `SPECIALIZED_RUNTIME` | `country inception route` | `HARDCODED_OFFSET` | `HIGH` |
| `backend_country_kundli_route` | `ADAPTER_CANDIDATE` | `HTTP API` | `HARDCODED_OFFSET` | `HIGH` |
