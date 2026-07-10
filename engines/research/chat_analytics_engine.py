"""
Chat Analytics Engine
Phase V2 -- Aggregates the conversation log into the demand dataset:
what users ask most, what least, in which language, by voice or text.
This is the training foundation for future ML personalisation.

Reads (read-only, G-D-01):
  data/chat/conversation_log.csv          every chat turn (voice + text)
  data/NSE/equity_master/*.csv            symbol list for mention extraction

Writes (atomic, G-D-02):
  data/intelligence/chat_analytics.csv
    metric_type: INTENT | LANGUAGE | MODE | HOUR_IST | SYMBOL | SUMMARY
    one row per key with count, share_pct, avg_latency_ms, last_seen

Run:  py -3.11 -m engines.research.chat_analytics_engine
"""

import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

LOG_CSV    = cfg.DATA_DIR / "chat" / "conversation_log.csv"
OUTPUT_CSV = cfg.INTELLIGENCE_DIR / "chat_analytics.csv"

COLS = ["metric_type", "key", "count", "share_pct", "avg_latency_ms",
        "last_seen", "run_date"]

# Symbols shorter than this are skipped for mention-matching (too many false
# positives: IT, MRF-style tickers stay, single/double letters like 'M' don't)
MIN_SYMBOL_LEN = 3
_STOPWORDS = {"THE", "AND", "FOR", "WHAT", "WHICH", "GIVE", "SHOW", "TOP",
              "KYA", "HAI", "AUR", "BEST", "BUY", "SELL", "NSE", "BSE",
              "SCORE", "STOCK", "PRICE", "TODAY", "NOW", "HOW", "WHY", "CAN"}


class ChatAnalyticsEngine:
    """Turns the raw conversation log into ranked demand metrics."""

    def __init__(self):
        self.output_dir = cfg.INTELLIGENCE_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.run_date = date.today().isoformat()

    # ── Entry ─────────────────────────────────────────────────────────────────

    def run(self) -> bool:
        logger.info("[ChatAnalytics] Starting")
        if not LOG_CSV.exists():
            logger.info("[ChatAnalytics] No conversation log yet -- skipped")
            return True   # nothing to analyse is a valid state

        df = pd.read_csv(LOG_CSV)
        if df.empty:
            logger.info("[ChatAnalytics] Log empty -- skipped")
            return True

        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
        df = df.dropna(subset=["ts"])
        df["latency_ms"] = pd.to_numeric(df["latency_ms"], errors="coerce")
        n = len(df)

        rows: list[dict] = []
        rows += self._dimension(df, "intent",   "INTENT",   n)
        rows += self._dimension(df, "language", "LANGUAGE", n)
        rows += self._dimension(df, "mode",     "MODE",     n)
        rows += self._hours(df, n)
        rows += self._symbols(df, n)
        rows.append({
            "metric_type": "SUMMARY", "key": "total_turns", "count": n,
            "share_pct": 100.0,
            "avg_latency_ms": round(float(df["latency_ms"].mean()), 0)
                              if df["latency_ms"].notna().any() else None,
            "last_seen": str(df["ts"].max())[:19], "run_date": self.run_date,
        })
        rows.append({
            "metric_type": "SUMMARY", "key": "unique_sessions",
            "count": int(df["session_id"].nunique()), "share_pct": None,
            "avg_latency_ms": None, "last_seen": str(df["ts"].max())[:19],
            "run_date": self.run_date,
        })

        out = pd.DataFrame(rows, columns=COLS)
        if out.empty:                                           # G-D-03
            raise ValueError("Refusing to write empty analytics frame")
        self._atomic_write(out, OUTPUT_CSV)
        top = out[out["metric_type"] == "INTENT"].head(1)
        logger.info("[ChatAnalytics] Complete -- %d turns analysed; top intent: %s",
                    n, top.iloc[0]["key"] if not top.empty else "n/a")
        return True

    # ── Aggregations ──────────────────────────────────────────────────────────

    def _dimension(self, df: pd.DataFrame, col: str, mtype: str, n: int) -> list[dict]:
        if col not in df.columns:
            return []
        g = df.groupby(df[col].fillna("(unknown)").astype(str))
        rows = []
        for key, grp in g:
            rows.append({
                "metric_type":   mtype,
                "key":           key,
                "count":         len(grp),
                "share_pct":     round(len(grp) / n * 100, 1),
                "avg_latency_ms": round(float(grp["latency_ms"].mean()), 0)
                                  if grp["latency_ms"].notna().any() else None,
                "last_seen":     str(grp["ts"].max())[:19],
                "run_date":      self.run_date,
            })
        rows.sort(key=lambda r: -r["count"])
        return rows

    def _hours(self, df: pd.DataFrame, n: int) -> list[dict]:
        ist_hours = (df["ts"] + pd.Timedelta(hours=5, minutes=30)).dt.hour
        rows = []
        for hour, cnt in ist_hours.value_counts().items():
            rows.append({
                "metric_type": "HOUR_IST", "key": f"{hour:02d}:00",
                "count": int(cnt), "share_pct": round(cnt / n * 100, 1),
                "avg_latency_ms": None, "last_seen": "", "run_date": self.run_date,
            })
        rows.sort(key=lambda r: r["key"])
        return rows

    def _load_symbols(self) -> set[str]:
        try:
            em_dir = cfg.EQUITY_MASTER_DIR
            for name in ("equity_master.csv", "company_fundamentals_master.csv"):
                p = em_dir / name
                if p.exists():
                    s = pd.read_csv(p, usecols=lambda c: c.lower() == "symbol")
                    col = s.columns[0]
                    return {str(x).strip().upper() for x in s[col].dropna()
                            if len(str(x).strip()) >= MIN_SYMBOL_LEN}
        except Exception as e:
            logger.warning("[ChatAnalytics] Symbol load failed: %s", e)
        return set()

    def _symbols(self, df: pd.DataFrame, n: int) -> list[dict]:
        """Which stocks are asked about most (uppercase token match vs master)."""
        universe = self._load_symbols()
        if not universe:
            return []
        counts: dict[str, int] = {}
        last: dict[str, str] = {}
        token_re = re.compile(r"[A-Z][A-Z0-9&-]{2,}")
        for _, r in df.iterrows():
            msg = str(r.get("user_message", "")).upper()
            hits = {t for t in token_re.findall(msg) if t in universe and t not in _STOPWORDS}
            for h in hits:
                counts[h] = counts.get(h, 0) + 1
                last[h] = str(r["ts"])[:19]
        rows = [{
            "metric_type": "SYMBOL", "key": sym, "count": cnt,
            "share_pct": round(cnt / n * 100, 1), "avg_latency_ms": None,
            "last_seen": last[sym], "run_date": self.run_date,
        } for sym, cnt in counts.items()]
        rows.sort(key=lambda r: -r["count"])
        return rows[:50]

    @staticmethod
    def _atomic_write(df: pd.DataFrame, path: Path) -> None:   # G-D-02
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))


if __name__ == "__main__":
    ok = ChatAnalyticsEngine().run()
    sys.exit(0 if ok else 1)
