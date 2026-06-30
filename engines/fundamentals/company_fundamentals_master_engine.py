"""
Company Fundamentals Master Engine
Phase 4A — Authoritative company master: identity + sector + industry + theme for 2123 EQ symbols.

Output: data/NSE/equity_master/company_fundamentals_master.csv
        data/NSE/equity_master/fundamentals_review_queue.csv
        data/NSE/equity_master/fundamentals_coverage_report.csv
"""

import sys
import shutil
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Platform taxonomies (canonical — change only via ADR)
# ---------------------------------------------------------------------------

VALID_SECTORS = {
    "BANKING", "FINANCIAL_SERVICES", "IT", "PHARMA", "FMCG", "AUTO",
    "CAPITAL_GOODS", "DEFENCE", "POWER", "ENERGY", "METAL", "REALTY",
    "INFRASTRUCTURE", "TELECOM", "CHEMICALS", "CEMENT", "LOGISTICS",
    "AGRICULTURE", "TEXTILES", "MEDIA", "RETAIL", "HOSPITALITY", "AVIATION",
    "HEALTHCARE", "INSURANCE", "AMC", "EXCHANGE", "DIVERSIFIED", "OTHER",
}

VALID_THEMES = {
    "DIGITAL_INDIA", "DEFENCE_ELECTRONICS", "EV_TRANSITION", "GREEN_ENERGY",
    "CHINA_PLUS_ONE", "CAPEX_CYCLE", "FINANCIALISATION", "REAL_ESTATE_RECOVERY",
    "INFRASTRUCTURE_BUILD", "SMART_MANUFACTURING", "DATA_CENTRES",
    "HEALTHCARE_EXPANSION", "RURAL_CONSUMPTION", "PREMIUMISATION",
    "EXPORT_GROWTH", "PSU_REVIVAL", "SEMICONDUCTOR", "LOGISTICS_MODERNISATION",
}

# Maps classification_v4 SECTOR values → our 29-sector canonical names
SECTOR_NORMALIZE = {
    "BANKING": "BANKING",
    "FINANCIAL_SERVICES": "FINANCIAL_SERVICES",
    "IT": "IT",
    "PHARMA": "PHARMA",
    "FMCG": "FMCG",
    "AUTO": "AUTO",
    "CAPITAL_GOODS": "CAPITAL_GOODS",
    "DEFENCE": "DEFENCE",
    "POWER": "POWER",
    "ENERGY": "ENERGY",
    "OIL_GAS": "ENERGY",
    "METALS": "METAL",
    "METAL": "METAL",
    "REALTY": "REALTY",
    "INFRASTRUCTURE": "INFRASTRUCTURE",
    "TELECOM": "TELECOM",
    "CHEMICALS": "CHEMICALS",
    "CEMENT": "CEMENT",
    "LOGISTICS": "LOGISTICS",
    "AGRICULTURE": "AGRICULTURE",
    "AGRI": "AGRICULTURE",
    "TEXTILES": "TEXTILES",
    "MEDIA": "MEDIA",
    "RETAIL": "RETAIL",
    "HOSPITALITY": "HOSPITALITY",
    "AVIATION": "AVIATION",
    "HEALTHCARE": "HEALTHCARE",
    "INSURANCE": "INSURANCE",
    "AMC": "AMC",
    "EXCHANGE": "EXCHANGE",
    "DIVERSIFIED": "DIVERSIFIED",
    # Non-canonical → closest 29-sector match
    "INDUSTRIAL_MANUFACTURING": "CAPITAL_GOODS",
    "CONSUMER_GOODS": "FMCG",
    "CONSUMER_DURABLES": "OTHER",
    "CONSUMER_SERVICES": "OTHER",
    "PROFESSIONAL_SERVICES": "IT",       # NSE consulting = IT-adjacent (TCS, Accenture, etc.)
    "PAPER": "OTHER",
    "TRADING": "OTHER",
    "EDUCATION": "HEALTHCARE",           # NSE education = healthcare adjacent in theme
    "ELECTRONICS": "CAPITAL_GOODS",
    "PACKAGING": "CHEMICALS",           # packaging materials = chemicals adjacent
}

# Basic sector → platform theme (Phase 4B refines this via industry_master)
SECTOR_TO_THEME = {
    "BANKING": "FINANCIALISATION",
    "FINANCIAL_SERVICES": "FINANCIALISATION",
    "INSURANCE": "FINANCIALISATION",
    "AMC": "FINANCIALISATION",
    "EXCHANGE": "FINANCIALISATION",
    "IT": "DIGITAL_INDIA",
    "TELECOM": "DIGITAL_INDIA",
    "MEDIA": "DIGITAL_INDIA",
    "DEFENCE": "DEFENCE_ELECTRONICS",
    "AUTO": "EV_TRANSITION",
    "POWER": "GREEN_ENERGY",
    "ENERGY": "GREEN_ENERGY",
    "REALTY": "REAL_ESTATE_RECOVERY",
    "CEMENT": "INFRASTRUCTURE_BUILD",
    "INFRASTRUCTURE": "INFRASTRUCTURE_BUILD",
    "LOGISTICS": "LOGISTICS_MODERNISATION",
    "CAPITAL_GOODS": "CAPEX_CYCLE",
    "METAL": "CAPEX_CYCLE",
    "PHARMA": "HEALTHCARE_EXPANSION",
    "HEALTHCARE": "HEALTHCARE_EXPANSION",
    "FMCG": "RURAL_CONSUMPTION",
    "AGRICULTURE": "RURAL_CONSUMPTION",
    "RETAIL": "PREMIUMISATION",
    "HOSPITALITY": "PREMIUMISATION",
    "AVIATION": "PREMIUMISATION",
    "CHEMICALS": "CHINA_PLUS_ONE",
    "TEXTILES": "CHINA_PLUS_ONE",
}

# Old market_cap_bucket → spec's 4-category system
MARKET_CAP_NORMALIZE = {
    "MEGA_CAP": "LARGE",
    "LARGE_CAP": "LARGE",
    "MID_CAP": "MID",
    "SMALL_CAP": "SMALL",
    "MICRO_CAP": "MICRO",
    "UNKNOWN": "UNKNOWN",
    "": "UNKNOWN",
}

# Required output columns — exactly as per Phase 4A spec
OUTPUT_COLUMNS = [
    "symbol", "isin", "company_name", "series", "status", "listing_date",
    "industry_nse", "sector_platform", "theme_platform", "market_cap_category",
    "business_profile", "fii_holding_pct", "dii_holding_pct",
    "promoter_holding_pct", "last_updated",
]

MIN_UNIVERSE_SIZE = 1800  # G-S-04


class CompanyFundamentalsMasterEngine:
    """
    Builds authoritative company master combining identity, classification,
    and market data for the complete 2123-symbol EQ universe.
    """

    def __init__(self):
        self.equity_master_path = cfg.EQUITY_MASTER_DIR / "equity_master.csv"
        self.classification_path = (
            cfg.REFERENCE_DIR / "company_classification_v4.csv"
        )
        self.name_mapping_path = (
            cfg.REFERENCE_DIR / "mapping" / "company_name_mapping.csv"
        )
        self.old_fundamentals_path = (
            cfg.REFERENCE_DIR / "company_fundamentals_master.csv"
        )
        self.override_path = (
            cfg.REFERENCE_DIR / "mapping" / "manual_override.csv"
        )

        self.output_path = cfg.EQUITY_MASTER_DIR / "company_fundamentals_master.csv"
        self.review_path = cfg.EQUITY_MASTER_DIR / "fundamentals_review_queue.csv"
        self.coverage_path = cfg.EQUITY_MASTER_DIR / "fundamentals_coverage_report.csv"

        self.run_date = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> bool:
        logger.info("[CompanyFundamentalsMasterEngine] Phase 4A starting")
        try:
            self._validate_inputs()
            universe = self._build_universe()
            enriched = self._enrich_classification(universe)
            enriched = self._enrich_isin(enriched)
            enriched = self._enrich_market_cap(enriched)
            enriched = self._apply_overrides(enriched)
            enriched = self._finalize_schema(enriched)
            self._validate_output(enriched)
            self._save(enriched)
            self._write_review_queue(enriched)
            self._write_coverage_report(enriched)
            self._log_summary(enriched)
            logger.info("[CompanyFundamentalsMasterEngine] Phase 4A complete")
            return True
        except Exception as e:
            logger.error(f"[CompanyFundamentalsMasterEngine] Failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Step 1 — Validate inputs exist
    # ------------------------------------------------------------------

    def _validate_inputs(self):
        required = {
            "equity_master": self.equity_master_path,
            "classification_v4": self.classification_path,
            "name_mapping": self.name_mapping_path,
            "old_fundamentals": self.old_fundamentals_path,
        }
        for name, path in required.items():
            if not path.exists():
                raise FileNotFoundError(f"Required input missing: {name} → {path}")
        logger.info("[validate_inputs] All required inputs present")

    # ------------------------------------------------------------------
    # Step 2 — Build EQ active universe from equity_master.csv
    # ------------------------------------------------------------------

    def _build_universe(self) -> pd.DataFrame:
        em = pd.read_csv(self.equity_master_path, dtype=str).fillna("")
        # G-S-01: EQ series only
        eq = em[em["SERIES"].str.strip() == "EQ"].copy()
        # Active symbols only
        eq = eq[eq["IS_ACTIVE"].str.strip() == "True"].copy()
        eq = eq.reset_index(drop=True)

        # G-S-04: universe size guard
        if len(eq) < MIN_UNIVERSE_SIZE:
            raise ValueError(
                f"Universe too small: {len(eq)} symbols (min {MIN_UNIVERSE_SIZE}). "
                "Check equity_master.csv."
            )
        logger.info(f"[build_universe] EQ active universe: {len(eq)} symbols")
        return eq[["SYMBOL", "COMPANY_NAME", "SERIES", "LISTING_DATE", "IS_ACTIVE"]].copy()

    # ------------------------------------------------------------------
    # Step 3 — Enrich with industry_nse and sector_platform
    # ------------------------------------------------------------------

    def _enrich_classification(self, df: pd.DataFrame) -> pd.DataFrame:
        clf = pd.read_csv(self.classification_path, dtype=str).fillna("")
        clf = clf.rename(columns={
            "SYMBOL": "symbol",
            "SECTOR": "_raw_sector",
            "THEME": "industry_nse",
        })
        clf = clf[["symbol", "_raw_sector", "industry_nse"]].drop_duplicates("symbol")

        df = df.rename(columns={
            "SYMBOL": "symbol",
            "COMPANY_NAME": "company_name",
            "SERIES": "series",
            "LISTING_DATE": "listing_date",
            "IS_ACTIVE": "status",
        })
        df["status"] = df["status"].map({"True": "ACTIVE", "False": "INACTIVE"}).fillna("UNKNOWN")

        df = df.merge(clf, on="symbol", how="left")

        # Normalize sector to 29-sector canonical taxonomy
        df["sector_platform"] = (
            df["_raw_sector"]
            .str.strip()
            .str.upper()
            .map(SECTOR_NORMALIZE)
            .fillna("OTHER")
        )

        # G-C-01: no null sectors
        unmatched = df[df["_raw_sector"].str.strip() != ""][
            ~df["_raw_sector"].str.strip().str.upper().isin(SECTOR_NORMALIZE)
        ]["symbol"].tolist()
        if unmatched:
            logger.warning(
                f"[enrich_classification] {len(unmatched)} symbols with unmapped sector → OTHER: "
                f"{unmatched[:10]}"
            )

        # Basic theme derivation from sector (Phase 4B will refine via industry_master)
        df["theme_platform"] = df["sector_platform"].map(SECTOR_TO_THEME)

        df = df.drop(columns=["_raw_sector"])
        logger.info(
            f"[enrich_classification] sector_platform coverage: "
            f"{df['sector_platform'].notna().sum()} / {len(df)}"
        )
        return df

    # ------------------------------------------------------------------
    # Step 4 — Enrich with ISIN from name_mapping (equity_master has blank ISINs)
    # ------------------------------------------------------------------

    def _enrich_isin(self, df: pd.DataFrame) -> pd.DataFrame:
        nm = pd.read_csv(self.name_mapping_path, dtype=str).fillna("")
        isin_map = nm.set_index("SYMBOL")["ISIN"].to_dict()
        df["isin"] = df["symbol"].map(isin_map).fillna("")

        null_isin = (df["isin"].str.strip() == "").sum()
        if null_isin > 0:
            logger.warning(
                f"[enrich_isin] {null_isin} symbols with no ISIN — added to review queue"
            )
        logger.info(
            f"[enrich_isin] ISIN populated: {len(df) - null_isin} / {len(df)}"
        )
        return df

    # ------------------------------------------------------------------
    # Step 5 — Enrich with market_cap_category from old fundamentals
    # ------------------------------------------------------------------

    def _enrich_market_cap(self, df: pd.DataFrame) -> pd.DataFrame:
        old = pd.read_csv(self.old_fundamentals_path, dtype=str).fillna("")
        mcap_map = old.set_index("SYMBOL")["MARKET_CAP_BUCKET"].to_dict()
        df["market_cap_category"] = (
            df["symbol"]
            .map(mcap_map)
            .fillna("")
            .map(MARKET_CAP_NORMALIZE)
            .fillna("UNKNOWN")
        )
        unknown = (df["market_cap_category"] == "UNKNOWN").sum()
        logger.info(
            f"[enrich_market_cap] market_cap_category: "
            f"{len(df) - unknown} known / {unknown} UNKNOWN"
        )
        return df

    # ------------------------------------------------------------------
    # Step 6 — Apply manual overrides (G-C-02: always last, immutable)
    # ------------------------------------------------------------------

    def _apply_overrides(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self.override_path.exists():
            logger.info("[apply_overrides] No manual_override.csv found — skipping")
            return df

        overrides = pd.read_csv(self.override_path, dtype=str).fillna("")
        override_count = 0
        for _, row in overrides.iterrows():
            symbol = row.get("symbol", "").strip()
            if not symbol:
                continue
            mask = df["symbol"] == symbol
            if not mask.any():
                logger.warning(f"[apply_overrides] Override for unknown symbol: {symbol}")
                continue
            for field in ["sector_platform", "theme_platform", "industry_nse"]:
                val = row.get(field, "").strip()
                if val:
                    df.loc[mask, field] = val
                    override_count += 1

        logger.info(f"[apply_overrides] Applied {override_count} field overrides")
        return df

    # ------------------------------------------------------------------
    # Step 7 — Finalize schema: add placeholder fields, reorder columns
    # ------------------------------------------------------------------

    def _finalize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        df["business_profile"] = df["company_name"]   # placeholder (real profile = Phase 4C)
        df["fii_holding_pct"] = None                  # populated in Phase 4 shareholding
        df["dii_holding_pct"] = None
        df["promoter_holding_pct"] = None
        df["last_updated"] = self.run_date

        # Validate sector values against canonical set
        bad_sectors = df[~df["sector_platform"].isin(VALID_SECTORS)]["symbol"].tolist()
        if bad_sectors:
            logger.warning(
                f"[finalize_schema] {len(bad_sectors)} symbols with invalid sector "
                f"(forcing to OTHER): {bad_sectors[:5]}"
            )
            df.loc[~df["sector_platform"].isin(VALID_SECTORS), "sector_platform"] = "OTHER"

        # Validate theme values — None is acceptable (G-C-01 only mandates sector)
        bad_themes = df[
            df["theme_platform"].notna()
            & ~df["theme_platform"].isin(VALID_THEMES)
        ]["symbol"].tolist()
        if bad_themes:
            logger.warning(
                f"[finalize_schema] {len(bad_themes)} symbols with invalid theme "
                f"(setting to None): {bad_themes[:5]}"
            )
            df.loc[
                df["theme_platform"].notna()
                & ~df["theme_platform"].isin(VALID_THEMES),
                "theme_platform",
            ] = None

        return df[OUTPUT_COLUMNS]

    # ------------------------------------------------------------------
    # Step 8 — Validate output before writing (G-D-03, G-D-04)
    # ------------------------------------------------------------------

    def _validate_output(self, df: pd.DataFrame):
        # G-D-03: no empty dataframe
        if df.empty:
            raise ValueError("Output DataFrame is empty — aborting write")

        # G-D-04: schema validation
        missing_cols = [c for c in OUTPUT_COLUMNS if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Output missing required columns: {missing_cols}")

        # G-S-04: universe size check
        if len(df) < MIN_UNIVERSE_SIZE:
            raise ValueError(
                f"Output too small: {len(df)} rows (min {MIN_UNIVERSE_SIZE})"
            )

        # ZERO null sectors allowed (G-C-01)
        null_sectors = df["sector_platform"].isna().sum()
        if null_sectors > 0:
            raise ValueError(f"sector_platform has {null_sectors} null values — violates G-C-01")

        logger.info(
            f"[validate_output] Passed — {len(df)} rows, all required columns present"
        )

    # ------------------------------------------------------------------
    # Step 9 — Atomic write (G-D-02)
    # ------------------------------------------------------------------

    def _safe_write(self, df: pd.DataFrame, target: Path):
        """Write to .tmp then rename — never direct write (G-D-02)."""
        tmp = target.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(target))

    def _save(self, df: pd.DataFrame):
        self._safe_write(df, self.output_path)
        logger.info(f"[save] Master written → {self.output_path}")

    # ------------------------------------------------------------------
    # Step 10 — Review queue and coverage report
    # ------------------------------------------------------------------

    def _write_review_queue(self, df: pd.DataFrame):
        """Symbols needing manual attention."""
        needs_review = df[
            (df["isin"].str.strip() == "")
            | (df["listing_date"].str.strip() == "")
            | (df["industry_nse"].str.strip() == "")
            | (df["sector_platform"] == "OTHER")
            | (df["market_cap_category"] == "UNKNOWN")
        ].copy()

        needs_review["review_reason"] = ""
        needs_review.loc[needs_review["isin"].str.strip() == "", "review_reason"] += "NULL_ISIN "
        needs_review.loc[needs_review["listing_date"].str.strip() == "", "review_reason"] += "NULL_LISTING_DATE "
        needs_review.loc[needs_review["industry_nse"].str.strip() == "", "review_reason"] += "NULL_INDUSTRY "
        needs_review.loc[needs_review["sector_platform"] == "OTHER", "review_reason"] += "UNCATEGORIZED_SECTOR "
        needs_review.loc[needs_review["market_cap_category"] == "UNKNOWN", "review_reason"] += "UNKNOWN_MCAP "
        needs_review["review_reason"] = needs_review["review_reason"].str.strip()

        if needs_review.empty:
            logger.info("[review_queue] No symbols require review")
        else:
            self._safe_write(needs_review[["symbol", "isin", "company_name", "sector_platform", "review_reason"]], self.review_path)
            logger.info(f"[review_queue] {len(needs_review)} symbols flagged → {self.review_path}")

    def _write_coverage_report(self, df: pd.DataFrame):
        total = len(df)
        report = {
            "total_symbols": total,
            "isin_populated": int((df["isin"].str.strip() != "").sum()),
            "industry_nse_populated": int((df["industry_nse"].str.strip() != "").sum()),
            "sector_classified": int((df["sector_platform"] != "OTHER").sum()),
            "theme_classified": int(df["theme_platform"].notna().sum()),
            "market_cap_known": int((df["market_cap_category"] != "UNKNOWN").sum()),
            "isin_pct": round((df["isin"].str.strip() != "").mean() * 100, 2),
            "sector_pct": round((df["sector_platform"] != "OTHER").mean() * 100, 2),
            "theme_pct": round(df["theme_platform"].notna().mean() * 100, 2),
            "market_cap_pct": round((df["market_cap_category"] != "UNKNOWN").mean() * 100, 2),
            "run_date": self.run_date,
        }
        self._safe_write(pd.DataFrame([report]), self.coverage_path)
        logger.info(f"[coverage_report] Written → {self.coverage_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _log_summary(self, df: pd.DataFrame):
        total = len(df)
        isin_pct = round((df["isin"].str.strip() != "").mean() * 100, 1)
        sector_pct = round((df["sector_platform"] != "OTHER").mean() * 100, 1)
        theme_pct = round(df["theme_platform"].notna().mean() * 100, 1)
        mcap_pct = round((df["market_cap_category"] != "UNKNOWN").mean() * 100, 1)

        print()
        print("=" * 70)
        print("  PHASE 4A — COMPANY FUNDAMENTALS MASTER COMPLETE")
        print("=" * 70)
        print(f"  Total symbols       : {total:,}")
        print(f"  ISIN populated      : {isin_pct}%")
        print(f"  Sector classified   : {sector_pct}%   (non-OTHER)")
        print(f"  Theme classified    : {theme_pct}%")
        print(f"  Market cap known    : {mcap_pct}%")
        print(f"  Output              : {self.output_path}")
        print(f"  Review queue        : {self.review_path}")
        print(f"  Coverage report     : {self.coverage_path}")
        print("=" * 70)

        print("\nSector distribution:")
        sec_dist = df["sector_platform"].value_counts()
        for sector, count in sec_dist.head(15).items():
            print(f"  {sector:<25} {count:>5}")
        if len(sec_dist) > 15:
            print(f"  ... and {len(sec_dist) - 15} more sectors")

        review_count = len(df[
            (df["isin"].str.strip() == "")
            | (df["sector_platform"] == "OTHER")
            | (df["market_cap_category"] == "UNKNOWN")
        ])
        if review_count:
            print(f"\nSymbols in review queue: {review_count}")
        print("=" * 70)


if __name__ == "__main__":
    engine = CompanyFundamentalsMasterEngine()
    engine.run()
