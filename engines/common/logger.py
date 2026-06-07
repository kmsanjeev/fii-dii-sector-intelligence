import logging
from engines.common.config import LOG_DIR
def get_logger(name:str)->logging.Logger:
    logger=logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter=logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh=logging.FileHandler(LOG_DIR / f"{name}.log",encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger
