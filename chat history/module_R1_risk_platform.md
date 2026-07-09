# MODULE R1 — RISK PLATFORM

Module-wise session log. Append-only per phased development protocol.

---

## Session 2026-07-09 — Phase R1: Portfolio Risk Foundation (COMPLETE)

**Origin:** Institutional completeness audit (Bloomberg/Aladdin benchmark) found the
platform had zero quantitative risk measurement attached to a system capable of live
order execution. Grep for VaR/ES/Monte Carlo/covariance across all engines matched
only Vedic astrology code (Vara/varga). Phase R1 closes the Critical gap.

**Architecture freeze:** contract approved with D1 (backup automation) deferred —
user will use an external drive; backup stays in pipeline backlog. Delivered D2-D4.

### D2 — Portfolio Risk Engine
- NEW `engines/risk/portfolio_risk_engine.py` (new `engines/risk/` package)
- Historical + parametric VaR (95/99, 1d + sqrt(10)-scaled 10d), ES 97.5/99 (Basel),
  component VaR via Euler decomposition, annualized vol, max drawdown (2Y synthetic
  curve), beta vs equal-weighted NIFTY 50 constituents (no index OHLCV exists in repo)
- Simple returns (not log) — required for linear aggregation r_p = w . r
- Ledoit-Wolf shrunk covariance (sklearn) — raw sample cov is ill-conditioned
- 500d lookback, 60d minimum aligned days, else returns None (never zeros)
- Symbols without cache history flagged EXCLUDED_NO_HISTORY / SHORT_HISTORY,
  surfaced in output — never silently dropped
- Outputs: `data/intelligence/portfolio_risk.csv` (history, deduped by run_date),
  `portfolio_risk_components.csv` (snapshot)
- Wired into daily pipeline as stage R1_portfolio_risk after 20_portfolio

### D3 — Backtest Metrics Upgrade (additive)
- `engines/backtest/metrics.py`: + sortino, profit_factor, avg_win, avg_loss,
  max_drawdown (sequential trade equity curve). Existing keys untouched.

### D4 — API + GUI
- NEW `backend/routers/risk.py`: GET /api/risk/portfolio, POST /api/risk/refresh
  (synchronous in-process compute); registered in backend/main.py
- PortfolioPage.tsx: new PORTFOLIO RISK panel — VaR/ES/vol/beta/maxDD cards
  (color-coded by VaR as % of portfolio), risk-contribution bars with capital-weight
  tick marks ("risk-heavy" flag when risk share > 1.35x weight), excluded-symbols
  warning strip, Refresh Risk button

### Verification (gate-2)
- Live portfolio: empty -> engine skips cleanly, exit 0, no file (valid state)
- Synthetic 10-position fixture (9 real symbols + 1 fake, I/O redirected to
  scratchpad): VaR95 1d = Rs 10,006 on Rs 678K (1.48%), VaR99 > VaR95,
  ES >= VaR, param/hist ratio 0.94, Euler contributions sum 100.01%,
  fake symbol flagged EXCLUDED_NO_HISTORY, beta 0.887, all assertions passed
- API smoke (TestClient): 404 on GET before first run, 422 with clear message on
  refresh with empty portfolio
- Frontend: tsc clean, vite build clean
- Test suite: 242 passed, 25 PRE-EXISTING failures (guardrail tests wanting
  TEST_TELEGRAM_TOKEN/TEST_GOOGLE_CREDS env fixtures + stale price-validator
  expectations; pytest was not even installed in the 3.11 env before this session).
  None of the failing modules import R1 code. TECH DEBT: fix test env fixtures.

### Deferred / next phases
- D1 backup automation -> external drive, still pending
- Phase R2: stress testing (2008/2020 replay) + Barra-lite factor model
- Phase R3: Monte Carlo VaR (single-node vectorized first, distributed seam later)
- Phase R4: TCA + order slicing (when live trading is regular)

---

## Session 2026-07-09 (later) — Test Suite Repair + Phase R2 (COMPLETE)

### Test suite: 25 pre-existing failures -> 267/267 green (commit f0ddd50)
GUARDRAILS.md used as the arbiter for every code-vs-test dispute.
- CODE BUGS (2): fetch_with_retry crashed on callables without __name__
  (Mock, functools.partial); validate_shareholding_sum TypeError on others=None
- STALE TESTS (23): G-I-02 API drift (returns RELIABLE/UNRELIABLE strings, not
  bool), G-I-05 inverted semantics (True means STALE per spec), np.bool_
  identity checks (`is True` fails), G-F-04 log-vs-raise contract, G-F-02
  pytest.raises match pattern, conftest fixture missing TEST_* env vars,
  EC-SYM-02 conceptually wrong (spin-off = distinct ISINs = both retained)
- Context: pytest was never installed in the py -3.11 env; suite had not run

### Phase R2 — Stress Testing + Factor Model
**stress_test_engine.py:**
- Historical: GFC_2008 (Sep-Nov 08), TAPER_2013, ILFS_2018, COVID_2020
  (Feb 19-Mar 23); per-holding actual window return from parquet cache;
  fallback basis SYMBOL -> SECTOR avg -> MARKET avg (NIFTY 500 universe,
  survivorship-biased fallback explicitly labelled); basis counts in output
- Hypothetical: MKT_DOWN_10/20, FII_EXODUS, RATE_SHOCK sector-shock maps
**factor_model_engine.py (Barra-lite):**
- 26-27 sector one-hots + MOMENTUM (90d ret z) + SIZE (log median 60d traded
  value z) + VALUE (earnings yield z from data/NSE/results/valuation_scores.csv)
- Static current exposures over 250d window; all cross-sections solved in one
  pinv; LW factor covariance; idio var from residuals
- Portfolio: x = wX exposures, sys var = x'Fx, idio = sum w^2 s^2, Euler
  per-factor contributions
- NOTE: valuation_scores.csv lives in data/NSE/results/ NOT data/intelligence/
  (CLAUDE.md intelligence listing is aspirational there)
**API:** /api/risk/stress + /api/risk/factors (GET + POST refresh)
**GUI:** StressPanel (scenario cards, proxied-position warnings) + FactorPanel
  (systematic share, top-10 factor bars) on PortfolioPage
**Pipeline:** R2a_stress_test + R2b_factor_model after R1_portfolio_risk

### Verification
- Fixture: Covid -34.6% / GFC -29.5% (sane vs NIFTY -38%), uniform -10% shock
  -> exactly -10.00%, basis counts sum to 9; factor model: 88.7% systematic,
  sector exposures sum 1.000, total^2 = sys^2 + idio^2 within 2%
- Live: factor universe 473 stocks, mean daily R2 0.14, factor_returns.csv 250d
- Factor-model total vol (19.9%) vs R1 direct LW vol (13.35%) on same fixture:
  different estimators + 250d vs 500d lookback; both retained deliberately
- tsc + vite build clean; suite 267/267
