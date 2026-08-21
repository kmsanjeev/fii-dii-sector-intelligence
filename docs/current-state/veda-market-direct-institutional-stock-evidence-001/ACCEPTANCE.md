# Acceptance register

| Gate | Result | Evidence |
|---|---|---|
| Existing source audit first | PASS | source and data inventory |
| Direct daily stock FII/DII proof | PASS_WITH_CONDITION | explicit no-source decision |
| Direct sector FII/DII proof | PASS_WITH_CONDITION | explicit no-source decision |
| Deals and ownership separated | PASS | contract and date model |
| Participant classification conservative | PASS | unknown fallback preserved |
| Canonical identity / ambiguity | PASS_WITH_CONDITION | exact symbol; unmatched symbols review-required |
| Stock contract additive | PASS | `stock-intelligence-1.1` nested evidence |
| Cross-layer per-stock fallback | PASS | existing market-only boundary retained |
| No score/prediction/ML/LLM/RAG changes | PASS | implementation inventory |
| Raw provider data committed | PASS | no new raw files |
| Full-suite/final Git gates | PASS_WITH_CONDITION | FII `1322 passed, 1 warning`; VEDA `76 passed, 2 warnings`; selective Git gates remain in the final commit/push record |

Overall activity status: `IMPLEMENTED_WITH_CONDITIONS`.
