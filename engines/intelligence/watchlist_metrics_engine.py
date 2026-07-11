"""
Watchlist Metrics Engine
Phase WL-1 -- Institutional decision metrics for the Watchlist table.

Produces per-symbol:
  rvol              Relative Volume = latest volume / 20d avg volume
  rs_30d            30d Relative Strength vs NIFTY 50 (stock ret - index ret)
  delivery_5d_pct   5-session average delivery percentage (true absorption)
  vs_dma_50         %% distance from the 50-DMA (overextension gauge)

Delivery source: nselib bhav_copy_with_delivery (priority-1 source). Raw
files cached IMMUTABLY under data/NSE/delivery/YYYY/ (G-D-01: existing
files are never refetched or modified). Sessions with no file after retry
are skipped; delivery needs >= 3 of the last 5 sessions else None.

Reads: technical_indicators.csv (vol_20d_avg, vs_dma_50),
       bull_run_probability.csv (ret_30d), index_momentum.csv (NIFTY 50)
Writes (atomic, G-D-02): data/intelligence/watchlist_metrics.csv

Run:  py -3.11 -m engines.intelligence.watchlist_metrics_engine
"""

import shutil
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

DELIVERY_DIR = cfg.NSE_DIR / "delivery"
OUTPUT_CSV   = cfg.INTELLIGENCE_DIR / "watchlist_metrics.csv"
TECH_CSV     = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
BULL_CSV     = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
INDEX_CSV    = cfg.INTELLIGENCE_DIR / "index_momentum.csv"

SESSIONS_WANTED = 5
LOOKBACK_DAYS   = 12          # calendar window to find 5 trading sessions
MIN_SESSIONS    = 3

COLS = ["symbol", "rvol", "rs_30d", "delivery_5d_pct", "vs_dma_50", "as_of"]


class WatchlistMetricsEngine:
    def __init__(self):
        DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
        cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Delivery raw acquisition (nselib, cached, immutable) ─────────────────

    def _delivery_path(self, d: date) -> Path:
        ydir = DELIVERY_DIR / str(d.year)
        ydir.mkdir(parents=True, exist_ok=True)
        return ydir / f"sec_del_{d.strftime('%Y%m%d')}.csv"

    def _fetch_session(self, d: date) -> bool:
        """Fetch one session's delivery bhavcopy unless already cached."""
        path = self._delivery_path(d)
        if path.exists():                                        # G-D-01
            return True
        try:
            from nselib import capital_market
        except ImportError:
            logger.error("[WatchlistMetrics] nselib not installed")
            return False
        for attempt in range(3):                                 # G-A-02
            try:
                df = capital_market.bhav_copy_with_delivery(d.strftime("%d-%m-%Y"))
                if df is None or df.empty:
                    return False                                 # holiday/weekend
                tmp = path.with_suffix(".tmp")                   # G-D-02
                df.to_csv(tmp, index=False)
                shutil.move(str(tmp), str(path))
                logger.info("[WatchlistMetrics] Fetched delivery %s (%d rows)",
                            d.isoformat(), len(df))
                return True
            except Exception as e:
                wait = 2 * (2 ** attempt)
                logger.warning("[WatchlistMetrics] %s attempt %d failed: %s",
                               d.isoformat(), attempt + 1, str(e)[:80])
                time.sleep(wait)
        return False

    def _collect_sessions(self) -> list[Path]:
        """Latest SESSIONS_WANTED delivery files, fetching missing ones."""
        got: list[Path] = []
        d = date.today()
        for _ in range(LOOKBACK_DAYS):
            if d.weekday() < 5:                                  # skip Sat/Sun
                if self._fetch_session(d):
                    got.append(self._delivery_path(d))
                    if len(got) >= SESSIONS_WANTED:
                        break
                time.sleep(cfg.API_DELAY)                        # G-A-01
            d -= timedelta(days=1)
        return got

    @staticmethod
    def _load_delivery(path: Path) -> pd.DataFrame | None:
        try:
            df = pd.read_csv(path)
            df.columns = [c.strip() for c in df.columns]
            df = df[df["SERIES"].astype(str).str.strip() == "EQ"]   # G-S-01
            df["SYMBOL"] = df["SYMBOL"].astype(str).str.strip().str.upper()
            for c in ("TTL_TRD_QNTY", "DELIV_PER"):
                df[c] = pd.to_numeric(
                    df[c].astype(str).str.replace(",", "").str.strip(),
                    errors="coerce")
            return df[["SYMBOL", "TTL_TRD_QNTY", "DELIV_PER"]].dropna(subset=["SYMBOL"])
        except Exception as e:
            logger.warning("[WatchlistMetrics] Bad delivery file %s: %s", path.name, e)
            return None

    # ── Main ──────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[WatchlistMetrics] Starting")
        sessions = self._collect_sessions()
        frames = [f for p in sessions if (f := self._load_delivery(p)) is not None]
        if not frames:
            logger.warning("[WatchlistMetrics] No delivery sessions available")
        latest = frames[0] if frames else None
        as_of = sessions[0].stem.replace("sec_del_", "") if sessions else date.today().strftime("%Y%m%d")

        # 5-session delivery average (>= MIN_SESSIONS sessions per symbol)
        deliv_5d = None
        if frames:
            allf = pd.concat(frames, ignore_index=True)
            g = allf.groupby("SYMBOL")["DELIV_PER"].agg(["mean", "count"])
            g = g[g["count"] >= min(MIN_SESSIONS, len(frames))]
            deliv_5d = g["mean"].round(1)

        # Technicals: 20d avg volume + vs_dma_50
        if not TECH_CSV.exists():
            logger.error("[WatchlistMetrics] technical_indicators.csv missing")
            return False
        tech = pd.read_csv(TECH_CSV, usecols=["symbol", "vol_20d_avg", "vs_dma_50"])
        tech["symbol"] = tech["symbol"].str.strip().str.upper()
        for c in ("vol_20d_avg", "vs_dma_50"):
            tech[c] = pd.to_numeric(tech[c], errors="coerce")
        out = tech.drop_duplicates(subset=["symbol"], keep="last").copy()

        # RVOL = latest session volume / 20d avg volume
        out["rvol"] = None
        if latest is not None:
            vol_map = latest.set_index("SYMBOL")["TTL_TRD_QNTY"]
            cur = out["symbol"].map(vol_map)
            with pd.option_context("mode.chained_assignment", None):
                out["rvol"] = (cur / out["vol_20d_avg"]).where(
                    out["vol_20d_avg"] > 0).round(2)

        # RS 30D vs NIFTY 50
        out["rs_30d"] = None
        if BULL_CSV.exists() and INDEX_CSV.exists():
            bull = pd.read_csv(BULL_CSV, usecols=["symbol", "ret_30d"])
            bull["symbol"] = bull["symbol"].str.strip().str.upper()
            bull["ret_30d"] = pd.to_numeric(bull["ret_30d"], errors="coerce")
            im = pd.read_csv(INDEX_CSV)
            nrow = im[im["INDEX_NAME"].astype(str).str.strip().str.upper() == "NIFTY 50"]
            if not nrow.empty:
                nifty_30 = float(nrow.iloc[0]["RETURN_30D"])
                rs = out["symbol"].map(bull.set_index("symbol")["ret_30d"]) - nifty_30
                out["rs_30d"] = rs.round(2)
                logger.info("[WatchlistMetrics] NIFTY 50 30d = %.2f%%", nifty_30)

        # Delivery
        out["delivery_5d_pct"] = out["symbol"].map(deliv_5d) if deliv_5d is not None else None

        out["as_of"] = as_of
        out = out[COLS]
        if out.empty:                                            # G-D-03
            return False
        tmp = OUTPUT_CSV.with_suffix(".tmp.csv")                 # G-D-02
        out.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_CSV))
        logger.info("[WatchlistMetrics] Complete -- %d symbols | rvol %d | rs %d | deliv %d",
                    len(out), out["rvol"].notna().sum(),
                    pd.to_numeric(out["rs_30d"], errors="coerce").notna().sum(),
                    pd.to_numeric(out["delivery_5d_pct"], errors="coerce").notna().sum())
        return True


if __name__ == "__main__":
    sys.exit(0 if WatchlistMetricsEngine().run() else 1)
