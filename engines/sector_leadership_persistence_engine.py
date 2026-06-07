"""
Leadership Persistence Engine V1.1
Capital Flow Intelligence Platform

Reads historical index_snapshot.csv and computes for each SECTOR and THEME:

  FIRST_SEEN_DATE    : earliest date this index appeared in snapshot history
  LAST_SEEN_DATE     : latest date (most recent snapshot)
  CURRENT_RANK       : rank on the most recent snapshot date
  CURRENT_SCORE      : momentum score on the most recent snapshot date
  DAYS_IN_TOP_3      : # snapshots where rank was <= 3
  DAYS_IN_TOP_5      : # snapshots where rank was <= 5
  DAYS_IN_TOP_10     : # snapshots where rank was <= 10
  LEADERSHIP_STREAK  : consecutive most-recent snapshots at rank <= 3
  TOTAL_SNAPSHOTS    : total trading days in history
  CONVICTION_SCORE   : composite 0-100 score (scaled by history length)
  SIGNAL             : STRONG_LEADER / LEADER / EMERGING / WATCH / LAGGARD

Corrections from V1:
  1. FIRST_SEEN_DATE and LAST_SEEN_DATE added
  2. Conviction score scaled by history length (min 20 days for full score)
  3. Separate outputs: sector_conviction_scores.csv + theme_conviction_scores.csv
     + combined leadership_conviction_scores.csv

Outputs:
  data/intelligence/sector_leadership_duration.csv
  data/intelligence/theme_leadership_duration.csv
  data/intelligence/sector_conviction_scores.csv    (SECTOR only)
  data/intelligence/theme_conviction_scores.csv     (THEME only)
  data/intelligence/leadership_conviction_scores.csv (combined)
"""

from pathlib import Path
from datetime import datetime

import pandas as pd


# ==============================================================
# CONFIGURATION
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SNAPSHOT_FILE = (
    PROJECT_ROOT
    / "data" / "intelligence" / "history"
    / "index_snapshot.csv"
)

INTEL_DIR = PROJECT_ROOT / "data" / "intelligence"

LOG_DIR = PROJECT_ROOT / "logs" / "leadership_persistence"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "leadership_persistence.log"

# Conviction score fully trusted only after this many trading days of history
HISTORY_SCALE_THRESHOLD = 20


# ==============================================================
# UTILITIES
# ==============================================================

def write_log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


def scale_conviction(raw_score: float, total_days: int) -> float:
    """
    Scale conviction score by available history length.

    With only 1 day of data, a 100% top-5 persistence rate is meaningless.
    Score ramps linearly from 0 to full value as history grows to HISTORY_SCALE_THRESHOLD.

    Examples (raw_score = 90):
      1  day  -> 4.5
      5  days -> 22.5
      10 days -> 45.0
      15 days -> 67.5
      20 days -> 90.0  (full trust)
      30 days -> 90.0  (no change beyond threshold)
    """
    if total_days >= HISTORY_SCALE_THRESHOLD:
        return raw_score
    return round(raw_score * (total_days / HISTORY_SCALE_THRESHOLD), 1)


def assign_signal(
    conviction: float,
    current_rank: int,
    total_indices: int,
) -> str:
    """
    Determine leadership quality signal from conviction and rank.

    STRONG_LEADER  : conviction >= 70 AND top 3
    LEADER         : conviction >= 50 AND top 5
    EMERGING       : conviction >= 30 AND top 40%
    LAGGARD        : bottom 30%
    WATCH          : everything else
    """
    top_40 = max(1, int(total_indices * 0.40))
    bottom_30_threshold = int(total_indices * 0.70)

    if conviction >= 70 and current_rank <= 3:
        return "STRONG_LEADER"
    elif conviction >= 50 and current_rank <= 5:
        return "LEADER"
    elif conviction >= 30 and current_rank <= top_40:
        return "EMERGING"
    elif current_rank > bottom_30_threshold:
        return "LAGGARD"
    else:
        return "WATCH"


# ==============================================================
# CORE COMPUTATION
# ==============================================================

def compute_persistence(df_cat: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    Compute leadership persistence metrics for all indices in one category.

    Args:
        df_cat   : filtered snapshot dataframe (SECTOR or THEME rows only)
        category : "SECTOR" or "THEME"

    Returns:
        DataFrame sorted by CONVICTION_SCORE descending.
    """
    dates = sorted(df_cat["SNAPSHOT_DATE"].unique())
    total_days = len(dates)
    latest_date = dates[-1] if dates else None

    if total_days == 0:
        return pd.DataFrame()

    total_indices = int(
        df_cat[df_cat["SNAPSHOT_DATE"] == latest_date]["INDEX_NAME"].nunique()
    )

    results = []

    for name in df_cat["INDEX_NAME"].unique():

        sub = (
            df_cat[df_cat["INDEX_NAME"] == name]
            .sort_values("SNAPSHOT_DATE")
        )

        # FIRST / LAST seen dates
        first_seen = str(sub["SNAPSHOT_DATE"].min())
        last_seen  = str(sub["SNAPSHOT_DATE"].max())

        # Current snapshot values
        latest_row = sub[sub["SNAPSHOT_DATE"] == latest_date]
        if latest_row.empty:
            current_rank  = total_indices
            current_score = 0.0
        else:
            current_rank  = int(latest_row["RANK"].iloc[0])
            current_score = float(latest_row["MOMENTUM_SCORE"].iloc[0])

        # Leadership band counts
        days_top3  = int((sub["RANK"] <= 3).sum())
        days_top5  = int((sub["RANK"] <= 5).sum())
        days_top10 = int((sub["RANK"] <= 10).sum())

        # Streak: consecutive most-recent snapshots at rank <= 3
        streak = 0
        for _, row in sub.sort_values("SNAPSHOT_DATE", ascending=False).iterrows():
            if row["RANK"] <= 3:
                streak += 1
            else:
                break

        # ----------------------------------------------------------
        # RAW CONVICTION SCORE  (0-100)
        #
        # 50 pts  - % of all snapshots where index was in top 5
        # 30 pts  - recent streak bonus (capped at 15 days for full 30 pts)
        # 20 pts  - current rank percentile bonus
        # ----------------------------------------------------------
        pct_in_top5  = days_top5 / total_days if total_days else 0
        streak_bonus = min(streak / 15.0, 1.0)
        rank_bonus   = max(0.0, 1.0 - (current_rank - 1) / total_indices)

        raw_conviction = (
            pct_in_top5  * 50.0
            + streak_bonus * 30.0
            + rank_bonus   * 20.0
        )

        # Scale conviction by history length to prevent misleading early scores
        conviction = scale_conviction(raw_conviction, total_days)

        signal = assign_signal(conviction, current_rank, total_indices)

        results.append({
            "INDEX_NAME":        name,
            "CATEGORY":          category,
            "FIRST_SEEN_DATE":   first_seen,
            "LAST_SEEN_DATE":    last_seen,
            "CURRENT_RANK":      current_rank,
            "CURRENT_SCORE":     round(current_score, 2),
            "DAYS_IN_TOP_3":     days_top3,
            "DAYS_IN_TOP_5":     days_top5,
            "DAYS_IN_TOP_10":    days_top10,
            "LEADERSHIP_STREAK": streak,
            "TOTAL_SNAPSHOTS":   total_days,
            "CONVICTION_SCORE":  conviction,
            "SIGNAL":            signal,
        })

    return (
        pd.DataFrame(results)
        .sort_values(
            ["CONVICTION_SCORE", "CURRENT_RANK"],
            ascending=[False, True],
        )
    )


# ==============================================================
# MAIN
# ==============================================================

def main():

    print("\n=== LEADERSHIP PERSISTENCE ENGINE V1.1 ===\n")
    write_log("START")

    if not SNAPSHOT_FILE.exists():
        raise FileNotFoundError(
            f"Snapshot file not found: {SNAPSHOT_FILE}\n"
            "Run index_snapshot_engine.py first."
        )

    df = pd.read_csv(SNAPSHOT_FILE)
    df["SNAPSHOT_DATE"] = df["SNAPSHOT_DATE"].astype(str)

    total_rows  = len(df)
    total_days  = df["SNAPSHOT_DATE"].nunique()
    latest_date = df["SNAPSHOT_DATE"].max()

    write_log(f"Rows={total_rows} | TradingDays={total_days} | Latest={latest_date}")

    print(f"Snapshot rows   : {total_rows}")
    print(f"Trading days    : {total_days}")
    print(f"Latest snapshot : {latest_date}")

    if total_days < HISTORY_SCALE_THRESHOLD:
        print(
            f"\nNote: {total_days}/{HISTORY_SCALE_THRESHOLD} days of history. "
            f"Conviction scores are scaled proportionally. "
            f"Full scoring accuracy reached after {HISTORY_SCALE_THRESHOLD} trading days."
        )

    # ----------------------------------------------------------
    # SECTOR PERSISTENCE
    # ----------------------------------------------------------
    sector_snap    = df[df["CATEGORY"] == "SECTOR"]
    sector_persist = compute_persistence(sector_snap, "SECTOR")
    sector_persist.to_csv(INTEL_DIR / "sector_leadership_duration.csv", index=False)
    sector_persist.to_csv(INTEL_DIR / "sector_conviction_scores.csv",   index=False)

    # ----------------------------------------------------------
    # THEME PERSISTENCE
    # ----------------------------------------------------------
    theme_snap    = df[df["CATEGORY"] == "THEME"]
    theme_persist = compute_persistence(theme_snap, "THEME")
    theme_persist.to_csv(INTEL_DIR / "theme_leadership_duration.csv", index=False)
    theme_persist.to_csv(INTEL_DIR / "theme_conviction_scores.csv",   index=False)

    # ----------------------------------------------------------
    # COMBINED OUTPUT (both sectors and themes)
    # ----------------------------------------------------------
    combined = pd.concat([sector_persist, theme_persist], ignore_index=True)
    combined.to_csv(INTEL_DIR / "leadership_conviction_scores.csv", index=False)

    # ----------------------------------------------------------
    # LOGGING & CONSOLE OUTPUT
    # ----------------------------------------------------------
    write_log(f"SectorIndices={len(sector_persist)}")
    write_log(f"ThemeIndices={len(theme_persist)}")
    write_log("COMPLETE")

    display_cols = [
        "INDEX_NAME", "CURRENT_RANK", "DAYS_IN_TOP_3",
        "DAYS_IN_TOP_5", "LEADERSHIP_STREAK",
        "CONVICTION_SCORE", "SIGNAL",
    ]

    print(f"\nSector indices  : {len(sector_persist)}")
    print(f"Theme indices   : {len(theme_persist)}")

    print("\n--- SECTOR LEADERSHIP ---")
    print(sector_persist[display_cols].head(10).to_string(index=False))

    print("\n--- THEME LEADERSHIP ---")
    print(theme_persist[display_cols].to_string(index=False))

    print("\nOutputs:")
    print("  sector_leadership_duration.csv")
    print("  theme_leadership_duration.csv")
    print("  sector_conviction_scores.csv      (SECTOR only)")
    print("  theme_conviction_scores.csv       (THEME only)")
    print("  leadership_conviction_scores.csv  (combined)")


if __name__ == "__main__":
    main()
