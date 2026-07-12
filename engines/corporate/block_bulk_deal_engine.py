"""
Block/Bulk Deal Intelligence Engine
Phase 7A — Institutional deal tracking at stock level

Downloads block and bulk deal history from NSE, classifies each client as
FII / MF / INSURANCE / PROMOTER / RETAIL, aggregates 30D net institutional
buying per symbol, and produces a deal signal per stock.

Block deals : qty >= 5 lakh shares OR value >= Rs 5 Cr on the BSE/NSE block window
Bulk deals  : qty >= 0.5% of total listed equity of the company

Outputs:
  data/intelligence/block_bulk_deals.csv        — raw history (incremental)
  data/intelligence/institutional_deal_signals.csv — per-symbol rolling signals
  data/intelligence/deal_records.csv            — sequence-paired client transactions

Guardrails: G-A-01, G-A-02, G-A-03, G-D-02, G-D-03
"""

import re
import shutil
import time
from pathlib import Path
import sys

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("block_bulk_deal")

INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
DEALS_HISTORY    = INTELLIGENCE_DIR / "block_bulk_deals.csv"
SIGNALS_OUTPUT   = INTELLIGENCE_DIR / "institutional_deal_signals.csv"
RECORDS_OUTPUT   = INTELLIGENCE_DIR / "deal_records.csv"
RECOVERY_QUEUE   = INTELLIGENCE_DIR / "corporate_recovery_queue.csv"

ROLLING_WINDOW_DAYS = 30

# Sequence-paired transaction matching (Phase UI-C fix): NSE publishes
# block/bulk deals at trade-DATE granularity only, with no intraday
# timestamp. The order rows are disclosed in NSE's own file -- preserved
# end to end via seq_id (see run(), never re-sorted by symbol/client) -- is
# the only available proxy for "which transaction happened first" when a
# client appears on both sides the same day.
QTY_TOLERANCE = 0.01  # 1% relative -- catches same-position rounding/partial-fill
                       # noise (e.g. 9,248,751 vs 9,248,816 shares) without
                       # pairing unrelated trades of different size


def _find_fifo_match(open_legs: list, qty: float, tol: float):
    """First open leg (earliest seq_id -- the list is append-ordered) whose
    quantity is within `tol` relative difference of `qty`."""
    for i, leg in enumerate(open_legs):
        if abs(leg["qty"] - qty) / max(leg["qty"], qty) <= tol:
            return i
    return None


def _make_pair_record(date, symbol, company, client, participant, entry, exit_, record_type) -> dict:
    entry_dir, exit_dir = ("SELL", "BUY") if record_type == "SHORT_BUILD_COVER" else ("BUY", "SELL")
    buy_leg, sell_leg = (exit_, entry) if entry_dir == "SELL" else (entry, exit_)
    net_value_cr = (sell_leg["qty"] * sell_leg["price"] - buy_leg["qty"] * buy_leg["price"]) / 1e7
    pnl_pct = (
        (exit_["price"] - entry["price"]) / entry["price"] * 100 if record_type == "LONG_BUILD_SQUAREOFF"
        else (entry["price"] - exit_["price"]) / entry["price"] * 100
    )
    qty_match_pct = min(entry["qty"], exit_["qty"]) / max(entry["qty"], exit_["qty"]) * 100
    return {
        "date": date, "symbol": symbol, "company": company,
        "client_name": client, "participant": participant,
        "record_type": record_type,
        "leg1_dir": entry_dir, "leg1_qty": entry["qty"], "leg1_price": entry["price"], "leg1_seq": entry["seq_id"],
        "leg2_dir": exit_dir,  "leg2_qty": exit_["qty"],  "leg2_price": exit_["price"],  "leg2_seq": exit_["seq_id"],
        "pnl_pct": round(pnl_pct, 2),
        "net_value_cr": round(net_value_cr, 4),
        "gross_value_cr": round((entry["qty"] * entry["price"] + exit_["qty"] * exit_["price"]) / 1e7, 4),
        "qty_match_pct": round(qty_match_pct, 2),
    }


def _make_standalone_record(date, symbol, company, client, participant, leg, direction, record_type) -> dict:
    value_cr = round(leg["qty"] * leg["price"] / 1e7, 4)
    return {
        "date": date, "symbol": symbol, "company": company,
        "client_name": client, "participant": participant,
        "record_type": record_type,
        "leg1_dir": direction, "leg1_qty": leg["qty"], "leg1_price": leg["price"], "leg1_seq": leg["seq_id"],
        "leg2_dir": None, "leg2_qty": None, "leg2_price": None, "leg2_seq": None,
        "pnl_pct": None,
        "net_value_cr": value_cr if direction == "BUY" else -value_cr,
        "gross_value_cr": value_cr,
        "qty_match_pct": None,
    }


def pair_client_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Within each (date, symbol, client) group, walk deals in seq_id order and
    pair opposite-direction legs whose quantity matches within QTY_TOLERANCE,
    FIFO. Whichever leg has the lower seq_id is the entry:
      entry BUY  -> exit SELL : LONG_BUILD_SQUAREOFF
      entry SELL -> exit BUY  : SHORT_BUILD_COVER
    A client can have multiple round trips in a day -- each matched pair
    becomes its own record. Legs left unmatched at the end of the group
    become standalone BUY_ONLY / SELL_ONLY records.
    """
    records = []
    for (date, symbol, company, client, participant), grp in df.groupby(
        ["date", "symbol", "company", "client_name", "participant"], sort=False
    ):
        grp = grp.sort_values("seq_id")
        open_buys: list[dict] = []
        open_sells: list[dict] = []

        for row in grp.itertuples(index=False):
            leg = {"qty": float(row.qty), "price": float(row.price),
                   "seq_id": int(row.seq_id), "deal_type": row.deal_type}
            if row.direction == "BUY":
                m = _find_fifo_match(open_sells, leg["qty"], QTY_TOLERANCE)
                if m is not None:
                    entry = open_sells.pop(m)
                    records.append(_make_pair_record(date, symbol, company, client, participant,
                                                       entry, leg, "SHORT_BUILD_COVER"))
                else:
                    open_buys.append(leg)
            else:
                m = _find_fifo_match(open_buys, leg["qty"], QTY_TOLERANCE)
                if m is not None:
                    entry = open_buys.pop(m)
                    records.append(_make_pair_record(date, symbol, company, client, participant,
                                                       entry, leg, "LONG_BUILD_SQUAREOFF"))
                else:
                    open_sells.append(leg)

        for leg in open_buys:
            records.append(_make_standalone_record(date, symbol, company, client, participant, leg, "BUY", "BUY_ONLY"))
        for leg in open_sells:
            records.append(_make_standalone_record(date, symbol, company, client, participant, leg, "SELL", "SELL_ONLY"))

    return pd.DataFrame(records)

# ---------------------------------------------------------------------------
# Participant classification — keyword patterns applied to client names
# ---------------------------------------------------------------------------
FII_KEYWORDS = [
    "GOLDMAN", "MORGAN STANLEY", "BARCLAYS", "NOMURA", "UBS", "CITIBANK",
    "CITI BANK", "JP MORGAN", "JPMORGAN", "DEUTSCHE", "BNP PARIBAS",
    "BNP ", "HSBC", "SOCIETE GENERALE", "MERRILL LYNCH", "CREDIT SUISSE",
    "MACQUARIE", "CLSA", "FIDELITY", "VANGUARD", "BLACKROCK", "ABERDEEN",
    "INVESCO", "TEMPLETON", "T. ROWE", "DIMENSIONAL", "APT UNIVERSAL",
    "ARROWHEAD", "CAPE COD", "ASHMORE", "ACADIAN", "ARTISAN",
]

MF_KEYWORDS = [
    "HDFC MF", "ICICI PRUDENTIAL", "SBI MF", "SBI MUTUAL", "NIPPON",
    "UTI MF", "UTI MUTUAL", "KOTAK MF", "KOTAK MUTUAL", "AXIS MF",
    "AXIS MUTUAL", "DSP", "FRANKLIN", "MIRAE", "MOTILAL OSWAL",
    "ADITYA BIRLA", "CANARA ROBECO", "BANDHAN MF", "EDELWEISS MF",
    "PARAG PARIKH", "TATA MF", "TATA MUTUAL", "SUNDARAM MF",
    "IDFC MF", "INVESCO MUTUAL", "QUANT MF", "MAHINDRA MANULIFE",
    "UNION MF", "QUANTUM MF", "WHITEOAK",
]

INSURANCE_KEYWORDS = [
    "LIC ", "LIFE INSURANCE CORPORATION", "HDFC LIFE", "SBI LIFE",
    "BAJAJ ALLIANZ", "MAX LIFE", "ICICI LOMBARD", "KOTAK LIFE",
    "TATA AIA", "RELIANCE LIFE", "STAR HEALTH", "NIVA BUPA",
    "BIRLA SUN LIFE", "GIC RE", "NEW INDIA",
]

PROMOTER_INDICATORS = [
    "PROMOTER", "FOUNDER", "FAMILY TRUST", "HOLDING LIMITED",
    "INVESTMENTS PVT", "INVESTMENTS PRIVATE", "VENTURES PVT",
    "ENTERPRISES PVT", "INDUSTRIES PVT",
]


def _classify_client(name: str) -> str:
    if not name or pd.isna(name):
        return "UNKNOWN"
    n = str(name).upper().strip()
    for kw in FII_KEYWORDS:
        if kw in n:
            return "FII"
    for kw in INSURANCE_KEYWORDS:
        if kw in n:
            return "INSURANCE"
    for kw in MF_KEYWORDS:
        if kw in n:
            return "MF"
    # "MUTUAL FUND" is a SEBI-reserved suffix (only registered AMCs may use it),
    # so any client name ending in it is MF even if the AMC brand isn't in the
    # enumerated list above (e.g. "QUANT MUTUAL FUND" vs the shorter "QUANT MF").
    if "MUTUAL FUND" in n:
        return "MF"
    for kw in PROMOTER_INDICATORS:
        if kw in n:
            return "PROMOTER"
    return "RETAIL"


def _parse_qty(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_price(val) -> float:
    if pd.isna(val):
        return 0.0
    s = str(val).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(val) -> str:
    """Normalise date to YYYY-MM-DD."""
    try:
        return pd.to_datetime(str(val), dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return ""


class BlockBulkDealEngine:
    """
    Phase 7A — Incremental downloader and classifier for block/bulk deals.

    Run daily (after 18:00 IST) to keep history current.
    First run downloads last 6M; subsequent runs download last 30D and dedup.
    """

    def __init__(self):
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        self.failed: list[dict] = []

    def run(self) -> bool:
        logger.info("[BlockBulkDeal] Starting Phase 7A")
        from nselib import capital_market

        existing = self._load_existing()
        last_date = existing["date"].max() if not existing.empty else ""

        # Download block + bulk deals
        block_raw = self._download_with_retry(capital_market.block_deals_data, "BLOCK", last_date)
        time.sleep(cfg.API_DELAY)
        bulk_raw  = self._download_with_retry(capital_market.bulk_deal_data,   "BULK",  last_date)

        # seq_id preserves the ORDER NSE returned each deal in (no intraday
        # timestamp exists in the source) -- this is the only proxy available
        # for "which transaction happened first" on a same-day multi-deal
        # client position, so it must never be destroyed by a later re-sort.
        # Block rows are numbered first, then bulk rows, continuing the
        # existing file's running counter (never renumbered on rewrite).
        new_rows = self._normalise(block_raw, "BLOCK") + self._normalise(bulk_raw, "BULK")
        next_seq = int(existing["seq_id"].max()) + 1 if (not existing.empty and "seq_id" in existing.columns and existing["seq_id"].notna().any()) else 0
        for i, row in enumerate(new_rows):
            row["seq_id"] = next_seq + i

        if not new_rows:
            logger.info("[7A] No new deal rows")
        else:
            new_df  = pd.DataFrame(new_rows)
            combined = pd.concat([existing, new_df], ignore_index=True)
            combined = (combined
                        # qty+price included so distinct multi-tranche legs by
                        # the same client/symbol/direction/date are never
                        # collapsed into one -- only true re-fetch duplicates
                        # of an already-seen disclosure are dropped.
                        .drop_duplicates(subset=["date", "symbol", "client_name", "deal_type",
                                                  "direction", "qty", "price"], keep="first")
                        # Sort by date then seq_id -- NEVER by symbol/client,
                        # which would scramble the within-date NSE report
                        # order that seq_id exists to preserve.
                        .sort_values(["date", "seq_id"])
                        .reset_index(drop=True))
            self._save_atomic(combined, DEALS_HISTORY)
            logger.info("[7A] Deals history: %d rows (added %d)", len(combined), len(new_rows))

        # Rebuild signals from full history
        deals = pd.read_csv(DEALS_HISTORY) if DEALS_HISTORY.exists() else pd.DataFrame()
        if not deals.empty:
            signals = self._compute_signals(deals)
            self._save_atomic(signals, SIGNALS_OUTPUT)

            # Sequence-paired transaction records (precomputed here, not at
            # request time -- pairing ~13k rows takes seconds, too slow for
            # a live API call on every page load).
            records = pair_client_transactions(deals)
            if not records.empty:
                self._save_atomic(records, RECORDS_OUTPUT)
                logger.info("[7A] Deal records: %d paired/standalone transactions", len(records))

        if self.failed:
            self._save_recovery(self.failed)

        self._print_summary(deals if not deals.empty else pd.DataFrame(new_rows) if new_rows else pd.DataFrame())
        return True

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------
    def _download_with_retry(self, func, label: str, last_date: str) -> pd.DataFrame:
        period = "1M" if last_date else "6M"
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            try:
                df = func(period=period)
                if df is not None and not df.empty:
                    return df
                return pd.DataFrame()
            except Exception as exc:
                if attempt < cfg.MAX_RETRIES:
                    time.sleep(cfg.RETRY_DELAY * attempt)
                else:
                    logger.warning("[7A] %s download failed: %s", label, exc)
                    self.failed.append({"source": label, "error": str(exc)})
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Normalise
    # ------------------------------------------------------------------
    def _normalise(self, df: pd.DataFrame, deal_type: str) -> list[dict]:
        if df is None or df.empty:
            return []
        df.columns = df.columns.str.strip()
        rows = []
        for _, r in df.iterrows():
            date_str = _parse_date(r.get("Date", ""))
            if not date_str:
                continue
            symbol = str(r.get("Symbol", "")).strip().upper()
            if not symbol:
                continue
            client  = str(r.get("ClientName", "")).strip()
            direction = str(r.get("Buy/Sell", "")).strip().upper()
            direction = "BUY" if "BUY" in direction else "SELL"
            qty   = _parse_qty(r.get("QuantityTraded", 0))
            price = _parse_price(r.get("TradePrice/Wght.Avg.Price", 0))
            value_cr = round(qty * price / 1e7, 4)
            participant = _classify_client(client)
            rows.append({
                "date": date_str,
                "symbol": symbol,
                "company": str(r.get("SecurityName", "")).strip(),
                "deal_type": deal_type,
                "client_name": client,
                "participant": participant,
                "direction": direction,
                "qty": qty,
                "price": price,
                "value_cr": value_cr,
            })
        return rows

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------
    def _compute_signals(self, deals: pd.DataFrame) -> pd.DataFrame:
        deals["date"] = pd.to_datetime(deals["date"])
        cutoff = deals["date"].max() - pd.Timedelta(days=ROLLING_WINDOW_DAYS)
        recent = deals[deals["date"] >= cutoff].copy()

        # Institutional = FII + MF + INSURANCE
        recent["is_institutional"] = recent["participant"].isin(["FII", "MF", "INSURANCE"])
        recent["net_qty"] = recent.apply(
            lambda r: r["qty"] if r["direction"] == "BUY" else -r["qty"], axis=1
        )
        recent["net_value_cr"] = recent.apply(
            lambda r: r["value_cr"] if r["direction"] == "BUY" else -r["value_cr"], axis=1
        )

        # Aggregate by symbol
        def agg_symbol(grp):
            inst = grp[grp["is_institutional"]]
            all_grp = grp
            return pd.Series({
                "total_deals": len(all_grp),
                "inst_deals": len(inst),
                "inst_net_qty": inst["net_qty"].sum(),
                "inst_net_value_cr": inst["net_value_cr"].sum(),
                "fii_net_value_cr": grp[grp["participant"] == "FII"]["net_value_cr"].sum(),
                "mf_net_value_cr":  grp[grp["participant"] == "MF"]["net_value_cr"].sum(),
                "promoter_net_value_cr": grp[grp["participant"] == "PROMOTER"]["net_value_cr"].sum(),
                "dominant_participant": grp.groupby("participant")["value_cr"].sum().idxmax() if not grp.empty else "UNKNOWN",
                "last_deal_date": all_grp["date"].max().strftime("%Y-%m-%d"),
            })

        if recent.empty:
            return pd.DataFrame()

        signals = recent.groupby("symbol").apply(agg_symbol).reset_index()

        def _signal(row) -> str:
            v = row["inst_net_value_cr"]
            prom = row["promoter_net_value_cr"]
            if v > 5 and prom > 0:
                return "STRONG_ACCUMULATION"
            if v > 5:
                return "INSTITUTIONAL_ACCUMULATION"
            if v < -5:
                return "INSTITUTIONAL_DISTRIBUTION"
            if prom > 2:
                return "PROMOTER_CONFIDENCE"
            if abs(v) <= 5:
                return "NEUTRAL"
            return "MIXED"

        signals["deal_signal"] = signals.apply(_signal, axis=1)
        signals["window_days"] = ROLLING_WINDOW_DAYS
        signals["as_of_date"] = deals["date"].max().strftime("%Y-%m-%d")

        return signals.sort_values("inst_net_value_cr", ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _load_existing(self) -> pd.DataFrame:
        if not DEALS_HISTORY.exists():
            return pd.DataFrame()
        df = pd.read_csv(DEALS_HISTORY)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        return df

    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))

    def _save_recovery(self, items: list[dict]):
        df = pd.DataFrame(items)
        df.to_csv(RECOVERY_QUEUE, index=False)

    def _print_summary(self, deals: pd.DataFrame):
        print()
        print("=" * 65)
        print("BLOCK/BULK DEAL ENGINE - PHASE 7A COMPLETE")
        print("=" * 65)
        if deals.empty:
            print("  No deals data available")
            return
        if "participant" in deals.columns:
            pc = deals["participant"].value_counts()
            print(f"Total deal rows  : {len(deals)}")
            for p, cnt in pc.items():
                print(f"  {p:12s}: {cnt}")
        if SIGNALS_OUTPUT.exists():
            sig = pd.read_csv(SIGNALS_OUTPUT)
            print()
            print(f"Symbol signals   : {len(sig)}")
            print("Top institutional accumulation (30D):")
            top = sig[sig["inst_net_value_cr"] > 0].head(8)
            for _, r in top.iterrows():
                print(f"  {r['symbol']:15s}: inst_net={r['inst_net_value_cr']:+.1f}Cr  {r['deal_signal']}")
        print("=" * 65)


if __name__ == "__main__":
    engine = BlockBulkDealEngine()
    engine.run()
