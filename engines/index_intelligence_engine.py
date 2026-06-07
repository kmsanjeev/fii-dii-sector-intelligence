"""
Index Intelligence Engine V1.1
Capital Flow Intelligence Platform

Changes from V1:
  - AUTO-DETECTS latest MW-All-Indices file (no more hardcoded filename)
  - Excludes non-investable categories from sector/theme rankings
  - Adds SIGNAL column: LEADER / GAINING / NEUTRAL / WEAK / LAGGARD
  - Full universe (all 139) preserved in index_strength.csv + index_momentum.csv
  - sector_rotation.csv and theme_rotation.csv contain ONLY investable indices
"""

from pathlib import Path
from datetime import datetime

import pandas as pd


# ==============================================================
# CONFIGURATION
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDICES_DIR = PROJECT_ROOT / "data" / "NSE" / "indices"

INDEX_MASTER_FILE = (
    PROJECT_ROOT / "data" / "reference" / "index_master.csv"
)

INTELLIGENCE_DIR = PROJECT_ROOT / "data" / "intelligence"

LOG_DIR = PROJECT_ROOT / "logs" / "index_intelligence"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "index_intelligence.log"

# Categories excluded from leadership rankings (not actionable rotation signals)
EXCLUDED_FROM_RANKINGS = {
    "DIVIDEND", "INVERSE", "LEVERAGED",
    "SPECIAL", "FIXED_INCOME", "GOVERNMENT",
    "CORPORATE_GROUP",
}


# ==============================================================
# UTILITIES
# ==============================================================

def write_log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


def detect_latest_mw_file() -> Path:
    """
    Auto-detect the most recently modified MW-All-Indices file.
    Eliminates need to edit code every new download cycle.
    """
    candidates = list(INDICES_DIR.glob("MW-All-Indices-*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No MW-All-Indices-*.csv found in {INDICES_DIR}\n"
            "Download from NSE -> Market Watch -> All Indices and place in data/NSE/indices/"
        )
    latest = max(candidates, key=lambda x: x.stat().st_mtime)
    return latest


def clean_percent(series: pd.Series) -> pd.Series:
    """Parse NSE percent strings to float, treating '-' as 0."""
    return (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace("-", "0")
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0.0)
    )


def assign_signal(rank: int, total: int, score: float) -> str:
    """
    Classify momentum signal based on percentile rank and score direction.

    LEADER  : top 15% AND positive momentum
    GAINING : top 35% AND positive momentum
    NEUTRAL : middle band (or flat score)
    WEAK    : negative momentum, not yet bottom 25%
    LAGGARD : bottom 25% AND negative momentum
    """
    pct = rank / total * 100
    if pct <= 15 and score > 0:
        return "LEADER"
    elif pct <= 35 and score > 0:
        return "GAINING"
    elif pct >= 75 and score < 0:
        return "LAGGARD"
    elif score < 0:
        return "WEAK"
    else:
        return "NEUTRAL"


# ==============================================================
# MAIN
# ==============================================================

def main():

    print("\n=== INDEX INTELLIGENCE ENGINE V1.1 ===\n")
    write_log("START")

    # ----------------------------------------------------------
    # AUTO-DETECT LATEST MW FILE
    # ----------------------------------------------------------
    index_file = detect_latest_mw_file()
    write_log(f"Source={index_file.name}")
    print(f"Source file : {index_file.name}")

    # ----------------------------------------------------------
    # LOAD RAW INDEX DATA
    # ----------------------------------------------------------
    df = pd.read_csv(index_file)
    df.columns = [col.strip() for col in df.columns]

    # Detect column names dynamically -- NSE may rename them
    index_col  = next(c for c in df.columns if c.startswith("INDEX"))
    ret30_col  = next(c for c in df.columns if c.startswith("30 D % CHNG"))
    ret365_col = next(c for c in df.columns if c.startswith("365 D % CHNG"))

    raw = pd.DataFrame({
        "INDEX_NAME":  df[index_col],
        "RETURN_30D":  clean_percent(df[ret30_col]),
        "RETURN_365D": clean_percent(df[ret365_col]),
    })

    # ----------------------------------------------------------
    # LOAD TAXONOMY
    # ----------------------------------------------------------
    taxonomy = pd.read_csv(INDEX_MASTER_FILE)

    # ----------------------------------------------------------
    # MOMENTUM SCORE
    # Weightings: 70% recent (30D) + 30% trend (365D)
    # ----------------------------------------------------------
    raw["MOMENTUM_SCORE"] = (
        raw["RETURN_30D"] * 0.70
        + raw["RETURN_365D"] * 0.30
    ).round(2)

    # Merge taxonomy (drop any stale CATEGORY if raw already has one)
    if "CATEGORY" in raw.columns:
        raw = raw.drop(columns=["CATEGORY"])
    full = raw.merge(taxonomy, on="INDEX_NAME", how="left")
    full["CATEGORY"] = full["CATEGORY"].fillna("UNKNOWN")

    # ----------------------------------------------------------
    # FULL UNIVERSE OUTPUT (all 139 indices)
    # ----------------------------------------------------------
    full = full.sort_values("MOMENTUM_SCORE", ascending=False)
    full["RANK"] = range(1, len(full) + 1)
    full.to_csv(INTELLIGENCE_DIR / "index_strength.csv", index=False)
    full.to_csv(INTELLIGENCE_DIR / "index_momentum.csv", index=False)

    # ----------------------------------------------------------
    # INVESTABLE UNIVERSE (exclude non-actionable categories)
    # ----------------------------------------------------------
    investable = full[~full["CATEGORY"].isin(EXCLUDED_FROM_RANKINGS)].copy()

    # ----------------------------------------------------------
    # SECTOR ROTATION
    # ----------------------------------------------------------
    sector_df = (
        investable[investable["CATEGORY"] == "SECTOR"]
        .copy()
        .sort_values("MOMENTUM_SCORE", ascending=False)
    )
    sector_df["RANK"] = range(1, len(sector_df) + 1)
    n = len(sector_df)
    sector_df["SIGNAL"] = sector_df.apply(
        lambda r: assign_signal(r["RANK"], n, r["MOMENTUM_SCORE"]), axis=1
    )
    sector_df.to_csv(INTELLIGENCE_DIR / "sector_rotation.csv", index=False)

    # ----------------------------------------------------------
    # THEME ROTATION
    # ----------------------------------------------------------
    theme_df = (
        investable[investable["CATEGORY"] == "THEME"]
        .copy()
        .sort_values("MOMENTUM_SCORE", ascending=False)
    )
    theme_df["RANK"] = range(1, len(theme_df) + 1)
    m = len(theme_df)
    theme_df["SIGNAL"] = theme_df.apply(
        lambda r: assign_signal(r["RANK"], m, r["MOMENTUM_SCORE"]), axis=1
    )
    theme_df.to_csv(INTELLIGENCE_DIR / "theme_rotation.csv", index=False)

    # ----------------------------------------------------------
    # LOGGING & CONSOLE OUTPUT
    # ----------------------------------------------------------
    write_log(f"FullUniverse={len(full)}")
    write_log(f"SectorIndices={len(sector_df)}")
    write_log(f"ThemeIndices={len(theme_df)}")
    write_log("COMPLETE")

    print(f"Full Universe   : {len(full)} indices")
    print(f"Sector Universe : {len(sector_df)} indices")
    print(f"Theme Universe  : {len(theme_df)} indices")
    print("\nOutputs:")
    print(f"  index_strength.csv   (all {len(full)} indices)")
    print(f"  index_momentum.csv   (all {len(full)} indices)")
    print(f"  sector_rotation.csv  ({len(sector_df)} sector indices)")
    print(f"  theme_rotation.csv   ({len(theme_df)} theme indices)")
    print(f"\nNote: DIVIDEND / INVERSE / LEVERAGED / SPECIAL excluded from rotation rankings.")


if __name__ == "__main__":
    main()
