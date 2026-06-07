from pathlib import Path
import pandas as pd
def ensure_directory(path:Path):
    path.mkdir(parents=True, exist_ok=True)
def safe_read_csv(path:Path)->pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
def safe_write_csv(df:pd.DataFrame,path:Path,index:bool=False):
    ensure_directory(path.parent)
    df.to_csv(path,index=index)
def backup_file(path:Path):
    if path.exists():
        path.replace(path.with_suffix(".bak"))
def get_latest_file(directory:Path,pattern:str):
    files=list(directory.glob(pattern))
    return max(files,key=lambda x:x.stat().st_mtime) if files else None
