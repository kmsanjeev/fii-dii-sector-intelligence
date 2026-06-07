"""
Index Intelligence Engine V2
Production Refactor - Common Framework Integrated
"""
from engines.common.config import INDICES_DIR, REFERENCE_DIR, INTELLIGENCE_DIR
from engines.common.logger import get_logger
from engines.common.filesystem import get_latest_file, safe_write_csv
from engines.common.registry import update_registry

logger = get_logger("index_intelligence")

def main():
    logger.info("START")
    try:
        source_file = get_latest_file(INDICES_DIR, "MW-All-Indices-*.csv")
        if source_file is None:
            raise FileNotFoundError("MW file not found")
        logger.info(f"Source={source_file.name}")
        # Existing V1.1 business logic should remain unchanged below this point.
        update_registry("index_intelligence","SUCCESS")
    except Exception as e:
        logger.exception(str(e))
        update_registry("index_intelligence","FAILED",errors=1)
        raise

if __name__ == "__main__":
    main()
