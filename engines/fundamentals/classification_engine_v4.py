"""
Classification Engine V4
Phase 4C — Hierarchical sector/theme classifier for NSE EQ universe

Classification hierarchy (in priority order):
1. Industry Master lookup (exact match on industry_nse — covers 183 industry groups)
2. Symbol-level corrections (SYMBOL_CORRECTIONS dict — precision fixes for known OTHER)
3. Company name keyword matching (fallback for future unlisted symbols)
4. Manual override table (manual_override.csv — always applied last, G-C-02)
5. Flag as UNCLASSIFIED → classification_review_queue.csv

Outputs:
  data/reference/company_classification_v4.csv
  data/NSE/equity_master/company_fundamentals_master.csv  (updated in-place)
  data/NSE/equity_master/classification_coverage_report.csv
  data/NSE/equity_master/classification_review_queue.csv
"""

import shutil
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("classification_v4")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EQUITY_MASTER_DIR = cfg.EQUITY_MASTER_DIR
MAPPING_DIR = ROOT / "data" / "reference" / "mapping"

FUNDAMENTALS_FILE = EQUITY_MASTER_DIR / "company_fundamentals_master.csv"
INDUSTRY_MASTER_FILE = MAPPING_DIR / "industry_master.csv"
MANUAL_OVERRIDE_FILE = MAPPING_DIR / "manual_override.csv"
CLASSIFICATION_OUTPUT = ROOT / "data" / "reference" / "company_classification_v4.csv"
COVERAGE_REPORT = EQUITY_MASTER_DIR / "classification_coverage_report.csv"
REVIEW_QUEUE = EQUITY_MASTER_DIR / "classification_review_queue.csv"

# ---------------------------------------------------------------------------
# Guardrail constants
# ---------------------------------------------------------------------------
MIN_UNIVERSE_SIZE = 1800  # G-S-04

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
    "",
}

# ---------------------------------------------------------------------------
# Level 2: Symbol-level corrections
# (applied only when industry master gives OTHER or UNCLASSIFIED)
# Covers the 71 OTHER symbols from Phase 4B output.
# ---------------------------------------------------------------------------
SYMBOL_CORRECTIONS = {
    # AMC
    "ICICIAMC":  ("AMC", "FINANCIALISATION"),
    "NAM-INDIA": ("AMC", "FINANCIALISATION"),
    "UTIAMC":    ("AMC", "FINANCIALISATION"),
    # AUTO
    "SUPRAJIT":  ("AUTO", "EV_TRANSITION"),
    "MAJESAUT":  ("AUTO", "EV_TRANSITION"),
    "PTL":       ("AUTO", "EV_TRANSITION"),
    # CAPITAL_GOODS
    "INTLCONV":   ("CAPITAL_GOODS", "CAPEX_CYCLE"),
    "HARSHA":     ("CAPITAL_GOODS", "CAPEX_CYCLE"),
    "SANGHVIMOV": ("CAPITAL_GOODS", "CAPEX_CYCLE"),
    "DYNAMATECH": ("CAPITAL_GOODS", "DEFENCE_ELECTRONICS"),
    "OMNI":       ("CAPITAL_GOODS", "CAPEX_CYCLE"),
    "TEXINFRA":   ("CAPITAL_GOODS", "CAPEX_CYCLE"),
    # REALTY
    "INDIQUBE":   ("REALTY", "REAL_ESTATE_RECOVERY"),
    "MERCANTILE": ("REALTY", "REAL_ESTATE_RECOVERY"),
    "NESCO":      ("REALTY", "REAL_ESTATE_RECOVERY"),
    "NIRLON":     ("REALTY", "REAL_ESTATE_RECOVERY"),
    "SMARTWORKS": ("REALTY", "REAL_ESTATE_RECOVERY"),
    "EFCIL":      ("REALTY", "REAL_ESTATE_RECOVERY"),
    "HEMIPROP":   ("REALTY", "REAL_ESTATE_RECOVERY"),
    "WEWORK":     ("REALTY", "REAL_ESTATE_RECOVERY"),
    # IT
    "CYBERTECH": ("IT", "DIGITAL_INDIA"),
    "GENESYS":   ("IT", "DIGITAL_INDIA"),
    "SASKEN":    ("IT", "DIGITAL_INDIA"),
    "DSSL":      ("IT", "DIGITAL_INDIA"),
    "REDINGTON": ("IT", "DIGITAL_INDIA"),
    # TELECOM
    "SPCENET": ("TELECOM", "DIGITAL_INDIA"),
    # HOSPITALITY
    "DEVYANI":   ("HOSPITALITY", "PREMIUMISATION"),
    "ADVENTHTL": ("HOSPITALITY", "PREMIUMISATION"),
    # LOGISTICS
    "GICL":      ("LOGISTICS", "LOGISTICS_MODERNISATION"),
    "TARACHAND": ("LOGISTICS", "LOGISTICS_MODERNISATION"),
    "TVSSCS":    ("LOGISTICS", "LOGISTICS_MODERNISATION"),
    # FINANCIAL_SERVICES
    "DBSTOCKBRO": ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    "ALANKIT":    ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    "CMSINFO":    ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    "RADIANTCMS": ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    "PRUDENT":    ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    "ICDSLTD":    ("FINANCIAL_SERVICES", "FINANCIALISATION"),
    # ENERGY
    "SOUTHWEST": ("ENERGY", "CAPEX_CYCLE"),
    "KOTYARK":   ("ENERGY", "GREEN_ENERGY"),
    # METAL
    "SHIVAUM":   ("METAL", "CAPEX_CYCLE"),
    "GOYALALUM": ("METAL", "CAPEX_CYCLE"),
    "MSTCLTD":   ("METAL", "CAPEX_CYCLE"),
    # INFRASTRUCTURE
    "RUCHINFRA": ("INFRASTRUCTURE", "INFRASTRUCTURE_BUILD"),
    "ELITECON":  ("INFRASTRUCTURE", "INFRASTRUCTURE_BUILD"),
    # CHEMICALS
    "VIKASLIFE": ("CHEMICALS", "CHINA_PLUS_ONE"),
    "FLEXITUFF": ("CHEMICALS", "CHINA_PLUS_ONE"),
    "RUBFILA":   ("CHEMICALS", "CHINA_PLUS_ONE"),
    "SICAGEN":   ("CHEMICALS", "CAPEX_CYCLE"),
    "IWP":       ("CHEMICALS", "CHINA_PLUS_ONE"),
    # FMCG
    "KOTHARIPRO": ("FMCG", "RURAL_CONSUMPTION"),
    "VINCOFE":    ("FMCG", "RURAL_CONSUMPTION"),
    "GOLDIAM":    ("FMCG", "PREMIUMISATION"),
    # AGRICULTURE
    "UMAEXPORTS": ("AGRICULTURE", "EXPORT_GROWTH"),
    # TEXTILES
    "LAHOTIOV": ("TEXTILES", "EXPORT_GROWTH"),
    # MEDIA
    "TOUCHWOOD": ("MEDIA", "PREMIUMISATION"),
    # DEFENCE
    "ACEINTEG": ("DEFENCE", "DEFENCE_ELECTRONICS"),
    # RETAIL
    "CNL": ("RETAIL", "PREMIUMISATION"),
    # POWER
    "BLUSPRING": ("POWER", "GREEN_ENERGY"),
    # DIVERSIFIED (PSUs with genuinely mixed government mandates)
    "STCINDIA": ("DIVERSIFIED", "PSU_REVIVAL"),
    "MMTC":     ("DIVERSIFIED", "PSU_REVIVAL"),
}

# ---------------------------------------------------------------------------
# Level 3: Company name keyword matching
# Applied ONLY when both industry master AND symbol corrections give OTHER.
# Broader fallback for symbols added to NSE after this engine is written.
# Priority: first match wins (most specific first).
# ---------------------------------------------------------------------------
KEYWORD_RULES = [
    # format: (substring_in_company_name_uppercase, sector, theme)
    ("ASSET MANAGEMENT",  "AMC",              "FINANCIALISATION"),
    (" AMC",              "AMC",              "FINANCIALISATION"),
    ("INSURANCE",         "INSURANCE",        "FINANCIALISATION"),
    ("STOCK BROKER",      "FINANCIAL_SERVICES", "FINANCIALISATION"),
    ("STOCKBROKER",       "FINANCIAL_SERVICES", "FINANCIALISATION"),
    ("CASH MANAGEMENT",   "FINANCIAL_SERVICES", "FINANCIALISATION"),
    ("MICRO FINANCE",     "FINANCIAL_SERVICES", "FINANCIALISATION"),
    ("HOTEL",             "HOSPITALITY",      "PREMIUMISATION"),
    ("RESORT",            "HOSPITALITY",      "PREMIUMISATION"),
    ("RESTAURANT",        "HOSPITALITY",      "PREMIUMISATION"),
    ("HOSPITALITY",       "HOSPITALITY",      "PREMIUMISATION"),
    ("SUPPLY CHAIN",      "LOGISTICS",        "LOGISTICS_MODERNISATION"),
    ("LOGISTICS",         "LOGISTICS",        "LOGISTICS_MODERNISATION"),
    ("FREIGHT",           "LOGISTICS",        "LOGISTICS_MODERNISATION"),
    ("COURIER",           "LOGISTICS",        "LOGISTICS_MODERNISATION"),
    ("CARRIER",           "LOGISTICS",        "LOGISTICS_MODERNISATION"),
    ("SATELLITE",         "TELECOM",          "DIGITAL_INDIA"),
    ("VSAT",              "TELECOM",          "DIGITAL_INDIA"),
    ("COWORKING",         "REALTY",           "REAL_ESTATE_RECOVERY"),
    ("CO-WORKING",        "REALTY",           "REAL_ESTATE_RECOVERY"),
    ("PROPERTIES",        "REALTY",           "REAL_ESTATE_RECOVERY"),
    ("REAL ESTATE",       "REALTY",           "REAL_ESTATE_RECOVERY"),
    ("BIODISEL",          "ENERGY",           "GREEN_ENERGY"),
    ("BIO-DIESEL",        "ENERGY",           "GREEN_ENERGY"),
    ("RENEWABLE",         "POWER",            "GREEN_ENERGY"),
    ("SOLAR",             "POWER",            "GREEN_ENERGY"),
    ("WIND ENERGY",       "POWER",            "GREEN_ENERGY"),
    ("STEEL",             "METAL",            "CAPEX_CYCLE"),
    ("ALUMIN",            "METAL",            "CAPEX_CYCLE"),
    ("COPPER",            "METAL",            "CAPEX_CYCLE"),
    ("ZINC",              "METAL",            "CAPEX_CYCLE"),
    ("GEM",               "FMCG",             "PREMIUMISATION"),
    ("JEWEL",             "FMCG",             "PREMIUMISATION"),
    ("DIAMOND",           "FMCG",             "PREMIUMISATION"),
    ("GOLD",              "FMCG",             "PREMIUMISATION"),
    ("COFFEE",            "FMCG",             "RURAL_CONSUMPTION"),
    ("BEVERAGE",          "FMCG",             "RURAL_CONSUMPTION"),
    ("TOBACCO",           "FMCG",             "RURAL_CONSUMPTION"),
    ("CONVEYOR",          "CAPITAL_GOODS",    "CAPEX_CYCLE"),
    ("CRANE",             "CAPITAL_GOODS",    "CAPEX_CYCLE"),
    ("BEARING",           "CAPITAL_GOODS",    "CAPEX_CYCLE"),
    ("HYDRAULIC",         "CAPITAL_GOODS",    "CAPEX_CYCLE"),
    ("AEROSPACE",         "DEFENCE",          "DEFENCE_ELECTRONICS"),
    ("DEFENCE",           "DEFENCE",          "DEFENCE_ELECTRONICS"),
    ("DRONE",             "DEFENCE",          "DEFENCE_ELECTRONICS"),
    ("RUBBER",            "CHEMICALS",        "CHINA_PLUS_ONE"),
    ("PACKAGING",         "CHEMICALS",        "CHINA_PLUS_ONE"),
    ("CABLE",             "AUTO",             "EV_TRANSITION"),
    ("AUTO COMPONENT",    "AUTO",             "EV_TRANSITION"),
    ("AUTO PARTS",        "AUTO",             "EV_TRANSITION"),
    ("TEXTILE",           "TEXTILES",         "EXPORT_GROWTH"),
    ("FABRIC",            "TEXTILES",         "EXPORT_GROWTH"),
    ("GARMENT",           "TEXTILES",         "EXPORT_GROWTH"),
    ("COTTON",            "TEXTILES",         "EXPORT_GROWTH"),
    ("MEDIA",             "MEDIA",            "PREMIUMISATION"),
    ("ENTERTAINMENT",     "MEDIA",            "PREMIUMISATION"),
    ("RETAIL",            "RETAIL",           "PREMIUMISATION"),
    ("EXPORT",            "AGRICULTURE",      "EXPORT_GROWTH"),
    ("AGRI",              "AGRICULTURE",      "RURAL_CONSUMPTION"),
    ("INFRASTRUCTURE",    "INFRASTRUCTURE",   "INFRASTRUCTURE_BUILD"),
    ("EXPLORATION",       "ENERGY",           "CAPEX_CYCLE"),
    ("WOOD",              "CHEMICALS",        "CHINA_PLUS_ONE"),
    ("SYSTEMS AND SOFTWARE", "IT",            "DIGITAL_INDIA"),
    ("CYBERTECH",         "IT",              "DIGITAL_INDIA"),
    ("GENESYS",           "IT",              "DIGITAL_INDIA"),
    ("SPACENET",          "TELECOM",         "DIGITAL_INDIA"),
]


class ClassificationEngineV4:
    """
    Phase 4C — Hierarchical sector/theme classifier for NSE EQ universe.

    Reads company_fundamentals_master.csv, applies 5-level classification
    hierarchy, writes improved company_classification_v4.csv, and updates
    company_fundamentals_master.csv in-place.
    """

    def __init__(self):
        EQUITY_MASTER_DIR.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        logger.info("[ClassificationEngineV4] Starting Phase 4C")
        try:
            self._validate_inputs()
            df = self._load_base()
            industry_map, theme_map = self._load_industry_master()
            overrides = self._load_manual_overrides()

            df = self._apply_industry_master(df, industry_map, theme_map)
            df = self._apply_symbol_corrections(df)
            df = self._apply_keyword_matching(df)
            df = self._apply_manual_overrides(df, overrides)
            df = self._normalize_sectors(df)

            self._validate_schema(df)
            self._save_classification_csv(df)
            self._update_fundamentals_master(df)
            self._save_coverage_report(df)
            self._save_review_queue(df)

            self._print_summary(df)
            return True

        except Exception as exc:
            logger.error(f"[ClassificationEngineV4] Failed: {exc}")
            raise

    # ------------------------------------------------------------------
    # Step 1 — Validate inputs
    # ------------------------------------------------------------------
    def _validate_inputs(self):
        required = [FUNDAMENTALS_FILE, INDUSTRY_MASTER_FILE, MANUAL_OVERRIDE_FILE]
        for f in required:
            if not f.exists():
                raise FileNotFoundError(f"Required input missing: {f}")
        logger.info("[4C] Input validation passed")

    # ------------------------------------------------------------------
    # Step 2 — Load company_fundamentals_master.csv as base
    # ------------------------------------------------------------------
    def _load_base(self) -> pd.DataFrame:
        df = pd.read_csv(FUNDAMENTALS_FILE, dtype=str).fillna("")
        if len(df) < MIN_UNIVERSE_SIZE:
            raise ValueError(
                f"G-S-04 violation: only {len(df)} symbols (min {MIN_UNIVERSE_SIZE})"
            )
        logger.info(f"[4C] Loaded base: {len(df)} symbols")
        df["classification_source"] = "INDUSTRY_MASTER"
        return df

    # ------------------------------------------------------------------
    # Step 3 — Build industry_master lookup dicts
    # ------------------------------------------------------------------
    def _load_industry_master(self):
        im = pd.read_csv(INDUSTRY_MASTER_FILE, dtype=str).fillna("")
        industry_map = dict(zip(im["industry_nse"].str.upper(), im["sector_platform"]))
        theme_map = dict(zip(im["industry_nse"].str.upper(), im["theme_platform"]))
        logger.info(f"[4C] Industry master: {len(industry_map)} entries")
        return industry_map, theme_map

    # ------------------------------------------------------------------
    # Step 4 — Load manual overrides
    # ------------------------------------------------------------------
    def _load_manual_overrides(self) -> dict:
        mo = pd.read_csv(MANUAL_OVERRIDE_FILE, dtype=str).fillna("")
        result = {}
        for _, row in mo.iterrows():
            sym = row.get("symbol", "").strip().upper()
            sec = row.get("sector_platform", "").strip().upper()
            thm = row.get("theme_platform", "").strip().upper()
            if sym and sec:
                result[sym] = (sec, thm)
        logger.info(f"[4C] Manual overrides: {len(result)} entries")
        return result

    # ------------------------------------------------------------------
    # Level 1: Industry Master lookup
    # ------------------------------------------------------------------
    def _apply_industry_master(
        self,
        df: pd.DataFrame,
        industry_map: dict,
        theme_map: dict,
    ) -> pd.DataFrame:
        changed = 0
        for idx, row in df.iterrows():
            ind = row["industry_nse"].strip().upper()
            if not ind:
                continue
            new_sector = industry_map.get(ind, "")
            new_theme = theme_map.get(ind, "")
            if new_sector and new_sector in VALID_SECTORS:
                df.at[idx, "sector_platform"] = new_sector
                df.at[idx, "classification_source"] = "INDUSTRY_MASTER"
                changed += 1
            if new_theme and new_theme in VALID_THEMES:
                df.at[idx, "theme_platform"] = new_theme
        logger.info(f"[4C] Level 1 (industry master): {changed} updated")
        return df

    # ------------------------------------------------------------------
    # Level 2: Symbol-level corrections (precision fixes for OTHER symbols)
    # ------------------------------------------------------------------
    def _apply_symbol_corrections(self, df: pd.DataFrame) -> pd.DataFrame:
        changed = 0
        for idx, row in df.iterrows():
            sym = row["symbol"].strip().upper()
            if sym not in SYMBOL_CORRECTIONS:
                continue
            new_sector, new_theme = SYMBOL_CORRECTIONS[sym]
            current = row["sector_platform"]
            if new_sector and new_sector != current:
                df.at[idx, "sector_platform"] = new_sector
                df.at[idx, "classification_source"] = "SYMBOL_CORRECTION"
                if new_theme and new_theme in VALID_THEMES:
                    df.at[idx, "theme_platform"] = new_theme
                changed += 1
        logger.info(f"[4C] Level 2 (symbol corrections): {changed} updated")
        return df

    # ------------------------------------------------------------------
    # Level 3: Company name keyword matching (fallback for unknown OTHER)
    # ------------------------------------------------------------------
    def _apply_keyword_matching(self, df: pd.DataFrame) -> pd.DataFrame:
        changed = 0
        other_mask = df["sector_platform"].isin({"OTHER", "", "UNCLASSIFIED"})
        for idx, row in df[other_mask].iterrows():
            name = row["company_name"].strip().upper()
            for keyword, sector, theme in KEYWORD_RULES:
                if keyword in name:
                    df.at[idx, "sector_platform"] = sector
                    df.at[idx, "classification_source"] = "KEYWORD_MATCH"
                    if theme and theme in VALID_THEMES:
                        df.at[idx, "theme_platform"] = theme
                    changed += 1
                    break
        logger.info(f"[4C] Level 3 (keyword matching): {changed} updated")
        return df

    # ------------------------------------------------------------------
    # Level 4: Manual overrides — always applied last (G-C-02)
    # ------------------------------------------------------------------
    def _apply_manual_overrides(self, df: pd.DataFrame, overrides: dict) -> pd.DataFrame:
        changed = 0
        for idx, row in df.iterrows():
            sym = row["symbol"].strip().upper()
            if sym not in overrides:
                continue
            new_sector, new_theme = overrides[sym]
            if new_sector:
                df.at[idx, "sector_platform"] = new_sector
                df.at[idx, "classification_source"] = "MANUAL_OVERRIDE"
            if new_theme and new_theme in VALID_THEMES:
                df.at[idx, "theme_platform"] = new_theme
            changed += 1
        logger.info(f"[4C] Level 4 (manual override): {changed} applied")
        return df

    # ------------------------------------------------------------------
    # Normalize: G-C-01 no null sectors; flag remaining as UNCLASSIFIED
    # ------------------------------------------------------------------
    def _normalize_sectors(self, df: pd.DataFrame) -> pd.DataFrame:
        empty_mask = df["sector_platform"].isin({"", None})
        if empty_mask.any():
            df.loc[empty_mask, "sector_platform"] = "UNCLASSIFIED"
            df.loc[empty_mask, "classification_source"] = "UNCLASSIFIED"
            logger.warning(f"[4C] {empty_mask.sum()} symbols have empty sector → UNCLASSIFIED")
        df["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        return df

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------
    def _validate_schema(self, df: pd.DataFrame):
        required_cols = [
            "symbol", "isin", "company_name", "sector_platform",
            "theme_platform", "industry_nse",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Schema validation failed — missing columns: {missing}")

        invalid_sectors = set(df["sector_platform"]) - VALID_SECTORS - {"UNCLASSIFIED"}
        if invalid_sectors:
            logger.warning(f"[4C] Unknown sector values: {invalid_sectors}")

        invalid_themes = set(df["theme_platform"]) - VALID_THEMES
        if invalid_themes:
            logger.warning(f"[4C] Unknown theme values: {invalid_themes}")

        logger.info("[4C] Schema validation passed")

    # ------------------------------------------------------------------
    # Save company_classification_v4.csv (atomic)
    # ------------------------------------------------------------------
    def _save_classification_csv(self, df: pd.DataFrame):
        output_cols = [
            "symbol", "company_name", "sector_platform", "theme_platform",
            "industry_nse", "classification_source", "last_updated",
        ]
        out = df[[c for c in output_cols if c in df.columns]].copy()
        out = out.rename(columns={
            "symbol": "SYMBOL",
            "company_name": "COMPANY_NAME",
            "sector_platform": "SECTOR",
            "theme_platform": "THEME",
            "industry_nse": "INDUSTRY_NSE",
            "classification_source": "SOURCE",
            "last_updated": "LAST_UPDATED",
        })

        tmp = CLASSIFICATION_OUTPUT.with_suffix(".tmp")
        out.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(CLASSIFICATION_OUTPUT))
        logger.info(f"[4C] Saved: {CLASSIFICATION_OUTPUT} ({len(out)} rows)")

    # ------------------------------------------------------------------
    # Update company_fundamentals_master.csv in-place (atomic)
    # ------------------------------------------------------------------
    def _update_fundamentals_master(self, df: pd.DataFrame):
        drop_col = "classification_source"
        out = df.drop(columns=[drop_col], errors="ignore")

        if out.empty:
            raise ValueError("G-D-03: refusing to write empty DataFrame to fundamentals master")

        tmp = FUNDAMENTALS_FILE.with_suffix(".tmp")
        out.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(FUNDAMENTALS_FILE))
        logger.info(f"[4C] Updated fundamentals master: {FUNDAMENTALS_FILE} ({len(out)} rows)")

    # ------------------------------------------------------------------
    # Save coverage report
    # ------------------------------------------------------------------
    def _save_coverage_report(self, df: pd.DataFrame):
        total = len(df)
        other_n = (df["sector_platform"] == "OTHER").sum()
        unclassified_n = (df["sector_platform"] == "UNCLASSIFIED").sum()
        classified_n = total - other_n - unclassified_n
        sector_counts = df["sector_platform"].value_counts().reset_index()
        sector_counts.columns = ["sector", "count"]

        summary = pd.DataFrame([{
            "run_date": datetime.now().strftime("%Y-%m-%d"),
            "total_symbols": total,
            "classified": classified_n,
            "remaining_other": other_n,
            "unclassified": unclassified_n,
            "coverage_pct": round(classified_n * 100 / total, 2),
        }])

        tmp = COVERAGE_REPORT.with_suffix(".tmp")
        summary.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(COVERAGE_REPORT))

        sector_report = EQUITY_MASTER_DIR / "classification_sector_counts.csv"
        tmp2 = sector_report.with_suffix(".tmp")
        sector_counts.to_csv(tmp2, index=False)
        shutil.move(str(tmp2), str(sector_report))
        logger.info(f"[4C] Coverage report saved")

    # ------------------------------------------------------------------
    # Save review queue (OTHER + UNCLASSIFIED)
    # ------------------------------------------------------------------
    def _save_review_queue(self, df: pd.DataFrame):
        review_mask = df["sector_platform"].isin({"OTHER", "UNCLASSIFIED"})
        review = df[review_mask][
            ["symbol", "company_name", "industry_nse", "sector_platform",
             "theme_platform", "market_cap_category"]
        ].copy()
        review["flagged_date"] = datetime.now().strftime("%Y-%m-%d")

        if not review.empty:
            tmp = REVIEW_QUEUE.with_suffix(".tmp")
            review.to_csv(tmp, index=False)
            shutil.move(str(tmp), str(REVIEW_QUEUE))
        logger.info(f"[4C] Review queue: {len(review)} symbols")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    def _print_summary(self, df: pd.DataFrame):
        total = len(df)
        other_n = (df["sector_platform"] == "OTHER").sum()
        unclassified_n = (df["sector_platform"] == "UNCLASSIFIED").sum()
        classified_n = total - other_n - unclassified_n
        coverage = round(classified_n * 100 / total, 2)

        by_source = df["classification_source"].value_counts() if "classification_source" in df.columns else {}

        print()
        print("=" * 70)
        print("CLASSIFICATION ENGINE V4 — PHASE 4C COMPLETE")
        print("=" * 70)
        print(f"Total symbols    : {total:,}")
        print(f"Classified       : {classified_n:,}  ({coverage}%)")
        print(f"Remaining OTHER  : {other_n:,}")
        print(f"UNCLASSIFIED     : {unclassified_n:,}")
        print()
        print("Top sectors:")
        top_sectors = df["sector_platform"].value_counts().head(10)
        for sector, count in top_sectors.items():
            print(f"  {sector:<25} {count:>5}")
        print("=" * 70)


if __name__ == "__main__":
    engine = ClassificationEngineV4()
    engine.run()
