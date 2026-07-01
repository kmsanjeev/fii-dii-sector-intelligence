"""
Shareholding Engine -- Phase 15C
Fetches quarterly shareholding patterns (promoter/FII/DII) from NSE XBRL archive.

Primary source:
  NSE API: /api/corporate-share-holdings-master  (discovered from page JS: activeApiName)
  NSE XBRL archive: nsearchives.nseindia.com/corporate/xbrl/SHP_*.xml

XBRL schema variants handled:
  V1 (2022+ large-caps): context suffix 'I'        e.g. InstitutionsDomesticI
  V2 (2024+ format):     context suffix '_ContextI'  e.g. InstitutionsDomestic_ContextI

Fallback:
  Screener.in HTML parsing (per-symbol, only for XBRL failures)

Outputs:
  data/NSE/shareholding/quarterly_shp.csv  -- raw per-symbol per-quarter
  data/NSE/equity_master/company_fundamentals_master.csv -- fii/dii/promoter cols updated

Guardrails enforced:
  G-D-02: atomic writes  G-D-03: no empty DF  G-I-04: no fillna(0)
  G-A-01: rate limiting  G-A-02: retry+backoff  G-A-03: recovery queue
  G-S-01: EQ series      G-S-04: universe size check
"""

import argparse
import math
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

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

SHP_API = "https://www.nseindia.com/api/corporate-share-holdings-master"
SHP_ORIGIN = "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern"

# Quarter-end date windows, most recent first
FILING_WINDOWS = [
    ("01-04-2025", "30-06-2025", "Q1FY26"),
    ("01-01-2025", "31-03-2025", "Q4FY25"),
    ("01-10-2024", "31-12-2024", "Q3FY25"),
    ("01-07-2024", "30-09-2024", "Q2FY25"),
]

# Both XBRL schema variants (V1 = 'I' suffix, V2 = '_ContextI' suffix)
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


class ShareholdingEngine:
    def __init__(self, windows: int = 1, use_screener_fallback: bool = True):
        self.windows = windows
        self.use_screener_fallback = use_screener_fallback
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

        # Load existing SHP to know which windows are already done
        existing = pd.DataFrame()
        if SHP_CSV.exists():
            existing = pd.read_csv(SHP_CSV)
        done_labels = set(existing["window_label"].unique()) if not existing.empty else set()
        logger.info(f"[ShareholdingEngine] Already done windows: {done_labels}")

        all_rows = [] if existing.empty else [existing]
        recovery = []
        windows_fetched = 0

        for from_date, to_date, label in FILING_WINDOWS:
            if windows_fetched >= self.windows:
                break
            if label in done_labels:
                logger.info(f"[ShareholdingEngine] Skipping {label} (already fetched)")
                continue

            logger.info(f"[ShareholdingEngine] Fetching master for {label} ({from_date} to {to_date})")
            master = self._fetch_master(from_date, to_date)
            if master is None or master.empty:
                logger.warning(f"[ShareholdingEngine] No master data for {label}")
                continue

            # Filter to EQ universe
            master = master[master["symbol"].isin(eq_symbols)].copy()
            logger.info(f"[ShareholdingEngine] {label}: {len(master)} EQ filings")

            # Parse XBRL for FII/DII
            rows = self._parse_xbrl_batch(master, label)

            # Screener fallback for XBRL failures
            if self.use_screener_fallback:
                parsed_symbols = {r["symbol"] for r in rows if r.get("fii_pct") is not None}
                missing = [r for r in rows if r["symbol"] not in parsed_symbols or r.get("fii_pct") is None]
                if missing:
                    logger.info(f"[ShareholdingEngine] Screener fallback for {len(missing)} symbols")
                    fallback = self._fetch_screener_batch([r["symbol"] for r in missing])
                    sym_to_fallback = {f["symbol"]: f for f in fallback}
                    for r in rows:
                        if r.get("fii_pct") is None and r["symbol"] in sym_to_fallback:
                            fb = sym_to_fallback[r["symbol"]]
                            r["fii_pct"] = fb.get("fii_pct")
                            r["dii_pct"] = fb.get("dii_pct")
                            r["promoter_pct"] = fb.get("promoter_pct") or r.get("promoter_pct")
                            r["source"] = "screener"
                            # Track XBRL failures
                            if fb.get("fii_pct") is None:
                                recovery.append({"symbol": r["symbol"], "window_label": label, "reason": "xbrl_and_screener_failed"})

            all_rows.append(pd.DataFrame(rows))
            windows_fetched += 1
            logger.info(f"[ShareholdingEngine] {label}: {len(rows)} rows parsed")

        if not all_rows:
            logger.error("[ShareholdingEngine] No data fetched")
            return False

        combined = pd.concat(all_rows, ignore_index=True)
        # G-D-05 equivalent: deduplicate by symbol + window_label (keep latest)
        combined = combined.drop_duplicates(subset=["symbol", "window_label"], keep="last")

        if combined.empty:
            logger.error("[ShareholdingEngine] Combined DataFrame is empty")
            return False

        # G-D-02: atomic write
        self._save_csv(combined, SHP_CSV)

        # Update company_fundamentals_master.csv with latest holding values
        self._update_fundamentals(combined)

        # G-A-03: write recovery queue
        if recovery:
            self._append_recovery(recovery)
            logger.warning(f"[ShareholdingEngine] {len(recovery)} symbols in recovery queue")

        logger.info(f"[ShareholdingEngine] Complete: {len(combined)} rows, {combined['symbol'].nunique()} symbols")
        return True

    def _fetch_master(self, from_date: str, to_date: str) -> Optional[pd.DataFrame]:
        from nselib.libutil import nse_urlfetch
        url = f"{SHP_API}?index=equities&from_date={from_date}&to_date={to_date}"
        for attempt in range(cfg.MAX_RETRIES):
            try:
                resp = nse_urlfetch(url, origin_url=SHP_ORIGIN)
                if resp.status_code != 200:
                    raise ValueError(f"HTTP {resp.status_code}")
                import json
                data = json.loads(resp.text)
                if not data:
                    return None
                df = pd.DataFrame(data)
                df = df.rename(columns={"pr_and_prgrp": "promoter_master_pct", "public_val": "public_master_pct"})
                df["promoter_master_pct"] = pd.to_numeric(df["promoter_master_pct"], errors="coerce")
                df["public_master_pct"]   = pd.to_numeric(df["public_master_pct"],   errors="coerce")
                return df
            except Exception as e:
                wait = cfg.RETRY_DELAY * (2 ** attempt)
                logger.warning(f"[ShareholdingEngine] Master fetch attempt {attempt+1} failed: {e}. Wait {wait}s")
                time.sleep(wait)
        return None

    def _parse_xbrl_batch(self, master: pd.DataFrame, window_label: str) -> list:
        from nselib.libutil import nse_urlfetch

        def _parse_one(row: dict) -> dict:
            symbol = row["symbol"]
            xbrl_url = row.get("xbrl", "")
            quarter_end = row.get("date", "")
            submission = row.get("submissionDate", "")
            promoter_pct = row.get("promoter_master_pct")

            base = {
                "symbol": symbol,
                "quarter_end_date": quarter_end,
                "submission_date": submission,
                "window_label": window_label,
                "promoter_pct": promoter_pct,
                "fii_pct": None,
                "dii_pct": None,
                "public_pct": row.get("public_master_pct"),
                "source": "nse_xbrl",
            }

            if not xbrl_url or str(xbrl_url).endswith("/xbrl/-"):
                base["source"] = "master_only"
                return base

            for attempt in range(cfg.MAX_RETRIES):
                try:
                    time.sleep(cfg.API_DELAY * 0.5)
                    resp = nse_urlfetch(xbrl_url, origin_url=SHP_ORIGIN)
                    if resp.status_code != 200:
                        raise ValueError(f"HTTP {resp.status_code}")
                    root = ET.fromstring(resp.text.encode())
                    parsed = {}
                    for elem in root.iter():
                        if elem.tag.endswith(_SHP_PCT_TAG):
                            ctx = elem.get("contextRef", "")
                            field = _XBRL_CONTEXTS.get(ctx)
                            if field and elem.text:
                                try:
                                    parsed[field] = float(elem.text.strip())
                                except ValueError:
                                    pass
                    base["fii_pct"]     = parsed.get("fii_pct")
                    base["dii_pct"]     = parsed.get("dii_pct")
                    base["public_pct"]  = parsed.get("public_pct") or base["public_pct"]
                    if parsed.get("promoter_pct"):
                        base["promoter_pct"] = parsed["promoter_pct"]
                    return base
                except Exception as e:
                    wait = cfg.RETRY_DELAY * (2 ** attempt)
                    logger.debug(f"[ShareholdingEngine] XBRL {symbol} attempt {attempt+1}: {e}")
                    time.sleep(wait)
            return base

        records = master.to_dict("records")
        n = min(cfg.MAX_CONCURRENCY, max(cfg.MIN_CONCURRENCY, len(records)))
        results = [None] * len(records)
        with ThreadPoolExecutor(max_workers=n) as ex:
            futures = {ex.submit(_parse_one, r): i for i, r in enumerate(records)}
            for fut in progress(as_completed(futures), total=len(futures), desc=f"XBRL {window_label}"):
                results[futures[fut]] = fut.result()
        return results

    def _fetch_screener_batch(self, symbols: list) -> list:
        import re
        results = []
        for symbol in symbols:
            try:
                time.sleep(1.5)
                url = f"https://www.screener.in/company/{symbol}/consolidated/"
                resp = requests.get(url, headers=_SCRN_HEADERS, timeout=15)
                if resp.status_code != 200:
                    url2 = f"https://www.screener.in/company/{symbol}/"
                    resp = requests.get(url2, headers=_SCRN_HEADERS, timeout=15)
                if resp.status_code != 200:
                    results.append({"symbol": symbol})
                    continue
                text = resp.text
                row = {"symbol": symbol}
                for cat_key, tag in [
                    ("promoter_pct", "promoters"),
                    ("fii_pct",      "foreign_institutions"),
                    ("dii_pct",      "domestic_institutions"),
                ]:
                    match = re.search(rf'plausible-event-classification={tag}', text)
                    if match:
                        tr_start = text.rfind("<tr", 0, match.start())
                        tr_end   = text.find("</tr>", match.end()) + 5
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
        # Use latest window per symbol
        latest = (
            shp.sort_values("quarter_end_date")
               .drop_duplicates("symbol", keep="last")
               [["symbol", "promoter_pct", "fii_pct", "dii_pct"]]
        )
        cfm = cfm.drop(columns=["fii_holding_pct", "dii_holding_pct", "promoter_holding_pct"], errors="ignore")
        cfm = cfm.merge(
            latest.rename(columns={"promoter_pct": "promoter_holding_pct", "fii_pct": "fii_holding_pct", "dii_pct": "dii_holding_pct"}),
            on="symbol", how="left",
        )
        self._save_csv(cfm, FUNDAMENTALS_CSV)
        n_filled = cfm["fii_holding_pct"].notna().sum()
        logger.info(f"[ShareholdingEngine] Updated fundamentals: {n_filled}/{len(cfm)} symbols have FII %")

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
        df_new["engine"] = "shareholding_15c"
        df_new["timestamp"] = pd.Timestamp.now().isoformat()
        if RECOVERY_QUEUE.exists():
            existing = pd.read_csv(RECOVERY_QUEUE)
            df_new = pd.concat([existing, df_new], ignore_index=True)
        self._save_csv(df_new, RECOVERY_QUEUE)


def _isnan(v) -> bool:
    try:
        return math.isnan(float(v))
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Shareholding Engine -- Phase 15C")
    parser.add_argument("--windows", type=int, default=1, help="Number of quarterly windows to fetch (default: 1 = most recent)")
    parser.add_argument("--full", action="store_true", help="Fetch all 4 windows (~6000 rows)")
    parser.add_argument("--no-screener", action="store_true", help="Disable Screener.in fallback")
    args = parser.parse_args()

    n_windows = 4 if args.full else args.windows
    engine = ShareholdingEngine(windows=n_windows, use_screener_fallback=not args.no_screener)
    ok = engine.run()

    if ok and SHP_CSV.exists():
        df = pd.read_csv(SHP_CSV)
        print(f"Shareholding data: {len(df)} rows, {df['symbol'].nunique()} symbols")
        print(f"Windows: {sorted(df['window_label'].unique())}")
        fii_cov = df['fii_pct'].notna().sum()
        print(f"FII coverage: {fii_cov}/{len(df)} ({fii_cov/len(df)*100:.1f}%)")
        print("\nSample (well-known stocks):")
        for sym in ['TCS', 'RELIANCE', 'INFY', 'HDFCBANK', 'WIPRO']:
            row = df[df['symbol'] == sym]
            if not row.empty:
                r = row.iloc[-1]
                print(f"  {sym}: promoter={r['promoter_pct']}, FII={r['fii_pct']}, DII={r['dii_pct']}")
