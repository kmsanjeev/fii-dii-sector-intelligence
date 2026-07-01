"""
Charts Router — Phase 11
GET /api/charts/ohlcv    -- OHLCV bars for a symbol via nselib (live NSE API)
GET /api/charts/signals  -- intelligence overlays for chart panel
GET /api/charts/symbols  -- symbol autocomplete list
GET /api/charts/movers   -- top gainers / losers (live)
"""

import sys
import time
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

VALID_PERIODS = {"1D", "1W", "1M", "3M", "6M", "1Y", "3Y", "5Y"}

# nselib accepts these as period= directly; others need from_date/to_date
_NSELIB_NATIVE = {"1D", "1W", "1M", "6M", "1Y"}

# Approximate day counts for periods nselib doesn't support natively
_PERIOD_DAYS = {"3M": 92, "3Y": 365 * 3 + 1, "5Y": 365 * 5 + 2}


def _nselib_kwargs(period: str) -> dict:
    """Return the correct kwargs for capital_market.price_volume_data."""
    if period in _NSELIB_NATIVE:
        return {"period": period}
    days = _PERIOD_DAYS.get(period, 365)
    fmt = "%d-%m-%Y"
    today = date.today()
    return {
        "from_date": (today - timedelta(days=days)).strftime(fmt),
        "to_date":   today.strftime(fmt),
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_nse_date(d: str) -> str:
    """Convert NSE date '30-Jun-2026' -> '2026-06-30' for lightweight-charts."""
    try:
        return pd.to_datetime(d, format="%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        return d


def _fetch_ohlcv(symbol: str, period: str) -> list[dict]:
    """Fetch OHLCV from NSE via nselib and return normalized bars list."""
    from nselib import capital_market

    kwargs = _nselib_kwargs(period)
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

    # Normalize columns — drop rupee symbol column to avoid cp1252 issues
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
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ""), errors="coerce")

    df["time"] = df["date"].apply(_parse_nse_date)
    df = df.dropna(subset=["time", "open", "high", "low", "close"])
    df = df.sort_values("time")
    df = df.drop_duplicates(subset=["time"], keep="last")  # nselib occasionally returns dup dates

    bars = df[["time", "open", "high", "low", "close", "volume"]].to_dict(orient="records")
    return bars


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/ohlcv")
def get_ohlcv(
    symbol: str = Query(..., description="NSE equity symbol e.g. RELIANCE"),
    period: str = Query("1Y", description="1M | 3M | 6M | 1Y | 3Y | 5Y"),
):
    """OHLCV candlestick bars for a symbol from NSE API."""
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period must be one of {VALID_PERIODS}")

    bars = _fetch_ohlcv(symbol, period)

    return {
        "symbol":  symbol.upper(),
        "period":  period,
        "bars":    bars,
        "count":   len(bars),
        "from":    bars[0]["time"]  if bars else None,
        "to":      bars[-1]["time"] if bars else None,
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
            result["bull_run_score"]   = float(r.get("bull_run_score", 0))
            result["label"]            = str(r.get("label", "NEUTRAL"))
            result["price_score"]      = float(r.get("price_score", 0))
            result["sector_flow_score"] = float(r.get("sector_flow_score", 0))
            result["deal_score"]       = float(r.get("deal_score", 0))
            result["corporate_score"]  = float(r.get("corporate_score", 0))
            result["market_regime"]    = str(r.get("market_regime", ""))
            result["regime_multiplier"] = float(r.get("regime_multiplier", 1))
            result["sector"]           = str(r.get("sector", ""))
            result["as_of_date"]       = str(r.get("as_of_date", ""))

    # ML scores
    if ML_SCORES.exists():
        ml = pd.read_csv(ML_SCORES)
        ml["symbol"] = ml["symbol"].str.strip().str.upper()
        row = ml[ml["symbol"] == sym]
        if not row.empty:
            r = row.iloc[0]
            result["ml_bull_run_score"]  = float(r["ml_bull_run_score"]) if pd.notna(r.get("ml_bull_run_score")) else None
            result["accumulation_score"] = float(r["accumulation_score"]) if pd.notna(r.get("accumulation_score")) else None

    # Sector rotation signal
    if SECTOR_ROT.exists() and result.get("sector"):
        sec = pd.read_csv(SECTOR_ROT)
        row = sec[sec["sector"] == result["sector"]]
        if not row.empty:
            r = row.iloc[0]
            result["rotation_signal"]   = str(r.get("rotation_signal", ""))
            result["sector_combined"]   = float(r.get("combined_score", 0))

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
        eq = eq[eq["SYMBOL"].str.startswith(q_up) | eq["COMPANY_NAME"].str.upper().str.contains(q_up, na=False)]
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
        # Keep EQ series only
        if "series" in df.columns:
            df = df[df["series"] == "EQ"]
        rows = df.head(10).to_dict(orient="records")
        return {"type": to_get, "movers": rows}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"NSE API error: {e}")
