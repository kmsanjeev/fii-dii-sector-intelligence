"""
Theme Intelligence Engine — Phase D
Aggregates stock-level intelligence into 15 macro themes, scoring each by
money flow (FII/DII), price momentum, and institutional conviction signals.

Run:
    py -3.11 engines/intelligence/theme_intelligence_engine.py

Output:
    data/intelligence/theme_intelligence.csv
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Theme metadata ─────────────────────────────────────────────────────────────

THEME_META = {
    "CAPEX_CYCLE": {
        "display_name": "Capital Expenditure Boom",
        "description": (
            "India's corporate and government capex supercycle — new factories, power plants, "
            "and industrial capacity being built at unprecedented scale."
        ),
        "macro_driver": "Government infra spend + PLI schemes + rising corporate profits",
        "risk": "Interest rate sensitivity, commodity cost inflation",
        "global_peer": "US Industrials, South Korea Steel cycle",
    },
    "CHINA_PLUS_ONE": {
        "display_name": "China+1 Manufacturing Shift",
        "description": (
            "Global companies diversifying supply chains out of China into India — "
            "chemicals, electronics, and textiles lead this structural decade-long shift."
        ),
        "macro_driver": "Geopolitical realignment, PLI incentives, competitive labour costs",
        "risk": "Execution risk, infrastructure gaps, China export dumping",
        "global_peer": "Vietnam textiles, Taiwan semiconductors shift",
    },
    "FINANCIALISATION": {
        "display_name": "Financialisation of Savings",
        "description": (
            "Indians shifting savings from gold and real estate into stocks and MFs — "
            "financial companies see structural demand growth."
        ),
        "macro_driver": "Rising incomes, SIP culture, SEBI reforms, UPI credit ecosystem",
        "risk": "Market correction dampens SIP inflows, credit cycle stress",
        "global_peer": "US wealth management boom (2010-2020)",
    },
    "RURAL_CONSUMPTION": {
        "display_name": "Rural India Consumption",
        "description": (
            "Rising rural incomes from better agri prices and government schemes "
            "driving demand for FMCG, two-wheelers, and agri inputs."
        ),
        "macro_driver": "Good monsoon, MSP hikes, MNREGA spend, rural credit growth",
        "risk": "Drought, inflation eroding real incomes",
        "global_peer": "Indonesia rural consumer cycle",
    },
    "DIGITAL_INDIA": {
        "display_name": "Digital India & Technology",
        "description": (
            "India's digital transformation — cloud adoption, fintech, digital payments, "
            "and IT services exports driving the next growth wave."
        ),
        "macro_driver": "UPI ecosystem, India Stack, AI adoption, US tech spend recovery",
        "risk": "INR appreciation, wage inflation, global tech slowdown",
        "global_peer": "Global AI infrastructure build (Nvidia, TSMC cycle)",
    },
    "HEALTHCARE_EXPANSION": {
        "display_name": "Healthcare & Pharma Growth",
        "description": (
            "Healthcare spending rising as incomes grow — hospitals, pharma R&D, "
            "diagnostics, and health insurance all in structural upcycle."
        ),
        "macro_driver": "Post-COVID health awareness, ageing population, insurance penetration",
        "risk": "US FDA import alerts, pricing pressure on generics",
        "global_peer": "US Medicare expansion cycle",
    },
    "PREMIUMISATION": {
        "display_name": "Premium Consumption Upgrade",
        "description": (
            "India's upper-middle class trading up — premium food, experiences, travel, "
            "and consumer goods seeing strong demand as aspirations rise."
        ),
        "macro_driver": "Rising urban incomes, aspirational class growth, credit availability",
        "risk": "Slowdown in discretionary spending during rate hike cycles",
        "global_peer": "China's premiumisation wave (2010-2015)",
    },
    "EV_TRANSITION": {
        "display_name": "Electric Vehicle Revolution",
        "description": (
            "India's shift to electric mobility — EV makers, battery suppliers, "
            "charging infrastructure, and ancillaries all in early play."
        ),
        "macro_driver": "FAME subsidies, falling battery costs, fuel cost savings",
        "risk": "Technology disruption risk, raw material shortage (lithium)",
        "global_peer": "Tesla/BYD supply chain expansion",
    },
    "INFRASTRUCTURE_BUILD": {
        "display_name": "Infrastructure Buildout",
        "description": (
            "Government's Rs 10 lakh crore annual infra push — roads, metro, ports, "
            "and urban infra creating a 7-10 year capex supercycle."
        ),
        "macro_driver": "National Infrastructure Pipeline (NIP), PPP revival, smart cities",
        "risk": "Land acquisition delays, liquidity stress in EPC companies",
        "global_peer": "US Infrastructure Act (2021), EU Green Deal",
    },
    "REAL_ESTATE_RECOVERY": {
        "display_name": "Real Estate Recovery",
        "description": (
            "After a decade of stagnation, real estate is recovering — rising property "
            "prices, luxury housing boom, and office space demand returning."
        ),
        "macro_driver": "Inventory correction, WFH reversal, NRI buying, low unsold stock",
        "risk": "Rate hike affordability pressure, new supply influx",
        "global_peer": "Japan real estate recovery (2012-2019)",
    },
    "GREEN_ENERGY": {
        "display_name": "Green & Renewable Energy",
        "description": (
            "India targeting 500GW renewable capacity by 2030 — solar, wind, "
            "green hydrogen, and energy storage companies are direct beneficiaries."
        ),
        "macro_driver": "Global climate commitments, falling solar costs, energy security",
        "risk": "Land acquisition, grid curtailment, financing costs",
        "global_peer": "Global clean energy transition (IRA, European Green Deal)",
    },
    "LOGISTICS_MODERNISATION": {
        "display_name": "Logistics Modernisation",
        "description": (
            "India's logistics costs (14% of GDP vs 8% globally) being tackled — "
            "warehousing, cold chain, and express delivery modernisation underway."
        ),
        "macro_driver": "GST e-waybill, PM Gati Shakti, Dedicated Freight Corridors",
        "risk": "Fragmented market, thin margins, fuel cost volatility",
        "global_peer": "Amazon logistics disruption, FedEx Asia expansion",
    },
    "DEFENCE_ELECTRONICS": {
        "display_name": "Defence & Aerospace",
        "description": (
            "India's indigenisation drive in defence — domestic manufacturers replacing "
            "imports in aerospace, missiles, naval systems, and electronics."
        ),
        "macro_driver": "Positive indigenisation lists, defence exports target, border tensions",
        "risk": "Long order-to-revenue cycles, technology transfer complexity",
        "global_peer": "US defence budget expansion, NATO spending surge",
    },
    "EXPORT_GROWTH": {
        "display_name": "Export & Global Trade",
        "description": (
            "India gaining share in global exports — specialty chemicals, pharma APIs, "
            "textiles, and IT services are leading export vectors."
        ),
        "macro_driver": "Weak INR, global supply chain shifts, FTA negotiations",
        "risk": "Global demand slowdown, anti-dumping duties, INR strengthening",
        "global_peer": "Emerging market export cycles",
    },
    "PSU_REVIVAL": {
        "display_name": "Public Sector Revival",
        "description": (
            "Government-owned companies being re-rated as governance improves — "
            "PSU banks, oil companies, and utilities recapturing investor attention."
        ),
        "macro_driver": "Government recapitalisation, dividend mandates, disinvestment re-think",
        "risk": "Government interference in business decisions, populist spending",
        "global_peer": "China SOE reform cycle",
    },
}


def _safe(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _normalize(series: pd.Series, lo: float, hi: float) -> pd.Series:
    """Min-max normalize to 0-1 range using soft clipping."""
    clipped = series.clip(lo, hi)
    return (clipped - lo) / (hi - lo)


def run():
    logger.info("[ThemeEngine] Starting theme intelligence engine")

    # ── Load data ──────────────────────────────────────────────────────────────
    clf_path  = cfg.REFERENCE_DIR / "company_classification_v4.csv"
    bull_path = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
    pm_path   = cfg.INTELLIGENCE_DIR / "price_momentum.csv"
    sr_path   = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
    ml_path   = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"

    for p in [clf_path, bull_path, pm_path, sr_path]:
        if not p.exists():
            logger.error(f"[ThemeEngine] Missing required file: {p}")
            return

    clf  = pd.read_csv(clf_path)
    bull = pd.read_csv(bull_path)
    pm   = pd.read_csv(pm_path)
    sr   = pd.read_csv(sr_path)
    ml   = pd.read_csv(ml_path) if ml_path.exists() else None

    # Normalize column names
    clf.columns = [c.upper() for c in clf.columns]
    bull["symbol"] = bull["symbol"].str.upper()
    pm["symbol"]   = pm["symbol"].str.upper()

    # Merge stock-level data
    stock_df = bull.merge(pm[["symbol", "ret_30d", "ret_60d", "ret_90d", "ret_365d", "vol_ratio"]], on="symbol", how="left", suffixes=("", "_pm"))
    if ml is not None:
        ml["symbol"] = ml["symbol"].str.upper()
        stock_df = stock_df.merge(ml[["symbol", "ml_bull_run_score", "accumulation_score"]], on="symbol", how="left")

    # Sector rotation signals (latest snapshot per sector)
    sr_latest = sr.copy()
    sr_latest["sector"] = sr_latest["sector"].str.upper()

    results = []

    for theme_code, meta in THEME_META.items():
        # Get stocks in this theme
        theme_stocks = clf[clf["THEME"] == theme_code]["SYMBOL"].dropna().str.upper().tolist()
        if not theme_stocks:
            logger.warning(f"[ThemeEngine] No stocks found for theme: {theme_code}")
            continue

        # Filter to stocks with intelligence data
        ts_df = stock_df[stock_df["symbol"].isin(theme_stocks)].copy()
        if ts_df.empty:
            continue

        stock_count    = len(ts_df)
        scored_count   = ts_df["bull_run_score"].notna().sum()

        # ── Price & score aggregates ───────────────────────────────────────────
        avg_bull       = ts_df["bull_run_score"].mean()
        avg_ret_30d    = ts_df["ret_30d"].mean() if "ret_30d" in ts_df.columns else None
        avg_ret_60d    = ts_df["ret_60d"].mean() if "ret_60d" in ts_df.columns else None
        avg_ret_90d    = ts_df["ret_90d"].mean() if "ret_90d" in ts_df.columns else None
        avg_ret_365d   = ts_df["ret_365d"].mean() if "ret_365d" in ts_df.columns else None
        avg_vol_ratio  = ts_df["vol_ratio"].mean() if "vol_ratio" in ts_df.columns else None
        avg_ml_score   = ts_df["ml_bull_run_score"].mean() if "ml_bull_run_score" in ts_df.columns else None
        avg_accum      = ts_df["accumulation_score"].mean() if "accumulation_score" in ts_df.columns else None

        # Label distribution
        label_counts = ts_df["label"].value_counts().to_dict() if "label" in ts_df.columns else {}
        strong_count  = label_counts.get("STRONG_CANDIDATE", 0)
        emerging_count = label_counts.get("EMERGING", 0)

        # ── Sector flow signals ────────────────────────────────────────────────
        theme_sectors_all = clf[clf["THEME"] == theme_code]["SECTOR"].dropna().str.upper().unique().tolist()
        sector_rows = sr_latest[sr_latest["sector"].isin(theme_sectors_all)]

        fii_flow   = sector_rows["FII_flow_score"].mean()   if not sector_rows.empty else None
        dii_flow   = sector_rows["DII_flow_score"].mean()   if not sector_rows.empty else None
        smart_money = sector_rows["Smart_Money_Score"].mean() if not sector_rows.empty else None
        price_mom_sector = sector_rows["price_momentum_score"].mean() if not sector_rows.empty else None

        # ── Theme score (composite 0-100) ──────────────────────────────────────
        # Component 1: stock intelligence (bull run scores) — 35%
        c1 = _normalize(pd.Series([avg_bull or 0]), 20, 60).iloc[0]

        # Component 2: smart money alignment — 30%
        sm = smart_money if smart_money is not None else 0
        c2 = _normalize(pd.Series([sm]), -50, 30).iloc[0]

        # Component 3: 1-year price momentum — 20%
        ret1y = avg_ret_365d if avg_ret_365d is not None else 0
        c3 = _normalize(pd.Series([ret1y]), -30, 60).iloc[0]

        # Component 4: 30-day recent momentum — 15%
        ret30 = avg_ret_30d if avg_ret_30d is not None else 0
        c4 = _normalize(pd.Series([ret30]), -10, 15).iloc[0]

        theme_score = round((0.35 * c1 + 0.30 * c2 + 0.20 * c3 + 0.15 * c4) * 100, 2)

        # ── Momentum phase detection ───────────────────────────────────────────
        # Based on: is recent momentum ACCELERATING (30D > 90D/3) or DECELERATING?
        # This detects early rotation vs late-stage themes
        r30 = avg_ret_30d or 0
        r90 = avg_ret_90d or 0
        r1y = avg_ret_365d or 0

        if r30 > 5 and r30 > (r90 / 3 + 1):
            momentum_phase = "ACCELERATING"
        elif r30 > 2 and r1y > 15:
            momentum_phase = "MOMENTUM"
        elif r30 > 0 and r1y < 5:
            momentum_phase = "EARLY_ROTATION"
        elif r30 < -2 and r1y > 10:
            momentum_phase = "DECELERATING"
        elif r1y < -10:
            momentum_phase = "DORMANT"
        else:
            momentum_phase = "CONSOLIDATING"

        # ── Theme signal (money trail based) ──────────────────────────────────
        sm_score = smart_money or 0
        if sm_score > 10 and r30 > 3:
            theme_signal = "HEATING_UP"
        elif sm_score > 0 and r1y > 15:
            theme_signal = "MOMENTUM"
        elif sm_score > 0 and r30 > 0:
            theme_signal = "BUILDING"
        elif sm_score < -20 and r30 > 3:
            theme_signal = "PRICE_LED"         # price up but smart money not participating
        elif sm_score < -15 and r30 < -2:
            theme_signal = "DISTRIBUTION"
        else:
            theme_signal = "NEUTRAL"

        # ── Participant leader (who drives this theme) ─────────────────────────
        fii_v = fii_flow or 0
        dii_v = dii_flow or 0
        if fii_v > 0 and fii_v > dii_v:
            participant_leader = "FII"
        elif dii_v > 0 and dii_v >= fii_v:
            participant_leader = "DII"
        elif sm_score > 0:
            participant_leader = "SMART_MONEY"
        else:
            participant_leader = "RETAIL"

        # ── Top picks ─────────────────────────────────────────────────────────
        top_picks_df = ts_df.nlargest(5, "bull_run_score")[["symbol", "bull_run_score", "label"]].copy()
        top_picks = top_picks_df.to_dict(orient="records")

        # ── Constituent sectors ────────────────────────────────────────────────
        sectors_str = ",".join(sorted(set(theme_sectors_all)))

        results.append({
            "theme":             theme_code,
            "display_name":      meta["display_name"],
            "description":       meta["description"],
            "macro_driver":      meta["macro_driver"],
            "risk_factor":       meta["risk"],
            "global_peer":       meta["global_peer"],
            "sectors":           sectors_str,
            "stock_count":       stock_count,
            "scored_count":      int(scored_count),
            "strong_count":      int(strong_count),
            "emerging_count":    int(emerging_count),
            "theme_score":       _safe(theme_score),
            "theme_signal":      theme_signal,
            "momentum_phase":    momentum_phase,
            "participant_leader": participant_leader,
            "avg_bull_score":    round(float(avg_bull), 2) if avg_bull is not None else None,
            "avg_ret_30d":       round(float(avg_ret_30d), 2) if avg_ret_30d is not None else None,
            "avg_ret_60d":       round(float(avg_ret_60d), 2) if avg_ret_60d is not None else None,
            "avg_ret_90d":       round(float(avg_ret_90d), 2) if avg_ret_90d is not None else None,
            "avg_ret_365d":      round(float(avg_ret_365d), 2) if avg_ret_365d is not None else None,
            "avg_vol_ratio":     round(float(avg_vol_ratio), 2) if avg_vol_ratio is not None else None,
            "avg_ml_score":      round(float(avg_ml_score), 2) if avg_ml_score is not None else None,
            "avg_accum_score":   round(float(avg_accum), 2) if avg_accum is not None else None,
            "fii_flow_score":    round(float(fii_flow), 2) if fii_flow is not None else None,
            "dii_flow_score":    round(float(dii_flow), 2) if dii_flow is not None else None,
            "smart_money_score": round(float(smart_money), 2) if smart_money is not None else None,
            "price_sector_momentum": round(float(price_mom_sector), 2) if price_mom_sector is not None else None,
            "top_picks":         json.dumps(top_picks),
            "as_of_date":        pd.Timestamp.now().strftime("%Y-%m-%d"),
        })

        logger.info(f"[ThemeEngine] {theme_code}: score={theme_score:.1f} signal={theme_signal} stocks={stock_count}")

    if not results:
        logger.error("[ThemeEngine] No theme results generated")
        return

    out_df = pd.DataFrame(results).sort_values("theme_score", ascending=False).reset_index(drop=True)
    out_path = cfg.INTELLIGENCE_DIR / "theme_intelligence.csv"
    out_df.to_csv(out_path, index=False)
    logger.info(f"[ThemeEngine] Wrote {len(out_df)} themes to {out_path}")
    return out_df


if __name__ == "__main__":
    run()
