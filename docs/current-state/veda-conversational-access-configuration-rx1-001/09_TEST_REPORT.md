# RX1 test report

## Backend

- Focused conversational/access/router/engine suite: **40 passed, 1 warning**.
- Full Python suite: **1,290 passed, 1 warning**, 630.67 seconds.
- Direct route/access smoke: passed for CORE, GENERAL, ASTRO, MUHURTA, KUNDLI,
  MARKET and ASTRO_FINANCE; duplicate primary ownership fails loudly.

## Frontend

- Full Vitest discovery: **8 files, 29 tests passed**.
- Production build: passed with existing nonblocking large-chunk warning.

The only test warning is the pre-existing Starlette/httpx deprecation warning.
No provider calls, RAG rebuild or production knowledge change was introduced.
