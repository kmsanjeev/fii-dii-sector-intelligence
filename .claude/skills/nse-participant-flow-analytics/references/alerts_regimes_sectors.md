# Alert Thresholds, Regime Classification, Sector Rotation, Macro Calendar

Load whenever generating signals, alerts, regime labels, sector-rotation output, or event-study analysis.

## Alert thresholds & signal rules

- FII net sell exceeds ₹2,000 Cr for 3+ consecutive sessions → flag.
- FII and DII diverge by more than ₹3,000 Cr net in a single session → flag.
- Pro net short in index futures while FII net long (or vice versa) → flag as a historically short-term reversal signal.
- Retail net long in index futures exceeds the 90th percentile of the trailing 60-session distribution → flag as contrarian extreme.
- Every alert must include: date, participant, segment (Cash/F&O), value, threshold breached, and a plain-English one-line summary.
- Render every alert as a traffic-light gauge card (green/amber/red: current value vs threshold) + a 30-session sparkline for that participant-segment pair.

## Sector rotation tracking

- Sectors: Nifty IT, Nifty Bank, Nifty Financial Services, Nifty Auto, Nifty Pharma, Nifty FMCG, Nifty Realty, Nifty Metal, Nifty Energy.
- Identify rotation by comparing rolling 5-session vs 20-session net flow per sector.
- Flag when a sector moves from net outflow to net inflow (or vice versa) for 2+ consecutive sessions.
- Sector-level data carries the `exchange` column too, for future BSE sectoral index mapping.

## Historical depth & backtesting

- Default lookback: 3 years of daily EOD data for participant/sector flow analysis.
- Backtesting any participant-based signal: minimum 2 years out-of-sample — never test and validate on the same window.
- Store raw fetched data before transformation, so it can be reprocessed if logic changes.
- Backfill strategy: fetch in monthly chunks to avoid rate limits, store incrementally by date partition.

## Market regime detection

Four regimes, classified per session from participant flow:

| Regime | Condition | Color |
|---|---|---|
| Risk-On | FII + DII both net buyers | Teal |
| Risk-Off | FII + DII both net sellers | Coral/red |
| Divergence-FII-Led | FII buying, DII selling | Blue |
| Divergence-DII-Led | DII buying, FII selling | Amber |

- Track rolling 20-session regime distribution to distinguish sustained shifts from one-off sessions.
- Annotate all charts/signal outputs with the current regime label.
- Regime calendar heatmap: trading days × months, cells color-coded per the palette above.

## Macro & calendar event context

- Maintain a calendar of: RBI MPC dates, US Fed meeting dates, NSE F&O expiry dates, India budget date, FII limit utilization threshold alerts (>90% utilized).
- Flag any signal generated within 2 trading sessions of a major macro event — downweight, higher uncertainty.
- RBI policy days: first-hour FII flow is often a knee-jerk reaction — note this in intraday analysis.
- Overlay macro event markers as vertical dashed lines on all time-series charts.
- Event-study charts: pre/post window (−5 to +5 sessions) for participant net flow, as a butterfly chart.
