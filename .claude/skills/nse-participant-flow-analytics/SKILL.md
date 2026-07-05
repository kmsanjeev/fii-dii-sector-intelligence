---
name: nse-participant-flow-analytics
description: Enforces Sanjeev's conventions and domain expertise for NSE/BSE participant-based money flow analysis (FII/DII/Pro/Retail) across Cash and F&O segments — schema rules, alert thresholds, OI/PCR/regime classification logic, sector rotation logic, nselib data-source guidance, and the full plotly/Streamlit visualization spec (color palette, chart-type mapping, mandatory infographics). Use this skill whenever writing, editing, or reviewing Python code that fetches, processes, analyzes, or visualizes NSE or BSE market data for this project — including participant flow, F&O OI/PCR, sector rotation, market regime detection, backtesting, macro-event overlays, or Streamlit dashboards — even if the user doesn't explicitly mention charts, conventions, or Indian markets by name.
---

# NSE/BSE Participant Flow Analytics

Domain + coding + visualization conventions for Sanjeev's Python platform tracking where FII, DII, Pro, and Retail capital moves across NSE (and eventually BSE) Cash and F&O segments. Apply coding expertise, market-microstructure expertise, and visualization together — never generate analysis code without also generating (or explicitly flagging as suggested) the matching chart.

## Before writing any code

1. **Schema**: every table/dataframe must carry `exchange` (NSE/BSE), `segment` (Cash/F&O), and `participant` (FII/DII/Pro/Retail) columns — even if only NSE is in scope today. This is non-negotiable; it's what keeps BSE integration a drop-in later rather than a rewrite.
2. **Module structure**: every module follows `config → fetch → process → store → visualize`, in that order, as separate functions/sections.
3. **Segments never merge without labelling.** Cash and F&O participant activity signal differently — always keep `segment` as an explicit grouping key, never silently aggregate across it.
4. **Net position over gross.** Always compute Buy − Sell net, not just turnover, and surface it as the headline number.

## Domain logic (apply automatically, don't wait to be asked)

- **FII ↔ DII divergence** (one net buying, other net selling at scale) is a key signal — flag explicitly whenever present.
- **Pro traders lead price** — treat Pro F&O positioning as a smart-money leading indicator.
- **Retail is often contrarian** — flag extreme readings (top/bottom decile historically), especially in index futures.
- **Indian market conventions**: NSE F&O lot sizes, T+1 settlement, 20% circuit limits, monthly expiry = last Thursday, weekly expiry = Thursday.
- **Expiry week** (last 4 trading days of the month) has noisier participant behavior — always flag these sessions in output and annotate/suppress signals accordingly.
- **OI + price → four buckets**: long buildup, short buildup, long unwinding, short covering. Classify participant positions into these wherever OI + price-direction data allows.
- For F&O analysis, always surface PCR, Max Pain, and OI change by strike/participant alongside directional flow.

Full alert thresholds, regime classification rules, sector rotation rules, and the macro-event calendar → see `references/alerts_regimes_sectors.md`. Load this whenever generating signals, alerts, regime labels, or sector-rotation output.

## Data sourcing

`nselib` is the primary source. It has known gaps and rate-limit behavior that affect fetch design (backfill chunking, fallback libraries, retry logic). → see `references/data_sourcing.md` before writing any fetch function or backfill script.

## Visualization — mandatory, not optional

Every data fetch, net-flow computation, alert, sector-rotation run, or backtest must be accompanied by its required chart(s) — see the full color palette, chart-type mapping table, mandatory-vs-suggested infographic rules, Streamlit dashboard layout, and chart formatting standards in `references/visualization.md`. Load this reference whenever producing any chart, dashboard, or report — the palette and chart-type mapping are fixed and must never be deviated from.

## Coding conventions — always apply

- Type hints on every function signature; NumPy-style docstrings on every function/class.
- `logging` module for all runtime output — never `print()`.
- Retry with exponential backoff (max 3 retries) on all `nselib`/API/network calls.
- Vectorized `pandas`/`numpy` — no Python loops over DataFrame rows.
- Validate fetched data before processing: null checks, schema checks, stale-date checks, range sanity checks.
- PEP 8, assume `black` + `isort` in the pipeline. Use `pathlib.Path` for all paths, never raw strings.
- Suggest `pytest` unit tests for every non-trivial function.
- Store raw fetched data before any transformation, so reprocessing is possible if logic changes later.

## Response format

- Always give complete, runnable Python with expected output shown in inline comments.
- If `nselib` has a known gap for the task, flag it upfront and suggest a workaround (see `references/data_sourcing.md`).
- Charts: axes labeled with units (₹ Cr / Contracts / Date), regime annotation layer, expiry-week shading — these are formatting requirements, not extras. Full standards in `references/visualization.md`.
