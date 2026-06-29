"""
NSE Constituents Engine V1
Phase 4D — Download index constituent lists for 30 NSE indices

Source: nsearchives.nseindia.com/content/indices/ (open, no auth required)
Covers:  12 broad-market indices + 18 sector/theme/PSU indices
Output:  data/NSE/indices/<slug>_constituents.csv   (one per index)
         data/NSE/indices/index_membership.csv       (symbol → [indices])
         data/NSE/indices/reports/download_registry.csv

Guardrails: G-A-01 (rate limit 1 s), G-A-02 (3 retries), G-A-03 (recovery queue),
            G-D-02 (atomic writes), G-D-03 (no empty df), G-D-04 (schema validation)
"""

import shutil
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
import sys

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("nse_constituents_v1")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INDICES_DIR = cfg.INDICES_DIR
REPORTS_DIR = INDICES_DIR / "reports"
RECOVERY_QUEUE = REPORTS_DIR / "constituents_recovery_queue.csv"
DOWNLOAD_REGISTRY = REPORTS_DIR / "download_registry.csv"
MEMBERSHIP_FILE = INDICES_DIR / "index_membership.csv"

BASE_URL = "https://nsearchives.nseindia.com/content/indices/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# ---------------------------------------------------------------------------
# Index registry
# (index_name, filename, platform_sector_hint)
# platform_sector_hint: the platform sector that membership in this index implies
#                       None = broad/strategy index (no sector hint)
# ---------------------------------------------------------------------------
INDEX_REGISTRY = [
    # ---- Broad market ----
    ("NIFTY 50",             "ind_nifty50list.csv",                         None),
    ("NIFTY NEXT 50",        "ind_niftynext50list.csv",                     None),
    ("NIFTY 100",            "ind_nifty100list.csv",                        None),
    ("NIFTY 200",            "ind_nifty200list.csv",                        None),
    ("NIFTY 500",            "ind_nifty500list.csv",                        None),
    ("NIFTY MIDCAP 50",      "ind_niftymidcap50list.csv",                   None),
    ("NIFTY MIDCAP 100",     "ind_niftymidcap100list.csv",                  None),
    ("NIFTY MIDCAP 150",     "ind_niftymidcap150list.csv",                  None),
    ("NIFTY SMALLCAP 100",   "ind_niftysmallcap100list.csv",                None),
    ("NIFTY SMALLCAP 250",   "ind_niftysmallcap250list.csv",                None),
    ("NIFTY LARGEMIDCAP 250","ind_niftylargemidcap250list.csv",             None),
    ("NIFTY MIDSMALLCAP 400","ind_niftymidsmallcap400list.csv",             None),
    # ---- Sector indices ----
    ("NIFTY AUTO",                 "ind_niftyautolist.csv",                 "AUTO"),
    ("NIFTY PHARMA",               "ind_niftypharmalist.csv",               "PHARMA"),
    ("NIFTY IT",                   "ind_niftyitlist.csv",                   "IT"),
    ("NIFTY METAL",                "ind_niftymetallist.csv",                "METAL"),
    ("NIFTY FMCG",                 "ind_niftyfmcglist.csv",                 "FMCG"),
    ("NIFTY MEDIA",                "ind_niftymedialist.csv",                "MEDIA"),
    ("NIFTY REALTY",               "ind_niftyrealtylist.csv",               "REALTY"),
    ("NIFTY BANK",                 "ind_niftybanklist.csv",                 "BANKING"),
    ("NIFTY PSU BANK",             "ind_niftypsubanklist.csv",              "BANKING"),
    ("NIFTY HEALTHCARE INDEX",     "ind_niftyhealthcarelist.csv",           "HEALTHCARE"),
    ("NIFTY OIL & GAS",            "ind_niftyoilgaslist.csv",               "ENERGY"),
    ("NIFTY ENERGY",               "ind_niftyenergylist.csv",               "ENERGY"),
    ("NIFTY FINANCIAL SERVICES 25/50", "ind_niftyfinancialservices25-50list.csv", "FINANCIAL_SERVICES"),
    ("NIFTY CONSUMER DURABLES",    "ind_niftyconsumerdurableslist.csv",     "FMCG"),
    # ---- Strategy / PSU / Theme ----
    ("NIFTY COMMODITIES",          "ind_niftycommoditieslist.csv",          None),
    ("NIFTY MNC",                  "ind_niftymnclist.csv",                  None),
    ("NIFTY CPSE",                 "ind_niftycpselist.csv",                 None),
    ("NIFTY PSE",                  "ind_niftypselist.csv",                  None),
]

# Required columns in every constituent CSV from nsearchives
REQUIRED_COLS = {"Symbol", "Company Name"}


def _index_slug(name: str) -> str:
    """NIFTY IT → nifty_it, NIFTY OIL & GAS → nifty_oil_gas"""
    return name.lower().replace(" & ", "_").replace(" ", "_").replace("/", "_")


class NSEConstituentsEngineV1:
    """
    Phase 4D — Download NSE index constituent lists from nsearchives.nseindia.com.

    Produces one CSV per index plus a symbol-level index membership master file
    that future engines can use for sector confirmation and cap-category inference.
    """

    def __init__(self):
        INDICES_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.session = self._create_session()
        self.registry_rows = []
        self.failed = []

    def run(self) -> bool:
        logger.info("[NSEConstituentsV1] Starting Phase 4D — %d indices", len(INDEX_REGISTRY))
        try:
            all_dfs = self._download_all()
            if not all_dfs:
                raise RuntimeError("All downloads failed — no constituent data retrieved")
            self._save_membership_master(all_dfs)
            self._save_registry()
            if self.failed:
                self._save_recovery_queue()
            self._print_summary(all_dfs)
            return True
        except Exception as exc:
            logger.error("[NSEConstituentsV1] Failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Session
    # ------------------------------------------------------------------
    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update(HEADERS)
        return s

    # ------------------------------------------------------------------
    # Download all indices
    # ------------------------------------------------------------------
    def _download_all(self) -> dict:
        """Returns {slug: DataFrame} for successful downloads."""
        all_dfs = {}
        total = len(INDEX_REGISTRY)
        for i, (name, filename, sector_hint) in enumerate(INDEX_REGISTRY, 1):
            slug = _index_slug(name)
            logger.info("[4D] %d/%d  %s", i, total, name)
            df = self._fetch_with_retry(name, filename)
            if df is not None:
                df = self._normalize(df, name, slug, sector_hint)
                self._save_constituent_csv(df, slug, name)
                all_dfs[slug] = df
                self.registry_rows.append({
                    "index_name": name,
                    "index_slug": slug,
                    "filename": filename,
                    "status": "SUCCESS",
                    "constituent_count": len(df),
                    "sector_hint": sector_hint or "",
                    "downloaded_date": datetime.now().strftime("%Y-%m-%d"),
                    "error": "",
                })
                logger.info("[4D]   OK — %d stocks", len(df))
            else:
                self.failed.append(name)
                self.registry_rows.append({
                    "index_name": name,
                    "index_slug": slug,
                    "filename": filename,
                    "status": "FAILED",
                    "constituent_count": 0,
                    "sector_hint": sector_hint or "",
                    "downloaded_date": datetime.now().strftime("%Y-%m-%d"),
                    "error": "download_failed",
                })
                logger.warning("[4D]   FAILED — %s", filename)
            # G-A-01: 1 second rate limit
            time.sleep(cfg.API_DELAY)
        return all_dfs

    # ------------------------------------------------------------------
    # Fetch with retry (G-A-02)
    # ------------------------------------------------------------------
    def _fetch_with_retry(self, name: str, filename: str) -> "pd.DataFrame | None":
        url = BASE_URL + filename
        delay = cfg.RETRY_DELAY
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            try:
                r = self.session.get(url, timeout=cfg.API_TIMEOUT)
                if r.status_code == 200:
                    df = pd.read_csv(BytesIO(r.content))
                    df.columns = [c.strip() for c in df.columns]
                    missing = REQUIRED_COLS - set(df.columns)
                    if missing:
                        logger.warning("[4D] %s — missing columns %s", name, missing)
                        return None
                    return df
                else:
                    logger.warning("[4D] %s — HTTP %d (attempt %d)", name, r.status_code, attempt)
            except Exception as exc:
                logger.warning("[4D] %s — error attempt %d: %s", name, attempt, exc)
            if attempt < cfg.MAX_RETRIES:
                time.sleep(delay)
                delay *= 2  # exponential backoff
        return None

    # ------------------------------------------------------------------
    # Normalize to canonical schema
    # ------------------------------------------------------------------
    def _normalize(
        self,
        df: pd.DataFrame,
        name: str,
        slug: str,
        sector_hint: "str | None",
    ) -> pd.DataFrame:
        df = df.copy()
        # Rename to canonical columns
        rename = {
            "Symbol": "symbol",
            "Company Name": "company_name",
            "Industry": "industry_nse",
            "Series": "series",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        df["symbol"] = df["symbol"].str.strip().str.upper()
        df["company_name"] = df.get("company_name", pd.Series([""] * len(df))).str.strip()
        df["industry_nse"] = df.get("industry_nse", pd.Series([""] * len(df))).str.strip()
        # Filter EQ series only where series column exists (G-S-01)
        if "series" in df.columns:
            df = df[df["series"].str.strip().str.upper() == "EQ"].copy()
        # Add metadata columns
        df["index_name"] = name
        df["index_slug"] = slug
        df["sector_hint"] = sector_hint or ""
        df["downloaded_date"] = datetime.now().strftime("%Y-%m-%d")
        # Keep canonical columns
        keep = ["symbol", "company_name", "industry_nse", "index_name", "index_slug",
                "sector_hint", "downloaded_date"]
        df = df[[c for c in keep if c in df.columns]]
        # G-D-03: reject empty
        if df.empty:
            raise ValueError(f"G-D-03: zero EQ rows for {name}")
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Save constituent CSV (atomic, G-D-02)
    # ------------------------------------------------------------------
    def _save_constituent_csv(self, df: pd.DataFrame, slug: str, name: str):
        out_path = INDICES_DIR / f"{slug}_constituents.csv"
        tmp = out_path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(out_path))
        logger.debug("[4D] Saved %s (%d rows)", out_path.name, len(df))

    # ------------------------------------------------------------------
    # Build symbol-level index membership master
    # ------------------------------------------------------------------
    def _save_membership_master(self, all_dfs: dict):
        """Produces: symbol → comma-separated index_names, index_slugs, sector_hints"""
        frames = list(all_dfs.values())
        combined = pd.concat(frames, ignore_index=True)
        membership = (
            combined.groupby("symbol")
            .agg(
                index_names=("index_name", lambda x: "|".join(sorted(set(x)))),
                index_slugs=("index_slug", lambda x: "|".join(sorted(set(x)))),
                sector_hints=("sector_hint", lambda x: "|".join(sorted(set(s for s in x if s)))),
                index_count=("index_name", "count"),
            )
            .reset_index()
        )
        # Infer dominant sector hint (most frequent non-empty)
        def dominant_hint(hints_str):
            hints = [h for h in hints_str.split("|") if h]
            if not hints:
                return ""
            from collections import Counter
            return Counter(hints).most_common(1)[0][0]

        membership["dominant_sector_hint"] = membership["sector_hints"].apply(dominant_hint)
        membership["last_updated"] = datetime.now().strftime("%Y-%m-%d")

        if membership.empty:
            raise ValueError("G-D-03: index_membership.csv would be empty")

        tmp = MEMBERSHIP_FILE.with_suffix(".tmp")
        membership.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(MEMBERSHIP_FILE))
        logger.info("[4D] index_membership.csv saved — %d symbols across %d indices",
                    len(membership), len(all_dfs))

    # ------------------------------------------------------------------
    # Save download registry
    # ------------------------------------------------------------------
    def _save_registry(self):
        df = pd.DataFrame(self.registry_rows)
        tmp = DOWNLOAD_REGISTRY.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(DOWNLOAD_REGISTRY))
        logger.info("[4D] download_registry.csv saved")

    # ------------------------------------------------------------------
    # Save recovery queue (G-A-03)
    # ------------------------------------------------------------------
    def _save_recovery_queue(self):
        df = pd.DataFrame([{
            "index_name": name,
            "source": BASE_URL,
            "failed_date": datetime.now().strftime("%Y-%m-%d"),
        } for name in self.failed])
        tmp = RECOVERY_QUEUE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))
        logger.warning("[4D] Recovery queue: %d failed indices → %s", len(self.failed), RECOVERY_QUEUE)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _print_summary(self, all_dfs: dict):
        success = len(all_dfs)
        failed = len(self.failed)
        total_stocks = sum(len(df) for df in all_dfs.values())

        print()
        print("=" * 70)
        print("NSE CONSTITUENTS ENGINE V1 — PHASE 4D COMPLETE")
        print("=" * 70)
        print(f"Indices attempted : {len(INDEX_REGISTRY)}")
        print(f"Downloaded        : {success}")
        print(f"Failed            : {failed}")
        print(f"Total constituent : {total_stocks:,} rows (across all indices)")
        print()
        if self.failed:
            print(f"Failed indices    : {', '.join(self.failed)}")
            print()
        print("Downloaded indices:")
        for row in self.registry_rows:
            if row["status"] == "SUCCESS":
                hint = f" [{row['sector_hint']}]" if row["sector_hint"] else ""
                print(f"  {row['index_name']:<40} {row['constituent_count']:>4} stocks{hint}")
        print("=" * 70)


if __name__ == "__main__":
    engine = NSEConstituentsEngineV1()
    engine.run()
