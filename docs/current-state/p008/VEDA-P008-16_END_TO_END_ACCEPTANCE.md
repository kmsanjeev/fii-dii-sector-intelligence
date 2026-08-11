# VEDA-P008 End-to-End Acceptance

Date: `2026-08-11`

## Scenario Results

### Scenario A — Approve

- candidate detail opens
- evidence is visible
- Admin decision is submitted
- approval returns `PROMOTION_READY`
- production knowledge remains unchanged

### Scenario B — Needs More Research

- `REQUEST_MORE_RESEARCH` path verified in API tests
- follow-up mission creation verified for synthetic follow-up-enabled candidate
- ledger records both the decision and follow-up creation

### Scenario C — Reject

- rejection path remains supported by the approval state machine
- archived/rejected knowledge remains queryable through approvals and ledger history

### Scenario D — Research Continues

- inherited P006/P007 continuation tests remain passing
- pending review does not block later research activity

## Evidence

- backend admin API tests: [tests/test_veda_research_admin_api.py](/D:/Projects/fii-dii-sector-intelligence/tests/test_veda_research_admin_api.py)
- frontend admin console tests: [frontend/src/test/AdminResearchControlCentre.test.tsx](/D:/Projects/fii-dii-sector-intelligence/frontend/src/test/AdminResearchControlCentre.test.tsx)
- continuation behavior: existing P006/P007 integration suites

