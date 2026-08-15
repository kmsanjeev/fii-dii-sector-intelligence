# Future Phase Registry

This is the single authoritative future registry.

| ID | Title | Track | Status | Dependencies | Gate / notes |
|---|---|---|---|---|---|
| P027 | Advanced Synthesis & Multi-Chart Reasoning | A | IMPLEMENTED / FROZEN | P014–P026, PRED-001–003, STD-001–003 | Evidence convergence, contradiction resolution, timing hierarchy, and governed multi-chart context; implementation evidence in `docs/current-state/p027/` |
| VEDA-EMP-001 | Empirical case acquisition and learning | D/C | ACTIVE_LONGITUDINAL | PRED-001–003 | Requires legitimate cases; no new store |
| VEDA-STD-003 | Universal Conversational Intelligence, Pragmatics & Multilingual Expression Standard | B/E | IMPLEMENTED / FROZEN | STD-001, STD-002, RM-001 | Shared context foundations; see `docs/current-state/std-003/` |
| VEDA-COMM-001 | Conversation-Type & Pragmatic Understanding Engine | E | IMPLEMENTED / FROZEN | STD-003 | Deterministic context, pragmatic intent, multi-turn stability, and ChatEngine fallback; see `docs/current-state/comm-001/` |
| VEDA-LANG-001 | English/Hindi/Hinglish idiom, phrase & slang intelligence | E | IMPLEMENTED / FROZEN | STD-003, COMM-001 | Deterministic Wave-1 registry and contextual resolver; see `docs/current-state/lang-001/` |
| VEDA-COMM-002 | Adaptive Conversational Response Engine | E | IMPLEMENTED / FROZEN | STD-003, COMM-001, LANG-001, LANG-001-R1 | Deterministic adaptation profile and response benchmark; human A/B validation remains pending; see `docs/current-state/comm-002/` |
| VEDA-GROUP-001 | Multi-Speaker / Group Conversation Intelligence | E | IMPLEMENTED / FROZEN | STD-003, COMM-001, COMM-002 | Deterministic participant/turn, reply/addressee, topic, position, conflict, and subject attribution layer; see `docs/current-state/group-001/` |
| VEDA-EMO-001 | Emotional & Relational Intelligence Engine | E | IMPLEMENTED / FROZEN | COMM-001, LANG-001, GROUP-001, COMM-002 | Human-sensitive emotional context, interaction need, relational signals, and per-speaker emotion; implementation evidence in `docs/current-state/emo-001/` |
| VEDA-LANG-002+ | Additional language packs | E | PLANNED | LANG-001, quality gates | Language-specific authorization |
| VEDA-ADM-EMP-001 | Empirical Case Intake & Bulk Import Console | F/D | IMPLEMENTED / FROZEN | EMP-001, shared case registry | Preview → validate → accept → ingest; see `docs/current-state/adm-emp-001/` |

Statuses are controlled vocabulary: IMPLEMENTED, ACTIVE, PLANNED, DEFERRED, RESERVED, BLOCKED, SUPERSEDED, RETIRED.

P027 policy: the historical reservation is preserved in prior roadmap records; the current scope is Advanced Synthesis & Multi-Chart Reasoning. P027 is `IMPLEMENTED / FROZEN`; the full-repository timeout condition remains documented separately from P027-specific acceptance.
