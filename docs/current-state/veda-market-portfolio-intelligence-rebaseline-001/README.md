# VEDA-MARKET-PORTFOLIO-INTELLIGENCE-REBASELINE-001

Status: `OPERATIONAL_WITH_CONDITIONS`
Date: 2026-08-21

This activity rebaselines the existing Phase-20 Portfolio engine into a
governed, read-only intelligence projection. It does not create a second
portfolio engine, migrate ownership into VEDA, enable trading, or change the
legacy mutation routes.

## Decision

The governed portfolio surface is operational for the current single-user
local portfolio. It is conditional because the current portfolio transaction
and position stores are local files, the audited portfolio is empty, risk
snapshots are therefore unavailable, and formal multi-user/workspace
persistence is not yet established.

Theme membership history remains explicitly deferred and is not a blocker for
current many-to-many Theme exposure. Historical acquisition remains
operational with source-conditioned freshness: equity and stock history reach
2026-08-20, while the audited F&O history/intelligence reaches 2026-08-19.

## Scope boundaries

- Reused `engines/portfolio/portfolio_engine.py` for transactions and positions.
- Reused existing cross-layer, Theme, sector and risk artifacts.
- Added only the read-only FII contract at `/api/portfolio/governed`.
- Exposed the formal VEDA capability `market.portfolio.intelligence`.
- No broker mutation, order submission, trade execution, ML, prediction, RAG,
  EMP, Jyotish, Theme-history or BEBOS change.
- `VEDA-MARKET-THEME-MEMBERSHIP-HISTORY-RX-001` remains deferred.

See [AUDIT.md](AUDIT.md), [CONTRACT.md](CONTRACT.md),
[VALIDATION.md](VALIDATION.md), and [ACCEPTANCE.md](ACCEPTANCE.md).
