# Module Log — Phase UI-D: Dashboard Consolidation

**Date:** 2026-07-12
**Status:** COMPLETE
**Version:** 4.40.0

## User Request

Review the Participant page: is a separate page really required? Move it to
the Dashboard. Remove Emerging Watchlist and Top Conviction (covered by the
Watchlist page). Fix Upcoming Catalysts (no links) and Block Deals (names
with no data). Sector Capital Rotation: 5 columns x 2 rows visible, rest
behind an expand option. Discussion first, then implementation.

## Analysis

Participant page was ~80% duplicate of Dashboard content. Unique elements
rescued: Flow Interpretation narrative, FII vs DII 1Y history chart with
period toggle, FPI vs MF 60-session cash bar chart, cash sub-participant
z-scores, 20D cash totals.

Block Deals root cause: frontend read `net_value_cr` / `client_name` /
`trade_date`, but `/api/corporate/deals` serves institutional_deal_signals.csv
whose columns are `inst_net_value_cr`, `deal_signal`, `dominant_participant`,
`last_deal_date`. Every field resolved to `--`.

## User Decisions (AskUserQuestion)

1. Sector grid top-10 sort: **by relative_score desc** (strongest rotation first)
2. History charts: **always visible** (side-by-side row, not collapsed)
3. Deals card: **keep 30D aggregated signal** (fixed rendering), not raw deals

## Implementation

- `Dashboard.tsx`: FlowInterpretation + ParticipantHistory components added;
  FlowBars extended with 4 cash-market rows (divider "CASH"); ConvictionPanel
  gained 20D rows; SectorHeatmap full-width 5-col with SECTORS_VISIBLE=10 and
  expand toggle; SidePanel replaced by CatalystsCard + DealsCard (both linked
  to stock pages, 8 rows each); EmergeCard + Emerging Watchlist row removed;
  new order: strip > instruments > flows+interpretation > history > sectors >
  catalysts+deals > X ticker > news.
- `App.tsx`: /participant route -> `<Navigate to="/" replace />`.
- `AppShell.tsx`: Participant nav entry removed.
- Deleted: `ParticipantPage.tsx`, `FlowCard.tsx` (orphaned).

## Verification

- tsc --noEmit clean; vite build clean (2.76s)
- /api/participant/latest live-checked: FPI/MF/INS/RETAIL scores present,
  same +/-100 scale as F&O scores -> shared maxAbs bar normalization valid
- /api/participant/history serves FPI_flow_5D -> cash bar chart renders

## Notes

- All participant flow scores are +/-100-style scaled scores, not raw sigma
  z-scores; mixing F&O and cash rows in one bar instrument is scale-safe.
