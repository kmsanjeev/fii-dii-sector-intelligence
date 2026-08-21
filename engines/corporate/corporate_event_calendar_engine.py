"""
Corporate Event Calendar Engine
Phase 7B — Board meeting dates, results announcements, AGM/EGM calendar

Downloads the NSE event calendar (board meetings / results dates) and builds:
  1. A cumulative history of all past events (incremental)
  2. An upcoming catalysts file: next 60D events prioritized by
     sector_rotation_intelligence score (high-flow sectors with imminent results)

Data source:
  nselib.capital_market.event_calendar_for_equity(from_date, to_date)
  Columns: symbol, company, purpose, bm_desc, date

Outputs:
  data/intelligence/event_calendar.csv         — full history (incremental)
  data/intelligence/upcoming_catalysts.csv     — next 60D, priority-sorted

Guardrails: G-A-01, G-A-02, G-D-02, G-D-03
"""

import json
import shutil
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.nse_client import create_session
from engines.common.progress import progress

logger = get_logger("corporate_event_calendar")

INTELLIGENCE_DIR  = cfg.INTELLIGENCE_DIR
CALENDAR_HISTORY  = INTELLIGENCE_DIR / "event_calendar.csv"
CATALYSTS_OUTPUT  = INTELLIGENCE_DIR / "upcoming_catalysts.csv"
REFRESH_STATE     = INTELLIGENCE_DIR / "corporate_event_calendar_refresh.json"
SECTOR_INTEL      = INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
CLASSIFICATION    = cfg.DATA_DIR / "reference" / "company_classification_v4.csv"

# Event calendar download start (pre-existing NSE history)
HISTORY_START = "01-01-2023"

# Purpose classification
PURPOSE_RANK = {
    "financial results": 4,
    "dividend":          3,
    "agm":               2,
    "egm":               2,
    "buyback":           4,
    "bonus":             3,
    "rights":            3,
    "split":             2,
    "other":             1,
}


def _classify_purpose(purpose: str) -> str:
    if not purpose:
        return "OTHER"
    p = str(purpose).strip().lower()
    if "financial result" in p or "quarterly" in p or "annual result" in p:
        return "FINANCIAL_RESULTS"
    if "board meeting" in p or p == "board" or p.startswith("board "):
        return "BOARD_MEETING"
    if "dividend" in p:
        return "DIVIDEND"
    if "agm" in p or "annual general" in p:
        return "AGM"
    if "egm" in p or "extra" in p:
        return "EGM"
    if "buyback" in p or "buy back" in p:
        return "BUYBACK"
    if "bonus" in p:
        return "BONUS"
    if "rights" in p:
        return "RIGHTS"
    if "split" in p or "sub-division" in p:
        return "SPLIT"
    return "OTHER"


def _to_nse_fmt(date: datetime) -> str:
    return date.strftime("%d-%m-%Y")


class CorporateEventCalendarEngine:
    """
    Phase 7B — builds an incremental event calendar and surfaces upcoming catalysts.
    """

    def __init__(self):
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.sector_map: dict[str, str] = {}
        self._source_errors: list[str] = []
        self._source_windows: list[dict[str, str]] = []
        self._source_rows = 0
        self._source_session: requests.Session | None = None

    def run(self) -> bool:
        logger.info("[CorporateEventCalendar] Starting Phase 7B")
        self._load_sector_map()

        existing = self._load_existing()
        last_date = existing["event_date"].max() if not existing.empty else ""

        # Catch-up start for any past gap, but ALWAYS rescan the recent week +
        # the forward window: board meetings are scheduled/rescheduled ahead of
        # time, so the calendar must be queried INTO THE FUTURE on every run.
        local_now = datetime.now().astimezone()
        local_tz = local_now.tzinfo
        catchup = (
            datetime.strptime(last_date, "%Y-%m-%d").replace(tzinfo=local_tz)
            + timedelta(days=1)
            if last_date
            else datetime.strptime(HISTORY_START, "%d-%m-%Y").replace(tzinfo=local_tz)
        )
        start = min(catchup, local_now - timedelta(days=7))
        end = local_now + timedelta(days=60)

        attempted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        new_rows = self._download_range(start, end)

        if new_rows:
            new_df  = pd.DataFrame(new_rows)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined = (
                combined
                .drop_duplicates(
                    subset=["event_date", "symbol", "purpose_type"],
                    keep="last",
                )
                .sort_values(["event_date", "symbol"])
                .reset_index(drop=True)
            )
            self._save_atomic(combined, CALENDAR_HISTORY)
            logger.info("[7B] Event calendar: %d rows (added %d)", len(combined), len(new_rows))
        else:
            logger.info("[7B] Event calendar already current")

        # Build upcoming catalysts (next 60 days from today)
        full = pd.read_csv(CALENDAR_HISTORY) if CALENDAR_HISTORY.exists() else pd.DataFrame()
        if not full.empty:
            catalysts = self._build_upcoming_catalysts(full)
            if not catalysts.empty:
                self._save_atomic(catalysts, CATALYSTS_OUTPUT)

        self._write_refresh_state(
            attempted_at=attempted_at,
            start=start,
            end=end,
            existing_rows=len(existing),
            rows_added=len(new_rows),
            final_rows=(len(pd.read_csv(CALENDAR_HISTORY)) if CALENDAR_HISTORY.exists() else 0),
        )
        self._print_summary()
        return not self._source_errors

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
    def _load_sector_map(self):
        if not CLASSIFICATION.exists():
            return
        df = pd.read_csv(CLASSIFICATION, usecols=["SYMBOL", "SECTOR"])
        df["SYMBOL"] = df["SYMBOL"].str.strip().str.upper()
        self.sector_map = dict(zip(df["SYMBOL"], df["SECTOR"]))

    def _load_existing(self) -> pd.DataFrame:
        if not CALENDAR_HISTORY.exists():
            return pd.DataFrame()
        df = pd.read_csv(CALENDAR_HISTORY)
        df["event_date"] = pd.to_datetime(df["event_date"]).dt.strftime("%Y-%m-%d")
        if "retrieved_at" not in df.columns:
            # Legacy records have no row-level acquisition timestamp.  Keep
            # them explicitly null; never backfill a fabricated timestamp.
            df["retrieved_at"] = None
        return df

    # ------------------------------------------------------------------
    # Download (chunked by month to avoid large payloads)
    # ------------------------------------------------------------------
    def _download_range(self, start: datetime, end: datetime) -> list[dict]:
        chunks = []
        cursor = start
        while cursor <= end:
            chunk_end = min(cursor + timedelta(days=30), end)
            chunks.append((cursor, chunk_end))
            cursor = chunk_end + timedelta(days=1)

        rows = []
        self._source_session = create_session(
            "https://www.nseindia.com/companies-listing/corporate-filings-event-calendar"
        )
        for i, (chunk_start, chunk_end) in enumerate(progress(chunks, desc="Event calendar chunks")):
            from_str = _to_nse_fmt(chunk_start)
            to_str   = _to_nse_fmt(chunk_end)
            self._source_windows.append({"from": from_str, "to": to_str})
            chunk_rows = self._fetch_chunk(self._source_session, from_str, to_str)
            rows.extend(chunk_rows)
            self._source_rows += len(chunk_rows)
            if i < len(chunks) - 1:
                time.sleep(cfg.API_DELAY)
        return rows

    def _fetch_chunk(self, session: requests.Session, from_str: str, to_str: str) -> list[dict]:
        endpoint = "https://www.nseindia.com/api/event-calendar"
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            try:
                response = session.get(
                    endpoint,
                    params={
                        "index": "equities",
                        "from_date": from_str,
                        "to_date": to_str,
                    },
                    timeout=cfg.API_TIMEOUT,
                )
                response.raise_for_status()
                df = pd.DataFrame(response.json())
                if df is None or df.empty:
                    return []
                df.columns = df.columns.str.strip()
                rows = []
                retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                for _, r in df.iterrows():
                    symbol = str(r.get("symbol", "")).strip().upper()
                    purpose_raw = str(r.get("purpose", "")).strip()
                    date_raw    = str(r.get("date", "")).strip()
                    try:
                        event_date = pd.to_datetime(date_raw, dayfirst=True).strftime("%Y-%m-%d")
                    except (TypeError, ValueError, OverflowError):
                        continue
                    purpose_type = _classify_purpose(purpose_raw)
                    rows.append({
                        "event_date":    event_date,
                        "symbol":        symbol,
                        "company":       str(r.get("company", "")).strip(),
                        "purpose_raw":   purpose_raw,
                        "purpose_type":  purpose_type,
                        "bm_desc":       str(r.get("bm_desc", "")).strip(),
                        "sector":        self.sector_map.get(symbol, "OTHER"),
                        "retrieved_at":  retrieved_at,
                    })
                return rows
            except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
                if attempt < cfg.MAX_RETRIES:
                    time.sleep(cfg.RETRY_DELAY * attempt)
                else:
                    self._source_errors.append(
                        f"{from_str}..{to_str}: {type(exc).__name__}: {exc}"
                    )
                    logger.warning("[7B] Chunk %s to %s failed: %s", from_str, to_str, exc)
        return []

    def _write_refresh_state(
        self,
        *,
        attempted_at: str,
        start: datetime,
        end: datetime,
        existing_rows: int,
        rows_added: int,
        final_rows: int,
    ) -> None:
        previous: dict = {}
        if REFRESH_STATE.exists():
            try:
                previous = json.loads(REFRESH_STATE.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                previous = {}
        source_ok = not self._source_errors
        state = {
            "dataset": "event_calendar",
            "source_id": "NSE_EVENT_CALENDAR",
            "attempted_at": attempted_at,
            "query_window": {
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            },
            "windows": self._source_windows,
            "source_rows": self._source_rows,
            "rows_added": rows_added,
            "existing_rows": existing_rows,
            "final_rows": final_rows,
            "state": "SUCCESS" if source_ok else "SOURCE_REFRESH_FAILED",
            "last_successful_update": attempted_at if source_ok else previous.get("last_successful_update"),
            "source_errors": self._source_errors,
            "limitations": [
                "Legacy rows retain null retrieved_at values.",
                "Source publication date and row retrieval time are distinct.",
            ],
        }
        tmp = REFRESH_STATE.with_suffix(".tmp.json")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        shutil.move(str(tmp), str(REFRESH_STATE))

    # ------------------------------------------------------------------
    # Upcoming catalysts
    # ------------------------------------------------------------------
    def _build_upcoming_catalysts(self, full: pd.DataFrame) -> pd.DataFrame:
        local_now = datetime.now().astimezone()
        today = local_now.strftime("%Y-%m-%d")
        horizon = (local_now + timedelta(days=60)).strftime("%Y-%m-%d")
        upcoming  = full[(full["event_date"] >= today) & (full["event_date"] <= horizon)].copy()

        if upcoming.empty:
            logger.info("[7B] No upcoming events in next 60 days")
            return pd.DataFrame()

        # Days until event
        upcoming["days_until"] = (
            pd.to_datetime(upcoming["event_date"]) - pd.Timestamp(today)
        ).dt.days

        # Priority: results > dividend > bonus/buyback > AGM > other
        priority_map = {
            "FINANCIAL_RESULTS": 5,
            "BUYBACK":           4,
            "BONUS":             3,
            "DIVIDEND":          3,
            "RIGHTS":            3,
            "SPLIT":             2,
            "AGM":               1,
            "EGM":               1,
            "OTHER":             0,
        }
        upcoming["purpose_priority"] = upcoming["purpose_type"].map(priority_map).fillna(0)

        # Join with sector flow scores (if available)
        if SECTOR_INTEL.exists():
            sector_snap = pd.read_csv(SECTOR_INTEL, usecols=["sector", "FII_flow_score", "combined_score"])
            sector_snap.columns = ["sector", "sector_fii_score", "sector_combined_score"]
            upcoming = upcoming.merge(sector_snap, on="sector", how="left")
        else:
            upcoming["sector_fii_score"]      = 0.0
            upcoming["sector_combined_score"] = 0.0

        # Catalyst priority score: purpose weight + sector flow (normalised)
        upcoming["sector_fii_score"]      = pd.to_numeric(upcoming.get("sector_fii_score", 0), errors="coerce").fillna(0)
        upcoming["sector_combined_score"] = pd.to_numeric(upcoming.get("sector_combined_score", 0), errors="coerce").fillna(0)
        upcoming["catalyst_score"] = (
            upcoming["purpose_priority"] * 10
            + upcoming["sector_combined_score"].clip(-100, 100) / 10
        ).round(2)

        upcoming = upcoming.sort_values(
            ["days_until", "catalyst_score"], ascending=[True, False]
        ).reset_index(drop=True)

        return upcoming

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[7B] Saved %s (%d rows)", path.name, len(df))

    def _print_summary(self):
        print()
        print("=" * 65)
        print("CORPORATE EVENT CALENDAR ENGINE - PHASE 7B COMPLETE")
        print("=" * 65)
        if CALENDAR_HISTORY.exists():
            cal = pd.read_csv(CALENDAR_HISTORY)
            print(f"Event history    : {len(cal)} rows")
            print(f"Date range       : {cal['event_date'].min()} to {cal['event_date'].max()}")
            print("Event types:")
            for ptype, cnt in cal["purpose_type"].value_counts().items():
                print(f"  {ptype:25s}: {cnt}")
        if CATALYSTS_OUTPUT.exists():
            cat = pd.read_csv(CATALYSTS_OUTPUT)
            print()
            print(f"Upcoming catalysts (next 60D): {len(cat)}")
            print("Top priority events:")
            for _, r in cat.head(10).iterrows():
                print(f"  [{r.get('days_until',0):2d}d] {r['symbol']:15s} {r['purpose_type']:20s} "
                      f"sector={r.get('sector','?'):15s} score={r.get('catalyst_score',0):+.1f}")
        print("=" * 65)


if __name__ == "__main__":
    engine = CorporateEventCalendarEngine()
    raise SystemExit(0 if engine.run() else 1)
