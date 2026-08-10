@echo off
git rm --cached data/NSE/corporate_actions/2026.csv
git rm --cached data/NSE/corporate_actions/2026.parquet
git rm --cached data/NSE/corporate_actions/corporate_actions_acquisition_log.csv
git rm --cached data/NSE/equity_master/equity_master.csv
git rm --cached data/NSE/equity_master/nse_corporate_actions_derived.csv
git rm --cached data/NSE/equity_master/nse_corporate_actions_derived.parquet
git rm --cached data/NSE/equity_master/nse_corporate_actions_master.csv
git rm --cached data/NSE/equity_master/nse_corporate_actions_master.parquet
git rm --cached data/NSE/equity_master/reports/mapping_coverage_report.csv
git rm --cached data/NSE/equity_master/reports/series_distribution.csv
git rm --cached data/historical/institutional/cash_market_flows_history.csv
git rm --cached data/historical/institutional/institutional_positioning_history.csv
git rm --cached data/intelligence/block_bulk_deals.csv
git rm --cached data/intelligence/bull_run_probability.csv
git rm --cached data/intelligence/bull_run_watchlist.csv
git rm --cached data/intelligence/corporate_action_signals.csv
git rm --cached data/intelligence/corporate_confidence_scores.csv
git rm --cached data/intelligence/event_calendar.csv
git rm --cached data/intelligence/institutional_deal_signals.csv
git rm --cached data/intelligence/participant_flow_scores.csv
git rm --cached data/intelligence/participant_intelligence.csv
git rm --cached data/intelligence/price_momentum.csv
git rm --cached data/intelligence/rag_knowledge/documents.jsonl
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_ALL.index
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_CORPORATE.index
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_DEAL.index
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_MARKET.index
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_SECTOR.index
git rm --cached data/intelligence/rag_knowledge/faiss/faiss_STOCK.index
git rm --cached data/intelligence/sector_capital_flows.csv
git rm --cached data/intelligence/sector_flow_scores.csv
git rm --cached data/intelligence/sector_rotation_history.csv
git rm --cached data/intelligence/sector_rotation_intelligence.csv
git rm --cached data/intelligence/upcoming_catalysts.csv
echo.
echo Done. All data files removed from git index.
