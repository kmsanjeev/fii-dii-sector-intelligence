"""
Auto Classification Engine V2
Capital Flow Intelligence Platform

Classifies all 2373 NSE equity symbols into sectors using a 2-layer approach:

  Layer 1 (Primary):  NSE industry data from ind_niftytotalmarket_list.csv
                      (if available in data/NSE/equity_master/ — download from NSE)
  Layer 2 (Fallback): Keyword rules applied to company names
                      (handles ~70-80% of symbols without NSE industry data)

Outputs:
  data/reference/company_classification.csv    -- all classified symbols
  data/reference/classification_review_queue.csv -- unclassified (manual review needed)
  data/reference/classification_coverage_report.csv -- sector distribution

Run classification_engine.py afterward to update coverage metrics.
"""

from pathlib import Path
from datetime import datetime

import pandas as pd


# ==============================================================
# CONFIGURATION
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EQUITY_MASTER = (
    PROJECT_ROOT / "data" / "NSE" / "equity_master" / "equity_master.csv"
)

# NSE Total Market / 500 index list (contains NSE industry per stock)
# Download from NSE -> Indices -> Nifty Total Market -> Download constituents
# Place in data/NSE/equity_master/ with any filename matching the pattern
NSE_INDUSTRY_SOURCES = [
    PROJECT_ROOT / "data" / "NSE" / "equity_master" / "ind_niftytotalmarket_list.csv",
    PROJECT_ROOT / "data" / "NSE" / "equity_master" / "ind_nifty500list.csv",
    PROJECT_ROOT / "data" / "NSE" / "equity_master" / "ind_nifty200list.csv",
]

REFERENCE_DIR = PROJECT_ROOT / "data" / "reference"

LOG_DIR = PROJECT_ROOT / "logs" / "classification_engine"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "auto_classification_v2.log"


# ==============================================================
# NSE INDUSTRY -> PLATFORM SECTOR MAPPING
# ==============================================================
# Maps NSE's own industry names to your 41-sector taxonomy.
# Extend this table as new NSE industries appear.

NSE_INDUSTRY_TO_SECTOR = {
    # Banking
    "PRIVATE SECTOR BANK":               "BANKING",
    "PUBLIC SECTOR BANK":                "BANKING",
    "BANK - PRIVATE":                    "BANKING",
    "BANK - PUBLIC":                     "BANKING",

    # Finance
    "FINANCE":                           "NBFC",
    "FINANCE - NBFC":                    "NBFC",
    "HOUSING FINANCE":                   "NBFC",
    "MICROFINANCE INSTITUTIONS":         "NBFC",

    # Insurance
    "INSURANCE":                         "INSURANCE",
    "INSURANCE - LIFE":                  "INSURANCE",
    "INSURANCE - GENERAL":               "INSURANCE",

    # AMC
    "ASSET MANAGEMENT COMPANIES & TRUSTEE COMPANIES": "AMC_WEALTH",
    "ASSET MANAGEMENT":                  "AMC_WEALTH",

    # Financial Services
    "CAPITAL MARKETS":                   "FINANCIAL_SERVICES",
    "STOCKBROKING & ALLIED":             "FINANCIAL_SERVICES",
    "FINANCIAL TECHNOLOGY (FINTECH)":    "FINANCIAL_SERVICES",

    # IT
    "IT - SOFTWARE":                     "IT",
    "IT ENABLED SERVICES":               "DIGITAL_SERVICES",
    "COMPUTERS - SOFTWARE & CONSULTING": "IT",
    "SOFTWARE":                          "IT",

    # Telecom
    "TELECOMMUNICATION - SERVICE PROVIDER": "TELECOM",
    "TELECOM - SERVICES":                "TELECOM",
    "TELECOM":                           "TELECOM",

    # Capital Goods
    "CAPITAL GOODS - ELECTRICAL EQUIPMENT": "ELECTRICAL_EQUIPMENT",
    "CAPITAL GOODS - NON ELECTRICAL EQUIPMENT": "CAPITAL_GOODS",
    "HEAVY ENGINEERING":                 "CAPITAL_GOODS",
    "INDUSTRIAL MACHINERY":              "CAPITAL_GOODS",
    "ENGINEERING":                       "CAPITAL_GOODS",

    # Industrial
    "INDUSTRIAL PRODUCTS":               "INDUSTRIAL_PRODUCTS",
    "INDUSTRIAL MANUFACTURING":          "INDUSTRIAL_MANUFACTURING",
    "DIVERSIFIED":                       "INDUSTRIAL_MANUFACTURING",

    # Infrastructure / Construction
    "INFRASTRUCTURE DEVELOPERS & OPERATORS": "INFRASTRUCTURE",
    "CONSTRUCTION":                      "CONSTRUCTION",
    "ROADS & HIGHWAYS":                  "INFRASTRUCTURE",
    "REAL ESTATE":                       "REALTY",
    "REALTY":                            "REALTY",
    "HOUSING":                           "REALTY",

    # Energy
    "POWER GENERATION & DISTRIBUTION":  "POWER",
    "POWER":                             "POWER",
    "OIL EXPLORATION":                   "OIL_GAS",
    "OIL REFINERY":                      "OIL_GAS",
    "GAS":                               "OIL_GAS",
    "OIL & GAS":                         "OIL_GAS",
    "PETROLEUM PRODUCTS":                "OIL_GAS",
    "RENEWABLE ENERGY":                  "RENEWABLE_ENERGY",
    "SOLAR ENERGY":                      "RENEWABLE_ENERGY",

    # Defence
    "AEROSPACE & DEFENCE":               "DEFENCE",
    "DEFENCE":                           "DEFENCE",

    # Mobility
    "AUTOMOBILES":                       "AUTO",
    "AUTOMOBILES & AUTO COMPONENTS":     "AUTO",
    "AUTO COMPONENTS & EQUIPMENT":       "AUTO_ANCILLARY",
    "AUTOMOBILE ANCILLARIES":            "AUTO_ANCILLARY",
    "TYRES & RUBBER PRODUCTS":           "AUTO_ANCILLARY",
    "TRANSPORTATION":                    "LOGISTICS",
    "LOGISTICS":                         "LOGISTICS",
    "SHIPPING":                          "SHIPBUILDING",

    # Healthcare
    "PHARMACEUTICALS & BIOTECHNOLOGY":   "PHARMA",
    "PHARMACEUTICAL":                    "PHARMA",
    "HEALTHCARE SERVICES":               "HEALTHCARE",
    "HOSPITAL & HEALTHCARE":             "HEALTHCARE",
    "DIAGNOSTICS":                       "DIAGNOSTICS",

    # Materials
    "METALS & MINING":                   "METALS",
    "STEEL":                             "METALS",
    "NON-FERROUS METALS":                "METALS",
    "MINING":                            "METALS",
    "CHEMICALS":                         "CHEMICALS",
    "SPECIALTY CHEMICALS":               "SPECIALTY_CHEMICALS",
    "FERTILISERS & AGROCHEMICALS":       "FERTILIZERS",
    "PESTICIDES & AGROCHEMICALS":        "SPECIALTY_CHEMICALS",
    "CEMENT & CEMENT PRODUCTS":          "CEMENT",
    "CEMENT":                            "CEMENT",

    # Agriculture
    "AGRICULTURAL FOOD & OTHER PRODUCTS": "AGRI",
    "AGRICULTURE":                       "AGRI",
    "SUGAR":                             "SUGAR",
    "FERTILIZERS":                       "FERTILIZERS",

    # Consumption
    "FAST MOVING CONSUMER GOODS":        "FMCG",
    "FMCG":                              "FMCG",
    "HOUSEHOLD & PERSONAL PRODUCTS":     "FMCG",
    "FOOD & BEVERAGES":                  "FMCG",
    "CONSUMER DURABLES":                 "CONSUMER_DURABLES",
    "RETAIL":                            "RETAIL",
    "RETAILING":                         "RETAIL",
    "HOTELS RESTAURANTS & TOURISM":      "HOSPITALITY",
    "HOSPITALITY":                       "HOSPITALITY",
    "MEDIA & ENTERTAINMENT":             "DIGITAL_SERVICES",
}


# ==============================================================
# KEYWORD RULES (Layer 2 fallback)
# ==============================================================
# Order matters: more specific rules must appear before generic ones.
# Each entry: (list_of_keywords_to_match, sector_name)
# Matching is done on UPPER-CASE company name.

KEYWORD_RULES = [
    # ── NBFC (before BANKING to avoid misclassification)
    (["NBFC", "NON BANKING FINANCE", "NON-BANKING FINANCE",
      "HOUSING FINANCE", "MICROFINANCE", "MUTHOOT FINANCE",
      "MANAPPURAM FINANCE", "BAJAJ FINANCE", "CHOLAMANDALAM",
      "MAHINDRA FINANCE", "TATA CAPITAL", "PIRAMAL FINANCE",
      "AAVAS FINANCIERS", "REPCO"], "NBFC"),

    # ── INSURANCE
    (["INSURANCE", " INS ", "REINSURANCE", "ASSURANCE",
      "STAR HEALTH", "CARE HEALTH", "HDFC ERGO"], "INSURANCE"),

    # ── AMC / WEALTH MANAGEMENT
    (["ASSET MANAGEMENT", " AMC ", "WEALTH MANAGEMENT",
      "NIPPON INDIA AMC", "MIRAE ASSET", "MOTILAL OSWAL ASSET",
      "UTI AMC", "ADITYA BIRLA AMC"], "AMC_WEALTH"),

    # ── BANKING
    (["BANK", "BANKING"], "BANKING"),

    # ── FINANCIAL SERVICES (catch-all after specific finance buckets)
    (["FINANCIAL SERVICES", "STOCK BROKER",
      "ANGEL ONE", "INDIA INFOLINE", "IIFL",
      "NUVAMA", "SECURITIES LTD", "SECURITIES LIM",
      "INVESTMENT LTD", "INVESTMENT LIM",
      "WEALTH LTD", "WEALTH LIM"], "FINANCIAL_SERVICES"),

    # ── TELECOM (before IT)
    (["TELECOM", "TELECOMMUNICATION", "AIRTEL",
      "VODAFONE IDEA", "TATA COMMUNICATIONS",
      "STERLITE TECHNOLOGIES", "RAILTEL",  # Railtel is telecom infra
      "ROUTE MOBILE", "TANLA PLATFORMS"], "TELECOM"),

    # ── IT / DIGITAL
    (["INFOTECH", "INFORMATION TECHNOLOGY",
      "INFOSYS", "WIPRO LTD", "TCS LTD",
      "TATA CONSULTANCY", "HCL TECHNOLOG",
      "MPHASIS", "TECH MAHINDRA",
      "TATA ELXSI", "KPIT TECHNOLOG",
      "PERSISTENT SYSTEMS", "COFORGE",
      "LTIMINDTREE", "HEXAWARE",
      "SOFTWARE LTD", "SOFTWARE LIM",
      "TECHNOLOGIES LTD", "TECHNOLOGIES LIM",
      " IT LTD", " IT LIM",
      "CONSULTANCY SERVICES", "CYIENT",
      "MASTEK", "ZENSAR", "BIRLASOFT",
      "INTELLECT DESIGN", "NEWGEN SOFTWARE",
      "KELLTON TECH"], "IT"),

    # ── DEFENCE
    (["DEFENCE", "DEFENSE",
      "HINDUSTAN AERONAUTICS",
      "BHARAT ELECTRONICS", "BHARAT DYNAMICS",
      "MAZAGON DOCK", "COCHIN SHIPYARD",
      "GARDEN REACH", "GRSE ",
      "DATA PATTERNS", "IDEAFORGE",
      "PARAS DEFENCE", "SOLAR INDUSTRIES",
      "PREMIER EXPLOSIVES", "MIDHANI",
      "BEML LTD", "BEML LIM",
      "ASTRA MICROWAVE"], "DEFENCE"),

    # ── AEROSPACE / AVIATION
    (["AEROSPACE", "AVIATION", "AIRLINE",
      "INTERGLOBE", "SPICEJET",
      "GMR AIRPORTS", "ADANI PORTS",   # port is logistics but GMR is airports
      "AIR WORKS", "BENGALURU INT"], "AEROSPACE"),

    # ── SHIPBUILDING / MARINE
    (["SHIPBUILDING", "SHIPYARD",
      "DREDGING CORPORATION",
      "OFFSHORE MARINE",
      "ABG SHIPYARD"], "SHIPBUILDING"),

    # ── RENEWABLE ENERGY (before generic POWER)
    (["RENEWABLE", "GREEN ENERGY",
      "SOLAR LTD", "SOLAR LIM",
      "WIND ENERGY", "ADANI GREEN",
      "GREENKO", "NTPC RENEWABLE",
      "JSW ENERGY RENEW",
      "INOX GREEN", "PREMIER ENERGIES"], "RENEWABLE_ENERGY"),

    # ── OIL & GAS (before POWER — avoid RELIANCE INDUSTRIES catching INDUSTRIAL)
    (["OIL & NATURAL GAS", "ONGC",
      "BHARAT PETROLEUM", "HINDUSTAN PETROLEUM",
      "INDIAN OIL", "BPCL", "HPCL",
      "RELIANCE INDUSTRIES",
      "PETRONET LNG", "GAIL ",
      "MAHANAGAR GAS", "INDRAPRASTHA GAS",
      "GUJARAT GAS", "GUJARAT STATE PETRO",
      "PETROLEUM CORP", "PETROLEUM LTD",
      "OIL INDIA LTD", "SELAN",
      "REFINERY LTD", "REFINERY LIM"], "OIL_GAS"),

    # ── POWER
    (["POWER LTD", "POWER LIM",
      "POWER CORP", "POWER GRID",
      "POWERGRID", "NTPC LTD", "NHPC LTD",
      "TATA POWER", "ADANI POWER",
      "TORRENT POWER", "CESC LTD",
      "JSPL POWER", "PTC INDIA",
      "ENERGY LTD", "ENERGY LIM",
      "JSW ENERGY", "KALPATARU POWER",
      "STERLITE POWER"], "POWER"),

    # ── RAILWAY
    (["RAILWAY", "RAIL VIKAS", "RVNL",
      "IRCON", "IRFC",
      "TITAGARH", "TEXMACO RAIL",
      "KERNEX MICROSYS",
      "HBL POWER SYSTEM"], "RAILWAY"),

    # ── REALTY (before CONSTRUCTION)
    (["REALTY LTD", "REALTY LIM",
      "REAL ESTATE", "PROPERTIES LTD", "PROPERTIES LIM",
      "DLF LTD", "GODREJ PROPERTIES",
      "OBEROI REALTY", "BRIGADE ENTERPRISES",
      "PRESTIGE ESTATES", "SOBHA LTD",
      "MACROTECH", "LODHA",
      "KOLTE PATIL", "SUNTECK REALTY",
      "MAHINDRA LIFESPACE",
      "HOUSING DEVELOPMENT FINANCE"], "REALTY"),

    # ── CONSTRUCTION
    (["CONSTRUCTION LTD", "CONSTRUCTION LIM",
      "LARSEN & TOUBRO", "NCC LTD",
      "DILIPBUILDCON", "KNR CONSTRUCTIONS",
      "ASHOKA BUILDCON", "PNC INFRATECH",
      "HG INFRA", "IRCON INTERNATIONAL",
      "ROADS LTD", "ROADS LIM",
      "HIGHWAY LTD", "HIGHWAY LIM"], "CONSTRUCTION"),

    # ── INFRASTRUCTURE (catch-all)
    (["INFRASTRUCTURE LTD", "INFRASTRUCTURE LIM",
      "INFRA LTD", "INFRA LIM",
      "TRANSMISSION LTD", "TRANSFORMER LTD",
      "ADANI ENTERPRISES"], "INFRASTRUCTURE"),

    # ── ELECTRICAL EQUIPMENT
    (["ELECTRICAL LTD", "ELECTRICAL LIM",
      "CABLES LTD", "CABLES LIM",
      "WIRES LTD", "WIRES LIM",
      "SWITCHGEAR", "HAVELLS INDIA",
      "POLYCAB INDIA", "FINOLEX CABLES",
      "KEI INDUSTRIES"], "ELECTRICAL_EQUIPMENT"),

    # ── CAPITAL GOODS (heavy engineering)
    (["ENGINEERS LTD", "ENGINEERS LIM",
      "ENGINEERING LTD", "ENGINEERING LIM",
      "BHARAT HEAVY ELECTRICALS",
      "THERMAX", "SIEMENS INDIA", "ABB INDIA",
      "MACHINERY LTD", "MACHINERY LIM",
      "BOILERS LTD", "TURBINES LTD",
      "CUMMINS INDIA",
      "GRINDWELL NORTON",
      "TIMKEN INDIA", "SKF INDIA"], "CAPITAL_GOODS"),

    # ── INDUSTRIAL PRODUCTS (precision / specialty components)
    (["BEARINGS LTD", "BEARINGS LIM",
      "VALVES LTD", "PUMPS LTD", "PUMPS LIM",
      "COMPRESSORS", "GEARS", "FASTENERS",
      "GABRIEL INDIA", "SUPRAJIT",
      "SCHAEFFLER INDIA"], "INDUSTRIAL_PRODUCTS"),

    # ── AVIATION (commercial airlines — after DEFENCE/AEROSPACE)
    (["INTERGLOBE AVIATION", "SPICEJET LTD",
      "AIR INDIA"], "AVIATION"),

    # ── LOGISTICS / TRANSPORT
    (["LOGISTICS LTD", "LOGISTICS LIM",
      "CARGO LTD", "CARGO LIM",
      "FREIGHT LTD", "FREIGHT LIM",
      "COURIER LTD", "COURIER LIM",
      "DELHIVERY LTD",
      "MAHINDRA LOGISTICS",
      "GATI LTD", "TCI EXPRESS",
      "CONTAINER CORP",
      "ALLCARGO", "TRANSPORT CORP"], "LOGISTICS"),

    # ── AUTO ANCILLARY (before AUTO)
    (["AUTO COMPONENTS",
      "TYRES LTD", "TYRE LTD",
      "TYRES LIM", "TYRE LIM",
      "BRAKES INDIA",
      "MINDA INDUSTRIES", "MINDA CORP",
      "SAMVARDHANA MOTHERSON",
      "BOSCH LTD", "BOSCH LIM",
      "EXIDE INDUSTRIES", "AMARA RAJA",
      "ENDURANCE TECH", "SONA BLW",
      "CRAFTSMAN AUTO",
      "SUPRAJIT ENGINEERING",
      "PRICOL LTD", "SANDHAR TECH",
      "FIEM INDUSTRIES"], "AUTO_ANCILLARY"),

    # ── AUTO
    (["MOTORS LTD", "MOTORS LIM",
      "AUTOMOBILES LTD", "AUTOMOBILES LIM",
      "AUTOMOTIVE LTD", "AUTOMOTIVE LIM",
      "TRACTORS LTD", "TRACTORS LIM",
      "MARUTI SUZUKI", "TATA MOTORS",
      "EICHER MOTORS", "HERO MOTOCORP",
      "BAJAJ AUTO", "TVS MOTOR",
      "ESCORTS KUBOTA", "FORCE MOTORS",
      "MAHINDRA & MAHINDRA"], "AUTO"),

    # ── DIAGNOSTICS (before HEALTHCARE)
    (["DIAGNOSTIC", "DIAGNOSTICS",
      "PATHOLOGY", "RADIOLOGY",
      "METROPOLIS HEALTHCARE",
      "DR LAL PATHLABS", "THYROCARE",
      "VIJAYA DIAGNOSTIC",
      "HEALTHONS"], "DIAGNOSTICS"),

    # ── HEALTHCARE (hospitals / services)
    (["HOSPITALS LTD", "HOSPITALS LIM",
      "HEALTHCARE LTD", "HEALTHCARE LIM",
      "HEALTH CARE LTD", "HEALTH CARE LIM",
      "MEDANTA", "APOLLO HOSPITALS",
      "FORTIS HEALTHCARE", "MAX HEALTHCARE",
      "NARAYANA HRUDAYALAYA",
      "ASTER DM HEALTHCARE",
      "GLOBAL HEALTH", "KIMS HOSPITALS",
      "YATHARTH HOSPITAL"], "HEALTHCARE"),

    # ── PHARMA
    (["PHARMA LTD", "PHARMA LIM",
      "PHARMACEUTICAL",
      "SUN PHARMA", "DR REDDY",
      "DIVI'S LABORATORIES",
      "LABORATORIES LTD", "LABORATORIES LIM",
      "BIOCON LTD", "SYNGENE",
      "LUPIN LTD", "CIPLA LTD",
      "ALKEM LABORATORIES",
      "IPCA LABORATORIES",
      "AJANTA PHARMA", "GRANULES",
      "NEULAND LABORATORIES",
      "LAURUS LABS", "GLAND PHARMA",
      "NATCO PHARMA", "CAPLIN POINT",
      "STRIDES PHARMA"], "PHARMA"),

    # ── SPECIALTY CHEMICALS (before CHEMICALS)
    (["SPECIALTY CHEMICALS", "SPECIALITY CHEMICALS",
      "FINE CHEMICALS",
      "PI INDUSTRIES", "DEEPAK NITRITE",
      "NAVIN FLUORINE", "CLEAN SCIENCE",
      "ROSSARI BIOTECH", "VINATI ORGANICS",
      "BALAJI AMINES", "LAXMI ORGANIC",
      "AGROCHEMICAL", "PESTICIDES",
      "INSECTICIDES", "HERBICIDES",
      "BAYER CROPSCIENCE", "UPL LTD",
      "DHANUKA AGRITECH"], "SPECIALTY_CHEMICALS"),

    # ── CHEMICALS
    (["CHEMICALS LTD", "CHEMICALS LIM",
      "ORGANICS LTD", "ORGANICS LIM",
      "PETROCHEMICALS LTD",
      "TATA CHEMICALS", "GUJARAT FLUORO",
      "AARTI INDUSTRIES",
      "KIRI INDUSTRIES",
      "SUDARSHAN CHEMICAL"], "CHEMICALS"),

    # ── CEMENT
    (["CEMENT LTD", "CEMENT LIM",
      "ULTRATECH CEMENT",
      "AMBUJA CEMENTS", "ACC LTD",
      "SHREE CEMENT", "DALMIA BHARAT",
      "RAMCO CEMENTS", "NUVOCO VISTAS",
      "INDIA CEMENTS", "HEIDELBERG",
      "BIRLA CORP", "STAR CEMENT",
      "MANGALAM CEMENT"], "CEMENT"),

    # ── METALS
    (["STEEL LTD", "STEEL LIM",
      "IRON & STEEL",
      "ALUMINIUM LTD", "ALUMINIUM LIM",
      "ALUMINUM", "COPPER LTD", "COPPER LIM",
      "ZINC LTD", "ZINC LIM",
      "STAINLESS STEEL", "TINPLATE",
      "TATA STEEL", "JSPL LTD",
      "STEEL AUTHORITY", "SAIL ",
      "HINDALCO INDUSTRIES",
      "NATIONAL ALUMINIUM", "NALCO ",
      "VEDANTA LTD", "HINDUSTAN COPPER",
      "HINDUSTAN ZINC",
      "JINDAL STAINLESS",
      "APL APOLLO TUBES",
      "RATNAMANI METALS"], "METALS"),

    # ── SUGAR
    (["SUGAR LTD", "SUGAR LIM",
      "ETHANOL LTD", "ETHANOL LIM",
      "DISTILLERY LTD", "DISTILLERY LIM",
      "BAJAJ HINDUSTHAN",
      "BALRAMPUR CHINI",
      "DWARIKESH SUGAR",
      "TRIVENI ENGINEERING"], "SUGAR"),

    # ── FERTILIZERS
    (["FERTILIZER", "FERTILISER",
      "UREA LTD", "POTASH LTD",
      "CHAMBAL FERTILISERS",
      "COROMANDEL INTERNATIONAL",
      "GSFC ", "GNFC ", "RCF LTD",
      "DEEPAK FERTILISERS",
      "NATIONAL FERTILIZERS"], "FERTILIZERS"),

    # ── AGRI
    (["SEEDS LTD", "SEEDS LIM",
      "KAVERI SEED",
      "AGRICULTURE LTD", "AGRI LTD",
      "CROP LTD", "FARM TECH",
      "RALLIS INDIA"], "AGRI"),

    # ── RETAIL
    (["RETAIL LTD", "RETAIL LIM",
      "SUPERMARKET", "HYPERMARKET",
      "E-COMMERCE", "ECOMMERCE",
      "ZOMATO LTD", "NYKAA",
      "FSN E-COMMERCE",
      "VEDANT FASHIONS", "TRENT LTD",
      "AVENUE SUPERMARTS", "DMART",
      "SHOPPERS STOP",
      "V2 RETAIL", "ADITYA BIRLA FASHION",
      "SAPPHIRE FOODS", "DEVYANI INTERNAT",
      "WESTLIFE FOODWORLD"], "RETAIL"),

    # ── HOSPITALITY
    (["HOTELS LTD", "HOTELS LIM",
      "RESORT LTD", "RESORT LIM",
      "HOSPITALITY LTD", "HOSPITALITY LIM",
      "LEMON TREE HOTELS",
      "INDIAN HOTELS", "EIH LTD",
      "CHALET HOTELS",
      "MAHINDRA HOLIDAYS",
      "ROYAL ORCHID",
      "WONDERLA HOLIDAYS"], "HOSPITALITY"),

    # ── CONSUMER DURABLES
    (["TITAN COMPANY", "VOLTAS LTD",
      "BLUE STAR LTD", "HAVELLS INDIA",
      "CROMPTON GREAVES CONSUMER",
      "BAJAJ ELECTRICALS",
      "SYMPHONY LTD", "ORIENT ELECTRIC",
      "AMBER ENTERPRISES",
      "DIXON TECHNOLOGIES",
      "PG ELECTROPLAST",
      "KALYANI STEELS"], "CONSUMER_DURABLES"),

    # ── FMCG (broad consumption catch-all)
    (["HINDUSTAN UNILEVER",
      "NESTLE INDIA", "ITC LTD",
      "COLGATE PALMOLIVE",
      "DABUR INDIA", "MARICO LTD",
      "GODREJ CONSUMER",
      "EMAMI LTD", "BAJAJ CONSUMER",
      "BRITANNIA INDUSTRIES",
      "VARUN BEVERAGES",
      "TATA CONSUMER",
      "RADICO KHAITAN",
      "UNITED SPIRITS",
      "GILLETTE INDIA",
      "FOODS LTD", "FOODS LIM",
      "BEVERAGES LTD", "BEVERAGES LIM",
      "CONFECTIONERY", "DAIRY LTD",
      "EDIBLE OIL", "CIGARETTE",
      "SOAP LTD", "DETERGENT LTD",
      "PERSONAL CARE"], "FMCG"),

    # ── DIGITAL SERVICES (late catch — after IT)
    (["DIGITAL SERVICES", "BPO LTD",
      "BPM LTD", "KPO LTD",
      "MEDIATEC", "MEDIA LTD"], "DIGITAL_SERVICES"),

    # ── INDUSTRIAL MANUFACTURING (generic catch — must be LAST)
    (["INDUSTRIES LTD", "INDUSTRIES LIM",
      "INDUSTRIAL LTD", "INDUSTRIAL LIM",
      "MANUFACTURING LTD", "MANUFACTURING LIM",
      "FABRICATORS LTD", "FABRICATORS LIM"], "INDUSTRIAL_MANUFACTURING"),
]


# ==============================================================
# UTILITIES
# ==============================================================

def write_log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} | {message}\n")


def load_nse_industry_data() -> pd.DataFrame:
    """
    Try to load NSE index constituent files that contain industry data.
    Returns empty DataFrame if none found.
    """
    for path in NSE_INDUSTRY_SOURCES:
        if path.exists():
            try:
                df = pd.read_csv(path)
                df.columns = [c.strip().upper() for c in df.columns]
                # NSE constituent files typically have: Symbol, Industry, ISIN
                if "SYMBOL" in df.columns and "INDUSTRY" in df.columns:
                    df = df[["SYMBOL", "INDUSTRY"]].copy()
                    df["SYMBOL"]   = df["SYMBOL"].str.strip().str.upper()
                    df["INDUSTRY"] = df["INDUSTRY"].str.strip().str.upper()
                    write_log(f"NSE industry data loaded: {path.name} ({len(df)} rows)")
                    return df
            except Exception as e:
                write_log(f"Could not load {path.name}: {e}")
    return pd.DataFrame()


def classify_by_nse_industry(industry: str) -> str:
    """Map NSE industry string to platform sector."""
    if not isinstance(industry, str):
        return "UNKNOWN"
    industry_upper = industry.strip().upper()
    return NSE_INDUSTRY_TO_SECTOR.get(industry_upper, "UNKNOWN")


def classify_by_keywords(company_name: str) -> str:
    """
    Apply keyword rules to company name.
    Returns sector name or 'UNKNOWN'.
    """
    if not isinstance(company_name, str):
        return "UNKNOWN"
    name_upper = company_name.strip().upper()
    for keywords, sector in KEYWORD_RULES:
        for kw in keywords:
            if kw.upper() in name_upper:
                return sector
    return "UNKNOWN"


# ==============================================================
# MAIN
# ==============================================================

def main():

    print("\n=== AUTO CLASSIFICATION ENGINE V2 ===\n")
    write_log("START")

    # ----------------------------------------------------------
    # LOAD EQUITY MASTER
    # ----------------------------------------------------------
    equity = pd.read_csv(EQUITY_MASTER)
    equity["SYMBOL"]       = equity["SYMBOL"].str.strip().str.upper()
    equity["COMPANY_NAME"] = equity["COMPANY_NAME"].str.strip()

    # Only classify EQ series (main tradeable universe)
    eq_universe = equity[equity["SERIES"] == "EQ"].copy()
    total = len(eq_universe)
    write_log(f"EQ Universe={total}")
    print(f"EQ Universe      : {total} symbols")

    # ----------------------------------------------------------
    # LAYER 1: NSE INDUSTRY DATA (primary — most accurate)
    # ----------------------------------------------------------
    nse_industry_df = load_nse_industry_data()
    layer1_count = 0

    if not nse_industry_df.empty:
        eq_universe = eq_universe.merge(
            nse_industry_df, on="SYMBOL", how="left"
        )
        eq_universe["SECTOR"] = eq_universe["INDUSTRY"].apply(
            classify_by_nse_industry
        )
        layer1_count = int((eq_universe["SECTOR"] != "UNKNOWN").sum())
        print(f"Layer 1 (NSE Industry) : {layer1_count} classified")
        write_log(f"Layer1 (NSE Industry)={layer1_count}")
    else:
        eq_universe["SECTOR"] = "UNKNOWN"
        print("Layer 1 (NSE Industry) : No file found — skipping")
        print(
            "  Tip: Download NSE index constituent list from:\n"
            "  NSE -> Equity -> Indices -> Nifty Total Market -> Download (CSV)\n"
            "  Place as: data/NSE/equity_master/ind_niftytotalmarket_list.csv"
        )

    # ----------------------------------------------------------
    # LAYER 2: KEYWORD RULES (fallback for unclassified)
    # ----------------------------------------------------------
    unclassified_mask = eq_universe["SECTOR"] == "UNKNOWN"
    eq_universe.loc[unclassified_mask, "SECTOR"] = (
        eq_universe.loc[unclassified_mask, "COMPANY_NAME"]
        .apply(classify_by_keywords)
    )
    layer2_count = int(
        (eq_universe["SECTOR"] != "UNKNOWN").sum() - layer1_count
    )
    print(f"Layer 2 (Keywords)     : {layer2_count} additional classified")
    write_log(f"Layer2 (Keywords)={layer2_count}")

    # ----------------------------------------------------------
    # BUILD OUTPUT FILES
    # ----------------------------------------------------------
    classified   = eq_universe[eq_universe["SECTOR"] != "UNKNOWN"].copy()
    unclassified = eq_universe[eq_universe["SECTOR"] == "UNKNOWN"].copy()

    total_classified = len(classified)
    coverage_pct     = round(total_classified / total * 100, 1)

    # company_classification.csv
    output_cols = ["SYMBOL", "COMPANY_NAME", "SECTOR"]
    classified["SOURCE"]       = "AUTO_V2"
    classified["LAST_UPDATED"] = datetime.now().strftime("%Y-%m-%d")
    classified_out = classified[
        ["SYMBOL", "COMPANY_NAME", "SECTOR", "SOURCE", "LAST_UPDATED"]
    ].sort_values("SYMBOL")
    classified_out.to_csv(
        REFERENCE_DIR / "company_classification.csv", index=False
    )

    # classification_review_queue.csv
    unclassified["STATUS"] = "PENDING"
    unclassified[["SYMBOL", "COMPANY_NAME", "STATUS"]].sort_values(
        "SYMBOL"
    ).to_csv(
        REFERENCE_DIR / "classification_review_queue.csv", index=False
    )

    # classification coverage report
    sector_dist = (
        classified.groupby("SECTOR")
        .size()
        .reset_index(name="COUNT")
        .sort_values("COUNT", ascending=False)
    )
    coverage_report = pd.DataFrame([{
        "TOTAL_SYMBOLS":       total,
        "CLASSIFIED_SYMBOLS":  total_classified,
        "PENDING_SYMBOLS":     len(unclassified),
        "COVERAGE_PERCENT":    coverage_pct,
        "LAYER1_NSE_INDUSTRY": layer1_count,
        "LAYER2_KEYWORDS":     layer2_count,
        "RUN_DATE":            datetime.now().strftime("%Y-%m-%d"),
    }])
    coverage_report.to_csv(
        REFERENCE_DIR / "classification_coverage_report.csv", index=False
    )
    sector_dist.to_csv(
        REFERENCE_DIR / "sector_distribution.csv", index=False
    )

    # ----------------------------------------------------------
    # LOGGING & CONSOLE OUTPUT
    # ----------------------------------------------------------
    write_log(f"Classified={total_classified}")
    write_log(f"Pending={len(unclassified)}")
    write_log(f"Coverage={coverage_pct}%")
    write_log("COMPLETE")

    print(f"\nResults:")
    print(f"  Classified  : {total_classified} / {total}")
    print(f"  Coverage    : {coverage_pct}%")
    print(f"  Review queue: {len(unclassified)} symbols")

    print(f"\nSector Distribution (top 15):")
    print(sector_dist.head(15).to_string(index=False))

    print(f"\nOutputs:")
    print(f"  company_classification.csv")
    print(f"  classification_review_queue.csv")
    print(f"  classification_coverage_report.csv")
    print(f"  sector_distribution.csv")


if __name__ == "__main__":
    main()
