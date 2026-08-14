# Implementation Inventory

| Role/capability | Current implementation |
|---|---|
| Orchestration | `AgentOrchestrator` minimal route selection |
| Shared context | `contracts.py` structured request/evidence contracts |
| Classical vs empirical | explicit layer/type enums and provenance fields |
| Pattern learning | `PatternRegistry`, expert and empirical records |
| Prediction/outcome | `PredictionRegistry`, immutable outcome lock |
| Retrieval | existing `UnifiedHybridRetriever` with STD-001 modes |
| Document learning | existing `DocumentLearningService`, compatible with pattern extraction |

The implementation is an extension/adapter, not a replacement of domain engines.
