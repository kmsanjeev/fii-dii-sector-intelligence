"""
Monte Carlo Simulation Engine
Phase R3 -- Correlated Monte Carlo VaR/ES for the current portfolio.

Method:
  - Daily LOG returns over 500d from the parquet cache (log scale is the
    natural space for multi-day compounding)
  - Ledoit-Wolf shrunk covariance, Cholesky factorization
  - Zero drift (standard short-horizon VaR convention -- expected return
    over 1-10 days is noise relative to vol and would flatter the numbers)
  - Simulate H daily steps per path, compound: true 10-day distribution,
    not the sqrt(10) scaling approximation used in Phase R1
  - Antithetic variates: each chunk generates n/2 normals and mirrors them
    (halves Monte Carlo error for symmetric estimators at same compute)
  - Deterministic seeding: chunk seed = base_seed + chunk_id -> bit-for-bit
    reproducible runs, auditable results

Distributed seam (Phase R3 contract):
  _orchestrate()     splits N paths into chunk specs      [master node]
  _simulate_chunk()  stateless: spec dict -> P&L array    [future worker]
  _aggregate()       reassembles distribution + metrics   [aggregator]
  Today all three run in-process; lifting _simulate_chunk into a queue
  worker (Redis Streams / RQ) is a deployment change, not a rewrite.

Reads (read-only, G-D-01):
  data/portfolio/positions.csv
  data/cache/stock_history/{SYMBOL}.parquet

Writes (atomic, G-D-02):
  data/intelligence/portfolio_mc_var.csv           per run_date x horizon summary
  data/intelligence/portfolio_mc_distribution.csv  histogram bins for GUI

Run:  py -3.11 -m engines.risk.monte_carlo_engine
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

POSITIONS_CSV = cfg.DATA_DIR / "portfolio" / "positions.csv"

MC_VAR_CSV    = cfg.INTELLIGENCE_DIR / "portfolio_mc_var.csv"
MC_DIST_CSV   = cfg.INTELLIGENCE_DIR / "portfolio_mc_distribution.csv"

# ── Parameters ────────────────────────────────────────────────────────────────

LOOKBACK_DAYS   = 500
MIN_COMMON_DAYS = 60
MIN_POSITIONS   = 2

DEFAULT_PATHS   = 100_000
CHUNK_SIZE      = 10_000     # paths per worker chunk (must be even: antithetic)
BASE_SEED       = 20260709   # fixed default -> reproducible daily runs
HORIZONS        = [1, 10]    # trading days
HIST_BINS       = 60

SUMMARY_COLS = [
    "run_date", "horizon_days", "n_paths", "seed", "portfolio_value",
    "n_positions", "common_days",
    "mc_var_95", "mc_var_99", "mc_es_975", "mc_es_99",
    "pnl_mean", "pnl_std", "pnl_p01", "pnl_p05", "pnl_p50", "pnl_p95", "pnl_p99",
]
DIST_COLS = ["run_date", "horizon_days", "bin_left", "bin_right", "count"]


class MonteCarloEngine:
    """Correlated Monte Carlo VaR for current holdings, chunked for future scale-out."""

    def __init__(self, n_paths: int = DEFAULT_PATHS, seed: int = BASE_SEED):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()
        # Even path count required by antithetic mirroring
        self.n_paths = max(2, n_paths - n_paths % 2)
        self.seed = seed
        self.excluded: list[str] = []

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[MonteCarloEngine] Starting -- %d paths, seed %d", self.n_paths, self.seed)
        model = self._build_model()
        if model is None:
            logger.info("[MonteCarloEngine] Skipped -- portfolio too small or insufficient history")
            return True   # empty/too-small portfolio is a valid state

        summaries, dist_rows = [], []
        for horizon in HORIZONS:
            pnl = self._aggregate(self._orchestrate(model, horizon))
            summaries.append(self._metrics(model, horizon, pnl))
            dist_rows.extend(self._histogram(horizon, pnl))
            logger.info("[MonteCarloEngine] H=%dd: VaR95=%.0f VaR99=%.0f ES97.5=%.0f",
                        horizon, summaries[-1]["mc_var_95"],
                        summaries[-1]["mc_var_99"], summaries[-1]["mc_es_975"])

        self._save(pd.DataFrame(summaries, columns=SUMMARY_COLS),
                   pd.DataFrame(dist_rows, columns=DIST_COLS))
        logger.info("[MonteCarloEngine] Complete -- %d horizons on %.0f INR portfolio",
                    len(HORIZONS), summaries[0]["portfolio_value"])
        return True

    # ── Model construction (shared with R1's loaders in spirit) ───────────────

    def _load_close_series(self, symbol: str) -> pd.Series | None:
        pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
        if not pq.exists():
            return None
        try:
            df = pd.read_parquet(pq, columns=["date", "close"])
        except Exception:
            return None
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"])
        df = df[df["close"] > 0]                                # G-P-01
        df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
        return df.set_index("date")["close"] if not df.empty else None

    def _build_model(self) -> dict | None:
        """Positions + Cholesky factor of the shrunk log-return covariance."""
        if not POSITIONS_CSV.exists():
            return None
        pos = pd.read_csv(POSITIONS_CSV)
        if pos.empty or len(pos) < MIN_POSITIONS:
            return None
        pos["symbol"] = pos["symbol"].str.strip().str.upper()
        pos["qty"]    = pd.to_numeric(pos["qty"], errors="coerce")
        pos = pos.dropna(subset=["symbol", "qty"])
        pos = pos[pos["qty"] > 0]

        series: dict[str, pd.Series] = {}
        for sym in pos["symbol"]:
            s = self._load_close_series(sym)
            if s is None or len(s) < MIN_COMMON_DAYS + 1:
                self.excluded.append(sym)
                continue
            series[sym] = s.tail(LOOKBACK_DAYS + 1)

        if len(series) < MIN_POSITIONS:
            return None

        closes = pd.DataFrame(series).dropna(how="any")         # G-I-04: drop, never fill
        log_rets = np.log(closes / closes.shift(1)).dropna(how="any")
        if len(log_rets) < MIN_COMMON_DAYS:
            return None

        symbols = list(log_rets.columns)
        posx = pos.set_index("symbol").loc[symbols]
        mv = np.array([float(posx.loc[s, "qty"]) * float(series[s].iloc[-1]) for s in symbols])
        V = float(mv.sum())
        if V <= 0:
            return None

        from sklearn.covariance import LedoitWolf
        sigma = LedoitWolf().fit(log_rets.values).covariance_
        try:
            L = np.linalg.cholesky(sigma)
        except np.linalg.LinAlgError:
            # Shrinkage should prevent this; jitter as last resort
            L = np.linalg.cholesky(sigma + 1e-10 * np.eye(len(symbols)))
            logger.warning("[MonteCarloEngine] Covariance needed jitter for Cholesky")

        return {
            "symbols": symbols, "mv": mv, "V": V, "L": L,
            "n_assets": len(symbols), "common_days": int(len(log_rets)),
        }

    # ── Distributed seam: orchestrator -> workers -> aggregator ──────────────

    def _orchestrate(self, model: dict, horizon: int) -> list[np.ndarray]:
        """Master node: split N paths into chunk specs and run the workers.
        In the distributed target architecture this publishes specs to a queue;
        here it maps them over the in-process worker."""
        specs = []
        remaining, chunk_id = self.n_paths, 0
        while remaining > 0:
            n = min(CHUNK_SIZE, remaining)
            n -= n % 2                       # antithetic needs even counts
            if n == 0:
                break
            specs.append({
                "chunk_id":  chunk_id,
                "n_paths":   n,
                "horizon":   horizon,
                "seed":      self.seed + horizon * 1_000_003 + chunk_id,
                "L":         model["L"],
                "mv":        model["mv"],
            })
            remaining -= n
            chunk_id += 1
        return [self._simulate_chunk(spec) for spec in specs]

    @staticmethod
    def _simulate_chunk(spec: dict) -> np.ndarray:
        """Stateless worker: fully self-contained spec -> P&L array (INR).

        This is the unit that moves onto a compute grid in the distributed
        architecture: it holds no engine state, derives its RNG entirely from
        the spec seed, and returns a plain array.
        """
        rng  = np.random.default_rng(spec["seed"])
        L    = spec["L"]                     # (N, N) Cholesky factor, daily
        mv   = spec["mv"]                    # (N,) position market values
        H    = spec["horizon"]
        half = spec["n_paths"] // 2
        n_assets = L.shape[0]

        # Antithetic: draw half, mirror the other half
        z = rng.standard_normal((half, H, n_assets))
        z = np.concatenate([z, -z], axis=0)              # (paths, H, N)

        # Correlated daily log returns (zero drift), compounded over horizon
        daily_log = z @ L.T                              # (paths, H, N)
        cum_log   = daily_log.sum(axis=1)                # (paths, N)
        pnl = (np.exp(cum_log) - 1.0) @ mv               # (paths,) INR
        return pnl

    @staticmethod
    def _aggregate(chunks: list[np.ndarray]) -> np.ndarray:
        """Aggregator: reassemble the full P&L distribution."""
        return np.concatenate(chunks)

    # ── Metrics / output ──────────────────────────────────────────────────────

    def _metrics(self, model: dict, horizon: int, pnl: np.ndarray) -> dict:
        p = np.percentile(pnl, [1, 2.5, 5, 50, 95, 99])
        tail_975 = pnl[pnl <= p[1]]
        tail_99  = pnl[pnl <= p[0]]
        return {
            "run_date":        self.run_date,
            "horizon_days":    horizon,
            "n_paths":         int(len(pnl)),
            "seed":            self.seed,
            "portfolio_value": round(model["V"], 2),
            "n_positions":     model["n_assets"],
            "common_days":     model["common_days"],
            "mc_var_95":       round(float(-p[2]), 2),
            "mc_var_99":       round(float(-p[0]), 2),
            "mc_es_975":       round(float(-tail_975.mean()), 2),
            "mc_es_99":        round(float(-tail_99.mean()), 2),
            "pnl_mean":        round(float(pnl.mean()), 2),
            "pnl_std":         round(float(pnl.std()), 2),
            "pnl_p01":         round(float(p[0]), 2),
            "pnl_p05":         round(float(p[2]), 2),
            "pnl_p50":         round(float(p[3]), 2),
            "pnl_p95":         round(float(p[4]), 2),
            "pnl_p99":         round(float(p[5]), 2),
        }

    def _histogram(self, horizon: int, pnl: np.ndarray) -> list[dict]:
        # Clip histogram range to p0.1-p99.9 so a single extreme path
        # cannot flatten the visible distribution
        lo, hi = np.percentile(pnl, [0.1, 99.9])
        counts, edges = np.histogram(pnl, bins=HIST_BINS, range=(lo, hi))
        return [{
            "run_date":     self.run_date,
            "horizon_days": horizon,
            "bin_left":     round(float(edges[i]), 2),
            "bin_right":    round(float(edges[i + 1]), 2),
            "count":        int(counts[i]),
        } for i in range(len(counts))]

    def _save(self, summary: pd.DataFrame, dist: pd.DataFrame) -> None:
        if summary.empty:                                       # G-D-03
            raise ValueError("Refusing to write empty MC summary")

        # Summary: append history, dedupe on (run_date, horizon)  (G-D-05)
        if MC_VAR_CSV.exists():
            hist = pd.read_csv(MC_VAR_CSV)
            hist = hist[hist["run_date"] != self.run_date]
            summary = pd.concat([hist, summary], ignore_index=True)
        self._atomic_write(summary, MC_VAR_CSV)

        # Distribution: latest run only
        self._atomic_write(dist, MC_DIST_CSV)

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATHS
    engine = MonteCarloEngine(n_paths=n)
    ok = engine.run()
    sys.exit(0 if ok else 1)
