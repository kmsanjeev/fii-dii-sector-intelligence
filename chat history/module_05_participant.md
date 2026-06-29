# Module 05 — Participant Intelligence Layer
## Session Log (append-only)

---

## Session: 2026-06-30 — Phase 5A / 5B / 5C

### Trigger
User: "start Phase 5"
Continued from prior context which had completed Phase 4C (classification V4) and Phase 4D (NSE constituents).

### Context Carryover
- Directory `engines/participant/` + `__init__.py` + `CLAUDE.md` already created in prior session
- Existing `institutional_positioning_history.csv`: 2563 rows, 2016-01-01 to 2026-06-02, 21 columns
- nselib column trailing-space quirk documented; cash function signature (single date only) confirmed

---

### Phase 5A — `participant_acquisition_engine.py`

**Purpose:** Incremental downloader for F&O participant data + new cash market flows history.

**Key design decisions:**
- F&O: reads existing history, finds last date (2026-06-02), generates weekdays to today
- Cash: new file from 2024-01-01; stored separately in `cash_market_flows_history.csv`
- Net position = futures only: `Future_Index_Long + Future_Stock_Long − Future_Index_Short − Future_Stock_Short`
- Backward compatible: FNO_SCHEMA matches existing 21-column schema exactly (Score cols = raw values)
- Holiday handling: weekday generator + API "no data" errors treated as natural skip (not failure)
- All guardrails: G-A-01 (1s sleep), G-A-02 (3 retries exp backoff), G-A-03 (recovery queue), G-D-02 (atomic), G-D-03 (no empty write)

**Outputs:**
- Appends to `data/historical/institutional/institutional_positioning_history.csv`
- Creates `data/historical/institutional/cash_market_flows_history.csv`
- Writes `data/historical/institutional/participant_recovery_queue.csv` on failures

---

### Phase 5B — `participant_flow_engine.py`

**Purpose:** Rolling metrics and normalized flow scores (full rebuild on run).

**Key design decisions:**
- OI Delta = day-over-day change; rolling sums at 5D/20D/60D windows
- Z-score normalisation: 252-day rolling window, clipped ±3, scaled to ±100
- Score base signal: 20D OI delta rolling sum (captures medium-term accumulation)
- Cash participants (FPI/MF/Insurance/Retail): merged from cash_market_flows_history; score based on 20D rolling net
- Full rebuild pattern (not incremental) — deterministic given same inputs

**Output:** `data/intelligence/participant_flow_scores.csv`

---

### Phase 5C — `participant_intelligence_engine.py`

**Purpose:** Derives actionable participant intelligence from flow scores.

**Signals computed:**
- Conviction = % of last 20D with positive OI delta (0–100%)
- Smart Money Score = avg(FII_flow_score, PRO_flow_score)
- Retail Score = CLIENT_flow_score (contrarian)
- FII_DII_Divergence = FII − DII scores
- Smart_Retail_Divergence = Smart Money − CLIENT
- Market Opportunity = max(0, Smart) × max(0, −Retail) / 100 (fires when smart buys + retail sells)
- Cash_Institutional_Score = avg(FPI, MF)
- Ensemble Regime = Smart 50% + DII 25% + Cash Inst 25% → 5-level regime

**Output:** `data/intelligence/participant_intelligence.csv`

---

### Files Created
| File | Description |
|------|-------------|
| `engines/participant/participant_acquisition_engine.py` | Phase 5A |
| `engines/participant/participant_flow_engine.py` | Phase 5B |
| `engines/participant/participant_intelligence_engine.py` | Phase 5C |
| `chat history/module_05_participant.md` | This log |

### Files Updated
| File | Change |
|------|--------|
| `docs/governance/CHANGELOG.md` | v2.8 entry |
| `docs/governance/MODULE_REGISTRY.md` | Module 01 Participant: PLANNED → ACTIVE 85% |
| `memory/project_fii_dii.md` | Phase 5 ✅ 100%, status updated to 2026-06-30 |

### Governance
- CHANGELOG: v2.8 entry added
- MODULE_REGISTRY: Module 01 updated to 85% complete, ACTIVE
- Memory: phase table updated, chat history reference added

### Next Priority
Phase 6 — Sector Rotation + Capital Flow Engines
  - Read participant flow scores + sector OHLCV → compute per-sector FII/DII/PRO/CLIENT flows
  - Rolling allocation ratios (sector vs total F&O)
  - Sector rotation signals: momentum, reversal, leadership persistence
  - Output: `data/intelligence/sector_flow_scores.csv`
