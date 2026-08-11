# VEDA-P008 Knowledge Gaps

Date: `2026-08-11`

Knowledge Gap Centre consumes the gap-generation work already established by P007.

## Surface Contents

- gap id
- domain
- gap description
- priority
- related legacy-rule ids
- mission count
- candidate count
- current status

## Admin Actions Exposed

- start research
- open related mission
- increase mission priority

## Backend Source

`ResearchPlatformService.knowledge_gap_rows()` provides the current read model and reuses P007 gap-generation behavior rather than duplicating gap logic in the UI.

