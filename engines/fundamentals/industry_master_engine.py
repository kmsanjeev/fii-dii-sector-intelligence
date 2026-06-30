"""
Industry Master Engine
Phase 4B — Build definitive industry_nse → sector_platform + theme_platform lookup table.

Reads Phase 4A output (company_fundamentals_master.csv), computes majority-vote sector
per industry, applies manual corrections, then writes the authoritative industry master
and immediately applies it back to improve company_fundamentals_master.csv.

Outputs:
    data/reference/mapping/industry_master.csv
    data/reference/mapping/industry_master_review.csv
    data/NSE/equity_master/company_fundamentals_master.csv  ← UPDATED in-place
"""

import sys
import shutil
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
# Canonical taxonomy (same as Phase 4A — do not modify without ADR)
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

# Industry group: broad meta-classification above sectors (for UI grouping)
SECTOR_TO_GROUP = {
    "BANKING":            "FINANCIAL_SERVICES",
    "FINANCIAL_SERVICES": "FINANCIAL_SERVICES",
    "INSURANCE":          "FINANCIAL_SERVICES",
    "AMC":                "FINANCIAL_SERVICES",
    "EXCHANGE":           "FINANCIAL_SERVICES",
    "IT":                 "TECHNOLOGY",
    "TELECOM":            "TECHNOLOGY",
    "MEDIA":              "TECHNOLOGY",
    "AUTO":               "MANUFACTURING",
    "CAPITAL_GOODS":      "MANUFACTURING",
    "METAL":              "MANUFACTURING",
    "CHEMICALS":          "MANUFACTURING",
    "TEXTILES":           "MANUFACTURING",
    "CEMENT":             "MANUFACTURING",
    "DEFENCE":            "MANUFACTURING",
    "PHARMA":             "HEALTHCARE",
    "HEALTHCARE":         "HEALTHCARE",
    "FMCG":               "CONSUMER",
    "RETAIL":             "CONSUMER",
    "HOSPITALITY":        "CONSUMER",
    "AVIATION":           "CONSUMER",
    "AGRICULTURE":        "AGRICULTURE",
    "INFRASTRUCTURE":     "INFRASTRUCTURE_ENERGY",
    "POWER":              "INFRASTRUCTURE_ENERGY",
    "ENERGY":             "INFRASTRUCTURE_ENERGY",
    "LOGISTICS":          "INFRASTRUCTURE_ENERGY",
    "REALTY":             "REAL_ESTATE",
    "DIVERSIFIED":        "DIVERSIFIED",
    "OTHER":              "OTHER",
}

# Default theme per sector (same as Phase 4A SECTOR_TO_THEME)
SECTOR_TO_THEME = {
    "BANKING":            "FINANCIALISATION",
    "FINANCIAL_SERVICES": "FINANCIALISATION",
    "INSURANCE":          "FINANCIALISATION",
    "AMC":                "FINANCIALISATION",
    "EXCHANGE":           "FINANCIALISATION",
    "IT":                 "DIGITAL_INDIA",
    "TELECOM":            "DIGITAL_INDIA",
    "MEDIA":              "DIGITAL_INDIA",
    "DEFENCE":            "DEFENCE_ELECTRONICS",
    "AUTO":               "EV_TRANSITION",
    "POWER":              "GREEN_ENERGY",
    "ENERGY":             "GREEN_ENERGY",
    "REALTY":             "REAL_ESTATE_RECOVERY",
    "CEMENT":             "INFRASTRUCTURE_BUILD",
    "INFRASTRUCTURE":     "INFRASTRUCTURE_BUILD",
    "LOGISTICS":          "LOGISTICS_MODERNISATION",
    "CAPITAL_GOODS":      "CAPEX_CYCLE",
    "METAL":              "CAPEX_CYCLE",
    "PHARMA":             "HEALTHCARE_EXPANSION",
    "HEALTHCARE":         "HEALTHCARE_EXPANSION",
    "FMCG":               "RURAL_CONSUMPTION",
    "AGRICULTURE":        "RURAL_CONSUMPTION",
    "RETAIL":             "PREMIUMISATION",
    "HOSPITALITY":        "PREMIUMISATION",
    "AVIATION":           "PREMIUMISATION",
    "CHEMICALS":          "CHINA_PLUS_ONE",
    "TEXTILES":           "CHINA_PLUS_ONE",
}

# Manual corrections: industry_nse → (sector_platform, theme_platform | None)
# Applied AFTER majority-vote to fix known wrong or ambiguous classifications.
MANUAL_CORRECTIONS = {
    # Phase 4A mapped PROFESSIONAL_SERVICES → IT, which pulled all
    # "DIVERSIFIED COMMERCIAL SERVICES" into IT. These are business service firms
    # (staffing, facility mgmt, security), not pure IT companies.
    "DIVERSIFIED COMMERCIAL SERVICES":            ("OTHER",        None),
    # Coal is a fuel/energy source, not just power generation infrastructure
    "COAL":                                       ("ENERGY",       "PSU_REVIVAL"),
    # Packaging → chemical-process industry (plastics, films, laminates)
    "PACKAGING":                                  ("CHEMICALS",    "CHINA_PLUS_ONE"),
    # Paper production is a chemical/pulp process
    "PAPER AND PAPER PRODUCTS":                   ("CHEMICALS",    "EXPORT_GROWTH"),
    # Home furnishing is a real estate ecosystem play
    "FURNITURE HOME FURNISHING":                  ("REALTY",       "REAL_ESTATE_RECOVERY"),
    # Houseware = consumer goods for home (cutlery, storage, cookware)
    "HOUSEWARE":                                  ("FMCG",         "RURAL_CONSUMPTION"),
    # Theme parks and recreational facilities → leisure/hospitality
    "AMUSEMENT PARKS OTHER RECREATION":           ("HOSPITALITY",  "PREMIUMISATION"),
    # Pure distributor businesses have no single underlying sector
    "TRADING AND DISTRIBUTORS":                   ("OTHER",        None),
    "DISTRIBUTORS":                               ("OTHER",        None),
    "OTHER CONSUMER SERVICES":                    ("OTHER",        None),
    # Timber/forest products — niche, insufficient data for sector assignment
    "FOREST PRODUCTS":                            ("OTHER",        None),
    # Sanitary ware → REALTY ancillary (used in construction and home-building)
    "SANITARY WARE":                              ("REALTY",       "REAL_ESTATE_RECOVERY"),
    # Gems and jewellery → premium consumer goods
    "GEMS JEWELLERY AND WATCHES":                 ("FMCG",         "PREMIUMISATION"),
}

# Confidence thresholds
HIGH_CONF   = 0.95   # majority ≥ 95% agreement → HIGH
MEDIUM_CONF = 0.75   # majority 75-94% → MEDIUM
LOW_CONF    = 0.60   # majority 60-74% → LOW (flagged for review)
REVIEW_THRESHOLD = 0.60  # below this → needs human review


class IndustryMasterEngine:
    """
    Builds the definitive industry_nse → sector_platform + theme_platform
    lookup table and immediately applies it to company_fundamentals_master.csv.
    """

    def __init__(self):
        self.fundamentals_path = cfg.EQUITY_MASTER_DIR / "company_fundamentals_master.csv"
        self.output_path = cfg.REFERENCE_DIR / "mapping" / "industry_master.csv"
        self.review_path = cfg.REFERENCE_DIR / "mapping" / "industry_master_review.csv"
        self.run_date = datetime.now().strftime("%Y-%m-%d")

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self) -> bool:
        logger.info("[IndustryMasterEngine] Phase 4B starting")
        try:
            self._validate_inputs()
            df = self._load_fundamentals()
            industry_master = self._build_master(df)
            industry_master = self._apply_corrections(industry_master)
            industry_master = self._assign_groups_and_themes(industry_master)
            industry_master = self._compute_confidence(industry_master)
            self._validate_master(industry_master)
            self._save_master(industry_master)
            self._write_review_queue(industry_master)
            updated = self._apply_to_fundamentals(df, industry_master)
            self._save_fundamentals(updated)
            self._log_summary(industry_master, updated)
            logger.info("[IndustryMasterEngine] Phase 4B complete")
            return True
        except Exception as e:
            logger.error(f"[IndustryMasterEngine] Failed: {e}")
            raise

    # ------------------------------------------------------------------
    # Step 1 — Validate
    # ------------------------------------------------------------------

    def _validate_inputs(self):
        if not self.fundamentals_path.exists():
            raise FileNotFoundError(
                f"Phase 4A output not found: {self.fundamentals_path}. "
                "Run company_fundamentals_master_engine.py first."
            )
        logger.info("[validate_inputs] Phase 4A output present")

    # ------------------------------------------------------------------
    # Step 2 — Load Phase 4A output
    # ------------------------------------------------------------------

    def _load_fundamentals(self) -> pd.DataFrame:
        df = pd.read_csv(self.fundamentals_path, dtype=str).fillna("")
        logger.info(f"[load_fundamentals] Loaded {len(df)} symbols, {df['industry_nse'].nunique()} unique industries")
        return df

    # ------------------------------------------------------------------
    # Step 3 — Compute majority sector per industry_nse
    # ------------------------------------------------------------------

    def _build_master(self, df: pd.DataFrame) -> pd.DataFrame:
        def majority_sector(series):
            counts = series.value_counts()
            return counts.index[0] if len(counts) else "OTHER"

        def sector_consistency(series):
            counts = series.value_counts()
            if len(counts) == 0:
                return 0.0
            return round(counts.iloc[0] / len(series), 4)

        agg = (
            df.groupby("industry_nse")
            .agg(
                sector_platform=("sector_platform", majority_sector),
                sector_consistency=("sector_platform", sector_consistency),
                company_count=("symbol", "count"),
                sample_symbols=("symbol", lambda x: ", ".join(x.head(5).tolist())),
            )
            .reset_index()
        )

        # Source tracks how this row was determined (overridden later for corrections)
        agg["source"] = "MAJORITY_VOTE"
        logger.info(f"[build_master] {len(agg)} industries, {(agg['sector_platform'] == 'OTHER').sum()} in OTHER")
        return agg

    # ------------------------------------------------------------------
    # Step 4 — Apply manual corrections (highest priority)
    # ------------------------------------------------------------------

    def _apply_corrections(self, master: pd.DataFrame) -> pd.DataFrame:
        # Initialize as empty string for ALL rows — prevents NaN propagation in _assign_groups_and_themes
        master["_manual_theme"] = ""
        corrections_applied = 0
        for industry_nse, (sector, theme) in MANUAL_CORRECTIONS.items():
            mask = master["industry_nse"] == industry_nse
            if not mask.any():
                logger.debug(f"[apply_corrections] industry not found in data: {industry_nse}")
                continue
            master.loc[mask, "sector_platform"] = sector
            master.loc[mask, "sector_consistency"] = 1.0   # manual = highest confidence
            master.loc[mask, "source"] = "MANUAL_CORRECTION"
            master.loc[mask, "_manual_theme"] = theme if theme else ""
            corrections_applied += 1
        logger.info(f"[apply_corrections] Applied {corrections_applied} manual corrections")
        return master

    # ------------------------------------------------------------------
    # Step 5 — Assign industry_group and theme_platform
    # ------------------------------------------------------------------

    def _assign_groups_and_themes(self, master: pd.DataFrame) -> pd.DataFrame:
        master["industry_group"] = master["sector_platform"].map(SECTOR_TO_GROUP).fillna("OTHER")
        master["theme_platform"] = master["sector_platform"].map(SECTOR_TO_THEME)

        # Apply manual theme overrides where set
        if "_manual_theme" in master.columns:
            manual_theme_mask = master["_manual_theme"].str.strip() != ""
            master.loc[manual_theme_mask, "theme_platform"] = (
                master.loc[manual_theme_mask, "_manual_theme"]
            )
            master = master.drop(columns=["_manual_theme"])

        # Validate theme values
        invalid_theme = master[
            master["theme_platform"].notna()
            & ~master["theme_platform"].isin(VALID_THEMES)
        ]
        if len(invalid_theme):
            logger.warning(
                f"[assign_groups_and_themes] {len(invalid_theme)} invalid themes → cleared: "
                f"{invalid_theme['theme_platform'].unique().tolist()}"
            )
            master.loc[
                master["theme_platform"].notna()
                & ~master["theme_platform"].isin(VALID_THEMES),
                "theme_platform",
            ] = None

        return master

    # ------------------------------------------------------------------
    # Step 6 — Compute confidence score
    # ------------------------------------------------------------------

    def _compute_confidence(self, master: pd.DataFrame) -> pd.DataFrame:
        def score(row):
            if row["source"] == "MANUAL_CORRECTION":
                return 1.00
            c = row["sector_consistency"]
            if c >= HIGH_CONF:
                return 0.95
            if c >= MEDIUM_CONF:
                return 0.80
            if c >= LOW_CONF:
                return 0.65
            return 0.50

        master["confidence_score"] = master.apply(score, axis=1)
        master["last_updated"] = self.run_date
        return master

    # ------------------------------------------------------------------
    # Step 7 — Validate master before write
    # ------------------------------------------------------------------

    def _validate_master(self, master: pd.DataFrame):
        if master.empty:
            raise ValueError("Industry master is empty — aborting")

        # All sectors must be canonical
        bad = master[~master["sector_platform"].isin(VALID_SECTORS)]["industry_nse"].tolist()
        if bad:
            raise ValueError(f"Non-canonical sectors in master: {bad}")

        # All themes (non-null) must be canonical
        bad_themes = master[
            master["theme_platform"].notna()
            & ~master["theme_platform"].isin(VALID_THEMES)
        ]["industry_nse"].tolist()
        if bad_themes:
            raise ValueError(f"Non-canonical themes in master: {bad_themes}")

        logger.info(f"[validate_master] {len(master)} industries — schema valid")

    # ------------------------------------------------------------------
    # Step 8 — Atomic write of industry_master.csv
    # ------------------------------------------------------------------

    def _safe_write(self, df: pd.DataFrame, target: Path):
        tmp = target.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(target))

    def _save_master(self, master: pd.DataFrame):
        output_cols = [
            "industry_nse", "sector_platform", "theme_platform",
            "industry_group", "confidence_score", "company_count",
            "sector_consistency", "source", "sample_symbols", "last_updated",
        ]
        out = master[output_cols].sort_values(
            ["industry_group", "sector_platform", "industry_nse"]
        )
        self._safe_write(out, self.output_path)
        logger.info(f"[save_master] Written → {self.output_path}")

    # ------------------------------------------------------------------
    # Step 9 — Write review queue for low-confidence industries
    # ------------------------------------------------------------------

    def _write_review_queue(self, master: pd.DataFrame):
        review = master[master["confidence_score"] < REVIEW_THRESHOLD].copy()
        if review.empty:
            logger.info("[review_queue] No industries need review")
            return
        review["review_reason"] = review.apply(
            lambda r: f"Low consistency: {r['sector_consistency']:.0%} agreement ({r['company_count']} companies)",
            axis=1,
        )
        self._safe_write(
            review[["industry_nse", "sector_platform", "company_count", "sector_consistency", "sample_symbols", "review_reason"]],
            self.review_path,
        )
        logger.warning(f"[review_queue] {len(review)} industries flagged → {self.review_path}")

    # ------------------------------------------------------------------
    # Step 10 — Apply improved master back to company_fundamentals_master.csv
    # ------------------------------------------------------------------

    def _apply_to_fundamentals(self, df: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
        """
        Re-derive sector_platform and theme_platform for every symbol
        using the authoritative industry_master lookup. Manual overrides
        in company_fundamentals_master.csv are preserved over the industry
        lookup (individual-symbol corrections take priority).
        """
        # Load the manual override file to know which symbols were hand-corrected
        override_path = cfg.REFERENCE_DIR / "mapping" / "manual_override.csv"
        manually_overridden_symbols: set = set()
        if override_path.exists():
            overrides = pd.read_csv(override_path, dtype=str).fillna("")
            manually_overridden_symbols = set(overrides["symbol"].str.strip().tolist())

        # Build quick lookup: industry_nse → (sector, theme)
        industry_lookup = master.set_index("industry_nse")[
            ["sector_platform", "theme_platform"]
        ].to_dict("index")

        before_other = (df["sector_platform"] == "OTHER").sum()
        sector_improved = 0
        theme_improved = 0

        for idx, row in df.iterrows():
            symbol = row["symbol"]
            if symbol in manually_overridden_symbols:
                continue  # Never override a hand-corrected symbol

            industry = row["industry_nse"].strip()
            if not industry or industry not in industry_lookup:
                continue

            new_sector = industry_lookup[industry]["sector_platform"]
            new_theme  = industry_lookup[industry]["theme_platform"]

            if new_sector and new_sector != row["sector_platform"]:
                df.at[idx, "sector_platform"] = new_sector
                sector_improved += 1

            # pd.notna check is required — float('nan') is truthy in Python
            if pd.notna(new_theme) and str(new_theme).strip() and row["theme_platform"] != str(new_theme):
                df.at[idx, "theme_platform"] = str(new_theme)
                theme_improved += 1

        after_other = (df["sector_platform"] == "OTHER").sum()
        logger.info(
            f"[apply_to_fundamentals] sector_platform updates: {sector_improved} | "
            f"theme_platform updates: {theme_improved} | "
            f"OTHER reduced: {before_other} → {after_other}"
        )
        df["last_updated"] = self.run_date
        return df

    def _save_fundamentals(self, df: pd.DataFrame):
        self._safe_write(df, self.fundamentals_path)
        logger.info(f"[save_fundamentals] company_fundamentals_master.csv updated → {self.fundamentals_path}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _log_summary(self, master: pd.DataFrame, updated_df: pd.DataFrame):
        total_industries = len(master)
        other_industries = (master["sector_platform"] == "OTHER").sum()
        manual_count = (master["source"] == "MANUAL_CORRECTION").sum()
        high_conf = (master["confidence_score"] >= HIGH_CONF).sum()
        review_count = (master["confidence_score"] < REVIEW_THRESHOLD).sum()

        total_symbols = len(updated_df)
        sector_pct = round((updated_df["sector_platform"] != "OTHER").mean() * 100, 1)
        theme_pct = round(updated_df["theme_platform"].notna().mean() * 100, 1)

        print()
        print("=" * 70)
        print("  PHASE 4B — INDUSTRY MASTER COMPLETE")
        print("=" * 70)
        print(f"  Industries mapped    : {total_industries}")
        print(f"  OTHER (unclassified) : {other_industries}")
        print(f"  Manual corrections   : {manual_count}")
        print(f"  High confidence      : {high_conf}")
        print(f"  Needs review         : {review_count}")
        print(f"  Output               : {self.output_path}")
        print()
        print("  company_fundamentals_master.csv (updated):")
        print(f"    Total symbols      : {total_symbols}")
        print(f"    Sector classified  : {sector_pct}%   (non-OTHER)")
        print(f"    Theme classified   : {theme_pct}%")
        print("=" * 70)

        print("\nIndustry group distribution:")
        for group, count in master.groupby("industry_group").size().sort_values(ascending=False).items():
            print(f"  {group:<30} {count:>4} industries")

        if other_industries > 0:
            print(f"\nUnclassified industries ({other_industries}):")
            for ind in master[master["sector_platform"] == "OTHER"]["industry_nse"].tolist():
                co = master.loc[master["industry_nse"] == ind, "company_count"].iloc[0]
                print(f"  {ind} ({co} companies)")
        print("=" * 70)


if __name__ == "__main__":
    engine = IndustryMasterEngine()
    engine.run()
