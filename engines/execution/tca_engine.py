"""
TCA Engine (Transaction Cost Analysis) -- Phase R4
Slippage per filled order against three benchmarks, plus aggregates.

Benchmarks (per fill):
  ARRIVAL   arrival_price captured at order placement (LTP at decision time).
            Pre-R4 orders have arrival_price=0 -> benchmark reported as
            NO_ARRIVAL, never guessed.
  VWAP      day VWAP proxy = (High+Low+Close)/3 of the fill date. The parquet
            cache carries no turnover column, so true VWAP is unavailable --
            the HLC/3 proxy is standard and explicitly labeled vwap_hlc3.
  CLOSE     same-day close.

Sign convention: positive bps = execution COST (bought above / sold below
the benchmark). cost_inr = signed cost in rupees for the filled quantity.

Reads (read-only, G-D-01):
  data/execution/orders.csv
  data/cache/stock_history/{SYMBOL}.parquet

Writes (atomic, G-D-02):
  data/intelligence/tca_report.csv    per-fill slippage detail
  data/intelligence/tca_summary.csv   aggregates per run (deduped by run_date)

Run:  py -3.11 -m engines.execution.tca_engine
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

ORDERS_CSV  = cfg.DATA_DIR / "execution" / "orders.csv"
REPORT_CSV  = cfg.INTELLIGENCE_DIR / "tca_report.csv"
SUMMARY_CSV = cfg.INTELLIGENCE_DIR / "tca_summary.csv"

REPORT_COLS = [
    "order_id", "fill_date", "symbol", "action", "filled_qty", "avg_fill_price",
    "order_type", "paper", "arrival_price", "vwap_hlc3", "day_close",
    "slip_arrival_bps", "slip_vwap_bps", "slip_close_bps",
    "cost_arrival_inr", "cost_vwap_inr", "benchmark_status",
]
SUMMARY_COLS = [
    "run_date", "n_fills", "n_with_arrival", "total_traded_value",
    "mean_slip_arrival_bps", "median_slip_arrival_bps", "total_cost_arrival_inr",
    "mean_slip_vwap_bps", "median_slip_vwap_bps", "total_cost_vwap_inr",
    "buy_mean_vwap_bps", "sell_mean_vwap_bps", "worst_fill_order_id", "worst_fill_bps",
]


class TCAEngine:
    """Computes execution slippage for every filled order in the blotter."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()
        self._day_cache: dict[str, pd.DataFrame | None] = {}

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[TCAEngine] Starting")
        fills = self._load_fills()
        if fills is None or fills.empty:
            logger.info("[TCAEngine] Skipped -- no filled orders in blotter")
            return True   # empty blotter is a valid state

        report = self._analyze(fills)
        if report.empty:
            logger.warning("[TCAEngine] No fills could be benchmarked")
            return True

        summary = self._summarize(report)
        self._save(report, summary)
        logger.info("[TCAEngine] Complete -- %d fills, mean VWAP slippage %.1f bps",
                    len(report), summary["mean_slip_vwap_bps"])
        return True

    # ── Inputs ────────────────────────────────────────────────────────────────

    def _load_fills(self) -> pd.DataFrame | None:
        if not ORDERS_CSV.exists():
            return None
        df = pd.read_csv(ORDERS_CSV)
        if df.empty:
            return None
        df = df[df["status"] == "FILLED"].copy()
        if df.empty:
            return None
        df["symbol"]         = df["symbol"].str.strip().str.upper()
        df["filled_qty"]     = pd.to_numeric(df["filled_qty"], errors="coerce")
        df["avg_fill_price"] = pd.to_numeric(df["avg_fill_price"], errors="coerce")
        df["arrival_price"]  = pd.to_numeric(df.get("arrival_price", 0), errors="coerce").fillna(0)
        df = df.dropna(subset=["filled_qty", "avg_fill_price"])
        df = df[(df["filled_qty"] > 0) & (df["avg_fill_price"] > 0)]
        df["fill_date"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True) \
                            .dt.tz_convert("Asia/Kolkata").dt.strftime("%Y-%m-%d")
        return df.dropna(subset=["fill_date"])

    def _day_bar(self, symbol: str, day: str) -> dict | None:
        """OHLC of the fill date (exact date only -- no nearest-day guessing)."""
        if symbol not in self._day_cache:
            pq = cfg.STOCK_HISTORY_CACHE / f"{symbol}.parquet"
            df = None
            if pq.exists():
                try:
                    df = pd.read_parquet(pq, columns=["date", "high", "low", "close"])
                    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
                    df = df.set_index("date")
                except Exception:
                    df = None
            self._day_cache[symbol] = df
        df = self._day_cache[symbol]
        if df is None or day not in df.index:
            return None
        row = df.loc[day]
        try:
            h, l, c = float(row["high"]), float(row["low"]), float(row["close"])
        except (TypeError, ValueError):
            return None
        if min(h, l, c) <= 0:
            return None
        return {"vwap_hlc3": (h + l + c) / 3.0, "close": c}

    # ── Core analysis ─────────────────────────────────────────────────────────

    @staticmethod
    def _slip_bps(fill: float, bench: float, action: str) -> float:
        """Signed slippage in bps: positive = cost for the given side."""
        raw = (fill - bench) / bench * 10_000.0
        return raw if action == "BUY" else -raw

    def _analyze(self, fills: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for _, o in fills.iterrows():
            sym, day, act = o["symbol"], o["fill_date"], str(o["action"]).upper()
            fill_px = float(o["avg_fill_price"])
            qty     = float(o["filled_qty"])
            arrival = float(o["arrival_price"])

            bar = self._day_bar(sym, day)
            status_parts = []

            slip_arr = cost_arr = None
            if arrival > 0:
                slip_arr = self._slip_bps(fill_px, arrival, act)
                cost_arr = slip_arr / 10_000.0 * arrival * qty
            else:
                status_parts.append("NO_ARRIVAL")

            slip_vwap = cost_vwap = slip_close = None
            vwap = close = None
            if bar is not None:
                vwap, close = bar["vwap_hlc3"], bar["close"]
                slip_vwap  = self._slip_bps(fill_px, vwap, act)
                cost_vwap  = slip_vwap / 10_000.0 * vwap * qty
                slip_close = self._slip_bps(fill_px, close, act)
            else:
                status_parts.append("NO_DAY_BAR")

            rows.append({
                "order_id":         o["order_id"],
                "fill_date":        day,
                "symbol":           sym,
                "action":           act,
                "filled_qty":       int(qty),
                "avg_fill_price":   round(fill_px, 2),
                "order_type":       o.get("order_type", ""),
                "paper":            o.get("paper", True),
                "arrival_price":    round(arrival, 2) if arrival > 0 else None,
                "vwap_hlc3":        round(vwap, 2) if vwap else None,
                "day_close":        round(close, 2) if close else None,
                "slip_arrival_bps": round(slip_arr, 1) if slip_arr is not None else None,
                "slip_vwap_bps":    round(slip_vwap, 1) if slip_vwap is not None else None,
                "slip_close_bps":   round(slip_close, 1) if slip_close is not None else None,
                "cost_arrival_inr": round(cost_arr, 2) if cost_arr is not None else None,
                "cost_vwap_inr":    round(cost_vwap, 2) if cost_vwap is not None else None,
                "benchmark_status": "+".join(status_parts) if status_parts else "OK",
            })
        return pd.DataFrame(rows, columns=REPORT_COLS)

    def _summarize(self, report: pd.DataFrame) -> dict:
        vw = report.dropna(subset=["slip_vwap_bps"])
        ar = report.dropna(subset=["slip_arrival_bps"])
        traded = float((report["avg_fill_price"] * report["filled_qty"]).sum())

        worst = vw.loc[vw["slip_vwap_bps"].idxmax()] if not vw.empty else None
        buys  = vw[vw["action"] == "BUY"]["slip_vwap_bps"]
        sells = vw[vw["action"] == "SELL"]["slip_vwap_bps"]

        def _m(s: pd.Series, fn) -> float | None:
            return round(float(fn(s)), 1) if len(s) else None

        return {
            "run_date":                self.run_date,
            "n_fills":                 len(report),
            "n_with_arrival":          len(ar),
            "total_traded_value":      round(traded, 2),
            "mean_slip_arrival_bps":   _m(ar["slip_arrival_bps"], np.mean),
            "median_slip_arrival_bps": _m(ar["slip_arrival_bps"], np.median),
            "total_cost_arrival_inr":  round(float(ar["cost_arrival_inr"].sum()), 2) if len(ar) else None,
            "mean_slip_vwap_bps":      _m(vw["slip_vwap_bps"], np.mean) or 0.0,
            "median_slip_vwap_bps":    _m(vw["slip_vwap_bps"], np.median),
            "total_cost_vwap_inr":     round(float(vw["cost_vwap_inr"].sum()), 2) if len(vw) else None,
            "buy_mean_vwap_bps":       _m(buys, np.mean),
            "sell_mean_vwap_bps":      _m(sells, np.mean),
            "worst_fill_order_id":     worst["order_id"] if worst is not None else "",
            "worst_fill_bps":          round(float(worst["slip_vwap_bps"]), 1) if worst is not None else None,
        }

    # ── Output ────────────────────────────────────────────────────────────────

    def _save(self, report: pd.DataFrame, summary: dict) -> None:
        if report.empty:                                        # G-D-03
            raise ValueError("Refusing to write empty TCA report")
        self._atomic_write(report, REPORT_CSV)

        row = pd.DataFrame([summary], columns=SUMMARY_COLS)
        if SUMMARY_CSV.exists():                                # G-D-05 dedupe
            hist = pd.read_csv(SUMMARY_CSV)
            hist = hist[hist["run_date"] != self.run_date]
            row = pd.concat([hist, row], ignore_index=True)
        self._atomic_write(row, SUMMARY_CSV)

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    engine = TCAEngine()
    ok = engine.run()
    sys.exit(0 if ok else 1)
