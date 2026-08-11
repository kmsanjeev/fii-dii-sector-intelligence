"""
Data Tools -- Phase 14A (+ Phase V-DATA, full-coverage expansion)
Structured data-access tools called by the chatbot to answer domain questions.
These are the bridge between natural language intent and intelligence CSVs.

All tools return plain Python dicts/lists (JSON-serializable).
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from engines.common import config as cfg
from engines.common.astrology_safety import present_astrofinance_signal
from engines.common.logger import get_logger

logger = get_logger(__name__)

INTEL = cfg.INTELLIGENCE_DIR

# Phase V-DATA -- previously-unreachable data sources wired into new tools
VALUATION_CSV   = cfg.NSE_DIR / "results" / "valuation_scores.csv"
EXT_FIN_CSV     = cfg.NSE_DIR / "results" / "extended_financials.csv"
QTR_RESULTS_CSV = cfg.NSE_DIR / "results" / "quarterly_results.csv"
SHP_CSV         = cfg.NSE_DIR / "shareholding" / "quarterly_shp.csv"
HOLDING_TRENDS_CSV   = cfg.NSE_DIR / "shareholding" / "holding_trends.csv"
MGMT_SENTIMENT_CSV   = cfg.NSE_DIR / "shareholding" / "management_sentiment.csv"
ANNOUNCEMENTS_CSV    = INTEL / "company_announcements.csv"
ANNOUNCEMENT_SIG_CSV = INTEL / "announcement_signals.csv"
CORP_ACTIONS_CSV     = INTEL / "corporate_action_signals.csv"
CONVICTION_CSV       = INTEL / "conviction_screener.csv"
DEAL_RECORDS_CSV     = INTEL / "deal_records.csv"


def _load(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        logger.warning(f"[DataTools] File missing: {path}")
        return None
    df = pd.read_csv(path)
    return df if not df.empty else None


def _clean(val: Any) -> Any:
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def _row_to_dict(row: pd.Series) -> dict:
    return {k: _clean(v) for k, v in row.items()}


# ------------------------------------------------------------------
# Market tools
# ------------------------------------------------------------------

def get_market_regime() -> dict:
    """Returns latest market regime and participant flow scores."""
    df = _load(INTEL / "participant_intelligence.csv")
    if df is None:
        return {"error": "participant_intelligence.csv not available"}
    latest = df.sort_values("date").iloc[-1]
    return _row_to_dict(latest)


def get_participant_history(n_days: int = 30) -> list[dict]:
    """Returns last n_days of participant flow data."""
    df = _load(INTEL / "participant_intelligence.csv")
    if df is None:
        return []
    df = df.sort_values("date").tail(n_days)
    return [_row_to_dict(r) for _, r in df.iterrows()]


# ------------------------------------------------------------------
# Sector tools
# ------------------------------------------------------------------

def get_all_sectors() -> list[dict]:
    """Returns all sectors with rotation signals and flow scores."""
    df = _load(INTEL / "sector_rotation_intelligence.csv")
    if df is None:
        return []
    return [_row_to_dict(r) for _, r in df.iterrows()]


def get_sector_detail(sector: str) -> dict:
    """Returns details for a specific sector."""
    df = _load(INTEL / "sector_rotation_intelligence.csv")
    if df is None:
        return {"error": "sector data unavailable"}
    matches = df[df["sector"].str.upper() == sector.upper()]
    if matches.empty:
        return {"error": f"Sector '{sector}' not found"}
    return _row_to_dict(matches.iloc[0])


def get_sectors_by_signal(signal: str) -> list[dict]:
    """Returns sectors matching a rotation signal (e.g. EARLY_ROTATION, LEADING)."""
    df = _load(INTEL / "sector_rotation_intelligence.csv")
    if df is None:
        return []
    matches = df[df["rotation_signal"].str.upper() == signal.upper()]
    return [_row_to_dict(r) for _, r in matches.iterrows()]


# ------------------------------------------------------------------
# Stock tools
# ------------------------------------------------------------------

# Full technical field set (Phase TI) -- RSI/MACD/ATR/Bollinger/ADX/OBV exist
# in technical_indicators.csv but were previously never exposed to any tool;
# only trend_signal/vs_dma_200/prox_52w_high/close_now made it through.
FULL_TECH_COLS = [
    "trend_signal", "close_now", "vs_dma_20", "vs_dma_50", "vs_dma_200",
    "prox_52w_high", "prox_52w_low", "high_52w", "low_52w",
    "rsi", "rsi_signal", "macd_line", "macd_signal", "macd_hist", "macd_cross",
    "atr_pct", "bb_pct", "bb_signal", "bb_squeeze",
    "adx", "adx_strength", "adx_direction", "obv_signal",
]


def _enrich_with_technical(df_rows: list[dict]) -> list[dict]:
    """Add the full technical indicator set (trend, DMA, 52W range, RSI,
    MACD, ATR, Bollinger Bands, ADX, OBV) plus watchlist decision metrics
    (RVOL, relative strength, delivery%) to each row."""
    tech = _load(INTEL / "technical_indicators.csv")
    if tech is not None:
        tech_idx = tech.set_index("symbol")
        for row in df_rows:
            sym = row.get("symbol", "")
            if sym and sym in tech_idx.index:
                t = tech_idx.loc[sym]
                for col in FULL_TECH_COLS:
                    row[col] = _clean(t.get(col))
    return _enrich_with_watchlist_metrics(df_rows)


def _enrich_with_watchlist_metrics(df_rows: list[dict]) -> list[dict]:
    """Add RVOL, 30D relative strength vs NIFTY 50, and 5D delivery% to each row."""
    wm = _load(INTEL / "watchlist_metrics.csv")
    if wm is None:
        return df_rows
    wm_idx = wm.set_index("symbol")
    for row in df_rows:
        sym = row.get("symbol", "")
        if sym and sym in wm_idx.index:
            w = wm_idx.loc[sym]
            row["rvol"]             = _clean(w.get("rvol"))
            row["rs_30d_vs_nifty"]  = _clean(w.get("rs_30d"))
            row["delivery_5d_pct"]  = _clean(w.get("delivery_5d_pct"))
    return df_rows


def get_top_stocks(label: str = "EMERGING", top_n: int = 20) -> list[dict]:
    """
    Returns top stocks by bull_run_score for a given label, enriched with
    ML scores and key technical signals for cross-validation.
    Current valid labels: BULL_RUN, EMERGING, WATCHLIST, NEUTRAL, ACCUMULATION, MARKDOWN.
    """
    df = _load(INTEL / "bull_run_probability.csv")
    if df is None:
        return []
    filtered = df[df["label"].str.upper() == label.upper()]
    top = filtered.nlargest(top_n, "bull_run_score")
    rows = [_row_to_dict(r) for _, r in top.iterrows()]

    # Enrich with ML scores
    ml = _load(INTEL / "ml_scores_combined.csv")
    if ml is not None:
        ml_idx = ml.set_index("symbol")
        for row in rows:
            sym = row.get("symbol", "")
            if sym and sym in ml_idx.index:
                m = ml_idx.loc[sym]
                row["ml_bull_run_score"] = _clean(m.get("ml_bull_run_score"))
                row["accumulation_score"] = _clean(m.get("accumulation_score"))

    return _enrich_with_technical(rows)


def get_fno_stocks(signal: str = "LONG_BUILDUP", top_n: int = 20) -> list[dict]:
    """
    Returns F&O stocks filtered by OI signal, sorted by 5-day OI change.
    Only stocks in fno_intelligence.csv are genuine F&O (futures & options) stocks.
    Valid signals: LONG_BUILDUP, SHORT_BUILDUP, LONG_UNWINDING, SHORT_COVERING.
    LONG_BUILDUP = rising price + rising OI = bullish conviction.
    SHORT_COVERING = falling OI + rising price = short squeeze.
    """
    fno = _load(INTEL / "fno_intelligence.csv")
    if fno is None:
        return []
    filtered = fno[fno["oi_signal"].str.upper() == signal.upper()]
    top = filtered.nlargest(top_n, "oi_5d")
    rows = [_row_to_dict(r) for _, r in top.iterrows()]

    # Enrich with bull_run score + sector
    br = _load(INTEL / "bull_run_probability.csv")
    if br is not None:
        br_idx = br.set_index("symbol")
        for row in rows:
            sym = row.get("symbol", "")
            if sym and sym in br_idx.index:
                b = br_idx.loc[sym]
                row["bull_run_score"] = _clean(b.get("bull_run_score"))
                row["label"]          = _clean(b.get("label"))
                row["sector"]         = _clean(b.get("sector"))

    return _enrich_with_technical(rows)


def get_stock_detail(symbol: str) -> dict:
    """Returns full intelligence profile for a stock symbol."""
    br = _load(INTEL / "bull_run_probability.csv")
    if br is None:
        return {"error": "bull_run_probability.csv not available"}

    match = br[br["symbol"].str.upper() == symbol.upper()]
    if match.empty:
        return {"error": f"Symbol '{symbol}' not found"}

    result = _row_to_dict(match.iloc[0])

    # Enrich with ML scores
    ml = _load(INTEL / "ml_scores_combined.csv")
    if ml is not None:
        ml_match = ml[ml["symbol"].str.upper() == symbol.upper()]
        if not ml_match.empty:
            ml_row = _row_to_dict(ml_match.iloc[0])
            result["ml_bull_run_score"] = ml_row.get("ml_bull_run_score")
            result["accumulation_score"] = ml_row.get("accumulation_score")

    # Enrich with the full technical indicator set + watchlist metrics
    # (same helper used by get_top_stocks/get_fno_stocks/get_stocks_by_sector
    # -- previously this pulled a different, smaller subset than those tools,
    # an inconsistency that made Veda's answers vary by which tool she used).
    result = _enrich_with_technical([result])[0]

    # Enrich with corporate confidence
    corp = _load(INTEL / "corporate_confidence_scores.csv")
    if corp is not None:
        corp_match = corp[corp["symbol"].str.upper() == symbol.upper()]
        if not corp_match.empty:
            result["confidence_score_12m"] = _clean(corp_match.iloc[0].get("confidence_score_12m"))

    return result


def get_stocks_by_sector(sector: str, top_n: int = 10) -> list[dict]:
    """Returns top stocks in a sector by bull_run_score."""
    df = _load(INTEL / "bull_run_probability.csv")
    if df is None:
        return []
    matches = df[df["sector"].str.upper() == sector.upper()]
    top = matches.nlargest(top_n, "bull_run_score")
    rows = [_row_to_dict(r) for _, r in top.iterrows()]
    return _enrich_with_technical(rows)


# ------------------------------------------------------------------
# AstroFinance tools
# ------------------------------------------------------------------

def get_astro_signal(sector: Optional[str] = None) -> dict:
    """
    Returns AstroFinance planetary signals for a sector or full market context.
    Shows ruling planet status, retrograde warnings, aspect quality, and a bounded AstroFinance heuristic label.
    """
    import json
    from pathlib import Path

    result: dict = {}

    # Market-level astro context
    ctx_path = INTEL / "market_astro_context.json"
    if ctx_path.exists():
        try:
            with open(ctx_path, encoding="utf-8") as f:
                ctx = json.load(f)
            result["market_astro_signal"] = ctx.get("market_astro_signal")
            result["market_astro_score"]  = ctx.get("market_astro_score")
            result["mercury_retrograde"]  = ctx.get("mercury_retrograde")
            result["venus_retrograde"]    = ctx.get("venus_retrograde")
            result["moon_phase"]          = ctx.get("moon_phase")
            result["moon_illumination"]   = ctx.get("moon_illumination")
            result["jupiter_sign"]        = ctx.get("jupiter_sign")
            result["saturn_sign"]         = ctx.get("saturn_sign")
            result["eclipse_active"]      = ctx.get("eclipse_active")
            result["eclipse_signal"]      = ctx.get("eclipse_signal")
            result["reversal_note"]       = ctx.get("reversal_note")
            result["planet_positions"]    = ctx.get("planet_positions")
            result["computed_date"]       = ctx.get("computed_date")
        except Exception as e:
            result["error_context"] = str(e)

    # Sector-level signals
    sector_df = _load(INTEL / "astro_signals.csv")
    if sector_df is not None:
        if sector:
            matches = sector_df[sector_df["sector"].str.upper() == sector.upper()]
            if not matches.empty:
                r = matches.iloc[0]
                result["sector"]           = str(r.get("sector", ""))
                result["ruling_planets"]   = str(r.get("ruling_planets", ""))
                result["primary_planet"]   = str(r.get("primary_planet", ""))
                result["planet_sign"]      = str(r.get("planet_sign", ""))
                result["planet_state"]     = str(r.get("planet_state", ""))
                result["planet_retrograde"]= bool(r.get("planet_retrograde", False))
                result["key_aspects"]      = str(r.get("key_aspects", ""))
                result["astro_score"]      = float(r.get("astro_score", 0) or 0)
                result["astro_action"]     = str(r.get("astro_action", "HOLD"))
                result["astro_reason"]     = str(r.get("astro_reason", ""))
                result = present_astrofinance_signal(result)
            else:
                result["sector_error"] = f"Sector '{sector}' not found in astro signals"
        else:
            # Return all sectors sorted by astro_score
            top = sector_df.sort_values("astro_score", ascending=False)
            result["all_sectors"] = [
                present_astrofinance_signal({
                    "sector":       str(r["sector"]),
                    "primary_planet": str(r["primary_planet"]),
                    "planet_state": str(r["planet_state"]),
                    "astro_score":  round(float(r.get("astro_score", 0) or 0), 1),
                    "astro_action": str(r["astro_action"]),
                })
                for _, r in top.iterrows()
            ]

    return result if result else {"error": "astro_signals.csv and market_astro_context.json not yet generated. Run astro_engine.py first."}


# ------------------------------------------------------------------
# Deal tools
# ------------------------------------------------------------------

def get_institutional_deals(top_n: int = 20, min_value_cr: float = 10.0) -> list[dict]:
    """Returns institutional deals above a threshold value."""
    df = _load(INTEL / "institutional_deal_signals.csv")
    if df is None:
        return []
    if "inst_net_value_cr" in df.columns:
        df = df[df["inst_net_value_cr"].abs() >= min_value_cr]
    top = df.nlargest(top_n, "inst_net_value_cr") if "inst_net_value_cr" in df.columns else df.head(top_n)
    return [_row_to_dict(r) for _, r in top.iterrows()]


# ------------------------------------------------------------------
# Corporate tools
# ------------------------------------------------------------------

def get_top_corporate_confidence(top_n: int = 20) -> list[dict]:
    """Returns stocks with highest corporate confidence scores."""
    df = _load(INTEL / "corporate_confidence_scores.csv")
    if df is None:
        return []
    col = "confidence_score_12m" if "confidence_score_12m" in df.columns else df.columns[-1]
    top = df.nlargest(top_n, col)
    return [_row_to_dict(r) for _, r in top.iterrows()]


def get_corporate_catalysts(upcoming_days: int = 30) -> list[dict]:
    """Returns upcoming corporate catalysts/events."""
    df = _load(INTEL / "event_calendar.csv")
    if df is None:
        return []
    date_col = "event_date" if "event_date" in df.columns else "date"
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        today = pd.Timestamp.now().normalize()
        cutoff = today + pd.Timedelta(days=upcoming_days)
        df = df[(df[date_col] >= today) & (df[date_col] <= cutoff)]
        df = df.sort_values(date_col)
    return [_row_to_dict(r) for _, r in df.head(50).iterrows()]


# ------------------------------------------------------------------
# Fundamentals & valuation (Phase V-DATA)
# ------------------------------------------------------------------

def get_stock_fundamentals(symbol: str) -> dict:
    """
    Returns valuation (P/E, P/B, ROE, valuation label), extended financials
    (OPM%, ROCE%, book value/share, sales growth CAGR), and the most recent
    quarterly result (revenue, net profit, EPS) for a stock.
    """
    sym = symbol.upper()
    result: dict = {"symbol": sym}
    found = False

    val = _load(VALUATION_CSV)
    if val is not None:
        m = val[val["symbol"].str.upper() == sym]
        if not m.empty:
            found = True
            r = _row_to_dict(m.iloc[0])
            result.update({
                "pe_ratio": r.get("pe_ratio"), "pb_ratio": r.get("pb_ratio"),
                "roe_pct": r.get("roe_pct"), "valuation_label": r.get("valuation_label"),
                "revenue_ttm_cr": r.get("revenue_ttm_cr"), "profit_ttm_cr": r.get("profit_ttm_cr"),
                "yoy_revenue_pct": r.get("yoy_revenue_pct"), "yoy_profit_pct": r.get("yoy_profit_pct"),
            })

    ext = _load(EXT_FIN_CSV)
    if ext is not None:
        m = ext[ext["symbol"].str.upper() == sym]
        if not m.empty:
            found = True
            r = _row_to_dict(m.iloc[0])
            result.update({
                "opm_pct": r.get("opm_pct"), "roce_pct": r.get("roce_pct"),
                "book_value_per_share": r.get("book_value_per_share"),
                "sales_growth_cagr_pct": r.get("sales_growth_cagr_pct"),
            })

    qr = _load(QTR_RESULTS_CSV)
    if qr is not None:
        m = qr[qr["symbol"].str.upper() == sym].copy()
        if not m.empty:
            found = True
            m["date_end"] = pd.to_datetime(m["date_end"], errors="coerce")
            latest = m.sort_values("date_end", ascending=False).iloc[0]
            result["latest_quarter"] = {
                "quarter_label": _clean(latest.get("quarter_label")),
                "revenue_cr": _clean(latest.get("revenue_cr")),
                "net_profit_cr": _clean(latest.get("net_profit_cr")),
                "eps": _clean(latest.get("eps")),
            }

    if not found:
        return {"error": f"No fundamentals data found for '{sym}'"}
    return result


# ------------------------------------------------------------------
# Shareholding pattern (Phase V-DATA)
# ------------------------------------------------------------------

def get_shareholding_pattern(symbol: str) -> dict:
    """
    Returns the last 4 quarters of promoter/FII/DII/public shareholding %
    plus the latest QoQ deltas and a conviction_signal (INCREASING/
    DECREASING/STABLE institutional or promoter stake).
    """
    sym = symbol.upper()
    result: dict = {"symbol": sym}

    shp = _load(SHP_CSV)
    if shp is not None:
        m = shp[shp["symbol"].str.upper() == sym].copy()
        if not m.empty:
            m["quarter_end_date"] = pd.to_datetime(m["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
            m = m.sort_values("quarter_end_date", ascending=False).head(4)
            result["quarterly_history"] = [
                {
                    "quarter_end": str(r["quarter_end_date"].date()) if pd.notna(r["quarter_end_date"]) else None,
                    "promoter_pct": _clean(r.get("promoter_pct")),
                    "fii_pct": _clean(r.get("fii_pct")),
                    "dii_pct": _clean(r.get("dii_pct")),
                    "public_pct": _clean(r.get("public_pct")),
                }
                for _, r in m.iterrows()
            ]

    trends = _load(HOLDING_TRENDS_CSV)
    if trends is not None:
        m = trends[trends["symbol"].str.upper() == sym].copy()
        if not m.empty:
            m["quarter_end_date"] = pd.to_datetime(m["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
            latest = m.sort_values("quarter_end_date", ascending=False).iloc[0]
            result["promoter_delta_qoq"] = _clean(latest.get("promoter_delta"))
            result["fii_delta_qoq"]      = _clean(latest.get("fii_delta"))
            result["dii_delta_qoq"]      = _clean(latest.get("dii_delta"))
            result["conviction_signal"]  = _clean(latest.get("conviction_signal"))

    if "quarterly_history" not in result and "conviction_signal" not in result:
        return {"error": f"No shareholding data found for '{sym}'"}
    return result


# ------------------------------------------------------------------
# Announcements & management sentiment (Phase V-DATA)
# ------------------------------------------------------------------

def get_stock_announcements(symbol: str, days: int = 30) -> dict:
    """
    Returns recent NSE corporate announcements for a stock (signal-scored:
    results, board outcomes, management changes, acquisitions, regulatory
    filings) plus a 30D/90D announcement-activity summary.
    """
    sym = symbol.upper()
    result: dict = {"symbol": sym}

    ann = _load(ANNOUNCEMENTS_CSV)
    if ann is not None:
        m = ann[ann["symbol"].str.upper() == sym].copy()
        if not m.empty:
            cutoff = (pd.Timestamp.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
            m = m[m["date"] >= cutoff].sort_values("date", ascending=False)
            result["recent_announcements"] = [
                {
                    "date": _clean(r.get("date")),
                    "type": _clean(r.get("announcement_type")),
                    "signal_score": _clean(r.get("signal_score")),
                    "summary": _clean(r.get("title_snippet")),
                }
                for _, r in m.head(20).iterrows()
            ]

    sig = _load(ANNOUNCEMENT_SIG_CSV)
    if sig is not None:
        m = sig[sig["symbol"].str.upper() == sym]
        if not m.empty:
            r = _row_to_dict(m.iloc[0])
            result["dominant_type_30d"] = r.get("dominant_type")
            result["score_30d"]         = r.get("score_30d")
            result["count_30d"]         = r.get("count_30d")
            result["count_90d"]         = r.get("count_90d")
            result["high_signal_30d"]   = r.get("high_signal_30d")

    if "recent_announcements" not in result and "score_30d" not in result:
        return {"error": f"No announcements found for '{sym}' in the last {days} days"}
    return result


def get_management_sentiment(symbol: str) -> dict:
    """
    Returns AI-scored management tone/sentiment (Claude-analysed from board
    announcements and holding trends): holding_signal, ai_tone_score,
    management_score, management_label.
    """
    sym = symbol.upper()
    df = _load(MGMT_SENTIMENT_CSV)
    if df is None:
        return {"error": "management_sentiment.csv not available"}
    m = df[df["symbol"].str.upper() == sym]
    if m.empty:
        return {"error": f"No management sentiment data for '{sym}'"}
    return _row_to_dict(m.iloc[0])


# ------------------------------------------------------------------
# Historical corporate actions (Phase V-DATA)
# ------------------------------------------------------------------

def get_corporate_action_history(symbol: str, years: int = 5) -> list[dict]:
    """
    Returns historical corporate actions (dividends, bonuses, splits,
    buybacks, rights issues) for a stock over the last N years, most
    recent first.
    """
    sym = symbol.upper()
    df = _load(CORP_ACTIONS_CSV)
    if df is None:
        return []
    m = df[df["symbol"].str.upper() == sym].copy()
    if m.empty:
        return []
    m["ex_date_dt"] = pd.to_datetime(m["ex_date_dt"], errors="coerce")
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=365 * years)
    m = m[m["ex_date_dt"] >= cutoff].sort_values("ex_date_dt", ascending=False)
    cols = ["ex_date", "action_type", "dividend_rs", "bonus_ratio", "split_new_fv", "subject"]
    m = m[[c for c in cols if c in m.columns]]
    return [_row_to_dict(r) for _, r in m.head(30).iterrows()]


# ------------------------------------------------------------------
# Conviction screener (Phase V-DATA -- exposes Phase SA-1's flagship output)
# ------------------------------------------------------------------

def get_conviction_picks(tier: Optional[str] = None, top_n: int = 20) -> list[dict]:
    """
    Returns the platform's efficacy-weighted conviction screener: stocks
    ranked by a composite score backtested against realized forward returns
    (Information Coefficient per factor), with supporting evidence and the
    primary risk flag for each pick. Tiers: HIGH, MEDIUM, WATCH.
    This is the platform's single most rigorously validated signal --
    prefer it over get_top_stocks for "what should I actually invest in"
    style questions.
    """
    df = _load(CONVICTION_CSV)
    if df is None:
        return []
    if tier:
        df = df[df["tier"].str.upper() == tier.upper()]
    df = df.sort_values("rank").head(top_n)
    return [_row_to_dict(r) for _, r in df.iterrows()]


# ------------------------------------------------------------------
# Deal tape (Phase V-DATA -- sequence-paired transactions, Phase UI-C)
# ------------------------------------------------------------------

def get_deal_tape(symbol: Optional[str] = None, top_n: int = 15) -> list[dict]:
    """
    Returns individual client block/bulk deal transactions, sequence-paired
    into LONG_BUILD_SQUAREOFF / SHORT_BUILD_COVER / BUY_ONLY / SELL_ONLY
    records (same-day same-client legs matched FIFO within 1% quantity
    tolerance -- see block_bulk_deal_engine.py). Filter by symbol for a
    specific stock's deal history, or omit for the largest deals market-wide.
    """
    df = _load(DEAL_RECORDS_CSV)
    if df is None:
        return []
    if symbol:
        df = df[df["symbol"].str.upper() == symbol.upper()]
    df = df.sort_values(["date", "gross_value_cr"], ascending=[False, False]).head(top_n)
    return [_row_to_dict(r) for _, r in df.iterrows()]


# ------------------------------------------------------------------
# Raw price history (Phase V-DATA)
# ------------------------------------------------------------------

def get_price_history(symbol: str, days: int = 90) -> dict:
    """
    Returns daily OHLCV price history for a stock -- the actual candle data,
    for exact moving-average crossovers, specific-date prices, or manual
    trend verification that derived scores can't answer.
    days is capped at 500 to keep the response manageable.
    """
    sym = symbol.upper()
    path = cfg.STOCK_HISTORY_CACHE / f"{sym}.parquet"
    if not path.exists():
        return {"error": f"No price history cached for '{sym}'"}
    days = min(max(days, 1), 500)
    try:
        df = pd.read_parquet(path, columns=["date", "open", "high", "low", "close", "volume"])
    except Exception as e:
        return {"error": f"Failed to read price history: {e}"}
    df = df.tail(days)
    return {
        "symbol": sym,
        "sessions": len(df),
        "candles": [
            {
                "date": str(r["date"])[:10],
                "open": _clean(r["open"]), "high": _clean(r["high"]),
                "low": _clean(r["low"]), "close": _clean(r["close"]),
                "volume": _clean(r["volume"]),
            }
            for _, r in df.iterrows()
        ],
    }


# ------------------------------------------------------------------
# Technical screener (Phase V-DATA)
# ------------------------------------------------------------------

_TECH_SCREEN_MAP = {
    "OVERSOLD":       ("rsi_signal", "OVERSOLD"),
    "OVERBOUGHT":     ("rsi_signal", "OVERBOUGHT"),
    "BULLISH_MACD":   ("macd_cross", "BULLISH"),
    "BEARISH_MACD":   ("macd_cross", "BEARISH"),
    "BB_SQUEEZE":     ("bb_squeeze", True),
    "STRONG_TREND":   ("adx_strength", "STRONG"),
}


def get_technical_screener(condition: str = "OVERSOLD", top_n: int = 20) -> list[dict]:
    """
    Screens the universe by a technical condition. Valid conditions:
    OVERSOLD (RSI<30, potential bounce), OVERBOUGHT (RSI>70, potential
    pullback), BULLISH_MACD (MACD line crossed above signal), BEARISH_MACD
    (crossed below), BB_SQUEEZE (Bollinger Bands compressed -- breakout
    setup), STRONG_TREND (ADX>25 -- trending, not choppy).
    """
    df = _load(INTEL / "technical_indicators.csv")
    if df is None:
        return []
    key = condition.upper()
    if key not in _TECH_SCREEN_MAP:
        return [{"error": f"Unknown condition '{condition}'. Valid: {list(_TECH_SCREEN_MAP)}"}]
    col, val = _TECH_SCREEN_MAP[key]
    if col not in df.columns:
        return []
    matches = df[df[col] == val]
    sort_col = "rsi" if key in ("OVERSOLD", "OVERBOUGHT") else "adx" if key == "STRONG_TREND" else "symbol"
    ascending = key == "OVERSOLD"
    if sort_col in matches.columns:
        matches = matches.sort_values(sort_col, ascending=ascending)
    cols = ["symbol", "close_now", "rsi", "rsi_signal", "macd_cross", "bb_squeeze",
            "adx", "adx_strength", "trend_signal"]
    matches = matches[[c for c in cols if c in matches.columns]]
    return [_row_to_dict(r) for _, r in matches.head(top_n).iterrows()]


# ------------------------------------------------------------------
# Personal Kundli tool
# ------------------------------------------------------------------

def generate_personal_kundli(
    date_of_birth: str,
    time_of_birth: str,
    place_name: str,
    latitude:  Optional[float] = None,
    longitude: Optional[float] = None,
    timezone_offset_hours: float = 5.5,
) -> dict:
    """
    Compute a complete Vedic natal chart for a person.
    Uses Swiss Ephemeris + exact Lahiri ayanamsha + whole-sign houses +
    Vimshottari dasha -- the same calculation core used for stock/company
    Kundlis, so a person's chart and a stock's chart are always consistent.

    Args:
        date_of_birth: "DD-MM-YYYY" or "YYYY-MM-DD"
        time_of_birth: "HH:MM" or "HH:MM:SS" (24-hr local time). "unknown" if not known.
        place_name: City of birth (auto lat/lon lookup for 80+ Indian + global cities)
        latitude/longitude: Optional override if city not found
        timezone_offset_hours: UTC offset (default 5.5 = IST)
    """
    try:
        from engines.intelligence.jyotisha_runtime import get_jyotisha_runtime_service
        from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli
        try:
            return get_jyotisha_runtime_service().compute_personal_chart(
                date_of_birth=date_of_birth,
                time_of_birth=time_of_birth,
                place_name=place_name,
                latitude=latitude,
                longitude=longitude,
                timezone_offset_hours=timezone_offset_hours,
            ).legacy_payload
        except Exception:
            return compute_personal_kundli(
                date_of_birth=date_of_birth,
                time_of_birth=time_of_birth,
                place_name=place_name,
                latitude=latitude,
                longitude=longitude,
                timezone_offset_hours=timezone_offset_hours,
            )
    except ImportError as e:
        return {"error": f"kundli_calculator import failed: {e}. Ensure pyswisseph is installed: py -3.11 -m pip install pyswisseph"}
    except Exception as e:
        return {"error": f"Kundli computation failed: {e}"}
