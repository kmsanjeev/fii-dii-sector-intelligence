
"""
Leadership Persistence Engine V2
Architecture V2 Production Conversion
"""
from engines.common.config import INTELLIGENCE_DIR
from engines.common.logger import get_logger
from engines.common.registry import update_registry
import pandas as pd

logger=get_logger("leadership_persistence")
HISTORY_SCALE_THRESHOLD=20

def scale_conviction(raw,total_days):
    if total_days >= HISTORY_SCALE_THRESHOLD:
        return raw
    return round(raw*(total_days/HISTORY_SCALE_THRESHOLD),1)

def main():
    try:
        df=pd.read_csv(INTELLIGENCE_DIR/"history"/"index_snapshot.csv")
        df["SNAPSHOT_DATE"]=df["SNAPSHOT_DATE"].astype(str)
        update_registry("leadership_persistence","SUCCESS",rows_processed=len(df))
    except Exception:
        logger.exception("FAILED")
        update_registry("leadership_persistence","FAILED",errors=1)
        raise

if __name__=="__main__":
    main()
