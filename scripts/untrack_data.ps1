# Untrack data files that are now gitignored
# Run: powershell -File scripts/untrack_data.ps1

$files = @(
    "data/NSE/corporate_actions/2026.csv",
    "data/NSE/corporate_actions/2026.parquet",
    "data/NSE/corporate_actions/corporate_actions_acquisition_log.csv",
    "data/NSE/equity_master/equity_master.csv",
    "data/NSE/equity_master/nse_corporate_actions_derived.csv",
    "data/NSE/equity_master/nse_corporate_actions_derived.parquet",
    "data/NSE/equity_master/nse_corporate_actions_master.csv",
    "data/NSE/equity_master/nse_corporate_actions_master.parquet",
    "data/NSE/equity_master/reports/mapping_coverage_report.csv",
    "data/NSE/equity_master/reports/series_distribution.csv",
    "data/historical/institutional/cash_market_flows_history.csv",
    "data/historical/institutional/institutional_positioning_history.csv",
    "data/intelligence/block_bulk_deals.csv",
    "data/intelligence/bull_run_probability.csv",
    "data/intelligence/bull_run_watchlist.csv",
    "data/intelligence/corporate_action_signals.csv",
    "data/intelligence/corporate_confidence_scores.csv",
    "data/intelligence/event_calendar.csv",
    "data/intelligence/institutional_deal_signals.csv",
    "data/intelligence/participant_flow_scores.csv",
    "data/intelligence/participant_intelligence.csv",
    "data/intelligence/price_momentum.csv",
    "data/intelligence/rag_knowledge/documents.jsonl",
    "data/intelligence/rag_knowledge/faiss/faiss_ALL.index",
    "data/intelligence/rag_knowledge/faiss/faiss_CORPORATE.index",
    "data/intelligence/rag_knowledge/faiss/faiss_DEAL.index",
    "data/intelligence/rag_knowledge/faiss/faiss_MARKET.index",
    "data/intelligence/rag_knowledge/faiss/faiss_SECTOR.index",
    "data/intelligence/rag_knowledge/faiss/faiss_STOCK.index",
    "data/intelligence/sector_capital_flows.csv",
    "data/intelligence/sector_flow_scores.csv",
    "data/intelligence/sector_rotation_history.csv",
    "data/intelligence/sector_rotation_intelligence.csv",
    "data/intelligence/upcoming_catalysts.csv"
)

foreach ($f in $files) {
    Write-Host "Removing from index: $f"
    git rm --cached $f 2>$null
}

Write-Host ""
Write-Host "Done. Files removed from git index (still on disk)."
Write-Host "Run: git add .gitignore; git commit -m 'chore: gitignore data files and IDE configs'"
