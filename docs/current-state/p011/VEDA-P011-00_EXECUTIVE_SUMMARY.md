# VEDA-P011 Executive Summary

VEDA-P011 adds an approved-core retrieval path on top of the existing unified retrieval and chat contract.

Implemented outcomes:
- approved-core records are retrieved as `APPROVED_CORE`, not flattened into generic RAG text
- citations, source IDs, passage IDs, claim IDs, rule IDs, conflict IDs, authority, and version state now survive retrieval
- unified retrieval keeps approved core, local evidence, reviewed internal memory, legacy unsourced knowledge, and ML signals separated
- chat prompt rules now explicitly preserve governed knowledge, citation integrity, inference labelling, and high-stakes boundaries
- Admin research diagnostics can inspect approved-core retrieval, ontology matches, audit data, and final context

Primary implementation paths:
- `engines/ai/knowledge/approved_core_rag.py`
- `engines/ai/knowledge/unified_retriever.py`
- `engines/ai/chatbot/chat_engine.py`
- `backend/routers/research.py`
- `frontend/src/components/admin/ResearchAdminConsole.tsx`

Boundaries preserved:
- no Approved Core promotion occurs in P011
- no production astrology rule activation occurs in P011
- no astrology calculation behavior changes occur in P011
