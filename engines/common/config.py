"""
Platform Configuration
Single source of truth for paths and runtime settings.
"""

from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root — makes TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY etc.
# available via os.getenv() in every engine without manual shell export.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

# ==========================================================
# PROJECT ROOT
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ==========================================================
# DATA ROOT
# ==========================================================

DATA_DIR = PROJECT_ROOT / "data"

NSE_DIR = DATA_DIR / "NSE"
BSE_DIR = DATA_DIR / "BSE"

CACHE_DIR = NSE_DIR / "nsecache"

REFERENCE_DIR = DATA_DIR / "reference"
INTELLIGENCE_DIR = DATA_DIR / "intelligence"

# ==========================================================
# DOCUMENTATION / LOGS
# ==========================================================

LOG_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"

# ==========================================================
# NSE PATHS
# ==========================================================

BHAVCOPY_DIR = NSE_DIR / "bhavcopy"

NSE_EQUITY_BHAVCOPY_DIR = BHAVCOPY_DIR / "equity"
NSE_FNO_BHAVCOPY_DIR = BHAVCOPY_DIR / "fno"

INDICES_DIR = NSE_DIR / "indices"
REPORTS_DIR = NSE_DIR / "reports"

EQUITY_MASTER_DIR = NSE_DIR / "equity_master"

CORPORATE_ACTIONS_DIR = NSE_DIR / "corporate_actions"
RESULTS_DIR = NSE_DIR / "results"
SHAREHOLDING_DIR = NSE_DIR / "shareholding"
ADJUSTED_EQUITY_DIR = NSE_DIR / "adjusted_equity"

# ==========================================================
# BSE PATHS (Future)
# ==========================================================

BSE_BHAVCOPY_DIR = BSE_DIR / "bhavcopy"

BSE_EQUITY_BHAVCOPY_DIR = BSE_BHAVCOPY_DIR / "equity"
BSE_FNO_BHAVCOPY_DIR = BSE_BHAVCOPY_DIR / "fno"

# ==========================================================
# CACHE
# ==========================================================

STOCK_HISTORY_CACHE = CACHE_DIR / "stock_history"
REPORT_CACHE = CACHE_DIR / "reports"

# ==========================================================
# HOLIDAYS
# ==========================================================

NSE_HOLIDAY_FILE = REFERENCE_DIR / "nse_holidays.csv"


# ==========================================================
# ACQUISITION SETTINGS
# ==========================================================

NSE_EQUITY_START_YEAR = 1995
NSE_FNO_START_YEAR = 2000
CORPORATE_ACTION_START_YEAR = 1995

# ============================================================
# VALIDATION WINDOWS
# ============================================================

NSE_EQUITY_VALIDATION_YEARS = 5
NSE_FNO_VALIDATION_YEARS = 5

# ============================================================
# WORKERS
# ============================================================

MIN_CONCURRENCY = 4
MAX_CONCURRENCY = 6

# ============================================================
# OUTPUT
# ============================================================

WRITE_CSV = True
WRITE_PARQUET = True

API_TIMEOUT = 30
API_DELAY = 1.0

MAX_RETRIES = 3
RETRY_DELAY = 3

# ==========================================================
# DIRECTORY INITIALIZATION
# ==========================================================

DIRECTORIES = [
    DATA_DIR,
    NSE_DIR,
    BSE_DIR,
    CACHE_DIR,
    REFERENCE_DIR,
    INTELLIGENCE_DIR,
    LOG_DIR,

    NSE_EQUITY_BHAVCOPY_DIR,
    NSE_FNO_BHAVCOPY_DIR,

    BSE_EQUITY_BHAVCOPY_DIR,
    BSE_FNO_BHAVCOPY_DIR,

    EQUITY_MASTER_DIR,
    CORPORATE_ACTIONS_DIR,
    ADJUSTED_EQUITY_DIR,
]

for directory in DIRECTORIES:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )