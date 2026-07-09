"""
Order Slicer -- Phase R4
ADV participation check + TWAP slice plans for orders too large for one print.

Rule: an order should not exceed max_adv_participation_pct (default 5%) of the
symbol's 20-day average daily volume. Larger orders get a TWAP plan: equal
child slices spread across the NSE session (09:15-15:30), each slice within
the participation limit.

Config key (data/execution/execution_config.json, managed by risk_engine):
  max_adv_participation_pct   default 5.0

Reads (read-only, G-D-01):
  data/cache/stock_history/{SYMBOL}.parquet   20d ADV from volume column

This module never places orders -- it produces plans and warnings only.
"""

import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.execution.risk_engine import load_config

logger = get_logger(__name__)

DEFAULT_MAX_PARTICIPATION_PCT = 5.0
ADV_WINDOW_DAYS  = 20
SESSION_START    = (9, 15)
SESSION_END      = (15, 30)
MIN_SLICES       = 2
MAX_SLICES       = 12


@dataclass
class ParticipationCheck:
    symbol:                str
    qty:                   int
    adv_20d:               float          # 20d average daily volume (shares)
    participation_pct:     float          # order qty as % of ADV
    max_participation_pct: float
    exceeds:               bool


@dataclass
class Slice:
    slice_no:     int
    time_ist:     str        # HH:MM suggested release time
    qty:          int
    pct_of_order: float


def get_adv(symbol: str, window: int = ADV_WINDOW_DAYS) -> float | None:
    """20-day average daily volume from the parquet cache. None if unavailable."""
    pq = cfg.STOCK_HISTORY_CACHE / f"{symbol.upper()}.parquet"
    if not pq.exists():
        return None
    try:
        df = pd.read_parquet(pq, columns=["date", "volume"])
    except Exception:
        return None
    vol = pd.to_numeric(df["volume"], errors="coerce").dropna()
    vol = vol[vol > 0]
    if len(vol) < window // 2:      # need at least half the window
        return None
    return float(vol.tail(window).mean())


def check_participation(symbol: str, qty: int) -> ParticipationCheck | None:
    """Order size vs ADV limit. None when ADV cannot be computed (no data)."""
    adv = get_adv(symbol)
    if adv is None or adv <= 0:
        return None
    max_pct = float(load_config().get("max_adv_participation_pct",
                                      DEFAULT_MAX_PARTICIPATION_PCT))
    pct = qty / adv * 100.0
    return ParticipationCheck(
        symbol                = symbol.upper(),
        qty                   = qty,
        adv_20d               = round(adv, 0),
        participation_pct     = round(pct, 2),
        max_participation_pct = max_pct,
        exceeds               = pct > max_pct,
    )


def build_twap_plan(symbol: str, qty: int) -> dict:
    """
    TWAP slice plan: equal child orders across the session, each within the
    participation limit. For orders already inside the limit, returns a
    single-slice plan (no slicing needed).
    """
    check = check_participation(symbol, qty)
    if check is None:
        return {
            "symbol": symbol.upper(), "qty": qty,
            "error": f"No volume history for {symbol.upper()} -- cannot compute ADV",
        }

    if not check.exceeds:
        return {
            **asdict(check),
            "slices_needed": False,
            "slices": [asdict(Slice(1, _session_times(1)[0], qty, 100.0))],
            "note": "Order within participation limit -- single print is fine",
        }

    # Max shares per slice that stays inside the limit
    max_per_slice = int(check.adv_20d * check.max_participation_pct / 100.0)
    n = -(-qty // max(max_per_slice, 1))          # ceil division
    n = max(MIN_SLICES, min(MAX_SLICES, n))

    base, rem = divmod(qty, n)
    times = _session_times(n)
    slices = []
    for i in range(n):
        q = base + (1 if i < rem else 0)
        slices.append(asdict(Slice(
            slice_no     = i + 1,
            time_ist     = times[i],
            qty          = q,
            pct_of_order = round(q / qty * 100.0, 1),
        )))

    per_slice_pct = round(slices[0]["qty"] / check.adv_20d * 100.0, 2)
    note = (f"{n} TWAP slices across the session; largest slice = "
            f"{per_slice_pct}% of 20d ADV")
    if per_slice_pct > check.max_participation_pct:
        note += (f" -- still above the {check.max_participation_pct:.0f}% limit even at "
                 f"{MAX_SLICES} slices; consider spreading over multiple days")

    return {**asdict(check), "slices_needed": True, "slices": slices, "note": note}


def _session_times(n: int) -> list[str]:
    """n evenly spaced release times across 09:15-15:30 IST (first at open+5m)."""
    start = datetime(2000, 1, 1, SESSION_START[0], SESSION_START[1]) + timedelta(minutes=5)
    end   = datetime(2000, 1, 1, SESSION_END[0], SESSION_END[1]) - timedelta(minutes=10)
    if n == 1:
        return [start.strftime("%H:%M")]
    step = (end - start) / (n - 1)
    return [(start + i * step).strftime("%H:%M") for i in range(n)]


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE"
    q   = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
    import json
    print(json.dumps(build_twap_plan(sym, q), indent=2))
