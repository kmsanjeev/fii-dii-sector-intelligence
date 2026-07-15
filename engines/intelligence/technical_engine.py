"""
Technical Indicators Engine — Phase A (rev2)
Computes institutional-grade indicators from daily adjusted parquets.
Output: data/intelligence/technical_indicators.csv

Indicators added (rev2):
  RSI(14)       — momentum oscillator; Wilder smoothing
  MACD(12,26,9) — trend + momentum; line/signal/histogram/crossover
  ATR(14)       — volatility; Wilder smoothing; used for stop-loss sizing
  BB(20,2)      — Bollinger Bands; %B position + bandwidth squeeze signal
  OBV slope     — On-Balance Volume 20D slope direction (ACCUMULATING/DISTRIBUTING)
  ADX(14)       — trend strength; +DI/-DI; STRONG/MODERATE/RANGING labels

Run: py -3.11 -m engines.intelligence.technical_engine
"""

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT  = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
ADJ_DIR = cfg.DATA_DIR / "NSE" / "adjusted_equity"
EQUITY_MASTER_FILE = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
LOOKBACK = 252  # trading sessions ~ 1 year


def _load_equity_universe() -> set[str] | None:
    """
    Active EQ-series symbols from equity_master.csv -- the platform's
    curated real-company universe. ETFs, index-tracking products, and
    similar financial instruments also trade under NSE's "EQ" series in
    raw bhavcopy, so a series=="EQ" filter alone does not exclude them;
    only equity_master.csv (which is built specifically to list actual
    listed companies) does. Without this, symbols like PSUBANK,
    IVZINGOLD, LICMFGOLD (ETFs) leaked into "stock" screening tools --
    found via a live chatbot response, see CHANGELOG v4.53.2.
    """
    if not EQUITY_MASTER_FILE.exists():
        logger.warning("[Technical] equity_master.csv not found -- cannot filter universe")
        return None
    em = pd.read_csv(EQUITY_MASTER_FILE)
    em.columns = [c.upper() for c in em.columns]
    if not {"SYMBOL", "SERIES", "IS_ACTIVE"}.issubset(em.columns):
        logger.warning("[Technical] equity_master.csv missing expected columns -- cannot filter universe")
        return None
    active_eq = em[(em["SERIES"] == "EQ") & (em["IS_ACTIVE"] == True)]  # noqa: E712
    return set(active_eq["SYMBOL"].astype(str))


# ─── Trend signal from DMA structure ─────────────────────────────────────────

def _trend_signal(close: float, d20, d50, d200) -> str:
    if d200 is None:
        return "INSUFFICIENT_DATA"
    above_200 = close > d200
    above_50  = d50  is not None and close > d50
    above_20  = d20  is not None and close > d20
    if above_200 and above_50 and above_20:
        return "STRONG_UPTREND"
    if above_200 and above_50:
        return "UPTREND"
    if above_200:
        return "CONSOLIDATING"
    return "DOWNTREND"


# ─── RSI(14) via Wilder smoothing ─────────────────────────────────────────────

def _rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) < period + 5:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder's smoothing: alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    val = rsi_series.iloc[-1]
    return round(float(val), 2) if pd.notna(val) else None


def _rsi_signal(rsi: float | None) -> str:
    if rsi is None:
        return ""
    if rsi >= 70:
        return "OVERBOUGHT"
    if rsi >= 55:
        return "BULLISH"
    if rsi >= 45:
        return "NEUTRAL"
    if rsi >= 30:
        return "BEARISH"
    return "OVERSOLD"


# ─── MACD(12,26,9) ────────────────────────────────────────────────────────────

def _macd(close: pd.Series) -> dict:
    if len(close) < 35:
        return {}
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line   = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram   = macd_line - signal_line

    ml   = round(float(macd_line.iloc[-1]),   4) if pd.notna(macd_line.iloc[-1])   else None
    sl   = round(float(signal_line.iloc[-1]),  4) if pd.notna(signal_line.iloc[-1]) else None
    hist = round(float(histogram.iloc[-1]),    4) if pd.notna(histogram.iloc[-1])   else None

    # Crossover detection: compare last two bars
    cross = ""
    if len(macd_line) >= 2 and len(signal_line) >= 2:
        ml_prev   = macd_line.iloc[-2]
        sl_prev   = signal_line.iloc[-2]
        ml_now    = macd_line.iloc[-1]
        sl_now    = signal_line.iloc[-1]
        if pd.notna(ml_prev) and pd.notna(sl_prev) and pd.notna(ml_now) and pd.notna(sl_now):
            if ml_prev <= sl_prev and ml_now > sl_now:
                cross = "BULLISH_CROSS"
            elif ml_prev >= sl_prev and ml_now < sl_now:
                cross = "BEARISH_CROSS"
            else:
                cross = "BULLISH" if ml_now > sl_now else "BEARISH"

    return {
        "macd_line":   ml,
        "macd_signal": sl,
        "macd_hist":   hist,
        "macd_cross":  cross,
    }


# ─── ATR(14) via Wilder smoothing ─────────────────────────────────────────────

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float | None:
    if len(close) < period + 5:
        return None
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    atr_series = tr.ewm(alpha=1 / period, min_periods=period).mean()
    val = atr_series.iloc[-1]
    return round(float(val), 4) if pd.notna(val) else None


# ─── Bollinger Bands(20,2) ────────────────────────────────────────────────────

def _bollinger(close: pd.Series, period: int = 20, n_std: float = 2.0) -> dict:
    if len(close) < period + 5:
        return {}
    sma   = close.rolling(period).mean()
    std   = close.rolling(period).std()
    upper = sma + n_std * std
    lower = sma - n_std * std

    u  = upper.iloc[-1]
    l  = lower.iloc[-1]
    m  = sma.iloc[-1]
    c  = close.iloc[-1]

    if not (pd.notna(u) and pd.notna(l) and pd.notna(m)):
        return {}

    band_range = float(u - l)
    bb_pct     = round((float(c) - float(l)) / band_range * 100, 2) if band_range > 0 else None
    bb_width   = round(band_range / float(m) * 100, 2) if float(m) != 0 else None

    # Squeeze: current bandwidth < 20-session min bandwidth
    widths = ((upper - lower) / sma * 100).dropna()
    squeeze = False
    if len(widths) >= 20:
        squeeze = bool(bb_width is not None and bb_width <= float(widths.tail(20).min()))

    # Position signal
    if bb_pct is not None:
        if bb_pct >= 90:
            pos_sig = "NEAR_UPPER"
        elif bb_pct <= 10:
            pos_sig = "NEAR_LOWER"
        elif squeeze:
            pos_sig = "SQUEEZE"
        else:
            pos_sig = "MID_BAND"
    else:
        pos_sig = ""

    return {
        "bb_upper":  round(float(u), 2),
        "bb_lower":  round(float(l), 2),
        "bb_mid":    round(float(m), 2),
        "bb_pct":    bb_pct,
        "bb_width":  bb_width,
        "bb_signal": pos_sig,
        "bb_squeeze": squeeze,
    }


# ─── OBV 20D slope ────────────────────────────────────────────────────────────

def _obv_slope(close: pd.Series, volume: pd.Series) -> str:
    if len(close) < 22 or len(volume) < 22:
        return ""
    direction = np.sign(close.diff().fillna(0))
    obv = (volume * direction).cumsum()
    # Slope: compare last 5D avg to 20D-start 5D avg (robust against single-day swings)
    recent   = float(obv.tail(5).mean())
    older    = float(obv.iloc[-20:-15].mean())
    if older == 0:
        return ""
    return "ACCUMULATING" if recent > older else "DISTRIBUTING"


# ─── ADX(14) ─────────────────────────────────────────────────────────────────

def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> dict:
    if len(close) < period * 2 + 5:
        return {}
    # True Range
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Directional Movement
    prev_high = high.shift(1)
    prev_low  = low.shift(1)
    up_move   = high - prev_high
    down_move = prev_low - low
    plus_dm   = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=close.index)
    minus_dm  = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=close.index)

    # Wilder smoothing
    atr14     = tr.ewm(alpha=1 / period, min_periods=period).mean()
    plus_di   = 100 * plus_dm.ewm(alpha=1 / period,  min_periods=period).mean() / atr14.replace(0, np.nan)
    minus_di  = 100 * minus_dm.ewm(alpha=1 / period, min_periods=period).mean() / atr14.replace(0, np.nan)

    dx_denom  = (plus_di + minus_di).replace(0, np.nan)
    dx        = 100 * (plus_di - minus_di).abs() / dx_denom
    adx_series = dx.ewm(alpha=1 / period, min_periods=period).mean()

    adx_val   = adx_series.iloc[-1]
    pdi_val   = plus_di.iloc[-1]
    mdi_val   = minus_di.iloc[-1]

    if not (pd.notna(adx_val) and pd.notna(pdi_val) and pd.notna(mdi_val)):
        return {}

    adx_f = round(float(adx_val), 2)
    pdi_f = round(float(pdi_val), 2)
    mdi_f = round(float(mdi_val), 2)

    if adx_f >= 30:
        strength = "STRONG_TREND"
    elif adx_f >= 20:
        strength = "MODERATE_TREND"
    else:
        strength = "RANGING"

    direction = "BULLISH" if pdi_f > mdi_f else "BEARISH"

    return {
        "adx":          adx_f,
        "adx_plus_di":  pdi_f,
        "adx_minus_di": mdi_f,
        "adx_strength": strength,
        "adx_direction": direction,
    }


# ─── Main run ─────────────────────────────────────────────────────────────────

def run() -> dict:
    all_files = sorted(ADJ_DIR.glob("**/*.parquet"))
    if len(all_files) < 20:
        return {"status": "ERROR", "error": f"Only {len(all_files)} parquet files found"}

    files = all_files[-LOOKBACK:]
    logger.info("[Technical] Reading %d parquet files for indicators", len(files))

    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(
                f, columns=["SYMBOL", "HIGH_PRICE", "LOW_PRICE", "CLOSE_PRICE", "TTL_TRD_QNTY"]
            )
            date_str = f.stem.replace("bhavcopy_", "")
            df["_date"] = pd.to_datetime(date_str, format="%Y%m%d")
            dfs.append(df)
        except Exception as exc:
            logger.warning("[Technical] Skip %s: %s", f.name, exc)

    if not dfs:
        return {"status": "ERROR", "error": "No parquet files readable"}

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.dropna(subset=["SYMBOL", "CLOSE_PRICE"])
    combined = combined[combined["CLOSE_PRICE"] > 0]

    close_piv = combined.pivot_table(index="_date", columns="SYMBOL", values="CLOSE_PRICE",  aggfunc="last").sort_index()
    high_piv  = combined.pivot_table(index="_date", columns="SYMBOL", values="HIGH_PRICE",   aggfunc="last").sort_index()
    low_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="LOW_PRICE",    aggfunc="last").sort_index()
    vol_piv   = combined.pivot_table(index="_date", columns="SYMBOL", values="TTL_TRD_QNTY", aggfunc="last").sort_index()

    as_of_date = str(close_piv.index[-1].date())
    symbols    = close_piv.columns.tolist()

    equity_universe = _load_equity_universe()
    if equity_universe is not None:
        before = len(symbols)
        symbols = [s for s in symbols if s in equity_universe]
        logger.info(
            "[Technical] Filtered to equity_master.csv universe: %d -> %d symbols "
            "(excluded ETFs/index products not in the platform's stock universe)",
            before, len(symbols),
        )

    logger.info("[Technical] Computing for %d symbols, as_of=%s", len(symbols), as_of_date)

    records = []
    for sym in symbols:
        cl = close_piv[sym].dropna()
        hi = high_piv[sym].dropna() if sym in high_piv.columns else pd.Series(dtype=float)
        lo = low_piv[sym].dropna()  if sym in low_piv.columns  else pd.Series(dtype=float)
        vo = vol_piv[sym].dropna()  if sym in vol_piv.columns  else pd.Series(dtype=float)

        if len(cl) < 5:
            continue

        close_now = float(cl.iloc[-1])
        high_52w  = float(hi.max()) if len(hi) > 0 else close_now
        low_52w   = float(lo.min()) if len(lo) > 0 else close_now

        prox_52w_high = round((close_now - high_52w) / high_52w * 100, 2) if high_52w > 0 else 0.0
        prox_52w_low  = round((close_now - low_52w)  / low_52w  * 100, 2) if low_52w  > 0 else 0.0

        dma_20  = round(float(cl.tail(20).mean()),  2) if len(cl) >= 20  else None
        dma_50  = round(float(cl.tail(50).mean()),  2) if len(cl) >= 50  else None
        dma_200 = round(float(cl.tail(200).mean()), 2) if len(cl) >= 200 else None

        vs_dma_20  = round((close_now - dma_20)  / dma_20  * 100, 2) if dma_20  else None
        vs_dma_50  = round((close_now - dma_50)  / dma_50  * 100, 2) if dma_50  else None
        vs_dma_200 = round((close_now - dma_200) / dma_200 * 100, 2) if dma_200 else None

        trend    = _trend_signal(close_now, dma_20, dma_50, dma_200)
        vol_20d_avg = round(float(vo.tail(20).mean()), 0) if len(vo) >= 5 else None

        # ── New indicators ────────────────────────────────────────────────────
        rsi_val  = _rsi(cl)
        rsi_sig  = _rsi_signal(rsi_val)

        # Align OHLCV to common date index for multi-series indicators
        _idx = cl.index
        hi_a = hi.reindex(_idx)
        lo_a = lo.reindex(_idx)
        vo_a = vo.reindex(_idx)

        macd_d   = _macd(cl)
        atr_val  = _atr(hi_a, lo_a, cl)
        atr_pct  = round(atr_val / close_now * 100, 2) if atr_val and close_now > 0 else None
        bb_d     = _bollinger(cl)
        obv_dir  = _obv_slope(cl, vo_a.fillna(0))
        adx_d    = _adx(hi_a, lo_a, cl)

        rec: dict = {
            "symbol":        sym,
            "close_now":     round(close_now, 2),
            "high_52w":      round(high_52w, 2),
            "low_52w":       round(low_52w, 2),
            "prox_52w_high": prox_52w_high,
            "prox_52w_low":  prox_52w_low,
            "dma_20":        dma_20,
            "dma_50":        dma_50,
            "dma_200":       dma_200,
            "vs_dma_20":     vs_dma_20,
            "vs_dma_50":     vs_dma_50,
            "vs_dma_200":    vs_dma_200,
            "trend_signal":  trend,
            "vol_20d_avg":   vol_20d_avg,
            # RSI
            "rsi":           rsi_val,
            "rsi_signal":    rsi_sig,
            # MACD
            "macd_line":     macd_d.get("macd_line"),
            "macd_signal":   macd_d.get("macd_signal"),
            "macd_hist":     macd_d.get("macd_hist"),
            "macd_cross":    macd_d.get("macd_cross", ""),
            # ATR
            "atr_14":        atr_val,
            "atr_pct":       atr_pct,
            # Bollinger Bands
            "bb_upper":      bb_d.get("bb_upper"),
            "bb_lower":      bb_d.get("bb_lower"),
            "bb_mid":        bb_d.get("bb_mid"),
            "bb_pct":        bb_d.get("bb_pct"),
            "bb_width":      bb_d.get("bb_width"),
            "bb_signal":     bb_d.get("bb_signal", ""),
            "bb_squeeze":    bb_d.get("bb_squeeze", False),
            # OBV
            "obv_signal":    obv_dir,
            # ADX
            "adx":           adx_d.get("adx"),
            "adx_plus_di":   adx_d.get("adx_plus_di"),
            "adx_minus_di":  adx_d.get("adx_minus_di"),
            "adx_strength":  adx_d.get("adx_strength", ""),
            "adx_direction": adx_d.get("adx_direction", ""),
            "as_of_date":    as_of_date,
        }
        records.append(rec)

    if not records:
        return {"status": "ERROR", "error": "No indicators computed"}

    df_out = pd.DataFrame(records)
    cfg.INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = OUTPUT.with_suffix(".tmp.csv")
    df_out.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(OUTPUT))
    logger.info("[Technical] Saved %d rows → %s", len(df_out), OUTPUT.name)
    return {"status": "DONE", "symbols": len(df_out), "as_of_date": as_of_date}


if __name__ == "__main__":
    r = run()
    print(f"Status:  {r['status']}")
    print(f"Symbols: {r.get('symbols', 0)}")
    print(f"As of:   {r.get('as_of_date', '')}")
    if r.get("error"):
        print(f"Error:   {r['error']}")
