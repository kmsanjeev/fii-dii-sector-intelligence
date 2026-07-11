"""
Global Snapshot Engine
Phase DMB-1 -- Overnight global markets for the pre-market brief.

yfinance is the justified source here (acquisition-priority rule): global
indices/futures/commodities/FX have no nselib or NSE source. Every fetch
failure is recorded as status=UNAVAILABLE -- the brief marks it N/A and
NEVER guesses a price.

Writes (atomic, G-D-02):
  data/intelligence/global_snapshot.csv
    group, name, ticker, last, prev_close, chg_pct, status, fetched_at

Run:  py -3.11 -m engines.briefing.global_snapshot_engine
"""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT_CSV = cfg.INTELLIGENCE_DIR / "global_snapshot.csv"

# group, display name, yahoo ticker
UNIVERSE: list[tuple[str, str, str]] = [
    ("US",          "Dow Jones",        "^DJI"),
    ("US",          "Nasdaq",           "^IXIC"),
    ("US",          "S&P 500",          "^GSPC"),
    ("EUROPE",      "Euro Stoxx 50",    "^STOXX50E"),
    ("EUROPE",      "FTSE 100",         "^FTSE"),
    ("EUROPE",      "DAX",              "^GDAXI"),
    ("ASIA",        "Nikkei 225",       "^N225"),
    ("ASIA",        "Hang Seng",        "^HSI"),
    ("ASIA",        "Shanghai Comp",    "000001.SS"),
    ("ASIA",        "Kospi",            "^KS11"),
    ("ASIA",        "ASX 200",          "^AXJO"),
    ("FUTURES",     "Dow Futures",      "YM=F"),
    ("FUTURES",     "Nasdaq Futures",   "NQ=F"),
    ("FUTURES",     "S&P Futures",      "ES=F"),
    ("INDIA_PROXY", "Nifty 50 (spot)",  "^NSEI"),
    ("INDIA_PROXY", "Bank Nifty (spot)","^NSEBANK"),
    ("COMMODITY",   "Gold",             "GC=F"),
    ("COMMODITY",   "Silver",           "SI=F"),
    ("COMMODITY",   "Brent Crude",      "BZ=F"),
    ("COMMODITY",   "WTI Crude",        "CL=F"),
    ("COMMODITY",   "Natural Gas",      "NG=F"),
    ("COMMODITY",   "Copper",           "HG=F"),
    ("CURRENCY",    "USD/INR",          "USDINR=X"),
    ("CURRENCY",    "Dollar Index",     "DX-Y.NYB"),
    ("CURRENCY",    "EUR/USD",          "EURUSD=X"),
    ("CURRENCY",    "USD/JPY",          "USDJPY=X"),
    ("BOND",        "US 10Y Yield",     "^TNX"),
    ("VOLATILITY",  "India VIX",        "^INDIAVIX"),
    ("VOLATILITY",  "CBOE VIX",         "^VIX"),
]

COLS = ["group", "name", "ticker", "last", "prev_close", "chg_pct",
        "status", "fetched_at"]


class GlobalSnapshotEngine:
    """One batched yfinance pull of everything global the brief needs."""

    def run(self) -> bool:
        logger.info("[GlobalSnapshot] Fetching %d tickers", len(UNIVERSE))
        try:
            import yfinance as yf
        except ImportError:
            logger.error("[GlobalSnapshot] yfinance not installed")
            return False

        fetched_at = datetime.now(timezone.utc).isoformat()
        tickers = [t for _, _, t in UNIVERSE]
        rows: list[dict] = []

        # Batched download: 2 daily bars per ticker gives last + prev close
        try:
            data = yf.download(tickers, period="5d", interval="1d",
                               group_by="ticker", progress=False, threads=True)
        except Exception as e:
            logger.error("[GlobalSnapshot] Batch download failed: %s", e)
            data = None

        for group, name, ticker in UNIVERSE:
            last = prev = chg = None
            status = "UNAVAILABLE"
            try:
                if data is not None:
                    closes = data[ticker]["Close"].dropna()
                    if len(closes) >= 2:
                        last = float(closes.iloc[-1])
                        prev = float(closes.iloc[-2])
                        chg = (last / prev - 1.0) * 100.0
                        status = "OK"
                    elif len(closes) == 1:
                        last = float(closes.iloc[-1])
                        status = "PARTIAL"
            except Exception:
                pass
            if status == "UNAVAILABLE":
                logger.warning("[GlobalSnapshot] %s (%s) unavailable", name, ticker)
            rows.append({
                "group": group, "name": name, "ticker": ticker,
                "last": round(last, 2) if last is not None else None,
                "prev_close": round(prev, 2) if prev is not None else None,
                "chg_pct": round(chg, 2) if chg is not None else None,
                "status": status, "fetched_at": fetched_at,
            })

        df = pd.DataFrame(rows, columns=COLS)
        ok_n = int((df["status"] == "OK").sum())
        if ok_n == 0:                                            # G-D-03 spirit
            logger.error("[GlobalSnapshot] Nothing fetched -- refusing to overwrite")
            return False
        tmp = OUTPUT_CSV.with_suffix(".tmp.csv")                 # G-D-02
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_CSV))
        logger.info("[GlobalSnapshot] Complete -- %d/%d OK", ok_n, len(UNIVERSE))
        return True


if __name__ == "__main__":
    sys.exit(0 if GlobalSnapshotEngine().run() else 1)
