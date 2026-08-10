# VEDA-P000-11 Future Roadmap

## Recommended programme structure

The roadmap below is derived from repository evidence, not legacy plan order.

### Phase roadmap

| PHASE_ID | TITLE | OBJECTIVE | RATIONALE | DEPENDENCIES | CURRENT_CAPABILITY_REUSED | RESEARCH_REQUIRED | ENGINEERING_REQUIRED | FILES/MODULES_LIKELY_AFFECTED | RISK_LEVEL | TEST_REQUIREMENTS | ACCEPTANCE_CRITERIA | DELIVERABLES |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VEDA-P001 | Baseline and Runtime Governance | freeze the current behaviour and secure the operating envelope | existing app is live but not sufficiently protected | VEDA-P000 | current tests, cached kundli corpus, API routes, docs/current-state | NO_NEW_RESEARCH | regression fixtures, secret governance, auth policy, route snapshots | `tests/`, `backend/auth/`, `backend/main.py`, kundli route tests, CI docs | HIGH | golden fixtures, API contract tests, runtime smoke checks | risky modules have baseline tests and known-good snapshots | baseline pack, governance ADRs, regression suite |
| VEDA-P002 | Research Governance and Source Registry | create the authoritative astrology source/provenance layer | current rules are mostly unsourced | VEDA-P001 | docs/governance structure, reviewed-memory concepts | CLASSICAL_RESEARCH_REQUIRED | source schema, authority rubric, approval workflow | `docs/governance/`, new source registry files/schemas | MEDIUM | schema tests, sample source review cases | at least one approved source path exists from text to metadata | source registry, authority rubric, approval checklist |
| VEDA-P003 | Knowledge Ontology and Rule Schema | define machine-readable astrology knowledge structures | current logic is hardcoded and duplicated | VEDA-P002 | existing kundli dictionaries and rule functions | CROSS_SOURCE_RESEARCH_REQUIRED | ontology, rule schema, mapping strategy | new `docs/modules/` + rule-schema locations, astrology engines | HIGH | schema validation, backward-compat mapping tests | approved schema can represent existing rules without runtime change | ontology spec, rule schema, migration plan |
| VEDA-P004 | Existing Calculation Foundation Validation | validate current ephemeris, Lagna, house, Graha, and Varga calculations | strongest current asset must be trusted before expansion | VEDA-P001, VEDA-P003 | `kundli_engine.py`, `kundli_calculator.py`, Swiss Ephemeris setup | VALIDATION_RESEARCH | fixture library, differential tests, timezone audit | `engines/intelligence/kundli_engine.py`, `engines/ai/chatbot/tools/kundli_calculator.py`, tests | HIGH | deterministic fixture tests across representative charts | approved fixtures match expected outputs with documented tolerances | validated fixture corpus, calculation audit report |
| VEDA-P005 | Existing Interpretation Engine Validation | validate current domain readings, Yogas, Doshas, and Dasha narratives | current outputs work but are unsourced and split | VEDA-P002, VEDA-P004 | personal-kundli report path, stock finance narrative path | CROSS_SOURCE_RESEARCH_REQUIRED | traceability from output to rules, interpretive fixture tests | personal interpreter files, `kundli_interpretator.py`, tests | HIGH | rule-trace tests, domain fixture tests | selected outputs can be traced to approved rule statements | interpretation trace matrix, validated domains |
| VEDA-P006 | Research Ingestion Framework | formalize how approved source material becomes durable knowledge | current retrieval substrate exists but is not astrology-ready | VEDA-P002, VEDA-P003 | reviewed memory, retrieval builders, approved docs corpus | CLASSICAL_RESEARCH_REQUIRED | ingestion pipeline, metadata schema, indexing policy | `engines/ai/knowledge/*`, review endpoints, data corpus locations | MEDIUM | ingestion tests, provenance checks, retrieval smoke tests | approved source docs are searchable with citation metadata | ingestion pipeline, searchable source corpus |
| VEDA-P007 | Unified Astrology Runtime Boundary | reduce risk from split stock/personal astrology paths without rewrite-first behaviour | current duplication is the largest structural astrology risk | VEDA-P004, VEDA-P005 | both existing kundli engines, routers, tool wrappers | NO_NEW_RESEARCH | boundary layer, shared contracts, adapter tests | kundli routers/tools/interfaces | HIGH | contract tests proving unchanged outputs for both surfaces | both surfaces continue to work through a documented boundary | boundary spec, adapter layer, regression evidence |
| VEDA-P008 | Progressive Jyotisha Capability Expansion | add high-priority missing classical capabilities in governed order | missing breadth should follow validated foundation | VEDA-P002 through VEDA-P007 | validated core, source registry, rule schema | CLASSICAL_RESEARCH_REQUIRED | targeted modules for strengths, Vargas, Dashas, domains | astrology engines, schema, tests, docs | HIGH | per-module fixtures and source-validation tests | each added capability is sourced, tested, and regression-safe | new validated modules, updated capability matrix |
| VEDA-P009 | Astrology Retrieval and Citation Layer | introduce source-grounded astrology retrieval after knowledge governance exists | current RAG substrate is reusable but not yet astrology-safe | VEDA-P006, VEDA-P008 | BM25/FAISS/unified retriever, review workflow | CROSS_SOURCE_RESEARCH_REQUIRED | citation-aware retrieval, answer constraints, provenance UI | `engines/ai/knowledge/*`, chat engine, frontend chat | MEDIUM | retrieval precision tests, citation regression tests | answers can cite approved source passages | astrology RAG MVP with citations |
| VEDA-P010 | Validation Datasets and Controlled ML Exploration | evaluate whether ML has a justified role after rule and source maturity exist | astrology ML is absent and should not precede governance | VEDA-P004, VEDA-P005, VEDA-P008 | existing ML stack, experiment patterns | EMPIRICAL_RESEARCH_REQUIRED | dataset pipeline, evaluation framework, risk review | `engines/ml/*`, new datasets/evals, docs | MEDIUM | offline eval tests, dataset governance checks | explicit evidence that ML adds value without weakening source control | dataset spec, benchmark suite, go/no-go decision |

## Module-level roadmap

### VEDA-P001 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P001-M001 | Secrets and auth governance baseline | P0 | NO_NEW_RESEARCH | rotate/remove checked-in secrets, decide auth policy, preserve runtime contracts |
| VEDA-P001-M002 | Stock kundli golden fixtures | P1 | NO_NEW_RESEARCH | snapshot representative stock and country outputs |
| VEDA-P001-M003 | Personal-kundli golden fixtures | P1 | NO_NEW_RESEARCH | snapshot formatted report and key computed fields |
| VEDA-P001-M004 | API and frontend contract baseline | P1 | NO_NEW_RESEARCH | route snapshots for report, chat, auth, data control |

### VEDA-P002 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P002-M001 | Astrology source registry schema | P1 | CLASSICAL_RESEARCH_REQUIRED | author/work/chapter/verse/translation/commentary fields |
| VEDA-P002-M002 | Authority and contradiction rubric | P1 | CROSS_SOURCE_RESEARCH_REQUIRED | how competing sources are ranked and recorded |
| VEDA-P002-M003 | Approval workflow for research artifacts | P2 | VALIDATION_RESEARCH | align with reviewed-memory concepts already in repo |

### VEDA-P003 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P003-M001 | Graha/Bhava/Rashi ontology | P1 | CLASSICAL_RESEARCH_REQUIRED | canonical machine-readable concepts |
| VEDA-P003-M002 | Yoga/Dosha rule schema | P1 | CLASSICAL_RESEARCH_REQUIRED | conditions, exceptions, strength, timing hooks |
| VEDA-P003-M003 | Dasha/Varga schema | P1 | CLASSICAL_RESEARCH_REQUIRED | calculation and interpretation metadata shapes |

### VEDA-P004 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P004-M001 | Ephemeris validation | P1 | VALIDATION_RESEARCH | verify Swiss Ephemeris outputs and file assumptions |
| VEDA-P004-M002 | Ayanamsha and node-method validation | P1 | VALIDATION_RESEARCH | document Lahiri and Rahu/Ketu method explicitly |
| VEDA-P004-M003 | Lagna and house validation | P1 | VALIDATION_RESEARCH | test against trusted reference charts |
| VEDA-P004-M004 | Varga calculation validation | P1 | VALIDATION_RESEARCH | verify each currently implemented division |
| VEDA-P004-M005 | Timezone and DST audit | P0 | VALIDATION_RESEARCH | especially fixed-offset stock-path handling |

### VEDA-P005 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P005-M001 | Finance interpretation validation | P1 | CROSS_SOURCE_RESEARCH_REQUIRED | stock astro score, houses, Yogas, transit heuristics |
| VEDA-P005-M002 | Personal life-domain interpretation validation | P1 | CROSS_SOURCE_RESEARCH_REQUIRED | marriage, career, children, health, longevity |
| VEDA-P005-M003 | Yoga and dosha traceability | P1 | CLASSICAL_RESEARCH_REQUIRED | document exact conditions and approved sources |
| VEDA-P005-M004 | Remedy policy validation | P2 | CLASSICAL_RESEARCH_REQUIRED | source and safety checks before extension |

### VEDA-P006 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P006-M001 | Source document ingestion contracts | P1 | CLASSICAL_RESEARCH_REQUIRED | parse and store approved sources with metadata |
| VEDA-P006-M002 | Citation-ready chunking and IDs | P1 | CROSS_SOURCE_RESEARCH_REQUIRED | passage IDs before retrieval expansion |
| VEDA-P006-M003 | Provenance-preserving indexing | P2 | VALIDATION_RESEARCH | BM25/FAISS metadata discipline |

### VEDA-P007 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P007-M001 | Shared kundli contract | P1 | NO_NEW_RESEARCH | unify interfaces before unifying implementations |
| VEDA-P007-M002 | REST and chat adapter validation | P1 | NO_NEW_RESEARCH | prove both surfaces preserve output expectations |
| VEDA-P007-M003 | Divergence audit harness | P1 | NO_NEW_RESEARCH | detect silent differences between stock and personal paths |

### VEDA-P008 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P008-M001 | planetary strength systems | P2 | CLASSICAL_RESEARCH_REQUIRED | Shadbala family after schema and validation exist |
| VEDA-P008-M002 | Varga expansion and interpretation | P2 | CLASSICAL_RESEARCH_REQUIRED | D24, D27, D40, D45 and validated usage |
| VEDA-P008-M003 | Dasha family expansion | P2 | CLASSICAL_RESEARCH_REQUIRED | Yogini, Ashtottari, others only after source approval |
| VEDA-P008-M004 | domain framework expansion | P2 | CROSS_SOURCE_RESEARCH_REQUIRED | marriage, finance, career, health, children |
| VEDA-P008-M005 | advanced schools | P3 | CLASSICAL_RESEARCH_REQUIRED | Jaimini, Ashtakavarga, Muhurta, Ayurdaya |

### VEDA-P009 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P009-M001 | astrology retrieval MVP | P3 | CROSS_SOURCE_RESEARCH_REQUIRED | citation-first retrieval only |
| VEDA-P009-M002 | contradiction-aware citation UI | P3 | CROSS_SOURCE_RESEARCH_REQUIRED | show source basis and conflicts |
| VEDA-P009-M003 | answer-grounding controls | P3 | VALIDATION_RESEARCH | prevent unsourced synthesis |

### VEDA-P010 modules

| MODULE_ID | TITLE | PRIORITY | RESEARCH_DEPENDENCY | Notes |
| --- | --- | --- | --- | --- |
| VEDA-P010-M001 | astrology dataset policy | P4 | EMPIRICAL_RESEARCH_REQUIRED | define permitted outcomes and labels |
| VEDA-P010-M002 | feature-generation experiment | P4 | EMPIRICAL_RESEARCH_REQUIRED | only after validated rule ontology exists |
| VEDA-P010-M003 | benchmark and red-team evaluation | P4 | EMPIRICAL_RESEARCH_REQUIRED | go/no-go gate for any ML claims |

## Roadmap priority model applied

- `P0` stability/security blocker
- `P1` foundation
- `P2` major functional capability
- `P3` advanced intelligence
- `P4` experimental

Resulting sequencing:

1. protect and validate the existing app
2. govern sources and machine-readable knowledge
3. validate current calculation and interpretation
4. reduce structural duplication risk
5. expand classical capability in controlled increments
6. only then add astrology retrieval or ML

## Roadmap conclusion

The evidence does not justify a rewrite programme.

It does justify a multi-phase preservation-and-validation programme that reuses:

- the live backend/frontend platform
- the retrieval substrate
- the deterministic ephemeris-backed calculation core
- the reviewed-memory workflow

Future work should be authorized phase by phase against the gates defined in the research-readiness audit.
