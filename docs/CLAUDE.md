# DOCS DIRECTORY — CLAUDE CONTEXT

## DOCUMENTATION GOVERNANCE (ADR-015)
Documentation is MANDATORY before release of any module.
The update sequence after every code change:
```
1. Update MODULE_REGISTRY.md (completion %)
2. Update MASTER_CHECKLIST.md (tick completed items)
3. Update CHANGELOG.md (what changed, why)
4. Update PROJECT_MASTER_STATE.md (phase status)
5. Update module doc in docs/modules/ (if module scope changed)
```

## DOCUMENT HIERARCHY

```
docs/
├── CLAUDE_MASTER_DEV_GUIDE.md    ← Full context guide (load when in doubt)
├── PROJECT_MASTER_STATE.md       ← Phase status + next priorities (keep current)
│
├── architecture/                 ← Structural blueprints (update with ADRs only)
│   ├── MASTER_ARCHITECTURE.md   ← 10-layer architecture
│   ├── DATA_ARCHITECTURE.md     ← Data flow + storage (needs path fix: NSE Data → NSE)
│   ├── AI_ARCHITECTURE.md
│   ├── GUI_ARCHITECTURE.md
│   └── BROKER_ARCHITECTURE.md
│
├── governance/                   ← Standards and tracking (update frequently)
│   ├── MASTER_ROADMAP.md        ← 11-phase roadmap
│   ├── MODULE_REGISTRY.md       ← Module inventory with completion %
│   ├── MASTER_CHECKLIST.md      ← ☐/◐/☑ tracker for all deliverables
│   ├── DEVELOPMENT_GOVERNANCE.md ← Coding standards, workflow, release rules
│   ├── PROJECT_SCOPE.md         ← Mission, objectives, capital flow framework
│   ├── RESEARCH_PIPELINE.md
│   └── CHANGELOG.md             ← Change history (update every session)
│
├── modules/                      ← Per-module specs (update when module changes)
│   ├── INSTITUTIONAL_INTELLIGENCE.md   ← 75% complete
│   ├── PARTICIPANT_INTELLIGENCE.md     ← 0% (ADR-016 approved)
│   ├── SECTOR_INTELLIGENCE.md          ← 45% complete
│   ├── THEME_INTELLIGENCE.md           ← 35% complete
│   ├── STOCK_INTELLIGENCE.md           ← 10% complete
│   ├── FUNDAMENTAL_INTELLIGENCE.md     ← 5% complete
│   ├── AI_PLATFORM.md
│   ├── GUI_PLATFORM.md
│   └── EXECUTION_PLATFORM.md
│
├── decisions/                    ← ADR register (never delete, only supersede)
│   └── ADR-001 through ADR-020
│
└── legacy/                       ← Old docs (DO NOT USE — for historical reference only)
```

## ADR CREATION RULES (ADR-012)
Create a new ADR whenever:
- A new architectural pattern is adopted
- A data source policy changes
- A new intelligence layer is added
- A major technology decision is made

ADR naming: `ADR-0NN-Title-With-Hyphens.md`
Next ADR number: ADR-021

ADR template:
```markdown
# ADR-0NN — Title
Status: [Proposed | Accepted | Superseded]
Date: YYYY-MM-DD
## Context
## Decision
## Consequences (Positive / Negative)
## Related ADRs
```

## WHEN TO UPDATE WHICH DOC
| Trigger | Update These Docs |
|---------|-------------------|
| Engine completed | MASTER_CHECKLIST.md, MODULE_REGISTRY.md, PROJECT_MASTER_STATE.md |
| New engine started | MODULE_REGISTRY.md (mark In Progress) |
| Bug found | MASTER_CHECKLIST.md (add to technical debt), CHANGELOG.md |
| Architecture decision | Create ADR, update MASTER_ARCHITECTURE.md if layer changes |
| Phase completed | PROJECT_MASTER_STATE.md, MASTER_CHECKLIST.md, MASTER_ROADMAP.md |
| New module | Create docs/modules/<MODULE>.md before writing code |
| Path/naming change | DATA_ARCHITECTURE.md, CLAUDE_MASTER_DEV_GUIDE.md |

## DATA_ARCHITECTURE.md FIX NEEDED
The file currently references `data/NSE Data/` (with a space) throughout.
Correct path is `data/NSE/`. Update when working in this file.

## LEGACY DOCS
`docs/legacy/` contains superseded versions of early docs.
They were valid during Generation 1 of the platform.
Do not use them for development reference — use current `docs/` structure.
