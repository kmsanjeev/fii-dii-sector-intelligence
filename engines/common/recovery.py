from pathlib import Path
import pandas as pd
def file_exists(path:Path)->bool:
    return path.exists()
def detect_corruption(path:Path)->bool:
    if not path.exists():
        return True
    try:
        pd.read_csv(path,nrows=5)
        return False
    except Exception:
        return True
def detect_missing_files(required_files:list[Path]):
    return [f for f in required_files if not f.exists()]
