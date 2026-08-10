# Veda Live UI QA Report

Date: 2026-08-04

Tester: Codex Selenium browser pass

Status: Passed for live browser UI flows. Microphone and spoken-audio QA are
still pending.

## Scope

This pass tested the live Veda UI against the running local app on August 4,
2026:

- chat page at `http://127.0.0.1:5173/chat`
- floating Veda widget
- attachment upload flow
- reviewed knowledge draft flow
- MIT repo study draft flow
- research availability state shown in the UI

## Method

- Chrome headless driven by Selenium
- live frontend at `http://127.0.0.1:5173`
- live backend at `http://127.0.0.1:8001`
- real browser rendering, real button clicks, real file upload, real API-backed
  responses

QA artifact screenshots saved during the pass:

- `D:\tmp\veda_live_qa\chat-page-initial-final.png`
- `D:\tmp\veda_live_qa\chat-page-after-attachment-final.png`
- `D:\tmp\veda_live_qa\chat-page-mit-repo-final.png`
- `D:\tmp\veda_live_qa\widget-open-final.png`

## What passed

### 1. Chat page research state is honest

- the page showed `RESEARCH UNAVAILABLE`
- the research button was disabled
- the tooltip said:
  - `Research mode is enabled, but no live research provider is available right now.`
- the textarea placeholder also reflected the unavailable research runtime

Plain meaning:

Veda no longer pretends that outside research is live when the provider is not
available in the runtime.

### 2. Attachment flow works in the live UI

- the Veda attachment input accepted:
  - `application/pdf`
  - `image/*`
  - `text/*`
  - `application/json`
- a real text file was attached through the live chat page
- the pending attachment pill appeared
- the message was sent successfully with the uploaded file
- the assistant response showed file-aware evidence:
  - `Files: 1 attachment`
  - `Basis: local data + your files`
- the assistant response also reflected the uploaded file content and included
  the unique QA token `ALPHA-73`

Plain meaning:

The live chat UI is correctly passing uploaded attachment context through to
Veda.

### 3. Save-to-knowledge review draft works

- `Review to save` appeared after the assistant reply
- the review panel opened
- the panel showed:
  - trace sources
  - `Approve And Save`
  - `Cancel`
- the draft loaded without hanging

Plain meaning:

The reviewed-save workflow is working at the draft/review stage in the live UI.

### 4. MIT repo study draft works

- the `MIT REPO` button was visible
- the panel opened successfully
- a real local repo path was entered:
  - `D:\Projects\fii-dii-sector-intelligence`
- repo scan completed
- the panel showed:
  - `License Check`
  - `Candidate Files`
  - `Approve And Save`
  - `Close`

Plain meaning:

The live MIT repo capability study workflow is working at the draft/review
stage in the browser.

### 5. Floating widget state matches the full chat page

- the Veda orb opened the widget successfully
- the widget also showed `RESEARCH UNAVAILABLE`
- the widget research button was disabled with the same explanatory tooltip
- the widget attachment input matched the page accept rules
- the uploaded attachment/message from the page was visible in the widget too

Plain meaning:

The shared Zustand state between ChatPage and VedaWidget is behaving correctly
in the live browser.

## Important limits of this QA pass

- microphone capture was not tested in this pass
- spoken audio playback was not tested in this pass
- no `Approve And Save` action was submitted during browser QA, to avoid
  creating extra permanent knowledge records just for testing
- outside research success was not tested because the live runtime on August 4,
  2026 reported:
  - `research_enabled = true`
  - `research_provider_available = false`
  - `research_runtime_ready = false`

## Verdict

### Browser UI

- passed

### Attachment handling

- passed

### Knowledge review draft

- passed

### MIT repo study draft

- passed

### Research availability messaging

- passed

### Voice and microphone

- still pending separate QA
