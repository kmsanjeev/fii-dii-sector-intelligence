"""
Shareholding Engine -- Phase 15C
Fetches quarterly shareholding patterns (promoter/FII/DII) from NSE XBRL archive.

Data availability:
  NSE API has SHP data from ~FY2008 onwards (1,200+ symbols).
  Pre-2008 NSE had no electronic XBRL filings; paper/PDF only (not parseable).

Primary source:
  NSE API: /api/corporate-share-holdings-master  (found in page JS: activeApiName)
  NSE XBRL: nsearchives.nseindia.com/corporate/xbrl/SHP_*.xml

XBRL schema variants handled:
  V1 (older large-caps): context suffix 'I'         e.g. InstitutionsDomesticI
  V2 (newer format):     context suffix '_ContextI'  e.g. InstitutionsDomestic_ContextI

Fallback:
  Screener.in HTML parsing (per-symbol, only for XBRL failures)

Outputs:
  data/NSE/shareholding/quarterly_shp.csv   -- raw per-symbol per-quarter (all windows)
  data/NSE/equity_master/company_fundamentals_master.csv -- fii/dii/promoter cols updated

CLI:
  --windows N   fetch N most recent windows (default: 1)
  --backfill    fetch all historical quarters from FY2008 to present (incremental)
  --validate    run data validation report on existing quarterly_shp.csv

Guardrails:
  G-D-02: atomic writes  G-D-03: no empty DF  G-I-04: no fillna(0)
  G-A-01: rate limiting  G-A-02: retry+backoff  G-A-03: recovery queue
  G-S-01: EQ series      G-S-04: universe size check
"""

import argparse
import math
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path before importing engines.common
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import requests
import xml.etree.ElementTree as ET

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.progress import progress

logger = get_logger(__name__)

SHAREHOLDING_DIR = cfg.NSE_DIR / "shareholding"
SHP_CSV          = SHAREHOLDING_DIR / "quarterly_shp.csv"
FUNDAMENTALS_CSV = cfg.NSE_DIR / "equity_master" / "company_fundamentals_master.csv"
EQUITY_MASTER    = cfg.NSE_DIR / "equity_master" / "equity_master.csv"
RECOVERY_QUEUE   = cfg.NSE_DIR / "recovery_queue.csv"

SHP_API    = "https://www.nseindia.com/api/corporate-share-holdings-master"
SHP_ORIGIN = "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern"

# Minimum symbols per window to accept as valid (not empty/broken API response)
MIN_SYMBOLS_PER_WINDOW = 50

# Both XBRL schema variants
_XBRL_CONTEXTS = {
    "ShareholdingOfPromoterAndPromoterGroupI":         "promoter_pct",
    "ShareholdingOfPromoterAndPromoterGroup_ContextI": "promoter_pct",
    "InstitutionsDomesticI":                           "dii_pct",
    "InstitutionsDomestic_ContextI":                   "dii_pct",
    "InstitutionsForeignI":                            "fii_pct",
    "InstitutionsForeign_ContextI":                    "fii_pct",
    "PublicShareholdingI":                             "public_pct",
    "PublicShareholding_ContextI":                     "public_pct",
}
_SHP_PCT_TAG = "ShareholdingAsAPercentageOfTotalNumberOfShares"

_SCRN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
}


def _generate_all_windows() -> list[tuple[str, str, str]]:
    """Generate all quarterly windows from Q1FY09 (Apr-Jun 2008) to current quarter.
    Returns list of (from_date, to_date, label) tuples, oldest first.
    NSE SHP data only starts from ~FY08; earlier quarters return 0 or <50 records.
    """
    windows = []
    today = date.today()

    # Quarters: Q1=Apr-Jun, Q2=Jul-Sep, Q3=Oct-Dec, Q4=Jan-Mar
    # FY year N: Apr(N-1) to Mar(N). e.g. FY09 = Apr2008-Mar2009
    # Q1FY09: Apr-Jun 2008  => from_date=01-04-2008, to_date=30-06-2008
    quarters = [
        (4, 1,  6, 30,  "Q1"),   # Q1: Apr-Jun, ends Jun 30
        (7, 1,  9, 30,  "Q2"),   # Q2: Jul-Sep, ends Sep 30
        (10, 1, 12, 31, "Q3"),   # Q3: Oct-Dec, ends Dec 31
        (1, 1,  3, 31,  "Q4"),   # Q4: Jan-Mar, ends Mar 31 (next cal year)
    ]

    for fy in range(9, 100):  # FY09 to FY99 (stops at today)
        cal_year_start = 2000 + fy - 1  # FY09 starts in 2008
        if cal_year_start > today.year + 1:
            break

        for from_m, from_d, to_m, to_d, q_label in quarters:
            if q_label == "Q4":
                # Q4 of FY{fy} is Jan-Mar of the next calendar year
                cal_year = cal_year_start + 1
            else:
                cal_year = cal_year_start

            quarter_end = date(cal_year, to_m, to_d)
            # Skip future quarters
            if quarter_end > today:
                break

            from_str = f"{from_d:02d}-{from_m:02d}-{cal_year}"
            to_str   = f"{to_d:02d}-{to_m:02d}-{cal_year}"
            label    = f"{q_label}FY{fy:02d}"
            windows.append((from_str, to_str, label))

    return windows  # oldest first


# Most recent 4 windows (default incremental mode)
RECENT_WINDOWS = [
    ("01-04-2025", "30-06-2025", "Q1FY26"),
    ("01-01-2025", "31-03-2025", "Q4FY25"),
    ("01-10-2024", "31-12-2024", "Q3FY25"),
    ("01-07-2024", "30-09-2024", "Q2FY25"),
]


def _is_null_xbrl(xbrl_url) -> bool:
    """Detect NSE's sentinel null-archive URL returned for pre-2024 quarters."""
    if not xbrl_url:
        return True
    s = str(xbrl_url).strip()
    return s in ("null", "None", "") or s.endswith("/xbrl/null") or s.endswith("/xbrl/-")


class ShareholdingEngine:
    def __init__(self, windows: int = 1, backfill: bool = False,
                 use_screener_fallback: bool = True, from_quarter: str | None = None):
        self.windows = windows
        self.backfill = backfill
        # Screener only has CURRENT data — disable for historical backfill
        self.use_screener_fallback = use_screener_fallback and not backfill
        self.from_quarter = from_quarter
        SHAREHOLDING_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        # G-S-01/G-S-04: load EQ universe
        if not EQUITY_MASTER.exists():
            logger.error("[ShareholdingEngine] equity_master.csv not found")
            return False
        em = pd.read_csv(EQUITY_MASTER)
        eq_symbols = set(em[em["SERIES"] == "EQ"]["SYMBOL"].str.strip())
        if len(eq_symbols) < 1800:
            logger.error(f"[ShareholdingEngine] Universe too small: {len(eq_symbols)}")
            return False
        logger.info(f"[ShareholdingEngine] EQ universe: {len(eq_symbols)} symbols")

        # Load existing SHP to know which windows are already done (G-D-05 equiv)
        existing = pd.DataFrame()
        if SHP_CSV.exists():
            existing = pd.read_csv(SHP_CSV)
        done_labels = set(existing["window_label"].unique()) if not existing.empty else set()
        logger.info(f"[ShareholdingEngine] Already fetched: {sorted(done_labels)}")

        # Decide which windows to process
        if self.backfill:
            candidate_windows = _generate_all_windows()  # oldest first
            if self.from_quarter:
                labels = [lbl for _, _, lbl in candidate_windows]
                if self.from_quarter in labels:
                    start_idx = labels.index(self.from_quarter)
                    candidate_windows = candidate_windows[start_idx:]
                    logger.info(f"[ShareholdingEngine] --from-quarter: skipping to {self.from_quarter} (dropped {start_idx} earlier windows)")
                else:
                    logger.warning(f"[ShareholdingEngine] --from-quarter '{self.from_quarter}' not found; processing all windows")
        else:
            candidate_windows = RECENT_WINDOWS  # most recent first

        pending = [(f, t, lbl) for f, t, lbl in candidate_windows if lbl not in done_labels]

        if not pending:
            logger.info("[ShareholdingEngine] All windows already fetched — nothing to do")
            return True

        limit = len(pending) if self.backfill else self.windows
        pending = pending[:limit]
        logger.info(f"[ShareholdingEngine] Processing {len(pending)} windows: {[lbl for _,_,lbl in pending]}")

        # Working copy starts from existing data; saved incrementally after each window
        accumulated = existing.copy() if not existing.empty else pd.DataFrame()
        recovery = []
        windows_done = 0

        for from_date, to_date, label in pending:
            logger.info(f"[ShareholdingEngine] Fetching master for {label} ({from_date} to {to_date})")
            master = self._fetch_master(from_date, to_date)
            if master is None or master.empty:
                logger.warning(f"[ShareholdingEngine] No master data for {label} — skipping")
                continue

            # Data validation: window must have meaningful coverage
            master_eq = master[master["symbol"].isin(eq_symbols)].copy()
            if len(master_eq) < MIN_SYMBOLS_PER_WINDOW:
                logger.warning(f"[ShareholdingEngine] {label}: only {len(master_eq)} EQ records (< {MIN_SYMBOLS_PER_WINDOW}) — skipping (pre-XBRL era)")
                continue

            logger.info(f"[ShareholdingEngine] {label}: {len(master_eq)} EQ filings")

            # Parse XBRL for FII/DII breakdown
            rows = self._parse_xbrl_batch(master_eq, label)

            # Screener.in fallback for XBRL failures
            if self.use_screener_fallback:
                missing_syms = [r["symbol"] for r in rows if r.get("fii_pct") is None]
                if missing_syms:
                    logger.info(f"[ShareholdingEngine] Screener fallback for {len(missing_syms)} symbols")
                    fallback_map = {f["symbol"]: f for f in self._fetch_screener_batch(missing_syms)}
                    for r in rows:
                        if r.get("fii_pct") is None and r["symbol"] in fallback_map:
                            fb = fallback_map[r["symbol"]]
                            r["fii_pct"]     = fb.get("fii_pct")
                            r["dii_pct"]     = fb.get("dii_pct")
                            r["promoter_pct"] = fb.get("promoter_pct") or r.get("promoter_pct")
                            r["source"]       = "screener"
                            if fb.get("fii_pct") is None:
                                recovery.append({"symbol": r["symbol"], "window_label": label, "reason": "xbrl_and_screener_failed"})

            # Validate rows before appending
            df_window = pd.DataFrame(rows)
            df_window = self._validate_window(df_window, label)
            if df_window is not None:
                # Merge into accumulated and save after every window (crash recovery)
                accumulated = pd.concat([accumulated, df_window], ignore_index=True)
                accumulated = accumulated.drop_duplicates(subset=["symbol", "window_label"], keep="last")
                self._save_csv(accumulated, SHP_CSV)
                windows_done += 1
                logger.info(f"[ShareholdingEngine] {label}: {len(df_window)} rows — total {len(accumulated)} rows saved")

        if accumulated.empty:
            logger.error("[ShareholdingEngine] No data fetched across any window")
            return False

        # Update company_fundamentals_master.csv with latest values
        self._update_fundamentals(accumulated)

        # G-A-03: write recovery queue
        if recovery:
            self._append_recovery(recovery)
            logger.warning(f"[ShareholdingEngine] {len(recovery)} symbols in recovery queue")

        logger.info(f"[ShareholdingEngine] Complete: {windows_done} windows, {len(accumulated)} rows, {accumulated['symbol'].nunique()} symbols")
        return True

    def _fetch_master(self, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
        from nselib.libutil import nse_urlfetch
        import json
        url = f"{SHP_API}?index=equities&from_date={from_date}&to_date={to_date}"
        for attempt in range(cfg.MAX_RETRIES):
            try:
                resp = nse_urlfetch(url, origin_url=SHP_ORIGIN)
                if resp.status_code != 200:
                    raise ValueError(f"HTTP {resp.status_code}")
                data = json.loads(resp.text)
                if not data:
                    return None
                df = pd.DataFrame(data)
                df = df.rename(columns={
                    "pr_and_prgrp": "promoter_master_pct",
                    "public_val":   "public_master_pct",
                })
                df["promoter_master_pct"] = pd.to_numeric(df["promoter_master_pct"], errors="coerce")
                df["public_master_pct"]   = pd.to_numeric(df["public_master_pct"],   errors="coerce")
                time.sleep(cfg.API_DELAY)
                return df
            except Exception as e:
                wait = cfg.RETRY_DELAY * (2 ** attempt)
                logger.warning(f"[ShareholdingEngine] Master fetch attempt {attempt+1} failed: {e}. Retrying in {wait}s")
                time.sleep(wait)
        return None

    def _parse_xbrl_batch(self, master: pd.DataFrame, window_label: str) -> list:
        from nselib.libutil import nse_urlfetch

        def _parse_one(row: dict) -> dict:
            symbol       = row["symbol"]
            xbrl_url     = row.get("xbrl", "")
            quarter_end  = row.get("date", "")
            submission   = row.get("submissionDate", "")
            promoter_pct = row.get("promoter_master_pct")

            base = {
                "symbol":           symbol,
                "quarter_end_date": quarter_end,
                "submission_date":  submission,
                "window_label":     window_label,
                "promoter_pct":     promoter_pct,
                "fii_pct":          None,
                "dii_pct":          None,
                "public_pct":       row.get("public_master_pct"),
                "source":           "nse_xbrl",
            }

            if _is_null_xbrl(xbrl_url):
                base["source"] = "master_only"
                return base

            for attempt in range(cfg.MAX_RETRIES):
                try:
                    time.sleep(cfg.API_DELAY * 0.4)
                    resp = nse_urlfetch(xbrl_url, origin_url=SHP_ORIGIN)
                    if resp.status_code != 200:
                        raise ValueError(f"HTTP {resp.status_code}")
                    root    = ET.fromstring(resp.text.encode())
                    parsed  = {}
                    for elem in root.iter():
                        if elem.tag.endswith(_SHP_PCT_TAG):
                            ctx   = elem.get("contextRef", "")
                            field = _XBRL_CONTEXTS.get(ctx)
                            if field and elem.text:
                                try:
                                    parsed[field] = float(elem.text.strip())
                                except ValueError:
                                    pass
                    base["fii_pct"]    = parsed.get("fii_pct")
                    base["dii_pct"]    = parsed.get("dii_pct")
                    base["public_pct"] = parsed.get("public_pct") or base["public_pct"]
                    if parsed.get("promoter_pct"):
                        base["promoter_pct"] = parsed["promoter_pct"]
                    return base
                except Exception as e:
                    wait = cfg.RETRY_DELAY * (2 ** attempt)
                    logger.debug(f"[ShareholdingEngine] XBRL {symbol} attempt {attempt+1}: {e}")
                    time.sleep(wait)
            return base

        records  = master.to_dict("records")
        n        = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(records)))
        results  = [None] * len(records)
        with ThreadPoolExecutor(max_workers=n) as ex:
            futures = {ex.submit(_parse_one, r): i for i, r in enumerate(records)}
            for fut in progress(as_completed(futures), total=len(futures), desc=f"XBRL {window_label}"):
                results[futures[fut]] = fut.result()
        return results

    def _validate_window(self, df: pd.DataFrame, label: str) -> Optional[pd.DataFrame]:
        """Data validation per window. Returns cleaned DataFrame or None if fatally invalid."""
        # G-D-03: no empty
        if df.empty:
            logger.error(f"[ShareholdingEngine] {label}: empty DataFrame — skipping")
            return None

        # Schema check: required columns
        required = {"symbol", "quarter_end_date", "window_label", "promoter_pct", "fii_pct", "dii_pct"}
        missing_cols = required - set(df.columns)
        if missing_cols:
            logger.error(f"[ShareholdingEngine] {label}: missing columns {missing_cols} — skipping")
            return None

        # Coverage check
        total = len(df)
        fii_filled = df["fii_pct"].notna().sum()
        fii_pct    = fii_filled / total * 100
        logger.info(f"[ShareholdingEngine] {label}: {total} symbols, FII coverage {fii_pct:.1f}%")
        if total < MIN_SYMBOLS_PER_WINDOW:
            logger.warning(f"[ShareholdingEngine] {label}: only {total} symbols — skipping")
            return None

        # Sanity check: promoter + public should sum to ~100 for rows with both
        both = df.dropna(subset=["promoter_pct", "public_pct"])
        if not both.empty:
            total_sum = (both["promoter_pct"] + both["public_pct"])
            bad = ((total_sum < 95) | (total_sum > 105)).sum()
            if bad > 0:
                logger.warning(f"[ShareholdingEngine] {label}: {bad} rows where promoter+public != 100%")

        # G-I-04: no fillna(0) on financial ratios — keep NaN
        return df

    def _fetch_screener_batch(self, symbols: list) -> list:
        import re
        results = []
        for symbol in symbols:
            try:
                time.sleep(1.5)
                for url in [
                    f"https://www.screener.in/company/{symbol}/consolidated/",
                    f"https://www.screener.in/company/{symbol}/",
                ]:
                    resp = requests.get(url, headers=_SCRN_HEADERS, timeout=15)
                    if resp.status_code == 200:
                        break
                if resp.status_code != 200:
                    results.append({"symbol": symbol})
                    continue

                text = resp.text
                row  = {"symbol": symbol}
                for cat_key, tag in [
                    ("promoter_pct", "promoters"),
                    ("fii_pct",      "foreign_institutions"),
                    ("dii_pct",      "domestic_institutions"),
                ]:
                    m = re.search(rf'plausible-event-classification={tag}', text)
                    if m:
                        tr_start = text.rfind("<tr", 0, m.start())
                        tr_end   = text.find("</tr>", m.end()) + 5
                        tds = re.findall(r'<td[^>]*>([\d.]+%)</td>', text[tr_start:tr_end])
                        if tds:
                            row[cat_key] = float(tds[-1].replace("%", ""))
                row["source"] = "screener"
                results.append(row)
            except Exception as e:
                logger.warning(f"[ShareholdingEngine] Screener failed for {symbol}: {e}")
                results.append({"symbol": symbol})
        return results

    def _update_fundamentals(self, shp: pd.DataFrame):
        if not FUNDAMENTALS_CSV.exists():
            logger.warning("[ShareholdingEngine] company_fundamentals_master.csv not found — skipping update")
            return
        cfm = pd.read_csv(FUNDAMENTALS_CSV)
        latest = (
            shp.sort_values("quarter_end_date")
               .drop_duplicates("symbol", keep="last")
               [["symbol", "promoter_pct", "fii_pct", "dii_pct"]]
        )
        cfm = cfm.drop(columns=["fii_holding_pct", "dii_holding_pct", "promoter_holding_pct"], errors="ignore")
        cfm = cfm.merge(
            latest.rename(columns={
                "promoter_pct": "promoter_holding_pct",
                "fii_pct":      "fii_holding_pct",
                "dii_pct":      "dii_holding_pct",
            }),
            on="symbol", how="left",
        )
        self._save_csv(cfm, FUNDAMENTALS_CSV)
        n_filled = cfm["fii_holding_pct"].notna().sum()
        logger.info(f"[ShareholdingEngine] Fundamentals updated: {n_filled}/{len(cfm)} symbols have FII %")

    def _save_csv(self, df: pd.DataFrame, path: Path):
        if df.empty:
            logger.error(f"[ShareholdingEngine] Refusing to write empty DataFrame to {path}")
            return
        tmp = path.with_suffix(".tmp.csv")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info(f"[ShareholdingEngine] Saved {len(df)} rows -> {path}")

    def _append_recovery(self, rows: list):
        df_new = pd.DataFrame(rows)
        df_new["engine"]    = "shareholding_15c"
        df_new["timestamp"] = pd.Timestamp.now().isoformat()
        if RECOVERY_QUEUE.exists():
            existing = pd.read_csv(RECOVERY_QUEUE)
            df_new = pd.concat([existing, df_new], ignore_index=True)
        self._save_csv(df_new, RECOVERY_QUEUE)


def validate_report(path: Path = SHP_CSV):
    """Print a data quality report for the existing quarterly_shp.csv."""
    if not path.exists():
        print("quarterly_shp.csv not found")
        return
    df = pd.read_csv(path)
    print(f"=== Shareholding Data Validation Report ===")
    print(f"Total rows   : {len(df):,}")
    print(f"Symbols      : {df['symbol'].nunique():,}")
    print(f"Windows      : {sorted(df['window_label'].unique())}")
    print()
    by_window = df.groupby("window_label").agg(
        symbols=("symbol", "nunique"),
        fii_filled=("fii_pct",      lambda x: x.notna().sum()),
        dii_filled=("dii_pct",      lambda x: x.notna().sum()),
        promo_filled=("promoter_pct", lambda x: x.notna().sum()),
    )
    by_window["fii_%"] = (by_window["fii_filled"] / by_window["symbols"] * 100).round(1)
    print(by_window.to_string())
    print()
    # Sanity: promoter+public sum
    both = df.dropna(subset=["promoter_pct", "public_pct"])
    if not both.empty:
        total_sum = both["promoter_pct"] + both["public_pct"]
        bad = ((total_sum < 95) | (total_sum > 105)).sum()
        print(f"Rows with promoter+public outside [95,105]: {bad} ({bad/len(both)*100:.1f}%)")
    print()
    # Source breakdown
    print("Source breakdown:")
    print(df["source"].value_counts().to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shareholding Engine -- Phase 15C")
    parser.add_argument("--windows",    type=int, default=1, help="Fetch N most recent windows (default: 1)")
    parser.add_argument("--backfill",      action="store_true", help="Fetch all historical windows from FY2008 to present (incremental)")
    parser.add_argument("--from-quarter",  type=str, default=None, metavar="LABEL",
                        help="With --backfill: start from this quarter label, e.g. Q1FY13")
    parser.add_argument("--validate",      action="store_true", help="Print data quality report for existing data")
    parser.add_argument("--no-screener",   action="store_true", help="Disable Screener.in fallback")
    args = parser.parse_args()

    if args.validate:
        validate_report()
    else:
        engine = ShareholdingEngine(
            windows=args.windows,
            backfill=args.backfill,
            use_screener_fallback=not args.no_screener,
            from_quarter=args.from_quarter,
        )
        ok = engine.run()

        if ok and SHP_CSV.exists():
            df = pd.read_csv(SHP_CSV)
            print(f"Shareholding data: {len(df):,} rows, {df['symbol'].nunique():,} symbols")
            print(f"Windows: {sorted(df['window_label'].unique())}")
            fii_cov = df['fii_pct'].notna().sum()
            print(f"FII coverage: {fii_cov}/{len(df)} ({fii_cov/len(df)*100:.1f}%)")
            print("\nSample (well-known stocks, latest window):")
            latest_df = df.sort_values("quarter_end_date").drop_duplicates("symbol", keep="last")
            for sym in ['TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'WIPRO', '20MICRONS']:
                row = latest_df[latest_df['symbol'] == sym]
                if not row.empty:
                    r = row.iloc[0]
                    print(f"  {sym}: promoter={r['promoter_pct']}, FII={r['fii_pct']}, DII={r['dii_pct']} ({r['window_label']})")
