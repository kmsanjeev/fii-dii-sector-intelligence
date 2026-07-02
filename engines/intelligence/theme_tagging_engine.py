"""
Theme Tagging Engine — Phase E
Multi-theme classification: assigns each symbol to 1-3 themes with purity scores.

Tagging sources (applied in order, highest purity wins per theme):
  1. Keyword rules  — company name + industry contains theme-specific terms (purity 0.75-0.95)
  2. Sector rules   — sector maps to theme(s) with baseline purity (0.50-0.80)
  3. Cap-size rules — LARGE/MID/SMALL category -> factor themes (purity 0.60)
  4. Cross-theme    — existing primary theme implies secondary themes (purity 0.55)

Output:
    data/reference/theme_tagging.csv
    Columns: SYMBOL, THEME, PURITY_SCORE, SOURCE, IS_PRIMARY

Run:
    py -3.11 engines/intelligence/theme_tagging_engine.py
"""

import sys
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Keyword rules ──────────────────────────────────────────────────────────────
# Each entry: (compiled_pattern, theme_code, purity_score)
# Matched against: "<COMPANY_NAME> | <INDUSTRY_NSE>" uppercased

KEYWORD_RULES = [
    # DATA_CENTRE
    (re.compile(r"\bDATA\s*CENT(RE|ER)|DATACENT|COLOCATION|CO-LOCATION|HYPERSCALE|\bCLOUD\s*INFRA"), "DATA_CENTRE", 0.90),
    (re.compile(r"\bHOSTING\b|\bIDC\b|INTERNET DATA"), "DATA_CENTRE", 0.80),

    # AI_ENABLERS
    (re.compile(r"\bARTIFICIAL\s+INTEL|\bMACHINE\s+LEARN|\bGENERATIVE\s+AI|\bGEN\s*AI\b"), "AI_ENABLERS", 0.90),
    (re.compile(r"\bAI\s+SOLUTION|\bAI\s+PLATFORM|\bAI\s+SERVICE|\bDATA\s+ANALYTICS|\bBIG\s+DATA"), "AI_ENABLERS", 0.80),
    (re.compile(r"\bNATURAL\s+LANG|\bNLP\b|\bCOMPUTER\s+VISION|\bDEEP\s+LEARN"), "AI_ENABLERS", 0.85),

    # SEMICONDUCTOR
    (re.compile(r"\bSEMICONDUCTOR|\bCHIP\s+MFG|\bWAFER\b|\bFABRICATION\b|VLSI\b"), "SEMICONDUCTOR", 0.92),
    (re.compile(r"\bPRINTED\s+CIRCUIT|\bPCB\b|\bELECTRONIC\s+COMPONENT|\bCOMPONENT\s+MFG"), "SEMICONDUCTOR", 0.80),
    (re.compile(r"\bDISPLAY\s+MODULE|\bLED\s+CHIP|\bMICROCONTROL|\bEMBEDDED\s+SYS"), "SEMICONDUCTOR", 0.75),

    # POWER_TD
    (re.compile(r"\bTRANSMISSION\s+(LINE|TOWER|GRID)|\bHVDC\b|\bSMART\s+METER|\bAMI\b"), "POWER_TD", 0.92),
    (re.compile(r"\bPOWER\s+DISTRIBUT|\bDISCOM\b|\bELECTRICITY\s+DISTRIBUT"), "POWER_TD", 0.88),
    (re.compile(r"\bTRANSFORMER|\bSWITCHGEAR|\bCIRCUIT\s+BREAK|\bPOWER\s+CABLE"), "POWER_TD", 0.80),
    (re.compile(r"\bENERGY\s+METER|\bSUBSTATION|\bPOWER\s+GRID"), "POWER_TD", 0.75),

    # WATER_MANAGEMENT
    (re.compile(r"\bWATER\s+TREAT|\bSEWAGE\s+TREAT|\bEFFLUENT\s+TREAT|\bSTP\b|\bWTP\b"), "WATER_MANAGEMENT", 0.92),
    (re.compile(r"\bWATER\s+SUPPLY|\bWATER\s+UTIL|\bIRRIGATION\s+SYS|\bDRIP\s+IRRIG"), "WATER_MANAGEMENT", 0.85),
    (re.compile(r"\bDEWATERING|\bWASTEWATER|\bZERO\s+LIQUID\s+DISCHARGE|\bZLD\b"), "WATER_MANAGEMENT", 0.80),

    # RAILWAYS_METRO
    (re.compile(r"\bRAILWAY\s+EQUIP|\bROLLING\s+STOCK|\bLOCOMOTIV|\bRAIL\s+COACH|\bVANDE\s+BHARAT"), "RAILWAYS_METRO", 0.95),
    (re.compile(r"\bMETRO\s+RAIL|\bMETRO\s+TRAIN|\bSIGNALLING\s+SYS|\bRAIL\s+SIGNAL"), "RAILWAYS_METRO", 0.90),
    (re.compile(r"\bRAILWAY\s+TRACK|\bRAIL\s+INFRA|\bRAILWAY\s+CONSTR|\bDEDICATED\s+FREIGHT"), "RAILWAYS_METRO", 0.85),

    # PORTS_SHIPPING
    (re.compile(r"\bPORT\s+OPER|\bSHIPPING\s+LINE|\bCONTAINER\s+TERM|\bDOCK\s+YARD|\bMARITIME"), "PORTS_SHIPPING", 0.92),
    (re.compile(r"\bBULK\s+CARRIER|\bTANKER\b|\bFREIGHT\s+FORWARD|\bCUSTOM\s+CLEAR|\bFREIGHT\s+AGENT"), "PORTS_SHIPPING", 0.80),
    (re.compile(r"\bSHIPBUILD|\bSHIP\s+REPAIR|\bMARINE\s+SERV"), "PORTS_SHIPPING", 0.85),

    # SMART_CITIES
    (re.compile(r"\bSMART\s+CITY|\bSURVEILLANCE\s+SYS|\bCCTV\b|\bTRAFFIC\s+MGMT|\bTRAFFIC\s+LIGHT"), "SMART_CITIES", 0.88),
    (re.compile(r"\bSMART\s+METER\s+INFRA|\bIoT\s+PLATFORM|\bIOT\b|\bSMART\s+GRID"), "SMART_CITIES", 0.75),

    # GREEN_HYDROGEN
    (re.compile(r"\bGREEN\s+HYDROGEN|\bHYDROGEN\s+PROD|\bELECTROLYSER|\bFUEL\s+CELL"), "GREEN_HYDROGEN", 0.95),
    (re.compile(r"\bHYDROGEN\s+STOR|\bGREEN\s+AMMONIA|\bH2\s+PROD"), "GREEN_HYDROGEN", 0.88),

    # BANKING_CREDIT
    (re.compile(r"\bCOMMERCIAL\s+BANK|\bPRIVATE\s+BANK|\bPUBLIC\s+SECTOR\s+BANK|\bSCHEDULED\s+BANK"), "BANKING_CREDIT", 0.90),
    (re.compile(r"\bSMALL\s+FINANCE\s+BANK|\bPAYMENT\s+BANK|\bNBFC\b|\bHOUSING\s+FINANC"), "BANKING_CREDIT", 0.80),

    # INSURANCE_GROWTH
    (re.compile(r"\bGENERAL\s+INSUR|\bLIFE\s+INSUR|\bHEALTH\s+INSUR|\bINSURANCE\s+COMP|\bREINSUR"), "INSURANCE_GROWTH", 0.95),

    # WEALTH_MGMT
    (re.compile(r"\bASSET\s+MANAG|\bMUTUAL\s+FUND|\bAMC\b|\bWEALTH\s+MANAG|\bPORT?FOLIO\s+MANAG"), "WEALTH_MGMT", 0.90),
    (re.compile(r"\bBROKERAGE\b|\bSTOCK\s+BROK|\bSECURITIES\s+BROK"), "WEALTH_MGMT", 0.75),

    # MICROFINANCE
    (re.compile(r"\bMICROFINANC|\bMICRO\s+FINANC|\bSELF\s+HELP\s+GROUP|\bMFI\b|\bJLG\b"), "MICROFINANCE", 0.95),

    # HEALTHTECH
    (re.compile(r"\bHEALTH\s*TECH|\bTELEMEDICIN|\bTELECONSULT|\bDIGITAL\s+HEALTH|\bHEALTH\s+ANALYT"), "HEALTHTECH", 0.90),
    (re.compile(r"\bMEDICAL\s+DEVICE|\bDIAGNOSTIC\s+EQUIP|\bMEDTECH\b|\bRADIOLOGY\s+AI"), "HEALTHTECH", 0.80),

    # SPECIALTY_CHEM
    (re.compile(r"\bSPECIALTY\s+CHEM|\bFINE\s+CHEM|\bAGROCHEM\b|\bCROP\s+CHEM|\bPESTICIDE\b"), "SPECIALTY_CHEM", 0.88),
    (re.compile(r"\bFLUOROCHEM|\bPIGMENT\b|\bDYE\s+CHEM|\bPHARMA\s+API|\bACTIVE\s+PHARMA"), "SPECIALTY_CHEM", 0.85),

    # QUICK_COMMERCE
    (re.compile(r"\bQUICK\s+COMM|\bD2C\b|\bDARK\s+STORE|\bHYPERLOCAL|\bON-DEMAND\s+DELIV"), "QUICK_COMMERCE", 0.88),
    (re.compile(r"\bFOOD\s+DELIVERY|\bGROCERY\s+DELIVERY|\bFAST\s+COMM"), "QUICK_COMMERCE", 0.75),

    # GOLD_JEWELLERY
    (re.compile(r"\bJEWELL?ERY\b|\bGOLD\s+ORNAMENT|\bGOLD\s+COIN|\bJEWELLER\b|\bDIAMOND\s+JEWEL"), "GOLD_JEWELLERY", 0.92),

    # TOURISM_HOSP
    (re.compile(r"\bHOTEL\b|\bRESORTS?\b|\bHOSPITALITY\b|\bTRAVEL\s+TOURISM|\bTOURISM\b"), "TOURISM_HOSP", 0.88),
    (re.compile(r"\bBED\s+AND\s+BREAK|\bHOME\s+STAY|\bECOTOURISM|\bCRUISE"), "TOURISM_HOSP", 0.80),

    # MEDIA_ENTERTAIN
    (re.compile(r"\bFILM\s+PROD|\bMOVIE\s+PROD|\bOTT\b|\bSTREAMING|\bCONTENT\s+PROD"), "MEDIA_ENTERTAIN", 0.88),
    (re.compile(r"\bGAMING\b|\beSPORTS\b|\bANIMATION|\bFANTASY\s+SPORT"), "MEDIA_ENTERTAIN", 0.85),

    # SPACE_ECONOMY
    (re.compile(r"\bSATELLITE\b|\bLAUNCH\s+VEH|\bROCKET\b|\bSPACE\s+TECH|\bINSPACE\b"), "SPACE_ECONOMY", 0.92),
    (re.compile(r"\bSATCOM\b|\bEARTH\s+OBS|\bGEOSPATIAL"), "SPACE_ECONOMY", 0.80),

    # BATTERY_STORAGE
    (re.compile(r"\bBATTERY\s+MANUF|\bLITHIUM\s+(ION|CELL)|\bENERGY\s+STORAGE\s+SYS|\bBESS\b"), "BATTERY_STORAGE", 0.92),
    (re.compile(r"\bSODIUM\s+ION|\bLEAD\s+ACID\s+BAT|\bBATTERY\s+PACK|\bCELL\s+MFG"), "BATTERY_STORAGE", 0.85),

    # CYBERSECURITY
    (re.compile(r"\bCYBER\s*SEC|\bINFO\s*SEC\b|\bNETWORK\s+SEC|\bENDPOINT\s+SEC|\bPENETRATION\s+TEST"), "CYBERSECURITY", 0.92),
    (re.compile(r"\bFIREWALL|\bVPN\s+SER|\bDLP\b|DATA\s+PROTEC"), "CYBERSECURITY", 0.80),

    # AGRITECH (only when company is clearly tech/digital applied to agri)
    (re.compile(r"\bAGRI\s*TECH|\bFARM\s+TECH|\bCROP\s+TECH|\bPRECISION\s+AGRI|\bSMART\s+FARM"), "AGRITECH", 0.88),
    (re.compile(r"\bAGRI\s*DRONE|\bFARM\s+DRONE|\bCROP\s+SENSOR"), "AGRITECH", 0.90),

    # GAMING_ESPORTS
    (re.compile(r"\bVIDEO\s+GAM|\bMOBILE\s+GAM|\beSPORT|\bGAMING\s+PLATFORM|\bFANTASY\s+SPORT"), "GAMING_ESPORTS", 0.90),
    (re.compile(r"\bONLINE\s+GAM|\bCAASUAL\s+GAM|\bREAL\s+MONEY\s+GAM"), "GAMING_ESPORTS", 0.85),

    # FINTECH_INFRASTR
    (re.compile(r"\bPAYMENT\s+GATEWAY|\bPAYMENT\s+TECH|\bUPI\s+INFRA|\bDIGITAL\s+PAYMENT"), "FINTECH_INFRASTR", 0.88),
    (re.compile(r"\bACCOUNT\s+AGGREG|\bCBDC\b|\bFINTECH\b|\bWALLET\b|\bLENDING\s+TECH"), "FINTECH_INFRASTR", 0.80),
]

# ── Sector → theme mapping ─────────────────────────────────────────────────────
# Format: sector_code -> [(theme_code, purity_score)]
# Only map ADDITIONAL new themes; existing primary themes come from classification_v4.csv

SECTOR_RULES: dict[str, list[tuple[str, float]]] = {
    "BANKING": [
        ("BANKING_CREDIT", 0.82),
        ("INTEREST_RATE_CYCLE", 0.65),
    ],
    "FINANCIAL_SERVICES": [
        ("BANKING_CREDIT", 0.55),
        ("INSURANCE_GROWTH", 0.50),
        ("WEALTH_MGMT", 0.55),
        ("INTEREST_RATE_CYCLE", 0.55),
        ("MICROFINANCE", 0.40),
    ],
    "AMC": [
        ("WEALTH_MGMT", 0.85),
        ("FINANCIALISATION", 0.75),
    ],
    "INSURANCE": [
        ("INSURANCE_GROWTH", 0.90),
    ],
    "POWER": [
        ("POWER_TD", 0.65),
        ("GREEN_ENERGY", 0.50),
    ],
    "ENERGY": [
        ("GREEN_ENERGY", 0.55),
        ("POWER_TD", 0.40),
        ("COMMODITY_SUPER", 0.50),
    ],
    "IT": [
        ("AI_ENABLERS", 0.55),
        ("DATA_CENTRE", 0.45),
        ("CYBERSECURITY", 0.45),
        ("FINTECH_INFRASTR", 0.40),
        ("DIGITAL_INDIA", 0.65),
    ],
    "TELECOM": [
        ("DATA_CENTRE", 0.50),
        ("DIGITAL_INDIA", 0.60),
        ("SMART_CITIES", 0.40),
    ],
    "CAPITAL_GOODS": [
        ("POWER_TD", 0.50),
        ("RAILWAYS_METRO", 0.45),
        ("SMART_CITIES", 0.40),
        ("SEMICONDUCTOR", 0.35),
    ],
    "INFRASTRUCTURE": [
        ("RAILWAYS_METRO", 0.50),
        ("PORTS_SHIPPING", 0.40),
        ("WATER_MANAGEMENT", 0.40),
        ("SMART_CITIES", 0.45),
    ],
    "LOGISTICS": [
        ("PORTS_SHIPPING", 0.55),
        ("SMART_CITIES", 0.35),
    ],
    "CHEMICALS": [
        ("SPECIALTY_CHEM", 0.60),
        ("GREEN_HYDROGEN", 0.35),
        ("BATTERY_STORAGE", 0.35),
        ("COMMODITY_SUPER", 0.50),
    ],
    "PHARMA": [
        ("SPECIALTY_CHEM", 0.55),
        ("HEALTHTECH", 0.35),
    ],
    "HEALTHCARE": [
        ("HEALTHTECH", 0.60),
    ],
    "DEFENCE": [
        ("SPACE_ECONOMY", 0.45),
        ("CYBERSECURITY", 0.50),
        ("SEMICONDUCTOR", 0.40),
    ],
    "AUTO": [
        ("EV_TRANSITION", 0.60),
        ("BATTERY_STORAGE", 0.40),
    ],
    "METAL": [
        ("COMMODITY_SUPER", 0.70),
        ("BATTERY_STORAGE", 0.35),
    ],
    "MINING": [
        ("COMMODITY_SUPER", 0.75),
    ],
    "AGRICULTURE": [
        ("MONSOON_AGRI", 0.75),
        ("AGRITECH", 0.35),
        ("RURAL_CONSUMPTION", 0.55),
    ],
    "FMCG": [
        ("RURAL_CONSUMPTION", 0.60),
        ("MONSOON_AGRI", 0.50),
        ("PREMIUMISATION", 0.55),
        ("QUICK_COMMERCE", 0.40),
    ],
    "RETAIL": [
        ("PREMIUMISATION", 0.55),
        ("QUICK_COMMERCE", 0.55),
        ("GOLD_JEWELLERY", 0.40),
    ],
    "REALTY": [
        ("INTEREST_RATE_CYCLE", 0.70),
        ("SMART_CITIES", 0.40),
    ],
    "HOSPITALITY": [
        ("TOURISM_HOSP", 0.85),
        ("PREMIUMISATION", 0.50),
    ],
    "AVIATION": [
        ("TOURISM_HOSP", 0.60),
        ("PREMIUMISATION", 0.50),
    ],
    "MEDIA": [
        ("MEDIA_ENTERTAIN", 0.80),
        ("GAMING_ESPORTS", 0.40),
    ],
    "TEXTILES": [
        ("CHINA_PLUS_ONE", 0.65),
        ("EXPORT_GROWTH", 0.60),
    ],
    "CEMENT": [
        ("INFRASTRUCTURE_BUILD", 0.65),
        ("REAL_ESTATE_RECOVERY", 0.45),
    ],
}

# ── Cross-theme rules ──────────────────────────────────────────────────────────
# If a symbol has primary theme X, also assign theme Y with given purity.
# Applied AFTER sector rules to enrich with macro themes.

CROSS_THEME_RULES: dict[str, list[tuple[str, float]]] = {
    "CHINA_PLUS_ONE":        [("INDIA_PLUS_ONE", 0.70), ("EXPORT_GROWTH", 0.60)],
    "EXPORT_GROWTH":         [("INDIA_PLUS_ONE", 0.65)],
    "DEFENCE_ELECTRONICS":   [("INDIA_PLUS_ONE", 0.55), ("CAPEX_CYCLE", 0.55)],
    "GREEN_ENERGY":          [("CAPEX_CYCLE", 0.55), ("BATTERY_STORAGE", 0.40)],
    "INFRASTRUCTURE_BUILD":  [("CAPEX_CYCLE", 0.70), ("INDIA_PLUS_ONE", 0.45)],
    "PSU_REVIVAL":           [("DIVIDEND_YIELD", 0.60), ("INTEREST_RATE_CYCLE", 0.50)],
    "REAL_ESTATE_RECOVERY":  [("INTEREST_RATE_CYCLE", 0.65)],
    "RURAL_CONSUMPTION":     [("MONSOON_AGRI", 0.60)],
    "EV_TRANSITION":         [("BATTERY_STORAGE", 0.55), ("CAPEX_CYCLE", 0.45)],
    "DIGITAL_INDIA":         [("AI_ENABLERS", 0.50), ("DATA_CENTRE", 0.40), ("FINTECH_INFRASTR", 0.45)],
}

# ── Cap-size → factor theme mapping ───────────────────────────────────────────
CAP_FACTOR_MAP = {
    "LARGE":  [("LARGECAP_VALUE", 0.62), ("DIVIDEND_YIELD", 0.55), ("QUALITY_GROWTH", 0.55)],
    "MID":    [("MIDCAP_MOMENTUM", 0.65), ("QUALITY_GROWTH", 0.50), ("TURNAROUND", 0.45)],
    "SMALL":  [("SMALLCAP_QUALITY", 0.62), ("TURNAROUND", 0.48)],
}


def _search_text(row: pd.Series) -> str:
    """Build the lookup text from company name + industry."""
    name = str(row.get("COMPANY_NAME", "")).upper()
    ind  = str(row.get("INDUSTRY_NSE", "")).upper()
    return f"{name} | {ind}"


def run():
    logger.info("[ThemeTagging] Starting Phase E multi-theme tagging engine")

    clf_path  = cfg.REFERENCE_DIR / "company_classification_v4.csv"
    fund_path = cfg.NSE_DIR / "equity_master" / "company_fundamentals_master.csv"

    if not clf_path.exists():
        logger.error(f"[ThemeTagging] Classification file missing: {clf_path}")
        return None

    clf = pd.read_csv(clf_path)
    clf.columns = [c.upper() for c in clf.columns]

    fund_df = None
    if fund_path.exists():
        fund_df = pd.read_csv(fund_path)
        fund_df.columns = [c.upper() for c in fund_df.columns]
        logger.info(f"[ThemeTagging] Loaded fundamentals: {len(fund_df)} rows")

    tags: list[dict] = []

    for _, row in clf.iterrows():
        symbol       = str(row["SYMBOL"]).upper().strip()
        sector       = str(row.get("SECTOR", "")).upper().strip()
        primary_theme = str(row.get("THEME", "")).upper().strip()
        search_text  = _search_text(row)

        # cap category from fundamentals
        cap_cat = ""
        if fund_df is not None:
            fund_row = fund_df[fund_df["SYMBOL"].str.upper() == symbol]
            if not fund_row.empty:
                cap_cat = str(fund_row.iloc[0].get("MARKET_CAP_CATEGORY", "")).upper().strip()

        # Collect all (theme, purity, source) for this symbol.
        # Use a dict keyed by theme to keep highest purity per theme.
        collected: dict[str, tuple[float, str]] = {}

        def _add(theme: str, purity: float, source: str):
            if theme not in collected or purity > collected[theme][0]:
                collected[theme] = (purity, source)

        # 1. Primary theme from existing classification (purity 1.0)
        if primary_theme and primary_theme not in ("", "NAN", "NONE", "NA"):
            _add(primary_theme, 1.0, "classification_v4")

        # 2. Keyword rules (highest specificity)
        for pattern, theme, purity in KEYWORD_RULES:
            if pattern.search(search_text):
                _add(theme, purity, "keyword")

        # 3. Sector rules
        sector_themes = SECTOR_RULES.get(sector, [])
        for theme, purity in sector_themes:
            _add(theme, purity, "sector")

        # 4. Cross-theme rules from primary
        cross = CROSS_THEME_RULES.get(primary_theme, [])
        for theme, purity in cross:
            _add(theme, purity, "cross_theme")

        # 5. Cap-size factor themes
        cap_themes = CAP_FACTOR_MAP.get(cap_cat, [])
        for theme, purity in cap_themes:
            _add(theme, purity, "cap_factor")

        # 6. Macro themes: COMMODITY_SUPER for metal/mining/chemicals
        if sector in ("METAL", "MINING", "CHEMICALS", "ENERGY") and "COMMODITY_SUPER" not in collected:
            _add("COMMODITY_SUPER", 0.55, "sector")

        # 7. INDIA_PLUS_ONE for all export/mfg facing sectors
        if sector in ("TEXTILES", "CHEMICALS", "PHARMA", "CAPITAL_GOODS", "DEFENCE") and "INDIA_PLUS_ONE" not in collected:
            _add("INDIA_PLUS_ONE", 0.50, "sector")

        # Emit one row per theme
        for theme, (purity, source) in collected.items():
            is_primary = (theme == primary_theme)
            tags.append({
                "SYMBOL":        symbol,
                "THEME":         theme,
                "PURITY_SCORE":  round(purity, 2),
                "SOURCE":        source,
                "IS_PRIMARY":    is_primary,
                "SECTOR":        sector,
            })

    if not tags:
        logger.error("[ThemeTagging] No tags generated")
        return None

    df = pd.DataFrame(tags)
    df = df.sort_values(["SYMBOL", "PURITY_SCORE"], ascending=[True, False]).reset_index(drop=True)

    # Stats
    theme_counts = df.groupby("THEME")["SYMBOL"].nunique().sort_values(ascending=False)
    logger.info(f"[ThemeTagging] Generated {len(df)} tags across {df['THEME'].nunique()} themes for {df['SYMBOL'].nunique()} symbols")
    logger.info(f"[ThemeTagging] Top themes by symbol count:\n{theme_counts.head(20).to_string()}")

    # Write atomically
    out_path = cfg.REFERENCE_DIR / "theme_tagging.csv"
    tmp_path = out_path.with_suffix(".tmp")
    df.to_csv(tmp_path, index=False)
    import shutil
    shutil.move(str(tmp_path), str(out_path))
    logger.info(f"[ThemeTagging] Wrote {len(df)} rows to {out_path}")

    # Print summary for terminal
    print(f"[ThemeTagging] Done. {len(df)} tags | {df['THEME'].nunique()} themes | {df['SYMBOL'].nunique()} symbols")
    print()
    print("Theme breakdown (symbols per theme):")
    for theme, count in theme_counts.items():
        bar = "#" * min(40, count // 10)
        print(f"  {theme:<30} {count:>4}  {bar}")

    return df


if __name__ == "__main__":
    run()
