# VEDA-P000-03 Feature Inventory

Status vocabulary used:

- `OPERATIONAL`
- `IMPLEMENTED`
- `PARTIALLY_IMPLEMENTED`
- `PLACEHOLDER`
- `DISCONNECTED`
- `BROKEN`
- `DEPRECATED`
- `DUPLICATED`
- `PLANNED_ONLY`
- `UNKNOWN`

## User-facing feature catalogue

| Feature | Status | Evidence | Runtime path | Tests | Notes |
| --- | --- | --- | --- | --- | --- |
| dashboard / market overview | OPERATIONAL | live frontend, `/api/market/*`, `/api/participant/*` | `frontend/src/pages/Dashboard.tsx` | indirect | core market surface |
| sectors explorer | OPERATIONAL | `/api/sectors`, `/api/sectors/{sector}` | `frontend/src/pages/SectorsPage.tsx` | indirect | sector rotation UI |
| stock detail | OPERATIONAL | `/api/stocks/{symbol}` | `frontend/src/pages/StockDetailPage.tsx` | indirect | broad stock intelligence |
| stock report page | OPERATIONAL | `/report/:symbol`, `/api/stocks/{symbol}/kundli`, `/api/charts/ohlcv` | `frontend/src/pages/ReportPage.tsx` | indirect | integrates astrology and market data |
| stock kundli card | OPERATIONAL | connected to live kundli endpoint | `frontend/src/components/platform/KundliCard.tsx` | no dedicated test found | stock/corporate astrology surface |
| AstroFinance sector signal card | OPERATIONAL | wired into stock UI via astro signal fields | `frontend/src/components/platform/AstroSignalCard.tsx` | no dedicated test found | sector/day-based astrology |
| chat page | OPERATIONAL | `/api/chat`, `/api/chat/capabilities`, session endpoints | `frontend/src/pages/ChatPage.tsx` | yes | VEDA chat/research surface |
| reviewed-memory workflow | OPERATIONAL | knowledge draft/approve endpoints + tests | chat + review panels | yes | saves durable knowledge |
| repo capability review workflow | OPERATIONAL | capability draft/approve endpoints + tests | chat review UI | yes | MIT repo intake |
| attachment upload in chat | OPERATIONAL | `/api/chat/attachments`, stored files seen under `data/veda/uploads` | chat + widget | yes | PDF/image/text |
| personal kundli via chat | OPERATIONAL | KUNDLI intent + tool + direct bypass | chat only | no dedicated end-to-end test found | no dedicated standalone UI form |
| human kundli REST endpoint | OPERATIONAL | live `POST /api/kundli/human` returned chart | REST only | no dedicated test found | lower-featured than chat report path |
| country kundli | OPERATIONAL | live `GET /api/kundli/country/India` | REST | no dedicated test found | hardcoded country charts |
| Gann analysis | OPERATIONAL | live `/api/kundli/gann/{symbol}` mounted | report/kundli surfaces | no dedicated test found | finance-oriented |
| themes page | OPERATIONAL | `/api/themes` | `frontend/src/pages/ThemesPage.tsx` | indirect | thematic intelligence |
| research screen | OPERATIONAL | `/api/research/*` | `frontend/src/pages/ResearchPage.tsx` | indirect | screener/notes |
| portfolio | OPERATIONAL | `/api/portfolio*` | `frontend/src/pages/PortfolioPage.tsx` | indirect | file-backed portfolio |
| backtest | OPERATIONAL | `/api/backtest/*` | `frontend/src/pages/BacktestPage.tsx` | indirect | backtest API/UI present |
| broker integration | OPERATIONAL | `/api/broker/*` | `frontend/src/pages/BrokerPage.tsx` | indirect | Dhan + CSV import |
| execution/trading panel | OPERATIONAL | `/api/execution/*` | `frontend/src/pages/ExecutionPage.tsx` | indirect | paper/live config surface |
| data-control/admin | OPERATIONAL | `/api/data/*`, `/api/auth/*`, `/admin` | `DataControlPage.tsx`, `AdminPage.tsx` | indirect | high-risk if auth off |
| login/admin auth UI | OPERATIONAL | `/login`, `/admin`, auth endpoints live | `LoginPage.tsx`, `AdminPage.tsx` | indirect | auth currently disabled in live config |
| voice TTS + analytics | OPERATIONAL | `/api/voice/*` | widget/chat integration | yes | conversation logs persisted |
| participant page route | DISCONNECTED | route redirects to `/` | `App.tsx` | n/a | explicit redirect, not standalone page |
| dedicated personal kundli screen | PLACEHOLDER | no standalone route/form found | none | n/a | personal kundli is chat-led instead |

## Internal platform capability catalogue

| Capability | Status | Evidence | Runtime path | Tests | Notes |
| --- | --- | --- | --- | --- | --- |
| dataset preload into memory | OPERATIONAL | `data_loader.startup()`, live `/health` | startup | indirect | 43 configured datasets |
| scheduled daily refresh | OPERATIONAL | scheduler code + startup hook | APScheduler | no direct test found | weekday 18:00 IST |
| scheduled daily market brief | OPERATIONAL | scheduler code + DMB engine hook | APScheduler | no direct test found | weekday 08:45 IST |
| subprocess pipeline control | OPERATIONAL | `/api/pipeline/*`, `/api/data/run/*` | routers + `daily_refresh.py` | indirect | mutates data |
| hybrid retrieval | OPERATIONAL | BM25/FAISS/unified retriever + live capabilities | chat engine | yes | local retrieval works |
| external web research | OPERATIONAL | live capabilities show DDGS ready | chat engine | yes | outside lookup optional |
| reviewed knowledge persistence | OPERATIONAL | `data/veda/knowledge_reviews`, approval endpoints | chat | yes | durable memory layer |
| repo capability persistence | OPERATIONAL | `data/veda/capability_reviews`, approval endpoints | chat | yes | capability memory |
| market ML scoring | OPERATIONAL | model files + `ml_scorer.py` + loaded score CSVs | daily pipeline + API | indirect | not astrology ML |
| stock kundli bulk generation | OPERATIONAL | live `2053` cached files | `KundliEngine.run()` | no dedicated test found | core astrology asset |
| Gann bulk generation | OPERATIONAL | `gann_signals.csv`, mounted routes | `GannEngine.run()` | no dedicated test found | finance-specific |
| AstroFinance sector engine | OPERATIONAL | `astro_signals.csv`, `market_astro_context.json` | `astro_engine.py` | no dedicated test found | separate from kundli |
| optional LLM narratives | IMPLEMENTED | multiple prompt surfaces found | LLM client | indirect | not always enabled |
| classical-source provenance registry | PLANNED_ONLY | no authoritative store found | none | none | key gap |
| structured astrology rule registry | PARTIALLY_IMPLEMENTED | hardcoded dicts and functions exist | kundli tools | none | not governed/source-linked |
| astrology RAG corpus | PLANNED_ONLY | no proven structured Jyotisha corpus in retrieval indexes; only market/platform retrieval is operational | none | none | retired ASTRO artifacts exist but no live sourced Jyotisha corpus was verified |
| astrology ML | PLANNED_ONLY | no astrology-labelled model/training path found | none | none | market ML only |

## Duplicate / disconnected / legacy surfaces

| Surface | Status | Reason |
| --- | --- | --- |
| `main.py` root vs `backend/main.py` | DUPLICATED | separate batch-orchestration vs live API entry |
| `kundli_engine.py` vs `kundli_calculator.py` | DUPLICATED | overlapping astrology logic with different coverage |
| retired ASTRO FAISS artifacts | DEPRECATED | `faiss_ASTRO.index.retired` observed in `data/intelligence/rag_knowledge/faiss` |
| participant route | DISCONNECTED | explicit frontend redirect to root |

## Feature-inventory conclusions

- the application is already broad and operational
- astrology is present, but split between finance-oriented and personal-reading-oriented implementations
- the strongest evidence-backed features are market intelligence, chat/retrieval, and stock-level astrology
- the weakest evidence-backed areas are classical Jyotisha breadth, source governance, and astrology-specific testing
