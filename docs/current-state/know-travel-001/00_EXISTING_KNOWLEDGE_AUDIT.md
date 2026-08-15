# Existing Knowledge Audit

Audit order: repository knowledge first, external research second. Scope is documentation/governance only; no provider calls, production-code changes, or RAG rebuild were made.

| Existing source | Authority | Passage available | Supported claim | Current use | Gap/conflict |
|---|---|---|---|---|---|
| `engines/ai/knowledge/travel_relocation_governance.py` | Platform registry | Yes, code | P030 is `RESEARCH_CANDIDATE`; D4 calculation validated, interpretation gated; D9/D10/D12 not validated | Runtime trust and blocked outputs | No classical rule is activated |
| `engines/intelligence/travel_relocation_synthesis_engine.py` | Platform evidence | Yes, code/tests | Separate travel, relocation, foreign travel/residence/settlement, return, timing, contradiction and safety dimensions | P030 frozen synthesis over supplied facts | Does not calculate houses/planets/Vargas/Dasha/Transit |
| `docs/current-state/p030/` | P030 governed documentation | Yes | Platform distinctions and cross-domain boundaries | Frozen implementation contract | Astrological inputs remain candidate/reference labels |
| `docs/current-state/p029/`, `know-prop-001/`, `p015-rx/` | Validated governance records | Yes | Home/residence/property boundary; D4 calculation method | P029 context only; D4 calculation metadata | D4 interpretation remains not validated |
| `data/veda/research/astrology/` | Existing research registry | Yes for unrelated foundations | Dasha, graha, bhava and transit foundation records | Reused as lineage/context only | No governed travel passage record existed |
| Legacy interpreter/chart-fact prose | Reference/legacy | Partial | General labels such as foreign lands, travel and expenditure | Not authoritative P030 evidence | No passage-level provenance; cannot promote |

Current P030 behavior is a deterministic platform synthesis over supplied `movement_scores` and optional P021/P023/P024/P029 context. It does not independently infer a classical rule from a house, graha, Varga, Dasha or Transit. The frozen status is preserved.

Knowledge counts are unchanged because this activity adds no governed JSON claim or RAG document: Approved Core 0 movement records; Validated Knowledge 0 movement records; Research Candidate 0 structured movement records; Experimental 0; Research Archive 0. Existing global knowledge counts were not rewritten.
