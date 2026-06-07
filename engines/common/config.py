"""
Platform Configuration
Single source of truth for paths and runtime settings.
"""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
NSE_DIR = DATA_DIR / "NSE"
CACHE_DIR = DATA_DIR / "cache"
REFERENCE_DIR = DATA_DIR / "reference"
INTELLIGENCE_DIR = DATA_DIR / "intelligence"
LOG_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"
BHAVCOPY_DIR = NSE_DIR / "bhavcopy"
INDICES_DIR = NSE_DIR / "indices"
REPORTS_DIR = NSE_DIR / "reports"
EQUITY_MASTER_DIR = NSE_DIR / "equity_master"
RESULTS_DIR = NSE_DIR / "results"
CORPORATE_ACTIONS_DIR = NSE_DIR / "corporate_actions"
SHAREHOLDING_DIR = NSE_DIR / "shareholding"
STOCK_HISTORY_CACHE = CACHE_DIR / "stock_history"
REPORT_CACHE = CACHE_DIR / "reports"
API_TIMEOUT = 30
API_DELAY = 1.0
MAX_RETRIES = 3
RETRY_DELAY = 3
DIRECTORIES = [DATA_DIR,NSE_DIR,CACHE_DIR,REFERENCE_DIR,INTELLIGENCE_DIR,LOG_DIR]
for directory in DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)
