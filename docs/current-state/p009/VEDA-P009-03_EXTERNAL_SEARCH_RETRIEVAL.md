# External Search And Retrieval

P009 separates:

- search/discovery;
- direct retrieval/fetch;
- evidence extraction.

Implemented flow:
1. mission selects a search provider;
2. provider returns normalized search results;
3. retrieval provider fetches content only after URI safety checks pass;
4. extracted text is sanitized and passed into the existing candidate pipeline.

The default external providers are generic and conservative:
- search results are discovery material;
- fetched web text is not treated as authoritative knowledge;
- generated candidates from external sources remain `RESEARCH_CANDIDATE`.
