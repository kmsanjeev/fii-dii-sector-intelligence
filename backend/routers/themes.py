"""
Themes Router — Phase E
GET /api/themes          — all 50 themes (10 categories) with intelligence scores
GET /api/themes/{theme}  — detailed view with enriched top picks
"""

import json
import math
import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.services import data_loader

router = APIRouter(prefix="/api/themes", tags=["themes"])


def _safe(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _clean(rec: dict) -> dict:
    return {k: (_safe(v) if isinstance(v, float) else v) for k, v in rec.items()}


def _parse_picks(raw) -> list:
    if not raw or (isinstance(raw, float) and math.isnan(raw)):
        return []
    try:
        return json.loads(str(raw))
    except Exception:
        return []


@router.get("")
def get_themes():
    df = data_loader.get("theme_intelligence")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="theme_intelligence not loaded")

    themes = []
    for _, row in df.iterrows():
        t = _clean(row.to_dict())
        t["sectors"] = [s.strip() for s in str(t.get("sectors", "")).split(",") if s.strip()]
        t["top_picks"] = _parse_picks(t.get("top_picks"))
        themes.append(t)

    return {"count": len(themes), "themes": themes}


@router.get("/{theme_code}")
def get_theme_detail(theme_code: str):
    df = data_loader.get("theme_intelligence")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="theme_intelligence not loaded")

    code = theme_code.upper()
    matched = df[df["theme"].str.upper() == code]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Theme '{code}' not found")

    row = _clean(matched.iloc[0].to_dict())
    row["sectors"] = [s.strip() for s in str(row.get("sectors", "")).split(",") if s.strip()]
    row["top_picks"] = _parse_picks(row.get("top_picks"))

    # Enrich top picks with current stock data
    bull_df = data_loader.get("bull_run")
    if bull_df is not None and row["top_picks"]:
        picks_syms = [p["symbol"] for p in row["top_picks"]]
        bull_rows  = bull_df[bull_df["symbol"].isin(picks_syms)]
        picks_enriched = []
        for pick in row["top_picks"]:
            br = bull_rows[bull_rows["symbol"] == pick["symbol"]]
            extra = {}
            if not br.empty:
                r = br.iloc[0]
                extra = {
                    "close_now":  _safe(r.get("close_now")),
                    "ret_30d":    _safe(r.get("ret_30d")),
                    "ret_365d":   _safe(r.get("ret_365d")),
                    "sector":     str(r.get("sector", "")),
                }
            picks_enriched.append({**pick, **extra})
        row["top_picks"] = picks_enriched

    return row


@router.get("/{theme_code}/stocks")
def get_theme_stocks(theme_code: str, limit: int = 50):
    """Return all stocks tagged to a theme, sorted by purity-weighted bull score."""
    code = theme_code.upper()

    tagging_df = data_loader.get("theme_tagging")
    if tagging_df is None or tagging_df.empty:
        raise HTTPException(status_code=503, detail="theme_tagging not loaded")

    tagged = tagging_df[tagging_df["THEME"].str.upper() == code].copy()
    if tagged.empty:
        raise HTTPException(status_code=404, detail=f"Theme '{code}' not found in tagging")

    # Enrich with bull run data
    bull_df = data_loader.get("bull_run")
    if bull_df is not None:
        bull_df_up = bull_df.copy()
        bull_df_up["symbol"] = bull_df_up["symbol"].str.upper()
        tagged = tagged.merge(
            bull_df_up[["symbol", "bull_run_score", "label", "close_now", "sector",
                        "ret_30d", "ret_365d"]].rename(columns={"symbol": "SYMBOL"}),
            on="SYMBOL", how="left"
        )

    # Purity-weighted sort score
    if "bull_run_score" in tagged.columns and "PURITY_SCORE" in tagged.columns:
        tagged["_sort"] = tagged["bull_run_score"].fillna(0) * tagged["PURITY_SCORE"].fillna(0)
        tagged = tagged.sort_values("_sort", ascending=False).drop(columns=["_sort"])

    tagged = tagged.head(limit)
    records = []
    for _, r in tagged.iterrows():
        rec = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.to_dict().items()}
        records.append(rec)

    return {"theme": code, "count": len(records), "stocks": records}
