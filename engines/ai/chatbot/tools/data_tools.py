"""
Data Tools -- Phase 14A
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
from engines.common.logger import get_logger

logger = get_logger(__name__)

INTEL = cfg.INTELLIGENCE_DIR


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

def _enrich_with_technical(df_rows: list[dict]) -> list[dict]:
    """Add key technical fields (trend_signal, vs_dma_200, prox_52w_high) to each row."""
    tech = _load(INTEL / "technical_indicators.csv")
    if tech is None:
        return df_rows
    tech_idx = tech.set_index("symbol")
    for row in df_rows:
        sym = row.get("symbol", "")
        if sym and sym in tech_idx.index:
            t = tech_idx.loc[sym]
            row["trend_signal"]  = _clean(t.get("trend_signal"))
            row["vs_dma_200"]    = _clean(t.get("vs_dma_200"))
            row["prox_52w_high"] = _clean(t.get("prox_52w_high"))
            row["close_now"]     = _clean(t.get("close_now"))
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

    # Enrich with technical indicators — critical for trend validation
    tech = _load(INTEL / "technical_indicators.csv")
    if tech is not None:
        tech_match = tech[tech["symbol"].str.upper() == symbol.upper()]
        if not tech_match.empty:
            t = tech_match.iloc[0]
            result["trend_signal"]  = _clean(t.get("trend_signal"))
            result["vs_dma_20"]     = _clean(t.get("vs_dma_20"))
            result["vs_dma_50"]     = _clean(t.get("vs_dma_50"))
            result["vs_dma_200"]    = _clean(t.get("vs_dma_200"))
            result["prox_52w_high"] = _clean(t.get("prox_52w_high"))
            result["prox_52w_low"]  = _clean(t.get("prox_52w_low"))
            result["close_now"]     = _clean(t.get("close_now"))
            result["high_52w"]      = _clean(t.get("high_52w"))
            result["low_52w"]       = _clean(t.get("low_52w"))

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
