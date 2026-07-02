"""
Theme Momentum Engine -- Phase H
Snapshots theme_intelligence.csv daily, computes score deltas vs prior snapshot,
detects phase transitions, and fires P11 Telegram alerts for significant rotations.

Run:
    py -3.11 engines/intelligence/theme_momentum_engine.py

Outputs:
    data/intelligence/theme_momentum.csv          -- current delta vs prior snapshot
    data/intelligence/theme_history/YYYY-MM-DD.csv -- daily archive snapshots

Telegram:
    P11_THEME_ROTATION alert for themes crossing phase thresholds
    Requires TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID in .env

Guardrails: G-D-02 atomic writes, G-D-03 no empty df, G-SYS-01 env var check
"""

import os
import shutil
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

THEME_INTEL_PATH = cfg.INTELLIGENCE_DIR / "theme_intelligence.csv"
MOMENTUM_PATH    = cfg.INTELLIGENCE_DIR / "theme_momentum.csv"
HISTORY_DIR      = cfg.INTELLIGENCE_DIR / "theme_history"

# Phase transition thresholds (theme_score crossing these levels triggers P11)
PHASE_THRESHOLDS = {
    "EMERGING":        45.0,   # NEUTRAL -> EMERGING
    "LEADING":         55.0,   # EARLY_ROTATION -> LEADING
    "MOMENTUM":        62.0,   # LEADING -> MOMENTUM
    "STRONG_MOMENTUM": 70.0,   # exceptional acceleration
}
# Minimum score delta (points) to count as meaningful momentum
DELTA_MIN = 3.0
# P11 alert: only fire when score crosses a threshold OR delta is large
P11_DELTA_ALERT = 5.0


# ── Telegram delivery (reuses project's existing Telegram utility) ────────────

def _send_telegram(message: str) -> bool:
    """Send a Telegram message using bot token + chat ID from .env."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat  = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat:
        logger.warning("[ThemeMomentum] Telegram env vars not set -- skipping alert")
        return False
    try:
        import requests
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat, "text": message, "parse_mode": "HTML"},
                             timeout=10)
        if resp.status_code == 200:
            logger.info("[ThemeMomentum] P11 alert sent")
            return True
        logger.warning("[ThemeMomentum] Telegram returned %d: %s", resp.status_code, resp.text[:100])
    except Exception as ex:
        logger.warning("[ThemeMomentum] Telegram delivery failed: %s", ex)
    return False


def _format_p11(transitions: list[dict]) -> str:
    lines = ["<b>[P11] THEME ROTATION SIGNALS</b>"]
    lines.append(f"<i>{date.today().isoformat()}</i>")
    lines.append("")
    for t in transitions[:8]:
        arrow  = "^" if t["delta"] >= 0 else "v"
        phase  = t.get("phase_transition", "")
        pt_tag = f" [{phase}]" if phase else ""
        lines.append(
            f"{arrow} <b>{t['theme']}</b>{pt_tag}\n"
            f"   Score: {t['prev_score']:.1f} -> {t['curr_score']:.1f} "
            f"(+{t['delta']:.1f})" if t['delta'] >= 0
            else f"   Score: {t['prev_score']:.1f} -> {t['curr_score']:.1f} "
                 f"({t['delta']:.1f})"
        )
    return "\n".join(lines)


def run() -> pd.DataFrame | None:
    logger.info("[ThemeMomentum] Phase H theme momentum engine starting")

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    if not THEME_INTEL_PATH.exists():
        logger.error("[ThemeMomentum] theme_intelligence.csv not found -- run theme_intelligence_engine.py first")
        return None

    curr = pd.read_csv(THEME_INTEL_PATH)
    logger.info("[ThemeMomentum] Loaded %d themes from current snapshot", len(curr))

    curr["theme_score"] = pd.to_numeric(curr["theme_score"], errors="coerce")
    today_str = date.today().isoformat()

    # ── Save today's snapshot ────────────────────────────────────────────────
    snap_path = HISTORY_DIR / f"{today_str}.csv"
    if not snap_path.exists():
        tmp_snap = snap_path.with_suffix(".tmp")
        curr.to_csv(tmp_snap, index=False)
        shutil.move(str(tmp_snap), str(snap_path))
        logger.info("[ThemeMomentum] Snapshot saved: %s", snap_path)

    # ── Find the most recent prior snapshot ──────────────────────────────────
    snap_files = sorted(HISTORY_DIR.glob("????-??-??.csv"), reverse=True)
    prior_snap = None
    for sf in snap_files:
        if sf.name != f"{today_str}.csv":
            prior_snap = sf
            break

    if prior_snap is None:
        logger.info("[ThemeMomentum] No prior snapshot found -- today is the first run. Snapshot saved.")
        print(f"[ThemeMomentum] First run -- snapshot saved. Run again tomorrow to compute momentum.")
        return None

    logger.info("[ThemeMomentum] Comparing vs prior snapshot: %s", prior_snap.name)
    prev = pd.read_csv(prior_snap)
    prev["theme_score"] = pd.to_numeric(prev["theme_score"], errors="coerce")

    # ── Merge and compute deltas ─────────────────────────────────────────────
    merged = curr[["theme", "display_name", "category", "theme_score",
                   "theme_signal", "momentum_phase", "stock_count"]].merge(
        prev[["theme", "theme_score", "momentum_phase"]].rename(columns={
            "theme_score":    "prev_score",
            "momentum_phase": "prev_phase",
        }),
        on="theme",
        how="left"
    )

    merged["prev_score"]  = merged["prev_score"].fillna(merged["theme_score"])
    merged["delta"]       = (merged["theme_score"] - merged["prev_score"]).round(2)
    merged["delta_pct"]   = ((merged["delta"] / merged["prev_score"].clip(lower=0.1)) * 100).round(1)
    merged["days_apart"]  = (pd.Timestamp(today_str) - pd.Timestamp(prior_snap.stem)).days
    merged["prior_date"]  = prior_snap.stem
    merged["as_of_date"]  = today_str

    # ── Detect phase transitions ─────────────────────────────────────────────
    def _detect_transition(row) -> str:
        curr_s = row["theme_score"]
        prev_s = row["prev_score"]
        for phase_name, threshold in sorted(PHASE_THRESHOLDS.items(), key=lambda x: x[1]):
            if prev_s < threshold <= curr_s:
                return f"CROSSED_{phase_name}"
        return ""

    merged["phase_transition"] = merged.apply(_detect_transition, axis=1)

    # ── Write theme_momentum.csv ─────────────────────────────────────────────
    output_cols = [
        "theme", "display_name", "category", "theme_score", "prev_score",
        "delta", "delta_pct", "theme_signal", "momentum_phase", "prev_phase",
        "phase_transition", "stock_count", "days_apart", "prior_date", "as_of_date",
    ]
    out_df = merged[[c for c in output_cols if c in merged.columns]].copy()
    out_df = out_df.sort_values("delta", ascending=False)

    tmp = MOMENTUM_PATH.with_suffix(".tmp")
    out_df.to_csv(tmp, index=False)
    shutil.move(str(tmp), str(MOMENTUM_PATH))
    logger.info("[ThemeMomentum] Wrote %d rows to %s", len(out_df), MOMENTUM_PATH)

    # ── P11 alert evaluation ─────────────────────────────────────────────────
    transitions = []
    for _, row in out_df.iterrows():
        delta = float(row["delta"])
        pt    = str(row.get("phase_transition", ""))
        if abs(delta) >= P11_DELTA_ALERT or pt:
            transitions.append({
                "theme":            str(row["theme"]),
                "display_name":     str(row.get("display_name", "")),
                "curr_score":       float(row["theme_score"]),
                "prev_score":       float(row["prev_score"]),
                "delta":            delta,
                "phase_transition": pt,
            })

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n[ThemeMomentum] Phase H theme momentum complete")
    print(f"  Prior snapshot    : {prior_snap.name} ({merged['days_apart'].iloc[0]} day(s) ago)")
    print(f"  Themes tracked    : {len(out_df)}")
    rising  = (out_df["delta"] >= DELTA_MIN).sum()
    falling = (out_df["delta"] <= -DELTA_MIN).sum()
    print(f"  Rising  (>={DELTA_MIN:g}pt)  : {rising}")
    print(f"  Falling (<=-{DELTA_MIN:g}pt) : {falling}")
    print(f"  Phase transitions  : {len(transitions)}")
    print()

    if out_df["delta"].abs().max() > 0:
        print("  Top movers:")
        movers = out_df.nlargest(5, "delta").append(out_df.nsmallest(3, "delta")) if len(out_df) > 8 else out_df.nlargest(8, "delta")
        for _, r in movers.iterrows():
            sign = "+" if r["delta"] >= 0 else ""
            pt   = f"  [{r['phase_transition']}]" if r.get("phase_transition") else ""
            print(f"    {str(r['theme']):<30} {r['prev_score']:.1f} -> {r['theme_score']:.1f} ({sign}{r['delta']:.1f}){pt}")

    # Fire P11 alert
    if transitions:
        msg = _format_p11(transitions)
        sent = _send_telegram(msg)
        if sent:
            print(f"\n  [P11] Telegram alert sent: {len(transitions)} theme rotation signal(s)")
        else:
            print(f"\n  [P11] Alert ready but Telegram not configured (set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID)")
    else:
        print("  No significant threshold crossings today -- no P11 alert")

    # Clean up old snapshots beyond 90 days
    cutoff_snap = pd.Timestamp.now() - pd.Timedelta(days=90)
    for sf in snap_files:
        try:
            if pd.Timestamp(sf.stem) < cutoff_snap:
                sf.unlink()
                logger.debug("[ThemeMomentum] Purged old snapshot: %s", sf.name)
        except Exception:
            pass

    return out_df


if __name__ == "__main__":
    run()
