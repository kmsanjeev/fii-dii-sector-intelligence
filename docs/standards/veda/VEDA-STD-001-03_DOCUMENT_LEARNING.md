# Document Learning

`DocumentLearningService` registers a supplied document, segments paragraphs into passages, creates candidate claims, compares them against research-mode retrieval, and labels each result as exact, supporting, or new knowledge.

Document learning creates pending research candidates. It never performs automatic Approved Core promotion. Existing source and passage identifiers are preserved; missing identifiers are not fabricated.
