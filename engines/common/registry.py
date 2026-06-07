from datetime import datetime
import pandas as pd
from engines.common.config import DATA_DIR
REGISTRY_FILE=DATA_DIR/"engine_registry.csv"
def update_registry(engine:str,status:str,rows_processed:int=0,errors:int=0):
    record=pd.DataFrame([{"ENGINE":engine,"RUN_TIME":datetime.now(),"STATUS":status,"ROWS_PROCESSED":rows_processed,"ERRORS":errors}])
    if REGISTRY_FILE.exists():
        existing=pd.read_csv(REGISTRY_FILE)
        existing=pd.concat([existing,record],ignore_index=True)
        existing.to_csv(REGISTRY_FILE,index=False)
    else:
        record.to_csv(REGISTRY_FILE,index=False)
