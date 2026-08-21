# Audit and readiness

## Acquisition and market foundations

| Area | Finding | Governance state |
|---|---|---|
| Equity bhavcopy | Latest audited data 2026-08-20 | Operational |
| Stock history | Manifest processed through 2026-08-20; 5,388 symbols | Operational |
| F&O historical acquisition | Latest audited report/intelligence 2026-08-19 | Operational with source condition |
| Daily scheduler | Existing staged refresh is present; GitHub workflow is currently manual-only | Existing condition; not changed here |
| Incremental refresh | Existing stock-history manifest and daily stages reused | Operational |
| Intraday | No governed query-time intraday foundation in this activity | Deferred; foundation required |
| Theme history | Current membership only; historical membership absent | Deferred, non-blocking |

The activity does not introduce a new acquisition system. The date gap between
equity and F&O is preserved as a source-freshness condition rather than filled
with synthetic values.

## Existing Portfolio surfaces

- `engines/portfolio/portfolio_engine.py` remains the calculation/transaction
  owner.
- `/api/portfolio`, `/buy`, `/sell`, import and delete routes remain intact.
- Existing risk engines and TCA artifacts are consumed, not recalculated by
  the governed projection.
- Broker adapters remain outside the new default read-only projection; no
  broker write path is reachable from it.
- Current local `transactions.csv` and `positions.csv` are empty. The empty
  result is explicit, not treated as missing or as a zero-valued portfolio.

## Legacy audit

| Legacy surface | Classification |
|---|---|
| `bull_run_probability.csv` | Compatibility-only context |
| `ml_bull_run_scores.csv` | Legacy; not authoritative |
| `company_announcements.csv` | Compatibility-only context |
| `corporate_confidence_scores.csv` | Legacy; not authoritative |
| `sector_rotation_intelligence.csv` | Compatibility-only context |
| `key_signal` | Deprecated for governed portfolio decisions |
| `trade_conviction_engine` | Legacy experimental; not authoritative |
| BUY/SELL labels | Not authoritative and not exposed as orders |

## Readiness

- Positional intelligence: ready for a separate governed implementation,
  conditional on EOD adjusted OHLCV and current cross-layer freshness.
- F&O intelligence: ready for hardening, conditional on current source
  freshness, expiry/OI/PCR provenance and downstream date semantics.
- Intraday intelligence: not ready; query-time acquisition and bounded
  session semantics are missing.
- Preferred next activity: `VEDA-MARKET-FNO-INTELLIGENCE-HARDENING-001`.

The deferred Theme-history activity is not started by this record.
