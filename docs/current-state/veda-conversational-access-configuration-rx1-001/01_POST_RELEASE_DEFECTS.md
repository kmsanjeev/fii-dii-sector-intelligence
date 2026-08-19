# Post-release defects and remediation

| Defect | Root cause | RX1 correction |
|---|---|---|
| General access was not independently configurable | `GENERAL_CHAT` was prohibited and core interaction was not represented separately | Added protected `CORE_INTERACTION`; `GENERAL_CHAT` is independently configurable |
| Routing depended on definition order | Related intent entries used first-wins behavior | Added one primary-owner map with duplicate detection that raises `RuntimeError` |
| Muhurta and Jyotish overlapped | Muhurta keywords were included in generic ASTRO handling | Added explicit Muhurta classifier and independent `MUHURTA` access route |
| AstroFinance contaminated ordinary Jyotish | ASTRO prompt and tool exposure included market signal behavior | Added `ASTRO_FINANCE`, market-free ASTRO prompt, and intent-scoped tools |
| Full Vitest discovery saw ignored dependency backups | Vitest had no durable discovery boundary | Included `src/test` and excluded dependency trees in `frontend/vite.config.ts` |

No source semantics, Muhurta recommendations, RAG, ML or prediction behavior
was changed.
