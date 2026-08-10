# Veda Phase 8 Rollout Checklist

Date: 2026-08-04

Status: Implementation complete, backend/API verification complete, automated
React coverage complete, and live browser UI QA complete. Microphone and spoken
voice acceptance are still planned as the separate detailed test round.

Detailed React audit report:

- `docs/governance/VEDA_REACT_TEST_REPORT_2026-08-04.md`
- `docs/governance/VEDA_LIVE_UI_QA_2026-08-04.md`

## What was verified in this session

- Focused Veda backend/API test suite passed:
  - `python -m pytest tests\test_veda_attachment_service.py tests\test_veda_research_service.py tests\test_veda_knowledge_review_service.py tests\test_veda_repo_capability_service.py tests\test_veda_mcp_provider.py tests\test_veda_chat_router.py -q`
  - Result: `22 passed`
- Follow-up backend capability verification passed:
  - `python -m pytest tests\test_veda_chat_router.py tests\test_veda_mcp_provider.py -q`
  - Result: `8 passed`
- Frontend React test suite passed:
  - `cmd /c npm test`
  - Result: `3 files, 5 tests passed`
- Frontend TypeScript check passed:
  - `cmd /c npx tsc --noEmit --pretty false`
- Live browser UI QA passed:
  - Chrome headless via Selenium against `http://127.0.0.1:5173/chat`
  - Result:
    - research unavailable state shown honestly
    - attachment upload flow passed
    - save-to-knowledge draft flow passed
    - MIT repo draft flow passed
    - floating widget shared-state flow passed
- Live HTTP smoke passed against the running local app:
  - frontend `http://127.0.0.1:5173` returned the Vite app shell
  - backend `http://127.0.0.1:8001/api/chat/capabilities` returned:
    - `research_enabled = true`
    - `research_provider_available = false`
    - `research_runtime_ready = false`
    - `attachments_enabled = true`
    - `mcp_enabled = false`
    - `supported_attachment_mime_prefixes = application/pdf, image/, text/, application/json`

## Important live-env note

- `mcp_enabled = false` in the running environment on August 4, 2026.
- This means the code supports MCP fallback, but no usable MCP server is active
  in the current runtime yet.
- Because of the follow-up fix, Veda now shows this truthfully in the UI
  instead of pretending research is live when the provider is unavailable.

## Browser UI checklist

1. Open `http://localhost:5173/chat`.
2. Confirm the research toggle, attachment button, and `MIT REPO` button are visible.
3. Click the attachment button and confirm the chooser only allows PDF, text,
   JSON, and image types.
4. Ask a normal local-data question and confirm Veda answers without breaking
   the evidence area.
5. Turn on research mode and ask an outside-information question.
6. Confirm the answer still shows source/evidence details and does not hide
   whether research was used.
7. Upload one PDF or text file and confirm:
   - the file appears as a pending attachment pill
   - the send button works with or without extra typed text
   - the assistant response shows file-aware evidence
8. Upload one image and confirm the same pending/response flow works.
9. Use `Review to save` / `Save to knowledge` and confirm the approval flow
   completes and the message shows the saved state.
10. Use `MIT REPO`, scan a local MIT repo path, and confirm the approval flow
    saves a reusable repo note.

## Manual voice checklist

1. Open the app in Chrome or Edge with microphone permission enabled.
2. Click the mic button and confirm speech capture starts and stops cleanly.
3. Ask one voice question and confirm Veda speaks the reply.
4. Press `Stop` during speech and confirm playback stops.
5. Turn wake word on and confirm `Veda` / `Adya` still opens the listen flow.
6. Turn follow-up on and confirm the mic reopens after a spoken reply.
7. In Hindi mode, confirm Hindi wake-word variants and Hindi spoken prompts
   still behave correctly.

## Exit rule for the later QA round

- If the manual browser and voice steps all pass, Veda Phase 8 is fully ready
  for normal use in this environment.
- If a manual step fails, record the exact failure, fix it, rerun the focused
  tests above, and update this checklist plus the changelog.
