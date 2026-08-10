# VEDA-P000-08 Gap Analysis

## Current-state capability matrix

| ID | Capability | Exists | Runtime Verified | Completeness | Source Evidence | Tests | Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-001 | React + FastAPI platform shell | yes | yes | 4/5 | `frontend/src/main.tsx`, `backend/main.py`, live `/` + `/health` | frontend tests, runtime probes | KEEP |
| CAP-002 | File-backed intelligence pipeline | yes | yes | 4/5 | `data/intelligence/*`, `backend/services/data_loader.py`, scheduler | indirect | KEEP |
| CAP-003 | Chat + reviewed knowledge workflow | yes | yes | 4/5 | `engines/ai/chatbot/*`, `data/veda/knowledge_reviews/*` | yes | KEEP |
| CAP-004 | Unified local retrieval (BM25 + FAISS) | yes | yes | 4/5 | `engines/ai/knowledge/*`, live capability flags, live retriever call | yes | VALIDATE |
| CAP-005 | External web research | yes | yes | 3/5 | `/api/chat/capabilities` reported provider ready | yes | VALIDATE |
| CAP-006 | Stock kundli engine | yes | yes | 3/5 | `engines/intelligence/kundli_engine.py`, live stock endpoint, 2053 cached files | no dedicated suite | VALIDATE |
| CAP-007 | Personal kundli chat engine | yes | yes | 3/5 | `kundli_calculator.py`, `kundli_interpreter.py`, `data_tools.py`, live tool call | no dedicated suite | VALIDATE |
| CAP-008 | Country kundli engine | yes | yes | 2/5 | `COUNTRY_BIRTH_DATA`, live `/api/kundli/country/India` | no dedicated suite | DEFER |
| CAP-009 | Gann analysis | yes | yes | 2/5 | `engines/intelligence/gann_engine.py`, mounted routes | no dedicated suite | VALIDATE |
| CAP-010 | AstroFinance sector astrology | yes | yes | 3/5 | `engines/intelligence/astro_engine.py`, frontend card wiring, output files | no dedicated suite | VALIDATE |
| CAP-011 | Astrology source provenance registry | no | no | 0/5 | no authoritative registry found in code or data | none | BUILD |
| CAP-012 | Structured astrology rule schema | partial | no | 1/5 | hardcoded dicts/functions only | none | RESEARCH_FIRST |
| CAP-013 | Astrology RAG corpus | no | no | 0/5 | no live sourced Jyotisha corpus found in retriever indexes | none | RESEARCH_FIRST |
| CAP-014 | Astrology ML | no | no | 0/5 | no astrology dataset/model/training path found | none | DEFER |
| CAP-015 | Auth / admin security envelope | yes | yes | 2/5 | `backend/auth/*`, live `/api/auth/config` shows auth off | indirect | VALIDATE |
| CAP-016 | Regression safety net | yes | partial | 3/5 | 339 Python tests, 16 frontend tests, but 8 chat failures and sparse astrology tests | yes | VALIDATE |

## Astrology knowledge maturity matrix

Score scale:

- `0` absent
- `1` experimental
- `2` basic
- `3` functional
- `4` mature
- `5` research-grade

| Capability | Calculation | Rule | Source | Interpretation | Testing | RAG | ML |
| --- | --- | --- | --- | --- | --- | --- | --- |
| astronomical foundations | 4 | 2 | 1 | 1 | 1 | 0 | 0 |
| Grahas | 4 | 2 | 1 | 2 | 1 | 0 | 0 |
| Rashi dignity/lordship | 3 | 3 | 1 | 2 | 0 | 0 | 0 |
| Bhavas | 3 | 2 | 1 | 2 | 0 | 0 | 0 |
| aspects | 2 | 2 | 1 | 1 | 0 | 0 | 0 |
| planetary strength systems | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| Nakshatras | 3 | 2 | 1 | 2 | 0 | 0 | 0 |
| Vargas | 2 | 1 | 0 | 1 | 0 | 0 | 0 |
| Dashas | 3 | 2 | 1 | 2 | 0 | 0 | 0 |
| Yogas / Doshas | 2 | 2 | 0 | 2 | 0 | 0 | 0 |
| transits / gochara | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| Gann / AstroFinance | 2 | 2 | 0 | 2 | 0 | 0 | 0 |

Important interpretations:

- astronomical calculation is the strongest astrology layer because Swiss Ephemeris, Lahiri sidereal mode, Lagna, and deterministic chart generation are executed code paths
- rule/source maturity is weak almost everywhere because classical provenance is not stored as verse-linked, authority-tracked knowledge
- testing maturity for astrology is materially lower than general platform maturity
- astrology RAG and astrology ML are effectively absent in operational form

## Research gap matrix

| Domain | Existing Implementation | Existing Source Quality | Research Gap | Engineering Gap | Priority |
| --- | --- | --- | --- | --- | --- |
| astronomical foundations | Swiss Ephemeris, Lahiri, Lagna, whole-sign downstream house assignment | UNSOURCED in repo terms | validation research against trusted fixtures | golden fixtures, contract tests, timezone audit | P1 |
| Grahas | Sun through Saturn, Rahu/Ketu, Uranus/Neptune in active code | UNSOURCED | research policy on optional outer planets and node method | unify graha usage across paths | P1 |
| Bhavas | house occupancy and limited financial-house summaries | UNSOURCED | house semantics and functional lordship depth | expand rule model beyond summaries | P1 |
| aspects | graha drishti in personal path, mixed special aspects in stock path, angular transit aspects | UNSOURCED | reconcile classical vs finance-oriented aspect logic | isolate and test each algorithm | P1 |
| planetary strengths | dignity tables only; no Shadbala family | UNSOURCED | major classical research required | new rule/data model needed | P2 |
| Vargas | partial set in REST; D9/D10 only in personal path output | UNSOURCED | source-backed varga formulas and usage priorities | missing charts, missing interpretation, missing tests | P1 |
| Yogas | limited hard-coded set | UNSOURCED | source-backed conditions, exceptions, strength, timing | rule registry + detection engine expansion | P2 |
| Doshas | some personal-path doshas only | UNSOURCED | source-backed criteria and caveats | unify and test dosha detection | P2 |
| Dashas | Vimshottari only; some interpretation | UNSOURCED | source-backed interpretation/timing methodology | broaden tests and separate calc from narrative | P1 |
| transits | simple current-transit comparison and Sade Sati logic | UNSOURCED | classical gochara framework research | richer timing pipeline needed | P2 |
| Nakshatras | names, padas, dasha lords, some narrative use | UNSOURCED | deity/gana/yoni/nadi and interpretation sources | structured metadata store needed | P2 |
| marriage | personal chat narrative only | UNSOURCED | source-backed marriage decision framework | reusable domain rule engine absent | P2 |
| finance | stock AstroFinance + financial houses + astro score | UNSOURCED | source-backed financial reading framework | current logic is heuristic and split | P2 |
| career | personal chat narrative only | UNSOURCED | source-backed career framework | no governed domain schema | P2 |
| children | personal chat narrative only | UNSOURCED | source-backed fertility/children framework | no governed domain schema | P2 |
| health | personal chat narrative only | UNSOURCED | source-backed health boundaries and safety policy | no governed domain schema | P2 |
| Ayurdaya | not verified | UNKNOWN | major classical research required | absent implementation | P3 |
| Muhurta | not verified | UNKNOWN | major classical research required | absent implementation | P3 |
| remedies | Lal Kitab remedies present in personal path | UNSOURCED | source and safety review required | provenance and policy missing | P3 |
| Jaimini | not verified | UNKNOWN | major classical research required | absent implementation | P3 |
| Ashtakavarga | not verified | UNKNOWN | major classical research required | absent implementation | P3 |

## Documentation audit

| Documentation Artifact | Classification | Evidence |
| --- | --- | --- |
| `docs/PROJECT_MASTER_STATE.md` | PARTIALLY_CURRENT | correctly describes the platform as a capital-flow system, but some counts and status claims are already stale relative to live runtime and current OpenAPI |
| `docs/phase_list.csv` | CONTRADICTED_BY_CODE | marks phases 17-25 as not started, while live routes and code show portfolio, backtest, broker, research, execution, and auth are implemented |
| `docs/data_flow_diagram.md` | PARTIALLY_CURRENT | architecture direction matches the platform, but endpoint counts and several implementation details are dated |
| prior roadmap / Jyotish programme material | PLANNING_ONLY | useful for intent, but not acceptable as proof of implementation without code/runtime confirmation |
| `docs/current-state/*` | CURRENT | created from live runtime and repository evidence during VEDA-P000 |

## Dead / disconnected / duplicate code audit

| Surface | Classification | Confidence | Evidence |
| --- | --- | --- | --- |
| `frontend` participant route | DISCONNECTED | high | `App.tsx` redirects `/participant` to `/` |
| `main.py` root vs `backend/main.py` | DUPLICATED | high | separate batch/runtime roles, both active in different contexts |
| `kundli_engine.py` vs `kundli_calculator.py` | DUPLICATED | high | overlapping astrology logic with different feature depth |
| retired ASTRO FAISS artifacts | DEPRECATED | high | `faiss_ASTRO.index.retired` under retrieval artifacts |
| astrology RAG expectations in planning docs | PLANNED_ONLY | medium | live retriever is market/platform-focused, not source-grounded Jyotisha |

## Technical debt classification

### Category A - Dangerous

- checked-in secrets in `.env`
- auth disabled by default while high-power operational endpoints are mounted
- default bootstrap admin password fallback
- plaintext broker credential storage

### Category B - Structural

- duplicated astrology engines with diverging behaviour
- backend startup has many side effects: DB init, scheduler, data loading, voice validation
- file-first persistence is practical but lacks central governance boundaries

### Category C - Functional

- incomplete classical breadth: no Shadbala family, Ashtakavarga, Jaimini, Muhurta, compatibility suite, or multiple dasha families
- personal and REST kundli features are not aligned
- country charts rely on hardcoded national birth data

### Category D - Knowledge

- astrology rules are mostly unsourced in machine-readable form
- no authority-ranked source registry
- no contradiction handling for classical interpretations

### Category E - Validation

- Python suite not fully green
- no strong astrology fixture suite
- limited end-to-end verification of kundli outputs

### Category F - Enhancement

- bundle-size warnings
- voice configuration comment drift
- route/document count drift in older docs

## Gap-analysis conclusion

VEDA already has a working platform and a working astrology subset, but it is not yet a governed, source-grounded Jyotisha platform.

The main gap is not "missing app scaffolding." The main gap is the layer between deterministic computation and trustworthy knowledge:

- provenance
- validation
- rule governance
- regression protection

That is why the next programme must begin with validation and governance, not feature expansion.
