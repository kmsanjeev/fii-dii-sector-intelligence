"""
Index Options Engine
Phase DMB-1 -- NIFTY / BANKNIFTY option-chain analytics from the FO bhavcopy.

For the NEAREST expiry of each index (UDiFF schema, FinInstrmTp=IDO):
  - PCR (total Put OI / total Call OI)
  - Max Pain (strike minimising total option-writer payout)
  - Top 3 Call-OI strikes (resistance) and Put-OI strikes (support)
  - Expected range (highest-Put-OI support .. highest-Call-OI resistance)
  - OI buildup vs prior day per side (from ChngInOpnIntrst)
  - Futures read: price change vs OI change -> LONG_BUILDUP / SHORT_BUILDUP
    / SHORT_COVERING / LONG_UNWINDING (nearest future, FinInstrmTp=IDF)

Reads (read-only, G-D-01):
  data/NSE/bhavcopy/fno/YYYY/fo_YYYYMMDD.csv   (latest file)

Writes (atomic, G-D-02):
  data/intelligence/index_options.csv

Run:  py -3.11 -m engines.briefing.index_options_engine
"""

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

OUTPUT_CSV = cfg.INTELLIGENCE_DIR / "index_options.csv"
INDEXES = ["NIFTY", "BANKNIFTY"]
COLS = ["index", "expiry", "key", "value", "note", "trade_date"]


def _latest_fo() -> Path | None:
    files = sorted(cfg.NSE_FNO_BHAVCOPY_DIR.glob("*/fo_*.csv"))
    return files[-1] if files else None


class IndexOptionsEngine:
    def run(self) -> bool:
        fo_path = _latest_fo()
        if fo_path is None:
            logger.warning("[IndexOptions] No FO bhavcopy found")
            return False
        logger.info("[IndexOptions] Using %s", fo_path.name)

        usecols = ["TradDt", "FinInstrmTp", "TckrSymb", "XpryDt", "StrkPric",
                   "OptnTp", "ClsPric", "PrvsClsgPric", "UndrlygPric",
                   "OpnIntrst", "ChngInOpnIntrst"]
        df = pd.read_csv(fo_path, usecols=usecols, low_memory=False)
        df["TckrSymb"] = df["TckrSymb"].astype(str).str.strip().str.upper()
        for c in ("StrkPric", "ClsPric", "PrvsClsgPric", "UndrlygPric",
                  "OpnIntrst", "ChngInOpnIntrst"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        trade_date = str(df["TradDt"].iloc[0])

        rows: list[dict] = []
        for idx in INDEXES:
            opts = df[(df["TckrSymb"] == idx) & (df["FinInstrmTp"] == "IDO")].copy()
            futs = df[(df["TckrSymb"] == idx) & (df["FinInstrmTp"] == "IDF")].copy()
            if opts.empty:
                rows.append({"index": idx, "expiry": "", "key": "status",
                             "value": None, "note": "N/A -- no option rows in FO file",
                             "trade_date": trade_date})
                continue

            # Nearest expiry only (the actively traded chain)
            opts["_xp"] = pd.to_datetime(opts["XpryDt"], errors="coerce")
            expiry = opts["_xp"].min()
            chain = opts[opts["_xp"] == expiry].dropna(subset=["StrkPric", "OpnIntrst"])
            exp_str = expiry.strftime("%Y-%m-%d")

            calls = chain[chain["OptnTp"] == "CE"]
            puts  = chain[chain["OptnTp"] == "PE"]
            call_oi, put_oi = float(calls["OpnIntrst"].sum()), float(puts["OpnIntrst"].sum())
            pcr = put_oi / call_oi if call_oi else None
            spot = float(chain["UndrlygPric"].dropna().iloc[0]) if chain["UndrlygPric"].notna().any() else None

            # Max pain: strike minimising intrinsic payout to option buyers
            strikes = np.sort(chain["StrkPric"].unique())
            coi = calls.groupby("StrkPric")["OpnIntrst"].sum()
            poi = puts.groupby("StrkPric")["OpnIntrst"].sum()
            pains = []
            for s in strikes:
                call_pain = float(((s - coi.index)[coi.index < s] * coi[coi.index < s]).sum())
                put_pain  = float(((poi.index - s)[poi.index > s] * poi[poi.index > s]).sum())
                pains.append(call_pain + put_pain)
            max_pain = float(strikes[int(np.argmin(pains))]) if pains else None

            top_calls = coi.sort_values(ascending=False).head(3)
            top_puts  = poi.sort_values(ascending=False).head(3)
            # Institutional definition: resistance = biggest call wall ABOVE
            # spot; support = biggest put wall BELOW spot. Without the spot
            # filter, a sparse far-expiry chain can put both walls on the
            # same strike (observed: BANKNIFTY 59000-59000 "range").
            if spot:
                coi_above = coi[coi.index > spot]
                poi_below = poi[poi.index < spot]
                resistance = float(coi_above.idxmax()) if len(coi_above) else \
                             (float(top_calls.index[0]) if len(top_calls) else None)
                support    = float(poi_below.idxmax()) if len(poi_below) else \
                             (float(top_puts.index[0]) if len(top_puts) else None)
            else:
                resistance = float(top_calls.index[0]) if len(top_calls) else None
                support    = float(top_puts.index[0]) if len(top_puts) else None

            # OI-change buildup per side (today's net change in the chain)
            call_doi = float(calls["ChngInOpnIntrst"].sum())
            put_doi  = float(puts["ChngInOpnIntrst"].sum())

            # Futures positioning: price change vs OI change on nearest future
            fut_read = None
            if not futs.empty:
                futs["_xp"] = pd.to_datetime(futs["XpryDt"], errors="coerce")
                f = futs.sort_values("_xp").iloc[0]
                pchg = (f["ClsPric"] / f["PrvsClsgPric"] - 1) if f["PrvsClsgPric"] else 0
                doi = f["ChngInOpnIntrst"] or 0
                fut_read = ("LONG_BUILDUP" if pchg > 0 and doi > 0 else
                            "SHORT_COVERING" if pchg > 0 and doi < 0 else
                            "SHORT_BUILDUP" if pchg < 0 and doi > 0 else
                            "LONG_UNWINDING" if pchg < 0 and doi < 0 else "FLAT")

            entries = [
                ("spot", round(spot, 1) if spot else None, "underlying at FO close"),
                ("pcr", round(pcr, 3) if pcr else None, "put OI / call OI, nearest expiry"),
                ("max_pain", max_pain, ""),
                ("support", support, "highest Put OI strike"),
                ("resistance", resistance, "highest Call OI strike"),
                ("expected_range", f"{support:.0f} - {resistance:.0f}"
                 if support and resistance else None, "put wall to call wall"),
                ("top_call_oi_strikes",
                 " | ".join(f"{int(s)}:{int(v/1e3)}k" for s, v in top_calls.items()), ""),
                ("top_put_oi_strikes",
                 " | ".join(f"{int(s)}:{int(v/1e3)}k" for s, v in top_puts.items()), ""),
                ("call_oi_change", int(call_doi), "chain net, today"),
                ("put_oi_change", int(put_doi), "chain net, today"),
                ("futures_read", fut_read, "price vs OI, nearest future"),
            ]
            for k, v, note in entries:
                rows.append({"index": idx, "expiry": exp_str, "key": k,
                             "value": v, "note": note, "trade_date": trade_date})
            logger.info("[IndexOptions] %s exp %s: PCR=%s maxpain=%s range=%s-%s fut=%s",
                        idx, exp_str, round(pcr, 2) if pcr else None,
                        max_pain, support, resistance, fut_read)

        if not rows:                                             # G-D-03
            return False
        out = pd.DataFrame(rows, columns=COLS)
        tmp = OUTPUT_CSV.with_suffix(".tmp.csv")                 # G-D-02
        out.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(OUTPUT_CSV))
        return True


if __name__ == "__main__":
    sys.exit(0 if IndexOptionsEngine().run() else 1)
