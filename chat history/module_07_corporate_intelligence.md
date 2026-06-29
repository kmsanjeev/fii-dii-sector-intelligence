# Module 07 — Corporate Intelligence Layer
## Session Log (append-only)

---

## Session: 2026-06-30 — Phase 7A / 7B / 7C

### Trigger
User: "start Phase 7"

### Context
- Phase 6 (Sector Rotation) completed in same session
- ADR-020 defines Corporate Intelligence Layer as Domains 2-6
- `data/NSE/corporate_actions/` already has 1999-2026 data from Phase 2
- nselib `financial_results_for_equity()` returns 404 on XBRL endpoint — skipped
- Management Intelligence (NLP/transcripts) deferred — requires AI pipeline

### Scope Decision
Phase 7 builds what's available without NLP/XBRL:
- 7A: Block/Bulk deal intelligence (FII/MF/PROMOTER classification)
- 7B: Event calendar (results dates, board meetings, upcoming catalysts)
- 7C: Corporate action intelligence (40k+ actions classified + confidence scores)

---

### Phase 7A — `block_bulk_deal_engine.py`

**Data sources:** `block_deals_data(period='6M')`, `bulk_deal_data(period='6M')`
- Block deals: qty >= 5L shares OR value >= Rs 5 Cr
- Bulk deals: qty >= 0.5% of total listed equity

**Participant classification via keyword matching:**
- FII: Goldman Sachs, Morgan Stanley, Barclays, UBS, Nomura, JP Morgan, BNP, HSBC, etc.
- MF: HDFC MF, ICICI Prudential, SBI MF, UTI, Kotak MF, etc.
- INSURANCE: LIC, HDFC Life, SBI Life, etc.
- PROMOTER: companies with PVT LTD, HOLDING LIMITED, FOUNDER patterns
- RETAIL: residual

**30D signal computation:**
- Net value = BUY - SELL in Cr per participant per symbol
- Signal: STRONG_ACCUMULATION (inst + promoter buying), INSTITUTIONAL_ACCUMULATION, INSTITUTIONAL_DISTRIBUTION, PROMOTER_CONFIDENCE, NEUTRAL

**Results (2026-06-30):**
- 12,467 deal rows (6M block + bulk)
- 361 symbols with signals
- Top accumulation: ADANIENT (+4790Cr), LENSKART (+3511Cr), LODHA (+2759Cr)

---

### Phase 7B — `corporate_event_calendar_engine.py`

**Data source:** `event_calendar_for_equity(from_date, to_date)` — chunked by month
- Start: 2023-01-01 (NSE archive depth for this function)
- Columns: symbol, company, purpose, bm_desc, date

**Event classification:**
- FINANCIAL_RESULTS: "financial result", "quarterly"
- DIVIDEND, BONUS, SPLIT, BUYBACK, RIGHTS: keyword matching on purpose field
- AGM, EGM: annual general / extraordinary general meeting
- OTHER: residual

**Upcoming catalyst prioritization:**
- Filter: next 60 days from today
- Catalyst score = purpose_priority × 10 + sector_combined_score / 10
- Blends event importance with sector participant flow signal

**Results (2026-06-30):**
- 33,839 event rows (2023-01-02 to 2026-06-30)
- 29,038 FINANCIAL_RESULTS, 691 DIVIDEND, 162 BONUS, 132 SPLIT, 83 BUYBACK
- 12 upcoming catalysts in next 60 days

---

### Phase 7C — `corporate_action_intelligence_engine.py`

**Data source:** existing `data/NSE/corporate_actions/<YYYY>.csv` (1999-2026, 28 files)
- Pure CSV processing, no API calls needed

**Classification regex patterns:**
- BUYBACK: "buy back", "buyback"
- BONUS: "bonus" + ratio extraction (e.g. "Bonus 1:2" → 0.5)
- SPLIT: "split", "sub-division" + new face value extraction
- DIVIDEND: "dividend", "div " + amount extraction in Rs
- RIGHTS: "rights"
- MERGER: "amalgam", "merger", "scheme of", "acquisition"
- AGM_EGM: "agm", "egm", "annual general", "extra ordinary"

**Confidence weights (12M rolling score):**
- BUYBACK +3, BONUS +2, SPLIT +1, DIVIDEND +0.5, RIGHTS -0.5

**Results (2026-06-30):**
- 40,517 EQ actions classified (1999-2026)
- 1,111 symbols with 12M rolling confidence scores
- Top: ECLERX (score +5.5, buyback+bonus), INFY (+4.0 buyback), LALPATHLAB (+4.0 bonus)

---

### Files Created
| File | Description |
|------|-------------|
| `engines/corporate/__init__.py` | Package init |
| `engines/corporate/CLAUDE.md` | Module context |
| `engines/corporate/block_bulk_deal_engine.py` | Phase 7A |
| `engines/corporate/corporate_event_calendar_engine.py` | Phase 7B |
| `engines/corporate/corporate_action_intelligence_engine.py` | Phase 7C |
| `data/intelligence/block_bulk_deals.csv` | 12,467 rows |
| `data/intelligence/institutional_deal_signals.csv` | 361 symbols |
| `data/intelligence/event_calendar.csv` | 33,839 rows |
| `data/intelligence/upcoming_catalysts.csv` | 12 items |
| `data/intelligence/corporate_action_signals.csv` | 40,517 rows |
| `data/intelligence/corporate_confidence_scores.csv` | 1,111 symbols |
| `chat history/module_07_corporate_intelligence.md` | This log |

### Files Updated
| File | Change |
|------|--------|
| `docs/governance/CHANGELOG.md` | v3.0 entry |
| `memory/project_fii_dii.md` | Phase 7 ✅ 100% |

### Deferred for Future Phases
- Financial results (XBRL) — nselib endpoint 404, needs alternative source
- Shareholding patterns — data not yet acquired
- Management Intelligence (NLP) — needs AI/LLM pipeline (Phase 9+)
- Governance Intelligence — complex scraping, deferred

### Next Priority
Phase 8 — Bull Run Probability Engine
Inputs now available: price momentum (Phase 3) + participant flows (Phase 5) +
sector rotation (Phase 6) + corporate intelligence (Phase 7)
Ready to compute per-stock bull run probability scores.
