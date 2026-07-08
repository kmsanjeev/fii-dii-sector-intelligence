"""
Phase FPI -- Fortnightly FPI Sector Data Engine
Fetches NSDL/CDSL/SEBI sector-wise FPI investment reports (fortnightly, Apr 2012-present)
and builds an incremental time-series for sector rotation analysis.

Source routing (tries in order until success):
  NSDL static files : works for 2018-2019 and recent months (2025-06 onwards)
  CDSL              : works for 2013 - Jun 2023
  SEBI              : works for Apr 2012 - May 2014 (original publisher)

Column formula (unified across all 3 sources):
  N = (total_cols - 2) // 4   (sub-columns per column group)
  auc_end_equity_col = 2 + 3*N  (AUC at period-end, Equity, INR Crore)
  net1_equity_col    = 2 + N    (Net investment period 1, Equity, INR Crore)
  net2_equity_col    = 2 + 2*N  (Net investment period 2, Equity, INR Crore)

Outputs:
  data/NSE/fpi/sector_fpi_fortnightly.csv
    Cols: date, sector_raw, sector_normalized, auc_equity_crore,
          net_inv_equity_crore, source, fortnight_label
"""

import re
import shutil
import time
from calendar import monthrange
from datetime import date
from pathlib import Path
import sys

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("sector_fpi_engine")

# ── Paths ────────────────────────────────────────────────────────────────────
OUTPUT_FILE   = cfg.FPI_DIR / "sector_fpi_fortnightly.csv"
MAPPING_FILE  = cfg.REFERENCE_DIR / "sector_nsdl_mapping.csv"
RECOVERY_FILE = cfg.FPI_DIR / "fpi_recovery_queue.csv"

# ── Constants ─────────────────────────────────────────────────────────────────
START_DATE  = date(2012, 4, 15)
FETCH_DELAY = 1.5  # seconds between HTTP requests

MONTHS_FULL = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
MONTHS_ABBR = [
    "", "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec"
]

_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-IN,en;q=0.9",
}

# Rows whose sector name exactly matches these are skipped (aggregate rows)
_SKIP_SECTOR_EXACT = {"total", "grand total", "sovereign"}

# ── Date Generation ───────────────────────────────────────────────────────────

def generate_fortnightly_dates(start: date, end: date) -> list:
    """Return sorted list of every 15th and month-end date between start and end."""
    out = []
    y, m = start.year, start.month
    while True:
        d15  = date(y, m, 15)
        last = date(y, m, monthrange(y, m)[1])
        for d in (d15, last):
            if start <= d <= end:
                out.append(d)
        if (y, m) == (end.year, end.month):
            break
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return sorted(out)


# ── URL Builders ──────────────────────────────────────────────────────────────

def _nsdl_urls(d: date) -> list:
    """NSDL static HTML: two variants (Invest / Inest typo for pre-2018)."""
    mon  = MONTHS_FULL[d.month]
    dd   = f"{d.day:02d}"
    yyyy = d.year
    base = (
        "https://www.fpi.nsdl.co.in/web/StaticReports/"
        "Fortnightly_Sector_wise_FII_Investment_Data/"
    )
    return [
        f"{base}FIIInvestSector_{mon}{dd}{yyyy}.html",
        f"{base}FIIInestSector_{mon}{dd}{yyyy}.html",
    ]


def _cdsl_url(d: date) -> str:
    """CDSL fortnightly sector page."""
    mon  = MONTHS_FULL[d.month]
    dd   = f"{d.day:02d}"
    yyyy = d.year
    return (
        "https://www.cdslindia.com/publications/FII/"
        f"FortnightlySecWisePages/{mon}%20{dd},%20{yyyy}.htm"
    )


def _sebi_url(d: date) -> str:
    """SEBI fortnightly sector page (Apr 2012 - May 2014 only)."""
    dd  = f"{d.day:02d}"
    mon = MONTHS_ABBR[d.month]
    return (
        "https://www.sebi.gov.in/statistics/fpi-investment/"
        f"fortnightly-sector-wise/{dd}-{mon}-{d.year}.html"
    )


# ── HTTP Fetch ────────────────────────────────────────────────────────────────

def _fetch(url: str, referer: str) -> str | None:
    """GET url; return decoded HTML or None if blocked/failed."""
    hdrs = {**_BROWSER_HEADERS, "Referer": referer}
    try:
        resp = requests.get(url, headers=hdrs, timeout=25)
        if resp.status_code != 200:
            return None
        content = resp.content
        # Detect UTF-16 LE (some CDSL files saved in this encoding)
        if content[:2] in (b"\xff\xfe", b"\xfe\xff") or (
            len(content) > 100 and b"\x00" in content[:100]
        ):
            html = content.decode("utf-16-le", errors="replace")
        else:
            html = content.decode("utf-8", errors="replace")
        # WAF rejection body is <=300 bytes of boilerplate
        return html if len(html) > 5_000 else None
    except Exception as exc:
        logger.debug("Fetch failed %s: %s", url, exc)
        return None


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_number(val: str) -> float | None:
    """'5,11,510' -> 511510.0 ; '(9,044)' -> -9044.0 ; '-' -> None."""
    v = str(val).strip().replace(",", "").replace("(", "-").replace(")", "")
    if v in ("", "-", "--", "NA", "N/A"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _clean_sector(name: str) -> str:
    """Strip whitespace, non-breaking spaces, trailing footnote digits."""
    cleaned = (
        name.replace("\xa0", " ")
            .replace("\r", "")
            .replace("\n", " ")
            .strip()
    )
    # Strip trailing footnote digits: 'Other Financial Services1' -> 'Other Financial Services'
    cleaned = re.sub(r"\d+$", "", cleaned).strip()
    return cleaned


def parse_fpi_table(html: str) -> list:
    """
    Unified parser for NSDL/CDSL/SEBI sector FPI tables.

    Row filter: keep only rows whose first cell is a pure integer (skip sub-sector
    rows like '2a', '2b' and header/footer rows).

    Column formula: N = (total_cols - 2) // 4
      auc_end_equity = col[2 + 3*N]   -> AUC at period end, Equity, INR Crore
      net1_equity    = col[2 + N]     -> Net investment, first fortnight, Equity, INR Crore
      net2_equity    = col[2 + 2*N]   -> Net investment, second fortnight, Equity, INR Crore
    """
    soup = BeautifulSoup(html, "html.parser")

    # Find the main data table: largest by number of usable data rows
    tables = soup.find_all("table")
    main_table = None
    best_count = 0
    for t in tables:
        rows = t.find_all("tr")
        count = sum(
            1 for r in rows
            if r.find_all("td") and len(r.find_all("td")) >= 5
        )
        if count > best_count:
            best_count = count
            main_table = t

    if not main_table or best_count < 5:
        return []

    all_rows = main_table.find_all("tr")

    # Detect column count from first integer-numbered data row
    total_cols = 0
    for row in all_rows:
        cells = row.find_all("td")
        if len(cells) >= 10 and re.match(r"^\d+$", cells[0].get_text(strip=True)):
            total_cols = len(cells)
            break

    if total_cols < 10:
        return []

    N            = (total_cols - 2) // 4
    auc_end_col  = 2 + 3 * N
    net1_col     = 2 + N
    net2_col     = 2 + 2 * N

    results = []
    for row in all_rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        row_num = cells[0].get_text(strip=True)
        # Only pure-integer row numbers; skip sub-sectors (2a, 2b) and headers
        if not re.match(r"^\d+$", row_num):
            continue

        sector_name = _clean_sector(cells[1].get_text(strip=True))
        if not sector_name:
            continue
        # Skip aggregate/irrelevant rows
        if sector_name.lower() in _SKIP_SECTOR_EXACT:
            continue

        # AUC at period end (Equity, INR Crore)
        auc_val = None
        if auc_end_col < len(cells):
            auc_val = _parse_number(cells[auc_end_col].get_text(strip=True))

        # Skip company/footnote rows — sector rows always have a valid AUC value
        if auc_val is None:
            continue

        # Net investment = sum of both fortnights (INR Crore)
        net_val: float | None = None
        if net1_col < len(cells):
            v = _parse_number(cells[net1_col].get_text(strip=True))
            if v is not None:
                net_val = v
        if net2_col < len(cells):
            v = _parse_number(cells[net2_col].get_text(strip=True))
            if v is not None:
                net_val = (net_val or 0.0) + v

        results.append({
            "sector_raw": sector_name,
            "auc_equity_crore": auc_val,
            "net_inv_equity_crore": net_val,
        })

    return results


# ── Sector Normalization ──────────────────────────────────────────────────────

_mapping_cache: dict = {}


def _load_mapping() -> dict:
    global _mapping_cache
    if _mapping_cache:
        return _mapping_cache
    if not MAPPING_FILE.exists():
        logger.warning("sector_nsdl_mapping.csv not found at %s", MAPPING_FILE)
        return {}
    df = pd.read_csv(MAPPING_FILE)
    for _, row in df.iterrows():
        raw  = str(row.get("sector_raw", "")).strip().upper()
        norm = str(row.get("sector_normalized", "")).strip()
        if raw and norm:
            _mapping_cache[raw] = norm
    # Also normalize whitespace variants: collapse multiple spaces
    extras = {}
    for k, v in _mapping_cache.items():
        collapsed = re.sub(r"\s+", " ", k)
        if collapsed != k:
            extras[collapsed] = v
    _mapping_cache.update(extras)
    logger.info("Loaded %d sector mappings", len(_mapping_cache))
    return _mapping_cache


def normalize_sector(raw: str) -> str:
    mapping = _load_mapping()
    key = re.sub(r"\s+", " ", raw.strip().upper())
    return mapping.get(key, raw.strip())


# ── Main Engine ───────────────────────────────────────────────────────────────

class SectorFPIEngine:
    """
    Fetches NSDL/CDSL/SEBI fortnightly sector FPI reports and builds
    an incremental CSV time-series at data/NSE/fpi/sector_fpi_fortnightly.csv.
    """

    def __init__(self):
        cfg.FPI_DIR.mkdir(parents=True, exist_ok=True)
        self.existing_dates: set = set()
        self.recovery: list = []

    def run(self, full_rebuild: bool = False, since: str | None = None) -> bool:
        logger.info("[FPI] Starting sector FPI engine")
        print("[FPI] Sector FPI Engine -- fortnightly data 2012-present")

        existing = pd.DataFrame()
        if OUTPUT_FILE.exists() and not full_rebuild:
            existing = pd.read_csv(OUTPUT_FILE)
            self.existing_dates = set(existing["date"].astype(str).unique())
            logger.info("[FPI] Already have %d dates", len(self.existing_dates))
            print(f"[FPI] Existing: {len(self.existing_dates)} dates already downloaded")

        end_date   = date.today()
        all_dates  = generate_fortnightly_dates(START_DATE, end_date)

        # Optional: only fetch from a specific date onwards
        if since:
            since_date = date.fromisoformat(since)
            all_dates  = [d for d in all_dates if d >= since_date]

        pending = [d for d in all_dates if str(d) not in self.existing_dates]
        print(f"[FPI] Total fortnightly dates: {len(all_dates)} | Pending: {len(pending)}")

        if not pending:
            print("[FPI] Already up to date -- nothing to fetch")
            return True

        new_rows: list = []
        for i, d in enumerate(pending):
            rows, source = self._fetch_date(d)
            if rows:
                label = f"{MONTHS_FULL[d.month]} {d.day}, {d.year}"
                for r in rows:
                    r["date"]                = str(d)
                    r["sector_normalized"]   = normalize_sector(r["sector_raw"])
                    r["source"]              = source
                    r["fortnight_label"]     = label
                new_rows.extend(rows)
                print(f"  [{i+1:>4}/{len(pending)}] {d}  {source:<5}  {len(rows)} sectors")
            else:
                self.recovery.append(str(d))
                print(f"  [{i+1:>4}/{len(pending)}] {d}  FAIL  -- added to recovery queue")
            time.sleep(FETCH_DELAY)

        if not new_rows and existing.empty:
            logger.error("[FPI] No data fetched and no existing data -- nothing saved")
            return False

        if new_rows:
            new_df   = pd.DataFrame(new_rows)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["date", "sector_raw"])
            combined = combined.sort_values(["date", "sector_normalized"]).reset_index(drop=True)
            self._save_atomic(combined)
            print(f"\n[FPI] Saved {len(combined)} rows -> {OUTPUT_FILE.name}")
        else:
            print("\n[FPI] No new rows fetched (all failed or already current)")

        if self.recovery:
            self._save_recovery()
            print(f"[FPI] Recovery queue: {len(self.recovery)} dates failed")

        return True

    # ── Source Routing ─────────────────────────────────────────────────────────

    def _fetch_date(self, d: date) -> tuple:
        """Try NSDL -> CDSL -> SEBI; return (rows, source) or ([], '')."""

        # 1. NSDL static files (primary; works for 2018-2019 + recent months)
        nsdl_referer = "https://www.fpi.nsdl.co.in/"
        for url in _nsdl_urls(d):
            html = _fetch(url, referer=nsdl_referer)
            if html:
                rows = parse_fpi_table(html)
                if rows:
                    return rows, "NSDL"

        # 2. CDSL fallback (works for 2013 - Jun 2023)
        cdsl_referer = "https://www.cdslindia.com/"
        html = _fetch(_cdsl_url(d), referer=cdsl_referer)
        if html:
            rows = parse_fpi_table(html)
            if rows:
                return rows, "CDSL"

        # 3. SEBI fallback (only Apr 2012 - May 2014)
        if d <= date(2014, 5, 31):
            sebi_referer = "https://www.sebi.gov.in/"
            html = _fetch(_sebi_url(d), referer=sebi_referer)
            if html:
                rows = parse_fpi_table(html)
                if rows:
                    return rows, "SEBI"

        return [], ""

    # ── I/O ───────────────────────────────────────────────────────────────────

    def _save_atomic(self, df: pd.DataFrame):
        if df.empty:
            raise ValueError("G-D-03: refusing to write empty DataFrame")
        tmp = OUTPUT_FILE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_FILE))
        logger.info("[FPI] Saved %d rows -> %s", len(df), OUTPUT_FILE)

    def _save_recovery(self):
        r_df = pd.DataFrame({"date": self.recovery})
        tmp  = RECOVERY_FILE.with_suffix(".tmp")
        r_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_FILE))
        logger.warning("[FPI] Recovery queue: %d dates -> %s", len(self.recovery), RECOVERY_FILE)

    def print_summary(self):
        if not OUTPUT_FILE.exists():
            print("[FPI] No output file yet")
            return
        df = pd.read_csv(OUTPUT_FILE)
        print()
        print("=" * 60)
        print("SECTOR FPI ENGINE -- SUMMARY")
        print("=" * 60)
        print(f"Total rows     : {len(df)}")
        print(f"Date range     : {df['date'].min()} -> {df['date'].max()}")
        print(f"Unique dates   : {df['date'].nunique()}")
        print(f"Sources        : {df['source'].value_counts().to_dict()}")
        print(f"Sectors (raw)  : {df['sector_raw'].nunique()}")
        print(f"Sectors (norm) : {df['sector_normalized'].nunique()}")
        print("=" * 60)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Fetch NSDL/CDSL/SEBI fortnightly sector FPI data"
    )
    ap.add_argument(
        "--rebuild", action="store_true",
        help="Re-fetch all dates from scratch (ignore existing CSV)"
    )
    ap.add_argument(
        "--since", type=str, metavar="YYYY-MM-DD",
        help="Only fetch dates on or after this date"
    )
    ap.add_argument(
        "--summary", action="store_true",
        help="Print summary of existing data and exit"
    )
    args = ap.parse_args()

    engine = SectorFPIEngine()

    if args.summary:
        engine.print_summary()
    else:
        engine.run(full_rebuild=args.rebuild, since=args.since)
        engine.print_summary()
