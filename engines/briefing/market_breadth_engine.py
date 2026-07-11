"""
Market Breadth Engine
Phase DMB-1 -- Yesterday's breadth + NIFTY/BANKNIFTY technical structure.

Breadth from the last two equity bhavcopy files (EQ series): advances,
declines, unchanged, up/down volume, turnover. 52-week high/low counts from
technical_indicators.csv. Delivery %% is NOT in the bhavcopy cache schema --
reported as N/A, never guessed.

Index technicals from yfinance daily history (^NSEI, ^NSEBANK):
RSI(14, Wilder), MACD(12/26/9) state, DMA 20/50/200 posture, trend label,
support/resistance from 20-day swing extremes.

Writes (atomic, G-D-02):
  data/intelligence/market_breadth.csv   (metric_type, key, value, note)

Run:  py -3.11 -m engines.briefing.market_breadth_engine
"""

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT_CSV = cfg.INTELLIGENCE_DIR / "market_breadth.csv"
TECH_CSV   = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"

INDEXES = [("NIFTY", "^NSEI"), ("BANKNIFTY", "^NSEBANK")]
COLS = ["metric_type", "key", "value", "note", "as_of"]


def _latest_bhavcopies(n: int = 2) -> list[Path]:
    root = cfg.NSE_EQUITY_BHAVCOPY_DIR
    files = sorted(root.glob("*/bhavcopy_*.csv"))
    return files[-n:] if len(files) >= n else []


def _load_eq(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["SERIES"].astype(str).str.strip() == "EQ"]        # G-S-01
    df["SYMBOL"] = df["SYMBOL"].str.strip().str.upper()
    for c in ("CLOSE_PRICE", "TTL_TRD_QNTY"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["CLOSE_PRICE"])
    df = df[df["CLOSE_PRICE"] > 0]                               # G-P-01
    return df[["SYMBOL", "CLOSE_PRICE", "TTL_TRD_QNTY"]]


def _rsi14(close: pd.Series) -> float:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return float((100 - 100 / (1 + rs)).iloc[-1])


class MarketBreadthEngine:
    def run(self) -> bool:
        logger.info("[MarketBreadth] Starting")
        rows: list[dict] = []
        as_of = ""

        # ── Breadth from last two bhavcopies ─────────────────────────────────
        files = _latest_bhavcopies(2)
        if len(files) == 2:
            prev, curr = _load_eq(files[0]), _load_eq(files[1])
            as_of = files[1].stem.replace("bhavcopy_", "")
            m = curr.merge(prev, on="SYMBOL", suffixes=("", "_prev"))
            m["chg"] = m["CLOSE_PRICE"] / m["CLOSE_PRICE_prev"] - 1.0
            adv = int((m["chg"] > 0.0005).sum())
            dec = int((m["chg"] < -0.0005).sum())
            unch = int(len(m) - adv - dec)
            up_vol = float(m.loc[m["chg"] > 0, "TTL_TRD_QNTY"].sum())
            dn_vol = float(m.loc[m["chg"] < 0, "TTL_TRD_QNTY"].sum())
            turnover_cr = float((m["CLOSE_PRICE"] * m["TTL_TRD_QNTY"]).sum() / 1e7)
            rows += [
                {"metric_type": "BREADTH", "key": "advances", "value": adv, "note": ""},
                {"metric_type": "BREADTH", "key": "declines", "value": dec, "note": ""},
                {"metric_type": "BREADTH", "key": "unchanged", "value": unch, "note": ""},
                {"metric_type": "BREADTH", "key": "ad_ratio",
                 "value": round(adv / dec, 2) if dec else None, "note": ""},
                {"metric_type": "BREADTH", "key": "up_down_volume_ratio",
                 "value": round(up_vol / dn_vol, 2) if dn_vol else None, "note": ""},
                {"metric_type": "BREADTH", "key": "turnover_cr",
                 "value": round(turnover_cr, 0), "note": "close x qty approximation"},
                {"metric_type": "BREADTH", "key": "delivery_pct", "value": None,
                 "note": "N/A -- delivery column not in bhavcopy cache schema"},
            ]
        else:
            rows.append({"metric_type": "BREADTH", "key": "status", "value": None,
                         "note": "N/A -- fewer than 2 bhavcopy files found"})

        # ── 52-week structure from technical indicators ───────────────────────
        if TECH_CSV.exists():
            t = pd.read_csv(TECH_CSV)
            for c in ("prox_52w_high", "prox_52w_low"):
                if c in t.columns:
                    t[c] = pd.to_numeric(t[c], errors="coerce")
            n_high = int((t.get("prox_52w_high", pd.Series(dtype=float)) >= -0.5).sum())
            n_low  = int((t.get("prox_52w_low",  pd.Series(dtype=float)) <= 0.5).sum())
            rows += [
                {"metric_type": "BREADTH", "key": "near_52w_high", "value": n_high,
                 "note": "within 0.5% of 52w high"},
                {"metric_type": "BREADTH", "key": "near_52w_low", "value": n_low,
                 "note": "within 0.5% of 52w low"},
            ]

        # ── Index technicals via yfinance ─────────────────────────────────────
        try:
            import yfinance as yf
            for name, ticker in INDEXES:
                try:
                    h = yf.download(ticker, period="1y", interval="1d", progress=False)
                    if isinstance(h.columns, pd.MultiIndex):
                        h.columns = h.columns.get_level_values(0)
                    close = h["Close"].dropna()
                    if len(close) < 210:
                        raise ValueError("insufficient history")
                    last = float(close.iloc[-1])
                    dma20, dma50, dma200 = (float(close.rolling(w).mean().iloc[-1])
                                            for w in (20, 50, 200))
                    rsi = _rsi14(close)
                    ema12 = close.ewm(span=12, adjust=False).mean()
                    ema26 = close.ewm(span=26, adjust=False).mean()
                    macd = ema12 - ema26
                    sig = macd.ewm(span=9, adjust=False).mean()
                    macd_state = "BULLISH_CROSS" if macd.iloc[-1] > sig.iloc[-1] else "BEARISH_CROSS"
                    hi20 = float(h["High"].tail(20).max())
                    lo20 = float(h["Low"].tail(20).min())
                    trend = ("STRONG_UPTREND" if last > dma20 > dma50 > dma200 else
                             "UPTREND" if last > dma50 > dma200 else
                             "DOWNTREND" if last < dma50 < dma200 else "SIDEWAYS")
                    for k, v, note in [
                        ("last", round(last, 1), ""),
                        ("trend", trend, ""),
                        ("rsi_14", round(rsi, 1), ""),
                        ("macd", macd_state, ""),
                        ("dma_20", round(dma20, 1), ""),
                        ("dma_50", round(dma50, 1), ""),
                        ("dma_200", round(dma200, 1), ""),
                        ("support", round(lo20, 1), "20d swing low"),
                        ("resistance", round(hi20, 1), "20d swing high"),
                    ]:
                        rows.append({"metric_type": f"INDEX_{name}", "key": k,
                                     "value": v, "note": note})
                except Exception as e:
                    logger.warning("[MarketBreadth] %s technicals failed: %s", name, e)
                    rows.append({"metric_type": f"INDEX_{name}", "key": "status",
                                 "value": None, "note": f"N/A -- {e}"})
        except ImportError:
            rows.append({"metric_type": "INDEX", "key": "status", "value": None,
                         "note": "N/A -- yfinance not installed"})

        if not rows:                                             # G-D-03
            return False
        for r in rows:
            r["as_of"] = as_of or datetime.now(timezone.utc).strftime("%Y%m%d")
        df = pd.DataFrame(rows, columns=COLS)
        tmp = OUTPUT_CSV.with_suffix(".tmp.csv")                 # G-D-02
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_CSV))
        logger.info("[MarketBreadth] Complete -- %d metrics", len(df))
        return True


if __name__ == "__main__":
    sys.exit(0 if MarketBreadthEngine().run() else 1)
