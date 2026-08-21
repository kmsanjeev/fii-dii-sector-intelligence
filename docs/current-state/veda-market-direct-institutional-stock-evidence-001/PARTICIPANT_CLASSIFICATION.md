# Participant classification

The existing deal engine classifies client names using keyword lists. That
classification is retained as `DERIVED_HEURISTIC` with `CONDITIONAL` confidence
for FII, MF, insurance and promoter labels. The engine's fallback `RETAIL` is
not a source-reported participant class and is normalized to `UNKNOWN` in the
authoritative contract.

Unknown remains unknown. No client-name match is treated as proof of a legal
institutional identity, fund mandate, beneficial owner, or FII/DII flow.

Cash/F&O participant categories remain separate and market-level. They are not
joined to stock-level deals by inference.
