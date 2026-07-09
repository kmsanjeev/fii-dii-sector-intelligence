"""
Stress Test Engine
Phase R2 -- Historical scenario replay + hypothetical shocks on current holdings.

Historical scenarios: each holding's actual return over a named crisis window,
read from the per-symbol parquet cache (full history 1995+). Symbols that did
not trade in the window fall back to their sector's average return over the
window, then to the universe average -- the fallback level is reported per
position (basis: SYMBOL / SECTOR / MARKET), never hidden.

Hypothetical scenarios: sector-level shock maps applied to current positions
(default market shock for sectors not explicitly listed).

Reads (read-only, G-D-01):
  data/portfolio/positions.csv
  data/cache/stock_history/{SYMBOL}.parquet
  data/intelligence/bull_run_probability.csv     symbol -> sector
  data/NSE/indices/nifty_500_constituents.csv    fallback universe

Writes (atomic, G-D-02):
  data/intelligence/portfolio_stress.csv          scenario-level P&L summary
  data/intelligence/portfolio_stress_detail.csv   per-position per-scenario detail

Run:  py -3.11 -m engines.risk.stress_test_engine
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

POSITIONS_CSV  = cfg.DATA_DIR / "portfolio" / "positions.csv"
SECTOR_SRC_CSV = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
NIFTY500_CSV   = cfg.INDICES_DIR / "nifty_500_constituents.csv"

STRESS_CSV     = cfg.INTELLIGENCE_DIR / "portfolio_stress.csv"
DETAIL_CSV     = cfg.INTELLIGENCE_DIR / "portfolio_stress_detail.csv"

# ── Historical crisis windows (close-to-close, dates are NSE trading days) ────

HISTORICAL_SCENARIOS: dict[str, dict] = {
    "GFC_2008": {
        "label":  "2008 Global Financial Crisis (Lehman phase)",
        "start":  "2008-09-01",
        "end":    "2008-11-28",
    },
    "TAPER_2013": {
        "label":  "2013 Taper Tantrum (INR crisis)",
        "start":  "2013-05-22",
        "end":    "2013-08-28",
    },
    "ILFS_2018": {
        "label":  "2018 IL&FS Default (NBFC/midcap selloff)",
        "start":  "2018-08-31",
        "end":    "2018-10-26",
    },
    "COVID_2020": {
        "label":  "2020 Covid Crash",
        "start":  "2020-02-19",
        "end":    "2020-03-23",
    },
}

# ── Hypothetical sector-shock scenarios ───────────────────────────────────────
# "market" = default shock for any sector not explicitly listed.

HYPOTHETICAL_SCENARIOS: dict[str, dict] = {
    "MKT_DOWN_10": {
        "label":  "Broad market -10%",
        "market": -0.10,
        "sectors": {},
    },
    "MKT_DOWN_20": {
        "label":  "Broad market -20% (bear market entry)",
        "market": -0.20,
        "sectors": {},
    },
    "FII_EXODUS": {
        "label":  "FII outflow regime: financials/high-beta hit hardest",
        "market": -0.12,
        "sectors": {"BANKING": -0.20, "FINANCIAL SERVICES": -0.20, "NBFC": -0.25,
                    "REALTY": -0.22, "METALS": -0.18, "IT": -0.08},
    },
    "RATE_SHOCK": {
        "label":  "RBI +100bps surprise: rate-sensitives derate",
        "market": -0.06,
        "sectors": {"BANKING": -0.10, "NBFC": -0.15, "REALTY": -0.18,
                    "AUTO": -0.12, "INFRASTRUCTURE": -0.12, "FMCG": -0.02,
                    "PHARMA": -0.02, "IT": -0.04},
    },
}

MIN_POSITIONS = 1   # stress replay is meaningful even for one position

SUMMARY_COLS = [
    "run_date", "scenario", "scenario_type", "label", "window_start", "window_end",
    "portfolio_value", "pnl", "pnl_pct", "n_symbol_basis", "n_sector_basis",
    "n_market_basis", "worst_position", "worst_position_pct",
]
DETAIL_COLS = [
    "run_date", "scenario", "symbol", "sector", "market_value",
    "scenario_return_pct", "pnl", "basis",
]


class StressTestEngine:
    """Replays historical crises and hypothetical shocks on current holdings."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()
        self._close_cache: dict[str, pd.Series | None] = {}

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[StressTestEngine] Starting")
        positions = self._load_positions()
        if positions is None:
            logger.info("[StressTestEngine] Skipped -- no positions")
            return True   # empty portfolio is a valid state

        sector_map = self._load_sector_map()
        summary_rows: list[dict] = []
        detail_rows:  list[dict] = []

        for name, spec in HISTORICAL_SCENARIOS.items():
            s, d = self._run_historical(name, spec, positions, sector_map)
            if s is not None:
                summary_rows.append(s)
                detail_rows.extend(d)

        for name, spec in HYPOTHETICAL_SCENARIOS.items():
            s, d = self._run_hypothetical(name, spec, positions, sector_map)
            summary_rows.append(s)
            detail_rows.extend(d)

        if not summary_rows:
            logger.warning("[StressTestEngine] No scenarios produced output")
            return False

        self._save(pd.DataFrame(summary_rows, columns=SUMMARY_COLS),
                   pd.DataFrame(detail_rows, columns=DETAIL_COLS))
        logger.info("[StressTestEngine] Complete -- %d scenarios, %d position rows",
                    len(summary_rows), len(detail_rows))
        return True

    # ── Inputs ────────────────────────────────────────────────────────────────

    def _load_positions(self) -> pd.DataFrame | None:
        if not POSITIONS_CSV.exists():
            return None
        df = pd.read_csv(POSITIONS_CSV)
        if df.empty or len(df) < MIN_POSITIONS:
            return None
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df["qty"]    = pd.to_numeric(df["qty"], errors="coerce")
        df = df.dropna(subset=["symbol", "qty"])
        df = df[df["qty"] > 0]
        if df.empty:
            return None

        # Market value from latest cached close
        mvs = []
        for _, row in df.iterrows():
            s = self._closes(row["symbol"])
            mvs.append(float(row["qty"]) * float(s.iloc[-1]) if s is not None and len(s) else np.nan)
        df = df.assign(market_value=mvs).dropna(subset=["market_value"])
        return df if len(df) >= MIN_POSITIONS else None

    def _closes(self, symbol: str) -> pd.Series | None:
        """Full daily close history (date-indexed), memoized per run."""
        if symbol in self._close_cache:
            return self._close_cache[symbol]
        pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
        out: pd.Series | None = None
        if pq.exists():
            try:
                df = pd.read_parquet(pq, columns=["date", "close"])
                df["date"]  = pd.to_datetime(df["date"], errors="coerce")
                df["close"] = pd.to_numeric(df["close"], errors="coerce")
                df = df.dropna(subset=["date", "close"])
                df = df[df["close"] > 0]                       # G-P-01
                df = df.drop_duplicates(subset=["date"], keep="last").sort_values("date")
                if not df.empty:
                    out = df.set_index("date")["close"]
            except Exception as e:
                logger.warning("[StressTestEngine] Bad parquet for %s: %s", symbol, e)
        self._close_cache[symbol] = out
        return out

    def _load_sector_map(self) -> dict[str, str]:
        if not SECTOR_SRC_CSV.exists():
            return {}
        try:
            df = pd.read_csv(SECTOR_SRC_CSV, usecols=["symbol", "sector"])
            df["symbol"] = df["symbol"].str.strip().str.upper()
            return df.set_index("symbol")["sector"].fillna("UNCATEGORIZED").to_dict()
        except Exception:
            return {}

    def _universe_symbols(self) -> list[str]:
        if not NIFTY500_CSV.exists():
            return []
        try:
            return pd.read_csv(NIFTY500_CSV)["symbol"].str.strip().str.upper().tolist()
        except Exception:
            return []

    # ── Historical replay ─────────────────────────────────────────────────────

    def _window_return(self, symbol: str, start: str, end: str) -> float | None:
        """Close-to-close return over [start, end]; None if symbol lacks coverage."""
        s = self._closes(symbol)
        if s is None:
            return None
        window = s.loc[start:end]
        # Require data spanning most of the window, not just a sliver at one edge
        if len(window) < 10:
            return None
        return float(window.iloc[-1] / window.iloc[0] - 1.0)

    def _run_historical(self, name: str, spec: dict, positions: pd.DataFrame,
                        sector_map: dict) -> tuple[dict | None, list[dict]]:
        start, end = spec["start"], spec["end"]

        # Build sector-average and market-average fallbacks from the NIFTY 500
        # universe (today's constituents -- survivorship-biased approximation,
        # acceptable for a fallback that is explicitly labelled).
        sector_rets: dict[str, list[float]] = {}
        market_rets: list[float] = []
        for sym in self._universe_symbols():
            r = self._window_return(sym, start, end)
            if r is None:
                continue
            market_rets.append(r)
            sec = sector_map.get(sym, "UNCATEGORIZED")
            sector_rets.setdefault(sec, []).append(r)

        if len(market_rets) < 30:
            logger.warning("[StressTestEngine] %s: only %d universe symbols cover the window -- skipping",
                           name, len(market_rets))
            return None, []

        sector_avg = {k: float(np.mean(v)) for k, v in sector_rets.items() if len(v) >= 3}
        market_avg = float(np.mean(market_rets))

        details: list[dict] = []
        n_sym = n_sec = n_mkt = 0
        for _, row in positions.iterrows():
            sym, mv = row["symbol"], float(row["market_value"])
            sec = sector_map.get(sym, "UNCATEGORIZED")
            r = self._window_return(sym, start, end)
            if r is not None:
                basis = "SYMBOL"; n_sym += 1
            elif sec in sector_avg:
                r = sector_avg[sec]; basis = "SECTOR"; n_sec += 1
            else:
                r = market_avg; basis = "MARKET"; n_mkt += 1
            details.append({
                "run_date": self.run_date, "scenario": name, "symbol": sym,
                "sector": sec, "market_value": round(mv, 2),
                "scenario_return_pct": round(r * 100, 2),
                "pnl": round(mv * r, 2), "basis": basis,
            })

        return self._summarize(name, "HISTORICAL", spec["label"], start, end,
                               positions, details), details

    # ── Hypothetical shocks ───────────────────────────────────────────────────

    def _run_hypothetical(self, name: str, spec: dict, positions: pd.DataFrame,
                          sector_map: dict) -> tuple[dict, list[dict]]:
        details: list[dict] = []
        for _, row in positions.iterrows():
            sym, mv = row["symbol"], float(row["market_value"])
            sec = sector_map.get(sym, "UNCATEGORIZED")
            r = spec["sectors"].get(sec, spec["market"])
            details.append({
                "run_date": self.run_date, "scenario": name, "symbol": sym,
                "sector": sec, "market_value": round(mv, 2),
                "scenario_return_pct": round(r * 100, 2),
                "pnl": round(mv * r, 2),
                "basis": "SECTOR_SHOCK" if sec in spec["sectors"] else "MARKET_SHOCK",
            })
        return self._summarize(name, "HYPOTHETICAL", spec["label"], "", "",
                               positions, details), details

    # ── Aggregation / output ──────────────────────────────────────────────────

    def _summarize(self, name: str, stype: str, label: str, start: str, end: str,
                   positions: pd.DataFrame, details: list[dict]) -> dict:
        V   = float(positions["market_value"].sum())
        pnl = float(sum(d["pnl"] for d in details))
        worst = min(details, key=lambda d: d["pnl"]) if details else None
        basis_counts = pd.Series([d["basis"] for d in details]).value_counts()
        return {
            "run_date":           self.run_date,
            "scenario":           name,
            "scenario_type":      stype,
            "label":              label,
            "window_start":       start,
            "window_end":         end,
            "portfolio_value":    round(V, 2),
            "pnl":                round(pnl, 2),
            "pnl_pct":            round(pnl / V * 100, 2) if V else 0.0,
            "n_symbol_basis":     int(basis_counts.get("SYMBOL", 0)),
            "n_sector_basis":     int(basis_counts.get("SECTOR", 0) + basis_counts.get("SECTOR_SHOCK", 0)),
            "n_market_basis":     int(basis_counts.get("MARKET", 0) + basis_counts.get("MARKET_SHOCK", 0)),
            "worst_position":     worst["symbol"] if worst else "",
            "worst_position_pct": worst["scenario_return_pct"] if worst else 0.0,
        }

    def _save(self, summary: pd.DataFrame, detail: pd.DataFrame) -> None:
        if summary.empty:                                       # G-D-03
            raise ValueError("Refusing to write empty stress summary")
        self._atomic_write(summary, STRESS_CSV)
        self._atomic_write(detail, DETAIL_CSV)

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    engine = StressTestEngine()
    ok = engine.run()
    sys.exit(0 if ok else 1)
