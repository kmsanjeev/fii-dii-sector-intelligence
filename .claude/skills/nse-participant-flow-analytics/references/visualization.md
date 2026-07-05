# Visualization Standards

Load this file whenever producing any chart, infographic, dashboard, or report. The palette and chart-type mapping are fixed — never deviate from them.

## Stack

- `plotly` — primary, all interactive charts
- `matplotlib` — static fallback for reports/exports (via `kaleido` for PNG export of plotly charts too)
- `Streamlit` — dashboards

## Color palette — fixed, use everywhere

| Series | Color |
|---|---|
| FII | Blue `#185FA5` |
| DII | Teal/Green `#1D9E75` |
| Pro | Amber `#BA7517` |
| Retail | Coral/Red `#D85A30` |
| Nifty (reference line) | Gray `#5F5E5A` |

- Cash segment → solid lines / filled bars
- F&O segment → dashed lines / hatched bars

## Chart-type mapping — use the right chart for the right data

| Data scenario | Required chart type |
|---|---|
| Single-day participant net flow | Horizontal grouped bar chart (Cash vs F&O side by side) |
| Multi-day participant flow trend | Multi-line chart with area fill, one line per participant |
| FII vs DII divergence over time | Dual-axis line chart: FII left axis, DII right axis, divergence area shaded |
| OI change by strike | Horizontal bar chart (calls blue, puts coral), Max Pain marked as vertical line |
| PCR over time | Line chart, threshold bands at 0.7 (oversold) and 1.2 (overbought) shaded |
| OI classification (4 buckets) | 2×2 matrix scorecard, color-coded cells per participant |
| Sector rotation (current day) | Treemap sized by absolute flow, colored by direction |
| Sector rotation (over time) | Heatmap: sectors on Y-axis, dates on X-axis, diverging red-green scale |
| Alert status dashboard | Card grid, traffic-light indicators (red/amber/green) + sparklines |
| Backtest equity curve | Line chart + shaded drawdown area below zero baseline |
| Monthly returns | Calendar heatmap: months × years, red-green diverging |
| Market regime history | Segmented timeline bar or calendar heatmap, 4-color regime coding |
| Macro event impact | Event-study butterfly chart: −5 to +5 sessions around event date |
| Data quality / completeness | Heatmap, missing = gray, complete = teal |
| Participant flow distribution | Box-plot or violin chart per participant, 10th/90th percentile lines marked |

## When infographics are mandatory (always generate, never skip)

1. After any data fetch → data quality heatmap + summary bar chart of what was retrieved.
2. After computing net flows for any session/date range → horizontal grouped bar chart.
3. After detecting any alert/signal → traffic-light card + 30-session sparkline.
4. After any sector rotation computation → both the treemap (current) and the heatmap (time series).
5. After any backtest run → all four backtest charts (equity curve, monthly heatmap, accuracy-by-regime, drawdown waterfall).
6. In every report/summary output → a one-page dashboard infographic as the first output.

## When infographics should be suggested, not auto-generated

- Intraday tick-level data (note it may be heavy to render).
- Correlation matrices between participant flows and index returns (suggest heatmap).
- Network/flow diagrams between segments (suggest Sankey via `plotly.graph_objects.Sankey`).

## Streamlit dashboard layout — fixed order for every page

1. Top row: 4 metric cards — FII net, DII net, Pro net, Retail net (selected date).
2. Second row: regime indicator badge + active alerts (traffic-light cards).
3. Third row: main time-series chart (participant flows over selected date range).
4. Fourth row: sector heatmap (left) + sector treemap (right), side by side.
5. Fifth row (F&O tab only): OI-by-strike bar chart (left) + PCR line chart (right).
6. Sixth row: data quality indicator + last-fetch timestamp.

## Chart formatting standards — every chart

- Title: sentence case, date range in subtitle.
- X-axis: labeled "Date" or "Strike" as applicable, with units.
- Y-axis: labeled "₹ Cr" for rupee values, "Contracts" for OI.
- Legend: always visible, top-right or bottom-center, never overlapping data.
- Expiry-week sessions: light gray vertical band on all time-series charts.
- Macro event dates: dashed vertical line, charcoal gray, text annotation.
- Regime annotation: color-coded horizontal band at top of all time-series charts.
- Export every chart as both interactive HTML (plotly) and static PNG (matplotlib/kaleido).

## Daily summary one-pager (mandatory report infographic)

Every daily summary report includes a single compiled infographic with:
- Header: date, market regime label, active alert count.
- 4 participant net flow gauges (circular, today vs 30-day average).
- Mini sector heatmap (1 row × 9 sectors, colored by today's flow direction).
- Nifty 50 price bar with participant flow overlay as colored arrows.
- Alert table, traffic-light color coding.
- Footer: data source, fetch timestamp, exchange (NSE), next F&O expiry date.
