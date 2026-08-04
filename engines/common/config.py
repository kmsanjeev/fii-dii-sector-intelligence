"""
Platform Configuration
Single source of truth for paths and runtime settings.
"""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for lean runtime envs
    def load_dotenv(*args, **kwargs):  # type: ignore[override]
        return False

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


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    return raw.strip() if raw and raw.strip() else default

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
FPI_DIR = NSE_DIR / "fpi"

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
# VEDA RESEARCH / ATTACHMENTS
# ==========================================================

VEDA_CACHE_DIR = DATA_DIR / "veda"
VEDA_RESEARCH_CACHE_DIR = VEDA_CACHE_DIR / "research_cache"
VEDA_CHAT_UPLOAD_DIR = VEDA_CACHE_DIR / "uploads"

VEDA_RESEARCH_ENABLED = _env_bool("VEDA_RESEARCH_ENABLED", True)
VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT = _env_bool("VEDA_RESEARCH_AUTO_FOR_RESEARCH_INTENT", False)
VEDA_RESEARCH_PROVIDER = _env_str("VEDA_RESEARCH_PROVIDER", "ddgs")
VEDA_RESEARCH_REGION = _env_str("VEDA_RESEARCH_REGION", "in-en")
VEDA_RESEARCH_TIMEOUT_S = _env_int("VEDA_RESEARCH_TIMEOUT_S", 8)
VEDA_RESEARCH_MAX_RESULTS = _env_int("VEDA_RESEARCH_MAX_RESULTS", 5)
VEDA_RESEARCH_NEWS_RESULTS = _env_int("VEDA_RESEARCH_NEWS_RESULTS", 2)
VEDA_RESEARCH_MAX_QUERY_CHARS = _env_int("VEDA_RESEARCH_MAX_QUERY_CHARS", 320)
VEDA_RESEARCH_MAX_SNIPPET_CHARS = _env_int("VEDA_RESEARCH_MAX_SNIPPET_CHARS", 280)
VEDA_RESEARCH_CACHE_TTL_S = _env_int("VEDA_RESEARCH_CACHE_TTL_S", 900)
VEDA_ATTACHMENTS_ENABLED = _env_bool("VEDA_ATTACHMENTS_ENABLED", False)
VEDA_SAVE_TO_KNOWLEDGE_ENABLED = _env_bool("VEDA_SAVE_TO_KNOWLEDGE_ENABLED", False)
VEDA_MCP_ENABLED = _env_bool("VEDA_MCP_ENABLED", False)

# ==========================================================
# HOLIDAYS
# ==========================================================

NSE_HOLIDAY_FILE = REFERENCE_DIR / "nse_holidays.csv"
SPECIAL_SESSIONS_FILE = REFERENCE_DIR / "special_trading_sessions.csv"


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
    VEDA_CACHE_DIR,
    VEDA_RESEARCH_CACHE_DIR,
    VEDA_CHAT_UPLOAD_DIR,

    NSE_EQUITY_BHAVCOPY_DIR,
    NSE_FNO_BHAVCOPY_DIR,

    BSE_EQUITY_BHAVCOPY_DIR,
    BSE_FNO_BHAVCOPY_DIR,

    EQUITY_MASTER_DIR,
    CORPORATE_ACTIONS_DIR,
    ADJUSTED_EQUITY_DIR,
    FPI_DIR,
]

for directory in DIRECTORIES:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )
