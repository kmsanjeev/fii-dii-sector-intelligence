"""
Stocks Router — Phase 10
GET /api/stocks/watchlist             — EMERGING+ watchlist (sorted by score)
GET /api/stocks/{symbol}              — full bull run breakdown for one symbol
GET /api/stocks/{symbol}/momentum     — price momentum detail
GET /api/stocks                       — all 2441 symbols (paginated)
"""

import math
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from backend.services import data_loader


def _clean(records):
    cleaned = []
    for rec in records:
        cleaned.append({
            k: (None if isinstance(v, float) and math.isnan(v) else v)
            for k, v in rec.items()
        })
    return cleaned


def _safe(v):
    """Return None for NaN floats so JSON serialization never fails."""
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _fmt_cr(v) -> str:
    """Format crore value as readable string."""
    if v is None:
        return "N/A"
    try:
        v = float(v)
        if v >= 100_000:
            return f"{v/100_000:.1f}L Cr"
        if v >= 1_000:
            return f"{v/1_000:.1f}K Cr"
        return f"{v:.0f} Cr"
    except Exception:
        return "N/A"


def _generate_insights(sym: str, row, fundamentals: dict, technical: dict,
                       shareholding: dict, holding_trends: list, fno: dict) -> list:
    insights = []
    label  = str(row.get("label", ""))
    score  = float(row.get("bull_run_score", 0) or 0)
    ret365 = _safe(row.get("ret_365d"))

    # 1 — Overall conviction (platform verdict in plain English)
    label_text = {
        "STRONG_CANDIDATE": f"Strong Opportunity — our intelligence rates this stock {score:.0f}/100. Multiple signals point to institutional accumulation.",
        "EMERGING":         f"Emerging Opportunity — rating {score:.0f}/100. Early-stage signals suggest smart money interest is building.",
        "WATCHLIST":        f"On the Watchlist — rating {score:.0f}/100. Interesting setup but needs more confirmation before entry.",
        "NEUTRAL":          f"No clear signal yet — rating {score:.0f}/100. Neither strongly attractive nor alarming at current levels.",
        "AVOID":            f"Caution advised — rating {score:.0f}/100. Multiple weak signals detected across the intelligence scorecard.",
    }
    if label in label_text:
        insights.append(label_text[label])

    # 2 — 1-year return (make it tangible with rupee example)
    if ret365 is not None:
        worth = 1 + ret365 / 100
        if ret365 >= 50:
            insights.append(f"Outstanding {ret365:.0f}% gain over the past year — if you had invested Rs 1 lakh a year ago, it would be worth Rs {worth:.1f} lakh today.")
        elif ret365 >= 20:
            insights.append(f"Good performer — up {ret365:.0f}% over the past year. Rs 1 lakh invested a year ago is now Rs {worth:.1f} lakh.")
        elif ret365 >= 5:
            insights.append(f"Modest gain of {ret365:.0f}% over the past year. Steady but below-average market returns.")
        elif ret365 >= -15:
            insights.append(f"Down {abs(ret365):.0f}% over the past year — currently underperforming. Monitor for recovery signals.")
        else:
            insights.append(f"Significant decline of {abs(ret365):.0f}% over the past year — high risk. Requires strong reason to stay invested.")

    # 3 — Price position vs key technical levels
    prox_high = technical.get("prox_52w_high")
    vs_200    = technical.get("vs_dma_200")
    if prox_high is not None and vs_200 is not None:
        if prox_high >= -5 and vs_200 >= 5:
            insights.append(f"Near its 52-week peak (only {abs(prox_high):.1f}% below) and {vs_200:.0f}% above its 200-day average — strong uptrend confirmed across all timeframes.")
        elif vs_200 >= 10:
            insights.append(f"Healthy uptrend: trading {vs_200:.0f}% above its 200-day moving average. Think of the 200-day average as the long-term direction indicator — being above it is positive.")
        elif abs(vs_200) <= 5:
            insights.append(f"At a key decision zone — hugging its 200-day average ({'+' if vs_200 >= 0 else ''}{vs_200:.0f}%). A breakout above could signal a new uptrend; a drop below would be bearish.")
        elif vs_200 < -10:
            insights.append(f"Still in a downtrend — {abs(vs_200):.0f}% below its 200-day average. Wait for the price to reclaim this level before considering a buy.")

    # 4 — Institutional ownership trends (latest quarter)
    if len(holding_trends) >= 2:
        latest = holding_trends[-1]
        fii_d  = latest.get("fii_delta")
        dii_d  = latest.get("dii_delta")
        pro_d  = latest.get("promoter_delta")
        period = latest.get("period", "last quarter")
        if fii_d is not None and dii_d is not None:
            if fii_d > 0.3 and dii_d > 0.3:
                insights.append(f"Strong institutional buying in {period} — foreign funds added {fii_d:.2f}% and domestic funds added {dii_d:.2f}%. When both camps accumulate together, it is a very strong signal.")
            elif fii_d > 0.2:
                insights.append(f"Foreign investor interest growing — FII stake rose {fii_d:.2f}% in {period}. Global funds typically do deep research before buying, so this signals confidence.")
            elif dii_d > 0.2:
                insights.append(f"Domestic funds accumulating — mutual funds and insurance companies added {dii_d:.2f}% in {period}. Local institutions see value here.")
            elif fii_d < -0.3:
                insights.append(f"Watch out: foreign investors reduced their stake by {abs(fii_d):.2f}% in {period}. FII selling can pressure the stock price in the near term.")
            elif pro_d is not None and pro_d > 0.5:
                insights.append(f"Insider vote of confidence — promoters bought an additional {pro_d:.2f}% of their own company in {period}. Insiders rarely buy unless they see undervaluation.")

    # 5 — Valuation clarity (plain-language P/E explanation)
    val_label  = fundamentals.get("valuation_label", "")
    pe         = fundamentals.get("pe_ratio")
    roe        = fundamentals.get("roe_pct")
    yoy_profit = fundamentals.get("yoy_profit_pct")
    if val_label == "CHEAP_QUALITY" and pe is not None:
        roe_str = f" while generating {roe:.0f}% return on shareholders' equity" if roe else ""
        insights.append(f"Attractively valued — P/E of {pe:.1f}x{roe_str}. In simple terms: for every Rs {pe:.0f} invested, you own Rs 1 of annual profit. Below-average valuation for this quality.")
    elif val_label == "EXPENSIVE" and pe is not None:
        insights.append(f"Premium-priced — P/E of {pe:.1f}x means you are paying Rs {pe:.0f} for every Rs 1 of annual earnings. This is justified only if earnings grow fast. Tread carefully on entry price.")
    elif yoy_profit is not None and yoy_profit > 20:
        insights.append(f"Earnings accelerating — net profit up {yoy_profit:.0f}% year-on-year. A rapidly growing profit base is one of the strongest drivers of long-term stock price appreciation.")
    elif yoy_profit is not None and yoy_profit < -20:
        insights.append(f"Earnings under pressure — net profit fell {abs(yoy_profit):.0f}% year-on-year. Until profits recover, the stock may remain subdued regardless of other signals.")

    # 6 — Derivatives market intelligence (plain English for laymen)
    oi_signal = fno.get("oi_signal", "")
    if oi_signal == "LONG_BUILDUP":
        insights.append("Futures market signal: institutional traders are adding fresh buy bets ('Long Buildup'). When smart money takes new positions in derivatives, it often precedes a price move up.")
    elif oi_signal == "SHORT_COVERING":
        insights.append("Reversal signal: traders who bet against this stock are now buying back to exit ('Short Covering'). This forced buying can create a sharp upward price move.")
    elif oi_signal == "SHORT_BUILDUP":
        insights.append("Caution: institutional traders are adding fresh sell bets ('Short Buildup') in futures. This signals that sophisticated market participants expect price weakness ahead.")

    return insights[:5]


router = APIRouter(prefix="/api/stocks", tags=["stocks"])


def _enrich_bulk(df: pd.DataFrame) -> pd.DataFrame:
    """Merge technical / F&O / ML / conviction columns into a bulk stock dataframe."""
    tech_df = data_loader.get("technical")
    if tech_df is not None:
        cols = [c for c in ["symbol", "trend_signal", "vs_dma_200", "prox_52w_high"] if c in tech_df.columns]
        df = df.merge(tech_df[cols], on="symbol", how="left")

    fno_df = data_loader.get("fno_intel")
    if fno_df is not None and "symbol" in fno_df.columns and "oi_signal" in fno_df.columns:
        df = df.merge(fno_df[["symbol", "oi_signal"]], on="symbol", how="left")

    ml_df = data_loader.get("ml_scores")
    if ml_df is not None:
        ml_cols = [c for c in ["symbol", "ml_bull_run_score", "accumulation_score"] if c in ml_df.columns]
        df = df.merge(ml_df[ml_cols], on="symbol", how="left")

    conv_df = data_loader.get("trade_conviction")
    if conv_df is not None and "symbol" in conv_df.columns:
        conv_cols = ["symbol"]
        if "score" in conv_df.columns:
            conv_cols.append("score")
        if "action" in conv_df.columns:
            conv_cols.append("action")
        merged = df.merge(conv_df[conv_cols], on="symbol", how="left")
        if "score" in conv_df.columns:
            merged = merged.rename(columns={"score": "conviction_score"})
        df = merged

    return df


@router.get("/watchlist")
def get_watchlist(label: str = "EMERGING", limit: int = 50):
    # EMERGING label: use pre-filtered watchlist CSV (faster); other labels: full bull_run dataset
    if label == "EMERGING":
        df = data_loader.get("bull_run_watchlist")
        if df is None or df.empty:
            raise HTTPException(status_code=503, detail="bull_run_watchlist not loaded")
        filtered = df if label == "ALL" else df[df["label"] == label]
    else:
        df = data_loader.get("bull_run")
        if df is None or df.empty:
            raise HTTPException(status_code=503, detail="bull_run_probability not loaded")
        filtered = df if label == "ALL" else df[df["label"] == label]

    filtered = filtered.nlargest(limit, "bull_run_score")
    filtered = _enrich_bulk(filtered)
    return {
        "label": label,
        "count": len(filtered),
        "stocks": _clean(filtered.to_dict(orient="records")),
    }


@router.get("")
def get_all_stocks(
    label: str = Query(None, description="Filter by label (STRONG_CANDIDATE, EMERGING, etc.)"),
    sector: str = Query(None),
    page: int = 1,
    per_page: int = 100,
):
    df = data_loader.get("bull_run")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="bull_run_probability not loaded")

    if label:
        df = df[df["label"] == label]
    if sector:
        df = df[df["sector"].str.upper() == sector.upper()]

    df = df.sort_values("bull_run_score", ascending=False)
    total = len(df)
    start = (page - 1) * per_page
    page_df = _enrich_bulk(df.iloc[start: start + per_page].copy())

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "stocks": _clean(page_df.to_dict(orient="records")),
    }


@router.get("/{symbol}")
def get_stock_detail(symbol: str):
    bull_df = data_loader.get("bull_run")
    if bull_df is None or bull_df.empty:
        raise HTTPException(status_code=503, detail="bull_run_probability not loaded")

    sym = symbol.upper()
    matched = bull_df[bull_df["symbol"].str.upper() == sym]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{sym}' not found")

    row = matched.iloc[0]

    # Deal signals
    deal_df = data_loader.get("deal_signals")
    deal_info = {}
    if deal_df is not None:
        deal_row = deal_df[deal_df["symbol"].str.upper() == sym]
        if not deal_row.empty:
            deal_info = deal_row.iloc[0].to_dict()

    # Corporate confidence
    corp_df = data_loader.get("corporate_confidence")
    corp_info = {}
    if corp_df is not None:
        corp_row = corp_df[corp_df["symbol"].str.upper() == sym]
        if not corp_row.empty:
            corp_info = corp_row.iloc[0].to_dict()

    # Phase 15B — Valuation
    fundamentals: dict = {}
    val_df = data_loader.get("valuation_scores")
    if val_df is not None:
        val_row = val_df[val_df["symbol"].str.upper() == sym]
        if not val_row.empty:
            r = val_row.iloc[0]
            fundamentals = {
                "pe_ratio":         _safe(r.get("pe_ratio")),
                "roe_pct":          _safe(r.get("roe_pct")),
                "valuation_score":  _safe(r.get("valuation_score")),
                "valuation_label":  str(r.get("valuation_label", "")),
                "revenue_ttm_cr":   _safe(r.get("revenue_ttm_cr")),
                "profit_ttm_cr":    _safe(r.get("profit_ttm_cr")),
                "yoy_revenue_pct":  _safe(r.get("yoy_revenue_pct")),
                "yoy_profit_pct":   _safe(r.get("yoy_profit_pct")),
                "as_of_date":       str(r.get("as_of_date", "")),
            }

    # Phase 15C — Shareholding (latest quarter per symbol)
    shareholding: dict = {}
    shp_df = data_loader.get("shareholding")
    if shp_df is not None:
        shp_rows = shp_df[shp_df["symbol"].str.upper() == sym]
        if not shp_rows.empty:
            shp_rows = shp_rows.sort_values("quarter_end_date")
            r = shp_rows.iloc[-1]
            shareholding = {
                "promoter_pct":     _safe(r.get("promoter_pct")),
                "fii_pct":          _safe(r.get("fii_pct")),
                "dii_pct":          _safe(r.get("dii_pct")),
                "public_pct":       _safe(r.get("public_pct")),
                "quarter_end_date": str(r.get("quarter_end_date", "")),
                "window_label":     str(r.get("window_label", "")),
            }

    # Phase 16 — Holding Trends (all quarters, sorted oldest first)
    holding_trends: list = []
    ht_df = data_loader.get("holding_trends")
    if ht_df is not None:
        ht_rows = ht_df[ht_df["symbol"].str.upper() == sym].copy()
        if not ht_rows.empty:
            ht_rows["_sort"] = pd.to_datetime(ht_rows["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
            ht_rows = ht_rows.sort_values("_sort").drop(columns=["_sort"])
            for _, r in ht_rows.iterrows():
                holding_trends.append({
                    "period":           str(r.get("period", "")),
                    "quarter_end_date": str(r.get("quarter_end_date", "")),
                    "promoter_pct":     _safe(r.get("promoter_pct")),
                    "fii_pct":          _safe(r.get("fii_pct")),
                    "dii_pct":          _safe(r.get("dii_pct")),
                    "public_pct":       _safe(r.get("public_pct")),
                    "promoter_delta":   _safe(r.get("promoter_delta")),
                    "fii_delta":        _safe(r.get("fii_delta")),
                    "dii_delta":        _safe(r.get("dii_delta")),
                    "conviction_signal": str(r.get("conviction_signal", "")),
                })

    # Phase 16 — Management Sentiment
    management: dict = {}
    ms_df = data_loader.get("management_sentiment")
    if ms_df is not None:
        ms_row = ms_df[ms_df["symbol"].str.upper() == sym]
        if not ms_row.empty:
            r = ms_row.iloc[0]
            management = {
                "holding_signal":      str(r.get("holding_signal", "")),
                "holding_score":       _safe(r.get("holding_score")),
                "announcement_score":  _safe(r.get("announcement_score")),
                "ai_tone_score":       _safe(r.get("ai_tone_score")),
                "management_score":    _safe(r.get("management_score")),
                "management_label":    str(r.get("management_label", "")),
                "announcement_types":  str(r.get("announcement_types", "")),
                "as_of_date":          str(r.get("as_of_date", "")),
            }

    # ML scores
    ml_scores: dict = {}
    ml_df = data_loader.get("ml_scores")
    if ml_df is not None:
        ml_row = ml_df[ml_df["symbol"].str.upper() == sym]
        if not ml_row.empty:
            r = ml_row.iloc[0]
            ml_scores = {
                "accumulation_score": _safe(r.get("accumulation_score")),
                "ml_bull_run_score":  _safe(r.get("ml_bull_run_score")),
            }

    # Technical indicators
    technical: dict = {}
    tech_df = data_loader.get("technical")
    if tech_df is not None:
        tech_row = tech_df[tech_df["symbol"].str.upper() == sym]
        if not tech_row.empty:
            r = tech_row.iloc[0]
            technical = {
                "close_now":      _safe(r.get("close_now")),
                "high_52w":       _safe(r.get("high_52w")),
                "low_52w":        _safe(r.get("low_52w")),
                "prox_52w_high":  _safe(r.get("prox_52w_high")),
                "prox_52w_low":   _safe(r.get("prox_52w_low")),
                "dma_20":         _safe(r.get("dma_20")),
                "dma_50":         _safe(r.get("dma_50")),
                "dma_200":        _safe(r.get("dma_200")),
                "vs_dma_20":      _safe(r.get("vs_dma_20")),
                "vs_dma_50":      _safe(r.get("vs_dma_50")),
                "vs_dma_200":     _safe(r.get("vs_dma_200")),
                "trend_signal":   str(r.get("trend_signal", "")),
                "vol_20d_avg":    _safe(r.get("vol_20d_avg")),
                "as_of_date":     str(r.get("as_of_date", "")),
            }

    # F&O intelligence
    fno: dict = {}
    fno_df = data_loader.get("fno_intel")
    if fno_df is not None:
        fno_row = fno_df[fno_df["symbol"].str.upper() == sym]
        if not fno_row.empty:
            r = fno_row.iloc[0]
            fno = {
                "futures_oi":  _safe(r.get("futures_oi")),
                "oi_1d":       _safe(r.get("oi_1d")),
                "oi_5d":       _safe(r.get("oi_5d")),
                "oi_signal":   str(r.get("oi_signal", "")),
                "fut_close":   _safe(r.get("fut_close")),
                "expiry":      str(r.get("expiry", "")),
                "as_of_date":  str(r.get("as_of_date", "")),
            }

    # Quarterly results (last 4 quarters)
    quarterly_results: list = []
    qr_df = data_loader.get("quarterly_results")
    if qr_df is not None and "symbol" in qr_df.columns:
        qr_rows = qr_df[qr_df["symbol"].str.upper() == sym].copy()
        if not qr_rows.empty:
            date_col = next((c for c in ["period_end_date", "period", "quarter_end_date", "date"] if c in qr_rows.columns), None)
            if date_col:
                qr_rows["_sort"] = pd.to_datetime(qr_rows[date_col], errors="coerce")
                qr_rows = qr_rows.sort_values("_sort", ascending=False).head(4).drop(columns=["_sort"])
            for _, r in qr_rows.iterrows():
                quarterly_results.append({
                    k: (_safe(v) if isinstance(v, float) else str(v) if not isinstance(v, (int, type(None))) else v)
                    for k, v in r.items()
                    if k in ["period", "period_end_date", "quarter_end_date", "revenue", "revenue_cr",
                              "net_profit", "net_profit_cr", "eps", "total_income", "total_expenses",
                              "yoy_revenue_pct", "yoy_profit_pct", "qoq_revenue_pct", "qoq_profit_pct"]
                })

    # Sector rotation signal for this stock's sector
    sector_rotation_signal = ""
    rot_df = data_loader.get("sector_rotation")
    if rot_df is not None and "sector" in rot_df.columns:
        sym_sector = str(row.get("sector", "")).upper()
        rot_row = rot_df[rot_df["sector"].str.upper() == sym_sector]
        if not rot_row.empty:
            sector_rotation_signal = str(rot_row.iloc[0].get("rotation_signal", ""))

    # Next catalyst
    catalyst: dict = {}
    cat_df = data_loader.get("upcoming_catalysts")
    if cat_df is not None:
        cat_row = cat_df[cat_df["symbol"].str.upper() == sym] if "symbol" in cat_df.columns else pd.DataFrame()
        if not cat_row.empty:
            r = cat_row.iloc[0]
            catalyst = {
                "event_date":    str(r.get("event_date", "")),
                "purpose_type":  str(r.get("purpose_type", "")),
                "catalyst_score": _safe(r.get("catalyst_score")),
            }

    # Phase F — News sentiment (7-day rolling)
    news_signal: dict = {}
    news_df = data_loader.get("news_signals")
    if news_df is not None and "symbol" in news_df.columns:
        news_row = news_df[news_df["symbol"].str.upper() == sym]
        if not news_row.empty:
            r = news_row.iloc[0]
            news_signal = {
                "news_count_7d":   _safe(r.get("news_count_7d")),
                "sentiment_7d":    _safe(r.get("sentiment_7d")),
                "sentiment_label": str(r.get("sentiment_label", "")),
                "bullish_count":   _safe(r.get("bullish_count")),
                "bearish_count":   _safe(r.get("bearish_count")),
                "top_theme":       str(r.get("top_theme", "")),
                "latest_headline": str(r.get("latest_headline", "")),
                "latest_date":     str(r.get("latest_date", "")),
            }

    # Phase F — Insider trade signals (30-day)
    insider_signal: dict = {}
    ins_df = data_loader.get("insider_signals")
    if ins_df is not None and "symbol" in ins_df.columns:
        ins_row = ins_df[ins_df["symbol"].str.upper() == sym]
        if not ins_row.empty:
            r = ins_row.iloc[0]
            insider_signal = {
                "buy_value_30d_cr":   _safe(r.get("buy_value_30d_cr")),
                "sell_value_30d_cr":  _safe(r.get("sell_value_30d_cr")),
                "net_value_30d_cr":   _safe(r.get("net_value_30d_cr")),
                "buy_count_30d":      _safe(r.get("buy_count_30d")),
                "sell_count_30d":     _safe(r.get("sell_count_30d")),
                "insider_conviction": str(r.get("insider_conviction", "")),
                "insider_score":      _safe(r.get("insider_score")),
                "acquirers":          str(r.get("acquirers", "")),
                "latest_date":        str(r.get("latest_date", "")),
            }

    # Phase G — Multi-signal consensus
    consensus: dict = {}
    con_df = data_loader.get("consensus_scores")
    if con_df is not None and "symbol" in con_df.columns:
        con_row = con_df[con_df["symbol"].str.upper() == sym]
        if not con_row.empty:
            r = con_row.iloc[0]
            consensus = {
                "consensus_score":   _safe(r.get("consensus_score")),
                "consensus_label":   str(r.get("consensus_label", "")),
                "signals_used":      str(r.get("signals_used", "")),
                "concall_norm":      _safe(r.get("concall_norm")),
                "insider_norm":      _safe(r.get("insider_norm")),
                "news_norm":         _safe(r.get("news_norm")),
                "deal_norm":         _safe(r.get("deal_norm")),
                "as_of_date":        str(r.get("as_of_date", "")),
            }

    # Phase F — Concall / earnings call signals
    concall_signal: dict = {}
    cc_df = data_loader.get("concall_summary")
    if cc_df is not None and "symbol" in cc_df.columns:
        cc_row = cc_df[cc_df["symbol"].str.upper() == sym]
        if not cc_row.empty:
            r = cc_row.iloc[0]
            concall_signal = {
                "date":               str(r.get("date", "")),
                "sentiment":          str(r.get("sentiment", "")),
                "sentiment_score":    _safe(r.get("sentiment_score")),
                "guidance_direction": str(r.get("guidance_direction", "")),
                "guidance_score":     _safe(r.get("guidance_score")),
                "capex_signal":       str(r.get("capex_signal", "")),
                "capex_amount_cr":    _safe(r.get("capex_amount_cr")),
                "themes":             str(r.get("themes", "")),
                "key_statement":      str(r.get("key_statement", "")),
                "concall_score":      _safe(r.get("concall_score")),
            }

    # Phase H — AGM / governance signals
    agm_signal: dict = {}
    agm_df = data_loader.get("agm_signals")
    if agm_df is not None and "symbol" in agm_df.columns:
        agm_row = agm_df[agm_df["symbol"].str.upper() == sym]
        if not agm_row.empty:
            r = agm_row.iloc[0]
            agm_signal = {
                "date":              str(r.get("date", "")),
                "announcement_type": str(r.get("announcement_type", "")),
                "governance_risk":   str(r.get("governance_risk", "")),
                "governance_score":  _safe(r.get("governance_score")),
                "dividend_signal":   str(r.get("dividend_signal", "")),
                "capex_confirm":     str(r.get("capex_confirm", "")),
                "management_change": str(r.get("management_change", "")),
                "sentiment":         str(r.get("sentiment", "")),
                "sentiment_score":   _safe(r.get("sentiment_score")),
                "key_decision":      str(r.get("key_decision", "")),
            }

    return {
        "symbol":             str(row.get("symbol", "")),
        "sector":             str(row.get("sector", "")),
        "close_now":          _safe(row.get("close_now")),
        "bull_run_score":     round(float(row.get("bull_run_score", 0) or 0), 2),
        "label":              str(row.get("label", "")),
        "market_regime":      str(row.get("market_regime", "")),
        "regime_multiplier":  float(row.get("regime_multiplier", 1.0) or 1.0),
        "components": {
            "price_score":        round(float(row.get("price_score",        0) or 0), 2),
            "sector_flow_score":  round(float(row.get("sector_flow_score",  0) or 0), 2),
            "deal_score":         round(float(row.get("deal_score",         0) or 0), 2),
            "corporate_score":    round(float(row.get("corporate_score",    0) or 0), 2),
        },
        "price": {
            "ret_30d":   _safe(row.get("ret_30d")),
            "ret_90d":   _safe(row.get("ret_90d")),
            "ret_365d":  _safe(row.get("ret_365d")),
            "vol_ratio": _safe(row.get("vol_ratio")),
        },
        "as_of_date":           str(row.get("as_of_date", "")),
        "deal_signals":         deal_info,
        "corporate_confidence": corp_info,
        "fundamentals":         fundamentals,
        "shareholding":         shareholding,
        "holding_trends":       holding_trends,
        "management":           management,
        "ml_scores":               ml_scores,
        "technical":               technical,
        "fno":                     fno,
        "catalyst":                catalyst,
        "sector_rotation_signal":  sector_rotation_signal,
        "quarterly_results":       quarterly_results,
        "analyst_insights":        _generate_insights(sym, row, fundamentals, technical, shareholding, holding_trends, fno),
        # Phase F alt-data
        "news":    news_signal,
        "insider": insider_signal,
        "concall": concall_signal,
        "agm":     agm_signal,
        # Phase G consensus
        "consensus": consensus,
    }


@router.get("/{symbol}/momentum")
def get_stock_momentum(symbol: str):
    df = data_loader.get("price_momentum")
    if df is None or df.empty:
        raise HTTPException(status_code=503, detail="price_momentum not loaded")

    sym = symbol.upper()
    matched = df[df["symbol"].str.upper() == sym]
    if matched.empty:
        raise HTTPException(status_code=404, detail=f"Symbol '{sym}' not found in momentum data")

    return matched.iloc[0].to_dict()
