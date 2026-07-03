"""
Feature Engineering Engine -- Phase 12A + Phase F extension
Builds the feature matrix from all intelligence + raw data layers.
Output: data/intelligence/ml_features/feature_matrix.parquet

Features per symbol (~50 total):
  Phase 8B scores:  bull_run_score, price_score, sector_flow_score, deal_score,
                    corporate_score, regime_multiplier
  Price:            ret_30d, ret_90d, ret_365d, vol_ratio, sector_rel_30d
  Sector snapshot:  sector_combined_score, rotation_signal_enc
  Sector rolling:   sec_FII_5d, sec_FII_20d, sec_FII_60d,
                    sec_DII_5d, sec_DII_20d, sec_DII_60d,
                    sec_smart_money, sec_retail_score
  Participant:      part_FII_flow, part_DII_flow, part_smart_money, regime_enc
  Fundamentals:     mkt_cap_enc, fund_promoter_pct, fund_fii_pct, fund_dii_pct
  Ownership (SHP):  shp_promoter_pct, shp_fii_pct, shp_dii_pct
  Index:            index_count
  Corporate acts:   div_count_12m, has_buyback_12m, has_bonus_12m
  Deals:            deal_net_cr, corp_confidence
  Phase F alt-data: theme_score_max, theme_purity_max,
                    news_sentiment_7d, insider_score,
                    concall_guidance_score, concall_sentiment_score
  Label:            label_enc (from Phase 8B rule-based scoring)

Note on labels:
  label_enc is derived from Phase 8B rule-based bull_run_probability.csv.
  This creates a circular dependency where ML replicates rules rather than
  predicting forward returns. True forward-return labels (is_up_10pct_in_20d)
  require accumulated daily scoring history (Phase 12B, 3-6 months of runs).

Look-ahead bias prevention:
  All features are point-in-time (as_of_date). No future data leaks in.
  TimeSeriesSplit CV only when training -- no random shuffle.
"""

import sys
import shutil
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import numpy as np

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR      = cfg.INTELLIGENCE_DIR / "ml_features"
OUTPUT_PATH = ML_DIR / "feature_matrix.parquet"
OUTPUT_CSV  = ML_DIR / "feature_matrix.csv"

BULL_RUN    = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
PRICE_MOM   = cfg.INTELLIGENCE_DIR / "price_momentum.csv"
SECTOR_ROT  = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
SECTOR_FLOW = cfg.INTELLIGENCE_DIR / "sector_flow_scores.csv"
PART_INTEL  = cfg.INTELLIGENCE_DIR / "participant_intelligence.csv"
DEAL_SIG    = cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv"
CORP_CONF   = cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv"
CORP_ACT    = cfg.INTELLIGENCE_DIR / "corporate_action_signals.csv"

FUND_MASTER  = cfg.NSE_DIR / "equity_master" / "company_fundamentals_master.csv"
INDEX_MEMB   = cfg.NSE_DIR / "indices" / "index_membership.csv"
SHP_CSV      = cfg.NSE_DIR / "shareholding" / "quarterly_shp.csv"
ANN_CSV      = cfg.INTELLIGENCE_DIR / "company_announcements.csv"

# Phase 12A — enriched fundamentals + technical + F&O sources
EXT_FIN      = cfg.NSE_DIR / "results" / "extended_financials.csv"
VAL_SCORES   = cfg.NSE_DIR / "results" / "valuation_scores.csv"
TECH_IND     = cfg.INTELLIGENCE_DIR / "technical_indicators.csv"
FNO_INTEL    = cfg.INTELLIGENCE_DIR / "fno_intelligence.csv"

# Phase F alt-data sources
THEME_TAG      = cfg.REFERENCE_DIR / "theme_tagging.csv"
THEME_INTEL    = cfg.INTELLIGENCE_DIR / "theme_intelligence.csv"
NEWS_SIGNALS   = cfg.INTELLIGENCE_DIR / "news_signals.csv"
INSIDER_SIGS   = cfg.INTELLIGENCE_DIR / "insider_signals.csv"
CONCALL_SUM    = cfg.INTELLIGENCE_DIR / "concall_summary.csv"
CONSENSUS      = cfg.INTELLIGENCE_DIR / "consensus_scores.csv"

# ---------------------------------------------------------------------------
# Encoding maps
# ---------------------------------------------------------------------------
LABEL_MAP = {
    "STRONG_CANDIDATE": 4,
    "EMERGING":         3,
    "WATCHLIST":        2,
    "NEUTRAL":          1,
    "AVOID":            0,
}
ROTATION_MAP = {
    "EARLY_ROTATION": 5,
    "LEADING":        4,
    "MOMENTUM":       3,
    "EMERGING":       2,
    "LAGGING":        1,
    "DECLINING":      0,
}
REGIME_MAP = {
    "STRONG_ACCUMULATION": 4,
    "ACCUMULATION":        3,
    "NEUTRAL":             2,
    "DISTRIBUTION":        1,
    "STRONG_DISTRIBUTION": 0,
}
MKTCAP_MAP = {
    "LARGE": 3,
    "MID":   2,
    "SMALL": 1,
    "MICRO": 0,
}
VALUATION_MAP = {
    "CHEAP_QUALITY": 3,
    "FAIR_VALUE":    2,
    "OVERVALUED":    1,
    "EXPENSIVE":     1,
    "LOSS":          0,
}
TREND_MAP = {
    "UPTREND":   2,
    "NEUTRAL":   1,
    "DOWNTREND": 0,
}
FNO_OI_MAP = {
    "BULLISH": 2,
    "NEUTRAL": 1,
    "BEARISH": 0,
}


class FeatureEngineeringEngine:
    """
    Assembles a point-in-time feature matrix from all available data layers.
    Joins intelligence outputs, fundamentals, ownership, index membership,
    and corporate action history onto the Phase 8B symbol universe.
    """

    def run(self) -> bool:
        logger.info("[FeatureEng] Starting feature engineering")
        ML_DIR.mkdir(parents=True, exist_ok=True)

        try:
            df = self._build_matrix()
            if df.empty:
                logger.error("[FeatureEng] Empty feature matrix -- aborting")
                return False

            self._validate(df)
            self._save(df)
            logger.info("[FeatureEng] Complete: %d symbols, %d features", len(df), len(df.columns))
            return True

        except Exception as e:
            logger.error("[FeatureEng] Failed: %s", e, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Master builder
    # ------------------------------------------------------------------
    def _build_matrix(self) -> pd.DataFrame:
        if not BULL_RUN.exists():
            raise FileNotFoundError(f"Required: {BULL_RUN}")

        bull = pd.read_csv(BULL_RUN)
        bull = bull.rename(columns={"market_regime": "regime_raw"})
        bull["symbol"] = bull["symbol"].str.strip().str.upper()

        bull = self._add_price_momentum(bull)
        bull = self._add_sector_snapshot(bull)
        bull = self._add_sector_rolling(bull)
        bull = self._add_participant(bull)
        bull = self._add_fundamentals(bull)
        bull = self._add_shareholding(bull)
        bull = self._add_index_membership(bull)
        bull = self._add_corporate_actions(bull)
        bull = self._add_corporate_confidence(bull)
        bull = self._add_deal_signals(bull)
        bull = self._add_announcement_features(bull)

        # Phase 12A — enriched fundamentals + technical + F&O features
        bull = self._add_extended_financials(bull)
        bull = self._add_valuation_features(bull)
        bull = self._add_technical_features(bull)
        bull = self._add_fno_features(bull)

        # Phase F alt-data features
        bull = self._add_theme_features(bull)
        bull = self._add_news_sentiment(bull)
        bull = self._add_insider_signals(bull)
        bull = self._add_concall_signals(bull)

        # Phase G consensus
        bull = self._add_consensus(bull)

        bull["label_enc"] = bull["label"].map(LABEL_MAP).fillna(1)

        feature_cols = [
            "symbol", "sector", "as_of_date",
            # Phase 8B component scores
            "bull_run_score", "label", "label_enc",
            "price_score", "sector_flow_score", "deal_score",
            "corporate_score", "regime_multiplier",
            # Price momentum
            "ret_30d", "ret_90d", "ret_365d", "vol_ratio", "sector_rel_30d",
            # Sector snapshot
            "sector_combined_score", "rotation_signal_enc",
            # Sector rolling (5D/20D/60D)
            "sec_FII_5d", "sec_FII_20d", "sec_FII_60d",
            "sec_DII_5d", "sec_DII_20d", "sec_DII_60d",
            "sec_smart_money", "sec_retail_score",
            # Participant (market-wide latest snapshot)
            "part_FII_flow", "part_DII_flow", "part_smart_money", "regime_enc",
            # Fundamentals master
            "mkt_cap_enc", "fund_promoter_pct", "fund_fii_pct", "fund_dii_pct",
            # Shareholding pattern (latest quarter)
            "shp_promoter_pct", "shp_fii_pct", "shp_dii_pct",
            # Index membership
            "index_count",
            # Corporate actions (12M)
            "div_count_12m", "has_buyback_12m", "has_bonus_12m",
            # Institutional signals
            "corp_confidence", "deal_net_cr",
            # Phase 18C — Announcement intelligence
            "ann_score_30d", "high_signal_30d", "distinct_types_30d",
            "ann_velocity_30d", "order_wins_6m", "spurt_count_30d", "distress_30d",
            # Phase F — Alt-data intelligence
            "theme_score_max", "theme_purity_max",
            "news_sentiment_7d", "insider_score",
            "concall_guidance_score", "concall_sentiment_score",
            # Phase G — Multi-signal consensus
            "consensus_score",
            # Phase 12A — enriched fundamentals
            "opm_pct", "roce_pct", "sales_growth_3y",
            # Phase 12A — valuation intelligence
            "pe_ratio_log", "roe_pct", "valuation_label_enc",
            "yoy_revenue_pct", "yoy_profit_pct",
            # Phase 12A — technical indicators
            "vs_dma_200", "trend_signal_enc",
            # Phase 12A — F&O open interest signal
            "fno_oi_signal_enc",
        ]
        available = [c for c in feature_cols if c in bull.columns]
        missing = [c for c in feature_cols if c not in bull.columns]
        if missing:
            logger.warning("[FeatureEng] Features not available (source missing): %s", missing)
        return bull[available].copy()

    # ------------------------------------------------------------------
    # Data source methods
    # ------------------------------------------------------------------
    def _add_price_momentum(self, df: pd.DataFrame) -> pd.DataFrame:
        if not PRICE_MOM.exists():
            logger.warning("[FeatureEng] price_momentum.csv missing -- skipping price features")
            return df
        cols_wanted = ["symbol", "ret_30d", "ret_90d", "ret_365d", "vol_ratio", "sector_rel_30d"]
        peek = pd.read_csv(PRICE_MOM, nrows=0).columns.tolist()
        usecols = [c for c in cols_wanted if c in peek]
        price = pd.read_csv(PRICE_MOM, usecols=usecols)
        price["symbol"] = price["symbol"].str.strip().str.upper()
        return df.merge(price, on="symbol", how="left", suffixes=("", "_pm"))

    def _add_sector_snapshot(self, df: pd.DataFrame) -> pd.DataFrame:
        if not SECTOR_ROT.exists():
            return df
        sec = pd.read_csv(SECTOR_ROT, usecols=["sector", "combined_score", "rotation_signal"])
        sec = sec.rename(columns={"combined_score": "sector_combined_score"})
        sec["rotation_signal_enc"] = sec["rotation_signal"].map(ROTATION_MAP).fillna(2)
        df = df.merge(sec[["sector", "sector_combined_score", "rotation_signal_enc"]],
                      on="sector", how="left")
        return df

    def _add_sector_rolling(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add per-sector rolling 5D/20D/60D flow scores from the latest date in sector_flow_scores."""
        if not SECTOR_FLOW.exists():
            logger.warning("[FeatureEng] sector_flow_scores.csv missing -- skipping rolling sector features")
            return df
        flows = pd.read_csv(SECTOR_FLOW)
        latest_date = flows["date"].max()
        latest = flows[flows["date"] == latest_date].copy()

        rename = {
            "FII_OI_5D":        "sec_FII_5d",
            "FII_OI_20D":       "sec_FII_20d",
            "FII_OI_60D":       "sec_FII_60d",
            "DII_OI_5D":        "sec_DII_5d",
            "DII_OI_20D":       "sec_DII_20d",
            "DII_OI_60D":       "sec_DII_60d",
            "Smart_Money_Score": "sec_smart_money",
            "Retail_Score":      "sec_retail_score",
        }
        avail = {k: v for k, v in rename.items() if k in latest.columns}
        sec_cols = list(avail.keys())
        latest = latest[["sector"] + sec_cols].rename(columns=avail)
        logger.info("[FeatureEng] Sector rolling flows from %s (%d sectors)", latest_date, len(latest))
        return df.merge(latest, on="sector", how="left")

    def _add_participant(self, df: pd.DataFrame) -> pd.DataFrame:
        if not PART_INTEL.exists():
            return df
        usecols = ["date", "FII_flow_score", "DII_flow_score", "Smart_Money_Score", "Market_Regime"]
        peek = pd.read_csv(PART_INTEL, nrows=0).columns.tolist()
        usecols = [c for c in usecols if c in peek]
        part = pd.read_csv(PART_INTEL, usecols=usecols).sort_values("date").iloc[-1]
        df["part_FII_flow"]   = float(part.get("FII_flow_score",   0) or 0)
        df["part_DII_flow"]   = float(part.get("DII_flow_score",   0) or 0)
        df["part_smart_money"] = float(part.get("Smart_Money_Score", 0) or 0)
        df["regime_enc"]      = REGIME_MAP.get(str(part.get("Market_Regime", "NEUTRAL")), 2)
        return df

    def _add_fundamentals(self, df: pd.DataFrame) -> pd.DataFrame:
        if not FUND_MASTER.exists():
            logger.warning("[FeatureEng] company_fundamentals_master.csv missing -- skipping fundamentals")
            return df
        fund = pd.read_csv(FUND_MASTER)
        fund["symbol"] = fund["symbol"].str.strip().str.upper()
        fund["mkt_cap_enc"] = fund["market_cap_category"].str.upper().map(MKTCAP_MAP)

        keep = ["symbol", "mkt_cap_enc"]
        for col, out in [("promoter_holding_pct", "fund_promoter_pct"),
                         ("fii_holding_pct",      "fund_fii_pct"),
                         ("dii_holding_pct",      "fund_dii_pct")]:
            if col in fund.columns:
                fund[out] = pd.to_numeric(fund[col], errors="coerce")
                keep.append(out)

        logger.info("[FeatureEng] Fundamentals master: %d symbols", fund["symbol"].nunique())
        return df.merge(fund[keep], on="symbol", how="left")

    def _add_shareholding(self, df: pd.DataFrame) -> pd.DataFrame:
        """Latest quarterly SHP per symbol -> promoter/FII/DII %."""
        if not SHP_CSV.exists():
            logger.warning("[FeatureEng] quarterly_shp.csv missing -- skipping SHP features")
            return df
        shp = pd.read_csv(SHP_CSV)
        shp["symbol"] = shp["symbol"].str.strip().str.upper()
        # Keep only the latest quarter per symbol (sort by quarter_end_date desc)
        shp["quarter_end_date"] = pd.to_datetime(shp["quarter_end_date"], format="%d-%b-%Y", errors="coerce")
        shp = (shp.sort_values("quarter_end_date", ascending=False)
                   .drop_duplicates(subset=["symbol"], keep="first"))
        rename = {
            "promoter_pct": "shp_promoter_pct",
            "fii_pct":      "shp_fii_pct",
            "dii_pct":      "shp_dii_pct",
        }
        shp = shp.rename(columns=rename)
        keep = ["symbol"] + [v for v in rename.values() if v in shp.columns]
        for col in keep[1:]:
            shp[col] = pd.to_numeric(shp[col], errors="coerce")
        logger.info("[FeatureEng] SHP: %d symbols (latest quarter each)", len(shp))
        return df.merge(shp[keep], on="symbol", how="left")

    def _add_index_membership(self, df: pd.DataFrame) -> pd.DataFrame:
        if not INDEX_MEMB.exists():
            return df
        idx = pd.read_csv(INDEX_MEMB, usecols=["symbol", "index_count"])
        idx["symbol"] = idx["symbol"].str.strip().str.upper()
        idx["index_count"] = pd.to_numeric(idx["index_count"], errors="coerce").fillna(0)
        logger.info("[FeatureEng] Index membership: %d symbols", len(idx))
        return df.merge(idx, on="symbol", how="left")

    def _add_corporate_actions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate corporate actions over the last 12 months per symbol."""
        if not CORP_ACT.exists():
            return df
        acts = pd.read_csv(CORP_ACT, usecols=["symbol", "ex_date", "action_type"])
        acts["symbol"]  = acts["symbol"].str.strip().str.upper()
        acts["ex_date"] = pd.to_datetime(acts["ex_date"], errors="coerce")
        cutoff = pd.Timestamp(date.today() - timedelta(days=365))
        acts = acts[acts["ex_date"] >= cutoff]

        div  = acts[acts["action_type"] == "DIVIDEND"].groupby("symbol").size().rename("div_count_12m")
        buy  = acts[acts["action_type"] == "BUYBACK"].groupby("symbol").size().rename("buyback_count")
        bon  = acts[acts["action_type"] == "BONUS"].groupby("symbol").size().rename("bonus_count")

        agg = pd.concat([div, buy, bon], axis=1).fillna(0).reset_index()
        agg["has_buyback_12m"] = (agg["buyback_count"] > 0).astype(int)
        agg["has_bonus_12m"]   = (agg["bonus_count"]   > 0).astype(int)
        keep = ["symbol", "div_count_12m", "has_buyback_12m", "has_bonus_12m"]
        logger.info("[FeatureEng] Corporate actions 12M: %d symbols with activity", len(agg))
        return df.merge(agg[keep], on="symbol", how="left")

    def _add_corporate_confidence(self, df: pd.DataFrame) -> pd.DataFrame:
        if not CORP_CONF.exists():
            return df
        corp = pd.read_csv(CORP_CONF, usecols=["symbol", "confidence_score_12m"])
        corp["symbol"] = corp["symbol"].str.strip().str.upper()
        corp = corp.rename(columns={"confidence_score_12m": "corp_confidence"})
        return df.merge(corp, on="symbol", how="left")

    def _add_deal_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        if not DEAL_SIG.exists():
            return df
        deals = pd.read_csv(DEAL_SIG, usecols=["symbol", "inst_net_value_cr"])
        deals["symbol"] = deals["symbol"].str.strip().str.upper()
        deals = deals.rename(columns={"inst_net_value_cr": "deal_net_cr"})
        return df.merge(deals, on="symbol", how="left")

    def _add_announcement_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Phase 18C — 7 announcement-derived features.
        All windows are point-in-time from today backward (no look-ahead).
        """
        if not ANN_CSV.exists():
            logger.warning("[FeatureEng] company_announcements.csv missing -- skipping ann features")
            return df

        ann = pd.read_csv(
            ANN_CSV,
            usecols=["symbol", "date", "announcement_type", "signal_score"],
            dtype=str,
        )
        ann["signal_score"] = pd.to_numeric(ann["signal_score"], errors="coerce").fillna(0).astype(int)
        ann["date"]   = pd.to_datetime(ann["date"], errors="coerce")
        ann["symbol"] = ann["symbol"].str.strip().str.upper()
        ann = ann.dropna(subset=["date"])

        today  = pd.Timestamp.now().normalize()
        cut30  = today - pd.Timedelta(days=30)
        cut60  = today - pd.Timedelta(days=60)
        cut180 = today - pd.Timedelta(days=180)

        w30  = ann[ann["date"] >= cut30]
        w60  = ann[ann["date"] >= cut60]
        w180 = ann[ann["date"] >= cut180]

        score_30d    = w30.groupby("symbol")["signal_score"].sum().rename("ann_score_30d")
        high_30d     = (w30[w30["signal_score"] >= 70]
                        .groupby("symbol").size().rename("high_signal_30d"))
        distinct_30d = (w30.groupby("symbol")["announcement_type"]
                        .nunique().rename("distinct_types_30d"))
        cnt_30d      = w30.groupby("symbol").size().rename("_cnt_30d")
        cnt_60d      = w60.groupby("symbol").size().rename("_cnt_60d")
        velocity     = (cnt_30d / cnt_60d.clip(lower=1)).rename("ann_velocity_30d")
        order_wins   = (w180[w180["announcement_type"] == "ORDER_WIN"]
                        .groupby("symbol").size().rename("order_wins_6m"))
        spurt_30d    = (w30[w30["announcement_type"] == "VOLUME_ALERT"]
                        .groupby("symbol").size().rename("spurt_count_30d"))
        distress_30d = (w30[w30["announcement_type"] == "DISTRESS"]
                        .groupby("symbol").size().rename("distress_30d"))

        agg = pd.concat(
            [score_30d, high_30d, distinct_30d, velocity,
             order_wins, spurt_30d, distress_30d],
            axis=1,
        ).fillna(0).reset_index()
        agg["ann_velocity_30d"] = agg["ann_velocity_30d"].round(3)

        logger.info("[FeatureEng] Announcement features: %d symbols with data", len(agg))
        return df.merge(agg, on="symbol", how="left")

    # ------------------------------------------------------------------
    # Phase F alt-data feature methods
    # ------------------------------------------------------------------
    def _add_theme_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Per-symbol max theme score (from theme_intelligence) and max purity score
        (from theme_tagging). Pure-play stocks rank higher in their theme.
        """
        added = False

        if THEME_INTEL.exists() and THEME_TAG.exists():
            try:
                intel = pd.read_csv(THEME_INTEL, usecols=["theme", "theme_score"])
                tag   = pd.read_csv(THEME_TAG)
                tag["SYMBOL"] = tag["SYMBOL"].str.strip().str.upper()
                tag["THEME"]  = tag["THEME"].str.strip().str.upper()
                tag["PURITY_SCORE"] = pd.to_numeric(tag["PURITY_SCORE"], errors="coerce")

                # Join theme score into tagging table
                intel["theme"] = intel["theme"].str.strip().str.upper()
                intel["theme_score"] = pd.to_numeric(intel["theme_score"], errors="coerce")
                tag = tag.merge(intel, left_on="THEME", right_on="theme", how="left")

                # Max theme_score per symbol (best performing theme the stock belongs to)
                ts_max = (tag.groupby("SYMBOL")["theme_score"].max().rename("theme_score_max")
                            .reset_index().rename(columns={"SYMBOL": "symbol"}))
                # Max purity across all themes for the symbol
                tp_max = (tag.groupby("SYMBOL")["PURITY_SCORE"].max().rename("theme_purity_max")
                            .reset_index().rename(columns={"SYMBOL": "symbol"}))

                df = df.merge(ts_max, on="symbol", how="left")
                df = df.merge(tp_max, on="symbol", how="left")
                added = True
                logger.info("[FeatureEng] Theme features: %d symbols tagged", ts_max["symbol"].nunique())
            except Exception as e:
                logger.warning("[FeatureEng] Theme features failed: %s", e)
        elif THEME_TAG.exists():
            # Fallback: just purity scores without theme score
            try:
                tag = pd.read_csv(THEME_TAG)
                tag["SYMBOL"] = tag["SYMBOL"].str.strip().str.upper()
                tag["PURITY_SCORE"] = pd.to_numeric(tag["PURITY_SCORE"], errors="coerce")
                tp_max = (tag.groupby("SYMBOL")["PURITY_SCORE"].max().rename("theme_purity_max")
                            .reset_index().rename(columns={"SYMBOL": "symbol"}))
                df = df.merge(tp_max, on="symbol", how="left")
                added = True
            except Exception as e:
                logger.warning("[FeatureEng] Theme purity fallback failed: %s", e)

        if not added:
            logger.warning("[FeatureEng] theme_tagging.csv / theme_intelligence.csv missing -- skipping theme features")

        return df

    def _add_news_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rolling 7-day news sentiment per symbol from news_signals.csv (Phase F)."""
        if not NEWS_SIGNALS.exists():
            logger.warning("[FeatureEng] news_signals.csv missing -- skipping news sentiment feature")
            return df
        try:
            news = pd.read_csv(NEWS_SIGNALS, usecols=["symbol", "sentiment_7d"])
            news["symbol"] = news["symbol"].str.strip().str.upper()
            news["sentiment_7d"] = pd.to_numeric(news["sentiment_7d"], errors="coerce")
            news = news.rename(columns={"sentiment_7d": "news_sentiment_7d"})
            # Dedup: if multiple rows per symbol take mean
            news = news.groupby("symbol")["news_sentiment_7d"].mean().reset_index()
            logger.info("[FeatureEng] News sentiment: %d symbols", len(news))
            return df.merge(news, on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng] News sentiment failed: %s", e)
            return df

    def _add_insider_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """30-day insider net-buy score per symbol from insider_signals.csv (Phase F).
        insider_score = net_value_30d_cr.clip(-20, 20) — ML-ready numeric."""
        if not INSIDER_SIGS.exists():
            logger.warning("[FeatureEng] insider_signals.csv missing -- skipping insider feature")
            return df
        try:
            ins = pd.read_csv(INSIDER_SIGS, usecols=["symbol", "insider_score"])
            ins["symbol"] = ins["symbol"].str.strip().str.upper()
            ins["insider_score"] = pd.to_numeric(ins["insider_score"], errors="coerce")
            logger.info("[FeatureEng] Insider signals: %d symbols", len(ins))
            return df.merge(ins, on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng] Insider signals failed: %s", e)
            return df

    def _add_consensus(self, df: pd.DataFrame) -> pd.DataFrame:
        """Phase G multi-signal consensus score [0-100] per symbol."""
        if not CONSENSUS.exists():
            logger.warning("[FeatureEng] consensus_scores.csv missing -- skipping consensus feature")
            return df
        try:
            cs = pd.read_csv(CONSENSUS, usecols=["symbol", "consensus_score"])
            cs["symbol"] = cs["symbol"].str.strip().str.upper()
            cs["consensus_score"] = pd.to_numeric(cs["consensus_score"], errors="coerce")
            logger.info("[FeatureEng] Consensus scores: %d symbols", len(cs))
            return df.merge(cs, on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng] Consensus feature failed: %s", e)
            return df

    def _add_concall_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Latest concall guidance + sentiment scores from concall_summary.csv (Phase F).
        guidance_score: RAISED=2, MAINTAINED=1, LOWERED=-1, NOT_GIVEN=0
        sentiment_score: BULLISH=1, NEUTRAL=0, BEARISH=-1"""
        if not CONCALL_SUM.exists():
            logger.warning("[FeatureEng] concall_summary.csv missing -- skipping concall feature")
            return df
        try:
            cols_want = ["symbol", "guidance_score", "sentiment_score"]
            peek = pd.read_csv(CONCALL_SUM, nrows=0).columns.tolist()
            usecols = [c for c in cols_want if c in peek]
            cc = pd.read_csv(CONCALL_SUM, usecols=usecols)
            cc["symbol"] = cc["symbol"].str.strip().str.upper()
            rename = {
                "guidance_score":  "concall_guidance_score",
                "sentiment_score": "concall_sentiment_score",
            }
            cc = cc.rename(columns={k: v for k, v in rename.items() if k in cc.columns})
            for col in ["concall_guidance_score", "concall_sentiment_score"]:
                if col in cc.columns:
                    cc[col] = pd.to_numeric(cc[col], errors="coerce")
            logger.info("[FeatureEng] Concall signals: %d symbols", len(cc))
            return df.merge(cc, on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng] Concall signals failed: %s", e)
            return df

    # ------------------------------------------------------------------
    # Phase 12A — enriched feature methods
    # ------------------------------------------------------------------

    def _add_extended_financials(self, df: pd.DataFrame) -> pd.DataFrame:
        """OPM%, ROCE%, 3Y Sales Growth CAGR from Phase 15B extended_financials.csv."""
        if not EXT_FIN.exists():
            logger.warning("[FeatureEng 12A] extended_financials.csv missing -- skipping")
            return df
        try:
            ef = pd.read_csv(
                EXT_FIN,
                usecols=["symbol", "opm_pct", "roce_pct", "sales_growth_cagr_pct"],
            )
            ef["symbol"] = ef["symbol"].str.strip().str.upper()
            ef = ef.rename(columns={"sales_growth_cagr_pct": "sales_growth_3y"})
            for col in ["opm_pct", "roce_pct", "sales_growth_3y"]:
                ef[col] = pd.to_numeric(ef[col], errors="coerce")
            # Clip extreme outliers before training
            ef["opm_pct"]        = ef["opm_pct"].clip(-50, 80)
            ef["roce_pct"]       = ef["roce_pct"].clip(-20, 60)
            ef["sales_growth_3y"] = ef["sales_growth_3y"].clip(-20, 100)
            logger.info("[FeatureEng 12A] Extended financials: %d symbols", ef["symbol"].nunique())
            return df.merge(ef, on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng 12A] Extended financials failed: %s", e)
            return df

    def _add_valuation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """P/E (log), ROE%, valuation label, YoY revenue & profit growth from Phase 15 valuation_scores.csv."""
        if not VAL_SCORES.exists():
            logger.warning("[FeatureEng 12A] valuation_scores.csv missing -- skipping")
            return df
        try:
            vs = pd.read_csv(
                VAL_SCORES,
                usecols=["symbol", "pe_ratio", "roe_pct", "valuation_label",
                         "yoy_revenue_pct", "yoy_profit_pct"],
            )
            vs["symbol"] = vs["symbol"].str.strip().str.upper()
            vs["pe_ratio"]       = pd.to_numeric(vs["pe_ratio"],       errors="coerce")
            vs["roe_pct"]        = pd.to_numeric(vs["roe_pct"],        errors="coerce")
            vs["yoy_revenue_pct"] = pd.to_numeric(vs["yoy_revenue_pct"], errors="coerce")
            vs["yoy_profit_pct"]  = pd.to_numeric(vs["yoy_profit_pct"],  errors="coerce")
            # log1p(max(0, pe)) compresses the long right tail; negative PE → NaN
            vs["pe_ratio_log"] = np.where(
                vs["pe_ratio"].notna() & (vs["pe_ratio"] > 0),
                np.log1p(vs["pe_ratio"]).clip(0, 5.5),
                np.nan,
            )
            vs["roe_pct"]         = vs["roe_pct"].clip(-30, 80)
            vs["yoy_revenue_pct"] = vs["yoy_revenue_pct"].clip(-50, 200)
            vs["yoy_profit_pct"]  = vs["yoy_profit_pct"].clip(-100, 300)
            vs["valuation_label_enc"] = (
                vs["valuation_label"].str.strip().str.upper().map(VALUATION_MAP).fillna(1)
            )
            keep = ["symbol", "pe_ratio_log", "roe_pct", "valuation_label_enc",
                    "yoy_revenue_pct", "yoy_profit_pct"]
            logger.info("[FeatureEng 12A] Valuation features: %d symbols", vs["symbol"].nunique())
            return df.merge(vs[keep], on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng 12A] Valuation features failed: %s", e)
            return df

    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """vs_200_dma and trend_signal from Phase A technical_indicators.csv."""
        if not TECH_IND.exists():
            logger.warning("[FeatureEng 12A] technical_indicators.csv missing -- skipping")
            return df
        try:
            ti = pd.read_csv(TECH_IND, usecols=["symbol", "vs_dma_200", "trend_signal"])
            ti["symbol"]    = ti["symbol"].str.strip().str.upper()
            ti["vs_dma_200"] = pd.to_numeric(ti["vs_dma_200"], errors="coerce").clip(-60, 100)
            ti["trend_signal_enc"] = (
                ti["trend_signal"].str.strip().str.upper().map(TREND_MAP).fillna(1)
            )
            keep = ["symbol", "vs_dma_200", "trend_signal_enc"]
            logger.info("[FeatureEng 12A] Technical features: %d symbols", ti["symbol"].nunique())
            return df.merge(ti[keep], on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng 12A] Technical features failed: %s", e)
            return df

    def _add_fno_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """F&O OI signal from Phase A fno_intelligence.csv (211 F&O-eligible stocks)."""
        if not FNO_INTEL.exists():
            logger.warning("[FeatureEng 12A] fno_intelligence.csv missing -- skipping")
            return df
        try:
            fi = pd.read_csv(FNO_INTEL, usecols=["symbol", "oi_signal"])
            fi["symbol"] = fi["symbol"].str.strip().str.upper()
            fi["fno_oi_signal_enc"] = (
                fi["oi_signal"].str.strip().str.upper().map(FNO_OI_MAP).fillna(1)
            )
            keep = ["symbol", "fno_oi_signal_enc"]
            logger.info("[FeatureEng 12A] F&O features: %d symbols (rest get NaN)", fi["symbol"].nunique())
            return df.merge(fi[keep], on="symbol", how="left")
        except Exception as e:
            logger.warning("[FeatureEng 12A] F&O features failed: %s", e)
            return df

    # ------------------------------------------------------------------
    # Validation + save
    # ------------------------------------------------------------------
    def _validate(self, df: pd.DataFrame):
        assert not df.empty, "Feature matrix is empty"
        assert "symbol" in df.columns, "Missing symbol column"
        numeric = df.select_dtypes(include=[np.number]).columns
        inf_count = np.isinf(df[numeric]).sum().sum()
        if inf_count > 0:
            logger.warning("[FeatureEng] %d Inf values -- replacing with NaN", inf_count)
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
        null_pct = df[numeric].isnull().mean().sort_values(ascending=False)
        high_null = null_pct[null_pct > 0.5]
        if not high_null.empty:
            logger.warning("[FeatureEng] Features with >50%% nulls: %s", high_null.index.tolist())
        logger.info("[FeatureEng] Validated: %d rows, %d cols, %d total nulls",
                    len(df), len(df.columns), df.isnull().sum().sum())

    def _save(self, df: pd.DataFrame):
        tmp = OUTPUT_PATH.with_suffix(".tmp.parquet")
        df.to_parquet(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_PATH))

        tmp_csv = OUTPUT_CSV.with_suffix(".tmp.csv")
        df.to_csv(tmp_csv, index=False)
        shutil.move(str(tmp_csv), str(OUTPUT_CSV))
        logger.info("[FeatureEng] Saved: %s", OUTPUT_PATH)


if __name__ == "__main__":
    engine = FeatureEngineeringEngine()
    engine.run()

    df = pd.read_parquet(OUTPUT_PATH)
    print(f"\nFeature matrix: {len(df)} symbols x {len(df.columns)} features")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")
    print()

    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    null_pct = df[numeric].isnull().mean().sort_values(ascending=False)
    print("Null % per feature:")
    for col, pct in null_pct.items():
        bar = "#" * int(pct * 20)
        print(f"  {col:30s} {pct*100:5.1f}%  {bar}")

    print()
    print(df[["symbol", "sector", "bull_run_score", "label",
              "shp_fii_pct", "mkt_cap_enc", "index_count"]].head(10).to_string())
