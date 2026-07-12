# Module Log — Phase V-DATA: Full Data Coverage for Veda + ML

**Date:** 2026-07-13
**Status:** COMPLETE (core scope); 2 items explicitly deferred, 1 new bug found and flagged
**Version:** 4.44.0

## User Request

Following a data-access audit (previous session turn) that found Veda only
had 14 tools and was giving an inaccurate self-report of her own
capabilities: "fix all the highlighted issues. I want Veda to have all
information handy with her and let ml learn from everything happening in
the entire application. no part should be missed by ml. plan for the
architecture updates if necessary. Confirm what all have been done and in
pending state."

## Part A — Veda tool registry: 14 -> 23 tools

New tools added to engines/ai/chatbot/tools/data_tools.py +
tool_registry.py: get_stock_fundamentals, get_shareholding_pattern,
get_stock_announcements, get_management_sentiment,
get_corporate_action_history, get_conviction_picks, get_deal_tape,
get_price_history, get_technical_screener.

Unified _enrich_with_technical() (shared by get_top_stocks, get_fno_stocks,
get_stocks_by_sector, and now get_stock_detail via a single call) to carry
the FULL technical_indicators.csv field set (rsi, macd, atr, bollinger
bands, adx) plus watchlist_metrics (rvol, rs_30d, delivery_5d_pct) --
previously only 4 fields were exposed, and get_stock_detail's own inline
enrichment carried a DIFFERENT, smaller subset than the list-tools, which
was part of why Veda's answers were inconsistent depending on which tool
she reached for.

intent_router.py STOCK/CORPORATE domain hints updated to actively steer
tool selection toward the new tools (tool descriptions alone don't
reliably win against habit).

## Part B — ML feature + label completeness

Two bugs found during this work, both pre-existing and unrelated to
today's earlier commits:

1. **FEATURE_COLS staleness.** accumulation_model.py and bull_run_model.py
   both trained on a ~40-column list that stopped growing after Phase
   18C, while feature_engineering.py's feature_matrix.parquet had grown
   to 77 columns across Phase 12A/12B/12C/F/G. Everything after Phase 18C
   (valuation, technical patterns, theme/news/insider/concall signals,
   consensus, forward_return_score) was computed and silently discarded
   at training time. Synced both FEATURE_COLS to the full available set.

2. **Label taxonomy mismatch (found because the retrain FAILED outright).**
   feature_engineering.py's LABEL_MAP used AVOID/STRONG_CANDIDATE, a
   taxonomy bull_run_probability_engine.py stopped producing at some point
   in favor of BULL_RUN/EMERGING/WATCHLIST/NEUTRAL/ACCUMULATION/MARKDOWN.
   Every row with a label the map didn't recognize (i.e. every BULL_RUN,
   ACCUMULATION, and MARKDOWN row) fell through `.fillna(1)` into the
   NEUTRAL encoding. XGBoost's multi-class fit failed with "Invalid
   classes inferred... Expected [0,1,2], got [1,2,3]" -- only 3 of the
   expected 5 classes were ever actually present in the target, which is
   what surfaced the bug. Fixed to the real 6-value taxonomy; propagated
   the fix through accumulation_model's binary threshold (was >=3 for
   "EMERGING or STRONG_CANDIDATE", now >=4 for "EMERGING or BULL_RUN") and
   bull_run_model's LABEL_WEIGHTS/predicted_label/prob_* columns.

New feature sources added (77 -> 88 columns): watchlist_metrics (rvol,
rs_30d_vs_nifty, delivery_5d_pct), holding_trends QoQ deltas +
conviction_signal_enc, management_sentiment (ai_tone_score,
management_score, management_label_enc), astro_signals (sector-joined
astro_score -- included per explicit "no part missed" instruction; whether
it actually helps is for the model/future signal_efficacy backtests to
determine, not assumed at feature-engineering time).

Full retrain: feature_engineering -> accumulation_model -> bull_run_model
-> ml_scorer. All four ran clean on the second attempt (after the label
fix); 2,370 symbols scored. Suite 267/267 green throughout.

## Part C — Chat-to-ML training question: clarified, not built

Traced the full data path: conversation_log.csv is written only by
voice.py's /log endpoint, read only by chat_analytics_engine.py, which
produces pure usage/demand analytics with zero connection to engines/ml/.
This is CORRECT as designed and should not change: what a user asks about
does not predict whether a stock's price will move, so chat content is not
a valid feature for the return-prediction models -- mixing it in would be
a category error, not a completeness gap. A legitimately different idea
(a separate personalization layer weighting alerts/screener ordering by a
user's chat history) was identified as a real but SEPARATE system with its
own design tradeoffs (risk of reinforcing confirmation bias) and explicitly
NOT built without further scope confirmation.

## Found but deferred (new discovery, not fixed this phase)

9 files check `label == "STRONG_CANDIDATE"` (some also "AVOID") against the
RULE-BASED label column (bull_run_probability.csv's `label` /
portfolio_engine's `bull_run_label`) -- a different taxonomy problem than
the ML one fixed above, and one that predates this phase entirely. Since
that column has used BULL_RUN/ACCUMULATION/MARKDOWN for a while, these
checks have been silently dead code: backend/routers/stocks.py (thesis
generation), report_generator.py (color mapping), portfolio_engine.py
(STRONG BUY / REVIEW POSITION signals), broker/sync_engine.py (order
labels), backtest_engine.py (stock prioritization), document_builder.py +
retriever.py (RAG documents), theme_intelligence_engine.py (signal
counts). Flagged clearly to the user; not fixed here -- 9-file blast
radius with per-file correct-fix semantics warrants its own scoped phase.

## Verification

- All 10 new/changed data_tools functions tested directly (function
  level, no LLM) -- zero exceptions, correct schemas.
- 2 live /api/chat end-to-end tests through real LLM tool-calling
  (technical indicator synthesis, HIGH-tier conviction picks) --
  confirmed correct tool selection and data synthesis, not just plumbing.
- Full retrain pipeline run clean end to end.
- Suite 267/267 green at every checkpoint.
- /api/stocks/{symbol} live-checked post-retrain (ml_scores nested object
  correctly populated -- an apparent "blank" in one manual PowerShell
  check turned out to be checking the wrong JSON path, not a real bug).
