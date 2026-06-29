"""
Sector Capital Flow Engine
Phase 6A — Weight-allocate participant F&O flows to platform sectors

Method:
  For each trading day:
    1. Load bhavcopy EQ series → compute turnover proxy (close × volume) per symbol
    2. Map each symbol to a platform sector (from company_classification_v4.csv)
    3. Compute sector_weight = sector_turnover / total_market_turnover
    4. Multiply total FII/DII/PRO/CLIENT OI and Volume by each sector's weight

Output:
  data/intelligence/sector_capital_flows.csv
  Rows: one per (date × sector) for all 29 platform sectors from 2016-01-01 to latest bhavcopy date
  Incremental: only processes bhavcopy dates newer than last row in output file

Guardrails: G-S-01 (EQ only), G-D-02 (atomic writes), G-D-03 (no empty write),
            G-I-04 (no fillna(0) on flow data)
"""

import shutil
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("sector_capital_flow")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LEGACY_BHAV_ROOT = cfg.DATA_DIR / "bhavcopy" / "equity"
CLASSIFICATION   = cfg.DATA_DIR / "reference" / "company_classification_v4.csv"
FNO_HISTORY      = cfg.DATA_DIR / "historical" / "institutional" / "institutional_positioning_history.csv"
INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
OUTPUT_FILE      = INTELLIGENCE_DIR / "sector_capital_flows.csv"

FNO_START_DATE = "2016-01-01"   # institutional_positioning_history.csv starts here

# All 29 platform sectors
PLATFORM_SECTORS = [
    "BANKING", "FINANCIAL_SERVICES", "IT", "PHARMA", "FMCG", "AUTO",
    "CAPITAL_GOODS", "DEFENCE", "POWER", "ENERGY", "METAL", "REALTY",
    "INFRASTRUCTURE", "TELECOM", "CHEMICALS", "CEMENT", "LOGISTICS",
    "AGRICULTURE", "TEXTILES", "MEDIA", "RETAIL", "HOSPITALITY", "AVIATION",
    "HEALTHCARE", "INSURANCE", "AMC", "EXCHANGE", "DIVERSIFIED", "OTHER",
]

# F&O columns to weight-allocate (raw contract values)
FNO_FLOW_COLS = [
    "FII_OI_Net", "DII_OI_Net", "PRO_OI_Net", "CLIENT_OI_Net",
    "FII_Volume_Net", "DII_Volume_Net", "PRO_Volume_Net", "CLIENT_Volume_Net",
]

OUTPUT_SCHEMA = ["date", "sector", "sector_turnover_cr", "sector_weight",
                 "market_turnover_cr", "symbol_count"] + [f"{c}_attr" for c in FNO_FLOW_COLS]


class SectorCapitalFlowEngine:
    """
    Phase 6A — builds daily sector-attributed participant flows.

    Run after participant_acquisition_engine.py (Phase 5A) to keep flows current.
    First run processes 2016–latest (~2500 dates); subsequent runs are incremental.
    """

    def __init__(self):
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.sector_map: dict[str, str] = {}
        self.fno: pd.DataFrame = pd.DataFrame()

    def run(self) -> bool:
        logger.info("[SectorCapitalFlow] Starting Phase 6A")
        self._load_sector_map()
        self._load_fno_history()

        existing = self._load_existing()
        last_date = existing["date"].max() if not existing.empty else ""
        start_date = FNO_START_DATE if not last_date else last_date

        bhavcopy_files = self._collect_bhavcopy_files(start_date)
        if not bhavcopy_files:
            logger.info("[6A] Already current — no new bhavcopy files to process")
            return True

        logger.info("[6A] Processing %d bhavcopy files (from %s)", len(bhavcopy_files),
                    bhavcopy_files[0].stem)

        new_rows = []
        for i, bfile in enumerate(bhavcopy_files, 1):
            rows = self._process_one_file(bfile)
            new_rows.extend(rows)
            if i % 100 == 0:
                logger.info("[6A] Progress: %d / %d files", i, len(bhavcopy_files))

        if not new_rows:
            logger.info("[6A] No new rows produced")
            return True

        new_df = pd.DataFrame(new_rows, columns=OUTPUT_SCHEMA)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined = (combined.drop_duplicates(subset=["date", "sector"])
                    .sort_values(["date", "sector"])
                    .reset_index(drop=True))

        self._save_atomic(combined, OUTPUT_FILE)
        self._print_summary(combined, len(new_rows))
        return True

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------
    def _load_sector_map(self):
        if not CLASSIFICATION.exists():
            raise FileNotFoundError(f"Classification file missing: {CLASSIFICATION}")
        df = pd.read_csv(CLASSIFICATION, usecols=["SYMBOL", "SECTOR"])
        df["SYMBOL"] = df["SYMBOL"].str.strip().str.upper()
        df["SECTOR"] = df["SECTOR"].str.strip().str.upper().fillna("OTHER")
        self.sector_map = dict(zip(df["SYMBOL"], df["SECTOR"]))
        logger.info("[6A] Sector map: %d symbols", len(self.sector_map))

    def _load_fno_history(self):
        if not FNO_HISTORY.exists():
            raise FileNotFoundError(f"F&O history missing: {FNO_HISTORY}")
        df = pd.read_csv(FNO_HISTORY)
        if "Date" in df.columns:
            df = df.rename(columns={"Date": "date"})
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        for col in FNO_FLOW_COLS:
            df[col] = pd.to_numeric(df.get(col, np.nan), errors="coerce")
        self.fno = df.set_index("date")
        logger.info("[6A] F&O history: %d rows (%s → %s)",
                    len(self.fno), self.fno.index.min(), self.fno.index.max())

    def _load_existing(self) -> pd.DataFrame:
        if not OUTPUT_FILE.exists():
            return pd.DataFrame(columns=OUTPUT_SCHEMA)
        df = pd.read_csv(OUTPUT_FILE)
        df["date"] = df["date"].astype(str)
        return df

    # ------------------------------------------------------------------
    # Bhavcopy file collection
    # ------------------------------------------------------------------
    def _collect_bhavcopy_files(self, after_date: str) -> list[Path]:
        all_files = sorted(LEGACY_BHAV_ROOT.rglob("*.csv"))
        result = []
        for f in all_files:
            # Filename: bhavcopy_YYYYMMDD.csv
            try:
                date_str = f.stem.split("_")[1]
                file_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except (IndexError, ValueError):
                continue
            if file_date <= after_date:
                continue
            if file_date < FNO_START_DATE:
                continue
            result.append(f)
        return sorted(result)

    # ------------------------------------------------------------------
    # Per-file processing
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_bhav(bfile: Path) -> pd.DataFrame | None:
        """
        Handle two bhavcopy schemas:
          New (2020+): CLOSE_PRICE, TTL_TRD_QNTY columns
          Old (pre-2020): CLOSE, TOTTRDQTY / TOTTRDVAL columns
        Returns a DataFrame with canonical columns: SYMBOL, SERIES, CLOSE_PRICE, TTL_TRD_QNTY
        or None if the file cannot be read or parsed.
        """
        try:
            raw = pd.read_csv(bfile)
        except Exception:
            return None

        # Strip column names
        raw.columns = raw.columns.str.strip()

        if "CLOSE_PRICE" in raw.columns and "TTL_TRD_QNTY" in raw.columns:
            # New schema
            return raw[["SYMBOL", "SERIES", "CLOSE_PRICE", "TTL_TRD_QNTY"]].copy()

        if "CLOSE" in raw.columns and "TOTTRDQTY" in raw.columns:
            # Old schema — rename to canonical names
            df = raw[["SYMBOL", "SERIES", "CLOSE", "TOTTRDQTY"]].copy()
            df = df.rename(columns={"CLOSE": "CLOSE_PRICE", "TOTTRDQTY": "TTL_TRD_QNTY"})
            return df

        return None

    def _process_one_file(self, bfile: Path) -> list[dict]:
        try:
            date_str_raw = bfile.stem.split("_")[1]
            date_str = f"{date_str_raw[:4]}-{date_str_raw[4:6]}-{date_str_raw[6:8]}"
        except (IndexError, ValueError):
            return []

        # Skip dates not in F&O history
        if date_str not in self.fno.index:
            return []

        bhav = self._normalize_bhav(bfile)
        if bhav is None:
            logger.warning("[6A] Unrecognised schema: %s", bfile.name)
            return []

        # G-S-01: EQ series only
        bhav = bhav[bhav["SERIES"] == "EQ"].copy()
        if bhav.empty:
            return []

        bhav["SYMBOL"] = bhav["SYMBOL"].str.strip().str.upper()
        bhav["CLOSE_PRICE"] = pd.to_numeric(bhav["CLOSE_PRICE"], errors="coerce")
        bhav["TTL_TRD_QNTY"] = pd.to_numeric(bhav["TTL_TRD_QNTY"], errors="coerce")
        bhav = bhav.dropna(subset=["CLOSE_PRICE", "TTL_TRD_QNTY"])

        # Turnover proxy in crores
        bhav["turnover"] = bhav["CLOSE_PRICE"] * bhav["TTL_TRD_QNTY"] / 1e7

        # Map sector
        bhav["sector"] = bhav["SYMBOL"].map(self.sector_map).fillna("OTHER")

        # Aggregate per sector
        sector_agg = (bhav.groupby("sector")
                      .agg(sector_turnover_cr=("turnover", "sum"),
                           symbol_count=("SYMBOL", "count"))
                      .reset_index())

        market_turnover = sector_agg["sector_turnover_cr"].sum()
        if market_turnover <= 0:
            return []

        sector_agg["sector_weight"] = sector_agg["sector_turnover_cr"] / market_turnover
        sector_agg["market_turnover_cr"] = market_turnover
        sector_agg["date"] = date_str

        # Get participant flows for this date
        fno_row = self.fno.loc[date_str]

        rows = []
        for _, row in sector_agg.iterrows():
            weight = row["sector_weight"]
            entry = {
                "date": date_str,
                "sector": row["sector"],
                "sector_turnover_cr": round(row["sector_turnover_cr"], 4),
                "sector_weight": round(weight, 6),
                "market_turnover_cr": round(market_turnover, 2),
                "symbol_count": int(row["symbol_count"]),
            }
            for col in FNO_FLOW_COLS:
                val = fno_row.get(col, np.nan)
                entry[f"{col}_attr"] = round(float(val) * weight, 2) if pd.notna(val) else np.nan
            rows.append(entry)

        # Ensure all 29 platform sectors present (even with 0 turnover)
        present = {r["sector"] for r in rows}
        for sec in PLATFORM_SECTORS:
            if sec not in present:
                entry = {
                    "date": date_str,
                    "sector": sec,
                    "sector_turnover_cr": 0.0,
                    "sector_weight": 0.0,
                    "market_turnover_cr": market_turnover,
                    "symbol_count": 0,
                }
                for col in FNO_FLOW_COLS:
                    entry[f"{col}_attr"] = 0.0
                rows.append(entry)

        return rows

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty DataFrame to {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info("[6A] Saved: %s (%d rows)", path.name, len(df))

    def _print_summary(self, df: pd.DataFrame, new_rows: int):
        unique_dates = df["date"].nunique()
        unique_sectors = df["sector"].nunique()
        print()
        print("=" * 65)
        print("SECTOR CAPITAL FLOW ENGINE — PHASE 6A COMPLETE")
        print("=" * 65)
        print(f"Date range       : {df['date'].min()} to {df['date'].max()}")
        print(f"Unique dates     : {unique_dates}")
        print(f"Sectors covered  : {unique_sectors}")
        print(f"Total rows       : {len(df)}")
        print(f"New rows added   : {new_rows}")
        print()
        # Latest date top sectors by weight
        latest = df[df["date"] == df["date"].max()].sort_values("sector_weight", ascending=False)
        print(f"Top sectors by weight on {latest['date'].iloc[0]}:")
        for _, r in latest.head(8).iterrows():
            print(f"  {r['sector']:20s}: {r['sector_weight']*100:5.1f}%  "
                  f"FII_OI_attr={r.get('FII_OI_Net_attr', 0):+.0f}")
        print("=" * 65)


if __name__ == "__main__":
    engine = SectorCapitalFlowEngine()
    engine.run()
