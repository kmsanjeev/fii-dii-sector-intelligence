
"""
NSE Constituents Engine V1
Architecture V2 Native Build
"""
from engines.common.logger import get_logger
from engines.common.nse_client import create_session
from engines.common.registry import update_registry
from engines.common.config import REFERENCE_DIR
import pandas as pd

logger=get_logger("nse_constituents")

def main():
    try:
        session=create_session()
        registry=pd.DataFrame(columns=["INDEX_NAME","STATUS"])
        registry.to_csv(REFERENCE_DIR/"constituents_registry.csv",index=False)
        update_registry("nse_constituents","SUCCESS")
    except Exception:
        logger.exception("FAILED")
        update_registry("nse_constituents","FAILED",errors=1)
        raise

if __name__=="__main__":
    main()
