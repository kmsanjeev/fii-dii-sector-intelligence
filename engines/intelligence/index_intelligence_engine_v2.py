
"""
Index Intelligence Engine V2
Architecture V2 Production Conversion
"""
from engines.common.config import INDICES_DIR, REFERENCE_DIR, INTELLIGENCE_DIR
from engines.common.logger import get_logger
from engines.common.filesystem import get_latest_file
from engines.common.registry import update_registry
from engines.common.validators import validate_columns
import pandas as pd

logger = get_logger("index_intelligence")

EXCLUDED_FROM_RANKINGS = {
    "DIVIDEND","INVERSE","LEVERAGED","SPECIAL",
    "FIXED_INCOME","GOVERNMENT","CORPORATE_GROUP"
}

def clean_percent(series):
    return (
        series.astype(str).str.replace(",", "", regex=False)
        .str.strip().replace("-", "0")
        .pipe(pd.to_numeric, errors="coerce").fillna(0.0)
    )

def assign_signal(rank,total,score):
    pct = rank / total * 100
    if pct <= 15 and score > 0: return "LEADER"
    elif pct <= 35 and score > 0: return "GAINING"
    elif pct >= 75 and score < 0: return "LAGGARD"
    elif score < 0: return "WEAK"
    return "NEUTRAL"

def main():
    try:
        source = get_latest_file(INDICES_DIR, "MW-All-Indices-*.csv")
        taxonomy = pd.read_csv(REFERENCE_DIR / "index_master.csv")
        df = pd.read_csv(source)
        df.columns=[c.strip() for c in df.columns]

        idx_col = next(c for c in df.columns if c.startswith("INDEX"))
        r30 = next(c for c in df.columns if c.startswith("30 D % CHNG"))
        r365 = next(c for c in df.columns if c.startswith("365 D % CHNG"))

        raw = pd.DataFrame({
            "INDEX_NAME": df[idx_col],
            "RETURN_30D": clean_percent(df[r30]),
            "RETURN_365D": clean_percent(df[r365])
        })

        raw["MOMENTUM_SCORE"]=(raw["RETURN_30D"]*0.7+raw["RETURN_365D"]*0.3).round(2)
        full = raw.merge(taxonomy,on="INDEX_NAME",how="left")
        full["CATEGORY"]=full["CATEGORY"].fillna("UNKNOWN")
        full=full.sort_values("MOMENTUM_SCORE",ascending=False)
        full["RANK"]=range(1,len(full)+1)

        full.to_csv(INTELLIGENCE_DIR/"index_strength.csv",index=False)
        full.to_csv(INTELLIGENCE_DIR/"index_momentum.csv",index=False)

        investable=full[~full["CATEGORY"].isin(EXCLUDED_FROM_RANKINGS)].copy()

        sector=investable[investable["CATEGORY"]=="SECTOR"].copy().sort_values("MOMENTUM_SCORE",ascending=False)
        sector["RANK"]=range(1,len(sector)+1)
        sector["SIGNAL"]=sector.apply(lambda r: assign_signal(r["RANK"],len(sector),r["MOMENTUM_SCORE"]),axis=1)
        sector.to_csv(INTELLIGENCE_DIR/"sector_rotation.csv",index=False)

        theme=investable[investable["CATEGORY"]=="THEME"].copy().sort_values("MOMENTUM_SCORE",ascending=False)
        theme["RANK"]=range(1,len(theme)+1)
        theme["SIGNAL"]=theme.apply(lambda r: assign_signal(r["RANK"],len(theme),r["MOMENTUM_SCORE"]),axis=1)
        theme.to_csv(INTELLIGENCE_DIR/"theme_rotation.csv",index=False)

        update_registry("index_intelligence","SUCCESS",rows_processed=len(full))
    except Exception:
        logger.exception("FAILED")
        update_registry("index_intelligence","FAILED",errors=1)
        raise

if __name__ == "__main__":
    main()
