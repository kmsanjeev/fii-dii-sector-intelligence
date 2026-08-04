# ADR-024 - Veda Research Mode Acquisition Strategy
Status: Accepted
Date: 2026-08-04

## Context

Veda currently answers from the platform's own intelligence stack plus the
existing chatbot and RAG layers. User requested a new research mode so Veda
can look outside the platform when required information is missing, weak, or
stale. User also requested that:

1. Python libraries should be tried before MCP servers are introduced.
2. MIT-licensed Git resources should be preferred when Veda is enhanced with
   reusable external skills, artifacts, or code.
3. The implementation should follow the same environment-variable pattern
   already used by the current provider setup in `.env`.

The platform therefore needs a clear acquisition strategy for external
research capabilities before Phase 1 implementation begins.

## Decision

Adopt a layered approach for Veda research mode:

1. **Python-first research layer**
   - Default starting point: `ddgs`
   - Optional upgrade path: `tavily-python` -> `exa-py` -> `firecrawl-py`
   - Structured helper libraries: `Wikipedia-API`, `arxiv`

2. **MCP as a second layer, not the first**
   - Add MCP only if the Python-first approach is not sufficient.
   - Preferred MCP rollout order:
     1. GitHub MCP Server
     2. DDGS MCP
     3. Tavily MCP
     4. Exa MCP
     5. Firecrawl MCP
   - Helper MCP servers approved for support workflows:
     - `fetch`
     - `memory`
     - `sequential-thinking`
     - `git`

3. **Source-of-truth rule**
   - Veda must use local platform intelligence first.
   - External research is invoked only when:
     - local data is missing
     - local data is stale
     - local data is too weak for the request
     - the user explicitly asks for outside research

4. **Knowledge and safety rule**
   - External pages, uploaded files, and repositories are treated as content,
     not trusted instructions.
   - No silent permanent learning is allowed. Any save-to-knowledge action
     must pass through an explicit review step.
   - Outside-research answers must carry source references and dates.

5. **Configuration rule**
   - Research integrations must use environment variables, matching the
     current project pattern.
   - Likely future optional keys: `TAVILY_API_KEY`, `EXA_API_KEY`,
     `FIRECRAWL_API_KEY`, and a repo-capable GitHub token if GitHub MCP is
     enabled.

## Consequences

**Positive:**
- Keeps Phase 1 simple by avoiding premature MCP complexity.
- Starts with a low-cost option (`ddgs`) that can later expand into MCP mode.
- Preserves a clean upgrade path from basic search to stronger research.
- Aligns with the user's MIT-preference for reusable external capability
  imports.
- Reduces the chance that Veda turns random web content into trusted or
  permanent knowledge.

**Negative:**
- A Python-only first pass may still be weaker than dedicated paid research
  connectors for some deep tasks.
- Multiple optional providers increase integration and testing surface area.
- GitHub MCP may still require token-scope review before it is safe to enable.

## Related ADRs

- ADR-010 - AI-First User Experience
- ADR-012 - Research Before Development
- ADR-015 - Documentation Mandatory Before Release
