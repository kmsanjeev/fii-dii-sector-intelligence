# Remediation

Implemented:

1. Extracted deterministic membership construction from request handling.
2. Added validated, source-fingerprinted membership snapshot loading.
3. Added a bounded derived price projection for the five supported windows.
4. Added independent price-manifest invalidation.
5. Added atomic artifact writes and artifact-hash validation.
6. Reused the existing concurrent local price loader for offline projection
   builds.
7. Added `--write-cache` to the canonical Theme snapshot build command.
8. Preserved current API contracts, Theme semantics, provenance, and safety
   boundaries.
9. Corrected VEDA natural Theme-query routing so “Analyse the capex cycle
   theme” selects the Theme capability instead of treating `CAPEX` as a stock.

The cold artifact build remains an explicit bounded preparation step and is
not hidden inside application startup. A missing artifact can still trigger a
bounded rebuild according to the existing provider behavior; deployments
should run the canonical build command before interactive use.
