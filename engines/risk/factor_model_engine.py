"""
Factor Model Engine (Barra-lite)
Phase R2 -- Cross-sectional factor model: sector + style factor returns,
portfolio risk decomposition into systematic vs idiosyncratic.

Model:
  r_it = sum_k X_ik * f_kt + e_it
  Factors: sector one-hots (from classification) + 3 style factors
    MOMENTUM : z-score of 90d return
    SIZE     : z-score of log(median 60d traded value)  [liquidity-based size]
    VALUE    : z-score of earnings yield (1 / pe_ratio); missing PE -> 0 (neutral)

Barra-lite simplifications (documented, deliberate):
  - Exposures X are CURRENT and held static across the estimation window
    (true Barra re-estimates daily; error is second-order for a 250d window)
  - Estimation universe: NIFTY 500 constituents with sufficient history
  - OLS (equal-weighted) cross-sections, solved for all days in one lstsq
  - Factor covariance: Ledoit-Wolf shrinkage on the factor-return series

Portfolio decomposition (when positions exist):
  x = sum_i w_i X_i                      portfolio factor exposures
  systematic var = x' F x                (F = factor covariance, daily)
  idiosyncratic  = sum_i w_i^2 s_i^2     (s_i = residual vol of holding i)

Reads (read-only, G-D-01):
  data/NSE/indices/nifty_500_constituents.csv
  data/cache/stock_history/{SYMBOL}.parquet
  data/intelligence/bull_run_probability.csv     symbol -> sector
  data/NSE/results/valuation_scores.csv          pe_ratio for VALUE factor
  data/portfolio/positions.csv

Writes (atomic, G-D-02):
  data/intelligence/factor_returns.csv               date x factor daily returns
  data/intelligence/portfolio_factor_exposure.csv    per-factor exposure + contribution
  data/intelligence/factor_model_summary.csv         run-level fit + decomposition

Run:  py -3.11 -m engines.risk.factor_model_engine
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

NIFTY500_CSV   = cfg.INDICES_DIR / "nifty_500_constituents.csv"
SECTOR_SRC_CSV = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
VALUATION_CSV  = cfg.RESULTS_DIR / "valuation_scores.csv"
POSITIONS_CSV  = cfg.DATA_DIR / "portfolio" / "positions.csv"

FACTOR_RETURNS_CSV  = cfg.INTELLIGENCE_DIR / "factor_returns.csv"
EXPOSURE_CSV        = cfg.INTELLIGENCE_DIR / "portfolio_factor_exposure.csv"
SUMMARY_CSV         = cfg.INTELLIGENCE_DIR / "factor_model_summary.csv"

# ── Parameters ────────────────────────────────────────────────────────────────

LOOKBACK_DAYS    = 250
MIN_HISTORY_DAYS = 120    # universe symbol must cover this much of the window
MIN_UNIVERSE     = 100    # abort if fewer usable symbols than this
STYLE_FACTORS    = ["MOMENTUM", "SIZE", "VALUE"]

SUMMARY_COLS = [
    "run_date", "universe_size", "n_factors", "common_days", "mean_daily_r2",
    "portfolio_value", "n_positions_modeled", "total_vol_annualized_pct",
    "systematic_vol_pct", "idiosyncratic_vol_pct", "systematic_share_pct",
]
EXPOSURE_COLS = [
    "run_date", "factor", "factor_type", "exposure",
    "factor_vol_annualized_pct", "var_contribution_pct",
]


class FactorModelEngine:
    """Estimates sector+style factor returns and decomposes portfolio risk."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[FactorModelEngine] Starting")

        returns, symbols = self._build_universe_returns()
        if returns is None:
            logger.warning("[FactorModelEngine] Aborted -- universe too small")
            return False

        sector_map = self._load_sector_map()
        X, factor_names, factor_types = self._build_exposures(symbols, returns, sector_map)

        # Solve all cross-sections at once: F = pinv(X) @ R'   -> (K, T)
        R = returns.values                       # (T, N)
        pinvX = np.linalg.pinv(X)                # (K, N)
        F = pinvX @ R.T                          # (K, T)
        E = R.T - X @ F                          # (N, T) residuals

        # Fit quality: mean cross-sectional R^2
        ss_res = (E ** 2).sum(axis=0)
        ss_tot = ((R.T - R.T.mean(axis=0)) ** 2).sum(axis=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            daily_r2 = 1.0 - np.where(ss_tot > 0, ss_res / ss_tot, np.nan)
        mean_r2 = float(np.nanmean(daily_r2))
        logger.info("[FactorModelEngine] Universe=%d, factors=%d, days=%d, mean R2=%.3f",
                    len(symbols), len(factor_names), returns.shape[0], mean_r2)

        factor_returns = pd.DataFrame(F.T, index=returns.index, columns=factor_names)

        # Factor covariance (daily) with Ledoit-Wolf shrinkage
        from sklearn.covariance import LedoitWolf
        F_cov = LedoitWolf().fit(factor_returns.values).covariance_   # (K, K)
        idio_var = E.var(axis=1)                                       # (N,) daily

        # Portfolio decomposition (optional -- portfolio may be empty)
        port = self._decompose_portfolio(symbols, X, F_cov, idio_var,
                                         factor_names, factor_types, sector_map)

        summary = {
            "run_date":                  self.run_date,
            "universe_size":             len(symbols),
            "n_factors":                 len(factor_names),
            "common_days":               int(returns.shape[0]),
            "mean_daily_r2":             round(mean_r2, 4),
            "portfolio_value":           port["value"] if port else None,
            "n_positions_modeled":       port["n_modeled"] if port else 0,
            "total_vol_annualized_pct":  port["total_vol"] if port else None,
            "systematic_vol_pct":        port["sys_vol"] if port else None,
            "idiosyncratic_vol_pct":     port["idio_vol"] if port else None,
            "systematic_share_pct":      port["sys_share"] if port else None,
        }

        self._save(factor_returns, summary,
                   port["exposures"] if port else pd.DataFrame(columns=EXPOSURE_COLS))
        logger.info("[FactorModelEngine] Complete -- %s",
                    f"portfolio systematic share {port['sys_share']}%" if port else "no portfolio")
        return True

    # ── Universe returns matrix ───────────────────────────────────────────────

    def _load_close_series(self, symbol: str) -> pd.Series | None:
        pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
        if not pq.exists():
            return None
        try:
            df = pd.read_parquet(pq, columns=["date", "close", "volume"])
        except Exception:
            try:   # some cache files may lack volume
                df = pd.read_parquet(pq, columns=["date", "close"])
                df["volume"] = np.nan
            except Exception:
                return None
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"])
        df = df[df["close"] > 0]                                # G-P-01
        df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
        if df.empty:
            return None
        s = df.set_index("date")["close"]
        s.attrs["traded_value"] = float(
            (df["close"] * pd.to_numeric(df["volume"], errors="coerce"))
            .tail(60).median()
        ) if df["volume"].notna().any() else np.nan
        return s

    def _build_universe_returns(self) -> tuple[pd.DataFrame | None, list[str]]:
        if not NIFTY500_CSV.exists():
            return None, []
        universe = pd.read_csv(NIFTY500_CSV)["symbol"].str.strip().str.upper().tolist()

        series: dict[str, pd.Series] = {}
        self._traded_value: dict[str, float] = {}
        for sym in universe:
            s = self._load_close_series(sym)
            if s is None:
                continue
            s = s.tail(LOOKBACK_DAYS + 1)
            if len(s) < MIN_HISTORY_DAYS:
                continue
            series[sym] = s
            self._traded_value[sym] = s.attrs.get("traded_value", np.nan)

        if len(series) < MIN_UNIVERSE:
            return None, []

        closes = pd.DataFrame(series)
        # Align on dates where at least 90% of symbols traded, then drop
        # symbols that still have gaps (keeps the matrix dense, no fills G-I-04)
        closes = closes[closes.notna().mean(axis=1) >= 0.90]
        closes = closes.dropna(axis=1)
        returns = closes.pct_change().dropna(how="any")
        return returns, list(returns.columns)

    # ── Exposure matrix ───────────────────────────────────────────────────────

    def _load_sector_map(self) -> dict[str, str]:
        if not SECTOR_SRC_CSV.exists():
            return {}
        try:
            df = pd.read_csv(SECTOR_SRC_CSV, usecols=["symbol", "sector"])
            df["symbol"] = df["symbol"].str.strip().str.upper()
            return df.set_index("symbol")["sector"].fillna("UNCATEGORIZED").to_dict()
        except Exception:
            return {}

    def _load_earnings_yield(self) -> dict[str, float]:
        if not VALUATION_CSV.exists():
            return {}
        try:
            df = pd.read_csv(VALUATION_CSV, usecols=["symbol", "pe_ratio"])
            df["symbol"]   = df["symbol"].str.strip().str.upper()
            df["pe_ratio"] = pd.to_numeric(df["pe_ratio"], errors="coerce")
            df = df[df["pe_ratio"] > 0]
            return (1.0 / df.set_index("symbol")["pe_ratio"]).to_dict()
        except Exception:
            return {}

    @staticmethod
    def _zscore(values: np.ndarray) -> np.ndarray:
        """Cross-sectional z-score; NaN -> 0 (neutral exposure), clipped +/-3."""
        v = values.astype(float)
        mask = np.isfinite(v)
        if mask.sum() < 10:
            return np.zeros_like(v)
        mu, sd = v[mask].mean(), v[mask].std()
        z = np.where(mask & (sd > 0), (v - mu) / (sd if sd > 0 else 1.0), 0.0)
        return np.clip(np.nan_to_num(z, nan=0.0), -3.0, 3.0)

    def _build_exposures(self, symbols: list[str], returns: pd.DataFrame,
                         sector_map: dict) -> tuple[np.ndarray, list[str], dict]:
        n = len(symbols)

        # Sector one-hots
        sectors = [sector_map.get(s, "UNCATEGORIZED") for s in symbols]
        sector_names = sorted(set(sectors))
        S = np.zeros((n, len(sector_names)))
        for i, sec in enumerate(sectors):
            S[i, sector_names.index(sec)] = 1.0

        # MOMENTUM: 90d return
        mom_raw = np.array([
            returns[s].tail(90).add(1.0).prod() - 1.0 if len(returns[s]) >= 90 else np.nan
            for s in symbols
        ])
        # SIZE: log median 60d traded value
        size_raw = np.array([
            np.log(self._traded_value.get(s, np.nan))
            if (self._traded_value.get(s) or 0) > 0 else np.nan
            for s in symbols
        ])
        # VALUE: earnings yield
        ey = self._load_earnings_yield()
        val_raw = np.array([ey.get(s, np.nan) for s in symbols])

        styles = np.column_stack([
            self._zscore(mom_raw), self._zscore(size_raw), self._zscore(val_raw),
        ])

        X = np.hstack([S, styles])
        factor_names = sector_names + STYLE_FACTORS
        factor_types = {f: ("SECTOR" if f in sector_names else "STYLE") for f in factor_names}
        self._exposure_lookup = {s: X[i] for i, s in enumerate(symbols)}
        return X, factor_names, factor_types

    # ── Portfolio decomposition ───────────────────────────────────────────────

    def _decompose_portfolio(self, symbols: list[str], X: np.ndarray,
                             F_cov: np.ndarray, idio_var: np.ndarray,
                             factor_names: list[str], factor_types: dict,
                             sector_map: dict) -> dict | None:
        if not POSITIONS_CSV.exists():
            return None
        pos = pd.read_csv(POSITIONS_CSV)
        if pos.empty:
            return None
        pos["symbol"] = pos["symbol"].str.strip().str.upper()
        pos["qty"]    = pd.to_numeric(pos["qty"], errors="coerce")
        pos = pos.dropna(subset=["symbol", "qty"])
        pos = pos[pos["qty"] > 0]

        sym_index = {s: i for i, s in enumerate(symbols)}
        mvs, idx = [], []
        for _, row in pos.iterrows():
            s = row["symbol"]
            if s not in sym_index:
                logger.warning("[FactorModelEngine] %s not in factor universe -- excluded from decomposition", s)
                continue
            i = sym_index[s]
            # market value from last close via returns matrix is unavailable here;
            # approximate weight base with invested value if close missing
            pq = cfg.STOCK_HISTORY_CACHE / f"{s}.parquet"
            try:
                last_close = float(pd.read_parquet(pq, columns=["close"])["close"].iloc[-1])
            except Exception:
                continue
            mvs.append(float(row["qty"]) * last_close)
            idx.append(i)

        if len(idx) < 1:
            return None

        mv = np.array(mvs)
        V  = float(mv.sum())
        w  = mv / V

        Xp = X[idx]                              # (P, K)
        x  = w @ Xp                              # (K,) portfolio exposures

        sys_var  = float(x @ F_cov @ x)          # daily
        idio_v   = float((w ** 2 * idio_var[idx]).sum())
        total    = sys_var + idio_v
        ann      = np.sqrt(252) * 100

        # Per-factor variance contribution (Euler on systematic part)
        marginal = F_cov @ x
        contrib  = x * marginal / total * 100 if total > 0 else np.zeros_like(x)
        factor_vol = np.sqrt(np.diag(F_cov)) * ann

        rows = [{
            "run_date":                   self.run_date,
            "factor":                     f,
            "factor_type":                factor_types[f],
            "exposure":                   round(float(x[k]), 4),
            "factor_vol_annualized_pct":  round(float(factor_vol[k]), 2),
            "var_contribution_pct":       round(float(contrib[k]), 2),
        } for k, f in enumerate(factor_names) if abs(x[k]) > 1e-6]

        return {
            "value":     round(V, 2),
            "n_modeled": len(idx),
            "total_vol": round(float(np.sqrt(total)) * ann, 2),
            "sys_vol":   round(float(np.sqrt(sys_var)) * ann, 2),
            "idio_vol":  round(float(np.sqrt(idio_v)) * ann, 2),
            "sys_share": round(sys_var / total * 100, 1) if total > 0 else 0.0,
            "exposures": pd.DataFrame(rows, columns=EXPOSURE_COLS),
        }

    # ── Output ────────────────────────────────────────────────────────────────

    def _save(self, factor_returns: pd.DataFrame, summary: dict,
              exposures: pd.DataFrame) -> None:
        if factor_returns.empty:                                # G-D-03
            raise ValueError("Refusing to write empty factor returns")

        fr = factor_returns.round(6).reset_index().rename(columns={"index": "date"})
        fr["date"] = pd.to_datetime(fr["date"]).dt.strftime("%Y-%m-%d")
        self._atomic_write(fr, FACTOR_RETURNS_CSV)

        row = pd.DataFrame([summary], columns=SUMMARY_COLS)
        if SUMMARY_CSV.exists():                                # G-D-05 dedupe
            hist = pd.read_csv(SUMMARY_CSV)
            hist = hist[hist["run_date"] != self.run_date]
            row = pd.concat([hist, row], ignore_index=True)
        self._atomic_write(row, SUMMARY_CSV)

        # Exposures may legitimately be empty (no portfolio) -- write header-only
        self._atomic_write(exposures, EXPOSURE_CSV)

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    engine = FactorModelEngine()
    ok = engine.run()
    sys.exit(0 if ok else 1)
