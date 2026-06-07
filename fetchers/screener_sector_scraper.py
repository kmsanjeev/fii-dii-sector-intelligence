# screener_sector_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re

# ----------------- CONFIG -----------------
OUTPUT_DIR = "screener_csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Use the sector codes you collected (paste full list here)
sector_codes = [
    "IN07/IN0702/IN070201",  # Aerospace & Defense
    "IN05/IN0501",           # Agricultural Vehicles
    "IN05/IN0502",           # Agricultural Food Products
    "IN06/IN0601",           # Auto Components
    "IN06/IN0602",           # Automobiles
    "IN08/IN0801",           # Banks
    "IN09/IN0901",           # Beverages
    "IN10/IN1001",           # Capital Markets
    "IN11/IN1101",           # Cement & Cement Products
    "IN12/IN1201",           # Chemicals & Petrochemicals
    "IN13/IN1301",           # Cigarettes & Tobacco
    "IN14/IN1401",           # Commercial Services & Supplies
    "IN15/IN1501",           # Construction
    "IN16/IN1601",           # Consumer Durables
    "IN17/IN1701",           # Diversified FMCG
    "IN18/IN1801",           # Electrical Equipment
    "IN19/IN1901",           # Entertainment
    "IN20/IN2001",           # Ferrous Metals
    "IN21/IN2101",           # Fertilizers & Agrochemicals
    "IN22/IN2201",           # Finance
    "IN23/IN2301",           # Food Products
    "IN24/IN2401",           # Gas
    "IN25/IN2501",           # Healthcare Services
    "IN26/IN2601",           # Household Products
    "IN27/IN2701",           # Industrial Manufacturing
    "IN28/IN2801",           # Insurance
    "IN29/IN2901",           # IT – Hardware
    "IN29/IN2902",           # IT – Services
    "IN29/IN2903",           # IT – Software
    "IN30/IN3001",           # Leisure Services
    "IN31/IN3101",           # Media
    "IN32/IN3201",           # Minerals & Mining
    "IN33/IN3301",           # Non-Ferrous Metals
    "IN34/IN3401",           # Oil
    "IN35/IN3501",           # Paper, Forest & Jute
    "IN36/IN3601",           # Personal Products
    "IN37/IN3701",           # Petroleum Products
    "IN38/IN3801",           # Pharmaceuticals & Biotechnology
    "IN39/IN3901",           # Power
    "IN40/IN4001",           # Printing & Publication
    "IN41/IN4101",           # Realty
    "IN42/IN4201",           # Retailing
    "IN43/IN4301",           # Telecom – Equipment
    "IN43/IN4302",           # Telecom – Services
    "IN44/IN4401",           # Textiles & Apparels
    "IN45/IN4501",           # Transport Infrastructure
    "IN45/IN4502",           # Transport Services
]

BASE_URL = "https://www.screener.in/market/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# ----------------- HELPERS -----------------
def clean_filename(s):
    s = re.sub(r'[\\/*?:"<>|]', "", s)
    s = s.strip().replace(" ", "_")
    return s[:120]

def fetch_sector_page(code):
    url = BASE_URL + code
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def parse_table(html):
    soup = BeautifulSoup(html, "lxml")
    # Screener uses table with class "data-table"
    table = soup.find("table", class_="data-table")
    if table is None:
        return None, None
    # headers
    headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]
    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        rows.append(cols)
    # derive sector name from page title
    title = soup.find("title").get_text(strip=True)
    sector_name = title.replace(" - Screener", "").strip()
    return sector_name, pd.DataFrame(rows, columns=headers)

# ----------------- MAIN -----------------
def main():
    saved_files = []
    for code in sector_codes:
        try:
            print("Fetching:", code)
            html = fetch_sector_page(code)
            sector_name, df = parse_table(html)
            if df is None:
                print("No table found for", code)
                time.sleep(2)
                continue
            fname = clean_filename(sector_name) + ".csv"
            outpath = os.path.join(OUTPUT_DIR, fname)
            df.to_csv(outpath, index=False)
            saved_files.append(outpath)
            print("Saved:", outpath, "| rows:", len(df))
            time.sleep(1.5)  # polite delay
        except Exception as e:
            print("Error for", code, ":", str(e))
            time.sleep(3)

    # Merge all CSVs into one master file
    if saved_files:
        print("Merging", len(saved_files), "files into master.csv")
        dfs = []
        for f in saved_files:
            try:
                tmp = pd.read_csv(f)
                tmp.insert(0, "SectorFile", os.path.basename(f))
                dfs.append(tmp)
            except Exception as e:
                print("Skipping file on merge:", f, e)
        if dfs:
            master = pd.concat(dfs, ignore_index=True, sort=False)
            master.to_csv(os.path.join(OUTPUT_DIR, "master_screener_universe.csv"), index=False)
            print("Master saved:", os.path.join(OUTPUT_DIR, "master_screener_universe.csv"))

if __name__ == "__main__":
    main()
