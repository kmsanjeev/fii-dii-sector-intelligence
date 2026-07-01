"""
Charts Router -- Phase 11
GET /api/charts/ohlcv    -- OHLCV bars for a symbol (timeframe-based candles)
GET /api/charts/signals  -- intelligence overlays for chart panel
GET /api/charts/symbols  -- symbol autocomplete list
GET /api/charts/movers   -- top gainers / losers (live)

Timeframe semantics:
  5M / 15M / 1H  -- intraday candles via yfinance (max available history)
  1D             -- daily candles, 1Y history from nselib (~255 bars)
  1W             -- weekly candles, resampled from 5Y daily data
  1M             -- monthly candles, resampled from 5Y daily data
  3M             -- quarterly candles, resampled from 5Y daily data
"""

import sys
import time
import warnings
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("charts")
router = APIRouter(prefix="/api/charts", tags=["charts"])

# ---------------------------------------------------------------------------
# Paths for intelligence overlays
# ---------------------------------------------------------------------------
BULL_RUN   = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
ML_SCORES  = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"
SECTOR_ROT = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
SHP_CSV    = cfg.NSE_DIR / "shareholding" / "quarterly_shp.csv"
EQUITY_MASTER = cfg.NSE_DIR / "equity_master" / "equity_master.csv"

VALID_TIMEFRAMES = {"5M", "15M", "1H", "1D", "1W", "1M", "3M"}

# Intraday timeframes served by yfinance; daily+ served by nselib
_INTRADAY = {"5M", "15M", "1H"}

# yfinance intervals and max-available periods per intraday timeframe
_YF_INTERVAL = {"5M": "5m", "15M": "15m", "1H": "1h"}
_YF_PERIOD   = {"5M": "7d", "15M": "60d", "1H": "730d"}

# nselib years of history to fetch for resampled timeframes
_DAILY_YEARS = {"1D": 1, "1W": 5, "1M": 5, "3M": 5}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_nse_date(d: str) -> str:
    """Convert NSE date '30-Jun-2026' -> '2026-06-30' for lightweight-charts."""
    try:
        return pd.to_datetime(d, format="%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        return d


def _normalize_daily_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip rupee columns, rename, numeric-parse, add 'time' string column."""
    df = df[[c for c in df.columns if "₹" not in c]]
    col_map = {
        "OpenPrice":           "open",
        "HighPrice":           "high",
        "LowPrice":            "low",
        "ClosePrice":          "close",
        "TotalTradedQuantity": "volume",
        "Date":                "date",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""), errors="coerce"
            )
    df["time"] = df["date"].apply(_parse_nse_date)
    df = df.dropna(subset=["time", "open", "high", "low", "close"])
    df = df.sort_values("time").drop_duplicates(subset=["time"], keep="last")
    return df


def _fetch_daily_data(symbol: str, years: int = 1) -> pd.DataFrame:
    """Fetch daily OHLCV from nselib for up to `years` years and return normalized df."""
    from nselib import capital_market

    if years <= 1:
        kwargs: dict = {"period": "1Y"}
    else:
        today = date.today()
        fmt = "%d-%m-%Y"
        kwargs = {
            "from_date": (today - timedelta(days=years * 365 + 2)).strftime(fmt),
            "to_date":   today.strftime(fmt),
        }

    df = None
    for attempt in range(3):
        try:
            df = capital_market.price_volume_data(symbol.upper(), **kwargs)
            break
        except Exception as e:
            if attempt == 2:
                raise HTTPException(status_code=502, detail=f"NSE API error: {e}")
            time.sleep(2 ** attempt)

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No data for {symbol}")

    return _normalize_daily_df(df)


def _resample_bars(df: pd.DataFrame, timeframe: str) -> list[dict]:
    """Resample daily OHLCV bars to weekly / monthly / quarterly candles."""
    df2 = df.copy()
    df2["_dt"] = pd.to_datetime(df2["time"])
    df2 = df2.sort_values("_dt").set_index("_dt")

    freq_map = {"1W": "W-FRI", "1M": "ME", "3M": "QE"}
    freq = freq_map[timeframe]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = df2[["open", "high", "low", "close", "volume"]].resample(freq).agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low",  "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
        ).dropna(subset=["close"])

    r = r[r["open"].notna()].reset_index()
    r["time"] = r["_dt"].dt.strftime("%Y-%m-%d")
    return r[["time", "open", "high", "low", "close", "volume"]].to_dict(orient="records")


def _fetch_intraday(symbol: str, timeframe: str) -> list[dict]:
    """Fetch intraday bars via yfinance for 5M / 15M / 1H timeframes."""
    try:
        import yfinance as yf
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="yfinance not installed -- run: py -3.11 -m pip install yfinance",
        )

    iv  = _YF_INTERVAL[timeframe]
    prd = _YF_PERIOD[timeframe]
    ticker = symbol.upper() + ".NS"

    df = None
    for attempt in range(3):
        try:
            df = yf.download(
                ticker, period=prd, interval=iv,
                auto_adjust=True, progress=False,
            )
            break
        except Exception as e:
            if attempt == 2:
                raise HTTPException(status_code=502, detail=f"yfinance error: {e}")
            time.sleep(2 ** attempt)

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"No intraday data for {symbol}")

    # Flatten MultiIndex columns that some yfinance versions produce
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()

    # Rename: Datetime / Date -> dt; OHLCV -> lowercase
    col_map: dict = {}
    for c in df.columns:
        cl = str(c).lower()
        if cl in ("datetime", "date", "index"):
            col_map[c] = "dt"
        elif cl == "open":    col_map[c] = "open"
        elif cl == "high":    col_map[c] = "high"
        elif cl == "low":     col_map[c] = "low"
        elif cl == "close":   col_map[c] = "close"
        elif cl == "volume":  col_map[c] = "volume"
    df = df.rename(columns=col_map)
    df = df.dropna(subset=["close"])

    bars: list[dict] = []
    seen: set = set()
    for _, row in df.iterrows():
        unix = int(pd.Timestamp(row["dt"]).timestamp())
        if unix in seen:
            continue
        seen.add(unix)
        bars.append({
            "time":   unix,
            "open":   round(float(row["open"]),  2),
            "high":   round(float(row["high"]),  2),
            "low":    round(float(row["low"]),   2),
            "close":  round(float(row["close"]), 2),
            "volume": int(row["volume"]) if pd.notna(row.get("volume")) else 0,
        })

    return sorted(bars, key=lambda x: x["time"])


def _fetch_ohlcv(symbol: str, timeframe: str) -> list[dict]:
    """Main dispatcher: returns OHLCV bars for the given candle timeframe."""
    if timeframe in _INTRADAY:
        return _fetch_intraday(symbol, timeframe)

    years = _DAILY_YEARS.get(timeframe, 1)
    df = _fetch_daily_data(symbol, years=years)

    if timeframe == "1D":
        return df[["time", "open", "high", "low", "close", "volume"]].to_dict(orient="records")

    return _resample_bars(df, timeframe)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/ohlcv")
def get_ohlcv(
    symbol:    str = Query(...,  description="NSE equity symbol e.g. RELIANCE"),
    timeframe: str = Query("1D", description="5M | 15M | 1H | 1D | 1W | 1M | 3M"),
):
    """OHLCV candlestick bars for a symbol.

    Timeframe = candle resolution (not date range). Max available history is
    always returned -- 1Y for daily, 5Y resampled for weekly/monthly/quarterly,
    7-730 days for intraday via yfinance.
    """
    tf = timeframe.upper()
    if tf not in VALID_TIMEFRAMES:
        raise HTTPException(
            status_code=400,
            detail=f"timeframe must be one of {sorted(VALID_TIMEFRAMES)}",
        )

    bars = _fetch_ohlcv(symbol, tf)

    return {
        "symbol":    symbol.upper(),
        "timeframe": tf,
        "bars":      bars,
        "count":     len(bars),
        "from":      bars[0]["time"]  if bars else None,
        "to":        bars[-1]["time"] if bars else None,
    }


@router.get("/signals")
def get_signals(symbol: str = Query(..., description="NSE equity symbol")):
    """Intelligence overlay signals for the chart panel."""
    sym = symbol.upper().strip()
    result: dict = {"symbol": sym}

    # Bull run probability
    if BULL_RUN.exists():
        br = pd.read_csv(BULL_RUN)
        br["symbol"] = br["symbol"].str.strip().str.upper()
        row = br[br["symbol"] == sym]
        if not row.empty:
            r = row.iloc[0]
            result["bull_run_score"]    = float(r.get("bull_run_score", 0))
            result["label"]             = str(r.get("label", "NEUTRAL"))
            result["price_score"]       = float(r.get("price_score", 0))
            result["sector_flow_score"] = float(r.get("sector_flow_score", 0))
            result["deal_score"]        = float(r.get("deal_score", 0))
            result["corporate_score"]   = float(r.get("corporate_score", 0))
            result["market_regime"]     = str(r.get("market_regime", ""))
            result["regime_multiplier"] = float(r.get("regime_multiplier", 1))
            result["sector"]            = str(r.get("sector", ""))
            result["as_of_date"]        = str(r.get("as_of_date", ""))

    # ML scores
    if ML_SCORES.exists():
        ml = pd.read_csv(ML_SCORES)
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        row = ml[ml["symbol"] == sym]
        if not row.empty:
            r = row.iloc[0]
            result["ml_bull_run_score"]  = float(r["ml_bull_run_score"])  if pd.notna(r.get("ml_bull_run_score"))  else None
            result["accumulation_score"] = float(r["accumulation_score"]) if pd.notna(r.get("accumulation_score")) else None

    # Sector rotation signal
    if SECTOR_ROT.exists() and result.get("sector"):
        sec = pd.read_csv(SECTOR_ROT)
        row = sec[sec["sector"] == result["sector"]]
        if not row.empty:
            r = row.iloc[0]
            result["rotation_signal"] = str(r.get("rotation_signal", ""))
            result["sector_combined"] = float(r.get("combined_score", 0))

    # Shareholding (latest quarter)
    if SHP_CSV.exists():
        shp = pd.read_csv(SHP_CSV)
        shp["symbol"] = shp["symbol"].str.strip().str.upper()
        rows = shp[shp["symbol"] == sym].copy()
        if not rows.empty:
            rows["quarter_end_date"] = pd.to_datetime(
                rows["quarter_end_date"], format="%d-%b-%Y", errors="coerce"
            )
            latest = rows.sort_values("quarter_end_date", ascending=False).iloc[0]
            result["shp_fii_pct"]      = float(latest["fii_pct"])      if pd.notna(latest.get("fii_pct"))      else None
            result["shp_dii_pct"]      = float(latest["dii_pct"])      if pd.notna(latest.get("dii_pct"))      else None
            result["shp_promoter_pct"] = float(latest["promoter_pct"]) if pd.notna(latest.get("promoter_pct")) else None
            result["shp_quarter"]      = str(latest.get("window_label", ""))

    return result


@router.get("/symbols")
def get_symbols(q: str = Query("", description="Search prefix")):
    """Return EQ symbols for autocomplete."""
    if not EQUITY_MASTER.exists():
        raise HTTPException(status_code=503, detail="equity_master.csv not loaded")
    em = pd.read_csv(EQUITY_MASTER)
    eq = em[em["SERIES"] == "EQ"][["SYMBOL", "COMPANY_NAME"]].copy()
    eq["SYMBOL"] = eq["SYMBOL"].str.strip().str.upper()
    if q:
        q_up = q.upper()
        eq = eq[
            eq["SYMBOL"].str.startswith(q_up) |
            eq["COMPANY_NAME"].str.upper().str.contains(q_up, na=False)
        ]
    eq = eq.sort_values("SYMBOL").head(50)
    return {"symbols": eq.to_dict(orient="records")}


@router.get("/movers")
def get_movers(type: str = Query("gainers", description="gainers | losers")):
    """Top gainers or losers from NSE live data."""
    from nselib import capital_market
    try:
        to_get = "gainers" if type != "losers" else "losers"
        df = capital_market.top_gainers_or_losers(to_get=to_get)
        df = df[[c for c in df.columns if "₹" not in c]]
        if "series" in df.columns:
            df = df[df["series"] == "EQ"]
        rows = df.head(10).to_dict(orient="records")
        return {"type": to_get, "movers": rows}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NSE API error: {e}")
