# Module Log — Phase V-DATA-2: Fix Stale STRONG_CANDIDATE/AVOID Taxonomy

**Date:** 2026-07-13
**Status:** COMPLETE
**Version:** 4.45.0

## User Request

"take on the STRONG_CANDIDATE bug next" -- follow-up to the Phase V-DATA
audit that found 9 files checking a dead label taxonomy.

## Root Cause

engines/intelligence/CLAUDE.md documented the label taxonomy as
`>=65 STRONG_CANDIDATE | >=45 EMERGING | >=30 WATCHLIST | >=15 NEUTRAL |
<15 AVOID`. bull_run_probability_engine.py's actual current implementation
uses a 6-value Wyckoff-cycle-aligned scheme (`>=60 BULL_RUN | >=52
EMERGING | >=40 WATCHLIST | >=25 NEUTRAL | <25 splits into ACCUMULATION
(institutional presence, Wyckoff accumulation phase) vs MARKDOWN (no
institutional support)`). The doc was never updated when the engine's
taxonomy changed, so nothing flagged the 9-file mismatch to a reader.

## Files fixed

1. **backend/routers/report_generator.py** -- LABEL_META dict was missing
   ACCUMULATION and MARKDOWN entirely; STRONG_CANDIDATE/AVOID keys never
   matched. Since lookup falls back to NEUTRAL styling on a miss, both the
   best (BULL_RUN) and worst (MARKDOWN) stocks rendered as bland amber
   "neutral" in every report. Rebuilt to full 6-value scheme.
2. **backend/routers/stocks.py** -- 4 separate call sites. Thesis
   generation gave BULL_RUN and ACCUMULATION (the newest label, no branch
   existed) the least informative fallback response. Added dedicated
   branches for both.
3. **engines/portfolio/portfolio_engine.py** + **engines/broker/
   sync_engine.py** -- identical `_key_signal()` pattern in both: STRONG
   BUY SIGNAL / REVIEW POSITION never fired. Added ACCUMULATION branch
   ("BASE BUILDING" -- distinct text to avoid colliding with the existing
   "ACCUMULATION" output string used for EMERGING positions).
4. **engines/backtest/backtest_engine.py** -- prioritization list never
   included the platform's strongest label; also added ACCUMULATION
   (genuinely new label, no old-taxonomy equivalent, worth prioritizing).
5. **engines/ai/knowledge/document_builder.py** (3 sites) + **retriever.py**
   -- RAG documents for BULL_RUN stocks either excluded entirely or
   contained the sentence "puts this stock in STRONG_CANDIDATE territory",
   a label that no longer exists.
6. **engines/intelligence/theme_intelligence_engine.py** -- BULL_RUN
   signal counter was reading 0.
7. **engines/research/conviction_screener_engine.py** -- most consequential
   find: `base[base["label"] != "AVOID"]` (the "red flag" hard gate) was a
   silent no-op since inception. MARKDOWN-labelled (actively declining)
   stocks were never actually excluded from the platform's flagship
   efficacy-weighted screener -- the exact screener wired into Veda
   yesterday as "prefer this over get_top_stocks."
8. **engines/intelligence/CLAUDE.md** -- corrected the Phase 8B docs to
   the real current thresholds/labels (this doc's staleness is what let
   the bug spread across 9 files undetected).

## NOT touched (correctly out of scope)

engines/intelligence/astro_engine.py, kundli_engine.py,
kundli_interpretator.py use "AVOID" as one of their OWN action values
(BUY/HOLD/CAUTION/EXIT/AVOID) -- a separate, correct, unrelated system.

## Verification (ran the actual engines, not just code review)

- `conviction_screener_engine.py` re-run: confirmed 0 MARKDOWN stocks in
  the 1,562-row output (previously unfiltered -- the bug was real and now
  demonstrably fixed).
- `document_builder.py` re-run: all 500 stock RAG documents now correctly
  say "Accumulation label is BULL_RUN" where applicable (verified by
  reading documents.jsonl directly, not just checking it ran).
- `faiss_indexer.py` + `bm25_indexer.py` rebuilt on the corrected corpus;
  live test queries returned BULL_RUN-labelled stocks correctly.
- Full test suite 267/267 green.
