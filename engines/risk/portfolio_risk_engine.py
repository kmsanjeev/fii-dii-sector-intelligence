"""
Portfolio Risk Engine
Phase R1 -- Quantitative portfolio risk: VaR, Expected Shortfall, component risk.

Reads (all read-only, G-D-01):
  data/portfolio/positions.csv                   current holdings
  data/cache/stock_history/{SYMBOL}.parquet      daily closes
  data/NSE/indices/nifty_50_constituents.csv     market proxy universe (beta)
  data/intelligence/bull_run_probability.csv     symbol -> sector map

Writes (atomic, G-D-02):
  data/intelligence/portfolio_risk.csv             one row per run date (history, deduped G-D-05)
  data/intelligence/portfolio_risk_components.csv  per-symbol snapshot (overwritten)

Methodology:
  - Simple (arithmetic) daily returns -- required for linear portfolio
    aggregation: r_p = w . r  holds only for simple returns.
  - Covariance: Ledoit-Wolf shrinkage (sklearn) -- never raw sample
    covariance; 50 names x 500 days is ill-conditioned without shrinkage.
  - Historical VaR: percentile of actual joint portfolio P&L series.
  - Parametric VaR: normal quantile on w'Sigma w.
  - ES (CVaR): mean loss beyond the historical VaR cut (97.5% Basel + 99%).
  - Component VaR: Euler decomposition of parametric VaR.
  - 10-day figures use sqrt(10) scaling (flagged approximation).
  - Beta: vs equal-weighted NIFTY 50 constituent return (no index OHLCV
    history exists in the repo; proxy documented in output column name).

Returns None (never zeros) when the portfolio has < MIN_POSITIONS holdings
or < MIN_COMMON_DAYS aligned trading days (G-I-01 spirit).

Run:  py -3.11 -m engines.risk.portfolio_risk_engine
"""

import shutil
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

POSITIONS_CSV   = cfg.DATA_DIR / "portfolio" / "positions.csv"
NIFTY50_CSV     = cfg.INDICES_DIR / "nifty_50_constituents.csv"
SECTOR_SRC_CSV  = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"

RISK_CSV        = cfg.INTELLIGENCE_DIR / "portfolio_risk.csv"
COMPONENTS_CSV  = cfg.INTELLIGENCE_DIR / "portfolio_risk_components.csv"

# ── Parameters ────────────────────────────────────────────────────────────────

LOOKBACK_DAYS    = 500   # trading days of returns history
MIN_COMMON_DAYS  = 60    # minimum aligned days or the run aborts
MIN_POSITIONS    = 2     # single-stock "portfolio" has no diversification math

Z_95  = 1.6449
Z_99  = 2.3263
SQRT_10 = np.sqrt(10.0)

RISK_COLS = [
    "run_date", "portfolio_value", "n_positions", "n_excluded", "common_days",
    "var_hist_95_1d", "var_hist_99_1d", "var_hist_95_10d", "var_hist_99_10d",
    "var_param_95_1d", "var_param_99_1d", "var_param_95_10d", "var_param_99_10d",
    "es_hist_975_1d", "es_hist_99_1d",
    "vol_annualized_pct", "beta_vs_nifty50_ew", "max_drawdown_pct",
]
COMPONENT_COLS = [
    "run_date", "symbol", "sector", "qty", "last_close", "market_value",
    "weight_pct", "standalone_vol_pct", "component_var_95_1d",
    "risk_contribution_pct", "status",
]


class PortfolioRiskEngine:
    """Produces daily VaR/ES/component-risk snapshot for the live portfolio."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()
        self.excluded: list[dict] = []   # {symbol, reason}

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[PortfolioRiskEngine] Starting")
        positions = self._load_positions()
        if positions is None:
            logger.info("[PortfolioRiskEngine] Skipped -- portfolio too small for risk math")
            return True   # not an error: empty portfolio is a valid state

        result = self._process(positions)
        if result is None:
            logger.warning("[PortfolioRiskEngine] Aborted -- insufficient aligned history")
            return False

        snapshot, components = result
        self._save(snapshot, components)
        logger.info(
            "[PortfolioRiskEngine] Complete -- VaR95(1d) = %.0f INR on %.0f INR portfolio (%d positions, %d excluded)",
            snapshot["var_hist_95_1d"], snapshot["portfolio_value"],
            snapshot["n_positions"], snapshot["n_excluded"],
        )
        return True

    # ── Inputs ────────────────────────────────────────────────────────────────

    def _load_positions(self) -> pd.DataFrame | None:
        if not POSITIONS_CSV.exists():
            logger.warning("[PortfolioRiskEngine] No positions.csv -- nothing to do")
            return None
        df = pd.read_csv(POSITIONS_CSV)
        if df.empty or len(df) < MIN_POSITIONS:
            return None
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df["qty"]    = pd.to_numeric(df["qty"], errors="coerce")
        df = df.dropna(subset=["symbol", "qty"])
        df = df[df["qty"] > 0]
        return df if len(df) >= MIN_POSITIONS else None

    def _load_close_series(self, symbol: str) -> pd.Series | None:
        """Daily close series indexed by date, or None if unavailable."""
        pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
        if not pq.exists():
            return None
        try:
            df = pd.read_parquet(pq, columns=["date", "close"])
        except Exception as e:
            logger.warning("[PortfolioRiskEngine] Bad parquet for %s: %s", symbol, e)
            return None
        if df.empty:
            return None
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"])
        df = df[df["close"] > 0]                    # G-P-01
        df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
        return df.set_index("date")["close"]

    def _build_returns_matrix(self, symbols: list[str]) -> pd.DataFrame:
        """Wide matrix of simple daily returns, one column per symbol.
        Symbols without usable history land in self.excluded, not in the matrix."""
        series: dict[str, pd.Series] = {}
        for sym in symbols:
            s = self._load_close_series(sym)
            if s is None:
                self.excluded.append({"symbol": sym, "reason": "NO_HISTORY"})
                continue
            s = s.tail(LOOKBACK_DAYS + 1)
            if len(s) < MIN_COMMON_DAYS + 1:
                self.excluded.append({"symbol": sym, "reason": "SHORT_HISTORY"})
                continue
            series[sym] = s

        if not series:
            return pd.DataFrame()

        closes = pd.DataFrame(series)
        # Inner-join alignment: keep only dates where every symbol traded.
        # NaN gaps are dropped, never filled (G-I-04).
        closes = closes.dropna(how="any")
        return closes.pct_change().dropna(how="any")

    def _load_sector_map(self) -> dict[str, str]:
        if not SECTOR_SRC_CSV.exists():
            return {}
        try:
            df = pd.read_csv(SECTOR_SRC_CSV, usecols=["symbol", "sector"])
            df["symbol"] = df["symbol"].str.strip().str.upper()
            return df.set_index("symbol")["sector"].fillna("UNCATEGORIZED").to_dict()
        except Exception:
            return {}

    def _market_returns(self, index: pd.DatetimeIndex) -> pd.Series | None:
        """Equal-weighted NIFTY 50 constituent daily return, aligned to `index`.
        Proxy for the market factor -- no index OHLCV history exists in repo."""
        if not NIFTY50_CSV.exists():
            return None
        try:
            syms = pd.read_csv(NIFTY50_CSV)["symbol"].str.strip().str.upper().tolist()
        except Exception:
            return None
        cols = {}
        for sym in syms:
            s = self._load_close_series(sym)
            if s is not None and len(s) > MIN_COMMON_DAYS:
                cols[sym] = s
        if len(cols) < 30:   # proxy meaningless if most constituents missing
            return None
        rets = pd.DataFrame(cols).pct_change()
        mkt = rets.mean(axis=1, skipna=True)
        mkt = mkt.reindex(index).dropna()
        return mkt if len(mkt) >= MIN_COMMON_DAYS else None

    # ── Core computation ─────────────────────────────────────────────────────

    def _process(self, positions: pd.DataFrame) -> tuple[dict, pd.DataFrame] | None:
        symbols = positions["symbol"].tolist()
        returns = self._build_returns_matrix(symbols)

        if returns.empty or returns.shape[1] < MIN_POSITIONS or len(returns) < MIN_COMMON_DAYS:
            return None

        live_syms = list(returns.columns)
        pos = positions.set_index("symbol").loc[live_syms]

        # Market values and weights from latest close in the returns window
        last_close = {s: float(self._load_close_series(s).iloc[-1]) for s in live_syms}
        mv = np.array([pos.loc[s, "qty"] * last_close[s] for s in live_syms])
        V  = float(mv.sum())
        if V <= 0:
            return None
        w = mv / V

        R = returns[live_syms].values          # (T, N) simple returns
        T, N = R.shape

        # Ledoit-Wolf shrunk daily covariance (G: never raw sample cov)
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf().fit(R)
        sigma = lw.covariance_                  # (N, N)

        # Portfolio daily volatility and parametric VaR
        var_p   = float(w @ sigma @ w)
        sigma_p = float(np.sqrt(var_p))
        var_param_95_1d = Z_95 * sigma_p * V
        var_param_99_1d = Z_99 * sigma_p * V

        # Historical simulation: actual joint P&L path
        pnl = R @ w * V                         # (T,) daily INR P&L
        var_hist_95_1d = float(-np.percentile(pnl, 5))
        var_hist_99_1d = float(-np.percentile(pnl, 1))

        # Expected Shortfall on the historical tail
        tail_975 = pnl[pnl <= np.percentile(pnl, 2.5)]
        tail_99  = pnl[pnl <= np.percentile(pnl, 1.0)]
        es_975 = float(-tail_975.mean()) if len(tail_975) else var_hist_95_1d
        es_99  = float(-tail_99.mean())  if len(tail_99)  else var_hist_99_1d

        # Component VaR: Euler decomposition of parametric VaR
        # MC_i = w_i * (Sigma w)_i / sigma_p ; sums exactly to sigma_p
        marginal = (sigma @ w) / sigma_p        # (N,)
        comp_var_95 = w * marginal * Z_95 * V   # INR per position
        risk_contrib_pct = (w * marginal) / sigma_p * 100.0

        # Beta vs equal-weighted NIFTY 50
        beta = np.nan
        rp = pd.Series(R @ w, index=returns.index)
        mkt = self._market_returns(returns.index)
        if mkt is not None:
            joined = pd.concat([rp, mkt], axis=1, keys=["p", "m"]).dropna()
            if len(joined) >= MIN_COMMON_DAYS and joined["m"].var() > 0:
                beta = float(joined["p"].cov(joined["m"]) / joined["m"].var())

        # Max drawdown of the synthetic holdings curve over the window
        equity = (1.0 + rp).cumprod()
        dd = (equity / equity.cummax() - 1.0).min()

        snapshot = {
            "run_date":            self.run_date,
            "portfolio_value":     round(V, 2),
            "n_positions":         N,
            "n_excluded":          len(self.excluded),
            "common_days":         T,
            "var_hist_95_1d":      round(var_hist_95_1d, 2),
            "var_hist_99_1d":      round(var_hist_99_1d, 2),
            "var_hist_95_10d":     round(var_hist_95_1d * SQRT_10, 2),   # sqrt-scaling approx
            "var_hist_99_10d":     round(var_hist_99_1d * SQRT_10, 2),
            "var_param_95_1d":     round(var_param_95_1d, 2),
            "var_param_99_1d":     round(var_param_99_1d, 2),
            "var_param_95_10d":    round(var_param_95_1d * SQRT_10, 2),
            "var_param_99_10d":    round(var_param_99_1d * SQRT_10, 2),
            "es_hist_975_1d":      round(es_975, 2),
            "es_hist_99_1d":       round(es_99, 2),
            "vol_annualized_pct":  round(sigma_p * np.sqrt(252) * 100, 2),
            "beta_vs_nifty50_ew":  round(beta, 3) if not np.isnan(beta) else None,
            "max_drawdown_pct":    round(float(dd) * 100, 2),
        }

        sector_map = self._load_sector_map()
        comp_rows = [{
            "run_date":              self.run_date,
            "symbol":                s,
            "sector":                sector_map.get(s, "UNCATEGORIZED"),
            "qty":                   float(pos.loc[s, "qty"]),
            "last_close":            round(last_close[s], 2),
            "market_value":          round(float(mv[i]), 2),
            "weight_pct":            round(float(w[i]) * 100, 2),
            "standalone_vol_pct":    round(float(np.sqrt(sigma[i, i]) * np.sqrt(252)) * 100, 2),
            "component_var_95_1d":   round(float(comp_var_95[i]), 2),
            "risk_contribution_pct": round(float(risk_contrib_pct[i]), 2),
            "status":                "OK",
        } for i, s in enumerate(live_syms)]
        comp_rows += [{
            "run_date": self.run_date, "symbol": e["symbol"],
            "sector":   sector_map.get(e["symbol"], "UNCATEGORIZED"),
            "qty": None, "last_close": None, "market_value": None,
            "weight_pct": None, "standalone_vol_pct": None,
            "component_var_95_1d": None, "risk_contribution_pct": None,
            "status": f"EXCLUDED_{e['reason']}",
        } for e in self.excluded]

        return snapshot, pd.DataFrame(comp_rows, columns=COMPONENT_COLS)

    # ── Output ────────────────────────────────────────────────────────────────

    def _save(self, snapshot: dict, components: pd.DataFrame) -> None:
        if components.empty:                                    # G-D-03
            raise ValueError("Refusing to write empty components frame")

        # portfolio_risk.csv: append history, dedupe on run_date (G-D-05)
        row = pd.DataFrame([snapshot], columns=RISK_COLS)
        if RISK_CSV.exists():
            hist = pd.read_csv(RISK_CSV)
            hist = hist[hist["run_date"] != self.run_date]
            row = pd.concat([hist, row], ignore_index=True)
        self._atomic_write(row, RISK_CSV)

        # components: latest snapshot only
        self._atomic_write(components, COMPONENTS_CSV)

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    engine = PortfolioRiskEngine()
    ok = engine.run()
    sys.exit(0 if ok else 1)
