# Future Phase Registry

This is the single authoritative future registry.

| ID | Title | Track | Status | Dependencies | Gate / notes |
|---|---|---|---|---|---|
| P027 | RESERVED — capability not assigned | A | RESERVED | Explicit capability decision | No arbitrary domain assignment |
| VEDA-EMP-001 | Empirical case acquisition and learning | D/C | ACTIVE_LONGITUDINAL | PRED-001–003 | Requires legitimate cases; no new store |
| VEDA-STD-003 | Universal Conversational Intelligence, Pragmatics & Multilingual Expression Standard | B/E | CAPTURED / PLANNED / NOT_IMPLEMENTED | STD-001, STD-002 | Separate authorization required |
| VEDA-COMM-001 | Conversation-Type & Pragmatic Understanding Engine | E | PLANNED | STD-003 | Only after STD-003 authorization |
| VEDA-LANG-001 | English/Hindi/Hinglish idiom, phrase & slang intelligence | E | PLANNED | STD-003 | Contextual use; no blind mirroring |
| VEDA-COMM-002 | Adaptive Conversational Response Engine | E | PLANNED | STD-003, COMM-001, LANG-001 | Response benchmark gate |
| VEDA-GROUP-001 | Multi-Speaker / Group Conversation Intelligence | E | PLANNED | STD-003, COMM-001 | Speaker/turn provenance required |
| VEDA-LANG-002+ | Additional language packs | E | PLANNED | LANG-001, quality gates | Language-specific authorization |
| VEDA-ADM-EMP-001 | Empirical Case Intake & Bulk Import Console | F/D | IMPLEMENTED / FROZEN | EMP-001, shared case registry | Preview → validate → accept → ingest; see `docs/current-state/adm-emp-001/` |

Statuses are controlled vocabulary: IMPLEMENTED, ACTIVE, PLANNED, DEFERRED, RESERVED, BLOCKED, SUPERSEDED, RETIRED.

P027 policy: Option A, retain sequential compatibility but reserve P027 until an explicit Jyotisha capability is authorized.
