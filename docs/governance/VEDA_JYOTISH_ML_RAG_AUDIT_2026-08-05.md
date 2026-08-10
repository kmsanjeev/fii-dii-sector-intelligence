# Veda Jyotish ML-RAG Programme Audit

Date: 2026-08-05
Status: Audit only, no runtime or product change in this step
Scope: Compare the current Veda + ML + RAG implementation against the proposed Jyotish training and research programme

## Plain Conclusion

The current repo is **strongly prepared at the Veda platform level**, but it is
**not yet a true source-grounded Jyotish knowledge system**.

What already exists is a solid base:

- Veda chat orchestration
- reviewed memory
- attachment ingestion
- OCR and image fallback
- unified BM25 + FAISS retrieval
- research mode
- MIT-capability intake
- evidence and provenance UI

What is still missing is the full **Jyotish scholarly layer**:

- validated text register
- edition-level metadata
- Sanskrit text engineering
- passage IDs
- authority scoring
- commentary separation
- contradiction retention
- citation-first answering
- Jyotish-specific evaluation

So the fair answer is:

- **Veda is ready to host this programme**
- **ML and RAG foundations are usable**
- **the Jyotish corpus/governance layer is still largely unbuilt**

## Main Verdict

The right target is **not** "autonomous accurate prediction in all aspects."
That claim is too strong and not evidence-safe.

The right target is:

1. deterministic astronomical calculation
2. source-grounded textual retrieval
3. explicit separation of tradition, commentary, modern interpretation, and empirical evidence
4. controlled experimental testing for any predictive hypothesis

This matches the stronger parts of the proposed programme and avoids mixing:

- calculation with interpretation
- scripture with commentary
- tradition with modern market heuristics
- hardcoded prompt rules with approved source evidence

## What Is Already Done And Reusable

### 1. Veda foundation is already strong

The Veda platform already has the practical infrastructure needed for a serious
knowledge programme:

- attachment upload in chat
- PDF/image extraction
- OCR fallback
- reviewed save-to-knowledge flow
- approved durable memory
- research-mode governance
- MIT repo capability intake
- unified local retrieval
- evidence display in chat
- retrieval benchmark and shadow mode

Evidence:

- `docs/modules/AI_PLATFORM.md` records completed chat attachments, reviewed
  save-to-knowledge, MCP fallback, and hardening rollout
- `docs/governance/VEDA_UNIFIED_ML_RAG_PLAN_2026-08-04.md` records the shared
  knowledge contract, unified corpus, unified retriever, and benchmark/shadow
  rollout

### 2. Deterministic astrology calculation already exists

The repo already has a real astronomical calculation base:

- `AstroEngine` for sector transit signal
- `KundliEngine` for stock/personal/country charts
- Swiss Ephemeris + Lahiri ayanamsha
- Vimshottari dasha
- divisional-chart support

This is valuable because the proposed programme correctly says the LLM should
**not** calculate astronomy from memory.

### 3. Generic knowledge contract exists

The new unified contract already separates some evidence types:

- predictive ML signal
- platform snapshot
- approved memory
- attachment memory
- MIT capability note

This is a good foundation for the future Jyotish contract.

## What Is Only Partly Done

### 1. Retrieval is unified, but not yet Jyotish-scholarly

The repo now has a working unified retriever, but it is still generic.

It does **not yet** have:

- edition-aware retrieval
- verse-aware retrieval
- commentary-aware retrieval
- contradiction-aware grouping
- authority filtering
- cross-encoder reranking
- knowledge-graph retrieval

### 2. Astro logic exists, but is still partly heuristic

The current ASTRO module is explicitly documented as a **secondary,
experimental intelligence layer**.

The important implication is this:

- it is useful as an experimental feature
- it is not yet fit to be treated as the authoritative Jyotish core

### 3. Some source language exists, but not source-grounded records

The personal Kundli layer and interpretation layer mention classical sources,
but the actual implementation is still mostly hardcoded interpretation content.

That means:

- the system can speak fluently
- but it cannot yet prove which edition/chapter/verse the claim came from

## What Is Still Missing

### 1. Phase 0 governance is incomplete

Missing or not yet formalized:

- programme charter
- approved use-case register
- prohibited-use register
- knowledge-claim taxonomy
- authority dimensions
- empirical-vs-traditional separation policy
- Jyotish-specific risk register

### 2. Phase 1 canon and bibliography audit is mostly missing

The repo does not yet contain a validated source register for:

- text identity
- edition identity
- translator identity
- commentary identity
- manuscript/witness identity
- dating uncertainty
- licence status

This is one of the biggest gaps.

### 3. Phase 2-3 corpus engineering is mostly missing

The repo does not yet show a real Jyotish corpus pipeline for:

- scan preservation
- diplomatic text
- normalized text
- transliteration layers
- Sanskrit/Hindi/English alignment
- passage identity
- commentary linking
- TEI-style encoding

### 4. Phase 4 ontology is only partly present

A generic evidence contract exists, but the programme needs a stronger Jyotish
data model with fields such as:

- `text_id`
- `witness_id`
- `edition_id`
- `passage_id`
- `source_layer`
- `diplomatic_text`
- `normalised_text`
- `transliteration`
- `translation`
- `commentary`
- `rule_conditions`
- `claimed_outcome`
- `exceptions`
- `empirical_status`
- multidimensional `authority_profile`

### 5. Phase 5 annotation is missing

There is no expert annotation programme yet for:

- graha/rashi/bhava/nakshatra entities
- rule conditions
- claimed outcomes
- exceptions
- source-layer labels
- disagreement groups

### 6. Phase 6-7 Jyotish retrieval/RAG is only partly done

The repo has retrieval infrastructure, but the specific Jyotish RAG programme
is still missing:

- approved textual corpus
- lexical benchmark for Jyotish questions
- dense retrieval over approved Jyotish passages
- source-layer grouping
- citation-first answer format
- abstention when corpus support is absent
- conflict-aware response template

### 7. Phase 8 ML enrichment is missing in the right form

There is already platform ML in the repo, but it is **not** the same as the ML
needed for the proposed Jyotish corpus programme.

Missing corpus-focused ML tasks include:

- OCR confidence routing
- script/language detection
- Sanskrit segmentation
- morphological tagging
- entity recognition
- entity linking
- rule extraction
- contradiction detection
- passage similarity
- source-layer classification

### 8. Phase 9 evaluation is incomplete for Jyotish

The repo now has unified-retrieval benchmarks, but it does not yet have a real
Jyotish benchmark suite for:

- exact verse lookup
- source comparison
- commentary comparison
- chronology/provenance questions
- rule-condition extraction
- unanswerable-question abstention
- adversarial prompt-injection tests inside source documents

### 9. Phase 10 learner curriculum is missing

No structured learner curriculum, annotation training pack, or review workflow
exists yet for the Jyotish programme.

## Current Repo Risks That Must Be Corrected

### Risk 1. Prompt rules are currently stronger than source grounding

The ASTRO prompt still contains hardcoded rules such as:

- Mercury retrograde -> avoid new positions in some sectors
- Jupiter exaltation/own-sign -> bullish sector claims
- Rahu/Ketu eclipse -> directional market claims

These are currently closer to prompt policy than to citation-backed corpus retrieval.

Recommended correction:

- move these into either:
  - source-grounded rule records with citations
  - or an experimental hypothesis registry

### Risk 2. Hardcoded interpretation tables are not yet scholarly evidence

`kundli_interpreter.py` contains large hardcoded interpretation tables while
mentioning BPHS, Phaladeepika, Saravali, Uttara Kalamrita, and Lal Kitab.

That is acceptable as an interim product layer, but not as a final scholarly
knowledge layer.

Recommended correction:

- separate:
  - classical primary text
  - commentary
  - modern interpretation
  - folk/remedial systems like Lal Kitab

### Risk 3. The ASTRO core is documented as experimental for a reason

The current ASTRO docs openly say the module still lacks:

- full Bhava Phal
- Ashtakavarga
- Shadbala
- signal-efficacy validation

It is also not wired into the main trade conviction engine yet.

That means the current astrology layer should stay framed as:

- exploratory
- explainable
- non-authoritative for hard financial action

### Risk 4. "Accurate predictions in all aspects" is not a safe programme goal

From both governance and evidence viewpoints, that goal is too broad.

The programme should instead promise:

- accurate calculation
- accurate source retrieval
- accurate citation
- honest disagreement handling
- careful experimental testing of predictive claims

## Phase-By-Phase Audit Against The Proposed Programme

| Programme Phase | Current repo state | Audit result |
|---|---|---|
| Phase 0 - governance | generic Veda governance exists, Jyotish-specific governance missing | PARTIAL |
| Phase 1 - canon/bibliography | no validated source register yet | MISSING |
| Phase 2 - acquisition/rights | no Jyotish rights/edition manifest yet | MISSING |
| Phase 3 - Sanskrit text engineering | no real Sanskrit corpus pipeline yet | MISSING |
| Phase 4 - ontology/knowledge model | generic contract exists, Jyotish contract missing | PARTIAL |
| Phase 5 - expert annotation | not present | MISSING |
| Phase 6 - search baseline | generic BM25/FAISS exists, Jyotish lexical baseline missing | PARTIAL |
| Phase 7 - hybrid RAG | generic hybrid RAG exists, Jyotish citation-first RAG missing | PARTIAL |
| Phase 8 - ML enrichment | generic platform ML exists, corpus-focused Sanskrit/Jyotish ML missing | PARTIAL |
| Phase 9 - evaluation/red team | generic retrieval benchmark exists, Jyotish evaluation framework missing | PARTIAL |
| Phase 10 - learner curriculum | not present | MISSING |

## Clear Programme Recommendation

The platform should be organized under three synced layers:

1. **Veda**
   - the user-facing orchestration, explanation, safety, review, and citation layer
2. **RAG**
   - the source-grounded textual retrieval layer
3. **ML**
   - the corpus-improvement and experimental analysis layer

Important correction:

Veda is **not** just the frontend face of ML and RAG.
Veda is the **decision and governance layer above them**.

That means:

- Veda decides what kind of answer is allowed
- RAG decides what approved source evidence is retrieved
- ML improves the corpus/retrieval pipeline and runs controlled experiments

## Best One-Shot Fix Order

If this programme is to be implemented properly in one coordinated track, the
order should be:

1. programme charter and epistemic governance
2. master source register and authority rubric
3. corpus acquisition + rights tracking
4. Sanskrit normalization + transliteration + passage ID standard
5. Jyotish ontology + rule schema + conflict model
6. expert annotation pilot
7. lexical retrieval baseline
8. hybrid citation-first RAG
9. corpus-focused ML enrichment
10. evaluation + red team + production gate

## Immediate Deliverables I Recommend Next

The next deliverables should be:

1. `JYOTISH-PROG-000001` -- Programme Charter
2. `JYOTISH-GOV-000001` -- Epistemic and Ethical Governance Standard
3. `JYOTISH-SRC-000001` -- Master Source Register
4. `JYOTISH-SRC-000002` -- Source Authority and Acceptance Rubric
5. `JYOTISH-CORP-000001` -- Corpus Architecture Specification

Only after these are frozen should the repo start large-scale Jyotish corpus
ingestion or any future model-tuning discussion.

## Evidence From The Current Repo

- `docs/modules/AI_PLATFORM.md`
  - Veda attachments, review-before-save, MCP fallback, rollout hardening
- `docs/governance/VEDA_UNIFIED_ML_RAG_PLAN_2026-08-04.md`
  - unified knowledge contract, unified corpus, unified retrieval, benchmark/shadow mode
- `docs/modules/ASTRO.md`
  - ASTRO is documented as experimental and incomplete for authoritative use
- `docs/decisions/ADR-022-AstroFinance-Vedic-Intelligence-Layer.md`
  - astronomy correctness fixes are real, but the module is still methodologically incomplete
- `engines/ai/knowledge/contracts.py`
  - generic evidence contract exists, but edition/passage/source-layer fields are absent
- `engines/ai/knowledge/unified_retriever.py`
  - generic hybrid retrieval exists, but no Jyotish-specific authority/citation logic
- `engines/ai/chatbot/intent_router.py`
  - ASTRO prompt still contains hardcoded source-like rules
- `engines/ai/chatbot/tools/kundli_interpreter.py`
  - large interpretation tables exist, but not as edition-cited corpus records

## External Research Used To Strengthen This Audit

These sources support the programme design direction:

- RAG should combine model generation with external non-parametric memory:
  https://arxiv.org/abs/2005.11401
- Dense retrieval is useful, but should be layered on top of a baseline:
  https://arxiv.org/abs/2004.04906
- BM25 remains a strong baseline for retrieval benchmarking:
  https://arxiv.org/abs/2104.08663
- TEI gives the right structure for text metadata and editions:
  https://guidelines.tei-c.de/en/html/index.html
- IIIF is relevant for manuscript/scan image interoperability:
  https://iiif.io/
- GRETIL is a practical source model for machine-readable Sanskrit texts:
  https://gretil.sub.uni-goettingen.de/gretil.html
- Pingree/CESS-style cataloguing is relevant for manuscript and text identity:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1172313/
- Sanskrit Heritage is relevant for segmentation and morphology tooling:
  https://sanskrit.inria.fr/
- IndicTrans2 is useful for multilingual alignment support, with expert review:
  https://arxiv.org/abs/2305.16307
- SanskritShala is relevant for Sanskrit NLP tooling:
  https://aclanthology.org/2023.acl-demo.10/
- RAGAS can help evaluate retrieval/generation, but should not replace expert review:
  https://arxiv.org/abs/2309.15217
- NIST AI RMF GenAI Profile is a useful governance reference:
  https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
- The classic double-blind astrology paper is a useful reminder to keep empirical claims separate from traditional claims:
  https://www.nature.com/articles/318419a0
