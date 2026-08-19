# Final Acceptance Register

Measured release gates before Git release: focused/API `38/38` passed; full
Python `1,285/1,285` passed with one existing deprecation warning; frontend
source tests `29/29` passed; frontend production build passed; runtime smoke
passed. Full frontend discovery remains a local conditional because an
ignored `node_modules.pre-npm-ci-*` backup directory is discovered as a test
tree. Commit, push, tag and clean-tree verification remain the final release
steps.

Required invariants:

- ordinary unmatched conversation routes to `GENERAL`;
- market, sector, stock, corporate, Astro, Kundli and explicit research remain available;
- protected safety cannot be disabled;
- capability access cannot promote maturity;
- no automatic market RAG for general conversation;
- no RAG corpus or Approved Core change;
- no provider-call or production prediction change;
- configuration persists atomically and resets to full defaults.

Independent review also verified that optional Muhurta definitions cannot
override the authoritative GENERAL or ASTRO intent-to-capability mappings.
