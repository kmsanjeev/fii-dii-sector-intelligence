import time,requests
from engines.common.config import API_TIMEOUT,MAX_RETRIES,RETRY_DELAY
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
def create_session():
    s=requests.Session(); s.headers.update(HEADERS)
    try: s.get("https://www.nseindia.com",timeout=API_TIMEOUT)
    except Exception: pass
    return s
def get(session,url):
    for _ in range(MAX_RETRIES):
        try:
            r=session.get(url,timeout=API_TIMEOUT); r.raise_for_status(); return r
        except Exception:
            time.sleep(RETRY_DELAY)
    return None
