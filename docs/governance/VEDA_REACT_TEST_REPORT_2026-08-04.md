# Veda React Test Report

Date: 2026-08-04

Tester: Codex runtime audit

Status: React/UI audit completed, follow-up fixes implemented, and automated
React coverage is now live

## Follow-up implementation update

The two audit findings from this report were fixed on the same date.

Closed items:

- research readiness is now reported honestly from backend to frontend:
  - backend capability response includes
    `research_provider_available` and `research_runtime_ready`
  - ChatPage and VedaWidget now disable the research toggle and show
    `RESEARCH UNAVAILABLE` when the runtime cannot actually do outside lookup
- the frontend now has a real React test stack:
  - `vitest`
  - `@testing-library/react`
  - `@testing-library/jest-dom`
  - `@testing-library/user-event`
  - `jsdom`

Automated verification after the fix:

- `cmd /c npm test` in `frontend/`
  - result: `3 files, 5 tests passed`
- `cmd /c npx tsc --noEmit --pretty false` in `frontend/`
  - result: passed
- `python -m pytest tests\test_veda_chat_router.py tests\test_veda_mcp_provider.py -q`
  - result: `8 passed`

## Scope

This test pass covered the Veda user-facing React surfaces and their main
flows:

- full chat page: `frontend/src/pages/ChatPage.tsx`
- floating Veda widget: `frontend/src/components/veda/VedaWidget.tsx`
- shared state: `frontend/src/store/vedaStore.ts`
- evidence display: `frontend/src/components/veda/MessageEvidence.tsx`
- knowledge review panel
- MIT repo capability review panel

## Test method

Because this repo does not currently have a React test runner or browser
automation package configured, this report used a mixed method:

1. Static React/state review of the Veda components and shared Zustand store
2. Live backend capability checks against the running app on:
   - `http://127.0.0.1:5173`
   - `http://127.0.0.1:8001`
3. Live API-backed smoke tests for the flows that the React UI drives

## What passed

### 1. App is live

- frontend responded on `http://127.0.0.1:5173`
- backend responded on `http://127.0.0.1:8001`

### 2. Capability handshake works

Live `GET /api/chat/capabilities` returned:

- `research_enabled = true`
- `attachments_enabled = true`
- `save_to_knowledge_enabled = true`
- `mit_repo_intake_enabled = true`
- `mcp_enabled = false`
- `supported_attachment_mime_prefixes = ["application/pdf", "image/", "text/", "application/json"]`

This means the React surfaces should render the research toggle, attachment
button, save-to-knowledge flow, and MIT repo flow in the current runtime.

### 3. Normal local chat works

Live `POST /api/chat` with a local market question returned:

- valid reply
- valid `session_id`
- `research.used = false`
- `research.reason = "local_first"`

So the normal local-first chat path is working.

### 4. Attachment upload works

Live `POST /api/chat/attachments` returned a proper attachment stub with:

- `storage_key`
- `excerpt`
- `kind = "text"`
- no warning

### 5. Attachment-aware answer works

After reusing the real returned `storage_key`, live `POST /api/chat` with the
attachment produced a file-aware summary reply. This shows the React attachment
flow should work when it uses the upload response correctly, which it does.

### 6. Save-to-knowledge flow works

Live endpoints worked end to end:

- `POST /api/chat/knowledge/draft`
- `POST /api/chat/knowledge/draft/{draft_id}/approve`

The approval returned:

- `status = "approved"`
- a valid `doc_id`

### 7. MIT repo study flow works

Live endpoints worked end to end against the local repo:

- `POST /api/chat/capabilities/repo/draft`
- `POST /api/chat/capabilities/repo/draft/{draft_id}/approve`

The repo draft showed:

- MIT license detection
- candidate files
- review facts/tags

The approval returned:

- `status = "approved"`
- a valid capability `doc_id`

## Findings

### 1. High: Research mode looks available in the UI even when live outside research is not actually usable

Files:

- `backend/routers/chat.py:60`
- `backend/routers/chat.py:254`
- `frontend/src/store/vedaStore.ts:461`
- `frontend/src/pages/ChatPage.tsx:1026`

What happened:

- live capabilities reported `research_enabled = true`
- live capabilities reported `mcp_enabled = false`
- a live research-mode chat request returned:
  - `research.used = false`
  - `research.provider = "ddgs"`
  - `research.error = "provider_unavailable"`

Plain meaning:

The React UI lets the user switch on research mode, but in the current runtime
that does not mean outside research will actually work.

Why this matters:

This is confusing for the user. The screen says research mode is on, but the
actual result is a local or generic fallback answer because the provider is not
available.

Root cause:

The capability contract exposed to React does not include a clear
`provider_available` or `research_runtime_ready` flag, so the UI cannot show a
truthful "research switch exists, but live provider is down" state.

Recommended fix:

- add a runtime readiness field to `ChatCapabilities`
- disable or warn on the research toggle when no live research provider is
  actually available

### 2. Medium: There is still no real React test runner in the frontend

File:

- `frontend/package.json:6`

What happened:

The frontend has `dev`, `build`, `lint`, and `preview`, but no `test` script
and no React test framework such as Vitest or Testing Library.

Plain meaning:

Veda UI changes can pass TypeScript and still break actual behavior without
being caught early.

Why this matters:

The Veda UI now has several stateful flows:

- shared store between widget and full chat
- attachment upload
- evidence rendering
- save-to-knowledge review
- MIT repo review
- research-mode state

These are exactly the kinds of flows that benefit from React integration tests.

Recommended fix:

- add `vitest` + `@testing-library/react`
- cover:
  - capability hydration in `vedaStore`
  - chat page research toggle behavior
  - attachment pill rendering/removal
  - knowledge review open/approve states
  - repo review open/approve states
  - evidence badges for local vs research vs attachment answers

## Important observations

- The attachment API is strict about using the real returned `storage_key`.
  A hand-crafted wrong key produced an empty-file answer. This is not a React
  bug because the React flow uses the real upload response.
- `mcp_enabled = false` in the current live environment on August 4, 2026.
  Phase 7 code is present, but no usable MCP server is active in this runtime.

## Overall verdict

### React/UI status

- core Veda flows are wired correctly and the main panels work through their
  live APIs
- attachment upload, reviewed knowledge save, and MIT repo study all passed
- the biggest live problem is not rendering, but truthfulness of the research
  availability state shown to the user

### Result

- UI foundation: good
- live research readiness reporting: not good enough yet
- automated React coverage: missing

## Suggested next step

1. Run the separate human browser + microphone acceptance round.
2. If the live env later enables MCP or another provider, confirm the research
   toggle moves from unavailable to available without UI regressions.
